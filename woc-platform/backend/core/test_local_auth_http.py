import json
from http.cookiejar import CookieJar
from urllib.request import build_opener, HTTPCookieProcessor, Request
from urllib.error import HTTPError
from django.test import LiveServerTestCase, override_settings
from django.contrib.auth.models import User


@override_settings(DEBUG=True,WOC_LOCAL_SCREEN_OTP=True,EMAIL_VERIFICATION_REQUIRED=False)
class LocalAuthHTTPTests(LiveServerTestCase):
 def test_real_http_email_and_phone_sessions(self):
  browser=build_opener(HTTPCookieProcessor(CookieJar()))
  def get(path):
   with browser.open(self.live_server_url+'/api/'+path,timeout=10) as response:
    return json.load(response)
  def post(path,data):
   csrf=get('csrf/')['csrfToken']
   request=Request(self.live_server_url+'/api/'+path,data=json.dumps(data).encode(),headers={'Content-Type':'application/json','X-CSRFToken':csrf},method='POST')
   with browser.open(request,timeout=10) as response:
    return json.load(response)
  account={'name':'HTTP Student','email':'http-local@example.test','password':'HTTPStrongPass!2035','age':21,'institution':'College','terms':True}
  self.assertFalse(post('register/',account)['requires_email_verification'])
  signed_in=post('login/',{'email':account['email'],'password':account['password']})
  self.assertEqual(get('me/')['user']['id'],signed_in['user']['id'])
  post('logout/',{})
  with self.assertRaises(HTTPError) as logged_out:
   get('me/')
  self.assertEqual(logged_out.exception.code,403)
  self.assertEqual(post('login/',{'email':account['email'],'password':account['password']})['user']['id'],signed_in['user']['id'])
  post('logout/',{})
  proof=post('phone/send-otp/',{'phone':'9876543219','country_code':'+91','purpose':'register'})
  mobile=post('auth/phone/',{**account,'challenge_id':proof['challenge_id'],'otp':proof['development_otp'],'action':'register'})
  self.assertEqual(get('me/')['user']['id'],mobile['user']['id'])
  self.assertTrue(User.objects.get(pk=mobile['user']['id']).profile.phone_verified)
  self.assertEqual(User.objects.count(),2)
