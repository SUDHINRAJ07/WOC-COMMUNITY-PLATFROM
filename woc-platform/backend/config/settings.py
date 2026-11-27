import os
from pathlib import Path
from dotenv import load_dotenv
BASE_DIR=Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR/'.env')
DEBUG=os.getenv('DEBUG','true').lower()=='true'
SECRET_KEY=os.getenv('DJANGO_SECRET_KEY','local-development-only-change-before-deployment')
if not DEBUG and SECRET_KEY.startswith('local-'): raise RuntimeError('Set DJANGO_SECRET_KEY for production')
raw_hosts = os.getenv('ALLOWED_HOSTS', '')
if raw_hosts:
    ALLOWED_HOSTS = [h.strip() for h in raw_hosts.split(',') if h.strip()]
else:
    ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'testserver', '[::1]']
    if DEBUG:
        ALLOWED_HOSTS.extend(['.trycloudflare.com', '*'])

INSTALLED_APPS=['django.contrib.admin','django.contrib.auth','django.contrib.contenttypes','django.contrib.sessions','django.contrib.messages','django.contrib.staticfiles','django_otp','django_otp.plugins.otp_totp','django_otp.plugins.otp_static','corsheaders','rest_framework','core']
MIDDLEWARE=['django.middleware.security.SecurityMiddleware','corsheaders.middleware.CorsMiddleware','django.contrib.sessions.middleware.SessionMiddleware','django.middleware.common.CommonMiddleware','django.middleware.csrf.CsrfViewMiddleware','django.contrib.auth.middleware.AuthenticationMiddleware','django_otp.middleware.OTPMiddleware','django.contrib.messages.middleware.MessageMiddleware','django.middleware.clickjacking.XFrameOptionsMiddleware']
ROOT_URLCONF='config.urls'
TEMPLATES=[{'BACKEND':'django.template.backends.django.DjangoTemplates','DIRS':[],'APP_DIRS':True,'OPTIONS':{'context_processors':['django.template.context_processors.request','django.contrib.auth.context_processors.auth','django.contrib.messages.context_processors.messages']}}]
WSGI_APPLICATION='config.wsgi.application'
if os.getenv('POSTGRES_DB'):
 DATABASES={'default':{'ENGINE':'django.db.backends.postgresql','NAME':os.getenv('POSTGRES_DB'),'USER':os.getenv('POSTGRES_USER'),'PASSWORD':os.getenv('POSTGRES_PASSWORD'),'HOST':os.getenv('POSTGRES_HOST','localhost'),'PORT':os.getenv('POSTGRES_PORT','5432')}}
