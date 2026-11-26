from django.contrib.auth.models import Group
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Profile


@receiver(post_save,sender=Profile,dispatch_uid='woc.baseline_student_group')
def baseline_student_group(sender,instance,created,raw=False,using='default',**kwargs):
 # Only the baseline student group is automatic. Privileged JSON labels are ignored.
 if created and not raw and isinstance(instance.roles,list) and 'student' in instance.roles:
  group,_=Group.objects.using(using).get_or_create(name='student')
  instance.user.groups.add(group)
