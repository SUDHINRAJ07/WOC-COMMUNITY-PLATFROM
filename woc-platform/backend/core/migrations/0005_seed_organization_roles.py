from django.db import migrations


def seed_roles(apps,schema_editor):
 db=schema_editor.connection.alias
 Group=apps.get_model('auth','Group')
 User=apps.get_model('auth','User')
 Profile=apps.get_model('core','Profile')
 Institution=apps.get_model('core','Institution')
 Membership=apps.get_model('core','CollegeMembership')
 groups={role:Group.objects.using(db).get_or_create(name=role)[0] for role in ['student','college_admin','company_admin','super_admin']}
 relation=User.groups.through
 for profile in Profile.objects.using(db).all().iterator():
  if isinstance(profile.roles,list) and 'student' in profile.roles:
   relation.objects.using(db).get_or_create(user_id=profile.user_id,group_id=groups['student'].pk)
 for user in User.objects.using(db).filter(is_superuser=True).iterator():
  relation.objects.using(db).get_or_create(user_id=user.pk,group_id=groups['super_admin'].pk)
 for college in Institution.objects.using(db).all().iterator():
  # Preserve explicit legacy ownership only; never infer affiliation from names.
  if college.verified:
   college.approval_status='approved'
   college.save(using=db,update_fields=['approval_status'])
  if college.owner_id:
   owner=User.objects.using(db).get(pk=college.owner_id)
   Membership.objects.using(db).get_or_create(user_id=owner.pk,institution_id=college.pk,role='college_admin',defaults={'status':'active' if college.verified and owner.is_active else 'pending'})


class Migration(migrations.Migration):
 dependencies=[('core','0004_organization_foundation')]
 operations=[migrations.RunPython(seed_roles,migrations.RunPython.noop)]
