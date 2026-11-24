from datetime import timedelta
import json
from unittest.mock import patch, MagicMock
from django.test import TestCase, override_settings
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.utils import timezone
from .models import Profile, PhoneOTPChallenge
from .auth_services import send_sms_otp, safe_send_mail, MessageDeliveryError


class MobileAuthenticationTests(TestCase):
 def challenge(self,purpose='register',phone='+919876543210',**extra):
  return PhoneOTPChallenge.objects.create(phone_number=phone,purpose=purpose,otp_hash=make_password('246810'),expires_at=timezone.now()+timedelta(minutes=5),**extra)
 def submit(self,c,action='register',**extra):
  return self.client.post('/api/auth/phone/',{'action':action,'challenge_id':str(c.id),'otp':'246810','name':'Mobile Student','age':20,'institution':'Example College','terms':True,**extra},content_type='application/json')
 def test_mobile_signup_creates_verified_account_and_session(self):
  c=self.challenge();r=self.submit(c)
  self.assertEqual(r.status_code,200)
  self.assertTrue(r.json()['user']['phone_verified'])
  self.assertEqual(self.client.get('/api/me/').json()['user']['phone_number'],c.phone_number)
  c.refresh_from_db();self.assertIsNotNone(c.consumed_at)
  self.assertEqual(self.submit(c).status_code,400)
 def test_mobile_login_uses_existing_verified_account(self):
  u=User.objects.create_user('phone-student');Profile.objects.create(user=u,age=20,phone_number='+919876543210',phone_verified=True)
  self.assertEqual(self.submit(self.challenge('login'),action='login').json()['user']['id'],u.id)
 def test_mobile_login_does_not_create_unknown_account(self):
  self.assertEqual(self.submit(self.challenge('login'),action='login').status_code,400)
  self.assertEqual(User.objects.count(),0)
 def test_staff_cannot_bypass_authenticator_with_phone(self):
  u=User.objects.create_user('staff',is_staff=True);Profile.objects.create(user=u,age=20,phone_number='+919876543210',phone_verified=True)
  self.assertEqual(self.submit(self.challenge('login'),action='login').status_code,403)
  self.assertNotIn('_auth_user_id',self.client.session)
 def test_challenge_cannot_be_used_for_another_purpose(self):
  self.assertEqual(self.submit(self.challenge('verification')).status_code,400)
 def test_underage_signup_requires_guardian_permission(self):
  c=self.challenge();self.assertEqual(self.submit(c,age=16).status_code,400)
  self.assertEqual(self.submit(c,age=16,guardian_consent=True).status_code,200)
 def test_wrong_code_attempts_are_persisted(self):
  c=self.challenge()
  for _ in range(3):self.assertEqual(self.submit(c,otp='000000').status_code,400)
  self.assertEqual(self.submit(c).status_code,400)
  c.refresh_from_db();self.assertEqual(c.attempts,3)
 def test_expired_code_is_rejected(self):
  c=self.challenge();c.expires_at=timezone.now()-timedelta(seconds=1);c.save()
  self.assertEqual(self.submit(c).status_code,400)
 def test_duplicate_phone_signup_is_rejected(self):
  u=User.objects.create_user('existing');Profile.objects.create(user=u,age=20,phone_number='+919876543210',phone_verified=True)
  self.assertEqual(self.submit(self.challenge()).status_code,409)
 def test_registration_email_failure_does_not_claim_delivery(self):
  with patch('core.views.send_verification_email',side_effect=MessageDeliveryError('Email could not be sent.')):
   r=self.client.post('/api/register/',{'name':'Email Student','email':'student@example.test','password':'StrongPass!2026','age':20,'institution':'College','terms':True},content_type='application/json')
  self.assertEqual(r.status_code,201)
  self.assertEqual(r.json()['delivery_status'],'failed')
  self.assertNotIn('development_verification_url',r.json())
 def test_google_callback_requires_session_state(self):
  with patch('core.views.exchange_google_code') as exchange:
   r=self.client.post('/api/auth/google/',{'code':'untrusted-code'},content_type='application/json')
  self.assertEqual(r.status_code,400);exchange.assert_not_called()


@override_settings(SMS_PROVIDER='msg91',MSG91_AUTH_KEY='unit-test-key',MSG91_TEMPLATE_ID='unit-test-template',DEBUG=False,SMS_DEV_MODE=False)
class DeliveryTests(TestCase):
 def test_console_mail_is_not_reported_as_live_delivery(self):
  with self.settings(EMAIL_BACKEND='django.core.mail.backends.console.EmailBackend'):
   self.assertFalse(safe_send_mail('Verify WOC','Example','recipient@example.test','<p>Example</p>','email_verification'))
 def provider(self,result):
  response=MagicMock();response.__enter__.return_value=response;response.read.return_value=json.dumps(result).encode();return response
 def test_msg91_acceptance_is_required(self):
  with patch('urllib.request.urlopen',return_value=self.provider({'type':'success','request_id':'example'})) as request:
   self.assertEqual(send_sms_otp('+919876543210','246810')['mode'],'live')
   sent=request.call_args.args[0]
   self.assertTrue(sent.full_url.startswith('https://control.msg91.com/api/v5/otp?'))
   self.assertNotIn('authkey=',sent.full_url)
   self.assertEqual(sent.get_header('Authkey'),'unit-test-key')
 def test_provider_rejection_is_not_reported_as_success(self):
  with patch('urllib.request.urlopen',return_value=self.provider({'type':'error','message':'Invalid template'})):
   with self.assertRaises(MessageDeliveryError):send_sms_otp('+919876543210','246810')
 def test_missing_credentials_never_fall_back_to_success(self):
  with self.settings(MSG91_AUTH_KEY='',DEBUG=True,SMS_DEV_MODE=True):
   with self.assertRaises(MessageDeliveryError):send_sms_otp('+919876543210','246810')
 def test_test_mode_is_refused_in_production(self):
  with self.settings(SMS_PROVIDER='test_mode',SMS_DEV_MODE=True):
   with self.assertRaises(MessageDeliveryError):send_sms_otp('+919876543210','246810')
 def test_failed_send_creates_no_valid_challenge(self):
  with patch('core.views.send_sms_otp',side_effect=MessageDeliveryError('Unavailable')):
   r=self.client.post('/api/phone/send-otp/',{'phone':'9876543210','purpose':'login'},content_type='application/json')
  self.assertEqual(r.status_code,503)
  self.assertEqual(PhoneOTPChallenge.objects.count(),0)
