from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Q, Count
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination

from .models import (
    Institution, CollegeMembership, MembershipStatus, OrganizationStatus,
    TrainingBatch, CampusPlacement, CollegePartnership, Program, Company, Opportunity, OpportunityStatus,
    AuthAuditLog, Notification
)
from .organization_access import is_super_admin, active_colleges, IsCollegeAdministrator
from .college_serializers import (
    CollegeProfileUpdateSerializer, StudentMembershipReviewSerializer,
    TrainingBatchSerializer, BatchEnrollmentSerializer,
    CampusPlacementSerializer, CollegePartnershipSerializer
)


class CollegePagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 50


def get_user_college(request):
    """Resolve the active approved college for the requesting user."""
    user = request.user
    if is_super_admin(user):
        college_id = request.query_params.get('college_id') or request.data.get('college_id')
        if college_id:
            try:
                return Institution.objects.get(pk=college_id)
            except (Institution.DoesNotExist, ValueError):
                return None
        first_approved = Institution.objects.filter(approval_status=OrganizationStatus.APPROVED).first()
        return first_approved or Institution.objects.first()

    membership = active_colleges(user, CollegeMembership.Role.ADMIN).select_related('institution').first()
    if membership:
        return membership.institution
    return None


def serialize_college_profile(inst: Institution):
    return {
        'id': inst.pk,
        'name': inst.name,
        'city': inst.city,
        'website': inst.website,
        'contact_email': inst.contact_email,
        'phone': getattr(inst, 'phone', ''),
        'principal_name': getattr(inst, 'principal_name', ''),
        'logo_url': getattr(inst, 'logo_url', ''),
        'description': getattr(inst, 'description', ''),
        'address': inst.address,
        'verified': inst.verified,
        'approval_status': inst.approval_status,
        'created_at': inst.created_at,
    }


def serialize_student_membership(membership: CollegeMembership):
    user = membership.user
    full_name = f"{user.first_name} {user.last_name}".strip() or user.username
    phone = ''
    if hasattr(user, 'profile'):
        phone = user.profile.phone_number or ''
    return {
        'membership_id': membership.pk,
        'user_id': user.pk,
        'name': full_name,
        'email': user.email,
        'phone': phone,
        'role': membership.role,
        'status': membership.status,
        'created_at': membership.created_at,
        'enrolled_batches_count': user.enrolled_batches.filter(institution=membership.institution).count(),
    }


def serialize_batch(batch: TrainingBatch, include_students=False):
    data = {
        'id': str(batch.id),
        'name': batch.name,
        'program': {
            'id': batch.program.pk,
            'title': batch.program.title,
            'module': batch.program.module,
            'slug': batch.program.slug,
        } if batch.program else None,
        'start_date': batch.start_date,
        'end_date': batch.end_date,
        'status': batch.status,
        'capacity': batch.capacity,
        'description': batch.description,
        'enrolled_count': batch.students.count(),
        'created_at': batch.created_at,
        'updated_at': batch.updated_at,
    }
    if include_students:
        data['students'] = [
            {
                'id': s.pk,
                'name': f"{s.first_name} {s.last_name}".strip() or s.username,
                'email': s.email,
            }
            for s in batch.students.all()
        ]
    return data


def serialize_placement(placement: CampusPlacement):
    return {
        'id': str(placement.id),
        'student': {
            'id': placement.student.pk,
            'name': f"{placement.student.first_name} {placement.student.last_name}".strip() or placement.student.username,
            'email': placement.student.email,
        },
        'company': {
            'id': str(placement.company.pk),
            'name': placement.company.name,
            'logo_url': placement.company.logo_url,
        } if placement.company else None,
        'company_name': placement.company_name or (placement.company.name if placement.company else ''),
        'opportunity': {
            'id': str(placement.opportunity.pk),
            'title': placement.opportunity.title,
            'type': placement.opportunity.opportunity_type,
        } if placement.opportunity else None,
        'role_title': placement.role_title,
        'placement_type': placement.placement_type,
        'compensation': placement.compensation,
        'status': placement.status,
        'placed_at': placement.placed_at,
        'created_at': placement.created_at,
    }


