import io
import json
from unittest.mock import MagicMock,patch
from django.core.cache import cache
from django.core.management import call_command,CommandError
from django.test import TestCase,override_settings
from core.auth_services import send_sms_otp,MessageDeliveryError
from core.models import PhoneOTPChallenge


@override_settings(SMS_PROVIDER='ninzasms',SMS_TEST_MODE=False,SMS_DEV_MODE=False,WOC_LOCAL_SCREEN_OTP=False,NINZASMS_API_KEY='private-test-token',NINZASMS_SENDER_ID='123',NINZASMS_API_URL='https://ninzasms.in.net/auth/send_sms.php')
class LiveOTPConfigurationTests(TestCase):
 def setUp(self):
  cache.clear()
 def response(self,payload):
  response=MagicMock()
  response.read.return_value=json.dumps(payload).encode()
  response.__enter__.return_value=response
  return response
 def test_documented_success_and_legacy_success(self):
  for payload in [{'status':1,'msg':'OTP Sent Successfully'},{'return':True,'message':'Accepted'}]:
   with patch('urllib.request.urlopen',return_value=self.response(payload)):
    self.assertEqual(send_sms_otp('+919876543210','123456')['mode'],'live')
 def test_documented_failure_never_claims_sent(self):
  for payload,expected in [({'status':0,'msg':'Insufficient balance'},'balance'),({'status':0,'msg':'Invalid API Key'},'authentication'),({'status':0,'return':True,'msg':'Gateway unavailable'},'could not')]:
   with patch('urllib.request.urlopen',return_value=self.response(payload)):
    with self.assertRaisesRegex(MessageDeliveryError,expected):send_sms_otp('+919876543210','123456')
 def test_unknown_or_malformed_response_fails_closed(self):
  for payload in [{},[],None,{'msg':'Unknown'},{'status':'unknown'}]:
   with patch('urllib.request.urlopen',return_value=self.response(payload)):
    with self.assertRaises(MessageDeliveryError):send_sms_otp('+919876543210','123456')
  response=self.response({});response.read.return_value=b'<html>Gateway error</html>'
  with patch('urllib.request.urlopen',return_value=response):
   with self.assertRaises(MessageDeliveryError):send_sms_otp('+919876543210','123456')
 def test_failed_request_invalidates_challenge(self):
  with patch('urllib.request.urlopen',return_value=self.response({'status':0,'msg':'Invalid API Key'})):
   response=self.client.post('/api/phone/send-otp/',{'phone':'9876543210','country_code':'+91','purpose':'register'},content_type='application/json')
  self.assertEqual(response.status_code,503)
  self.assertNotIn('challenge_id',response.json())
  self.assertFalse(PhoneOTPChallenge.objects.filter(consumed_at__isnull=True).exists())
 def test_explicit_sender_required(self):
  with self.settings(NINZASMS_SENDER_ID=''):
   with patch('urllib.request.urlopen') as request:
    with self.assertRaises(MessageDeliveryError):send_sms_otp('+919876543210','123456')
    request.assert_not_called()
 def test_config_command_does_not_expose_secrets_or_send(self):
  with self.settings(EMAIL_BACKEND='django.core.mail.backends.smtp.EmailBackend',EMAIL_HOST='smtp.gmail.com',EMAIL_HOST_USER='sender@example.com',EMAIL_HOST_PASSWORD='secret-mail-password',EMAIL_PORT=587,EMAIL_USE_TLS=True,EMAIL_USE_SSL=False,EMAIL_SIGNUP_OTP_REQUIRED=True):
   output=io.StringIO()
   with patch('urllib.request.urlopen') as sms,patch('django.core.mail.backends.smtp.EmailBackend.open') as smtp:
    call_command('check_otp_config',stdout=output)
    sms.assert_not_called();smtp.assert_not_called()
   self.assertNotIn('private-test-token',output.getvalue())
   self.assertNotIn('secret-mail-password',output.getvalue())
   with self.settings(NINZASMS_API_KEY=''):
    with self.assertRaises(CommandError):call_command('check_otp_config',stdout=io.StringIO())
 def test_resend_rejects_invalid_email_syntax(self):
  response=self.client.post('/api/email/resend-otp/',{'email':'bad@invalid..com'},content_type='application/json')
  self.assertEqual(response.status_code,400)
