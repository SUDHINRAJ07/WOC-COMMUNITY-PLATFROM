import io
import tempfile
from django.test import TestCase, override_settings
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache
from PIL import Image
from .models import Profile, Company, CompanyMembership, Institution, CollegeMembership, Opportunity


class PortalProfileTests(TestCase):
    def setUp(self):
        cache.clear()
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.settings_override = override_settings(MEDIA_ROOT=self.directory.name)
        self.settings_override.enable()
        self.addCleanup(self.settings_override.disable)
        self.user = User.objects.create_user(username='portal-owner', password=None)
        self.other = User.objects.create_user(username='portal-other', password=None)
        Profile.objects.create(user=self.user, age=20, roles=['student'])
        Profile.objects.create(user=self.other, age=21, roles=['student'])
        self.client.force_login(self.user)

    def pdf(self):
        return SimpleUploadedFile('resume.pdf', b'%PDF-1.4\nprivate resume\n%%EOF', content_type='application/pdf')

    def test_pdf_upload_download_and_delete_are_private(self):
        url = '/api/student/profile/files/resume/'
        before = self.client.get('/api/student/profile/').json()['profile_completion']['percentage']
        response = self.client.post(url, {'file': self.pdf()})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['user']['has_resume'])
        self.assertGreater(response.json()['profile_completion']['percentage'], before)
        download = self.client.get(url)
        self.assertEqual(download.status_code, 200)
        self.assertEqual(download['Cache-Control'], 'private, no-store')
        download.close()
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(url).status_code, 404)
        self.client.force_login(self.user)
        self.assertEqual(self.client.delete(url).status_code, 200)
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_fake_and_oversized_documents_rejected(self):
        for name, content in [('bad.pdf', b'<html>not a pdf</html>'), ('bad.html', b'%PDF-1.4\n%%EOF'), ('large.pdf', b'%PDF-'+b'x'*(5*1024*1024))]:
            self.assertEqual(self.client.post('/api/student/profile/files/document/', {'file':SimpleUploadedFile(name, content)}).status_code, 400)

    def test_photo_is_reencoded_and_counted(self):
        image = io.BytesIO()
        Image.new('RGB', (20, 20), 'red').save(image, format='PNG')
        response = self.client.post('/api/student/profile/files/photo/', {'file':SimpleUploadedFile('photo.png', image.getvalue())})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['user']['has_photo'])
        photo = self.client.get('/api/student/profile/files/photo/')
        self.assertEqual(photo['Content-Type'], 'image/jpeg')
        photo.close()
        self.assertEqual(self.client.post('/api/student/profile/files/photo/', {'file':self.pdf()}).status_code, 400)

    def test_graduation_year_profile_update(self):
        response = self.client.patch('/api/student/profile/', {'graduation_year':2027}, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['user']['graduation_year'], 2027)
        self.assertEqual(self.client.patch('/api/student/profile/', {'graduation_year':9999}, content_type='application/json').status_code, 400)

    def test_organization_evidence_is_tenant_scoped(self):
        company = Company.objects.create(name='Portal company', website='https://example.com', contact_email='office@example.com', created_by=self.user)
        CompanyMembership.objects.create(company=company, user=self.user)
        url = f'/api/onboarding/company/{company.pk}/document/'
        self.assertEqual(self.client.post(url, {'file':self.pdf()}).status_code, 200)
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(url).status_code, 404)
        self.assertEqual(self.client.post(url, {'file':self.pdf()}).status_code, 404)

    def test_college_registration_reuses_phone_field_and_pending_role(self):
        response = self.client.post('/api/onboarding/college/', {'name':'Portal College','city':'Chennai','contact_email':'office@college.example','contact_phone':'1234567890','state':'Tamil Nadu','registration_reference':'COL-01'}, content_type='application/json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Institution.objects.get(pk=response.json()['id']).phone, '1234567890')
        self.assertEqual(self.client.get('/api/access/').json()['dashboard_url'], '/onboarding/')

    def test_posting_fields_are_saved_without_bypassing_review(self):
        company = Company.objects.create(name='Approved company', website='https://example.com',contact_email='office@example.com',created_by=self.user,approval_status='approved')
        CompanyMembership.objects.create(company=company,user=self.user,status='active')
        response = self.client.post('/api/company/opportunities/', {'opportunity_type':'internship','title':'Data Intern','description':'Analyze datasets and document meaningful findings.','department':'Analytics','responsibilities':'Analyze data','eligible_graduation_years':'2027, 2028','selection_process':'Technical discussion','benefits':'Mentorship','recruitment_email':'jobs@example.com'}, content_type='application/json')
        self.assertEqual(response.status_code, 201)
        opportunity=Opportunity.objects.get(pk=response.json()['id'])
        self.assertEqual(opportunity.department,'Analytics')
        self.assertEqual(opportunity.status,'draft')

    def test_unauthenticated_upload_rejected(self):
        self.client.logout()
        self.assertEqual(self.client.post('/api/student/profile/files/resume/', {'file':self.pdf()}).status_code, 403)


    @override_settings(EMAIL_VERIFICATION_REQUIRED=False)
    def test_college_account_and_organization_register_together(self):
        self.client.logout()
        response=self.client.post('/api/register/',{'name':'College Administrator','age':30,'email':'new-college@example.com','password':'StrongCampus!2026','terms':True,'organization_kind':'college','organization':{'name':'New Campus','city':'Chennai','website':'https://college.example.com','contact_email':'office@college.example.com','contact_phone':'1234567890','registration_reference':'COL-123'}},content_type='application/json')
        self.assertEqual(response.status_code,201)
        user=User.objects.get(username='new-college@example.com')
        membership=CollegeMembership.objects.get(user=user)
        self.assertEqual(membership.institution.approval_status,'pending')
        self.assertEqual(membership.status,'pending')
        self.assertFalse(user.is_staff)
        self.client.force_login(user)
        self.assertEqual(self.client.get('/api/access/').json()['dashboard_url'],'/onboarding/')

    @override_settings(EMAIL_VERIFICATION_REQUIRED=False)
    def test_company_registration_validation_prevents_orphan_account(self):
        self.client.logout()
        response=self.client.post('/api/register/',{'name':'Company Administrator','age':30,'email':'invalid-company@example.com','password':'StrongCampus!2026','terms':True,'organization_kind':'company','organization':{'name':'Company with invalid PIN','contact_email':'office@example.com','pin_code':'BAD'}},content_type='application/json')
        self.assertEqual(response.status_code,400)
        self.assertFalse(User.objects.filter(username='invalid-company@example.com').exists())

    @override_settings(EMAIL_VERIFICATION_REQUIRED=False)
    def test_company_account_is_pending_without_privilege_escalation(self):
        self.client.logout()
        response=self.client.post('/api/register/',{'name':'Company Administrator','age':30,'email':'new-company@example.com','password':'StrongCampus!2026','terms':True,'organization_kind':'company','organization':{'name':'New Company','website':'https://company.example.com','contact_email':'office@company.example.com','industry':'Technology'}},content_type='application/json')
        self.assertEqual(response.status_code,201)
        user=User.objects.get(username='new-company@example.com')
        membership=CompanyMembership.objects.get(user=user)
        self.assertEqual(membership.company.approval_status,'pending')
        self.assertEqual(membership.status,'pending')
        self.client.force_login(user)
        self.assertEqual(self.client.get('/api/company/dashboard/').status_code,403)


    @override_settings(EMAIL_VERIFICATION_REQUIRED=False)
    def test_new_company_fields_save_without_fabricating_age(self):
        self.client.logout()
        response=self.client.post('/api/register/',{'name':'Recruiter Name','email':'hr@new-business.example','password':'StrongBusiness!2026','confirm_password':'StrongBusiness!2026','terms':True,'organization_kind':'company','organization':{'name':'Registered Business','company_type':'Private Limited','industry':'IT','company_size':'11-50','registration_reference':'REG-123','cin':'U12345TN2020PTC123456','address':'Chennai office','state':'Tamil Nadu','city':'Chennai','pin_code':'600001','contact_person':'Recruiter Name','designation':'HR Manager','contact_email':'hr@new-business.example','contact_phone':'9876543210'}},content_type='application/json')
        self.assertEqual(response.status_code,201)
        user=User.objects.get(username='hr@new-business.example')
        company=Company.objects.get(created_by=user)
        self.assertEqual(company.company_type,'Private Limited')
        self.assertEqual(company.pin_code,'600001')
        self.assertEqual(company.designation,'HR Manager')
        self.assertEqual(company.cin,'U12345TN2020PTC123456')
        self.assertIsNone(user.profile.age)
        self.assertEqual(company.approval_status,'pending')

    @override_settings(EMAIL_VERIFICATION_REQUIRED=False)
    def test_company_confirmation_mismatch_does_not_create_account(self):
        self.client.logout()
        response=self.client.post('/api/register/',{'name':'Recruiter','email':'mismatch@example.com','password':'StrongBusiness!2026','confirm_password':'DifferentPassword!2026','terms':True,'organization_kind':'company'},content_type='application/json')
        self.assertEqual(response.status_code,400)
        self.assertFalse(User.objects.filter(username='mismatch@example.com').exists())
