import hashlib
import secrets
from datetime import timedelta
from django.contrib.auth import authenticate,login,logout
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core import signing
from django.conf import settings
from django.db import transaction,IntegrityError
from django.middleware.csrf import get_token
from django.views.decorators.csrf import csrf_protect
from django.utils import timezone
from rest_framework.decorators import api_view,permission_classes,throttle_classes
from rest_framework.permissions import AllowAny,IsAuthenticated,IsAdminUser
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle,UserRateThrottle
from django.contrib.auth.hashers import make_password,check_password
from .models import *
from .auth_services import (
 send_verification_email,send_email_otp,send_welcome_email,send_password_reset_email,log_auth_event,
 send_registration_confirmation_email,send_status_update_email,create_in_app_notification,
 normalize_phone_number,mask_phone_number,generate_secure_otp,send_sms_otp,get_client_ip,
 build_google_auth_url,verify_google_id_token,exchange_google_code,handle_google_user,
 AccountLinkingRequiredError,MessageDeliveryError
)


class OTPRateThrottle(AnonRateThrottle):
 scope='otp_requests'
 rate='20/hour'

def program_data(p):
 return {k:getattr(p,k) for k in ['slug','module','title','description','category','location','duration','level','capacity','sample','verified','details']}|{'fee':str(p.fee)}
def record_data(r):
 return {'id':str(r.id),'program':program_data(r.program),'status':r.status,'data':r.data,'created_at':r.created_at,'certificate':str(r.certificate.id) if hasattr(r,'certificate') else None,'student':r.user.first_name,'email':r.user.email}
def user_data(u):
 p=u.profile
 from .organization_access import access_context
 authorization=access_context(u)
 return {
  'id':u.id,
  'name':u.first_name,
  'email':u.email,
  'institution':p.institution,
  'age':p.age,
  'bio':p.bio,
  'city':p.city,
  'qualification':p.qualification,
  'skills':p.skills if isinstance(p.skills,list) else [],
  'interests':p.interests if isinstance(p.interests,list) else [],
  'career_goals':p.career_goals,
  'resume_url':p.resume_url,
  'graduation_year':p.graduation_year,
  'has_photo':bool(p.photo),'has_resume':bool(p.resume_file),'has_supporting_document':bool(p.supporting_document),
  'linkedin_url':p.linkedin_url,
  'github_url':p.github_url,
  'roles':authorization['roles'],
  'authorization':authorization,
  'is_staff':u.is_staff,
  'email_verified':p.email_verified,
  'email_verified_at':p.email_verified_at.isoformat() if p.email_verified_at else None,
  'phone_number':p.phone_number,
  'phone_verified':p.phone_verified,
  'phone_verified_at':p.phone_verified_at.isoformat() if p.phone_verified_at else None,
  'auth_provider':p.auth_provider,
  'notification_preferences':p.notification_preferences
 }

@api_view(['GET'])
@permission_classes([AllowAny])
def csrf(request): return Response({'csrfToken':get_token(request),'mode':'local-backend'})

@csrf_protect
@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
 d=request.data
 email=str(d.get('email','')).strip().lower()
 name=str(d.get('name','')).strip()
 company_signup=d.get('organization_kind')=='company'
 try: age=None if company_signup and not d.get('age') else int(d.get('age',0))
 except (ValueError,TypeError): return Response({'error':'Enter a valid age.'},status=400)
 if not name or '@' not in email or len(email)>254: return Response({'error':'A name and valid email are required.'},status=400)
 if age is not None and (age<13 or age>100): return Response({'error':'Membership is available from age 13.'},status=400)
 if age is not None and age<18 and not d.get('guardian_consent'): return Response({'error':'School and guardian permission is required for under-18 participation.'},status=400)
 if company_signup and 'confirm_password' in d and d.get('confirm_password')!=d.get('password'):
  return Response({'error':'Passwords do not match.'},status=400)
 if not d.get('terms'): return Response({'error':'Please accept the terms and privacy notice.'},status=400)
 try: validate_password(d.get('password',''))
 except ValidationError as exc: return Response({'error':' '.join(exc.messages)},status=400)
 organization_data=None
 organization_kind=d.get('organization_kind')
 if organization_kind:
  if organization_kind not in ['college','company'] or (age is not None and age<18):
   return Response({'error':'Choose College or Company and an administrator aged 18 or above.'},status=400)
  from .organization_serializers import CollegeOnboardingSerializer,CompanyOnboardingSerializer
  serializer=(CollegeOnboardingSerializer if organization_kind=='college' else CompanyOnboardingSerializer)(data=d.get('organization',{}))
  serializer.is_valid(raise_exception=True)
  organization_data=serializer.validated_data
 try:
  with transaction.atomic():
   u=User.objects.create_user(email,email,d['password'],first_name=name)
   Profile.objects.create(
    user=u,
    age=age,
    guardian_consent=bool(d.get('guardian_consent')),
    institution=str(d.get('institution',''))[:200],
    roles=['student'],
    auth_provider='local',
    email_verified=False
   )
   if organization_data is not None:
    from .models import Institution,Company,CollegeMembership,CompanyMembership
    if organization_kind=='college':
     org=Institution.objects.create(owner=u,**organization_data)
     CollegeMembership.objects.create(user=u,institution=org,role=CollegeMembership.Role.ADMIN)
    else:
     org=Company.objects.create(created_by=u,**organization_data)
     CompanyMembership.objects.create(user=u,company=org)
    AuthAuditLog.objects.create(user=u,event_type=organization_kind+'_onboarding_requested',metadata={'organization_id':str(org.pk),'source':'registration'})
 except IntegrityError: return Response({'error':'An account already exists with this email.'},status=400)
 if not settings.EMAIL_VERIFICATION_REQUIRED:
  create_in_app_notification(u,'Welcome to WOC. Your account is ready. Sign in with your email and password.')
  log_auth_event(u,'registered',request)
  return Response({'message':'Account created. You can now sign in with your email and password.','requires_email_verification':False},status=201)
 try: url=send_verification_email(u,request)
 except MessageDeliveryError as exc:
  return Response({'message':'Your account was created. Verify your email before signing in.','delivery_status':'failed','delivery_error':str(exc)},status=201)
 log_auth_event(u,'registered',request)
 result={'message':'Account created. Check your email for verification.'}
 if settings.DEBUG: result['development_verification_url']=url
 return Response(result,status=201)

