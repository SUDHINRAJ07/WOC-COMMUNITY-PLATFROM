import uuid
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class OrganizationStatus(models.TextChoices):
 PENDING='pending','Pending review'
 APPROVED='approved','Approved'
 REJECTED='rejected','Rejected'
 SUSPENDED='suspended','Suspended'

class MembershipStatus(models.TextChoices):
 PENDING='pending','Pending'
 ACTIVE='active','Active'
 INACTIVE='inactive','Inactive'
 REJECTED='rejected','Rejected'

class Profile(models.Model):
 photo=models.FileField(upload_to="profiles/photos/",blank=True)
 resume_file=models.FileField(upload_to="profiles/resumes/",blank=True)
 supporting_document=models.FileField(upload_to="profiles/documents/",blank=True)
 education_start_year=models.PositiveIntegerField(null=True,blank=True)
 department=models.CharField(max_length=150,blank=True)
 graduation_year=models.PositiveIntegerField(null=True,blank=True)
 user=models.OneToOneField(User,on_delete=models.CASCADE)
 institution=models.CharField(max_length=500,blank=True)
 age=models.PositiveIntegerField(null=True,blank=True)
 guardian_consent=models.BooleanField(default=False)
 email_verified=models.BooleanField(default=False)
 email_verified_at=models.DateTimeField(null=True,blank=True)
 phone_number=models.CharField(max_length=20,blank=True,default='')
 phone_verified=models.BooleanField(default=False)
 phone_verified_at=models.DateTimeField(null=True,blank=True)
 notification_preferences=models.JSONField(default=dict,blank=True)
 auth_provider=models.CharField(max_length=20,default='local')
 roles=models.JSONField(default=list)
 address=models.CharField(max_length=500,blank=True)
 pin_code=models.CharField(max_length=6,blank=True)
 professional_headline=models.CharField(max_length=160,blank=True)
 languages=models.JSONField(default=list,blank=True)
 current_status=models.CharField(max_length=20,blank=True,choices=[("studying","Studying"),("graduated","Graduated"),("working","Working")])
 bio=models.TextField(blank=True)
 state=models.CharField(max_length=100,blank=True)
 city=models.CharField(max_length=100,blank=True)
 qualification=models.CharField(max_length=200,blank=True)
 skills=models.JSONField(default=list,blank=True)
 interests=models.JSONField(default=list,blank=True)
 career_goals=models.TextField(blank=True)
 resume_url=models.URLField(max_length=500,blank=True)
 linkedin_url=models.URLField(max_length=500,blank=True)
 github_url=models.URLField(max_length=500,blank=True)
 class Meta:
  constraints=[models.UniqueConstraint(fields=['phone_number'],condition=~models.Q(phone_number=''),name='unique_profile_phone')]

class Institution(models.Model):
 state=models.CharField(max_length=100,blank=True)
 registration_reference=models.CharField(max_length=200,blank=True)
 verification_document=models.FileField(upload_to="organizations/verification/",blank=True)
 name=models.CharField(max_length=200)
 city=models.CharField(max_length=100)
 verified=models.BooleanField(default=False)
 owner=models.ForeignKey(User,null=True,on_delete=models.SET_NULL)
 website=models.URLField(max_length=500,blank=True)
 contact_email=models.EmailField(blank=True)
 address=models.TextField(blank=True)
 phone=models.CharField(max_length=30,blank=True)
 principal_name=models.CharField(max_length=150,blank=True)
 logo_url=models.URLField(max_length=500,blank=True)
 description=models.TextField(blank=True)
 approval_status=models.CharField(max_length=20,choices=OrganizationStatus.choices,default=OrganizationStatus.PENDING,db_index=True)
 reviewed_by=models.ForeignKey(User,null=True,blank=True,on_delete=models.SET_NULL,related_name='reviewed_institutions')
 reviewed_at=models.DateTimeField(null=True,blank=True)
 review_note=models.TextField(blank=True)
 created_at=models.DateTimeField(default=timezone.now,editable=False)
 class Meta:
  permissions=[('manage_organizations','Can administer organization approvals and memberships')]
  constraints=[models.CheckConstraint(condition=models.Q(approval_status__in=OrganizationStatus.values),name='valid_institution_approval')]

