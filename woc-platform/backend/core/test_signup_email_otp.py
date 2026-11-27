import re
from unittest.mock import patch
from django.contrib.auth.models import User
from django.core import mail
from django.core.cache import cache
from django.test import TestCase,override_settings
from core.models import Profile,EmailOTPChallenge
from core.auth_services import MessageDeliveryError

@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',EMAIL_VERIFICATION_REQUIRED=False,EMAIL_SIGNUP_OTP_REQUIRED=True)
class SignupEmailOTPTests(TestCase):
 def setUp(self):
  cache.clear()
  self.payload={'name':'Signup Student','email':'signup@example.test','password':'StrongSignup!2026','age':21,'terms':True}
 def test_signup_verification_then_repeated_password_login(self):
  response=self.client.post('/api/register/',self.payload,content_type='application/json')
  self.assertEqual(response.status_code,201)
  self.assertTrue(response.json()['requires_email_verification'])
  self.assertNotIn('otp',response.json())
  self.assertNotIn('development_verification_url',response.json())
  otp=re.search(r'code is: (\d{6})',mail.outbox[0].body).group(1)
  challenge=EmailOTPChallenge.objects.get(pk=response.json()['challenge_id'])
  self.assertNotEqual(challenge.otp_hash,otp)
  credentials={'email':self.payload['email'],'password':self.payload['password']}
  self.assertEqual(self.client.post('/api/login/',credentials,content_type='application/json').status_code,403)
  verify={'challenge_id':str(challenge.pk),'otp':otp,'email':self.payload['email']}
  self.assertEqual(self.client.post('/api/email/verify-otp/',verify,content_type='application/json').status_code,200)
  self.assertEqual(self.client.post('/api/email/verify-otp/',verify,content_type='application/json').status_code,400)
  mail_count=len(mail.outbox)
  for _ in range(2):
   login=self.client.post('/api/login/',credentials,content_type='application/json')
   self.assertEqual(login.status_code,200)
   self.assertEqual(login.json()['user']['authorization']['dashboard_url'],'/dashboard/')
   self.client.logout()
  self.assertEqual(len(mail.outbox),mail_count)
 def test_code_cannot_verify_a_different_email(self):
  response=self.client.post('/api/register/',self.payload,content_type='application/json')
  otp=re.search(r'code is: (\d{6})',mail.outbox[0].body).group(1)
  response=self.client.post('/api/email/verify-otp/',{'challenge_id':response.json()['challenge_id'],'otp':otp,'email':'another@example.test'},content_type='application/json')
  self.assertEqual(response.status_code,403)
  self.assertFalse(Profile.objects.get(user__email=self.payload['email']).email_verified)
 def test_existing_account_not_forced_to_verify(self):
  user=User.objects.create_user(username='old@example.test',email='old@example.test',password='ExistingPass!2026')
  Profile.objects.create(user=user,roles=['student'],email_verified=False)
  self.assertEqual(self.client.post('/api/login/',{'email':user.email,'password':'ExistingPass!2026'},content_type='application/json').status_code,200)
 def test_invalid_email_creates_no_account(self):
  for email in ['bad@','bad@invalid..com','not-an-email']:
   self.assertEqual(self.client.post('/api/register/',{**self.payload,'email':email},content_type='application/json').status_code,400)
  self.assertFalse(User.objects.exists())
 def test_delivery_failure_and_resend_cooldown(self):
  with patch('core.views.send_email_otp',side_effect=MessageDeliveryError('Provider failure')):
   response=self.client.post('/api/register/',self.payload,content_type='application/json')
  self.assertEqual(response.status_code,201)
  self.assertEqual(response.json()['delivery_status'],'failed')
  self.assertFalse(EmailOTPChallenge.objects.filter(consumed_at__isnull=True).exists())
  self.assertEqual(self.client.post('/api/email/resend-otp/',{'email':self.payload['email']},content_type='application/json').status_code,429)