@csrf_protect
@api_view(['POST'])
@permission_classes([AllowAny])
def verify(request):
 token=str(request.data.get('token','')).strip()
 if not token: return Response({'error':'Verification token is required.'},status=400)
 try:
  payload=signing.loads(token,salt='verify-email',max_age=86400)
  p=Profile.objects.select_related('user').get(user_id=payload['user'])
 except (signing.BadSignature,Profile.DoesNotExist):
  return Response({'error':'Invalid or expired verification link.'},status=400)
 if p.email_verified and p.email_verified_at is not None:
  return Response({'error':'This verification link has already been used. Please sign in.'},status=400)
 p.email_verified=True
 p.email_verified_at=timezone.now()
 p.save()
 log_auth_event(p.user,'email_verified',request)
 send_welcome_email(p.user)
 return Response({'message':'Email verified successfully. You can now sign in.','email':p.user.email})

@csrf_protect
@api_view(['POST'])
@permission_classes([AllowAny])
def resend_verification(request):
 email=str(request.data.get('email','')).strip().lower()
 if not email or '@' not in email: return Response({'error':'Enter a valid email address.'},status=400)
 u=User.objects.filter(email=email).first()
 if not u or not hasattr(u,'profile'):
  return Response({'message':'If an unverified account exists with this email, a verification link has been sent.'})
 if u.profile.email_verified:
  return Response({'error':'This email address is already verified. Please sign in.'},status=400)
 recent=EmailDeliveryLog.objects.filter(
  recipient=email,
  template_name='email_verification',status='sent',
  created_at__gte=timezone.now()-timedelta(seconds=60)
 ).first()
 if recent:
  return Response({'error':'Please wait 60 seconds before requesting another verification email.'},status=429)
 try: url=send_verification_email(u,request)
 except MessageDeliveryError as exc: return Response({'error':str(exc)},status=503)
 log_auth_event(u,'verification_resent',request)
 result={'message':'A fresh verification link has been sent to your email.'}
 if settings.DEBUG: result['development_verification_url']=url
 return Response(result,status=200)

def _is_live_sms_mode():
 provider=getattr(settings,'SMS_PROVIDER','ninzasms').lower()
 test_mode=getattr(settings,'SMS_TEST_MODE',False)
 return provider in ['ninzasms','msg91','twilio'] and not test_mode


def _local_phone_error(request):
 # Screen-visible OTP is deliberately restricted to direct local development when live SMS is off.
 from urllib.parse import urlsplit
 if _is_live_sms_mode():
  return None
 if not settings.WOC_LOCAL_SCREEN_OTP:
  return Response({'error':'Local on-screen OTP is disabled.'},status=410)
 host=urlsplit('http://'+request.META.get('HTTP_HOST','')).hostname
 forwarded=any(request.META.get(key) for key in ['HTTP_X_FORWARDED_FOR','HTTP_X_FORWARDED_HOST','HTTP_X_FORWARDED_PROTO'])
 if not settings.DEBUG or request.META.get('REMOTE_ADDR') not in ['127.0.0.1','::1'] or host not in ['127.0.0.1','localhost','::1'] or forwarded:
  return Response({'error':'On-screen OTP is available only on direct localhost development. No SMS was sent.'},status=403)
 return None


