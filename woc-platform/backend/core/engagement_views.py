from django.contrib.auth.models import User
from django.db import transaction, IntegrityError
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination

from .models import (
    Institution, CollegeMembership, MembershipStatus, OrganizationStatus,
    CampusEvent, EventRegistration, StudentClub, ClubMembership,
    CampusLeadership, CampusAnnouncement, Notification, AuthAuditLog
)
from .organization_access import IsCollegeAdministrator, IsPlatformSuperAdmin, active_colleges
from .college_views import get_user_college
from .engagement_serializers import (
    CampusEventSerializer, EventParticipantUpdateSerializer,
    StudentClubSerializer, ClubMembershipReviewSerializer,
    CampusLeadershipAssignSerializer, CampusAnnouncementSerializer,
    SuperAdminEngagementModerationSerializer, DEFAULT_ROLE_PERMISSIONS
)


class EngagementPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 50


def _student_active_college(user):
    m = active_colleges(user, CollegeMembership.Role.STUDENT).select_related('institution').first()
    return m.institution if m else None


def serialize_event(event: CampusEvent, user=None):
    reg_count = event.registrations.exclude(status=EventRegistration.Status.CANCELLED).count()
    attended_count = event.registrations.filter(status=EventRegistration.Status.ATTENDED).count()
    my_reg = None
    if user and user.is_authenticated:
        r = event.registrations.filter(student=user).first()
        if r:
            my_reg = {
                'id': str(r.id),
                'status': r.status,
                'achievement': r.achievement,
                'registered_at': r.registered_at,
            }
    return {
        'id': str(event.id),
        'institution_id': event.institution_id,
        'institution_name': event.institution.name,
        'title': event.title,
        'event_type': event.event_type,
        'description': event.description,
        'eligibility': event.eligibility,
        'venue': event.venue,
        'event_date': event.event_date,
        'end_date': event.end_date,
        'registration_deadline': event.registration_deadline,
        'capacity': event.capacity,
        'registered_count': reg_count,
        'attended_count': attended_count,
        'visibility': event.visibility,
        'status': event.status,
        'moderation_note': event.moderation_note,
        'my_registration': my_reg,
        'created_at': event.created_at,
    }


def serialize_club(club: StudentClub, user=None):
    approved_count = club.memberships.filter(status=ClubMembership.Status.APPROVED).count()
    pending_count = club.memberships.filter(status=ClubMembership.Status.PENDING).count()
    my_status = None
    if user and user.is_authenticated:
        m = club.memberships.filter(student=user).first()
        my_status = m.status if m else None
    return {
        'id': str(club.id),
        'institution_id': club.institution_id,
        'institution_name': club.institution.name,
        'name': club.name,
        'category': club.category,
        'description': club.description,
        'status': club.status,
        'moderation_note': club.moderation_note,
        'members_count': approved_count,
        'pending_count': pending_count,
        'my_membership_status': my_status,
        'created_at': club.created_at,
    }


def serialize_leadership(role_obj: CampusLeadership):
    student = role_obj.student
    return {
        'id': str(role_obj.id),
        'institution_id': role_obj.institution_id,
        'institution_name': role_obj.institution.name,
        'student': {
            'id': student.pk,
            'name': f"{student.first_name} {student.last_name}".strip() or student.username,
            'email': student.email,
        },
        'role': role_obj.role,
        'club': {'id': str(role_obj.club.id), 'name': role_obj.club.name} if role_obj.club else None,
        'title': role_obj.title,
        'responsibilities': role_obj.responsibilities,
        'permissions': role_obj.permissions or [],
        'status': role_obj.status,
        'activity_log': role_obj.activity_log or [],
        'assigned_at': role_obj.assigned_at,
        'revoked_at': role_obj.revoked_at,
    }


