from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.contrib.auth.models import User
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import (
    Institution, Company, CollegeMembership, CompanyMembership,
    Opportunity, OpportunityStatus, OpportunityType, OrganizationStatus,
    MembershipStatus, AuthAuditLog, Notification
)
from .organization_access import IsPlatformSuperAdmin
from .opportunity_serializers import SuperAdminReviewSerializer, OpportunitySubmissionValidator


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsPlatformSuperAdmin])
def super_admin_overview(request):
    today = timezone.now().date()
    students_count = User.objects.filter(is_staff=False, is_superuser=False).exclude(company_memberships__role='company_admin').exclude(college_memberships__role='college_admin').exclude(groups__name='super_admin').distinct().count()
    colleges_count = Institution.objects.count()
    companies_count = Company.objects.count()
    pending_orgs = (
        Institution.objects.filter(approval_status=OrganizationStatus.PENDING).count() +
        Company.objects.filter(approval_status=OrganizationStatus.PENDING).count()
    )
    published_jobs = Opportunity.objects.filter(
        opportunity_type=OpportunityType.JOB,
        status=OpportunityStatus.APPROVED,
        company__approval_status=OrganizationStatus.APPROVED
    ).filter(Q(deadline__isnull=True) | Q(deadline__gte=today)).count()

    published_internships = Opportunity.objects.filter(
        opportunity_type=OpportunityType.INTERNSHIP,
        status=OpportunityStatus.APPROVED,
        company__approval_status=OrganizationStatus.APPROVED
    ).filter(Q(deadline__isnull=True) | Q(deadline__gte=today)).count()

    pending_opps = Opportunity.objects.filter(status=OpportunityStatus.PENDING_REVIEW).count()

    return Response({
        'summary': {
            'total_students': students_count,
            'registered_colleges': colleges_count,
            'registered_companies': companies_count,
            'pending_organizations': pending_orgs,
            'published_jobs': published_jobs,
            'published_internships': published_internships,
            'pending_opportunities': pending_opps,
        }
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsPlatformSuperAdmin])
def super_admin_organizations(request):
    status_filter = request.GET.get('status') # 'pending', 'approved', 'rejected', 'suspended' or empty for all
    colleges_qs = Institution.objects.select_related('owner').order_by('-created_at')
    companies_qs = Company.objects.select_related('created_by').order_by('-created_at')

    if status_filter:
        colleges_qs = colleges_qs.filter(approval_status=status_filter)
        companies_qs = companies_qs.filter(approval_status=status_filter)

    colleges_list = [{
        'kind': 'college',
        'id': c.pk,
        'name': c.name,
        'city': c.city,
        'website': c.website,
        'contact_email': c.contact_email,
        'registration_reference':c.registration_reference,'state':c.state,'has_verification_document':bool(c.verification_document),
        'approval_status': c.approval_status,
        'created_at': c.created_at,
        'review_note': c.review_note,
        'submitted_by': c.owner.email if c.owner else None,
    } for c in colleges_qs[:100]]

    companies_list = [{
        'kind': 'company',
        'id': str(c.pk),
        'name': c.name,
        'city': c.city,
        'website': c.website,
        'contact_email': c.contact_email,
        'registration_reference':c.registration_reference,'state':c.state,'has_verification_document':bool(c.verification_document),
        'recruitment_email': c.recruitment_email,
        'careers_website': c.careers_website,
        'logo_url': c.logo_url,
        'industry': c.industry,
        'company_size': c.company_size,
        'contact_person': c.contact_person,
        'description': c.description,
        'approval_status': c.approval_status,
        'created_at': c.created_at,
        'review_note': c.review_note,
        'submitted_by': c.created_by.email if c.created_by else None,
    } for c in companies_qs[:100]]

    return Response({
        'organizations': sorted(colleges_list + companies_list, key=lambda x: x['created_at'], reverse=True)
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsPlatformSuperAdmin])
def super_admin_review_organization(request, kind, pk):
    serializer = SuperAdminReviewSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    action = serializer.validated_data['action']
    note = serializer.validated_data.get('note', '').strip()

    with transaction.atomic():
        if kind == 'company':
            org = get_object_or_404(Company.objects.select_for_update(), pk=pk)
            owner = org.created_by
            membership_model = CompanyMembership
            membership_filter = {'company': org}
            admin_role = 'company_admin'
        elif kind == 'college':
            org = get_object_or_404(Institution.objects.select_for_update(), pk=pk)
            owner = org.owner
            membership_model = CollegeMembership
            membership_filter = {'institution': org}
            admin_role = 'college_admin'
        else:
            return Response({'error': 'Invalid organization kind. Expected college or company.'}, status=400)

        prev_status = org.approval_status

        # Strict lifecycle transitions for organizations
        if action == 'approve':
            if prev_status not in [OrganizationStatus.PENDING, OrganizationStatus.REJECTED]:
                return Response({'error': f"Cannot approve an organization with status '{prev_status}'. Only pending or rejected organizations can be approved."}, status=400)
        elif action == 'reject':
            if prev_status != OrganizationStatus.PENDING:
                return Response({'error': f"Cannot reject an organization with status '{prev_status}'. Only pending organizations can be rejected."}, status=400)
        elif action == 'suspend':
            if prev_status != OrganizationStatus.APPROVED:
                return Response({'error': f"Cannot suspend an organization with status '{prev_status}'. Only approved organizations can be suspended."}, status=400)
        elif action == 'reactivate':
            if prev_status != OrganizationStatus.SUSPENDED:
                return Response({'error': f"Cannot reactivate an organization with status '{prev_status}'. Only suspended organizations can be reactivated."}, status=400)
        else:
            return Response({'error': f"Invalid review action '{action}'."}, status=400)

        org.reviewed_by = request.user
        org.reviewed_at = timezone.now()
        org.review_note = note

        if action == 'approve':
            org.approval_status = OrganizationStatus.APPROVED
            # Security: Activate ONLY pending administrator memberships without exceeding uniqueness constraint.
            # Never activate inactive, revoked, or rejected memberships.
            has_active = membership_model.objects.filter(**membership_filter, role=admin_role, status=MembershipStatus.ACTIVE).exists()
            if not has_active:
                pending_admin = membership_model.objects.filter(**membership_filter, role=admin_role, status=MembershipStatus.PENDING).first()
                if pending_admin:
                    pending_admin.status = MembershipStatus.ACTIVE
                    pending_admin.save(update_fields=['status'])
            if owner:
                Notification.objects.create(
                    user=owner,
                    message=f"Congratulations! Your {kind} '{org.name}' has been approved by Super Admin."
                )
        elif action == 'reject':
            org.approval_status = OrganizationStatus.REJECTED
            membership_model.objects.filter(**membership_filter, status=MembershipStatus.PENDING).update(status=MembershipStatus.REJECTED)
            if owner:
                Notification.objects.create(
                    user=owner,
                    message=f"Your {kind} registration '{org.name}' was rejected. Note: {note or 'Not specified.'}"
                )
        elif action == 'suspend':
            org.approval_status = OrganizationStatus.SUSPENDED
            if owner:
                Notification.objects.create(
                    user=owner,
                    message=f"Notice: Your {kind} '{org.name}' has been suspended by Super Admin."
                )
        elif action == 'reactivate':
            org.approval_status = OrganizationStatus.APPROVED
            # On reactivation, preserve explicit inactive/revoked memberships.
            # Only activate pending if no active admin currently exists.
            has_active = membership_model.objects.filter(**membership_filter, role=admin_role, status=MembershipStatus.ACTIVE).exists()
            if not has_active:
                pending_admin = membership_model.objects.filter(**membership_filter, role=admin_role, status=MembershipStatus.PENDING).first()
                if pending_admin:
                    pending_admin.status = MembershipStatus.ACTIVE
                    pending_admin.save(update_fields=['status'])
            if owner:
                Notification.objects.create(
                    user=owner,
                    message=f"Notice: Your {kind} '{org.name}' has been reactivated by Super Admin."
                )

        org.save()
        AuthAuditLog.objects.create(
            user=request.user,
            event_type=f'{kind}_review_{action}',
            metadata={'id': str(org.pk), 'name': org.name, 'previous_status': prev_status, 'note': note}
        )

    return Response({
        'message': f"Organization {action}d successfully.",
        'organization': {
            'kind': kind,
            'id': str(org.pk),
            'name': org.name,
            'approval_status': org.approval_status,
            'review_note': org.review_note,
        }
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsPlatformSuperAdmin])
def super_admin_opportunities(request):
    status_filter = request.GET.get('status')
    qs = Opportunity.objects.select_related('company').order_by('-created_at')
    if status_filter:
        qs = qs.filter(status=status_filter)

    results = [{
        'id': str(o.pk),
        'company_id': str(o.company_id),
        'company_name': o.company.name,
        'company_approval': o.company.approval_status,
        'opportunity_type': o.opportunity_type,
        'title': o.title,
        'description': o.description,
        'required_skills': o.required_skills,
        'qualification': o.qualification,
        'experience_level': o.experience_level,
        'employment_type': o.employment_type,
        'work_mode': o.work_mode,
        'location': o.location,
        'compensation': o.compensation,
        'is_paid': o.is_paid,
        'openings': o.openings,
        'duration': o.duration,
        'recruitment_email': o.recruitment_email,
        'careers_url': o.careers_url,
        'deadline': o.deadline.isoformat() if o.deadline else None,
        'status': o.status,
        'previous_status': o.previous_status,
        'review_note': o.review_note,
        'created_at': o.created_at,
    } for o in qs[:100]]

    return Response({'opportunities': results})


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsPlatformSuperAdmin])
def super_admin_review_opportunity(request, pk):
    serializer = SuperAdminReviewSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    action = serializer.validated_data['action']
    note = serializer.validated_data.get('note', '').strip()

    with transaction.atomic():
        opp = get_object_or_404(Opportunity.objects.select_for_update().select_related('company'), pk=pk)
        prev_status = opp.status

        # Strict opportunity lifecycle transitions
        if action == 'approve':
            if prev_status != OpportunityStatus.PENDING_REVIEW:
                return Response({'error': f"Cannot approve an opportunity with status '{prev_status}'. Only submitted opportunities pending review can be approved."}, status=400)
        elif action == 'reject':
            if prev_status != OpportunityStatus.PENDING_REVIEW:
                return Response({'error': f"Cannot reject an opportunity with status '{prev_status}'. Only submitted opportunities pending review can be rejected."}, status=400)
        elif action == 'suspend':
            if prev_status != OpportunityStatus.APPROVED:
                return Response({'error': f"Cannot suspend an opportunity with status '{prev_status}'. Only approved opportunities can be suspended."}, status=400)
        elif action == 'reactivate':
            if prev_status != OpportunityStatus.SUSPENDED:
                return Response({'error': f"Cannot reactivate an opportunity with status '{prev_status}'. Only suspended opportunities can be reactivated."}, status=400)
        else:
            return Response({'error': f"Invalid review action '{action}'."}, status=400)

        # Revalidate completeness, destination, and deadline before publication or reactivation
        if action in ['approve', 'reactivate']:
            if opp.company.approval_status != OrganizationStatus.APPROVED:
                return Response({'error': f'Cannot {action} an opportunity for a company that is not approved.'}, status=400)
            
            # Destination verification
            if not (opp.recruitment_email or opp.careers_url):
                return Response({'error': 'Approved opportunity must specify at least one valid application destination (recruitment email or HTTPS careers URL).'}, status=400)
            
            # Non-expired validation
            today = timezone.now().date()
            if opp.deadline and opp.deadline < today:
                return Response({'error': 'Cannot approve or reactivate an expired opportunity. The application deadline has already passed.'}, status=400)

            # Completeness validation
            try:
                OpportunitySubmissionValidator.validate_for_submission(opp)
            except Exception as e:
                return Response({'error': f"Opportunity fails completeness validation: {e}"}, status=400)

        opp.previous_status = prev_status
        opp.reviewed_by = request.user
        opp.reviewed_at = timezone.now()
        opp.review_note = note

        company_owner = opp.company.created_by

        if action in ['approve', 'reactivate']:
            opp.status = OpportunityStatus.APPROVED
            if company_owner:
                Notification.objects.create(
                    user=company_owner,
                    message=f"Your posting '{opp.title}' has been {'approved and is now live on the WOC Careers Portal' if action == 'approve' else 'reactivated'}."
                )
        elif action == 'reject':
            opp.status = OpportunityStatus.REJECTED
            if company_owner:
                Notification.objects.create(
                    user=company_owner,
                    message=f"Your posting '{opp.title}' was rejected by Super Admin. Feedback: {note or 'Not specified.'}"
                )
        elif action == 'suspend':
            opp.status = OpportunityStatus.SUSPENDED
            if company_owner:
                Notification.objects.create(
                    user=company_owner,
                    message=f"Your posting '{opp.title}' was suspended by Super Admin. Note: {note or 'Policy violation.'}"
                )

        opp.save()
        AuthAuditLog.objects.create(
            user=request.user,
            event_type=f'opportunity_review_{action}',
            metadata={'id': str(opp.pk), 'title': opp.title, 'company': opp.company.name, 'previous_status': prev_status, 'note': note}
        )

    return Response({
        'message': f"Opportunity {action}d successfully.",
        'opportunity': {
            'id': str(opp.pk),
            'title': opp.title,
            'status': opp.status,
            'review_note': opp.review_note,
        }
    })