class Program(models.Model):
 slug=models.SlugField(unique=True)
 module=models.CharField(max_length=30)
 title=models.CharField(max_length=200)
 description=models.TextField()
 category=models.CharField(max_length=80)
 location=models.CharField(max_length=100,default='Chennai / Online')
 duration=models.CharField(max_length=80,blank=True)
 level=models.CharField(max_length=40,default='Beginner')
 fee=models.DecimalField(max_digits=10,decimal_places=2,default=0)
 capacity=models.PositiveIntegerField(default=40)
 sample=models.BooleanField(default=True)
 verified=models.BooleanField(default=False)
 details=models.JSONField(default=dict)

class Record(models.Model):
 id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
 user=models.ForeignKey(User,on_delete=models.CASCADE)
 program=models.ForeignKey(Program,on_delete=models.PROTECT)
 status=models.CharField(max_length=30,default='submitted')
 data=models.JSONField(default=dict)
 created_at=models.DateTimeField(auto_now_add=True)
 updated_at=models.DateTimeField(auto_now=True)
 class Meta: constraints=[models.UniqueConstraint(fields=['user','program'],name='one_record_per_program')]

class Certificate(models.Model):
 id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
 record=models.OneToOneField(Record,on_delete=models.PROTECT)
 issued_at=models.DateTimeField(auto_now_add=True)
 issued_by=models.ForeignKey(User,on_delete=models.PROTECT)

class Notification(models.Model):
 user=models.ForeignKey(User,on_delete=models.CASCADE)
 message=models.CharField(max_length=250)
 read=models.BooleanField(default=False)
 created_at=models.DateTimeField(auto_now_add=True)

class Enquiry(models.Model):
 name=models.CharField(max_length=100)
 email=models.EmailField()
 kind=models.CharField(max_length=40)
 message=models.TextField()
 created_at=models.DateTimeField(auto_now_add=True)

class AuditLog(models.Model):
 actor=models.ForeignKey(User,null=True,on_delete=models.SET_NULL)
 action=models.CharField(max_length=120)
 target=models.CharField(max_length=120)
 created_at=models.DateTimeField(auto_now_add=True)

class Match(models.Model):
 tournament=models.ForeignKey(Program,on_delete=models.CASCADE)
 team_a=models.ForeignKey(Record,related_name='matches_a',on_delete=models.CASCADE)
 team_b=models.ForeignKey(Record,related_name='matches_b',on_delete=models.CASCADE)
 score_a=models.PositiveIntegerField(null=True)
 score_b=models.PositiveIntegerField(null=True)
 published=models.BooleanField(default=False)

class OAuthIdentity(models.Model):
 id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
 user=models.ForeignKey(User,on_delete=models.CASCADE,related_name='oauth_identities')
 provider=models.CharField(max_length=40,default='google')
 provider_uid=models.CharField(max_length=255,unique=True)
 email=models.EmailField(max_length=254,blank=True)
 extra_data=models.JSONField(default=dict,blank=True)
 created_at=models.DateTimeField(auto_now_add=True)
 updated_at=models.DateTimeField(auto_now=True)

class PhoneOTPChallenge(models.Model):
 id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
 phone_number=models.CharField(max_length=20)
 otp_hash=models.CharField(max_length=128)
 attempts=models.PositiveIntegerField(default=0)
 expires_at=models.DateTimeField()
 consumed_at=models.DateTimeField(null=True,blank=True)
 created_at=models.DateTimeField(auto_now_add=True)
 ip_address=models.GenericIPAddressField(null=True,blank=True)
 purpose=models.CharField(max_length=20,default='verification')
 user=models.ForeignKey(User,null=True,blank=True,on_delete=models.CASCADE)

class EmailOTPChallenge(models.Model):
 id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
 email=models.EmailField(max_length=254)
 otp_hash=models.CharField(max_length=128)
 attempts=models.PositiveIntegerField(default=0)
 expires_at=models.DateTimeField()
 consumed_at=models.DateTimeField(null=True,blank=True)
 created_at=models.DateTimeField(auto_now_add=True)
 ip_address=models.GenericIPAddressField(null=True,blank=True)
 purpose=models.CharField(max_length=20,default='verification')
 user=models.ForeignKey(User,null=True,blank=True,on_delete=models.CASCADE)