def serialize_announcement(ann: CampusAnnouncement):
    return {
        'id': str(ann.id),
        'institution_name': ann.institution.name,
        'club': {'id': str(ann.club.id), 'name': ann.club.name} if ann.club else None,
        'author_name': (f"{ann.author.first_name} {ann.author.last_name}".strip() or ann.author.username) if ann.author else 'Campus Admin',
        'title': ann.title,
        'content': ann.content,
        'scope': ann.scope,
        'is_moderated_hidden': ann.is_moderated_hidden,
        'created_at': ann.created_at,
    }


# ==============================================================================
# 1. COLLEGE ADMIN — EVENTS, PARTICIPANTS, CLUBS, LEADERSHIP, ANNOUNCEMENTS
# ==============================================================================

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated, IsCollegeAdministrator])
def college_events(request):
    college = get_user_college(request)
    if not college:
        return Response({'error': 'No approved college affiliation found.'}, status=403)

    if request.method == 'GET':
        qs = CampusEvent.objects.filter(institution=college).select_related('institution').order_by('event_date')
        status_filter = request.query_params.get('status')
        if status_filter and status_filter != 'all':
            qs = qs.filter(status=status_filter)
        event_type = request.query_params.get('event_type')
        if event_type and event_type != 'all':
            qs = qs.filter(event_type=event_type)
        paginator = EngagementPagination()
        page = paginator.paginate_queryset(qs, request)
        return paginator.get_paginated_response([serialize_event(e) for e in page])

    serializer = CampusEventSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    event = CampusEvent.objects.create(
        institution=college,
        created_by=request.user,
        **serializer.validated_data
    )
    return Response(serialize_event(event), status=201)


@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated, IsCollegeAdministrator])
def college_event_detail(request, pk):
    college = get_user_college(request)
    if not college:
        return Response({'error': 'No approved college affiliation found.'}, status=403)

    event = get_object_or_404(CampusEvent.objects.select_related('institution'), pk=pk, institution=college)

    if request.method == 'GET':
        regs = event.registrations.select_related('student').order_by('-registered_at')
        data = serialize_event(event)
        data['participants'] = [
            {
                'registration_id': str(r.id),
                'student_id': r.student_id,
                'name': f"{r.student.first_name} {r.student.last_name}".strip() or r.student.username,
                'email': r.student.email,
                'status': r.status,
                'achievement': r.achievement,
                'notes': r.notes,
                'registered_at': r.registered_at,
            }
            for r in regs
        ]
        return Response(data)

    if request.method == 'DELETE':
        event.delete()
        return Response({'message': 'Event deleted.'}, status=204)

    if event.status == CampusEvent.Status.SUSPENDED:
        return Response({'error': 'This event has been suspended by a platform moderator and cannot be edited.'}, status=403)

    old_date = event.event_date
    old_status = event.status
    serializer = CampusEventSerializer(data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    for k, v in serializer.validated_data.items():
        setattr(event, k, v)
    event.save()

    # Notify active registrants on cancellation or schedule change
    notify_msg = None
    if old_status != event.status and event.status == CampusEvent.Status.CANCELLED:
        notify_msg = f"{college.name}: Event '{event.title}' has been cancelled."[:250]
    elif old_date != event.event_date:
        notify_msg = f"{college.name}: Schedule updated for '{event.title}'."[:250]

    if notify_msg:
        active_regs = event.registrations.filter(status=EventRegistration.Status.REGISTERED).select_related('student')
        for r in active_regs:
            Notification.objects.create(user=r.student, message=notify_msg)

    return Response(serialize_event(event))


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsCollegeAdministrator])
def college_event_participant_update(request, pk, reg_id):
    college = get_user_college(request)
    if not college:
        return Response({'error': 'No approved college affiliation found.'}, status=403)

    event = get_object_or_404(CampusEvent, pk=pk, institution=college)
    reg = get_object_or_404(EventRegistration.objects.select_related('student'), pk=reg_id, event=event)

    serializer = EventParticipantUpdateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    for k, v in serializer.validated_data.items():
        setattr(reg, k, v)
    reg.save()

    if reg.achievement:
        Notification.objects.create(
            user=reg.student,
            message=f"{college.name}: Achievement recorded for '{event.title}' — {reg.achievement}"[:250]
        )

    return Response({
        'registration_id': str(reg.id),
        'student_id': reg.student_id,
        'status': reg.status,
        'achievement': reg.achievement,
        'notes': reg.notes,
    })


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated, IsCollegeAdministrator])
def college_clubs(request):
    college = get_user_college(request)
    if not college:
        return Response({'error': 'No approved college affiliation found.'}, status=403)

    if request.method == 'GET':
        qs = StudentClub.objects.filter(institution=college).select_related('institution').order_by('name')
        return Response({'results': [serialize_club(c) for c in qs]})

    serializer = StudentClubSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    if StudentClub.objects.filter(institution=college, name__iexact=serializer.validated_data['name']).exists():
        return Response({'error': 'A club or chapter with this name already exists at your institution.'}, status=409)
    club = StudentClub.objects.create(institution=college, **serializer.validated_data)
    return Response(serialize_club(club), status=201)


