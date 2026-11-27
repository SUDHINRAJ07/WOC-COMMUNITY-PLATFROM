from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination

from .models import (
    Company, CompanyMembership, Opportunity, OpportunityStatus,
    OpportunityType, OrganizationStatus, MembershipStatus, AuthAuditLog
)
from .organization_access import IsCompanyAdministrator, active_companies
from .opportunity_serializers import (
    CompanyProfileUpdateSerializer, OpportunityInputSerializer,
    OpportunitySubmissionValidator
)


class OpportunityPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 50


def serialize_company_profile(company: Company):
    return {
        'id': str(company.pk),'company_type':company.company_type,'cin':company.cin,'address':company.address,'pin_code':company.pin_code,'designation':company.designation,'registration_reference':company.registration_reference,'contact_phone':company.contact_phone,'state':company.state,
        'name': company.name,
        'city': company.city,
        'website': company.website,
        'contact_email': company.contact_email,
        'recruitment_email': company.recruitment_email,
        'careers_website': company.careers_website,
        'logo_url': company.logo_url,
        'industry': company.industry,
        'company_size': company.company_size,
        'contact_person': company.contact_person,
        'description': company.description,
        'approval_status': company.approval_status,
        'created_at': company.created_at,
    }


def serialize_opportunity(opp: Opportunity, include_moderation=False):
    data = {
        'id': str(opp.pk),
        'company_id': str(opp.company_id),
        'sample_listing': opp.company.contact_email.lower().endswith('@woc-demo.test'),
        'company_name': opp.company.name,
        'company_logo': opp.company.logo_url,
        'company_city': opp.company.city,
        'company_website': opp.company.website,
        'opportunity_type': opp.opportunity_type,
        'title': opp.title,
        'department':opp.department,'responsibilities':opp.responsibilities,'eligible_graduation_years':opp.eligible_graduation_years,'selection_process':opp.selection_process,'benefits':opp.benefits,
        'description': opp.description,
        'required_skills': opp.required_skills,
        'qualification': opp.qualification,
        'experience_level': opp.experience_level,
        'employment_type': opp.employment_type,
        'work_mode': opp.work_mode,
        'location': opp.location,
        'compensation': opp.compensation,
        'is_paid': opp.is_paid,
        'openings': opp.openings,
        'duration': opp.duration,
        'recruitment_email': opp.recruitment_email,
        'careers_url': opp.careers_url,
        'deadline': opp.deadline.isoformat() if opp.deadline else None,
        'status': opp.status,
        'created_at': opp.created_at,
        'updated_at': opp.updated_at,
    }
    if include_moderation:
        data.update({
            'previous_status': opp.previous_status,
            'review_note': opp.review_note,
            'reviewed_at': opp.reviewed_at,
        })
    return data


def get_user_active_company(user):
    active_m = CompanyMembership.objects.select_related('company').filter(
        user=user,
        role=CompanyMembership.Role.ADMIN,
        status=MembershipStatus.ACTIVE,
        company__approval_status=OrganizationStatus.APPROVED
    ).first()
    if active_m:
        return active_m.company
    # Fallback to any company registered by user if reviewing pending/submitted state
    own_m = CompanyMembership.objects.select_related('company').filter(
        user=user,
        role=CompanyMembership.Role.ADMIN
    ).first()
    return own_m.company if own_m else None


# ==========================================
# 1. COMPANY DASHBOARD & PROFILE ENDPOINTS
# ==========================================

@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated, IsCompanyAdministrator])
def company_profile(request):
    company = get_user_active_company(request.user)
    if not company:
        return Response({'error': 'No company registered or authorized for this account.'}, status=404)

    if request.method == 'GET':
        return Response(serialize_company_profile(company))

    serializer = CompanyProfileUpdateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    for field, val in serializer.validated_data.items():
        setattr(company, field, val)
    company.save()
    AuthAuditLog.objects.create(user=request.user, event_type='company_profile_updated', metadata={'company_id': str(company.pk)})
    return Response(serialize_company_profile(company))


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsCompanyAdministrator])
def company_dashboard(request):
    company = get_user_active_company(request.user)
    if not company:
        return Response({'error': 'No company registered or authorized for this account.'}, status=404)

    today = timezone.now().date()
    qs = Opportunity.objects.filter(company=company)
    total_opps = qs.count()
    active_jobs = qs.filter(opportunity_type=OpportunityType.JOB, status=OpportunityStatus.APPROVED).filter(Q(deadline__isnull=True) | Q(deadline__gte=today)).count()
    active_internships = qs.filter(opportunity_type=OpportunityType.INTERNSHIP, status=OpportunityStatus.APPROVED).filter(Q(deadline__isnull=True) | Q(deadline__gte=today)).count()
    pending = qs.filter(status=OpportunityStatus.PENDING_REVIEW).count()
    drafts = qs.filter(status=OpportunityStatus.DRAFT).count()
    closed = qs.filter(status=OpportunityStatus.CLOSED).count()

    return Response({
        'company': serialize_company_profile(company),
        'metrics': {
            'total_opportunities': total_opps,
            'active_jobs': active_jobs,
            'active_internships': active_internships,
            'pending_review': pending,
            'drafts': drafts,
            'closed': closed,
        }
    })


