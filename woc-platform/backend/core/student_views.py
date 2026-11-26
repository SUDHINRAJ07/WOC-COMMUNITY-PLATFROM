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
    TrainingBatch, Record, Certificate, Notification, AuthAuditLog,
    Opportunity, OpportunityStatus, SavedOpportunity, OpportunityApplicationLog
)
from .opportunity_views import serialize_opportunity
from .student_serializers import (
    StudentProfileUpdateSerializer, CollegeMembershipRequestSerializer,
    OpportunityBookmarkSerializer, OpportunityTrackSerializer
)


class StudentPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 50


def compute_profile_completion(user):
    p = user.profile
    checks = [
        ('Profile photo', bool(p.photo)),
        ('Education graduation year', bool(p.graduation_year)),
        ('Full name', bool((user.first_name or '').strip())),
        ('Email verified', bool(p.email_verified)),
        ('Mobile verified', bool(p.phone_verified)),
        ('City / Location', bool((p.city or '').strip())),
        ('Educational qualification', bool((p.qualification or '').strip())),
        ('About / Bio', bool((p.bio or '').strip())),
        ('Skills', bool(p.skills and len(p.skills) > 0)),
        ('Interests', bool(p.interests and len(p.interests) > 0)),
        ('Career goals', bool((p.career_goals or '').strip())),
        ('Resume or Portfolio link', bool(p.resume_file or (p.resume_url or '').strip() or (p.linkedin_url or '').strip() or (p.github_url or '').strip())),
    ]
    completed = [label for label, ok in checks if ok]
    missing = [label for label, ok in checks if not ok]
    percentage = int(round((len(completed) / len(checks)) * 100))
    return {
        'percentage': percentage,
        'completed': completed,
        'missing': missing,
    }


def serialize_student_college_membership(m: CollegeMembership):
    return {
        'membership_id': m.pk,
        'institution_id': m.institution_id,
        'institution_name': m.institution.name,
        'institution_city': m.institution.city,
        'institution_verified': m.institution.verified,
        'institution_website': m.institution.website,
        'status': m.status,
        'created_at': m.created_at,
    }


def serialize_student_batch(batch: TrainingBatch, progress_map=None):
    prog = batch.program
    prog_progress = None
    if prog and progress_map is not None:
        prog_progress = progress_map.get(prog.pk)
    return {
        'id': str(batch.id),
        'name': batch.name,
        'institution_name': batch.institution.name,
        'institution_city': batch.institution.city,
        'program': {
            'id': prog.pk,
            'slug': prog.slug,
            'module': prog.module,
            'title': prog.title,
            'duration': prog.duration,
        } if prog else None,
        'start_date': batch.start_date,
        'end_date': batch.end_date,
        'status': batch.status,
        'capacity': batch.capacity,
        'description': batch.description,
        'progress': prog_progress,
    }


def compute_course_progress(record: Record):
    lessons = record.data.get('lessons', []) if isinstance(record.data, dict) else []
    lessons_count = len(set(lessons))
    if record.status == 'completed':
        pct = 100
    elif record.status == 'awaiting_review':
        pct = 90
    else:
        pct = min(80, int(round((lessons_count / 3) * 80)))
    return {
        'record_id': str(record.id),
        'program_id': record.program_id,
        'program_slug': record.program.slug,
        'program_title': record.program.title,
        'status': record.status,
        'lessons_completed': lessons_count,
        'total_lessons': 3,
        'percentage': pct,
        'has_certificate': hasattr(record, 'certificate'),
    }


def serialize_application_log(log: OpportunityApplicationLog):
    return {
        'id': str(log.id),
        'opportunity': serialize_opportunity(log.opportunity),
        'status': log.status,
        'external_click_count': log.external_click_count,
        'last_clicked_at': log.last_clicked_at,
        'applied_at': log.applied_at,
        'notes': log.notes,
        'updated_at': log.updated_at,
    }