def serialize_partnership(partnership: CollegePartnership):
    return {
        'id': str(partnership.id),
        'company': {
            'id': str(partnership.company.pk),
            'name': partnership.company.name,
            'city': partnership.company.city,
            'website': partnership.company.website,
            'logo_url': partnership.company.logo_url,
        },
        'partnership_type': partnership.partnership_type,
        'status': partnership.status,
        'mou_signed_date': partnership.mou_signed_date,
        'contact_person': partnership.contact_person,
        'notes': partnership.notes,
        'created_at': partnership.created_at,
        'updated_at': partnership.updated_at,
    }


# ==============================================================================
# 1. COLLEGE DASHBOARD OVERVIEW & PROFILE
# ==============================================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsCollegeAdministrator])
def college_dashboard(request):
    college = get_user_college(request)
    if not college:
        return Response({'error': 'No approved college affiliation found for this user.'}, status=403)

    student_memberships = CollegeMembership.objects.filter(institution=college, role=CollegeMembership.Role.STUDENT)
    total_students = student_memberships.count()
    active_students = student_memberships.filter(status=MembershipStatus.ACTIVE).count()
    pending_students = student_memberships.filter(status=MembershipStatus.PENDING).count()

    batches = TrainingBatch.objects.filter(institution=college)
    total_batches = batches.count()
    active_batches = batches.filter(status__in=['upcoming', 'in_progress']).count()

    placements = CampusPlacement.objects.filter(institution=college)
    total_placements = placements.count()
    placed_accepted = placements.filter(status='accepted').count()
    placed_offered = placements.filter(status='offered').count()

    partnerships = CollegePartnership.objects.filter(institution=college, status='active').count()

    recent_batches = [serialize_batch(b) for b in batches.order_by('-created_at')[:5]]
    recent_placements = [serialize_placement(p) for p in placements.order_by('-placed_at', '-created_at')[:5]]
    pending_roster = [serialize_student_membership(m) for m in student_memberships.filter(status=MembershipStatus.PENDING).order_by('-created_at')[:5]]

    return Response({
        'college': serialize_college_profile(college),
        'metrics': {
            'total_students': total_students,
            'active_students': active_students,
            'pending_requests': pending_students,
            'total_batches': total_batches,
            'active_batches': active_batches,
            'total_placements': total_placements,
            'placed_accepted': placed_accepted,
            'placed_offered': placed_offered,
            'active_partnerships': partnerships,
        },
        'recent_batches': recent_batches,
        'recent_placements': recent_placements,
        'pending_students': pending_roster,
    })


