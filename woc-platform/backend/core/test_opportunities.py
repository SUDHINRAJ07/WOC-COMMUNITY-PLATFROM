import datetime
from django.test import TestCase, Client
from django.contrib.auth.models import User, Group, Permission
from django.utils import timezone
from .models import (
    Profile, Company, CompanyMembership, Opportunity, OpportunityType,
    OpportunityStatus, EmploymentType, WorkMode, OrganizationStatus,
    MembershipStatus, AuthAuditLog, Notification
)


class OpportunityPhase2Tests(TestCase):
    def setUp(self):
        from django.core.cache import cache
        cache.clear()

        # Seed roles if not present
        for role in ['student', 'college_admin', 'company_admin', 'super_admin']:
            Group.objects.get_or_create(name=role)

        # 1. Company Admin 1
        self.company_user = self.create_user('recruiter1@company.com')
        # 2. Company Admin 2 (different tenant)
        self.other_company_user = self.create_user('recruiter2@other.com')
        # 3. Super Admin
        self.super_user = self.create_user('admin@woc.org', is_staff=True, is_superuser=True)
        # 4. Student
        self.student_user = self.create_user('student@university.edu')

        # Create approved company for recruiter 1
        self.company1 = Company.objects.create(
            name='TechCorp Innovations',
            city='Bengaluru',
            website='https://techcorp.com',
            contact_email='contact@techcorp.com',
            recruitment_email='careers@techcorp.com',
            careers_website='https://techcorp.com/careers',
            logo_url='https://techcorp.com/logo.png',
            industry='Software & AI',
            company_size='51-200',
            contact_person='Priya Sharma',
            description='Leading enterprise AI solutions.',
            approval_status=OrganizationStatus.APPROVED,
            created_by=self.company_user
        )
        self.membership1 = CompanyMembership.objects.create(
            user=self.company_user,
            company=self.company1,
            role=CompanyMembership.Role.ADMIN,
            status=MembershipStatus.ACTIVE
        )

        # Create pending company for recruiter 2
        self.company2 = Company.objects.create(
            name='Startup Hub',
            city='Hyderabad',
            website='https://startuphub.io',
            contact_email='hello@startuphub.io',
            approval_status=OrganizationStatus.PENDING,
            created_by=self.other_company_user
        )
        self.membership2 = CompanyMembership.objects.create(
            user=self.other_company_user,
            company=self.company2,
            role=CompanyMembership.Role.ADMIN,
            status=MembershipStatus.PENDING
        )

        self.client = Client()

    def create_user(self, email, is_staff=False, is_superuser=False):
        user = User.objects.create_user(
            username=email,
            email=email,
            password='TestPassword@2026',
            is_staff=is_staff,
            is_superuser=is_superuser,
            first_name=email.split('@')[0]
        )
        Profile.objects.create(user=user, age=22, roles=['student'])
        return user

    # ----------------------------------------------------
    # 1. Company Profile Management Tests
    # ----------------------------------------------------
    def test_company_profile_get_and_patch(self):
        self.client.force_login(self.company_user)
        # GET
        res = self.client.get('/api/company/profile/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()['name'], 'TechCorp Innovations')
        self.assertEqual(res.json()['recruitment_email'], 'careers@techcorp.com')

        # PATCH
        patch_data = {
            'industry': 'Artificial Intelligence',
            'company_size': '201-500',
            'contact_person': 'Priya S.',
            'careers_website': 'https://techcorp.com/jobs'
        }
        res_patch = self.client.patch('/api/company/profile/', data=patch_data, content_type='application/json')
        self.assertEqual(res_patch.status_code, 200)
        self.company1.refresh_from_db()
        self.assertEqual(self.company1.industry, 'Artificial Intelligence')
        self.assertEqual(self.company1.company_size, '201-500')
        self.assertEqual(self.company1.careers_website, 'https://techcorp.com/jobs')

    def test_company_profile_rejects_insecure_urls(self):
        self.client.force_login(self.company_user)
        bad_urls = [
            'http://insecure.com',
            'javascript:alert(1)',
            'https://user:pass@evil.com'
        ]
        for url in bad_urls:
            res = self.client.patch('/api/company/profile/', data={'careers_website': url}, content_type='application/json')
            self.assertEqual(res.status_code, 400)

    # ----------------------------------------------------
    # 2. Opportunity Creation & Validation Tests
    # ----------------------------------------------------
    def test_opportunity_draft_creation(self):
        self.client.force_login(self.company_user)
        payload = {
            'opportunity_type': 'job',
            'title': 'Junior Full Stack Developer',
            'description': 'Work with Python, Django, React, and TypeScript to build scalable platforms.',
            'required_skills': ['Python', 'Django', 'React'],
            'employment_type': 'full_time',
            'work_mode': 'remote',
            'location': 'Remote / India',
            'compensation': '₹6-8 LPA',
            'is_paid': True,
            'openings': 3,
            'recruitment_email': 'jobs@techcorp.com',
            'careers_url': 'https://techcorp.com/apply/fullstack',
            'deadline': (timezone.now() + datetime.timedelta(days=30)).date().isoformat()
        }
        res = self.client.post('/api/company/opportunities/', data=payload, content_type='application/json')
        self.assertEqual(res.status_code, 201)
        data = res.json()
        self.assertEqual(data['status'], 'draft')
        self.assertEqual(data['title'], 'Junior Full Stack Developer')
        self.assertTrue(Opportunity.objects.filter(id=data['id']).exists())

    def test_opportunity_submission_validation(self):
        self.client.force_login(self.company_user)
        # Create incomplete draft without application destination
        opp = Opportunity.objects.create(
            company=self.company1,
            opportunity_type=OpportunityType.JOB,
            title='Incomplete Job',
            description='Short',
            status=OpportunityStatus.DRAFT
        )
        # Try submitting
        res = self.client.post(f'/api/company/opportunities/{opp.id}/submit/')
        self.assertEqual(res.status_code, 400)
        self.assertIn('application_destination', res.json()['error'] if 'error' in res.json() else str(res.json()))

        # Add valid destination and description
        opp.description = 'This is a complete description of the opportunity with over thirty characters.'
        opp.recruitment_email = 'apply@techcorp.com'
        opp.save()

        # Submit again
        res_valid = self.client.post(f'/api/company/opportunities/{opp.id}/submit/')
        self.assertEqual(res_valid.status_code, 200)
        opp.refresh_from_db()
        self.assertEqual(opp.status, 'pending_review')

    def test_pending_company_cannot_submit_opportunity(self):
        # Recruiter 2's company is PENDING, so IsCompanyAdministrator denies access (403)
        self.client.force_login(self.other_company_user)
        opp = Opportunity.objects.create(
            company=self.company2,
            opportunity_type=OpportunityType.INTERNSHIP,
            title='Frontend Intern',
            description='A valid detailed internship description of more than 30 characters.',
            recruitment_email='interns@startuphub.io',
            status=OpportunityStatus.DRAFT
        )
        res = self.client.post(f'/api/company/opportunities/{opp.id}/submit/')
        self.assertEqual(res.status_code, 403)

    # ----------------------------------------------------
    # 3. Super Admin Moderation Tests
    # ----------------------------------------------------
    def test_super_admin_organization_approval_and_rejection(self):
        self.client.force_login(self.super_user)
        # Approve company 2
        res = self.client.post(f'/api/super-admin/approvals/organizations/company/{self.company2.pk}/review/', data={'action': 'approve', 'note': 'Verified legitimate startup.'}, content_type='application/json')
        self.assertEqual(res.status_code, 200)
        self.company2.refresh_from_db()
        self.assertEqual(self.company2.approval_status, 'approved')
        self.membership2.refresh_from_db()
        self.assertEqual(self.membership2.status, 'active')
        self.assertTrue(Notification.objects.filter(user=self.other_company_user).exists())

    def test_super_admin_opportunity_approval_and_rejection(self):
        opp = Opportunity.objects.create(
            company=self.company1,
            opportunity_type=OpportunityType.JOB,
            title='Backend Engineer',
            description='Detailed backend role description with more than thirty characters.',
            recruitment_email='careers@techcorp.com',
            status=OpportunityStatus.PENDING_REVIEW
        )

        self.client.force_login(self.super_user)
        # Approve
        res = self.client.post(f'/api/super-admin/approvals/opportunities/{opp.id}/review/', data={'action': 'approve', 'note': 'Approved for portal publication.'}, content_type='application/json')
        self.assertEqual(res.status_code, 200)
        opp.refresh_from_db()
        self.assertEqual(opp.status, 'approved')
        self.assertEqual(opp.reviewed_by, self.super_user)

    # ----------------------------------------------------
    # 4. Content Edit Triggers Reapproval Test
    # ----------------------------------------------------
    def test_editing_approved_opportunity_triggers_reapproval(self):
        opp = Opportunity.objects.create(
            company=self.company1,
            opportunity_type=OpportunityType.JOB,
            title='Staff Security Engineer',
            description='Security engineering role description with more than thirty characters.',
            recruitment_email='security@techcorp.com',
            status=OpportunityStatus.APPROVED
        )
        self.client.force_login(self.company_user)
        # Edit title and compensation
        res = self.client.patch(f'/api/company/opportunities/{opp.id}/', data={'title': 'Lead Security Engineer', 'compensation': '₹25-30 LPA'}, content_type='application/json')
        self.assertEqual(res.status_code, 200)
        opp.refresh_from_db()
        self.assertEqual(opp.title, 'Lead Security Engineer')
        self.assertEqual(opp.status, 'pending_review')
        self.assertEqual(opp.previous_status, 'approved')
        self.assertIn('re-approval', opp.review_note)

    # ----------------------------------------------------
    # 5. Delete Eligible Drafts Only Test
    # ----------------------------------------------------
    def test_delete_draft_vs_published_opportunity(self):
        self.client.force_login(self.company_user)
        draft_opp = Opportunity.objects.create(company=self.company1, opportunity_type=OpportunityType.JOB, title='Draft 1', description='Draft', status=OpportunityStatus.DRAFT)
        approved_opp = Opportunity.objects.create(company=self.company1, opportunity_type=OpportunityType.JOB, title='Approved 1', description='Approved', status=OpportunityStatus.APPROVED)

        # Draft deletion succeeds
        res_del_draft = self.client.delete(f'/api/company/opportunities/{draft_opp.id}/')
        self.assertEqual(res_del_draft.status_code, 200)
        self.assertFalse(Opportunity.objects.filter(id=draft_opp.id).exists())

        # Approved deletion rejected
        res_del_approved = self.client.delete(f'/api/company/opportunities/{approved_opp.id}/')
        self.assertEqual(res_del_approved.status_code, 400)
        self.assertTrue(Opportunity.objects.filter(id=approved_opp.id).exists())

    # ----------------------------------------------------
    # 6. Tenant Isolation Tests (Cross-Company Access)
    # ----------------------------------------------------
    def test_cross_company_access_rejected(self):
        # Company 1 opp
        opp1 = Opportunity.objects.create(company=self.company1, opportunity_type=OpportunityType.JOB, title='Company 1 Opp', description='Description...', status=OpportunityStatus.DRAFT)

        # Unapproved user gets 403
        self.client.force_login(self.other_company_user)
        self.assertEqual(self.client.get(f'/api/company/opportunities/{opp1.id}/').status_code, 403)

        # Now approve Company 2 and activate membership for recruiter 2
        self.company2.approval_status = OrganizationStatus.APPROVED
        self.company2.save()
        self.membership2.status = MembershipStatus.ACTIVE
        self.membership2.save()

        # Company 2 user tries to access/edit/delete Company 1 opp -> 404 Not Found (tenant-isolated)
        self.assertEqual(self.client.get(f'/api/company/opportunities/{opp1.id}/').status_code, 404)
        self.assertEqual(self.client.patch(f'/api/company/opportunities/{opp1.id}/', data={'title': 'Hacked'}, content_type='application/json').status_code, 404)
        self.assertEqual(self.client.delete(f'/api/company/opportunities/{opp1.id}/').status_code, 404)

    # ----------------------------------------------------
    # 7. Public Portal Discovery & Filtering Tests
    # ----------------------------------------------------
    def test_public_portal_visibility_and_company_suspension(self):
        # Active approved job with future deadline
        job1 = Opportunity.objects.create(
            company=self.company1,
            opportunity_type=OpportunityType.JOB,
            title='React Native Mobile Developer',
            description='Build mobile applications with React Native and TypeScript.',
            required_skills=['React Native', 'TypeScript', 'Redux'],
            work_mode='remote',
            employment_type='full_time',
            recruitment_email='mobile@techcorp.com',
            deadline=(timezone.now() + datetime.timedelta(days=15)).date(),
            status=OpportunityStatus.APPROVED
        )

        # Active approved internship with NO deadline (must remain visible)
        intern1 = Opportunity.objects.create(
            company=self.company1,
            opportunity_type=OpportunityType.INTERNSHIP,
            title='UI/UX Design Intern',
            description='Design intuitive user flows and student prototypes in Figma.',
            required_skills=['Figma', 'UI Design', 'Wireframing'],
            work_mode='hybrid',
            employment_type='part_time',
            recruitment_email='design@techcorp.com',
            deadline=None,
            status=OpportunityStatus.APPROVED
        )

        # Expired opportunity
        expired = Opportunity.objects.create(
            company=self.company1,
            opportunity_type=OpportunityType.JOB,
            title='Expired Sysadmin',
            description='Expired listing.',
            deadline=(timezone.now() - datetime.timedelta(days=2)).date(),
            status=OpportunityStatus.APPROVED
        )

        # Draft opportunity
        draft = Opportunity.objects.create(
            company=self.company1,
            opportunity_type=OpportunityType.JOB,
            title='Secret Draft',
            description='Draft listing.',
            status=OpportunityStatus.DRAFT
        )

        # Anonymous / public client
        client_pub = Client()
        res = client_pub.get('/api/opportunities/')
        self.assertEqual(res.status_code, 200)
        ids = [item['id'] for item in res.json()['results']]
        self.assertIn(str(job1.id), ids)
        self.assertIn(str(intern1.id), ids)
        self.assertNotIn(str(expired.id), ids)
        self.assertNotIn(str(draft.id), ids)

        # Filter by type: internship
        res_intern = client_pub.get('/api/opportunities/?type=internship')
        intern_ids = [item['id'] for item in res_intern.json()['results']]
        self.assertIn(str(intern1.id), intern_ids)
        self.assertNotIn(str(job1.id), intern_ids)

        # Filter by work_mode: remote
        res_remote = client_pub.get('/api/opportunities/?work_mode=remote')
        remote_ids = [item['id'] for item in res_remote.json()['results']]
        self.assertIn(str(job1.id), remote_ids)
        self.assertNotIn(str(intern1.id), remote_ids)

        # Detail view
        self.assertEqual(client_pub.get(f'/api/opportunities/{job1.id}/').status_code, 200)
        self.assertEqual(client_pub.get(f'/api/opportunities/{draft.id}/').status_code, 404)
        self.assertEqual(client_pub.get(f'/api/opportunities/{expired.id}/').status_code, 404)

        # Company suspension immediately hides opportunities
        self.company1.approval_status = OrganizationStatus.SUSPENDED
        self.company1.save()

        res_after_suspend = client_pub.get('/api/opportunities/')
        self.assertEqual(res_after_suspend.json()['count'], 0)
        self.assertEqual(client_pub.get(f'/api/opportunities/{job1.id}/').status_code, 404)

        # Reactivation restores visibility
        self.company1.approval_status = OrganizationStatus.APPROVED
        self.company1.save()
        res_after_reactivate = client_pub.get('/api/opportunities/')
        self.assertEqual(res_after_reactivate.json()['count'], 2)

    def test_strict_opportunity_status_transitions(self):
        # 1. Draft cannot be approved directly
        draft = Opportunity.objects.create(
            company=self.company1,
            opportunity_type=OpportunityType.JOB,
            title='Direct Draft Approval Test',
            description='This is a long description with over thirty characters.',
            recruitment_email='jobs@techcorp.com',
            status=OpportunityStatus.DRAFT
        )
        self.client.force_login(self.super_user)
        res_bad_approve = self.client.post(f'/api/super-admin/approvals/opportunities/{draft.id}/review/', {'action': 'approve'}, format='json')
        self.assertEqual(res_bad_approve.status_code, 400)
        self.assertIn('Cannot approve an opportunity with status', res_bad_approve.json()['error'])

        # 2. Draft cannot be reactivated or suspended
        res_bad_reactivate = self.client.post(f'/api/super-admin/approvals/opportunities/{draft.id}/review/', {'action': 'reactivate'}, format='json')
        self.assertEqual(res_bad_reactivate.status_code, 400)
        res_bad_suspend = self.client.post(f'/api/super-admin/approvals/opportunities/{draft.id}/review/', {'action': 'suspend'}, format='json')
        self.assertEqual(res_bad_suspend.status_code, 400)

        # 3. Submit properly to pending_review
        draft.status = OpportunityStatus.PENDING_REVIEW
        draft.save()

        # 4. Now approve works
        res_approve = self.client.post(f'/api/super-admin/approvals/opportunities/{draft.id}/review/', {'action': 'approve'}, format='json')
        self.assertEqual(res_approve.status_code, 200)
        draft.refresh_from_db()
        self.assertEqual(draft.status, OpportunityStatus.APPROVED)

        # 5. Approved can be suspended, but cannot be reactivated or rejected
        res_reactivate_approved = self.client.post(f'/api/super-admin/approvals/opportunities/{draft.id}/review/', {'action': 'reactivate'}, format='json')
        self.assertEqual(res_reactivate_approved.status_code, 400)
        res_suspend = self.client.post(f'/api/super-admin/approvals/opportunities/{draft.id}/review/', {'action': 'suspend'}, format='json')
        self.assertEqual(res_suspend.status_code, 200)
        draft.refresh_from_db()
        self.assertEqual(draft.status, OpportunityStatus.SUSPENDED)

        # 6. Suspended can be reactivated
        res_reactivate = self.client.post(f'/api/super-admin/approvals/opportunities/{draft.id}/review/', {'action': 'reactivate'}, format='json')
        self.assertEqual(res_reactivate.status_code, 200)
        draft.refresh_from_db()
        self.assertEqual(draft.status, OpportunityStatus.APPROVED)

    def test_cannot_approve_expired_or_destination_less_opportunity(self):
        self.client.force_login(self.super_user)
        # Opportunity with past deadline
        expired_opp = Opportunity.objects.create(
            company=self.company1,
            opportunity_type=OpportunityType.JOB,
            title='Expired Job Review',
            description='This is a long description with over thirty characters.',
            recruitment_email='jobs@techcorp.com',
            deadline=timezone.now().date() - datetime.timedelta(days=2),
            status=OpportunityStatus.PENDING_REVIEW
        )
        res = self.client.post(f'/api/super-admin/approvals/opportunities/{expired_opp.id}/review/', {'action': 'approve'}, format='json')
        self.assertEqual(res.status_code, 400)
        self.assertIn('expired', res.json()['error'].lower())

        # Opportunity with no destination
        no_dest_opp = Opportunity.objects.create(
            company=self.company1,
            opportunity_type=OpportunityType.JOB,
            title='No Destination Job',
            description='This is a long description with over thirty characters.',
            recruitment_email='',
            careers_url='',
            status=OpportunityStatus.PENDING_REVIEW
        )
        res2 = self.client.post(f'/api/super-admin/approvals/opportunities/{no_dest_opp.id}/review/', {'action': 'approve'}, format='json')
        self.assertEqual(res2.status_code, 400)
        self.assertIn('destination', res2.json()['error'].lower())

    def test_membership_security_and_organization_transitions(self):
        self.client.force_login(self.super_user)
        # Create a new pending company
        new_user = User.objects.create_user('newfounder@test.com', 'newfounder@test.com', 'Pass123!')
        Profile.objects.create(user=new_user, roles=['student'], age=22)
        new_company = Company.objects.create(name='New Startup', website='https://startup.com', contact_email='info@startup.com', created_by=new_user)
        pending_mem = CompanyMembership.objects.create(company=new_company, user=new_user, role=CompanyMembership.Role.ADMIN, status=MembershipStatus.PENDING)

        # Create an explicitly inactive former member
        former_user = User.objects.create_user('former@test.com', 'former@test.com', 'Pass123!')
        inactive_mem = CompanyMembership.objects.create(company=new_company, user=former_user, role=CompanyMembership.Role.ADMIN, status=MembershipStatus.INACTIVE)

        # Approve company
        res = self.client.post(f'/api/super-admin/approvals/organizations/company/{new_company.id}/review/', {'action': 'approve'}, format='json')
        self.assertEqual(res.status_code, 200)

        pending_mem.refresh_from_db()
        inactive_mem.refresh_from_db()
        # Pending was activated
        self.assertEqual(pending_mem.status, MembershipStatus.ACTIVE)
        # Inactive membership was NOT activated
        self.assertEqual(inactive_mem.status, MembershipStatus.INACTIVE)

        # Suspend company
        res_suspend = self.client.post(f'/api/super-admin/approvals/organizations/company/{new_company.id}/review/', {'action': 'suspend'}, format='json')
        self.assertEqual(res_suspend.status_code, 200)
        new_company.refresh_from_db()
        self.assertEqual(new_company.approval_status, OrganizationStatus.SUSPENDED)

        # Cannot suspend again
        res_bad_suspend = self.client.post(f'/api/super-admin/approvals/organizations/company/{new_company.id}/review/', {'action': 'suspend'}, format='json')
        self.assertEqual(res_bad_suspend.status_code, 400)

        # Reactivate
        res_reactivate = self.client.post(f'/api/super-admin/approvals/organizations/company/{new_company.id}/review/', {'action': 'reactivate'}, format='json')
        self.assertEqual(res_reactivate.status_code, 200)
        inactive_mem.refresh_from_db()
        self.assertEqual(inactive_mem.status, MembershipStatus.INACTIVE)

    def test_cannot_edit_closed_opportunity(self):
        opp = Opportunity.objects.create(
            company=self.company1,
            opportunity_type=OpportunityType.JOB,
            title='Close Edit Test',
            description='This is a long description with over thirty characters.',
            recruitment_email='jobs@techcorp.com',
            status=OpportunityStatus.CLOSED
        )
        self.client.force_login(self.company_user)
        res = self.client.patch(f'/api/company/opportunities/{opp.id}/', {'title': 'New Closed Title'}, content_type='application/json')
        self.assertEqual(res.status_code, 400)
        self.assertIn('Cannot edit a closed opportunity', res.json()['error'])
