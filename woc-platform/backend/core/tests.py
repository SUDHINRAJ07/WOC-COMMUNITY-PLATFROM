from datetime import timedelta
from django.utils import timezone
from django.test import TestCase,Client
from django.contrib.auth.models import User
from django.core import signing
from .models import Profile,Program,Record,Certificate,AuditLog,EmailDeliveryLog,AuthAuditLog,PhoneOTPChallenge,OAuthIdentity,PasswordResetToken,Notification
class WorkflowTests(TestCase):
 def setUp(self):
  self.user=User.objects.create_user('learner@example.test','learner@example.test','LongPass!2026',first_name='Learner')
  Profile.objects.create(user=self.user,age=20,email_verified=True,roles=['student'])
  self.course=Program.objects.create(slug='sample-course',module='academy',title='Sample Course',description='Sample',category='Learning')
  self.client.force_login(self.user)
 def test_registration_duplicate_is_rejected(self):
  self.assertEqual(self.client.post('/api/records/',{'program':self.course.slug,'data':{}},content_type='application/json').status_code,201)
  self.assertEqual(self.client.post('/api/records/',{'program':self.course.slug,'data':{}},content_type='application/json').status_code,400)
 def test_student_cannot_access_admin(self):self.assertEqual(self.client.get('/api/admin/records/').status_code,403)
 def test_records_are_private(self):
  other=User.objects.create_user('other','other@example.test','AnotherPass!2026')
  Record.objects.create(user=other,program=self.course)
  self.assertEqual(self.client.get('/api/records/').json()['results'],[])
 def test_underage_registration_needs_permission(self):
  self.client.logout()
  response=self.client.post('/api/register/',{'name':'School student','email':'school@example.test','password':'LongPass!2026','age':16,'terms':True},content_type='application/json')
  self.assertEqual(response.status_code,400)
 def test_sports_team_size_validated(self):
  p=Program.objects.create(slug='cricket',module='sports',title='Cricket',description='Sample',category='Cricket',details={'min_players':11,'max_players':15})
  response=self.client.post('/api/records/',{'program':p.slug,'data':{'team':'Team','players':'Only one'}},content_type='application/json')
  self.assertEqual(response.status_code,400)
 def test_learning_requires_lessons_before_assessment(self):
  r=Record.objects.create(user=self.user,program=self.course,status='enrolled')
  response=self.client.post(f'/api/learning/{r.id}/',{'action':'assessment','answers':[1,0,2],'project':'A project with a detailed description.'},content_type='application/json')
  self.assertEqual(response.status_code,400)
 def test_full_learning_and_staff_issuance(self):
  r=Record.objects.create(user=self.user,program=self.course,status='enrolled')
  for i in range(3):self.assertEqual(self.client.post(f'/api/learning/{r.id}/',{'action':'lesson','lesson':i},content_type='application/json').status_code,200)
  self.client.post(f'/api/learning/{r.id}/',{'action':'assessment','answers':[1,0,2],'project':'I built a focused prototype and tested it with students.'},content_type='application/json')
  r.refresh_from_db();self.assertEqual(r.status,'awaiting_review');self.assertFalse(Certificate.objects.exists())
  self.user.is_staff=True;self.user.save()
  self.assertEqual(self.client.patch('/api/admin/records/',{'id':str(r.id),'status':'completed'},content_type='application/json').status_code,200)
  self.assertTrue(Certificate.objects.filter(record=r).exists());self.assertTrue(AuditLog.objects.exists())
 def test_anonymous_login_requires_csrf(self):
  client=Client(enforce_csrf_checks=True)
  response=client.post('/api/login/',{'email':self.user.email,'password':'LongPass!2026'},content_type='application/json')
  self.assertEqual(response.status_code,403)
 def test_registration_and_single_use_verification(self):
  self.client.logout()
  with self.settings(DEBUG=True,AUTH_TEST_MODE=True):
   reg_resp=self.client.post('/api/register/',{'name':'New Student','email':'newstudent@example.test','password':'StrongPass#2026','age':19,'terms':True},content_type='application/json')
  self.assertEqual(reg_resp.status_code,201)
  new_user=User.objects.get(email='newstudent@example.test')
  self.assertFalse(new_user.profile.email_verified)
  dev_url=reg_resp.json().get('development_verification_url')
  self.assertIsNotNone(dev_url)
  token=dev_url.split('token=')[1]
  # First verification succeeds
  ver_resp=self.client.post('/api/verify/',{'token':token},content_type='application/json')
  self.assertEqual(ver_resp.status_code,200)
  new_user.profile.refresh_from_db()
  self.assertTrue(new_user.profile.email_verified)
  self.assertIsNotNone(new_user.profile.email_verified_at)
  # Second verification with same token is rejected (single-use)
  ver_again=self.client.post('/api/verify/',{'token':token},content_type='application/json')
  self.assertEqual(ver_again.status_code,400)
  self.assertIn('already been used',ver_again.json()['error'])
 def test_tampered_verification_token_is_rejected(self):
  resp=self.client.post('/api/verify/',{'token':'tampered.invalid.token'},content_type='application/json')
  self.assertEqual(resp.status_code,400)
 def test_resend_verification_and_rate_limit(self):
  self.client.logout()
  with self.settings(DEBUG=True,AUTH_TEST_MODE=True):
   reg_resp=self.client.post('/api/register/',{'name':'Resend Student','email':'resend@example.test','password':'StrongPass#2026','age':20,'terms':True},content_type='application/json')
  self.assertEqual(reg_resp.status_code,201)
  # First resend immediate should hit 60s rate limit since register already sent one
  resend_blocked=self.client.post('/api/resend-verification/',{'email':'resend@example.test'},content_type='application/json')
  self.assertEqual(resend_blocked.status_code,429)
  # Clear delivery log to simulate 60s passed
  EmailDeliveryLog.objects.filter(recipient='resend@example.test').delete()
  with self.settings(DEBUG=True,AUTH_TEST_MODE=True):
   resend_ok=self.client.post('/api/resend-verification/',{'email':'resend@example.test'},content_type='application/json')
  self.assertEqual(resend_ok.status_code,200)
  self.assertIn('development_verification_url',resend_ok.json())
  # Verified user resend returns 400
  p=Profile.objects.get(user__email='resend@example.test')
  p.email_verified=True;p.save()
  resend_verified=self.client.post('/api/resend-verification/',{'email':'resend@example.test'},content_type='application/json')
  self.assertEqual(resend_verified.status_code,400)
 def test_unverified_user_cannot_login(self):
  self.client.logout()
  u=User.objects.create_user('unverified@example.test','unverified@example.test','StrongPass#2026')
  Profile.objects.create(user=u,age=21,email_verified=False)
  login_resp=self.client.post('/api/login/',{'email':'unverified@example.test','password':'StrongPass#2026'},content_type='application/json')
  self.assertEqual(login_resp.status_code,403)
  self.assertIn('Verify your email',login_resp.json()['error'])
 def test_phone_otp_send_and_verify_success(self):
  self.client.force_login(self.user)
  with self.settings(DEBUG=True,SMS_DEV_MODE=True,SMS_PROVIDER='test_mode'):
   send_resp=self.client.post('/api/phone/send-otp/',{'phone':'9876543210','country_code':'+91'},content_type='application/json')
  self.assertEqual(send_resp.status_code,200)
  data=send_resp.json()
  self.assertEqual(data['phone'],'+919876543210')
  self.assertIn('challenge_id',data)
  otp=data.get('development_otp')
  self.assertIsNotNone(otp)
  challenge=PhoneOTPChallenge.objects.get(id=data['challenge_id'])
  self.assertNotEqual(challenge.otp_hash,otp)
  # Verify with correct OTP
  ver_resp=self.client.post('/api/phone/verify-otp/',{'challenge_id':data['challenge_id'],'otp':otp},content_type='application/json')
  self.assertEqual(ver_resp.status_code,200)
  self.user.profile.refresh_from_db()
  self.assertTrue(self.user.profile.phone_verified)
  self.assertEqual(self.user.profile.phone_number,'+919876543210')
  self.assertIsNotNone(self.user.profile.phone_verified_at)
 def test_phone_otp_resend_cooldown(self):
  with self.settings(DEBUG=True,SMS_DEV_MODE=True,SMS_PROVIDER='test_mode'):
   resp1=self.client.post('/api/phone/send-otp/',{'phone':'9123456780'},content_type='application/json')
   self.assertEqual(resp1.status_code,200)
   # Immediate second request hits cooldown
   resp2=self.client.post('/api/phone/resend-otp/',{'phone':'9123456780'},content_type='application/json')
   self.assertEqual(resp2.status_code,429)
   self.assertIn('60 seconds',resp2.json()['error'])
 def test_phone_otp_max_3_attempts_enforced(self):
  with self.settings(DEBUG=True,SMS_DEV_MODE=True,SMS_PROVIDER='test_mode'):
   send_resp=self.client.post('/api/phone/send-otp/',{'phone':'9988776655'},content_type='application/json')
  cid=send_resp.json()['challenge_id']
  # Attempt 1 wrong
  r1=self.client.post('/api/phone/verify-otp/',{'challenge_id':cid,'otp':'000000'},content_type='application/json')
  self.assertEqual(r1.status_code,400)
  self.assertIn('2 attempt(s) remaining',r1.json()['error'])
  # Attempt 2 wrong
  r2=self.client.post('/api/phone/verify-otp/',{'challenge_id':cid,'otp':'111111'},content_type='application/json')
  self.assertEqual(r2.status_code,400)
  self.assertIn('1 attempt(s) remaining',r2.json()['error'])
  # Attempt 3 wrong -> locked
  r3=self.client.post('/api/phone/verify-otp/',{'challenge_id':cid,'otp':'222222'},content_type='application/json')
  self.assertEqual(r3.status_code,400)
  self.assertIn('Maximum verification attempts exceeded',r3.json()['error'])
  # Attempt 4 (even with correct code) is blocked
  correct_otp=send_resp.json().get('development_otp')
  r4=self.client.post('/api/phone/verify-otp/',{'challenge_id':cid,'otp':correct_otp},content_type='application/json')
  self.assertEqual(r4.status_code,400)
 def test_phone_otp_expiration(self):
  from datetime import timedelta
  from django.utils import timezone
  from django.contrib.auth.hashers import make_password
  c=PhoneOTPChallenge.objects.create(
   phone_number='+919999999999',
   otp_hash=make_password('123456'),
   expires_at=timezone.now()-timedelta(minutes=1)
  )
  resp=self.client.post('/api/phone/verify-otp/',{'challenge_id':str(c.id),'otp':'123456'},content_type='application/json')
  self.assertEqual(resp.status_code,400)
  self.assertIn('expired',resp.json()['error'])
 def test_invalid_phone_format_rejected(self):
  resp=self.client.post('/api/phone/send-otp/',{'phone':'12345'},content_type='application/json')
  self.assertEqual(resp.status_code,400)
 def test_google_auth_signup_new_user(self):
  self.client.logout()
  token='mock-google-token:newgoogler@example.test:sub-goog-101:Google Learner'
  with self.settings(DEBUG=True,AUTH_TEST_MODE=True):
   resp=self.client.post('/api/auth/google/',{'id_token':token},content_type='application/json')
  self.assertEqual(resp.status_code,200)
  data=resp.json()
  self.assertEqual(data['action'],'created')
  self.assertEqual(data['user']['email'],'newgoogler@example.test')
  self.assertTrue(data['user']['email_verified'])
  u=User.objects.get(email='newgoogler@example.test')
  self.assertTrue(OAuthIdentity.objects.filter(user=u,provider='google',provider_uid='sub-goog-101').exists())
 def test_google_auth_login_existing_google_user(self):
  self.client.logout()
  token='mock-google-token:existinggoogler@example.test:sub-goog-202:Existing Googler'
  with self.settings(DEBUG=True,AUTH_TEST_MODE=True):
   r1=self.client.post('/api/auth/google/',{'id_token':token},content_type='application/json')
   self.assertEqual(r1.status_code,200)
   self.assertEqual(r1.json()['action'],'created')
   # Second login via Google
   r2=self.client.post('/api/auth/google/',{'id_token':token},content_type='application/json')
   self.assertEqual(r2.status_code,200)
   self.assertEqual(r2.json()['action'],'logged_in')
 def test_google_auth_prevents_insecure_account_takeover(self):
  self.client.logout()
  # Existing local user with password
  u=User.objects.create_user('localuser@example.test','localuser@example.test','SecretPass#2026')
  Profile.objects.create(user=u,age=22,email_verified=True,auth_provider='local')
  # Unverified Google login attempt with same email without password
  token='mock-google-token:localuser@example.test:attacker-sub-666:Imposter'
  with self.settings(DEBUG=True,AUTH_TEST_MODE=True):
   resp=self.client.post('/api/auth/google/',{'id_token':token},content_type='application/json')
  self.assertEqual(resp.status_code,409)
  self.assertEqual(resp.json().get('action'),'require_link_password')
  # Identity not linked yet
  self.assertFalse(OAuthIdentity.objects.filter(provider_uid='attacker-sub-666').exists())
 def test_google_auth_secure_linking_with_password(self):
  self.client.logout()
  u=User.objects.create_user('linkme@example.test','linkme@example.test','CorrectPass#2026')
  Profile.objects.create(user=u,age=23,email_verified=True,auth_provider='local')
  token='mock-google-token:linkme@example.test:sub-goog-303:Real Owner'
  with self.settings(DEBUG=True,AUTH_TEST_MODE=True):
   # Wrong password fails
   r_wrong=self.client.post('/api/auth/google/',{'id_token':token,'link_password':'WrongPassword'},content_type='application/json')
   self.assertEqual(r_wrong.status_code,400)
   # Correct password succeeds
   r_ok=self.client.post('/api/auth/google/',{'id_token':token,'link_password':'CorrectPass#2026'},content_type='application/json')
   self.assertEqual(r_ok.status_code,200)
   self.assertEqual(r_ok.json()['action'],'linked')
   self.assertTrue(OAuthIdentity.objects.filter(user=u,provider_uid='sub-goog-303').exists())
 def test_invalid_google_token_rejected(self):
  resp=self.client.post('/api/auth/google/',{'id_token':''},content_type='application/json')
  self.assertEqual(resp.status_code,400)
 def test_password_reset_anti_enumeration(self):
  self.client.logout()
  with self.settings(DEBUG=True,AUTH_TEST_MODE=True):
   resp=self.client.post('/api/password-reset/request/',{'email':'nonexistent@example.test'},content_type='application/json')
  self.assertEqual(resp.status_code,200)
  self.assertIn('If an account exists',resp.json()['message'])
  self.assertNotIn('development_reset_url',resp.json())
 def test_password_reset_full_flow(self):
  self.client.logout()
  with self.settings(DEBUG=True,AUTH_TEST_MODE=True):
   req_resp=self.client.post('/api/password-reset/request/',{'email':self.user.email},content_type='application/json')
  self.assertEqual(req_resp.status_code,200)
  dev_url=req_resp.json().get('development_reset_url')
  self.assertIsNotNone(dev_url)
  raw_token=dev_url.split('token=')[1]
  token_obj=PasswordResetToken.objects.filter(user=self.user,used=False).first()
  self.assertIsNotNone(token_obj)
  self.assertTrue(token_obj.expires_at>timezone.now())
  # Mismatched confirm password rejected
  bad_confirm=self.client.post('/api/password-reset/confirm/',{'token':raw_token,'password':'BrandNewPass#2026','confirm_password':'DifferentPass'},content_type='application/json')
  self.assertEqual(bad_confirm.status_code,400)
  self.assertIn('Passwords do not match',bad_confirm.json()['error'])
  # Weak password rejected by Django validator
  weak_resp=self.client.post('/api/password-reset/confirm/',{'token':raw_token,'password':'123','confirm_password':'123'},content_type='application/json')
  self.assertEqual(weak_resp.status_code,400)
  # Successful reset
  confirm_resp=self.client.post('/api/password-reset/confirm/',{'token':raw_token,'password':'BrandNewPass#2026','confirm_password':'BrandNewPass#2026'},content_type='application/json')
  self.assertEqual(confirm_resp.status_code,200)
  token_obj.refresh_from_db()
  self.assertTrue(token_obj.used)
  # Old password no longer works
  old_login=self.client.post('/api/login/',{'email':self.user.email,'password':'LongPass!2026'},content_type='application/json')
  self.assertEqual(old_login.status_code,400)
  # New password works
  new_login=self.client.post('/api/login/',{'email':self.user.email,'password':'BrandNewPass#2026'},content_type='application/json')
  self.assertEqual(new_login.status_code,200)
 def test_password_reset_single_use_and_expiration(self):
  self.client.logout()
  with self.settings(DEBUG=True,AUTH_TEST_MODE=True):
   req_resp=self.client.post('/api/password-reset/request/',{'email':self.user.email},content_type='application/json')
  raw_token=req_resp.json()['development_reset_url'].split('token=')[1]
  # Successfully use it once
  r1=self.client.post('/api/password-reset/confirm/',{'token':raw_token,'password':'FreshPassword#2026','confirm_password':'FreshPassword#2026'},content_type='application/json')
  self.assertEqual(r1.status_code,200)
  # Second attempt rejected
  r2=self.client.post('/api/password-reset/confirm/',{'token':raw_token,'password':'AnotherPass#2026','confirm_password':'AnotherPass#2026'},content_type='application/json')
  self.assertEqual(r2.status_code,400)
  self.assertIn('already been used',r2.json()['error'])
 def test_password_reset_expired_token(self):
  self.client.logout()
  with self.settings(DEBUG=True,AUTH_TEST_MODE=True):
   req_resp=self.client.post('/api/password-reset/request/',{'email':self.user.email},content_type='application/json')
  raw_token=req_resp.json()['development_reset_url'].split('token=')[1]
  # Artificially expire the token
  token_obj=PasswordResetToken.objects.filter(user=self.user,used=False).first()
  token_obj.expires_at=timezone.now()-timedelta(minutes=5)
  token_obj.save()
  r_exp=self.client.post('/api/password-reset/confirm/',{'token':raw_token,'password':'FreshPassword#2026'},content_type='application/json')
  self.assertEqual(r_exp.status_code,400)
  self.assertIn('expired',r_exp.json()['error'])
 def test_password_reset_rate_limiting(self):
  self.client.logout()
  with self.settings(DEBUG=True,AUTH_TEST_MODE=True):
   r1=self.client.post('/api/password-reset/request/',{'email':self.user.email},content_type='application/json')
   self.assertEqual(r1.status_code,200)
   # Second request immediately triggers 429
   r2=self.client.post('/api/password-reset/request/',{'email':self.user.email},content_type='application/json')
   self.assertEqual(r2.status_code,429)
 def test_registration_creates_notification_and_email(self):
  Notification.objects.filter(user=self.user).delete()
  EmailDeliveryLog.objects.filter(recipient=self.user.email).delete()
  p=Program.objects.create(slug='robotics-workshop',module='events',title='Robotics Workshop',description='Event',category='Workshop')
  resp=self.client.post('/api/records/',{'program':p.slug,'data':{}},content_type='application/json')
  self.assertEqual(resp.status_code,201)
  notif=Notification.objects.filter(user=self.user,read=False).first()
  self.assertIsNotNone(notif)
  self.assertIn('Robotics Workshop',notif.message)
  email_log=EmailDeliveryLog.objects.filter(recipient=self.user.email,template_name='registration_confirmation').first()
  self.assertIsNotNone(email_log)
  self.assertEqual(email_log.status,'sent')
 def test_admin_status_update_creates_notification_and_email(self):
  r=Record.objects.create(user=self.user,program=self.course,status='submitted')
  Notification.objects.filter(user=self.user).delete()
  EmailDeliveryLog.objects.filter(recipient=self.user.email).delete()
  self.user.is_staff=True;self.user.save()
  resp=self.client.patch('/api/admin/records/',{'id':str(r.id),'status':'approved'},content_type='application/json')
  self.assertEqual(resp.status_code,200)
  notif=Notification.objects.filter(user=self.user).first()
  self.assertIsNotNone(notif)
  self.assertIn('approved',notif.message)
  email_log=EmailDeliveryLog.objects.filter(recipient=self.user.email,template_name='status_update').first()
  self.assertIsNotNone(email_log)
  self.assertEqual(email_log.status,'sent')
 def test_notifications_unread_count_and_mark_read(self):
  Notification.objects.filter(user=self.user).delete()
  n1=Notification.objects.create(user=self.user,message='First alert',read=False)
  n2=Notification.objects.create(user=self.user,message='Second alert',read=False)
  get_resp=self.client.get('/api/notifications/')
  self.assertEqual(get_resp.status_code,200)
  data=get_resp.json()
  self.assertEqual(data['unread_count'],2)
  self.assertEqual(len(data['results']),2)
  self.assertIn('created_at',data['results'][0])
  p1=self.client.patch('/api/notifications/',{'id':n1.id},content_type='application/json')
  self.assertEqual(p1.status_code,200)
  self.assertEqual(p1.json()['unread_count'],1)
  n1.refresh_from_db()
  self.assertTrue(n1.read)
  p2=self.client.patch('/api/notifications/',{'all':True},content_type='application/json')
  self.assertEqual(p2.status_code,200)
  self.assertEqual(p2.json()['unread_count'],0)
  n2.refresh_from_db()
  self.assertTrue(n2.read)