def _handle_send_phone_otp(request):
 disabled=_local_phone_error(request)
 if disabled is not None: return disabled
 raw_phone=request.data.get('phone','')
 purpose=request.data.get('purpose','verification')
 if purpose not in ['verification','login','register']: return Response({'error':'Choose a valid verification flow.'},status=400)
 if purpose=='verification' and not request.user.is_authenticated: return Response({'error':'Sign in before linking a mobile number.'},status=403)
 try: normalized=normalize_phone_number(raw_phone,default_country=str(request.data.get('country_code','+91')))
 except ValueError as exc: return Response({'error':str(exc)},status=400)
 if PhoneOTPChallenge.objects.filter(phone_number=normalized,created_at__gte=timezone.now()-timedelta(seconds=60)).exists():
  return Response({'error':'Please wait 60 seconds before requesting another OTP.'},status=429)
 otp=generate_secure_otp()
 PhoneOTPChallenge.objects.filter(phone_number=normalized,consumed_at__isnull=True).update(consumed_at=timezone.now())
 previous=request.session.get('woc_phone_challenge')
 if previous: PhoneOTPChallenge.objects.filter(id=previous,consumed_at__isnull=True).update(consumed_at=timezone.now())
 challenge=PhoneOTPChallenge.objects.create(phone_number=normalized,otp_hash=make_password(otp),expires_at=timezone.now()+timedelta(minutes=5),ip_address=get_client_ip(request),purpose=purpose,user=request.user if request.user.is_authenticated else None)
 request.session['woc_phone_challenge']=str(challenge.id)
 if _is_live_sms_mode():
  try:
   send_sms_otp(normalized,otp)
  except MessageDeliveryError as exc:
   challenge.consumed_at=timezone.now();challenge.save(update_fields=['consumed_at'])
   return Response({'error':str(exc)},status=503)
  log_auth_event(request.user if request.user.is_authenticated else None,'phone_otp_sent',request,metadata={'phone':mask_phone_number(normalized),'purpose':purpose})
  return Response({'message':'A 6-digit verification code has been sent to your mobile number.','challenge_id':str(challenge.id),'phone':normalized,'expires_in':300,'delivery_mode':'live'})
 res={'message':'Local development OTP is shown below. No SMS was sent.','challenge_id':str(challenge.id),'phone':normalized,'expires_in':300,'delivery_mode':'test','development_otp':otp}
 return Response(res)

@csrf_protect
@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([OTPRateThrottle,UserRateThrottle])
def send_phone_otp(request):
 return _handle_send_phone_otp(request)

@csrf_protect
@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([OTPRateThrottle,UserRateThrottle])
def resend_phone_otp(request):
 return _handle_send_phone_otp(request)

@csrf_protect
@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([OTPRateThrottle,UserRateThrottle])
def verify_phone_otp(request):
 disabled=_local_phone_error(request)
 if disabled is not None: return disabled
 if not request.data.get('challenge_id') or str(request.data.get('challenge_id'))!=request.session.get('woc_phone_challenge'): return Response({'error':'Request a new OTP in this browser.'},status=400)
 if not request.user.is_authenticated: return Response({'error':'Sign in before linking a mobile number.'},status=403)
 with transaction.atomic():
  try: challenge=PhoneOTPChallenge.objects.select_for_update().get(id=request.data.get('challenge_id'))
  except (PhoneOTPChallenge.DoesNotExist,ValueError,ValidationError): return Response({'error':'Invalid verification challenge.'},status=400)
  error=_phone_challenge_error(challenge,request.data.get('otp'),'verification',request.user)
  if error: return Response({'error':error},status=400)
  if Profile.objects.filter(phone_number=challenge.phone_number).exclude(user=request.user).exists(): return Response({'error':'This number is already linked to another account.'},status=409)
  try:
   with transaction.atomic():
    p=request.user.profile;p.phone_number=challenge.phone_number;p.phone_verified=True;p.phone_verified_at=timezone.now();p.save()
  except IntegrityError: return Response({'error':'This number is already linked to another account.'},status=409)
  challenge.consumed_at=timezone.now();challenge.save()
  log_auth_event(request.user,'phone_verified',request,metadata={'phone':mask_phone_number(challenge.phone_number)})
 return Response({'message':'Mobile number verified.','phone':challenge.phone_number,'phone_verified':True})


