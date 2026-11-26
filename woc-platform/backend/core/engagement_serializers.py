from rest_framework import serializers
from .organization_serializers import StrictInputSerializer
from .models import CampusEvent, EventRegistration, StudentClub, ClubMembership, CampusLeadership


ALLOWED_LEADERSHIP_PERMISSIONS = [
    'post_club_announcement',
    'manage_club_activities',
    'assist_event_attendance',
    'coordinate_campus_outreach',
]

DEFAULT_ROLE_PERMISSIONS = {
    CampusLeadership.Role.AMBASSADOR: ['coordinate_campus_outreach'],
    CampusLeadership.Role.COORDINATOR: ['assist_event_attendance', 'coordinate_campus_outreach'],
    CampusLeadership.Role.CLUB_LEADER: ['post_club_announcement', 'manage_club_activities'],
}


class CampusEventSerializer(StrictInputSerializer):
    title = serializers.CharField(max_length=200)
    event_type = serializers.ChoiceField(choices=CampusEvent.EventType.choices)
    description = serializers.CharField(max_length=5000)
    eligibility = serializers.CharField(max_length=300, required=False, allow_blank=True)
    venue = serializers.CharField(max_length=200)
    event_date = serializers.DateTimeField()
    end_date = serializers.DateTimeField(required=False, allow_null=True)
    registration_deadline = serializers.DateTimeField(required=False, allow_null=True)
    capacity = serializers.IntegerField(min_value=1, max_value=10000, required=False, default=100)
    visibility = serializers.ChoiceField(choices=CampusEvent.Visibility.choices, required=False, default=CampusEvent.Visibility.COLLEGE)
    status = serializers.ChoiceField(
        choices=[
            CampusEvent.Status.UPCOMING,
            CampusEvent.Status.ONGOING,
            CampusEvent.Status.COMPLETED,
            CampusEvent.Status.CANCELLED,
        ],
        required=False,
        default=CampusEvent.Status.UPCOMING
    )

    def validate(self, attrs):
        start = attrs.get('event_date')
        end = attrs.get('end_date')
        deadline = attrs.get('registration_deadline')
        if start and end and end < start:
            raise serializers.ValidationError({'end_date': 'End date cannot be earlier than event start date.'})
        if start and deadline and deadline > start:
            raise serializers.ValidationError({'registration_deadline': 'Registration deadline cannot be after the event start time.'})
        return attrs


class EventParticipantUpdateSerializer(StrictInputSerializer):
    status = serializers.ChoiceField(choices=[
        EventRegistration.Status.REGISTERED,
        EventRegistration.Status.ATTENDED,
        EventRegistration.Status.ABSENT,
        EventRegistration.Status.CANCELLED,
    ])
    achievement = serializers.CharField(max_length=200, required=False, allow_blank=True)
    notes = serializers.CharField(max_length=1000, required=False, allow_blank=True)


class StudentClubSerializer(StrictInputSerializer):
    name = serializers.CharField(max_length=150)
    category = serializers.ChoiceField(choices=StudentClub.Category.choices)
    description = serializers.CharField(max_length=3000)
    status = serializers.ChoiceField(
        choices=[StudentClub.Status.ACTIVE, StudentClub.Status.INACTIVE],
        required=False,
        default=StudentClub.Status.ACTIVE
    )


class ClubMembershipReviewSerializer(StrictInputSerializer):
    action = serializers.ChoiceField(choices=['approve', 'reject'])


class CampusLeadershipAssignSerializer(StrictInputSerializer):
    student_id = serializers.IntegerField(min_value=1)
    role = serializers.ChoiceField(choices=CampusLeadership.Role.choices)
    club_id = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    title = serializers.CharField(max_length=150, required=False, allow_blank=True)
    responsibilities = serializers.CharField(max_length=3000, required=False, allow_blank=True)
    permissions = serializers.ListField(
        child=serializers.ChoiceField(choices=ALLOWED_LEADERSHIP_PERMISSIONS),
        required=False
    )


class CampusAnnouncementSerializer(StrictInputSerializer):
    title = serializers.CharField(max_length=200)
    content = serializers.CharField(max_length=4000)
    club_id = serializers.CharField(required=False, allow_null=True, allow_blank=True)


class SuperAdminEngagementModerationSerializer(StrictInputSerializer):
    kind = serializers.ChoiceField(choices=['event', 'club', 'announcement'])
    target_id = serializers.CharField()
    action = serializers.ChoiceField(choices=['suspend', 'restore'])
    note = serializers.CharField(max_length=1000, required=False, allow_blank=True)