class PasswordResetToken(models.Model):
 id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
 user=models.ForeignKey(User,on_delete=models.CASCADE,related_name='password_reset_tokens')
 token_hash=models.CharField(max_length=128)
 expires_at=models.DateTimeField()
 used=models.BooleanField(default=False)
 created_at=models.DateTimeField(auto_now_add=True)

class AuthAuditLog(models.Model):
 id=models.BigAutoField(primary_key=True)
 user=models.ForeignKey(User,null=True,blank=True,on_delete=models.SET_NULL,related_name='auth_audit_logs')
 event_type=models.CharField(max_length=60)
 ip_address=models.GenericIPAddressField(null=True,blank=True)
 user_agent=models.CharField(max_length=255,blank=True)
 metadata=models.JSONField(default=dict,blank=True)
 created_at=models.DateTimeField(auto_now_add=True)

class EmailDeliveryLog(models.Model):
 id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
 recipient=models.EmailField()
 subject=models.CharField(max_length=255)
 template_name=models.CharField(max_length=80)
 status=models.CharField(max_length=20,default='sent')
 error_message=models.TextField(blank=True)
 created_at=models.DateTimeField(auto_now_add=True)


class Company(models.Model):
 company_type=models.CharField(max_length=100,blank=True)
 cin=models.CharField(max_length=21,blank=True)
 address=models.TextField(blank=True)
 pin_code=models.CharField(max_length=6,blank=True)
 designation=models.CharField(max_length=150,blank=True)
 contact_phone=models.CharField(max_length=30,blank=True)
 state=models.CharField(max_length=100,blank=True)
 registration_reference=models.CharField(max_length=200,blank=True)
 verification_document=models.FileField(upload_to="organizations/verification/",blank=True)
 id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
 name=models.CharField(max_length=200)
 city=models.CharField(max_length=100,blank=True)
 website=models.URLField(max_length=500)
 contact_email=models.EmailField()
 recruitment_email=models.EmailField(blank=True)
 careers_website=models.URLField(max_length=500,blank=True)
 logo_url=models.URLField(max_length=500,blank=True)
 industry=models.CharField(max_length=100,blank=True)
 company_size=models.CharField(max_length=50,blank=True)
 contact_person=models.CharField(max_length=150,blank=True)
 description=models.TextField(blank=True)
 approval_status=models.CharField(max_length=20,choices=OrganizationStatus.choices,default=OrganizationStatus.PENDING,db_index=True)
 created_by=models.ForeignKey(User,on_delete=models.PROTECT,related_name='registered_companies')
 reviewed_by=models.ForeignKey(User,null=True,blank=True,on_delete=models.SET_NULL,related_name='reviewed_companies')
 reviewed_at=models.DateTimeField(null=True,blank=True)
 review_note=models.TextField(blank=True)
 created_at=models.DateTimeField(default=timezone.now,editable=False)
 class Meta:
  constraints=[models.CheckConstraint(condition=models.Q(approval_status__in=OrganizationStatus.values),name='valid_company_approval')]


class CollegeMembership(models.Model):
 class Role(models.TextChoices):
  STUDENT='student','Student'
  ADMIN='college_admin','College administrator'
 user=models.ForeignKey(User,on_delete=models.PROTECT,related_name='college_memberships')
 institution=models.ForeignKey(Institution,on_delete=models.PROTECT,related_name='memberships')
 role=models.CharField(max_length=30,choices=Role.choices)
 status=models.CharField(max_length=20,choices=MembershipStatus.choices,default=MembershipStatus.PENDING,db_index=True)
 created_at=models.DateTimeField(default=timezone.now,editable=False)
 class Meta:
  constraints=[
   models.UniqueConstraint(fields=['user','institution','role'],name='unique_college_membership'),
   models.UniqueConstraint(fields=['user'],condition=models.Q(role='student',status='active'),name='one_active_college_per_student'),
   models.UniqueConstraint(fields=['institution'],condition=models.Q(role='college_admin',status__in=['pending','active']),name='one_initial_college_admin'),
   models.CheckConstraint(condition=models.Q(role__in=['student','college_admin']),name='valid_college_member_role'),
   models.CheckConstraint(condition=models.Q(status__in=MembershipStatus.values),name='valid_college_member_status'),
  ]