@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated, IsCollegeAdministrator])
def college_profile(request):
    college = get_user_college(request)
    if not college:
        return Response({'error': 'No approved college affiliation found for this user.'}, status=403)

    if request.method == 'GET':
        return Response(serialize_college_profile(college))

    serializer = CollegeProfileUpdateSerializer(data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    validated = serializer.validated_data

    for attr, val in validated.items():
        setattr(college, attr, val)
    college.save()

    return Response(serialize_college_profile(college))


# ==============================================================================
# 2. STUDENT MEMBERSHIP ROSTER & REVIEWS
# ==============================================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsCollegeAdministrator])
def college_students(request):
    college = get_user_college(request)
    if not college:
        return Response({'error': 'No approved college affiliation found.'}, status=403)

    queryset = CollegeMembership.objects.filter(
        institution=college,
        role=CollegeMembership.Role.STUDENT
    ).select_related('user', 'user__profile').order_by('-created_at')

    status_filter = request.query_params.get('status')
    if status_filter and status_filter != 'all':
        queryset = queryset.filter(status=status_filter)

    search = request.query_params.get('q', '').strip()
    if search:
        queryset = queryset.filter(
            Q(user__first_name__icontains=search) |
            Q(user__last_name__icontains=search) |
            Q(user__email__icontains=search) |
            Q(user__profile__phone_number__icontains=search)
        )

    paginator = CollegePagination()
    page = paginator.paginate_queryset(queryset, request)
    return paginator.get_paginated_response([serialize_student_membership(m) for m in page])


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsCollegeAdministrator])
def college_student_review(request, membership_id):
    college = get_user_college(request)
    if not college:
        return Response({'error': 'No approved college affiliation found.'}, status=403)

    serializer = StudentMembershipReviewSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    action = serializer.validated_data['action']

    with transaction.atomic():
        try:
            membership = CollegeMembership.objects.select_for_update().get(
                pk=membership_id,
                institution=college,
                role=CollegeMembership.Role.STUDENT
            )
        except CollegeMembership.DoesNotExist:
            return Response({'error': 'Student membership not found in this institution.'}, status=404)

        if action in ['approve', 'reactivate']:
            # Enforce single active college constraint across the platform
            existing_active = CollegeMembership.objects.filter(
                user=membership.user,
                role=CollegeMembership.Role.STUDENT,
                status=MembershipStatus.ACTIVE
            ).exclude(pk=membership.pk).select_related('institution').first()

            if existing_active:
                return Response({
                    'error': f'Student already has an active affiliation with {existing_active.institution.name}. Their prior affiliation must be deactivated before activating a new one.'
                }, status=409)

            membership.status = MembershipStatus.ACTIVE
            membership.save(update_fields=['status'])

        elif action == 'reject':
            membership.status = MembershipStatus.REJECTED
            membership.save(update_fields=['status'])

        elif action == 'deactivate':
            membership.status = MembershipStatus.INACTIVE
            membership.save(update_fields=['status'])

        AuthAuditLog.objects.create(
            user=request.user,
            event_type=f'college_student_membership_{action}',
            ip_address=request.META.get('REMOTE_ADDR'),
            metadata={'membership_id': membership.pk, 'student_user_id': membership.user_id, 'institution_id': college.pk}
        )
        status_label = {'approve': 'approved', 'reactivate': 'reactivated', 'reject': 'rejected', 'deactivate': 'deactivated'}.get(action, action)
        Notification.objects.create(
            user=membership.user,
            message=f"{college.name}: Your student membership request has been {status_label}."[:250]
        )

    return Response(serialize_student_membership(membership))


# ==============================================================================
# 3. TRAINING BATCHES
# ==============================================================================

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated, IsCollegeAdministrator])
def college_batches(request):
    college = get_user_college(request)
    if not college:
        return Response({'error': 'No approved college affiliation found.'}, status=403)

    if request.method == 'GET':
        queryset = TrainingBatch.objects.filter(institution=college).select_related('program').prefetch_related('students').order_by('-created_at')
        status_filter = request.query_params.get('status')
        if status_filter and status_filter != 'all':
            queryset = queryset.filter(status=status_filter)

        search = request.query_params.get('q', '').strip()
        if search:
            queryset = queryset.filter(Q(name__icontains=search) | Q(program__title__icontains=search))

        paginator = CollegePagination()
        page = paginator.paginate_queryset(queryset, request)
        return paginator.get_paginated_response([serialize_batch(b) for b in page])

    serializer = TrainingBatchSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    program = None
    program_id = data.pop('program_id', None)
    if program_id:
        program = Program.objects.filter(Q(pk=program_id if str(program_id).isdigit() else None) | Q(slug=str(program_id))).first()
        if not program:
            return Response({'error': 'Referenced training program not found.'}, status=400)

    batch = TrainingBatch.objects.create(institution=college, program=program, **data)
    return Response(serialize_batch(batch), status=201)