# ==========================================
# 2. COMPANY OPPORTUNITY MANAGEMENT ENDPOINTS
# ==========================================

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated, IsCompanyAdministrator])
def company_opportunities(request):
    company = get_user_active_company(request.user)
    if not company:
        return Response({'error': 'No company authorized for this account.'}, status=404)

    if request.method == 'GET':
        qs = Opportunity.objects.filter(company=company).order_by('-created_at')
        status_filter = request.GET.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        type_filter = request.GET.get('type')
        if type_filter:
            qs = qs.filter(opportunity_type=type_filter)
        q = request.GET.get('q')
        if q:
            qs = qs.filter(Q(title__icontains=q) | Q(description__icontains=q))

        paginator = OpportunityPagination()
        page = paginator.paginate_queryset(qs, request)
        return paginator.get_paginated_response([serialize_opportunity(o, include_moderation=True) for o in page])

    # POST: create draft
    serializer = OpportunityInputSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    with transaction.atomic():
        opp = Opportunity.objects.create(
            company=company,
            status=OpportunityStatus.DRAFT,
            **serializer.validated_data
        )
        AuthAuditLog.objects.create(user=request.user, event_type='opportunity_created', metadata={'opportunity_id': str(opp.pk), 'type': opp.opportunity_type})
    return Response(serialize_opportunity(opp, include_moderation=True), status=201)


@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated, IsCompanyAdministrator])
def company_opportunity_detail(request, pk):
    company = get_user_active_company(request.user)
    if not company:
        return Response({'error': 'No company authorized.'}, status=404)
    opp = get_object_or_404(Opportunity.objects.select_related('company'), pk=pk, company=company)

    if request.method == 'GET':
        return Response(serialize_opportunity(opp, include_moderation=True))

    if request.method == 'DELETE':
        with transaction.atomic():
            opp = get_object_or_404(Opportunity.objects.select_for_update(), pk=pk, company=company)
            if opp.status != OpportunityStatus.DRAFT:
                return Response({'error': 'Only draft opportunities can be deleted. Published, review, or closed opportunities must remain for historical records.'}, status=400)
            opp_id = str(opp.pk)
            opp.delete()
            AuthAuditLog.objects.create(user=request.user, event_type='opportunity_deleted', metadata={'opportunity_id': opp_id})
        return Response({'message': 'Draft opportunity deleted successfully.'}, status=200)

    # PATCH: Edit
    serializer = OpportunityInputSerializer(data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)

    with transaction.atomic():
        opp = get_object_or_404(Opportunity.objects.select_for_update(), pk=pk, company=company)
        if opp.status == OpportunityStatus.CLOSED:
            return Response({'error': 'Cannot edit a closed opportunity.'}, status=400)

        was_approved = (opp.status == OpportunityStatus.APPROVED)
        for k, v in serializer.validated_data.items():
            setattr(opp, k, v)
        
        # If it was previously approved and content/destinations changed, trigger reapproval
        if was_approved:
            opp.previous_status = OpportunityStatus.APPROVED
            opp.status = OpportunityStatus.PENDING_REVIEW
            opp.review_note = "Opportunity modified by company; automatically queued for Super Admin re-approval."
        opp.save()
        AuthAuditLog.objects.create(user=request.user, event_type='opportunity_updated', metadata={'opportunity_id': str(opp.pk), 'reapproval_triggered': was_approved})

    return Response(serialize_opportunity(opp, include_moderation=True))


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsCompanyAdministrator])
def company_opportunity_submit(request, pk):
    company = get_user_active_company(request.user)
    if not company:
        return Response({'error': 'No company authorized.'}, status=404)
    if company.approval_status != OrganizationStatus.APPROVED:
        return Response({'error': 'Your company registration must be approved by Super Admin before submitting opportunities.'}, status=403)

    with transaction.atomic():
        opp = get_object_or_404(Opportunity.objects.select_for_update(), pk=pk, company=company)
        if opp.status not in [OpportunityStatus.DRAFT, OpportunityStatus.REJECTED]:
            return Response({'error': f'Opportunity is currently in {opp.status} status and cannot be submitted for review.'}, status=400)

        # Validate completeness
        OpportunitySubmissionValidator.validate_for_submission(opp)

        opp.previous_status = opp.status
        opp.status = OpportunityStatus.PENDING_REVIEW
        opp.review_note = "Submitted for Super Admin review."
        opp.save()
        AuthAuditLog.objects.create(user=request.user, event_type='opportunity_submitted_for_review', metadata={'opportunity_id': str(opp.pk)})

    return Response({
        'message': 'Opportunity submitted for Super Admin review.',
        'opportunity': serialize_opportunity(opp, include_moderation=True)
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsCompanyAdministrator])
def company_opportunity_close(request, pk):
    company = get_user_active_company(request.user)
    if not company:
        return Response({'error': 'No company authorized.'}, status=404)

    with transaction.atomic():
        opp = get_object_or_404(Opportunity.objects.select_for_update(), pk=pk, company=company)
        if opp.status == OpportunityStatus.CLOSED:
            return Response({'message': 'Opportunity is already closed.', 'opportunity': serialize_opportunity(opp, include_moderation=True)})

        opp.previous_status = opp.status
        opp.status = OpportunityStatus.CLOSED
        opp.save()
        AuthAuditLog.objects.create(user=request.user, event_type='opportunity_closed', metadata={'opportunity_id': str(opp.pk)})

    return Response({
        'message': 'Opportunity has been closed and removed from the public portal.',
        'opportunity': serialize_opportunity(opp, include_moderation=True)
    })


