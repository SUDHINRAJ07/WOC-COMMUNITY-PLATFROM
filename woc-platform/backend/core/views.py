from django.contrib.auth import authenticate,login,logout
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core import signing
from django.core.mail import send_mail
from django.conf import settings
from django.db import transaction,IntegrityError
from django.middleware.csrf import get_token
from django.views.decorators.csrf import csrf_protect
from rest_framework.decorators import api_view,permission_classes
from rest_framework.permissions import AllowAny,IsAuthenticated,IsAdminUser
from rest_framework.response import Response
from .models import *

def program_data(p):
 return {k:getattr(p,k) for k in ['slug','module','title','description','category','location','duration','level','capacity','sample','verified','details']}|{'fee':str(p.fee)}
def record_data(r):
 return {'id':str(r.id),'program':program_data(r.program),'status':r.status,'data':r.data,'created_at':r.created_at,'certificate':str(r.certificate.id) if hasattr(r,'certificate') else None,'student':r.user.first_name,'email':r.user.email}
def user_data(u):
 p=u.profile
 return {'id':u.id,'name':u.first_name,'email':u.email,'institution':p.institution,'age':p.age,'bio':p.bio,'roles':p.roles,'is_staff':u.is_staff}

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
 try: age=int(d.get('age',0))
 except (ValueError,TypeError): return Response({'error':'Enter a valid age.'},status=400)
 if not name or '@' not in email or len(email)>254: return Response({'error':'A name and valid email are required.'},status=400)
 if age<13 or age>100: return Response({'error':'Membership is available from age 13.'},status=400)
 if age<18 and not d.get('guardian_consent'): return Response({'error':'School and guardian permission is required for under-18 participation.'},status=400)
 if not d.get('terms'): return Response({'error':'Please accept the terms and privacy notice.'},status=400)
 try: validate_password(d.get('password',''))
 except ValidationError as exc: return Response({'error':' '.join(exc.messages)},status=400)
 try:
  with transaction.atomic():
   u=User.objects.create_user(email,email,d['password'],first_name=name)
   Profile.objects.create(user=u,age=age,guardian_consent=bool(d.get('guardian_consent')),institution=d.get('institution',''),roles=['student'])
 except IntegrityError: return Response({'error':'An account already exists with this email.'},status=400)
 token=signing.dumps({'user':u.id},salt='verify-email')
 url=settings.FRONTEND_URL+'/verify/?token='+token
 send_mail('Verify your WOC email','Verify your account: '+url,settings.DEFAULT_FROM_EMAIL,[email])
 result={'message':'Account created. Check your email for verification.'}
 if settings.DEBUG: result['development_verification_url']=url
 return Response(result,status=201)

@csrf_protect
@api_view(['POST'])
@permission_classes([AllowAny])
def verify(request):
 try:
  payload=signing.loads(request.data.get('token',''),salt='verify-email',max_age=86400)
  p=Profile.objects.get(user_id=payload['user']);p.email_verified=True;p.save()
 except (signing.BadSignature,Profile.DoesNotExist): return Response({'error':'Invalid or expired verification link.'},status=400)
 return Response({'message':'Email verified. You can sign in.'})

@csrf_protect
@api_view(['POST'])
@permission_classes([AllowAny])
def sign_in(request):
 u=authenticate(username=str(request.data.get('email','')).lower(),password=request.data.get('password',''))
 if not u: return Response({'error':'Email or password is incorrect.'},status=400)
 if not hasattr(u,'profile') or not u.profile.email_verified: return Response({'error':'Verify your email first.'},status=403)
 device=None
 if u.is_staff:
  from django_otp.plugins.otp_totp.models import TOTPDevice
  device=next((d for d in TOTPDevice.objects.filter(user=u,confirmed=True) if d.verify_token(request.data.get('otp',''))),None)
  if not device:return Response({'error':'A valid admin authenticator code is required.'},status=403)
 login(request,u)
 if device:
  from django_otp import login as otp_login
  otp_login(request,device)
 return Response({'user':user_data(u),'csrfToken':get_token(request)})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def sign_out(request): logout(request);return Response({'message':'Signed out.'})

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
   Notification.objects.create(user=request.user,message=f'{p.title}: registration received.')
   AuditLog.objects.create(actor=request.user,action='registration_created',target=str(r.id))
 except IntegrityError: return Response({'error':'You have already registered for this program.'},status=400)
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

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def notifications(request): return Response({'results':list(Notification.objects.filter(user=request.user).order_by('-created_at').values('id','message','read')[:50])})

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
   AuditLog.objects.create(actor=request.user,action='status_'+status,target=str(r.id));Notification.objects.create(user=r.user,message=f'{r.program.title}: {status}.')
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