@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated, IsCollegeAdministrator])
def college_batch_detail(request, pk):
    college = get_user_college(request)
    if not college:
        return Response({'error': 'No approved college affiliation found.'}, status=403)

    batch = get_object_or_404(TrainingBatch.objects.select_related('program').prefetch_related('students'), pk=pk, institution=college)

    if request.method == 'GET':
        return Response(serialize_batch(batch, include_students=True))

    if request.method == 'DELETE':
        batch.delete()
        return Response({'message': 'Training batch removed successfully.'}, status=204)

    serializer = TrainingBatchSerializer(data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    if 'program_id' in data:
        program_id = data.pop('program_id')
        if program_id:
            program = Program.objects.filter(Q(pk=program_id if str(program_id).isdigit() else None) | Q(slug=str(program_id))).first()
            if not program:
                return Response({'error': 'Referenced training program not found.'}, status=400)
            batch.program = program
        else:
            batch.program = None

    for attr, val in data.items():
        setattr(batch, attr, val)
    batch.save()

    return Response(serialize_batch(batch, include_students=True))


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsCollegeAdministrator])
def college_batch_enroll(request, pk):
    college = get_user_college(request)
    if not college:
        return Response({'error': 'No approved college affiliation found.'}, status=403)

    batch = get_object_or_404(TrainingBatch, pk=pk, institution=college)

    serializer = BatchEnrollmentSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    action = serializer.validated_data['action']
    student_ids = serializer.validated_data['student_ids']

    # Tenant verification: all target users must be active student members of THIS institution
    valid_members = CollegeMembership.objects.filter(
        institution=college,
        role=CollegeMembership.Role.STUDENT,
        status=MembershipStatus.ACTIVE,
        user_id__in=student_ids
    ).values_list('user_id', flat=True)

    invalid_ids = set(student_ids) - set(valid_members)
    if invalid_ids:
        return Response({
            'error': f'The following users are not active students of this college: {list(invalid_ids)}'
        }, status=400)

    students = User.objects.filter(pk__in=valid_members)

    with transaction.atomic():
        if action == 'enroll':
            current_count = batch.students.count()
            new_to_add = set(valid_members) - set(batch.students.values_list('pk', flat=True))
            if current_count + len(new_to_add) > batch.capacity:
                return Response({
                    'error': f'Cannot enroll students: exceeds batch capacity of {batch.capacity} (currently {current_count} enrolled, attempting to add {len(new_to_add)}).'
                }, status=400)
            batch.students.add(*students)
            for student in students:
                if student.pk in new_to_add:
                    Notification.objects.create(
                        user=student,
                        message=f"{college.name}: You have been assigned to training batch '{batch.name}'."[:250]
                    )
        elif action == 'unenroll':
            batch.students.remove(*students)

    return Response(serialize_batch(batch, include_students=True))


# ==============================================================================
# 4. CAMPUS PLACEMENTS & CORPORATE PARTNERSHIPS
# ==============================================================================

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated, IsCollegeAdministrator])
def college_placements(request):
    college = get_user_college(request)
    if not college:
        return Response({'error': 'No approved college affiliation found.'}, status=403)

    if request.method == 'GET':
        queryset = CampusPlacement.objects.filter(
            institution=college
        ).select_related('student', 'company', 'opportunity').order_by('-placed_at', '-created_at')

        status_filter = request.query_params.get('status')
        if status_filter and status_filter != 'all':
            queryset = queryset.filter(status=status_filter)

        placement_type = request.query_params.get('placement_type')
        if placement_type and placement_type != 'all':
            queryset = queryset.filter(placement_type=placement_type)

        search = request.query_params.get('q', '').strip()
        if search:
            queryset = queryset.filter(
                Q(student__first_name__icontains=search) |
                Q(student__last_name__icontains=search) |
                Q(role_title__icontains=search) |
                Q(company_name__icontains=search)
            )

        paginator = CollegePagination()
        page = paginator.paginate_queryset(queryset, request)
        return paginator.get_paginated_response([serialize_placement(p) for p in page])

    serializer = CampusPlacementSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    # Tenant check: Student must be active member of this college
    student_id = data.pop('student_id')
    is_active_student = CollegeMembership.objects.filter(
        institution=college,
        user_id=student_id,
        role=CollegeMembership.Role.STUDENT,
        status=MembershipStatus.ACTIVE
    ).exists()
    if not is_active_student:
        return Response({'error': 'Student is not an active member of this institution.'}, status=400)

    student = get_object_or_404(User, pk=student_id)

    company = None
    company_id = data.pop('company_id', None)
    if company_id:
        company = Company.objects.filter(pk=company_id, approval_status=OrganizationStatus.APPROVED).first()

    opportunity = None
    opportunity_id = data.pop('opportunity_id', None)
    if opportunity_id:
        opportunity = Opportunity.objects.filter(pk=opportunity_id, status=OpportunityStatus.APPROVED).first()
        if opportunity and not company:
            company = opportunity.company

    company_name = data.pop('company_name', '')
    if not company_name and company:
        company_name = company.name

    placement = CampusPlacement.objects.create(
        institution=college,
        student=student,
        company=company,
        company_name=company_name,
        opportunity=opportunity,
        **data
    )
    return Response(serialize_placement(placement), status=201)