def _phone_challenge_error(challenge, otp, purpose, user=None):
 if challenge.purpose!=purpose: return 'This code belongs to a different verification flow.'
 if challenge.user_id and (not user or challenge.user_id!=user.id): return 'This code belongs to another account.'
 if challenge.consumed_at: return 'This OTP has already been used.'
 if timezone.now()>challenge.expires_at: return 'This OTP has expired. Please request a new code.'
 if challenge.attempts>=5: return 'Maximum verification attempts exceeded. Please request a new OTP.'
 if not check_password(str(otp or ''),challenge.otp_hash):
  challenge.attempts+=1;challenge.save(update_fields=['attempts'])
  return f'Incorrect OTP. {max(0,5-challenge.attempts)} attempt(s) remaining.' if challenge.attempts<5 else 'Maximum verification attempts exceeded. Please request a new OTP.'
 return None


@csrf_protect
@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([OTPRateThrottle,UserRateThrottle])
def send_email_otp_view(request):
 raw_email=str(request.data.get('email','')).strip().lower()
 if request.user.is_authenticated:
  email=(request.user.email or '').strip().lower()
  if raw_email and raw_email!=email:
   return Response({'error':'You can only verify your own registered email address.'},status=403)
  u=request.user
 else:
  email=raw_email
  if not email or '@' not in email or len(email)>254:
   return Response({'error':'Enter a valid email address.'},status=400)
  u=User.objects.filter(email=email).first()
  if not u or not hasattr(u,'profile'):
   return Response({'message':'If an unverified account exists with this email, a 6-digit verification code has been sent.','expires_in':300},status=200)
 if hasattr(u,'profile') and u.profile.email_verified:
  if request.user.is_authenticated:
   return Response({'error':'Your email address is already verified.'},status=400)
  return Response({'message':'If an unverified account exists with this email, a 6-digit verification code has been sent.','expires_in':300},status=200)
 if EmailOTPChallenge.objects.filter(email=email,created_at__gte=timezone.now()-timedelta(seconds=60)).exists():
  return Response({'error':'Please wait 60 seconds before requesting another email OTP.'},status=429)
 otp=generate_secure_otp()
 EmailOTPChallenge.objects.filter(email=email,consumed_at__isnull=True).update(consumed_at=timezone.now())
 challenge=EmailOTPChallenge.objects.create(email=email,otp_hash=make_password(otp),expires_at=timezone.now()+timedelta(minutes=5),ip_address=get_client_ip(request),purpose='verification',user=u)
 try:
  send_email_otp(email,otp,user=u)
 except MessageDeliveryError as exc:
  challenge.consumed_at=timezone.now();challenge.save(update_fields=['consumed_at'])
  return Response({'error':str(exc)},status=503)
 log_auth_event(u,'email_otp_sent',request,metadata={'email':email})
 return Response({'message':'A 6-digit verification code has been sent to your email address.','challenge_id':str(challenge.id),'expires_in':300},status=200)


@csrf_protect
@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([OTPRateThrottle,UserRateThrottle])
def verify_email_otp_view(request):
 challenge_id=request.data.get('challenge_id')
 email=str(request.data.get('email','')).strip().lower()
 otp=str(request.data.get('otp','')).strip()
 if not otp or len(otp)!=6 or not otp.isdigit():
  return Response({'error':'Enter a valid 6-digit verification code.'},status=400)
 with transaction.atomic():
  if challenge_id:
   try: challenge=EmailOTPChallenge.objects.select_for_update().get(id=challenge_id)
   except (EmailOTPChallenge.DoesNotExist,ValueError,ValidationError): return Response({'error':'Invalid email verification challenge.'},status=400)
  elif request.user.is_authenticated:
   challenge=EmailOTPChallenge.objects.select_for_update().filter(user=request.user,consumed_at__isnull=True).order_by('-created_at').first()
   if not challenge: return Response({'error':'No active email verification code found. Please request a new code.'},status=400)
  elif email:
   challenge=EmailOTPChallenge.objects.select_for_update().filter(email=email,consumed_at__isnull=True).order_by('-created_at').first()
   if not challenge: return Response({'error':'Invalid or expired verification code.'},status=400)
  else:
   return Response({'error':'Challenge ID or email is required.'},status=400)
  if challenge.user_id and request.user.is_authenticated and challenge.user_id!=request.user.id:
   return Response({'error':'This code belongs to another account.'},status=403)
  if challenge.consumed_at:
   return Response({'error':'This OTP has already been used.'},status=400)
  if timezone.now()>challenge.expires_at:
   return Response({'error':'This OTP has expired. Please request a new code.'},status=400)
  if challenge.attempts>=5:
   return Response({'error':'Maximum verification attempts exceeded. Please request a new OTP.'},status=400)
  if not check_password(otp,challenge.otp_hash):
   challenge.attempts+=1;challenge.save(update_fields=['attempts'])
   msg=f'Incorrect OTP. {max(0,5-challenge.attempts)} attempt(s) remaining.' if challenge.attempts<5 else 'Maximum verification attempts exceeded. Please request a new OTP.'
   return Response({'error':msg},status=400)
  u=challenge.user or User.objects.filter(email=challenge.email).first()
  if not u or not hasattr(u,'profile'):
   return Response({'error':'Account not found.'},status=404)
  u.profile.email_verified=True
  u.profile.email_verified_at=timezone.now()
  u.profile.save(update_fields=['email_verified','email_verified_at'])
  challenge.consumed_at=timezone.now()
  challenge.save(update_fields=['consumed_at'])
  log_auth_event(u,'email_verified',request,metadata={'method':'otp'})
 send_welcome_email(u)
 return Response({'message':'Email verified successfully.','email':u.email,'email_verified':True},status=200)