# ==========================================
# 3. PUBLIC OPPORTUNITY PORTAL ENDPOINTS
# ==========================================

@api_view(['GET'])
@permission_classes([AllowAny])
def public_opportunities(request):
    today = timezone.now().date()
    qs = Opportunity.objects.select_related('company').filter(
        status=OpportunityStatus.APPROVED,
        company__approval_status=OrganizationStatus.APPROVED
    ).filter(
        Q(deadline__isnull=True) | Q(deadline__gte=today)
    ).order_by('-created_at')

    # Filters
    opp_type = request.GET.get('type')
    if opp_type in [OpportunityType.JOB, OpportunityType.INTERNSHIP]:
        qs = qs.filter(opportunity_type=opp_type)

    work_mode = request.GET.get('work_mode')
    if work_mode:
        qs = qs.filter(work_mode=work_mode)

    emp_type = request.GET.get('employment_type')
    if emp_type:
        qs = qs.filter(employment_type=emp_type)

    loc = request.GET.get('location')
    if loc:
        qs = qs.filter(location__icontains=loc)

    q = request.GET.get('q')
    if q:
        qs = qs.filter(
            Q(title__icontains=q) |
            Q(description__icontains=q) |
            Q(company__name__icontains=q) |
            Q(required_skills__icontains=q)
        )

    paginator = OpportunityPagination()
    page = paginator.paginate_queryset(qs, request)
    return paginator.get_paginated_response([serialize_opportunity(o) for o in page])


@api_view(['GET'])
@permission_classes([AllowAny])
def public_opportunity_detail(request, pk):
    today = timezone.now().date()
    opp = get_object_or_404(
        Opportunity.objects.select_related('company').filter(
            status=OpportunityStatus.APPROVED,
            company__approval_status=OrganizationStatus.APPROVED
        ).filter(
            Q(deadline__isnull=True) | Q(deadline__gte=today)
        ),
        pk=pk
    )
    return Response(serialize_opportunity(opp))


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsCompanyAdministrator])
def company_partnerships(request):
    from .models import CollegePartnership
    from rest_framework.pagination import PageNumberPagination
    company=get_user_active_company(request.user)
    if not company:return Response({'error':'Approved company membership required.'},status=403)
    qs=CollegePartnership.objects.filter(company=company).select_related('institution').order_by('-created_at')
    pagination=PageNumberPagination();pagination.page_size=20
    page=pagination.paginate_queryset(qs,request)
    return pagination.get_paginated_response([{'id':str(p.pk),'institution_name':p.institution.name,'status':p.status,'partnership_type':p.partnership_type,'mou_signed_date':p.mou_signed_date} for p in page])