class CompanyMembership(models.Model):
 class Role(models.TextChoices):
  ADMIN='company_admin','Company administrator'
 user=models.ForeignKey(User,on_delete=models.PROTECT,related_name='company_memberships')
 company=models.ForeignKey(Company,on_delete=models.PROTECT,related_name='memberships')
 role=models.CharField(max_length=30,choices=Role.choices,default=Role.ADMIN)
 status=models.CharField(max_length=20,choices=MembershipStatus.choices,default=MembershipStatus.PENDING,db_index=True)
 created_at=models.DateTimeField(default=timezone.now,editable=False)
 class Meta:
  constraints=[
   models.UniqueConstraint(fields=['user','company','role'],name='unique_company_membership'),
   models.UniqueConstraint(fields=['company'],condition=models.Q(role='company_admin',status__in=['pending','active']),name='one_initial_company_admin'),
   models.CheckConstraint(condition=models.Q(role='company_admin'),name='valid_company_member_role'),
   models.CheckConstraint(condition=models.Q(status__in=MembershipStatus.values),name='valid_company_member_status'),
  ]


class OpportunityType(models.TextChoices):
 JOB='job','Job'
 INTERNSHIP='internship','Internship'


class OpportunityStatus(models.TextChoices):
 DRAFT='draft','Draft'
 PENDING_REVIEW='pending_review','Pending review'
 APPROVED='approved','Approved'
 REJECTED='rejected','Rejected'
 CLOSED='closed','Closed'
 SUSPENDED='suspended','Suspended'


class EmploymentType(models.TextChoices):
 FULL_TIME='full_time','Full-time'
 PART_TIME='part_time','Part-time'
 CONTRACT='contract','Contract'


class WorkMode(models.TextChoices):
 ON_SITE='on_site','On-site'
 REMOTE='remote','Remote'
 HYBRID='hybrid','Hybrid'


class Opportunity(models.Model):
 department=models.CharField(max_length=150,blank=True)
 responsibilities=models.TextField(blank=True)
 eligible_graduation_years=models.CharField(max_length=150,blank=True)
 selection_process=models.TextField(blank=True)
 benefits=models.TextField(blank=True)
 id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
 company=models.ForeignKey(Company,on_delete=models.CASCADE,related_name='opportunities')
 opportunity_type=models.CharField(max_length=20,choices=OpportunityType.choices,db_index=True)
 title=models.CharField(max_length=200)
 description=models.TextField()
 required_skills=models.JSONField(default=list,blank=True)
 qualification=models.CharField(max_length=200,blank=True)
 experience_level=models.CharField(max_length=100,blank=True)
 employment_type=models.CharField(max_length=20,choices=EmploymentType.choices,default=EmploymentType.FULL_TIME)
 work_mode=models.CharField(max_length=20,choices=WorkMode.choices,default=WorkMode.ON_SITE)
 location=models.CharField(max_length=150,blank=True)
 compensation=models.CharField(max_length=100,blank=True)
 is_paid=models.BooleanField(default=True)
 openings=models.PositiveIntegerField(null=True,blank=True)
 duration=models.CharField(max_length=80,blank=True)
 recruitment_email=models.EmailField(blank=True)
 careers_url=models.URLField(max_length=500,blank=True)
 deadline=models.DateField(null=True,blank=True,db_index=True)
 status=models.CharField(max_length=25,choices=OpportunityStatus.choices,default=OpportunityStatus.DRAFT,db_index=True)
 previous_status=models.CharField(max_length=25,blank=True)
 reviewed_by=models.ForeignKey(User,null=True,blank=True,on_delete=models.SET_NULL,related_name='reviewed_opportunities')
 reviewed_at=models.DateTimeField(null=True,blank=True)
 review_note=models.TextField(blank=True)
 created_at=models.DateTimeField(default=timezone.now,editable=False)
 updated_at=models.DateTimeField(auto_now=True)

 class Meta:
  ordering=['-created_at']
  constraints=[
   models.CheckConstraint(condition=models.Q(opportunity_type__in=OpportunityType.values),name='valid_opportunity_type'),
   models.CheckConstraint(condition=models.Q(status__in=OpportunityStatus.values),name='valid_opportunity_status'),
   models.CheckConstraint(condition=models.Q(employment_type__in=EmploymentType.values),name='valid_opportunity_employment'),
   models.CheckConstraint(condition=models.Q(work_mode__in=WorkMode.values),name='valid_opportunity_work_mode'),
  ]