@csrf_protect
@api_view(['POST'])
@permission_classes([AllowAny])
def phone_auth(request):
 disabled=_local_phone_error(request)
 if disabled is not None: return disabled
 if not request.data.get('challenge_id') or str(request.data.get('challenge_id'))!=request.session.get('woc_phone_challenge'): return Response({'error':'Request a new OTP in this browser.'},status=400)
 action=request.data.get('action')
 if action not in ['login','register']: return Response({'error':'Choose sign in or create account.'},status=400)
 if action=='register':
  name=str(request.data.get('name','')).strip();institution=str(request.data.get('institution','')).strip()
  try: age=int(request.data.get('age',0))
  except (ValueError,TypeError): return Response({'error':'Enter a valid age.'},status=400)
  if not name or len(name)>150 or not institution or len(institution)>200: return Response({'error':'Enter your name and institution.'},status=400)
  if not 13<=age<=100: return Response({'error':'Membership is available from age 13.'},status=400)
  if not request.data.get('terms'): return Response({'error':'Accept the terms and privacy notice.'},status=400)
  if age<18 and not request.data.get('guardian_consent'): return Response({'error':'School and guardian permission is required.'},status=400)
 with transaction.atomic():
  try: challenge=PhoneOTPChallenge.objects.select_for_update().get(id=request.data.get('challenge_id'))
  except (PhoneOTPChallenge.DoesNotExist,ValueError,ValidationError): return Response({'error':'Invalid verification challenge.'},status=400)
  error=_phone_challenge_error(challenge,request.data.get('otp'),action,request.user if request.user.is_authenticated else None)
  if error: return Response({'error':error},status=400)
  profile=Profile.objects.select_related('user').filter(phone_number=challenge.phone_number,phone_verified=True).first()
  if action=='login':
   if not profile: return Response({'error':'No account is linked to this number. Create a mobile account first.'},status=400)
   user=profile.user
   if not user.is_active or user.is_staff or user.is_superuser: return Response({'error':'Please use email sign-in for this account.'},status=403)
  else:
   if profile: return Response({'error':'An account already uses this number. Please sign in.'},status=409)
   try:
    with transaction.atomic():
     user=User.objects.create_user(username='phone:'+challenge.phone_number,first_name=name)
     user.set_unusable_password();user.save()
     Profile.objects.create(user=user,age=age,institution=institution,guardian_consent=bool(request.data.get('guardian_consent')),roles=['student'],auth_provider='phone',phone_number=challenge.phone_number,phone_verified=True,phone_verified_at=timezone.now())
   except IntegrityError: return Response({'error':'An account already uses this number. Please sign in.'},status=409)
   create_in_app_notification(user,'Welcome to WOC. Your mobile number is verified.')
  challenge.consumed_at=timezone.now();challenge.save(update_fields=['consumed_at'])
 login(request,user)
 log_auth_event(user,'phone_'+action,request)
 return Response({'user':user_data(user),'csrfToken':get_token(request)})

@api_view(['GET'])
@permission_classes([AllowAny])
def google_auth_url(request):
 try: return Response({'url':build_google_auth_url(request),'configured':True})
 except ValueError as exc: return Response({'error':str(exc),'configured':False})