else: DATABASES={'default':{'ENGINE':'django.db.backends.sqlite3','NAME':BASE_DIR/'db.sqlite3'}}
AUTH_PASSWORD_VALIDATORS=[{'NAME':'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},{'NAME':'django.contrib.auth.password_validation.MinimumLengthValidator'},{'NAME':'django.contrib.auth.password_validation.CommonPasswordValidator'},{'NAME':'django.contrib.auth.password_validation.NumericPasswordValidator'}]
LANGUAGE_CODE='en-in'
TIME_ZONE='Asia/Kolkata'
USE_TZ=True
STATIC_URL='/static/'
DEFAULT_AUTO_FIELD='django.db.models.BigAutoField'

FRONTEND_URL=os.getenv('FRONTEND_URL','http://localhost:4317')
raw_cors=os.getenv('CORS_ALLOWED_ORIGINS','')
if raw_cors:
    CORS_ALLOWED_ORIGINS=[o.strip() for o in raw_cors.split(',') if o.strip()]
else:
    CORS_ALLOWED_ORIGINS=['http://localhost:4317','http://127.0.0.1:4317','http://localhost:3000','http://127.0.0.1:3000']

if FRONTEND_URL and FRONTEND_URL not in CORS_ALLOWED_ORIGINS:
    CORS_ALLOWED_ORIGINS.append(FRONTEND_URL)

if DEBUG:
    CORS_ALLOWED_ORIGIN_REGEXES=[
        r"^https://.*\.trycloudflare\.com$",
        r"^http://192\.168\.\d{1,3}\.\d{1,3}(:\d+)?$",
        r"^http://10\.\d{1,3}\.\d{1,3}\.\d{1,3}(:\d+)?$",
        r"^http://172\.(1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3}(:\d+)?$",
        r"^http://localhost(:\d+)?$",
        r"^http://127\.0\.0\.1(:\d+)?$",
    ]

raw_csrf=os.getenv('CSRF_TRUSTED_ORIGINS','')
if raw_csrf:
    CSRF_TRUSTED_ORIGINS=[o.strip() for o in raw_csrf.split(',') if o.strip()]
else:
    CSRF_TRUSTED_ORIGINS=list(CORS_ALLOWED_ORIGINS)
    if DEBUG:
        CSRF_TRUSTED_ORIGINS.extend([
            'https://*.trycloudflare.com',
            'http://*.trycloudflare.com',
            'http://127.0.0.1:*',
            'http://localhost:*',
        ])

CORS_ALLOW_CREDENTIALS=True
SESSION_COOKIE_HTTPONLY=True
SESSION_COOKIE_SECURE=not DEBUG or os.getenv('SESSION_COOKIE_SECURE','false').lower()=='true'
CSRF_COOKIE_SECURE=not DEBUG or os.getenv('CSRF_COOKIE_SECURE','false').lower()=='true'
SESSION_COOKIE_SAMESITE=os.getenv('SESSION_COOKIE_SAMESITE','Lax')
CSRF_COOKIE_SAMESITE=os.getenv('CSRF_COOKIE_SAMESITE','Lax')
SECURE_PROXY_SSL_HEADER=('HTTP_X_FORWARDED_PROTO','https')
USE_X_FORWARDED_HOST=True
USE_X_FORWARDED_PORT=True
EMAIL_BACKEND=os.getenv('EMAIL_BACKEND','django.core.mail.backends.console.EmailBackend')
EMAIL_HOST=os.getenv('EMAIL_HOST','localhost')
EMAIL_PORT=int(os.getenv('EMAIL_PORT',587))
EMAIL_HOST_USER=os.getenv('EMAIL_HOST_USER','')
EMAIL_HOST_PASSWORD=os.getenv('EMAIL_HOST_PASSWORD','')
EMAIL_USE_TLS=os.getenv('EMAIL_USE_TLS','true').lower()=='true'
EMAIL_USE_SSL=os.getenv('EMAIL_USE_SSL','false').lower()=='true'
EMAIL_TIMEOUT=int(os.getenv('EMAIL_TIMEOUT',10))
DEFAULT_FROM_EMAIL=os.getenv('DEFAULT_FROM_EMAIL','THE WOC <noreply@woc.org>')
FRONTEND_URL=os.getenv('FRONTEND_URL','http://localhost:4317')
SMS_PROVIDER=os.getenv('SMS_PROVIDER','ninzasms')
WOC_LOCAL_SCREEN_OTP=os.getenv('WOC_LOCAL_SCREEN_OTP','false').lower()=='true'
EMAIL_VERIFICATION_REQUIRED=os.getenv('EMAIL_VERIFICATION_REQUIRED','false').lower()=='true'
EMAIL_SIGNUP_OTP_REQUIRED=os.getenv('EMAIL_SIGNUP_OTP_REQUIRED','false').lower()=='true'
SMS_DEV_MODE=os.getenv('SMS_DEV_MODE','false').lower()=='true'
SMS_TEST_MODE=os.getenv('SMS_TEST_MODE','false').lower()=='true'
NINZASMS_API_KEY=os.getenv('NINZASMS_API_KEY','')
NINZASMS_SENDER_ID=os.getenv('NINZASMS_SENDER_ID','16402')
NINZASMS_API_URL=os.getenv('NINZASMS_API_URL','https://ninzasms.in.net/auth/send_sms.php')
TWILIO_ACCOUNT_SID=os.getenv('TWILIO_ACCOUNT_SID','')
TWILIO_AUTH_TOKEN=os.getenv('TWILIO_AUTH_TOKEN','')
TWILIO_PHONE_NUMBER=os.getenv('TWILIO_PHONE_NUMBER','')
MSG91_AUTH_KEY=os.getenv('MSG91_AUTH_KEY','')
MSG91_SENDER_ID=os.getenv('MSG91_SENDER_ID','WOCIND')
MSG91_TEMPLATE_ID=os.getenv('MSG91_TEMPLATE_ID','')
GOOGLE_CLIENT_ID=os.getenv('GOOGLE_CLIENT_ID','')
FIREBASE_PROJECT_ID=os.getenv('FIREBASE_PROJECT_ID','woc-29231')
FIREBASE_PHONE_MAX_AGE=300
GOOGLE_CLIENT_SECRET=os.getenv('GOOGLE_CLIENT_SECRET','')
GOOGLE_REDIRECT_URI=os.getenv('GOOGLE_REDIRECT_URI',f"{FRONTEND_URL}/verify/?google_callback=true")
REST_FRAMEWORK={'DEFAULT_AUTHENTICATION_CLASSES':['core.auth.CsrfSessionAuthentication'],'DEFAULT_PERMISSION_CLASSES':['rest_framework.permissions.IsAuthenticatedOrReadOnly'],'DEFAULT_THROTTLE_CLASSES':['rest_framework.throttling.AnonRateThrottle','rest_framework.throttling.UserRateThrottle'],'DEFAULT_THROTTLE_RATES':{'anon':'100/hour','user':'1000/hour'}}
CELERY_BROKER_URL=os.getenv('REDIS_URL','redis://localhost:6379/0')
SECURE_CONTENT_TYPE_NOSNIFF=True
X_FRAME_OPTIONS='DENY'
LOGGING={'version':1,'disable_existing_loggers':False,'handlers':{'console':{'class':'logging.StreamHandler'}},'root':{'handlers':['console'],'level':'INFO'}}

# Private uploads are served only through authenticated, ownership-checked APIs.
MEDIA_ROOT=os.getenv("WOC_PRIVATE_UPLOAD_ROOT",str(BASE_DIR / "private-uploads"))
FILE_UPLOAD_MAX_MEMORY_SIZE=5*1024*1024
DATA_UPLOAD_MAX_MEMORY_SIZE=6*1024*1024

# Password-only superuser preview access is explicitly opt-in and loopback-only.
WOC_LOCAL_ADMIN_PASSWORD_LOGIN=os.getenv("WOC_LOCAL_ADMIN_PASSWORD_LOGIN","false").lower()=="true"
