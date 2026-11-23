"""Exercise real HTTP session/CSRF/email/enrolment flow, then remove only its own QA user."""
import os,json,uuid,http.cookiejar,urllib.request
os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings')
import django
django.setup()
from django.contrib.auth.models import User
email='woc-qa-'+uuid.uuid4().hex+'@example.test'
base='http://127.0.0.1:8317/api'
opener=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
token=''
def call(path,data=None):
 global token
 headers={'Content-Type':'application/json','Origin':'http://127.0.0.1:4317'}
 if token:headers['X-CSRFToken']=token
 req=urllib.request.Request(base+path,data=json.dumps(data).encode() if data is not None else None,headers=headers)
 result=json.load(opener.open(req,timeout=10))
 token=result.get('csrfToken',token)
 return result
try:
 call('/csrf/')
 registered=call('/register/',{'name':'Synthetic QA Student','email':email,'password':'Synthetic-QA-Only-2026!','age':20,'institution':'QA fixture','terms':True})
 verify_token=registered['development_verification_url'].split('token=',1)[1]
 call('/verify/',{'token':verify_token})
 signed_in=call('/login/',{'email':email,'password':'Synthetic-QA-Only-2026!'})
 assert signed_in['user']['email']==email
 created=call('/records/',{'program':'communication-skills','data':{}})
 assert created['status']=='enrolled'
 assert len(call('/records/')['results'])==1
 call('/logout/',{})
 print('PASS: real HTTP CSRF, registration, email verification, session login, enrollment, own records and logout.')
finally:
 User.objects.filter(username=email,email=email).delete()
