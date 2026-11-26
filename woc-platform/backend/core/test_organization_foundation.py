from unittest.mock import patch
from django.contrib import admin
from django.contrib.auth.models import User,Group,Permission
from django.db import IntegrityError,transaction
from django.db.models.deletion import ProtectedError
from django.test import TestCase,Client,RequestFactory
from .models import Profile,Institution,Company,CollegeMembership,CompanyMembership,AuthAuditLog
from .organization_access import access_context,is_super_admin,IsCollegeAdministrator,IsCompanyAdministrator


class OrganizationFoundationTests(TestCase):
 def setUp(self):
  from django.core.cache import cache
  cache.clear()
  self.user=self.account('student')
  self.other=self.account('other')
  self.root=self.account('root',is_staff=True,is_superuser=True)
  self.client.force_login(self.user)
 def account(self,name,**flags):
  user=User.objects.create_user(name+'@example.com',name+'@example.com','FoundationPass!2035',**flags)
  Profile.objects.create(user=user,age=20,roles=['student'])
  return user
 def company(self,name='Example',user=None,status='approved',membership='active'):
  user=user or self.user
  company=Company.objects.create(name=name,website='https://example.com',contact_email='recruit@example.com',created_by=user,approval_status=status)
  member=CompanyMembership.objects.create(company=company,user=user,status=membership)
  return company,member
 def college(self,name='College',user=None,status='approved',membership='active'):
  user=user or self.user
  college=Institution.objects.create(name=name,city='Chennai',owner=user,approval_status=status)
  member=CollegeMembership.objects.create(institution=college,user=user,role='college_admin',status=membership)
  return college,member
 def post(self,kind='company',**extra):
  data={'name':'New organization','city':'Chennai','website':'https://example.com','contact_email':'office@example.com',**extra}
  return self.client.post('/api/onboarding/'+kind+'/',data,content_type='application/json')

 def test_anonymous_access_and_onboarding_denied(self):
  self.client.logout()
  for url in ['/api/access/','/api/onboarding/company/','/api/onboarding/college/','/api/organizations/companies/','/api/organizations/colleges/']:
   self.assertEqual(self.client.get(url).status_code,403)
  self.assertEqual(self.post().status_code,403)

 def test_company_onboarding_is_pending_and_does_not_grant_access(self):
  response=self.post();self.assertEqual(response.status_code,201)
  company=Company.objects.get(pk=response.json()['id'])
  self.assertEqual(company.approval_status,'pending');self.assertEqual(company.created_by,self.user)
  self.assertEqual(company.memberships.get().status,'pending')
  self.assertFalse(self.user.is_staff)
  self.assertNotIn('company_admin',self.client.get('/api/access/').json()['roles'])
  self.assertEqual(self.client.get('/api/organizations/companies/').status_code,403)
  self.assertEqual(self.client.get('/api/onboarding/company/').json()['count'],1)
  self.assertIsNone(company.reviewed_at)
  self.assertTrue(AuthAuditLog.objects.filter(user=self.user,event_type='company_onboarding_requested').exists())

 def test_college_onboarding_is_pending_and_preserves_account(self):
  password=self.user.password
  response=self.post('college');self.assertEqual(response.status_code,201)
  college=Institution.objects.get(pk=response.json()['id'])
  self.assertFalse(college.verified);self.assertEqual(college.approval_status,'pending')
  self.assertEqual(college.memberships.get().role,'college_admin')
  self.user.refresh_from_db();self.assertEqual(self.user.password,password)
  self.assertFalse(self.user.profile.email_verified)
  self.assertEqual(self.client.get('/api/organizations/colleges/').status_code,403)

 def test_mass_assignment_and_status_injection_rejected(self):
  for kind in ['company','college']:
   for field,value in [('approval_status','approved'),('status','active'),('created_by',self.other.pk),('owner',self.other.pk),('roles',['super_admin']),('is_staff',True),('reviewed_by',self.root.pk)]:
    with self.subTest(kind=kind,field=field):
     self.assertEqual(self.post(kind,**{field:value}).status_code,400)
  self.assertEqual(Company.objects.count(),0);self.assertEqual(Institution.objects.count(),0)

 def test_website_and_contact_validation(self):
  for fields in [{'website':'http://example.com'},{'website':'javascript:alert(1)'},{'website':'https://user:pass@example.com'},{'contact_email':'invalid'},{'name':'   '}]:
   self.assertEqual(self.post(**fields).status_code,400)

 def test_duplicate_submission_returns_conflict_without_extra_records(self):
  self.assertEqual(self.post().status_code,201)
  self.assertEqual(self.post(name='NEW ORGANIZATION').status_code,409)
  self.assertEqual(Company.objects.count(),1);self.assertEqual(CompanyMembership.objects.count(),1)
  self.assertEqual(self.post('college').status_code,201)
  self.assertEqual(self.post('college').status_code,409)

 def test_onboarding_list_is_private(self):
  self.post();self.post('college')
  self.client.force_login(self.other)
  for kind in ['college','company']:
   response=self.client.get('/api/onboarding/'+kind+'/')
   self.assertEqual(response.json()['count'],0)

 def test_company_list_and_detail_are_organization_scoped(self):
  own,_=self.company();foreign,_=self.company('Foreign',self.other)
  response=self.client.get('/api/organizations/companies/')
  self.assertEqual(response.status_code,200);self.assertEqual(response.json()['count'],1)
  self.assertEqual(response.json()['results'][0]['id'],str(own.pk))
  self.assertEqual(self.client.get(f'/api/organizations/companies/{foreign.pk}/').status_code,404)
  self.assertEqual(self.client.get(f'/api/organizations/companies/{own.pk}/').status_code,200)

 def test_college_list_and_detail_are_organization_scoped(self):
  own,_=self.college();foreign,_=self.college('Foreign',self.other)
  response=self.client.get('/api/organizations/colleges/')
  self.assertEqual(response.json()['count'],1)
  self.assertEqual(response.json()['results'][0]['id'],own.pk)
  self.assertEqual(self.client.get(f'/api/organizations/colleges/{foreign.pk}/').status_code,404)
  self.assertEqual(self.client.get(f'/api/organizations/colleges/{own.pk}/').status_code,200)

 def test_company_role_does_not_grant_college_access(self):
  self.company()
  self.assertEqual(self.client.get('/api/organizations/colleges/').status_code,403)

 def test_college_role_does_not_grant_company_access(self):
  self.college()
  self.assertEqual(self.client.get('/api/organizations/companies/').status_code,403)

 def test_pending_rejected_suspended_companies_do_not_grant_access(self):
  company,member=self.company()
  for state in ['pending','rejected','suspended']:
   Company.objects.filter(pk=company.pk).update(approval_status=state)
   self.assertNotIn('company_admin',access_context(self.user)['roles'])
   self.assertEqual(self.client.get('/api/organizations/companies/').status_code,403)

 def test_inactive_membership_loses_access_immediately(self):
  company,member=self.company()
  self.assertIn('company_admin',access_context(self.user)['roles'])
  member.status='inactive';member.save()
  self.assertNotIn('company_admin',access_context(self.user)['roles'])
  self.assertEqual(self.client.get('/api/organizations/companies/').status_code,403)
  self.assertEqual(self.client.get('/api/onboarding/company/').json()['count'],0)

 def test_unapproved_college_and_inactive_admin_membership_denied(self):
  college,member=self.college(status='pending')
  self.assertEqual(self.client.get('/api/organizations/colleges/').status_code,403)
  college.approval_status='approved';college.save()
  member.status='inactive';member.save()
  self.assertEqual(self.client.get('/api/organizations/colleges/').status_code,403)
  self.assertEqual(self.client.get('/api/onboarding/college/').json()['count'],0)

 def test_profile_role_json_and_global_org_groups_do_not_grant_privileges(self):
  Profile.objects.filter(user=self.user).update(roles=['super_admin','college_admin','company_admin'])
  for role in ['college_admin','company_admin','super_admin']:
   group,_=Group.objects.get_or_create(name=role);self.user.groups.add(group)
  self.assertFalse(is_super_admin(self.user))
  self.assertEqual(self.client.get('/api/organizations/companies/').status_code,403)
  self.assertEqual(self.client.get('/api/organizations/colleges/').status_code,403)

 def test_staff_flag_alone_is_not_super_admin(self):
  User.objects.filter(pk=self.user.pk).update(is_staff=True)
  self.assertEqual(self.client.get('/api/organizations/companies/').status_code,403)
  self.assertNotIn('super_admin',self.client.get('/api/access/').json()['roles'])

 def test_super_admin_requires_group_and_explicit_permission_or_superuser(self):
  permission=Permission.objects.get(codename='manage_organizations',content_type__app_label='core')
  self.user.user_permissions.add(permission)
  self.assertFalse(is_super_admin(User.objects.get(pk=self.user.pk)))
  group,_=Group.objects.get_or_create(name='super_admin');self.user.groups.add(group)
  self.assertTrue(is_super_admin(User.objects.get(pk=self.user.pk)))
  self.assertTrue(is_super_admin(self.root))

 def test_super_admin_can_inspect_all_organizations(self):
  self.company();self.company('Other',self.other,status='pending');self.college()
  self.client.force_login(self.root)
  self.assertEqual(self.client.get('/api/organizations/companies/').json()['count'],2)
  self.assertEqual(self.client.get('/api/organizations/colleges/').json()['count'],1)

 def test_inactive_user_has_no_access(self):
  self.company();self.user.is_active=False;self.user.save()
  self.assertEqual(access_context(self.user)['roles'],[])
  self.assertFalse(is_super_admin(self.user))
  self.assertEqual(self.client.get('/api/access/').status_code,403)

 def test_one_active_college_per_student_is_database_enforced(self):
  first,_=self.college();second,_=self.college('Second',self.other)
  member=CollegeMembership.objects.create(user=self.user,institution=first,role='student',status='active')
  with self.assertRaises(IntegrityError),transaction.atomic():
   CollegeMembership.objects.create(user=self.user,institution=second,role='student',status='active')
  member.status='inactive';member.save()
  CollegeMembership.objects.create(user=self.user,institution=second,role='student',status='active')
  self.assertEqual(CollegeMembership.objects.filter(user=self.user,role='student',status='active').count(),1)

 def test_one_initial_college_administrator_is_database_enforced(self):
  college,_=self.college(membership='pending')
  with self.assertRaises(IntegrityError),transaction.atomic():
   CollegeMembership.objects.create(user=self.other,institution=college,role='college_admin',status='active')

 def test_one_initial_company_administrator_is_database_enforced(self):
  company,_=self.company(membership='pending')
  with self.assertRaises(IntegrityError),transaction.atomic():
   CompanyMembership.objects.create(user=self.other,company=company,status='active')

 def test_inactive_admin_can_be_replaced_without_deleting_history(self):
  company,member=self.company();member.status='inactive';member.save()
  replacement=CompanyMembership.objects.create(user=self.other,company=company,status='pending')
  self.assertEqual(company.memberships.count(),2);self.assertEqual(replacement.status,'pending')

 def test_duplicate_memberships_are_database_rejected(self):
  company,_=self.company();college,_=self.college()
  with self.assertRaises(IntegrityError),transaction.atomic():CompanyMembership.objects.create(user=self.user,company=company,status='inactive')
  with self.assertRaises(IntegrityError),transaction.atomic():CollegeMembership.objects.create(user=self.user,institution=college,role='college_admin',status='inactive')

 def test_invalid_roles_and_statuses_are_database_rejected(self):
  company,_=self.company();college,_=self.college()
  for model,values in [(CompanyMembership,{'company':company,'user':self.other,'role':'super_admin'}),(CollegeMembership,{'institution':college,'user':self.other,'role':'super_admin'}),(Company,{'name':'Invalid','website':'https://example.com','contact_email':'a@example.com','created_by':self.other,'approval_status':'published'})]:
   with self.subTest(model=model),self.assertRaises(IntegrityError),transaction.atomic():model.objects.create(**values)

 def test_membership_history_protects_users_and_organizations(self):
  company,_=self.company()
  with self.assertRaises(ProtectedError):company.delete()
  with self.assertRaises(ProtectedError):self.user.delete()

 def test_csrf_required_and_valid_csrf_onboarding_works(self):
  client=Client(enforce_csrf_checks=True);client.force_login(self.user)
  data={'name':'CSRF College','city':'Chennai','contact_email':'college@example.com'}
  self.assertEqual(client.post('/api/onboarding/college/',data).status_code,403)
  token=client.get('/api/csrf/').json()['csrfToken']
  # JSON is the documented API contract.
  self.assertEqual(client.post('/api/onboarding/college/',data,content_type='application/json',HTTP_X_CSRFTOKEN=token).status_code,201)

 def test_phase1_organization_apis_do_not_expose_mutation_or_approval(self):
  company,_=self.company()
  for method in ['patch','delete','put']:
   self.assertEqual(getattr(self.client,method)(f'/api/organizations/companies/{company.pk}/',{},content_type='application/json').status_code,405)
  self.assertEqual(self.client.post(f'/api/organizations/companies/{company.pk}/approve/',{}).status_code,404)

 def test_existing_me_response_gains_metadata_without_modifying_profile_roles(self):
  self.company()
  response=self.client.get('/api/me/').json()['user']
  self.assertIn('company_admin',response['authorization']['roles'])
  self.assertEqual(response['authorization']['dashboard_url'],'/company/')
  self.assertEqual(Profile.objects.get(user=self.user).roles,['student'])

 def test_object_permission_helpers_enforce_organization_ownership(self):
  own,_=self.company();foreign,_=self.company('Foreign',self.other)
  request=RequestFactory().get('/');request.user=self.user
  self.assertTrue(IsCompanyAdministrator().has_object_permission(request,None,own))
  self.assertFalse(IsCompanyAdministrator().has_object_permission(request,None,foreign))
  self.assertFalse(IsCollegeAdministrator().has_permission(request,None))

 def test_foundation_admin_is_super_admin_read_only(self):
  model_admin=admin.site._registry[Company]
  request=RequestFactory().get('/admin/');request.user=self.root
  self.assertTrue(model_admin.has_view_permission(request))
  self.assertFalse(model_admin.has_change_permission(request))
  self.assertFalse(model_admin.has_add_permission(request))
  self.assertFalse(model_admin.has_delete_permission(request))
  request.user=self.user;self.assertFalse(model_admin.has_view_permission(request))

 def test_audit_failure_rolls_back_onboarding(self):
  with patch('core.organization_views.AuthAuditLog.objects.create',side_effect=RuntimeError('audit unavailable')):
   with self.assertRaises(RuntimeError):self.post()
  self.assertEqual(Company.objects.count(),0);self.assertEqual(CompanyMembership.objects.count(),0)

 def test_new_student_profile_gets_only_baseline_group(self):
  self.assertTrue(self.user.groups.filter(name='student').exists())
  self.assertFalse(self.user.groups.filter(name__in=['college_admin','company_admin','super_admin']).exists())

 def test_student_affiliation_does_not_grant_college_admin_access(self):
  college,_=self.college(user=self.other)
  CollegeMembership.objects.create(user=self.user,institution=college,role='student',status='active')
  context=self.client.get('/api/access/').json()
  self.assertEqual(context['college_memberships'][0]['college_id'],college.pk)
  self.assertNotIn('college_admin',context['roles'])
  self.assertEqual(self.client.get('/api/organizations/colleges/').status_code,403)

 def test_onboarding_write_rate_limit_is_separate_from_reads(self):
  with patch('core.organization_views.OnboardingWriteThrottle.rate','2/hour'):
   self.assertEqual(self.post(name='First').status_code,201)
   self.assertEqual(self.post(name='Second').status_code,201)
   self.assertEqual(self.post(name='Third').status_code,429)
   self.assertEqual(self.client.get('/api/onboarding/company/').status_code,200)

 def test_pagination_does_not_expose_another_tenant_on_later_pages(self):
  for index in range(21):self.company(f'Own {index}')
  foreign,_=self.company('Foreign',self.other)
  page=self.client.get('/api/organizations/companies/?page=2').json()
  self.assertEqual(page['count'],21);self.assertEqual(len(page['results']),1)
  self.assertNotEqual(page['results'][0]['id'],str(foreign.pk))


