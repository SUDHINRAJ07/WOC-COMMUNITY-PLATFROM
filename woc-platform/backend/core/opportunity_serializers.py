from rest_framework import serializers
from urllib.parse import urlsplit
from django.core.validators import validate_email
from django.core.exceptions import ValidationError as DjangoValidationError
from .organization_serializers import StrictInputSerializer
from .models import Company, Opportunity, OpportunityType, OpportunityStatus, EmploymentType, WorkMode


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


class CompanyProfileUpdateSerializer(StrictInputSerializer):
    company_type=serializers.CharField(max_length=100,required=False,allow_blank=True)
    cin=serializers.RegexField(r"^[A-Za-z0-9]{21}$",max_length=21,required=False,allow_blank=True)
    address=serializers.CharField(max_length=2000,required=False,allow_blank=True)
    pin_code=serializers.RegexField(r"^[0-9]{6}$",max_length=6,required=False,allow_blank=True)
    designation=serializers.CharField(max_length=150,required=False,allow_blank=True)
    name = serializers.CharField(max_length=200, required=False)
    city = serializers.CharField(max_length=100, required=False, allow_blank=True)
    website = serializers.URLField(max_length=500, required=False)
    contact_email = serializers.EmailField(max_length=254, required=False)
    recruitment_email = serializers.EmailField(max_length=254, required=False, allow_blank=True)
    careers_website = serializers.URLField(max_length=500, required=False, allow_blank=True)
    logo_url = serializers.URLField(max_length=500, required=False, allow_blank=True)
    industry = serializers.CharField(max_length=100, required=False, allow_blank=True)
    company_size = serializers.CharField(max_length=50, required=False, allow_blank=True)
    contact_person = serializers.CharField(max_length=150, required=False, allow_blank=True)
    description = serializers.CharField(max_length=5000, required=False, allow_blank=True)

    def validate_website(self, value):
        return validate_secure_url(value, "Official website")

    def validate_careers_website(self, value):
        return validate_secure_url(value, "Careers website")

    def validate_logo_url(self, value):
        return validate_secure_url(value, "Company logo URL")


class OpportunityInputSerializer(StrictInputSerializer):
    department = serializers.CharField(max_length=150,required=False,allow_blank=True)
    responsibilities = serializers.CharField(max_length=5000,required=False,allow_blank=True)
    eligible_graduation_years = serializers.CharField(max_length=150,required=False,allow_blank=True)
    selection_process = serializers.CharField(max_length=5000,required=False,allow_blank=True)
    benefits = serializers.CharField(max_length=5000,required=False,allow_blank=True)
    opportunity_type = serializers.ChoiceField(choices=OpportunityType.choices)
    title = serializers.CharField(max_length=200)
    description = serializers.CharField(max_length=15000)
    required_skills = serializers.ListField(child=serializers.CharField(max_length=80), required=False, default=list)
    qualification = serializers.CharField(max_length=200, required=False, allow_blank=True)
    experience_level = serializers.CharField(max_length=100, required=False, allow_blank=True)
    employment_type = serializers.ChoiceField(choices=EmploymentType.choices, required=False, default=EmploymentType.FULL_TIME)
    work_mode = serializers.ChoiceField(choices=WorkMode.choices, required=False, default=WorkMode.ON_SITE)
    location = serializers.CharField(max_length=150, required=False, allow_blank=True)
    compensation = serializers.CharField(max_length=100, required=False, allow_blank=True)
    is_paid = serializers.BooleanField(required=False, default=True)
    openings = serializers.IntegerField(required=False, allow_null=True, min_value=1, max_value=9999)
    duration = serializers.CharField(max_length=80, required=False, allow_blank=True)
    recruitment_email = serializers.EmailField(required=False, allow_blank=True, max_length=254)
    careers_url = serializers.URLField(required=False, allow_blank=True, max_length=500)
    deadline = serializers.DateField(required=False, allow_null=True)

    def validate_careers_url(self, value):
        return validate_secure_url(value, "Careers application URL")

    def validate_required_skills(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("Skills must be provided as a list.")
        clean = [str(s).strip() for s in value if str(s).strip()]
        return clean[:30]


class OpportunitySubmissionValidator:
    """Validates that a draft is complete and eligible for Super Admin review."""
    @staticmethod
    def validate_for_submission(opp: Opportunity):
        errors = {}
        if not opp.title or not opp.title.strip():
            errors['title'] = "Title is required for submission."
        if not opp.description or len(opp.description.strip()) < 30:
            errors['description'] = "Description must be at least 30 characters."
        
        has_email = bool(opp.recruitment_email and opp.recruitment_email.strip())
        has_url = bool(opp.careers_url and opp.careers_url.strip())
        if not has_email and not has_url:
            errors['application_destination'] = "Provide at least one valid recruitment email or official careers URL."
        
        if has_url:
            try:
                validate_secure_url(opp.careers_url, "Careers URL")
            except serializers.ValidationError as exc:
                errors['careers_url'] = exc.detail[0] if isinstance(exc.detail, list) else str(exc.detail)

        if has_email:
            try:
                validate_email(opp.recruitment_email)
            except DjangoValidationError:
                errors['recruitment_email'] = "Enter a valid recruitment email address."

        if opp.deadline:
            from django.utils import timezone
            if opp.deadline < timezone.now().date():
                errors['deadline'] = "Application deadline cannot be in the past."

        if errors:
            raise serializers.ValidationError(errors)


class SuperAdminReviewSerializer(StrictInputSerializer):
    action = serializers.ChoiceField(choices=['approve', 'reject', 'suspend', 'reactivate'])
    note = serializers.CharField(max_length=1000, required=False, allow_blank=True, default='')