@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated, IsCollegeAdministrator])
def college_club_detail(request, pk):
    college = get_user_college(request)
    if not college:
        return Response({'error': 'No approved college affiliation found.'}, status=403)

    club = get_object_or_404(StudentClub.objects.select_related('institution'), pk=pk, institution=college)

    if request.method == 'GET':
        memberships = club.memberships.select_related('student').order_by('-joined_at')
        data = serialize_club(club)
        data['members'] = [
            {
                'membership_id': str(m.id),
                'student_id': m.student_id,
                'name': f"{m.student.first_name} {m.student.last_name}".strip() or m.student.username,
                'email': m.student.email,
                'status': m.status,
                'joined_at': m.joined_at,
            }
            for m in memberships
        ]
        return Response(data)

    if request.method == 'DELETE':
        club.delete()
        return Response({'message': 'Club deleted.'}, status=204)

    if club.status == StudentClub.Status.SUSPENDED:
        return Response({'error': 'This club is suspended by a platform moderator.'}, status=403)

    serializer = StudentClubSerializer(data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    for k, v in serializer.validated_data.items():
        setattr(club, k, v)
    club.save()
    return Response(serialize_club(club))


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsCollegeAdministrator])
def college_club_member_review(request, pk, membership_id):
    college = get_user_college(request)
    if not college:
        return Response({'error': 'No approved college affiliation found.'}, status=403)

    club = get_object_or_404(StudentClub, pk=pk, institution=college)
    membership = get_object_or_404(ClubMembership.objects.select_related('student'), pk=membership_id, club=club)

    serializer = ClubMembershipReviewSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    action = serializer.validated_data['action']

    membership.status = ClubMembership.Status.APPROVED if action == 'approve' else ClubMembership.Status.REJECTED
    membership.save(update_fields=['status', 'updated_at'])

    Notification.objects.create(
        user=membership.student,
        message=f"{college.name}: Your membership request for '{club.name}' was {'approved' if action == 'approve' else 'rejected'}."[:250]
    )
    return Response({'membership_id': str(membership.id), 'status': membership.status})


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated, IsCollegeAdministrator])
def college_leadership(request):
    college = get_user_college(request)
    if not college:
        return Response({'error': 'No approved college affiliation found.'}, status=403)

    if request.method == 'GET':
        qs = CampusLeadership.objects.filter(institution=college).select_related('institution', 'student', 'club')
        return Response({'results': [serialize_leadership(l) for l in qs]})

    serializer = CampusLeadershipAssignSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    # Verify student is an active student member of THIS college
    student_id = data.pop('student_id')
    if not CollegeMembership.objects.filter(
        institution=college, user_id=student_id, role=CollegeMembership.Role.STUDENT, status=MembershipStatus.ACTIVE
    ).exists():
        return Response({'error': 'Leadership roles can only be assigned to active students of your institution.'}, status=400)
    student = get_object_or_404(User, pk=student_id)

    club = None
    club_id = data.pop('club_id', None)
    if club_id:
        club = get_object_or_404(StudentClub, pk=club_id, institution=college)

    role = data['role']
    perms = data.pop('permissions', None)
    if perms is None:
        perms = DEFAULT_ROLE_PERMISSIONS.get(role, [])

    assignment = CampusLeadership.objects.create(
        institution=college,
        student=student,
        club=club,
        permissions=perms,
        assigned_by=request.user,
        activity_log=[{'event': 'assigned', 'at': timezone.now().isoformat(), 'by': request.user.email}],
        **data
    )

    Notification.objects.create(
        user=student,
        message=f"{college.name}: You have been assigned as {assignment.get_role_display()}{f' ({assignment.title})' if assignment.title else ''}."[:250]
    )
    AuthAuditLog.objects.create(
        user=request.user,
        event_type='campus_leadership_assigned',
        metadata={'institution_id': college.pk, 'student_id': student.pk, 'role': role}
    )
    return Response(serialize_leadership(assignment), status=201)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsCollegeAdministrator])