def get_recommended_opportunities(user, limit=6):
    p = user.profile
    tokens = set()
    for item in (p.skills or []) + (p.interests or []):
        for word in str(item).lower().replace(',', ' ').split():
            if len(word) >= 2:
                tokens.add(word)

    today = timezone.now().date()
    qs = Opportunity.objects.filter(
        status=OpportunityStatus.APPROVED,
        company__approval_status=OrganizationStatus.APPROVED,
    ).filter(Q(deadline__isnull=True) | Q(deadline__gte=today)).select_related('company').order_by('-created_at')[:50]

    scored = []
    for opp in qs:
        score = 0
        matched = []
        if tokens:
            opp_skills = [str(s).lower() for s in (opp.required_skills or [])]
            opp_text = f"{opp.title} {opp.description} {' '.join(opp_skills)}".lower()
            for tok in tokens:
                if any(tok in sk for sk in opp_skills):
                    score += 3
                    matched.append(tok)
                elif tok in opp_text:
                    score += 1
                    matched.append(tok)
        scored.append((score, opp, sorted(set(matched))))

    scored.sort(key=lambda x: (x[0], x[1].created_at), reverse=True)
    results = []
    for score, opp, matched in scored[:limit]:
        data = serialize_opportunity(opp)
        data['match_score'] = score
        data['matched_keywords'] = matched[:5]
        results.append(data)
    return results


# ==============================================================================
# 1. STUDENT DASHBOARD OVERVIEW & PROFILE
# ==============================================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def student_dashboard(request):
    user = request.user
    completion = compute_profile_completion(user)

    # College affiliation (active first, otherwise latest request)
    memberships = CollegeMembership.objects.filter(
        user=user, role=CollegeMembership.Role.STUDENT
    ).select_related('institution').order_by('-created_at')
    active_m = memberships.filter(status=MembershipStatus.ACTIVE).first()
    current_m = active_m or memberships.first()

    # Learning & progress
    academy_records = list(
        Record.objects.filter(user=user, program__module='academy')
        .select_related('program')
        .order_by('-updated_at')
    )
    progress_list = [compute_course_progress(r) for r in academy_records]
    avg_progress = int(round(sum(x['percentage'] for x in progress_list) / len(progress_list))) if progress_list else 0
    resume_target = next((x for x in progress_list if x['status'] != 'completed'), None)
    completed_courses = sum(1 for x in progress_list if x['status'] == 'completed')

    # Assigned batches
    batches = list(
        TrainingBatch.objects.filter(students=user)
        .select_related('institution', 'program')
        .order_by('-created_at')
    )
    progress_map = {x['program_id']: x for x in progress_list}

    # Saved & tracked opportunities
    saved_ids = list(
        SavedOpportunity.objects.filter(user=user).values_list('opportunity_id', flat=True)
    )
    app_logs = OpportunityApplicationLog.objects.filter(user=user)
    confirmed_apps = app_logs.exclude(status=OpportunityApplicationLog.Status.CLICKED).count()
    external_clicks = app_logs.filter(status=OpportunityApplicationLog.Status.CLICKED).count()

    # Certificates & notifications
    certs_count = Certificate.objects.filter(record__user=user).count()
    unread_notifs = Notification.objects.filter(user=user, read=False).count()

    return Response({
        'profile_completion': completion,
        'college_affiliation': serialize_student_college_membership(current_m) if current_m else None,
        'learning': {
            'enrolled_count': len(academy_records),
            'completed_count': completed_courses,
            'average_progress': avg_progress,
            'resume_target': resume_target,
            'courses': progress_list,
        },
        'batches': {
            'total': len(batches),
            'upcoming': sum(1 for b in batches if b.status == 'upcoming'),
            'in_progress': sum(1 for b in batches if b.status == 'in_progress'),
            'completed': sum(1 for b in batches if b.status == 'completed'),
            'recent': [serialize_student_batch(b, progress_map) for b in batches[:5]],
        },
        'opportunities': {
            'saved_count': len(saved_ids),
            'saved_ids': [str(oid) for oid in saved_ids],
            'confirmed_applications_count': confirmed_apps,
            'external_clicks_count': external_clicks,
            'recommended': get_recommended_opportunities(user, limit=4),
        },
        'certificates_count': certs_count,
        'unread_notifications_count': unread_notifs,
    })