@csrf_protect
@api_view(['POST'])
@permission_classes([AllowAny])
def google_auth(request):
 link_password=request.data.get('link_password')
 link_token=request.data.get('link_token')
 try:
  if link_token:
   pending=request.session.get('google_link_pending',{})
   signing.loads(link_token,salt='google-link',max_age=600)
   if not secrets.compare_digest(str(pending.get('token','')),str(link_token)): raise ValueError('Restart Google sign-in to link your account.')
   google_info=pending['info']
  elif request.data.get('id_token'):
   google_info=verify_google_id_token(request.data['id_token'])
  elif request.data.get('code'):
   state=str(request.data.get('state',''));expected=request.session.pop('google_oauth_state','')
   if not state or not expected or not secrets.compare_digest(state,expected): raise ValueError('Google sign-in expired. Please start again.')
   signing.loads(state,salt='google-oauth-state',max_age=600)
   google_info=exchange_google_code(request.data['code'],request.data.get('redirect_uri'))
  else: raise ValueError('Google credentials are required.')
 except (ValueError,KeyError,signing.BadSignature):
  return Response({'error':'Google sign-in could not be verified. Please start again.'},status=400)
 if User.objects.filter(email=google_info['email'],is_staff=True).exists(): return Response({'error':'Staff must sign in using email and their authenticator code.'},status=403)
 try:
  user,action=handle_google_user(google_info,link_password=link_password,current_user=request.user)
 except AccountLinkingRequiredError as exc:
  ticket=signing.dumps({'nonce':secrets.token_urlsafe(24)},salt='google-link')
  request.session['google_link_pending']={'token':ticket,'info':google_info}
  return Response({'error':str(exc),'action':'require_link_password','email':exc.email,'link_token':ticket},status=409)
 except ValueError as exc: return Response({'error':str(exc)},status=400)
 if not user.is_active or user.is_staff: return Response({'error':'Use email sign-in for this account.'},status=403)
 request.session.pop('google_link_pending',None)
 login(request,user)
 log_auth_event(user,f'google_auth_{action}',request)
 return Response({'user':user_data(user),'csrfToken':get_token(request),'action':action})

@csrf_protect
@api_view(['POST'])
@permission_classes([AllowAny])
def sign_in(request):
 email=str(request.data.get('email','')).strip()
 password=request.data.get('password','')
 # Prefer a unique username; email fallback must never choose between accounts.
 candidates=User.objects.filter(username__iexact=email)
 if candidates.count()!=1:
  candidates=User.objects.filter(email__iexact=email)
 identity=candidates.first() if candidates.count()==1 else None
 u=authenticate(username=identity.username,password=password) if identity else None
 if not u:
  log_auth_event(None,'login_failed',request,metadata={'email':email})
  return Response({'error':'Username/email or password is incorrect.'},status=400)
 # Explicitly enabled local preview mode; never applies over a proxy or in production.
 import ipaddress
 try:
  local_request=(ipaddress.ip_address(request.META.get('REMOTE_ADDR','')).is_loopback and request.get_host().split(':')[0] in ['127.0.0.1','localhost'])
 except ValueError:local_request=False
 forwarded=any(request.META.get(key) for key in ['HTTP_X_FORWARDED_FOR','HTTP_X_FORWARDED_HOST','HTTP_X_FORWARDED_PROTO','HTTP_FORWARDED'])
 local_admin=bool(settings.DEBUG and getattr(settings,'WOC_LOCAL_ADMIN_PASSWORD_LOGIN',False) and u.is_superuser and local_request and not forwarded)
 if not hasattr(u,'profile') or (settings.EMAIL_VERIFICATION_REQUIRED and not u.profile.email_verified and not local_admin):
  log_auth_event(u,'login_blocked_unverified',request)
  return Response({'error':'Verify your email first.'},status=403)
 device=None
 if u.is_staff and not local_admin:
  from django_otp.plugins.otp_totp.models import TOTPDevice
  device=next((d for d in TOTPDevice.objects.filter(user=u,confirmed=True) if d.verify_token(request.data.get('otp',''))),None)
  if not device:
   log_auth_event(u,'login_mfa_failed',request)
   return Response({'error':'A valid admin authenticator code is required.','requires_staff_mfa':True},status=403)
 login(request,u)
 if device:
  from django_otp import login as otp_login
  otp_login(request,device)
 if local_admin:log_auth_event(u,'local_admin_password_login',request)
 log_auth_event(u,'login_success',request)
 return Response({'user':user_data(u),'csrfToken':get_token(request)})

@api_view(['POST'])
@permission_classes([AllowAny])
def sign_out(request):
 if request.user.is_authenticated:
  log_auth_event(request.user,'logout',request)
 logout(request);return Response({'message':'Signed out.'})

@csrf_protect
@api_view(['POST'])
@permission_classes([AllowAny])
def request_password_reset(request):
 email=str(request.data.get('email','')).strip().lower()
 if not email or '@' not in email or len(email)>254:
  return Response({'error':'Enter a valid email address.'},status=400)
 user=User.objects.filter(email=email).first()
 if not user:
  return Response({'message':'If an account exists with this email address, a password reset link has been sent.'},status=200)
 recent=PasswordResetToken.objects.filter(user=user,created_at__gte=timezone.now()-timedelta(seconds=60)).first()
 if recent:
  return Response({'error':'Please wait 60 seconds before requesting another password reset.'},status=429)
 try: url=send_password_reset_email(user,request)
 except MessageDeliveryError as exc: return Response({'error':str(exc)},status=503)
 log_auth_event(user,'password_reset_requested',request,metadata={'email':email})
 result={'message':'If an account exists with this email address, a password reset link has been sent.'}
 if settings.DEBUG:
  result['development_reset_url']=url
 return Response(result,status=200)