@api_view(['PATCH', 'DELETE'])
@permission_classes([IsAuthenticated, IsCollegeAdministrator])
def college_placement_detail(request, pk):
    college = get_user_college(request)
    if not college:
        return Response({'error': 'No approved college affiliation found.'}, status=403)

    placement = get_object_or_404(CampusPlacement, pk=pk, institution=college)

    if request.method == 'DELETE':
        placement.delete()
        return Response({'message': 'Placement record deleted.'}, status=204)

    serializer = CampusPlacementSerializer(data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    for attr, val in data.items():
        if attr not in ['student_id', 'company_id', 'opportunity_id']:
            setattr(placement, attr, val)
    placement.save()

    return Response(serialize_placement(placement))


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated, IsCollegeAdministrator])
def college_partnerships(request):
    college = get_user_college(request)
    if not college:
        return Response({'error': 'No approved college affiliation found.'}, status=403)

    if request.method == 'GET':
        queryset = CollegePartnership.objects.filter(
            institution=college
        ).select_related('company').order_by('-created_at')

        status_filter = request.query_params.get('status')
        if status_filter and status_filter != 'all':
            queryset = queryset.filter(status=status_filter)

        search = request.query_params.get('q', '').strip()
        if search:
            queryset = queryset.filter(company__name__icontains=search)

        paginator = CollegePagination()
        page = paginator.paginate_queryset(queryset, request)
        return paginator.get_paginated_response([serialize_partnership(p) for p in page])

    serializer = CollegePartnershipSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    company_id = data.pop('company_id')
    company = Company.objects.filter(pk=company_id, approval_status=OrganizationStatus.APPROVED).first()
    if not company:
        return Response({'error': 'Approved partner company not found.'}, status=400)

    if CollegePartnership.objects.filter(institution=college, company=company).exists():
        return Response({'error': f'A partnership with {company.name} already exists.'}, status=409)

    partnership = CollegePartnership.objects.create(
        institution=college,
        company=company,
        **data
    )
    return Response(serialize_partnership(partnership), status=201)


@api_view(['PATCH', 'DELETE'])
@permission_classes([IsAuthenticated, IsCollegeAdministrator])
def college_partnership_detail(request, pk):
    college = get_user_college(request)
    if not college:
        return Response({'error': 'No approved college affiliation found.'}, status=403)

    partnership = get_object_or_404(CollegePartnership, pk=pk, institution=college)

    if request.method == 'DELETE':
        partnership.delete()
        return Response({'message': 'Partnership record removed.'}, status=204)

    serializer = CollegePartnershipSerializer(data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    if 'company_id' in data:
        data.pop('company_id')  # Company association cannot be changed once established

    for attr, val in data.items():
        setattr(partnership, attr, val)
    partnership.save()

    return Response(serialize_partnership(partnership))


# ==============================================================================
# 5. CATALOG DATA (Available Programs, Companies & Opportunities for selection)
# ==============================================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsCollegeAdministrator])
def college_catalog(request):
    """Provides selectable programs, approved partner companies, and opportunities for modals."""
    programs = Program.objects.all().order_by('title')
    companies = Company.objects.filter(approval_status=OrganizationStatus.APPROVED).order_by('name')
    opportunities = Opportunity.objects.filter(status=OpportunityStatus.APPROVED).select_related('company').order_by('title')

    return Response({
        'programs': [{'id': p.pk, 'title': p.title, 'module': p.module, 'slug': p.slug} for p in programs],
        'companies': [{'id': str(c.pk), 'name': c.name, 'city': c.city, 'website': c.website, 'logo_url': c.logo_url} for c in companies],
        'opportunities': [{
            'id': str(o.pk),
            'title': o.title,
            'type': o.opportunity_type,
            'company_id': str(o.company_id),
            'company_name': o.company.name,
            'compensation': o.compensation,
        } for o in opportunities],
    })
