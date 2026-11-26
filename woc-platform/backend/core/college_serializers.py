from rest_framework import serializers
from urllib.parse import urlsplit
from .organization_serializers import StrictInputSerializer
from .models import (
    Institution, CollegeMembership, MembershipStatus,
    TrainingBatch, CampusPlacement, CollegePartnership, Program, Company, Opportunity
)


def validate_secure_url(value, field_name="URL"):
    if not value:
        return value
    value = str(value).strip()
    if not value.startswith("https://"):
        raise serializers.ValidationError(f"{field_name} must use a secure HTTPS URL.")
    split = urlsplit(value)
    if split.username is not None or split.password is not None:
        raise serializers.ValidationError(f"{field_name} cannot contain embedded credentials.")
    if not split.netloc or "." not in split.netloc:
        raise serializers.ValidationError(f"{field_name} must have a valid domain.")
    return value


class CollegeProfileUpdateSerializer(StrictInputSerializer):
    phone = serializers.CharField(max_length=30, required=False, allow_blank=True)
    principal_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    logo_url = serializers.URLField(max_length=500, required=False, allow_blank=True)
    description = serializers.CharField(max_length=5000, required=False, allow_blank=True)
    website = serializers.URLField(max_length=500, required=False, allow_blank=True)
    contact_email = serializers.EmailField(max_length=254, required=False, allow_blank=True)
    address = serializers.CharField(max_length=2000, required=False, allow_blank=True)
    city = serializers.CharField(max_length=100, required=False, allow_blank=True)

    def validate_website(self, value):
        return validate_secure_url(value, "Official website")

    def validate_logo_url(self, value):
        return validate_secure_url(value, "Institution logo URL")


class StudentMembershipReviewSerializer(StrictInputSerializer):
    action = serializers.ChoiceField(choices=['approve', 'reject', 'deactivate', 'reactivate'])
    note = serializers.CharField(max_length=500, required=False, allow_blank=True)


class TrainingBatchSerializer(StrictInputSerializer):
    name = serializers.CharField(max_length=150)
    program_id = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    start_date = serializers.DateField(required=False, allow_null=True)
    end_date = serializers.DateField(required=False, allow_null=True)
    capacity = serializers.IntegerField(min_value=1, max_value=2000, required=False, default=50)
    description = serializers.CharField(max_length=3000, required=False, allow_blank=True)
    status = serializers.ChoiceField(
        choices=['upcoming', 'in_progress', 'completed', 'cancelled'],
        required=False,
        default='upcoming'
    )

    def validate(self, attrs):
        start = attrs.get('start_date')
        end = attrs.get('end_date')
        if start and end and end < start:
            raise serializers.ValidationError({"end_date": "End date cannot be earlier than start date."})
        return attrs


class BatchEnrollmentSerializer(StrictInputSerializer):
    action = serializers.ChoiceField(choices=['enroll', 'unenroll'])
    student_ids = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1,
        allow_empty=False
    )


class CampusPlacementSerializer(StrictInputSerializer):
    student_id = serializers.IntegerField()
    company_id = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    company_name = serializers.CharField(max_length=200, required=False, allow_blank=True)
    opportunity_id = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    role_title = serializers.CharField(max_length=150)
    placement_type = serializers.ChoiceField(choices=['job', 'internship'], required=False, default='job')
    compensation = serializers.CharField(max_length=100, required=False, allow_blank=True)
    status = serializers.ChoiceField(choices=['offered', 'accepted', 'declined'], required=False, default='offered')
    placed_at = serializers.DateField(required=False, allow_null=True)


class CollegePartnershipSerializer(StrictInputSerializer):
    company_id = serializers.CharField()
    partnership_type = serializers.CharField(max_length=100, required=False, default='Recruitment & Training')
    status = serializers.ChoiceField(choices=['active', 'pending', 'ended'], required=False, default='active')
    mou_signed_date = serializers.DateField(required=False, allow_null=True)
    contact_person = serializers.CharField(max_length=150, required=False, allow_blank=True)
    notes = serializers.CharField(max_length=3000, required=False, allow_blank=True)
