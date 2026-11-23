import uuid
from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
 user=models.OneToOneField(User,on_delete=models.CASCADE)
 institution=models.CharField(max_length=200,blank=True)
 age=models.PositiveIntegerField()
 guardian_consent=models.BooleanField(default=False)
 email_verified=models.BooleanField(default=False)
 roles=models.JSONField(default=list)
 bio=models.TextField(blank=True)

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