class TrainingBatch(models.Model):
 id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
 institution=models.ForeignKey(Institution,on_delete=models.CASCADE,related_name='training_batches')
 name=models.CharField(max_length=150)
 program=models.ForeignKey(Program,on_delete=models.SET_NULL,null=True,blank=True,related_name='college_batches')
 start_date=models.DateField(null=True,blank=True)
 end_date=models.DateField(null=True,blank=True)
 status=models.CharField(max_length=25,default='upcoming',choices=[('upcoming','Upcoming'),('in_progress','In progress'),('completed','Completed'),('cancelled','Cancelled')])
 capacity=models.PositiveIntegerField(default=50)
 description=models.TextField(blank=True)
 students=models.ManyToManyField(User,blank=True,related_name='enrolled_batches')
 created_at=models.DateTimeField(default=timezone.now,editable=False)
 updated_at=models.DateTimeField(auto_now=True)
 class Meta:
  ordering=['-created_at']


class CampusPlacement(models.Model):
 id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
 institution=models.ForeignKey(Institution,on_delete=models.CASCADE,related_name='campus_placements')
 student=models.ForeignKey(User,on_delete=models.CASCADE,related_name='placements')
 company=models.ForeignKey(Company,on_delete=models.SET_NULL,null=True,blank=True,related_name='campus_hires')
 company_name=models.CharField(max_length=200,blank=True)
 opportunity=models.ForeignKey(Opportunity,on_delete=models.SET_NULL,null=True,blank=True,related_name='placements')
 role_title=models.CharField(max_length=150)
 placement_type=models.CharField(max_length=20,default='job',choices=[('job','Job'),('internship','Internship')])
 compensation=models.CharField(max_length=100,blank=True)
 status=models.CharField(max_length=20,default='offered',choices=[('offered','Offered'),('accepted','Accepted'),('declined','Declined')])
 placed_at=models.DateField(default=timezone.now)
 created_at=models.DateTimeField(default=timezone.now,editable=False)
 class Meta:
  ordering=['-placed_at','-created_at']


class CollegePartnership(models.Model):
 id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
 institution=models.ForeignKey(Institution,on_delete=models.CASCADE,related_name='partnerships')
 company=models.ForeignKey(Company,on_delete=models.CASCADE,related_name='college_partnerships')
 status=models.CharField(max_length=20,default='active',choices=[('active','Active'),('pending','Pending'),('ended','Ended')])
 partnership_type=models.CharField(max_length=100,default='Recruitment & Training')
 mou_signed_date=models.DateField(null=True,blank=True)
 contact_person=models.CharField(max_length=150,blank=True)
 notes=models.TextField(blank=True)
 created_at=models.DateTimeField(default=timezone.now,editable=False)
 updated_at=models.DateTimeField(auto_now=True)
 class Meta:
  constraints=[
   models.UniqueConstraint(fields=['institution','company'],name='unique_college_company_partnership')
  ]


class SavedOpportunity(models.Model):
 id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
 user=models.ForeignKey(User,on_delete=models.CASCADE,related_name='saved_opportunities')
 opportunity=models.ForeignKey(Opportunity,on_delete=models.CASCADE,related_name='saved_by')
 created_at=models.DateTimeField(default=timezone.now,editable=False)
 class Meta:
  ordering=['-created_at']
  constraints=[
   models.UniqueConstraint(fields=['user','opportunity'],name='unique_saved_opportunity')
  ]


