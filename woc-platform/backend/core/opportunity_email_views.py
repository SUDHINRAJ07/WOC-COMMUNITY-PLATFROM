from pathlib import Path
from datetime import timedelta
from smtplib import SMTPException
from django.conf import settings
from django.core.mail import EmailMessage
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.decorators import api_view,permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Opportunity,OpportunityApplicationLog,EmailDeliveryLog,AuthAuditLog
from .organization_access import access_context


@api_view(['GET','POST'])
@permission_classes([IsAuthenticated])
def apply_by_email(request,pk):
    if 'student' not in access_context(request.user)['roles']:
        return Response({'error':'Sign in with a student account to apply.'},status=403)
    opp=get_object_or_404(Opportunity.objects.select_related('company').filter(status='approved',company__approval_status='approved').filter(Q(deadline__isnull=True)|Q(deadline__gte=timezone.localdate())),pk=pk)
    profile=request.user.profile
    recipient=opp.recruitment_email.strip()
    sample=opp.company.contact_email.lower().endswith('@woc-demo.test')
    can_send=bool(recipient) and not sample and not recipient.lower().endswith(('.test','.invalid','.example'))
    details={'name':request.user.first_name or request.user.username,'email':request.user.email,'phone':profile.phone_number if profile.phone_verified else '',
        'institution':profile.institution,'qualification':profile.qualification,'department':profile.department,'graduation_year':profile.graduation_year,
        'skills':profile.skills,'linkedin_url':profile.linkedin_url,'resume_name':Path(profile.resume_file.name).name if profile.resume_file else ''}
    if request.method=='GET':
        previous=OpportunityApplicationLog.objects.filter(user=request.user,opportunity=opp).first()
        return Response({'student':details,'recipient':recipient,'can_send':can_send,'email_verified':profile.email_verified,
            'delivery_state':previous.email_delivery_state if previous else '',
            'notice':'Sample listing: personal information cannot be sent to placeholder employers.' if sample else ''})
    if set(request.data)-{'consent'} or request.data.get('consent') is not True:
        return Response({'error':'Confirm consent to share your profile and resume.'},status=400)
    if not can_send:
        return Response({'error':'This listing does not accept email applications. Sample addresses cannot receive personal information.'},status=400)
    if any(name in settings.EMAIL_BACKEND for name in ['console.EmailBackend','filebased.EmailBackend','dummy.EmailBackend']) or (not settings.DEBUG and 'locmem.EmailBackend' in settings.EMAIL_BACKEND):
        return Response({'error':'Live application email delivery is not configured. Please contact support.'},status=503)
    if not profile.email_verified:
        return Response({'error':'Verify your email before sending an application.'},status=403)
    try:
        validate_email(recipient);validate_email(request.user.email)
    except ValidationError:
        return Response({'error':'A valid applicant and recruitment email are required.'},status=400)
    if not profile.resume_file:
        return Response({'error':'Upload your PDF resume in My Profile before applying.'},status=400)
    try:
        with profile.resume_file.open('rb') as source:
            resume=source.read(5*1024*1024+1)
        if len(resume)>5*1024*1024 or not resume.startswith(b'%PDF-'):
            return Response({'error':'Resume must be a PDF up to 5 MB.'},status=400)
    except (OSError,ValueError):
        return Response({'error':'Your saved resume is unavailable. Upload it again in My Profile.'},status=400)
    # Claim the unique user/opportunity receipt before contacting the mail server.
    # Sending/uncertain requests cannot be retried automatically and duplicated.
    with transaction.atomic():
        current=get_object_or_404(Opportunity.objects.select_for_update().filter(status="approved",company__approval_status="approved").filter(Q(deadline__isnull=True)|Q(deadline__gte=timezone.localdate())),pk=opp.pk)
        if current.recruitment_email.strip()!=recipient:
            return Response({"error":"Application destination changed. Reload and review before applying."},status=409)
        receipt,_=OpportunityApplicationLog.objects.get_or_create(user=request.user,opportunity=opp)
        receipt=OpportunityApplicationLog.objects.select_for_update().get(pk=receipt.pk)
        if receipt.email_delivery_state in ['sending','sent']:
            return Response({'error':'This application is already submitted or being processed.'},status=409)
        if receipt.email_consent_at and receipt.email_consent_at>timezone.now()-timedelta(seconds=60):
            return Response({'error':'Please wait 60 seconds before retrying.'},status=429)
        receipt.email_delivery_state='sending';receipt.email_consent_at=timezone.now();receipt.emailed_recipient=recipient
        receipt.save(update_fields=['email_delivery_state','email_consent_at','emailed_recipient'])
    title=opp.title.replace('\r',' ').replace('\n',' ')
    body='Application submitted through WOC with the student’s consent.\n\nPosition: '+title+'\n\n'
    body+='\n'.join(f'{label}: {value}' for label,value in [
        ('Name',details['name']),('Email',details['email']),('Verified phone',details['phone']),('Institution',details['institution']),
        ('Qualification',details['qualification']),('Department',details['department']),('Graduation year',details['graduation_year'] or ''),
        ('Skills',', '.join(details['skills'] or [])),('LinkedIn',details['linkedin_url'])])
    body+='\n\nThe student’s PDF resume is attached. Reply directly to the student using Reply-To.\n'
    message=EmailMessage(subject=('WOC Application: '+title)[:200],body=body,from_email=settings.DEFAULT_FROM_EMAIL,to=[recipient],reply_to=[request.user.email])
    message.attach('Resume.pdf',resume,'application/pdf')
    try:
        accepted=message.send(fail_silently=False)
        if accepted!=1:raise SMTPException('Provider did not accept message')
    except Exception:
        # Unknown transport outcome may already have reached the provider.
        # Retain sending state to avoid duplicate emails on an automatic retry.
        EmailDeliveryLog.objects.create(recipient=recipient,subject=message.subject,template_name='opportunity_application',status='failed',error_message='Delivery outcome uncertain. Check provider/server logs before retrying.')
        return Response({'error':'Email delivery could not be confirmed. Contact support before retrying to avoid a duplicate application.'},status=503)
    receipt.email_delivery_state='sent';receipt.email_submitted_at=timezone.now();receipt.status='applied';receipt.applied_at=timezone.localdate()
    receipt.save(update_fields=['email_delivery_state','email_submitted_at','status','applied_at','updated_at'])
    EmailDeliveryLog.objects.create(recipient=recipient,subject=message.subject,template_name='opportunity_application',status='sent')
    AuthAuditLog.objects.create(user=request.user,event_type='opportunity_email_submitted',metadata={'opportunity_id':str(opp.pk),'consent':True})
    return Response({'message':'Your application and resume were accepted by the email server. Inbox delivery is not guaranteed.','delivery_state':'sent'})