class PriorityAccountCorrectionsTests(TestCase):
 def test_account_permissions_and_history(self):
  from django.contrib.auth.models import User
  from .models import AuthAuditLog
  root=User.objects.create_superuser(username='priority-root',password='test')
  student=User.objects.create_user(username='priority-student',password='test')
  self.client.force_login(student)
  self.assertEqual(self.client.get('/api/super-admin/accounts/').status_code,403)
  self.client.force_login(root)
  self.assertEqual(self.client.get('/api/super-admin/accounts/?role=student').status_code,200)
  result=self.client.post('/api/super-admin/accounts/',{'user_id':student.pk,'action':'suspend'},content_type='application/json')
  self.assertEqual(result.status_code,200)
  student.refresh_from_db();self.assertFalse(student.is_active)
  self.assertTrue(AuthAuditLog.objects.filter(event_type='admin_account_suspend',metadata__target_user_id=student.pk).exists())
  self.assertEqual(self.client.post('/api/super-admin/accounts/',{'user_id':root.pk,'action':'suspend'},content_type='application/json').status_code,403)
 def test_legacy_career_submission_blocked(self):
  from django.contrib.auth.models import User
  from .models import Program,Record
  user=User.objects.create_user(username='priority-career',password='test')
  program=Program.objects.create(slug='priority-career',module='careers',title='Career',description='Example',category='Job')
  self.client.force_login(user)
  self.assertEqual(self.client.post('/api/records/',{'program':program.slug,'data':{}},content_type='application/json').status_code,400)
  self.assertFalse(Record.objects.filter(program=program).exists())