class OpportunityApplicationLog(models.Model):
 class Status(models.TextChoices):
  CLICKED='clicked','External Link Clicked'
  APPLIED='applied','Applied'
  INTERVIEWING='interviewing','Interviewing'
  OFFER_RECEIVED='offer_received','Offer Received'
  REJECTED='rejected','Rejected'
  WITHDRAWN='withdrawn','Withdrawn'
 id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
 user=models.ForeignKey(User,on_delete=models.CASCADE,related_name='opportunity_applications')
 opportunity=models.ForeignKey(Opportunity,on_delete=models.CASCADE,related_name='student_logs')
 status=models.CharField(max_length=30,choices=Status.choices,default=Status.CLICKED,db_index=True)
 external_click_count=models.PositiveIntegerField(default=0)
 last_clicked_at=models.DateTimeField(null=True,blank=True)
 applied_at=models.DateField(null=True,blank=True)
 notes=models.TextField(blank=True)
 created_at=models.DateTimeField(default=timezone.now,editable=False)
 updated_at=models.DateTimeField(auto_now=True)
 class Meta:
  ordering=['-updated_at']
  constraints=[
   models.UniqueConstraint(fields=['user','opportunity'],name='unique_student_opportunity_log')
  ]


class CampusEvent(models.Model):
 class EventType(models.TextChoices):
  TECHNICAL='technical','Technical Event'
  WORKSHOP='workshop','Workshop'
  WEBINAR='webinar','Webinar'
  SEMINAR='seminar','Seminar'
  COMPETITION='competition','Competition'
  SPORTS='sports','Sports'
  CULTURAL='cultural','Cultural'
 class Visibility(models.TextChoices):
  PUBLIC='public','Public'
  COLLEGE='college','College Only'
 class Status(models.TextChoices):
  UPCOMING='upcoming','Upcoming'
  ONGOING='ongoing','Ongoing'
  COMPLETED='completed','Completed'
  CANCELLED='cancelled','Cancelled'
  SUSPENDED='suspended','Suspended by Moderator'
 id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
 institution=models.ForeignKey(Institution,on_delete=models.CASCADE,related_name='campus_events')
 created_by=models.ForeignKey(User,on_delete=models.SET_NULL,null=True,related_name='created_events')
 title=models.CharField(max_length=200)
 event_type=models.CharField(max_length=30,choices=EventType.choices,default=EventType.TECHNICAL)
 description=models.TextField()
 eligibility=models.CharField(max_length=300,blank=True)
 venue=models.CharField(max_length=200)
 event_date=models.DateTimeField(db_index=True)
 end_date=models.DateTimeField(null=True,blank=True)
 registration_deadline=models.DateTimeField(null=True,blank=True)
 capacity=models.PositiveIntegerField(default=100)
 visibility=models.CharField(max_length=20,choices=Visibility.choices,default=Visibility.COLLEGE,db_index=True)
 status=models.CharField(max_length=20,choices=Status.choices,default=Status.UPCOMING,db_index=True)
 moderation_note=models.TextField(blank=True)
 created_at=models.DateTimeField(default=timezone.now,editable=False)
 updated_at=models.DateTimeField(auto_now=True)
 class Meta:
  ordering=['event_date']


class EventRegistration(models.Model):
 class Status(models.TextChoices):
  REGISTERED='registered','Registered'
  CANCELLED='cancelled','Cancelled'
  ATTENDED='attended','Attended'
  ABSENT='absent','Absent'
 id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
 event=models.ForeignKey(CampusEvent,on_delete=models.CASCADE,related_name='registrations')
 student=models.ForeignKey(User,on_delete=models.CASCADE,related_name='event_registrations')
 status=models.CharField(max_length=20,choices=Status.choices,default=Status.REGISTERED,db_index=True)
 achievement=models.CharField(max_length=200,blank=True)
 notes=models.TextField(blank=True)
 registered_at=models.DateTimeField(default=timezone.now,editable=False)
 updated_at=models.DateTimeField(auto_now=True)
 class Meta:
  ordering=['-registered_at']
  constraints=[
   models.UniqueConstraint(fields=['event','student'],name='unique_campus_event_registration')
  ]


class StudentClub(models.Model):
 class Category(models.TextChoices):
  TECHNICAL='technical','Technical'
  CULTURAL='cultural','Cultural'
  SPORTS='sports','Sports'
  ENTREPRENEURSHIP='entrepreneurship','Entrepreneurship'
  PROFESSIONAL='professional','Professional Development'
 class Status(models.TextChoices):
  ACTIVE='active','Active'
  INACTIVE='inactive','Inactive'
  SUSPENDED='suspended','Suspended by Moderator'
 id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
 institution=models.ForeignKey(Institution,on_delete=models.CASCADE,related_name='clubs')
 name=models.CharField(max_length=150)
 category=models.CharField(max_length=30,choices=Category.choices,default=Category.TECHNICAL)
 description=models.TextField()
 status=models.CharField(max_length=20,choices=Status.choices,default=Status.ACTIVE,db_index=True)
 moderation_note=models.TextField(blank=True)
 created_at=models.DateTimeField(default=timezone.now,editable=False)
 updated_at=models.DateTimeField(auto_now=True)
 class Meta:
  ordering=['name']
  constraints=[
   models.UniqueConstraint(fields=['institution','name'],name='unique_college_club_name')
  ]