@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
def student_profile(request):
    user = request.user
    profile = user.profile

    if request.method == 'PATCH':
        serializer = StudentProfileUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        if 'name' in data:
            user.first_name = data.pop('name').strip()
            user.save(update_fields=['first_name'])

        for field, val in data.items():
            setattr(profile, field, val)
        profile.save()

    from .views import user_data
    return Response({
        'user': user_data(user),
        'profile_completion': compute_profile_completion(user),
    })


# ==============================================================================
# 2. STUDENT COLLEGE AFFILIATION
# ==============================================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def student_colleges(request):
    q = request.query_params.get('q', '').strip()
    approved = Institution.objects.filter(approval_status=OrganizationStatus.APPROVED)
    if q:
        approved = approved.filter(Q(name__icontains=q) | Q(city__icontains=q))
    approved = approved.order_by('name')[:30]

    memberships = CollegeMembership.objects.filter(
        user=request.user,
        role=CollegeMembership.Role.STUDENT
    ).select_related('institution').order_by('-created_at')

    return Response({
        'colleges': [
            {
                'id': c.pk,
                'name': c.name,
                'city': c.city,
                'website': c.website,
                'verified': c.verified,
                'description': c.description,
            }
            for c in approved
        ],
        'memberships': [serialize_student_college_membership(m) for m in memberships],
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def student_college_request(request):
    serializer = CollegeMembershipRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    institution_id = serializer.validated_data['institution_id']

    college = Institution.objects.filter(
        pk=institution_id,
        approval_status=OrganizationStatus.APPROVED
    ).first()
    if not college:
        return Response({'error': 'Approved institution not found.'}, status=404)

    with transaction.atomic():
        # Lock student's memberships to prevent concurrent conflicting affiliations
        active_elsewhere = CollegeMembership.objects.select_for_update().filter(
            user=request.user,
            role=CollegeMembership.Role.STUDENT,
            status=MembershipStatus.ACTIVE
        ).select_related('institution').first()

        if active_elsewhere:
            if active_elsewhere.institution_id == college.pk:
                return Response({'error': f'You are already an active student member of {college.name}.'}, status=409)
            return Response({
                'error': f'You already have an active affiliation with {active_elsewhere.institution.name}. Leave or deactivate your current college affiliation before joining another.'
            }, status=409)

        existing = CollegeMembership.objects.select_for_update().filter(
            user=request.user,
            institution=college,
            role=CollegeMembership.Role.STUDENT
        ).first()

        if existing:
            if existing.status == MembershipStatus.PENDING:
                return Response({'error': f'Your membership request for {college.name} is already pending review.'}, status=409)
            existing.status = MembershipStatus.PENDING
            existing.save(update_fields=['status'])
            membership = existing
        else:
            membership = CollegeMembership.objects.create(
                user=request.user,
                institution=college,
                role=CollegeMembership.Role.STUDENT,
                status=MembershipStatus.PENDING
            )

        AuthAuditLog.objects.create(
            user=request.user,
            event_type='student_college_membership_requested',
            ip_address=request.META.get('REMOTE_ADDR'),
            metadata={'institution_id': college.pk, 'membership_id': membership.pk}
        )

    return Response(serialize_student_college_membership(membership), status=201)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def student_college_leave(request):
    membership_id = request.data.get('membership_id')
    with transaction.atomic():
        qs = CollegeMembership.objects.select_for_update().filter(
            user=request.user,
            role=CollegeMembership.Role.STUDENT,
            status__in=[MembershipStatus.ACTIVE, MembershipStatus.PENDING]
        )
        if membership_id:
            qs = qs.filter(pk=membership_id)
        membership = qs.select_related('institution').first()
        if not membership:
            return Response({'error': 'No active or pending college membership found.'}, status=404)
        membership.status = MembershipStatus.INACTIVE
        membership.save(update_fields=['status'])
        AuthAuditLog.objects.create(
            user=request.user,
            event_type='student_college_membership_left',
            ip_address=request.META.get('REMOTE_ADDR'),
            metadata={'institution_id': membership.institution_id, 'membership_id': membership.pk}
        )
    return Response(serialize_student_college_membership(membership))


# ==============================================================================
# 3. STUDENT ASSIGNED TRAINING BATCHES
# ==============================================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def student_batches(request):
    batches = TrainingBatch.objects.filter(
        students=request.user
    ).select_related('institution', 'program').order_by('-created_at')

    status_filter = request.query_params.get('status')
    if status_filter and status_filter != 'all':
        batches = batches.filter(status=status_filter)

    academy_records = Record.objects.filter(user=request.user, program__module='academy').select_related('program')
    progress_map = {r.program_id: compute_course_progress(r) for r in academy_records}

    return Response({
        'results': [serialize_student_batch(b, progress_map) for b in batches]
    })


# ==============================================================================
# 4. STUDENT SAVED OPPORTUNITIES & APPLICATION TRACKING
# ==============================================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def student_saved_opportunities(request):
    qs = SavedOpportunity.objects.filter(
        user=request.user,
        opportunity__status=OpportunityStatus.APPROVED,
        opportunity__company__approval_status=OrganizationStatus.APPROVED,
    ).select_related('opportunity', 'opportunity__company').order_by('-created_at')

    paginator = StudentPagination()
    page = paginator.paginate_queryset(qs, request)
    return paginator.get_paginated_response([
        {
            'saved_id': str(s.id),
            'saved_at': s.created_at,
            'opportunity': serialize_opportunity(s.opportunity),
        }
        for s in page
    ])


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def student_opportunity_save(request, pk):
    serializer = OpportunityBookmarkSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    action = serializer.validated_data['action']

    opp = get_object_or_404(
        Opportunity,
        pk=pk,
        status=OpportunityStatus.APPROVED,
        company__approval_status=OrganizationStatus.APPROVED
    )

    existing = SavedOpportunity.objects.filter(user=request.user, opportunity=opp).first()
    if action == 'remove' or (action == 'toggle' and existing):
        if existing:
            existing.delete()
        return Response({'saved': False, 'opportunity_id': str(opp.pk)})

    if not existing:
        try:
            SavedOpportunity.objects.create(user=request.user, opportunity=opp)
        except IntegrityError:
            pass
    return Response({'saved': True, 'opportunity_id': str(opp.pk)})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def student_opportunity_applications(request):
    qs = OpportunityApplicationLog.objects.filter(
        user=request.user
    ).select_related('opportunity', 'opportunity__company').order_by('-updated_at')

    status_filter = request.query_params.get('status')
    if status_filter and status_filter != 'all':
        qs = qs.filter(status=status_filter)

    paginator = StudentPagination()
    page = paginator.paginate_queryset(qs, request)
    return paginator.get_paginated_response([serialize_application_log(item) for item in page])


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def student_opportunity_track(request, pk):
    serializer = OpportunityTrackSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data
    action = data['action']

    opp = get_object_or_404(
        Opportunity,
        pk=pk,
        status=OpportunityStatus.APPROVED,
        company__approval_status=OrganizationStatus.APPROVED
    )

    with transaction.atomic():
        log, _created = OpportunityApplicationLog.objects.select_for_update().get_or_create(
            user=request.user,
            opportunity=opp,
            defaults={'status': OpportunityApplicationLog.Status.CLICKED}
        )

        if action == 'click':
            # External link click tracking MUST NOT overwrite a manual application status or mark as applied
            log.external_click_count += 1
            log.last_clicked_at = timezone.now()
            log.save(update_fields=['external_click_count', 'last_clicked_at', 'updated_at'])
        elif action == 'update_status':
            log.status = data['status']
            if data['status'] == OpportunityApplicationLog.Status.APPLIED and not log.applied_at:
                log.applied_at = data.get('applied_at') or timezone.now().date()
            elif 'applied_at' in data and data['applied_at']:
                log.applied_at = data['applied_at']
            if 'notes' in data:
                log.notes = data['notes']
            log.save()

    return Response(serialize_application_log(log))


# ==============================================================================
# 5. STUDENT CERTIFICATES
# ==============================================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def student_certificates(request):
    certs = Certificate.objects.filter(
        record__user=request.user
    ).select_related('record__program').order_by('-issued_at')

    return Response({
        'results': [
            {
                'id': str(c.id),
                'record_id': str(c.record_id),
                'program_title': c.record.program.title,
                'program_slug': c.record.program.slug,
                'module': c.record.program.module,
                'sample': c.record.program.sample,
                'issued_at': c.issued_at,
            }
            for c in certs
        ]
    })


# No public media route: resumes, evidence and photographs require an authenticated owner.
def validated_upload(upload, photo=False):
    import io, uuid
    from django.core.files.base import ContentFile
    from rest_framework.exceptions import ValidationError
    if not upload or upload.size > 5 * 1024 * 1024:
        raise ValidationError({'error':'Choose a file up to 5 MB.'})
    if photo:
        from PIL import Image, UnidentifiedImageError
        try:
            with Image.open(upload) as image:
                if image.format not in ['JPEG','PNG'] or image.width * image.height > 20000000:
                    raise ValueError('Unsupported image')
                image.verify()
            upload.seek(0)
            with Image.open(upload) as image:
                image = image.convert('RGB')
                image.thumbnail((1000,1000))
                output=io.BytesIO();image.save(output,format='JPEG',quality=88)
            return ContentFile(output.getvalue(),name=uuid.uuid4().hex+'.jpg')
        except (UnidentifiedImageError,ValueError,OSError,Image.DecompressionBombError):
            raise ValidationError({'error':'Choose a valid JPG or PNG photograph.'})
    content=upload.read()
    if not upload.name.lower().endswith('.pdf') or not content.startswith(b'%PDF-') or b'%%EOF' not in content[-2048:]:
        raise ValidationError({'error':'Choose a valid PDF document.'})
    return ContentFile(content,name=uuid.uuid4().hex+'.pdf')

@api_view(['GET','POST','DELETE'])
@permission_classes([IsAuthenticated])
def student_profile_file(request, kind):
    from django.http import FileResponse
    from .models import Profile
    from .views import user_data
    fields={'photo':'photo','resume':'resume_file','document':'supporting_document'}
    if kind not in fields: return Response({'error':'Invalid file kind.'},status=404)
    field=fields[kind]
    if request.method=='GET':
        file=getattr(request.user.profile,field)
        if not file: return Response({'error':'No file uploaded.'},status=404)
        response=FileResponse(file.open('rb'),content_type='image/jpeg' if kind=='photo' else 'application/pdf',as_attachment=kind!='photo',filename='profile.jpg' if kind=='photo' else kind+'.pdf')
        response['Cache-Control']='private, no-store';response['X-Content-Type-Options']='nosniff'
        return response
    content=validated_upload(request.FILES.get('file'),photo=kind=='photo') if request.method=='POST' else None
    with transaction.atomic():
        profile=Profile.objects.select_for_update().get(user=request.user)
        file=getattr(profile,field)
        old_name=file.name
        storage=file.storage
        if request.method=='POST': file.save(content.name,content,save=False)
        else: setattr(profile,field,'')
        profile.save(update_fields=[field])
        if old_name: transaction.on_commit(lambda: storage.delete(old_name))
        AuthAuditLog.objects.create(user=request.user,event_type='profile_file_'+request.method.lower(),metadata={'kind':kind})
    request.user.refresh_from_db()
    return Response({'user':user_data(request.user),'profile_completion':compute_profile_completion(request.user)})
