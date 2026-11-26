from django.contrib.auth.models import User
from django.db import transaction, IntegrityError
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes,throttle_classes
from rest_framework.throttling import UserRateThrottle
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from .models import Institution,Company,CollegeMembership,CompanyMembership,AuthAuditLog,MembershipStatus
from .organization_access import access_context,is_super_admin,active_colleges,active_companies,IsCollegeAdministrator,IsCompanyAdministrator
from .organization_serializers import CollegeOnboardingSerializer,CompanyOnboardingSerializer


class OrganizationPagination(PageNumberPagination):
 page_size=20


class OnboardingWriteThrottle(UserRateThrottle):
 scope='organization_onboarding'
 rate='20/hour'
 def get_cache_key(self,request,view):
  if request.method!='POST': return None
  return super().get_cache_key(request,view)


def college_data(college):
 return {'id':college.pk,'name':college.name,'city':college.city,'website':college.website,'contact_email':college.contact_email,'address':college.address,'contact_phone':college.phone,'state':college.state,'registration_reference':college.registration_reference,'has_verification_document':bool(college.verification_document),'approval_status':college.approval_status,'created_at':college.created_at}


def company_data(company):
 return {'id':str(company.pk),'name':company.name,'city':company.city,'website':company.website,'contact_email':company.contact_email,'description':company.description,'company_type':company.company_type,'cin':company.cin,'address':company.address,'pin_code':company.pin_code,'designation':company.designation,'contact_phone':company.contact_phone,'state':company.state,'registration_reference':company.registration_reference,'has_verification_document':bool(company.verification_document),'approval_status':company.approval_status,'created_at':company.created_at}


def page_response(request,queryset,serialize):
 pagination=OrganizationPagination()
 page=pagination.paginate_queryset(queryset,request)
 return pagination.get_paginated_response([serialize(obj) for obj in page])


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def access(request):
 return Response(access_context(request.user))


@api_view(['GET','POST'])
@permission_classes([IsAuthenticated])
@throttle_classes([UserRateThrottle,OnboardingWriteThrottle])
def college_onboarding(request):
 if request.method=='GET':
  return page_response(request,Institution.objects.filter(memberships__user=request.user,memberships__role=CollegeMembership.Role.ADMIN,memberships__status__in=[MembershipStatus.PENDING,MembershipStatus.ACTIVE,MembershipStatus.REJECTED]).distinct().order_by('pk'),college_data)
 serializer=CollegeOnboardingSerializer(data=request.data);serializer.is_valid(raise_exception=True)
 data=serializer.validated_data
 try:
  with transaction.atomic():
   # Serialize repeated submissions for this account without changing its roles.
   User.objects.select_for_update().get(pk=request.user.pk)
   if CollegeMembership.objects.filter(user=request.user,role=CollegeMembership.Role.ADMIN,status__in=[MembershipStatus.PENDING,MembershipStatus.ACTIVE],institution__name__iexact=data['name']).exists():
    return Response({'error':'You have already submitted this college.'},status=409)
   college=Institution.objects.create(owner=request.user,**data)
   CollegeMembership.objects.create(user=request.user,institution=college,role=CollegeMembership.Role.ADMIN)
   AuthAuditLog.objects.create(user=request.user,event_type='college_onboarding_requested',metadata={'college_id':college.pk})
 except IntegrityError:
  return Response({'error':'This onboarding request conflicts with an existing membership.'},status=409)
 return Response(college_data(college),status=201)


@api_view(['GET','POST'])
@permission_classes([IsAuthenticated])
@throttle_classes([UserRateThrottle,OnboardingWriteThrottle])
def company_onboarding(request):
 if request.method=='GET':
  return page_response(request,Company.objects.filter(memberships__user=request.user,memberships__role=CompanyMembership.Role.ADMIN,memberships__status__in=[MembershipStatus.PENDING,MembershipStatus.ACTIVE,MembershipStatus.REJECTED]).distinct().order_by('created_at','pk'),company_data)
 serializer=CompanyOnboardingSerializer(data=request.data);serializer.is_valid(raise_exception=True)
 data=serializer.validated_data
 try:
  with transaction.atomic():
   User.objects.select_for_update().get(pk=request.user.pk)
   if CompanyMembership.objects.filter(user=request.user,status__in=[MembershipStatus.PENDING,MembershipStatus.ACTIVE],company__name__iexact=data['name']).exists():
    return Response({'error':'You have already submitted this company.'},status=409)
   company=Company.objects.create(created_by=request.user,**data)
   CompanyMembership.objects.create(user=request.user,company=company)
   AuthAuditLog.objects.create(user=request.user,event_type='company_onboarding_requested',metadata={'company_id':str(company.pk)})
 except IntegrityError:
  return Response({'error':'This onboarding request conflicts with an existing membership.'},status=409)
 return Response(company_data(company),status=201)


def scoped_colleges(user):
 if is_super_admin(user): return Institution.objects.all()
 return Institution.objects.filter(pk__in=active_colleges(user,CollegeMembership.Role.ADMIN).values('institution_id'))


def scoped_companies(user):
 if is_super_admin(user): return Company.objects.all()
 return Company.objects.filter(pk__in=active_companies(user).values('company_id'))


@api_view(['GET'])
@permission_classes([IsAuthenticated,IsCollegeAdministrator])
def colleges(request):
 return page_response(request,scoped_colleges(request.user).order_by('pk'),college_data)


@api_view(['GET'])
@permission_classes([IsAuthenticated,IsCollegeAdministrator])
def college_detail(request,pk):
 college=get_object_or_404(scoped_colleges(request.user),pk=pk)
 return Response(college_data(college))


@api_view(['GET'])
@permission_classes([IsAuthenticated,IsCompanyAdministrator])
def companies(request):
 return page_response(request,scoped_companies(request.user).order_by('created_at','pk'),company_data)


@api_view(['GET'])
@permission_classes([IsAuthenticated,IsCompanyAdministrator])
def company_detail(request,pk):
 company=get_object_or_404(scoped_companies(request.user),pk=pk)
 return Response(company_data(company))


@api_view(['GET','POST'])
@permission_classes([IsAuthenticated])
def organization_document(request,kind,pk):
 from django.http import FileResponse
 from .student_views import validated_upload
 from .models import OrganizationStatus
 if kind not in ['college','company']:return Response({'error':'Not found.'},status=404)
 model=Institution if kind=='college' else Company
 try: org=get_object_or_404(model,pk=pk)
 except (ValueError,TypeError):return Response({'error':'Not found.'},status=404)
 memberships=org.memberships.filter(user=request.user,role='college_admin' if kind=='college' else 'company_admin')
 if not is_super_admin(request.user) and not memberships.exists():return Response({'error':'Not found.'},status=404)
 if request.method=='GET':
  if not org.verification_document:return Response({'error':'No document uploaded.'},status=404)
  response=FileResponse(org.verification_document.open('rb'),as_attachment=True,filename='organization-verification.pdf',content_type='application/pdf')
  response['Cache-Control']='private, no-store';response['X-Content-Type-Options']='nosniff';return response
 content=validated_upload(request.FILES.get('file'))
 with transaction.atomic():
  org=model.objects.select_for_update().get(pk=org.pk)
  org.verification_document.save(content.name,content,save=False)
  if org.approval_status==OrganizationStatus.APPROVED:org.approval_status=OrganizationStatus.PENDING
  org.save()
  AuthAuditLog.objects.create(user=request.user,event_type='organization_verification_uploaded',metadata={'kind':kind,'id':str(org.pk)})
 return Response({'message':'Verification document saved for Super Admin review.'})