class ClubMembership(models.Model):
 class Status(models.TextChoices):
  PENDING='pending','Pending'
  APPROVED='approved','Approved'
  REJECTED='rejected','Rejected'
  LEFT='left','Left'
 id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
 club=models.ForeignKey(StudentClub,on_delete=models.CASCADE,related_name='memberships')
 student=models.ForeignKey(User,on_delete=models.CASCADE,related_name='club_memberships')
 status=models.CharField(max_length=20,choices=Status.choices,default=Status.PENDING,db_index=True)
 joined_at=models.DateTimeField(default=timezone.now,editable=False)
 updated_at=models.DateTimeField(auto_now=True)
 class Meta:
  ordering=['-joined_at']
  constraints=[
   models.UniqueConstraint(fields=['club','student'],name='unique_student_club_membership')
  ]


class CampusLeadership(models.Model):
 class Role(models.TextChoices):
  AMBASSADOR='campus_ambassador','Campus Ambassador'
  COORDINATOR='student_coordinator','Student Coordinator'
  CLUB_LEADER='club_leader','Club Leader'
 class Status(models.TextChoices):
  ACTIVE='active','Active'
  REVOKED='revoked','Revoked'
 id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
 institution=models.ForeignKey(Institution,on_delete=models.CASCADE,related_name='leadership_roles')
 student=models.ForeignKey(User,on_delete=models.CASCADE,related_name='leadership_assignments')
 role=models.CharField(max_length=30,choices=Role.choices)
 club=models.ForeignKey(StudentClub,on_delete=models.SET_NULL,null=True,blank=True,related_name='leaders')
 title=models.CharField(max_length=150,blank=True)
 responsibilities=models.TextField(blank=True)
 permissions=models.JSONField(default=list,blank=True)
 status=models.CharField(max_length=20,choices=Status.choices,default=Status.ACTIVE,db_index=True)
 assigned_by=models.ForeignKey(User,on_delete=models.SET_NULL,null=True,related_name='assigned_leadership_roles')
 activity_log=models.JSONField(default=list,blank=True)
 assigned_at=models.DateTimeField(default=timezone.now,editable=False)
 revoked_at=models.DateTimeField(null=True,blank=True)
 class Meta:
  ordering=['-assigned_at']


class CampusAnnouncement(models.Model):
 id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
 institution=models.ForeignKey(Institution,on_delete=models.CASCADE,related_name='announcements')
 club=models.ForeignKey(StudentClub,on_delete=models.CASCADE,null=True,blank=True,related_name='announcements')
 author=models.ForeignKey(User,on_delete=models.SET_NULL,null=True,related_name='campus_announcements')
 title=models.CharField(max_length=200)
 content=models.TextField()
 scope=models.CharField(max_length=20,choices=[('college','College Wide'),('club','Club Specific')],default='college')
 is_moderated_hidden=models.BooleanField(default=False)
 created_at=models.DateTimeField(default=timezone.now,editable=False)
 class Meta:
  ordering=['-created_at']


class ProfileSuggestion(models.Model):
 """Public reference catalog; never grants institution affiliation or privileges."""
 kind=models.CharField(max_length=20,db_index=True)
 source_id=models.CharField(max_length=100)
 name=models.CharField(max_length=500)
 search_name=models.CharField(max_length=500,db_index=True)
 state=models.CharField(max_length=100,blank=True,db_index=True)
 district=models.CharField(max_length=150,blank=True)
 source=models.CharField(max_length=100,blank=True)
 class Meta:
  constraints=[models.UniqueConstraint(fields=['kind','source_id'],name='unique_profile_suggestion_source')]
  indexes=[models.Index(fields=['kind','search_name'],name='profile_suggestion_search')]