def college_leadership_revoke(request, pk):
    college = get_user_college(request)
    if not college:
        return Response({'error': 'No approved college affiliation found.'}, status=403)

    assignment = get_object_or_404(CampusLeadership.objects.select_related('student'), pk=pk, institution=college)
    if assignment.status == CampusLeadership.Status.REVOKED:
        return Response({'error': 'Leadership assignment is already revoked.'}, status=400)

    assignment.status = CampusLeadership.Status.REVOKED
    assignment.revoked_at = timezone.now()
    log = list(assignment.activity_log or [])
    log.append({'event': 'revoked', 'at': timezone.now().isoformat(), 'by': request.user.email})
    assignment.activity_log = log
    assignment.save(update_fields=['status', 'revoked_at', 'activity_log'])

    Notification.objects.create(
        user=assignment.student,
        message=f"{college.name}: Your {assignment.get_role_display()} responsibility has been concluded/revoked."[:250]
    )
    return Response(serialize_leadership(assignment))


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated, IsCollegeAdministrator])
def college_announcements(request):
    college = get_user_college(request)
    if not college:
        return Response({'error': 'No approved college affiliation found.'}, status=403)

    if request.method == 'GET':
        qs = CampusAnnouncement.objects.filter(institution=college).select_related('institution', 'club', 'author')
        return Response({'results': [serialize_announcement(a) for a in qs[:50]]})

    serializer = CampusAnnouncementSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    club = None
    scope = 'college'
    if data.get('club_id'):
        club = get_object_or_404(StudentClub, pk=data['club_id'], institution=college)
        scope = 'club'

    ann = CampusAnnouncement.objects.create(
        institution=college,
        club=club,
        author=request.user,
        title=data['title'],
        content=data['content'],
        scope=scope
    )

    # Notify relevant students
    if club:
        recipients = User.objects.filter(
            club_memberships__club=club, club_memberships__status=ClubMembership.Status.APPROVED
        ).distinct()
    else:
        recipients = User.objects.filter(
            college_memberships__institution=college,
            college_memberships__role=CollegeMembership.Role.STUDENT,
            college_memberships__status=MembershipStatus.ACTIVE
        ).distinct()
    for recipient in recipients[:200]:
        Notification.objects.create(
            user=recipient,
            message=f"{club.name if club else college.name}: {ann.title}"[:250]
        )

    return Response(serialize_announcement(ann), status=201)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsCollegeAdministrator])
