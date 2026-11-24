import uuid
from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
 user=models.OneToOneField(User,on_delete=models.CASCADE)
 institution=models.CharField(max_length=200,blank=True)
 age=models.PositiveIntegerField()
 guardian_consent=models.BooleanField(default=False)
 email_verified=models.BooleanField(default=False)
 email_verified_at=models.DateTimeField(null=True,blank=True)
 phone_number=models.CharField(max_length=20,blank=True,default='')
 phone_verified=models.BooleanField(default=False)
 phone_verified_at=models.DateTimeField(null=True,blank=True)
 notification_preferences=models.JSONField(default=dict,blank=True)
 auth_provider=models.CharField(max_length=20,default='local')
 roles=models.JSONField(default=list)
 bio=models.TextField(blank=True)
 class Meta:
  constraints=[models.UniqueConstraint(fields=['phone_number'],condition=~models.Q(phone_number=''),name='unique_profile_phone')]

class Institution(models.Model):
 name=models.CharField(max_length=200)
 city=models.CharField(max_length=100)
 verified=models.BooleanField(default=False)
 owner=models.ForeignKey(User,null=True,on_delete=models.SET_NULL)

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
