from datetime import timedelta
from unittest.mock import patch
from django.test import TestCase, Client, override_settings
from django.contrib.auth.models import User
from django.contrib.auth.hashers import check_password
from django.utils import timezone
from .models import Profile, PhoneOTPChallenge


@override_settings(DEBUG=True, WOC_LOCAL_SCREEN_OTP=True, SMS_TEST_MODE=True, EMAIL_VERIFICATION_REQUIRED=False, EMAIL_SIGNUP_OTP_REQUIRED=False)
class LocalAuthenticationTests(TestCase):
 def setUp(self):
  from django.core.cache import cache
  cache.clear()
  self.client.defaults['HTTP_HOST']='127.0.0.1:8317'
 def post(self,path,data,client=None,**extra):
  return (client or self.client).post('/api/'+path,data,content_type='application/json',**extra)
 def email_signup(self,**changes):
  return self.post('register/',{'name':'Local Student','email':'local@example.test','password':'LocalPass!2035','age':20,'institution':'College','terms':True,**changes})
 def send(self,purpose='register',phone='9876543210'):
  return self.post('phone/send-otp/',{'purpose':purpose,'phone':phone,'country_code':'+91'})
 def verify(self,proof,action='register',**changes):
  return self.post('auth/phone/',{'challenge_id':proof['challenge_id'],'otp':proof['development_otp'],'action':action,'name':'Mobile Student','age':20,'institution':'College','terms':True,**changes})

 def test_email_signup_and_repeated_password_login_persist(self):
  with patch('core.views.send_verification_email') as mail:
   response=self.email_signup()
   self.assertEqual(response.status_code,201);mail.assert_not_called()
  self.assertFalse(response.json()['requires_email_verification'])
  user=User.objects.get(username='local@example.test')
  self.assertTrue(user.check_password('LocalPass!2035'))
  self.assertNotEqual(user.password,'LocalPass!2035')
  self.assertFalse(user.profile.email_verified)
  for _ in range(2):
   self.assertEqual(self.post('login/',{'email':user.email,'password':'LocalPass!2035'}).status_code,200)
   self.assertEqual(self.client.get('/api/me/').json()['user']['id'],user.pk)
   self.post('logout/',{})
  self.assertEqual(User.objects.filter(email=user.email).count(),1)

 def test_email_wrong_password_and_duplicates_rejected(self):
  self.email_signup()
  self.assertEqual(self.post('login/',{'email':'local@example.test','password':'wrong'}).status_code,400)
  self.assertEqual(self.email_signup().status_code,400)

 def test_terms_and_underage_permissions_still_required(self):
  self.assertEqual(self.email_signup(terms=False).status_code,400)
  self.assertEqual(self.email_signup(age=16).status_code,400)
  self.assertEqual(self.email_signup(age=16,guardian_consent=True).status_code,201)

 def test_mobile_signup_then_fresh_otp_login_persists_same_account(self):
  with patch('core.views.send_sms_otp') as sms:
   proof=self.send().json();sms.assert_not_called()
  self.assertEqual(proof['delivery_mode'],'test')
  self.assertRegex(proof['development_otp'],r'^\d{6}$')
  challenge=PhoneOTPChallenge.objects.get(pk=proof['challenge_id'])
  self.assertNotEqual(challenge.otp_hash,proof['development_otp'])
  self.assertTrue(check_password(proof['development_otp'],challenge.otp_hash))
  response=self.verify(proof);self.assertEqual(response.status_code,200)
  user_id=response.json()['user']['id']
  self.assertEqual(self.client.get('/api/me/').json()['user']['phone_number'],'+919876543210')
  challenge.refresh_from_db();self.assertIsNotNone(challenge.consumed_at)
  self.assertEqual(self.verify(proof).status_code,400)
  self.post('logout/',{})
  PhoneOTPChallenge.objects.filter(pk=challenge.pk).update(created_at=timezone.now()-timedelta(seconds=61))
  login_proof=self.send('login').json()
  self.assertEqual(self.verify(login_proof,'login').json()['user']['id'],user_id)
  self.assertEqual(User.objects.count(),1)

 def test_wrong_otp_attempts_lock_challenge(self):
  proof=self.send().json()
  wrong='000000' if proof['development_otp']!='000000' else '111111'
  for _ in range(5):self.assertEqual(self.verify(proof,otp=wrong).status_code,400)
  self.assertEqual(self.verify(proof).status_code,400)
  self.assertEqual(PhoneOTPChallenge.objects.get(pk=proof['challenge_id']).attempts,5)

 def test_expired_otp_and_resend_cooldown(self):
  proof=self.send().json()
  self.assertEqual(self.send().status_code,429)
  PhoneOTPChallenge.objects.filter(pk=proof['challenge_id']).update(expires_at=timezone.now()-timedelta(seconds=1))
  self.assertEqual(self.verify(proof).status_code,400)

 def test_otp_is_bound_to_requesting_browser(self):
  proof=self.send().json()
  other=Client(HTTP_HOST='127.0.0.1:8317')
  response=self.post('auth/phone/',{'challenge_id':proof['challenge_id'],'otp':proof['development_otp'],'action':'register'},client=other)
  self.assertEqual(response.status_code,400)
  self.assertEqual(User.objects.count(),0)

 def test_resend_invalidates_previous_challenge(self):
  first=self.send().json()
  PhoneOTPChallenge.objects.filter(pk=first['challenge_id']).update(created_at=timezone.now()-timedelta(seconds=61))
  second=self.send().json()
  self.assertIsNotNone(PhoneOTPChallenge.objects.get(pk=first['challenge_id']).consumed_at)
  self.assertEqual(self.verify(first).status_code,400)
  self.assertEqual(self.verify(second).status_code,200)

 def test_unknown_mobile_login_does_not_create_account(self):
  proof=self.send('login').json()
  self.assertEqual(self.verify(proof,'login').status_code,400)
  self.assertEqual(User.objects.count(),0)

 def test_duplicate_mobile_signup_is_rejected(self):
  user=User.objects.create_user('existing')
  Profile.objects.create(user=user,age=20,phone_number='+919876543210',phone_verified=True)
  self.assertEqual(self.verify(self.send().json()).status_code,409)

 def test_screen_otp_is_blocked_on_production_external_and_forwarded_requests(self):
  with self.settings(DEBUG=False):self.assertEqual(self.send().status_code,403)
  with self.settings(WOC_LOCAL_SCREEN_OTP=False):self.assertEqual(self.send().status_code,410)
  for extra in [{'REMOTE_ADDR':'192.168.1.10'},{'HTTP_HOST':'testserver'},{'HTTP_X_FORWARDED_FOR':'8.8.8.8'},{'HTTP_X_FORWARDED_HOST':'localhost:8317'}]:
   self.assertEqual(self.post('phone/send-otp/',{'phone':'9876543210'},**extra).status_code,403)
  self.assertEqual(PhoneOTPChallenge.objects.count(),0)

 def test_phone_format_and_purpose_validation(self):
  self.assertEqual(self.send(phone='12345').status_code,400)
  self.assertEqual(self.send(purpose='other').status_code,400)

 def test_staff_cannot_bypass_mfa_with_local_phone(self):
  user=User.objects.create_user('staff',is_staff=True)
  Profile.objects.create(user=user,age=20,phone_number='+919876543210',phone_verified=True)
  self.assertEqual(self.verify(self.send('login').json(),'login').status_code,403)

 def test_csrf_required_for_email_and_mobile_requests(self):
  client=Client(enforce_csrf_checks=True,HTTP_HOST='127.0.0.1:8317')
  for path in ['register/','login/','phone/send-otp/','auth/phone/']:
   self.assertEqual(self.post(path,{},client=client).status_code,403)