def college_engagement_stats(request):
    college = get_user_college(request)
    if not college:
        return Response({'error': 'No approved college affiliation found.'}, status=403)

    events = CampusEvent.objects.filter(institution=college)
    regs = EventRegistration.objects.filter(event__institution=college)
    clubs = StudentClub.objects.filter(institution=college)
    leaders = CampusLeadership.objects.filter(institution=college, status=CampusLeadership.Status.ACTIVE)

    return Response({
        'total_events': events.count(),
        'upcoming_events': events.filter(status__in=[CampusEvent.Status.UPCOMING, CampusEvent.Status.ONGOING]).count(),
        'completed_events': events.filter(status=CampusEvent.Status.COMPLETED).count(),
        'total_registrations': regs.exclude(status=EventRegistration.Status.CANCELLED).count(),
        'total_attended': regs.filter(status=EventRegistration.Status.ATTENDED).count(),
        'active_clubs': clubs.filter(status=StudentClub.Status.ACTIVE).count(),
        'pending_club_requests': ClubMembership.objects.filter(club__institution=college, status=ClubMembership.Status.PENDING).count(),
        'active_leaders': leaders.count(),
    })


# ==============================================================================
# 2. STUDENT — EVENTS, CLUBS, LEADERSHIP, ACHIEVEMENTS, ANNOUNCEMENTS
# ==============================================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def student_engagement_overview(request):
    user = request.user
    college = _student_active_college(user)

    # Eligible events: public OR active affiliated college (excluding suspended)
    event_q = Q(visibility=CampusEvent.Visibility.PUBLIC)
    if college:
        event_q |= Q(institution=college)

    events_qs = CampusEvent.objects.filter(event_q).exclude(
        status=CampusEvent.Status.SUSPENDED
    ).select_related('institution').order_by('event_date')

    upcoming_events = [
        serialize_event(e, user)
        for e in events_qs.filter(status__in=[CampusEvent.Status.UPCOMING, CampusEvent.Status.ONGOING])[:20]
    ]

    my_regs = EventRegistration.objects.filter(student=user).select_related('event', 'event__institution').order_by('-registered_at')
    my_events = [
        {
            'registration_id': str(r.id),
            'status': r.status,
            'achievement': r.achievement,
            'registered_at': r.registered_at,
            'event': serialize_event(r.event, user),
        }
        for r in my_regs
    ]
    achievements = [
        {
            'id': str(r.id),
            'title': r.achievement,
            'event_title': r.event.title,
            'institution_name': r.event.institution.name,
            'event_date': r.event.event_date,
        }
        for r in my_regs if r.achievement
    ]

    # Clubs of active affiliated college
    clubs = []
    announcements = []
    if college:
        club_qs = StudentClub.objects.filter(institution=college, status=StudentClub.Status.ACTIVE).select_related('institution')
        clubs = [serialize_club(c, user) for c in club_qs]

        approved_club_ids = list(
            ClubMembership.objects.filter(student=user, status=ClubMembership.Status.APPROVED).values_list('club_id', flat=True)
        )
        ann_qs = CampusAnnouncement.objects.filter(
            institution=college, is_moderated_hidden=False
        ).filter(Q(scope='college') | Q(club_id__in=approved_club_ids)).select_related('institution', 'club', 'author')[:20]
        announcements = [serialize_announcement(a) for a in ann_qs]

    leadership = [
        serialize_leadership(l)
        for l in CampusLeadership.objects.filter(
            student=user, status=CampusLeadership.Status.ACTIVE
        ).select_related('institution', 'student', 'club')
    ]

    return Response({
        'affiliated_college': {'id': college.pk, 'name': college.name, 'city': college.city} if college else None,
        'stats': {
            'registered_events': my_regs.exclude(status=EventRegistration.Status.CANCELLED).count(),
            'attended_events': my_regs.filter(status=EventRegistration.Status.ATTENDED).count(),
            'approved_clubs': ClubMembership.objects.filter(student=user, status=ClubMembership.Status.APPROVED).count(),
            'active_leadership_roles': len(leadership),
            'achievements_count': len(achievements),
        },
        'upcoming_events': upcoming_events,
        'my_registrations': my_events,
        'clubs': clubs,
        'leadership_roles': leadership,
        'achievements': achievements,
        'announcements': announcements,
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def student_event_register(request, pk):
    user = request.user
    college = _student_active_college(user)

    with transaction.atomic():
        event = get_object_or_404(CampusEvent.objects.select_for_update().select_related('institution'), pk=pk)

        if event.status not in [CampusEvent.Status.UPCOMING, CampusEvent.Status.ONGOING]:
            return Response({'error': 'Registration is only open for upcoming or ongoing events.'}, status=400)
        if event.visibility == CampusEvent.Visibility.COLLEGE and (not college or event.institution_id != college.pk):
            return Response({'error': 'This event is restricted to active students of the host institution.'}, status=403)
        if event.registration_deadline and timezone.now() > event.registration_deadline:
            return Response({'error': 'The registration deadline for this event has passed.'}, status=400)

        existing = EventRegistration.objects.select_for_update().filter(event=event, student=user).first()
        if existing and existing.status == EventRegistration.Status.REGISTERED:
            return Response({'error': 'You are already registered for this event.'}, status=409)

        active_count = event.registrations.exclude(status=EventRegistration.Status.CANCELLED).count()
        if active_count >= event.capacity:
            return Response({'error': 'This event has reached full participant capacity.'}, status=400)

        if existing:
            existing.status = EventRegistration.Status.REGISTERED
            existing.save(update_fields=['status', 'updated_at'])
            reg = existing
        else:
            reg = EventRegistration.objects.create(event=event, student=user, status=EventRegistration.Status.REGISTERED)

        Notification.objects.create(
            user=user,
            message=f"{event.institution.name}: Registration confirmed for '{event.title}'."[:250]
        )

    return Response(serialize_event(event, user), status=201)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def student_event_cancel(request, pk):
    user = request.user
    event = get_object_or_404(CampusEvent.objects.select_related('institution'), pk=pk)
    reg = EventRegistration.objects.filter(event=event, student=user, status=EventRegistration.Status.REGISTERED).first()
    if not reg:
        return Response({'error': 'Active registration not found for this event.'}, status=404)

    reg.status = EventRegistration.Status.CANCELLED
    reg.save(update_fields=['status', 'updated_at'])

    Notification.objects.create(
        user=user,
        message=f"{event.institution.name}: Your registration for '{event.title}' has been cancelled."[:250]
    )
    return Response(serialize_event(event, user))


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def student_club_join(request, pk):
    user = request.user
    college = _student_active_college(user)
    club = get_object_or_404(StudentClub.objects.select_related('institution'), pk=pk)

    if club.status != StudentClub.Status.ACTIVE:
        return Response({'error': 'This club is not currently accepting memberships.'}, status=400)
    if not college or club.institution_id != college.pk:
        return Response({'error': 'You can only join clubs at your active affiliated college.'}, status=403)

    existing = ClubMembership.objects.filter(club=club, student=user).first()
    if existing:
        if existing.status == ClubMembership.Status.APPROVED:
            return Response({'error': 'You are already a member of this club.'}, status=409)
        if existing.status == ClubMembership.Status.PENDING:
            return Response({'error': 'Your club membership request is already pending approval.'}, status=409)
        existing.status = ClubMembership.Status.PENDING
        existing.save(update_fields=['status', 'updated_at'])
    else:
        ClubMembership.objects.create(club=club, student=user, status=ClubMembership.Status.PENDING)

    return Response(serialize_club(club, user), status=201)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def student_club_leave(request, pk):
    user = request.user
    club = get_object_or_404(StudentClub.objects.select_related('institution'), pk=pk)
    m = ClubMembership.objects.filter(club=club, student=user, status__in=[ClubMembership.Status.PENDING, ClubMembership.Status.APPROVED]).first()
    if not m:
        return Response({'error': 'No active or pending club membership found.'}, status=404)
    m.status = ClubMembership.Status.LEFT
    m.save(update_fields=['status', 'updated_at'])
    return Response(serialize_club(club, user))


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def student_leader_post_announcement(request):
    """Allows an active Club Leader with explicit 'post_club_announcement' permission to post to their assigned club only."""
    user = request.user
    club_id = request.data.get('club_id')
    if not club_id:
        return Response({'error': 'Club ID is required.'}, status=400)

    club = get_object_or_404(StudentClub.objects.select_related('institution'), pk=club_id)
    leadership = CampusLeadership.objects.filter(
        student=user,
        institution=club.institution,
        club=club,
        status=CampusLeadership.Status.ACTIVE
    ).first()

    if not leadership or 'post_club_announcement' not in (leadership.permissions or []):
        return Response({'error': 'You do not have active club leader permission to post announcements for this club.'}, status=403)

    serializer = CampusAnnouncementSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    ann = CampusAnnouncement.objects.create(
        institution=club.institution,
        club=club,
        author=user,
        title=data['title'],
        content=data['content'],
        scope='club'
    )

    log = list(leadership.activity_log or [])
    log.append({'event': 'posted_announcement', 'title': ann.title, 'at': timezone.now().isoformat()})
    leadership.activity_log = log
    leadership.save(update_fields=['activity_log'])

    members = User.objects.filter(club_memberships__club=club, club_memberships__status=ClubMembership.Status.APPROVED).distinct()
    for member in members[:200]:
        Notification.objects.create(user=member, message=f"{club.name}: {ann.title}"[:250])

    return Response(serialize_announcement(ann), status=201)


# ==============================================================================
# 3. SUPER ADMIN — PLATFORM-WIDE ENGAGEMENT OVERSIGHT & MODERATION
# ==============================================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsPlatformSuperAdmin])
def super_admin_engagement_overview(request):
    events = CampusEvent.objects.select_related('institution').order_by('-created_at')[:50]
    clubs = StudentClub.objects.select_related('institution').order_by('-created_at')[:50]
    announcements = CampusAnnouncement.objects.select_related('institution', 'club', 'author').order_by('-created_at')[:30]

    return Response({
        'summary': {
            'total_events': CampusEvent.objects.count(),
            'active_events': CampusEvent.objects.filter(status__in=[CampusEvent.Status.UPCOMING, CampusEvent.Status.ONGOING]).count(),
            'suspended_events': CampusEvent.objects.filter(status=CampusEvent.Status.SUSPENDED).count(),
            'total_clubs': StudentClub.objects.count(),
            'suspended_clubs': StudentClub.objects.filter(status=StudentClub.Status.SUSPENDED).count(),
            'active_leadership_roles': CampusLeadership.objects.filter(status=CampusLeadership.Status.ACTIVE).count(),
        },
        'events': [serialize_event(e) for e in events],
        'clubs': [serialize_club(c) for c in clubs],
        'announcements': [serialize_announcement(a) for a in announcements],
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsPlatformSuperAdmin])
def super_admin_moderate_engagement(request):
    serializer = SuperAdminEngagementModerationSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    kind = serializer.validated_data['kind']
    target_id = serializer.validated_data['target_id']
    action = serializer.validated_data['action']
    note = serializer.validated_data.get('note', '')

    if kind == 'event':
        obj = get_object_or_404(CampusEvent, pk=target_id)
        obj.status = CampusEvent.Status.SUSPENDED if action == 'suspend' else CampusEvent.Status.UPCOMING
        obj.moderation_note = note
        obj.save(update_fields=['status', 'moderation_note', 'updated_at'])
    elif kind == 'club':
        obj = get_object_or_404(StudentClub, pk=target_id)
        obj.status = StudentClub.Status.SUSPENDED if action == 'suspend' else StudentClub.Status.ACTIVE
        obj.moderation_note = note
        obj.save(update_fields=['status', 'moderation_note', 'updated_at'])
    else:
        obj = get_object_or_404(CampusAnnouncement, pk=target_id)
        obj.is_moderated_hidden = (action == 'suspend')
        obj.save(update_fields=['is_moderated_hidden'])

    AuthAuditLog.objects.create(
        user=request.user,
        event_type=f'super_admin_moderate_{kind}_{action}',
        metadata={'target_id': str(target_id), 'note': note}
    )
    return Response({'message': f'{kind.capitalize()} {action}ed successfully.', 'target_id': str(target_id), 'action': action})