@csrf_protect
@api_view(['POST'])
@permission_classes([AllowAny])
def confirm_password_reset(request):
 token=str(request.data.get('token','')).strip()
 password=request.data.get('password','')
 confirm_password=request.data.get('confirm_password')
 if not token:
  return Response({'error':'Password reset token is required.'},status=400)
 if confirm_password is not None and password!=confirm_password:
  return Response({'error':'Passwords do not match.'},status=400)
 token_hash=hashlib.sha256(token.encode('utf-8')).hexdigest()
 reset_token=PasswordResetToken.objects.select_related('user__profile').filter(token_hash=token_hash).first()
 if not reset_token:
  return Response({'error':'Invalid or expired password reset link.'},status=400)
 if reset_token.used:
  return Response({'error':'This password reset link has already been used. Please request a new one.'},status=400)
 if timezone.now()>reset_token.expires_at:
  return Response({'error':'This password reset link has expired. Please request a new one.'},status=400)
 user=reset_token.user
 try:
  validate_password(password,user=user)
 except ValidationError as exc:
  return Response({'error':' '.join(exc.messages)},status=400)
 with transaction.atomic():
  user.set_password(password)
  user.save()
  reset_token.used=True
  reset_token.save()
  PasswordResetToken.objects.filter(user=user,used=False).update(used=True)
  if hasattr(user,'profile') and not user.profile.email_verified:
   user.profile.email_verified=True
   user.profile.email_verified_at=timezone.now()
   user.profile.save()
 if request.user.is_authenticated and request.user.id==user.id:
  logout(request)
 log_auth_event(user,'password_reset_completed',request,metadata={'email':user.email})
 return Response({'message':'Your password has been successfully reset. You can now sign in with your new password.'},status=200)

@api_view(['GET','PATCH'])
@permission_classes([IsAuthenticated])
def me(request):
 if request.method=='PATCH':
  p=request.user.profile;p.institution=str(request.data.get('institution',p.institution))[:200];p.bio=str(request.data.get('bio',p.bio))[:2000];p.save()
  request.user.first_name=str(request.data.get('name',request.user.first_name))[:150];request.user.save()
 return Response({'user':user_data(request.user)})

@api_view(['GET'])
@permission_classes([AllowAny])
def catalogue(request):
 qs=Program.objects.all()
 if request.GET.get('module'): qs=qs.filter(module=request.GET['module'])
 if request.GET.get('q'): qs=qs.filter(title__icontains=request.GET['q'])
 return Response({'results':[program_data(p) for p in qs.order_by('id')[:100]]})

@api_view(['GET','POST'])
@permission_classes([IsAuthenticated])
def records(request):
 if request.method=='GET': return Response({'results':[record_data(r) for r in Record.objects.filter(user=request.user).select_related('program').order_by('-created_at')]})
 try: p=Program.objects.get(slug=request.data.get('program'))
 except Program.DoesNotExist: return Response({'error':'Program not found.'},status=404)
 if p.module=='careers': return Response({'error':'Internal career submissions are disabled. Apply through the official external recruitment link.'},status=400)
 if p.module=='careers': return Response({'error':'Internal career submissions are disabled. Apply through the company recruitment email or careers website.'},status=400)
 d=request.data.get('data',{})
 if not isinstance(d,dict): return Response({'error':'Invalid registration details.'},status=400)
 if len(str(d))>15000: return Response({'error':'Registration details are too long.'},status=400)
 if p.module=='careers' and not p.sample and not p.verified: return Response({'error':'This employer has not been verified.'},status=400)
 if p.module=='sports':
  if not str(d.get('team','')).strip(): return Response({'error':'A team name is required.'},status=400)
  players=[x.strip() for x in str(d.get('players','')).split('\n') if x.strip()]
  minimum=p.details.get('min_players',1);maximum=p.details.get('max_players',15)
  if not minimum<=len(players)<=maximum: return Response({'error':f'Enter {minimum}–{maximum} player names, one per line.'},status=400)
 if p.module=='culturals' and d.get('format') not in ['Solo','Group']: return Response({'error':'Select solo or group participation.'},status=400)
 if p.module=='incubation' and len(str(d.get('idea','')))<30: return Response({'error':'Describe your idea in at least 30 characters.'},status=400)
 try:
  with transaction.atomic():
   Program.objects.select_for_update().get(pk=p.pk)
   if Record.objects.filter(program=p).exclude(status='rejected').count()>=p.capacity: return Response({'error':'This program is full.'},status=400)
   r=Record.objects.create(user=request.user,program=p,data=d,status='enrolled' if p.module=='academy' and p.fee==0 else 'submitted')
   create_in_app_notification(request.user,f'{p.title}: registration received.')
   AuditLog.objects.create(actor=request.user,action='registration_created',target=str(r.id))
 except IntegrityError: return Response({'error':'You have already registered for this program.'},status=400)
 send_registration_confirmation_email(request.user,p,r)
 return Response(record_data(r),status=201)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def learning(request,pk):
 try: r=Record.objects.get(pk=pk,user=request.user,program__module='academy')
 except (Record.DoesNotExist,ValueError): return Response({'error':'Enrollment not found.'},status=404)
 if r.program.fee>0 and r.status not in ['enrolled','completed']: return Response({'error':'Paid enrollment requires staff payment confirmation. No payment gateway is connected.'},status=400)
 action=request.data.get('action')
 if action=='lesson':
  n=request.data.get('lesson')
  if n not in [0,1,2]: return Response({'error':'Invalid lesson.'},status=400)
  r.data['lessons']=sorted(set(r.data.get('lessons',[])+[n]))
 elif action=='assessment':
  if len(r.data.get('lessons',[]))<3 or len(str(request.data.get('project','')))<30: return Response({'error':'Complete all lessons and submit a project description of at least 30 characters.'},status=400)
  answers=request.data.get('answers',[]);score=sum(a==b for a,b in zip(answers,[1,0,2]))
  r.data.update(score=score,project=request.data['project'])
  if score>=2:r.status='awaiting_review'
 else:return Response({'error':'Invalid learning action.'},status=400)
 r.save();return Response(record_data(r))