@override_settings(DEBUG=True,WOC_LOCAL_ADMIN_PASSWORD_LOGIN=True,EMAIL_VERIFICATION_REQUIRED=True)
class LocalAdminPreviewLoginTests(TestCase):
 def setUp(self):
  from django.core.cache import cache
  cache.clear()
  self.admin=User.objects.create_superuser(username='preview-admin',password='PreviewOnlyPass!2026')
  Profile.objects.create(user=self.admin,age=None,roles=[],email_verified=False)
 def sign_in(self,**metadata):
  client=Client(REMOTE_ADDR='127.0.0.1',HTTP_HOST='127.0.0.1:8317',**metadata)
  return client.post('/api/login/',{'email':'preview-admin','password':'PreviewOnlyPass!2026'},content_type='application/json')
 def test_loopback_superadmin_can_access_preview_without_changing_verification(self):
  response=self.sign_in()
  self.assertEqual(response.status_code,200)
  self.assertEqual(response.json()['user']['authorization']['dashboard_url'],'/super-admin/')
  self.admin.profile.refresh_from_db()
  self.assertFalse(self.admin.profile.email_verified)
 def test_preview_exception_is_disabled_for_production_proxy_and_remote(self):
  for settings_kwargs in [{'DEBUG':False},{'WOC_LOCAL_ADMIN_PASSWORD_LOGIN':False}]:
   with override_settings(**settings_kwargs):self.assertEqual(self.sign_in().status_code,403)
  self.assertEqual(self.sign_in(HTTP_X_FORWARDED_FOR='127.0.0.1').status_code,403)
  remote=Client(REMOTE_ADDR='203.0.113.4',HTTP_HOST='127.0.0.1:8317')
  self.assertEqual(remote.post('/api/login/',{'email':'preview-admin','password':'PreviewOnlyPass!2026'},content_type='application/json').status_code,403)
