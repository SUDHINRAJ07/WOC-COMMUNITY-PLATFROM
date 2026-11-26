from datetime import timedelta
import json
from unittest.mock import patch, MagicMock
from django.test import TestCase, override_settings
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.utils import timezone
from .models import Profile, PhoneOTPChallenge
from .auth_services import send_sms_otp, safe_send_mail, MessageDeliveryError


@override_settings(EMAIL_VERIFICATION_REQUIRED=True)
class AccountDeliveryRegressionTests(TestCase):
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


@override_settings(WOC_LOCAL_SCREEN_OTP=False,SMS_PROVIDER='msg91',MSG91_AUTH_KEY='unit-test-key',MSG91_TEMPLATE_ID='unit-test-template',DEBUG=False,SMS_DEV_MODE=False)
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
  self.assertEqual(r.status_code,410)
  self.assertEqual(PhoneOTPChallenge.objects.count(),0)
