from rest_framework import serializers
from .organization_serializers import StrictInputSerializer
from .college_serializers import validate_secure_url


class StudentProfileUpdateSerializer(StrictInputSerializer):
    graduation_year = serializers.IntegerField(min_value=1950,max_value=2100,required=False,allow_null=True)
    name = serializers.CharField(max_length=150, required=False)
    institution = serializers.CharField(max_length=200, required=False, allow_blank=True)
    bio = serializers.CharField(max_length=2000, required=False, allow_blank=True)
    city = serializers.CharField(max_length=100, required=False, allow_blank=True)
    qualification = serializers.CharField(max_length=200, required=False, allow_blank=True)
    skills = serializers.ListField(
        child=serializers.CharField(max_length=60),
        max_length=30,
        required=False
    )
    interests = serializers.ListField(
        child=serializers.CharField(max_length=60),
        max_length=30,
        required=False
    )
    career_goals = serializers.CharField(max_length=2000, required=False, allow_blank=True)
    resume_url = serializers.URLField(max_length=500, required=False, allow_blank=True)
    linkedin_url = serializers.URLField(max_length=500, required=False, allow_blank=True)
    github_url = serializers.URLField(max_length=500, required=False, allow_blank=True)

    def validate_resume_url(self, value):
        return validate_secure_url(value, "Resume URL")

    def validate_linkedin_url(self, value):
        return validate_secure_url(value, "LinkedIn URL")

    def validate_github_url(self, value):
        return validate_secure_url(value, "GitHub URL")

    def validate_skills(self, value):
        cleaned = []
        seen = set()
        for item in value:
            s = item.strip()
            if s and s.lower() not in seen:
                seen.add(s.lower())
                cleaned.append(s)
        return cleaned

    def validate_interests(self, value):
        cleaned = []
        seen = set()
        for item in value:
            s = item.strip()
            if s and s.lower() not in seen:
                seen.add(s.lower())
                cleaned.append(s)
        return cleaned


class CollegeMembershipRequestSerializer(StrictInputSerializer):
    institution_id = serializers.IntegerField(min_value=1)


class OpportunityBookmarkSerializer(StrictInputSerializer):
    action = serializers.ChoiceField(choices=['save', 'remove', 'toggle'], required=False, default='toggle')


class OpportunityTrackSerializer(StrictInputSerializer):
    action = serializers.ChoiceField(choices=['click', 'update_status'])
    status = serializers.ChoiceField(
        choices=['applied', 'interviewing', 'offer_received', 'rejected', 'withdrawn'],
        required=False
    )
    applied_at = serializers.DateField(required=False, allow_null=True)
    notes = serializers.CharField(max_length=2000, required=False, allow_blank=True)

    def validate(self, attrs):
        if attrs.get('action') == 'update_status' and not attrs.get('status'):
            raise serializers.ValidationError({'status': 'Status is required when updating application status.'})
        return attrs