@api_view(['GET','PATCH','POST'])
@permission_classes([IsAuthenticated])
def notifications(request):
 if request.method in ['PATCH','POST']:
  mark_all=request.data.get('all',False)
  notif_id=request.data.get('id')
  if mark_all:
   Notification.objects.filter(user=request.user,read=False).update(read=True)
  elif notif_id:
   Notification.objects.filter(user=request.user,id=notif_id).update(read=True)
  unread=Notification.objects.filter(user=request.user,read=False).count()
  return Response({'message':'Notifications updated.','unread_count':unread})
 notifs=list(Notification.objects.filter(user=request.user).order_by('-created_at').values('id','message','read','created_at')[:50])
 unread=Notification.objects.filter(user=request.user,read=False).count()
 return Response({'results':notifs,'unread_count':unread})

@csrf_protect
@api_view(['POST'])
@permission_classes([AllowAny])
def enquiry(request):
 d=request.data
 if not str(d.get('name','')).strip() or '@' not in str(d.get('email','')) or len(str(d.get('message','')))<10: return Response({'error':'Enter your name, email and a message of at least 10 characters.'},status=400)
 Enquiry.objects.create(name=d['name'][:100],email=d['email'][:254],kind=str(d.get('kind','general'))[:40],message=d['message'][:5000])
 return Response({'message':'Your enquiry has been saved. The WOC team can review it in admin.'},status=201)

@api_view(['GET','PATCH'])
@permission_classes([IsAdminUser])
def admin_records(request):
 if request.method=='PATCH':
  try:r=Record.objects.get(id=request.data.get('id'))
  except (Record.DoesNotExist,ValueError):return Response({'error':'Record not found.'},status=404)
  status=request.data.get('status')
  if status not in ['approved','rejected','enrolled','shortlisted','completed']:return Response({'error':'Invalid status.'},status=400)
  if status=='completed' and (r.program.module!='academy' or r.data.get('score',0)<2):return Response({'error':'A passing assessment is required before issuing a learning certificate.'},status=400)
  with transaction.atomic():
   r.status=status;r.save()
   if status=='completed':Certificate.objects.get_or_create(record=r,defaults={'issued_by':request.user})
   AuditLog.objects.create(actor=request.user,action='status_'+status,target=str(r.id))
   create_in_app_notification(r.user,f'{r.program.title}: application {status}.')
   if status=='completed':
    create_in_app_notification(r.user,f'{r.program.title}: Certificate issued! Verify it in your Certificates tab.')
  send_status_update_email(r.user,r.program,status)
 return Response({'results':[record_data(r) for r in Record.objects.select_related('program','user').order_by('-created_at')[:200]],'enquiries':list(Enquiry.objects.order_by('-created_at').values()[:50])})

@api_view(['GET'])
@permission_classes([AllowAny])
def certificate(request,pk):
 try:c=Certificate.objects.select_related('record__program','record__user').get(pk=pk)
 except (Certificate.DoesNotExist,ValueError):return Response({'error':'Certificate not found.'},status=404)
 return Response({'id':str(c.id),'name':c.record.user.first_name,'program':c.record.program.title,'issued_at':c.issued_at,'sample':c.record.program.sample})

@api_view(['GET'])
@permission_classes([AllowAny])
def health(request):return Response({'status':'ok','sample_catalogue':True,'payments_connected':False})