@api_view(['GET','POST'])
@permission_classes([IsAuthenticated, IsPlatformSuperAdmin])
def super_admin_accounts(request):
    if request.method == 'POST':
        if set(request.data) != {'user_id', 'action'} or request.data.get('action') not in ['activate','suspend']:
            return Response({'error':'Provide user_id and activate or suspend action.'},status=400)
        try: target_id=int(request.data['user_id'])
        except (ValueError,TypeError): return Response({'error':'Invalid account ID.'},status=400)
        with transaction.atomic():
            target=get_object_or_404(User.objects.select_for_update(),pk=target_id)
            if target.pk == request.user.pk or target.is_staff or target.is_superuser or target.groups.filter(name='super_admin').exists():
                return Response({'error':'Protected administrative accounts cannot be changed here.'},status=403)
            target.is_active=request.data['action']=='activate'
            target.save(update_fields=['is_active'])
            AuthAuditLog.objects.create(user=request.user,event_type='admin_account_'+request.data['action'],metadata={'target_user_id':target.pk})
        return Response({'message':'Account updated.'})
    from .organization_access import access_context
    if request.method == 'POST':
        if set(request.data) - {'user_id', 'action'} or request.data.get('action') not in ['activate', 'suspend']:
            return Response({'error': 'Invalid account action.'}, status=400)
        try:
            user_id = int(request.data.get('user_id'))
        except (ValueError, TypeError):
            return Response({'error': 'Invalid user ID.'}, status=400)
        with transaction.atomic():
            target = get_object_or_404(User.objects.select_for_update(), pk=user_id)
            if target.pk == request.user.pk or target.is_superuser or target.is_staff or target.groups.filter(name='super_admin').exists():
                return Response({'error': 'Protected administrative account.'}, status=403)
            previous = target.is_active
            target.is_active = request.data['action'] == 'activate'
            target.save(update_fields=['is_active'])
            AuthAuditLog.objects.create(user=request.user, event_type='admin_account_' + request.data['action'], metadata={'target_user_id': target.pk, 'previous_active': previous})
        return Response({'message': 'Account updated.'})
    from django.core.paginator import Paginator
    users = User.objects.all().order_by('id')
    search = request.GET.get('q', '').strip()
    if search:
        users = users.filter(Q(username__icontains=search)|Q(email__icontains=search)|Q(first_name__icontains=search)|Q(last_name__icontains=search))
    items = []
    counts = {'student': 0, 'college_admin': 0, 'company_admin': 0, 'super_admin': 0}
    for user in users:
        if user.is_superuser or user.groups.filter(name='super_admin', permissions__codename='manage_organizations').exists(): role='super_admin'
        elif user.company_memberships.filter(role='company_admin').exclude(status='inactive').exists(): role='company_admin'
        elif user.college_memberships.filter(role='college_admin').exclude(status='inactive').exists(): role='college_admin'
        else: role='student'
        counts[role] += 1
        if request.GET.get('role') and request.GET['role'] != role: continue
        if request.GET.get('status') == 'active' and not user.is_active: continue
        if request.GET.get('status') == 'suspended' and user.is_active: continue
        items.append({'id': user.pk, 'name': user.get_full_name() or user.username, 'email': user.email, 'role': role, 'is_active': user.is_active})
    page = Paginator(items, 20).get_page(request.GET.get('page', 1))
    history = list(AuthAuditLog.objects.filter(event_type__startswith='admin_account_').order_by('-created_at').values('user_id','event_type','metadata','created_at')[:50])
    return Response({'results': list(page), 'count': len(items), 'pages': page.paginator.num_pages, 'statistics': counts, 'history': history})
