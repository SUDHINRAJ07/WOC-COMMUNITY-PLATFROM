from django.contrib.auth.models import User
from django.test import TestCase, Client
from rest_framework import status

from core.models import (
    Profile, Institution, Company, CollegeMembership,
    OrganizationStatus, MembershipStatus, Program, Record, Certificate,
    TrainingBatch, Opportunity, OpportunityType, OpportunityStatus,
    Notification, SavedOpportunity, OpportunityApplicationLog
)


class StudentExperienceTests(TestCase):
    def setUp(self):
        self.client = Client()

        # Student A
        self.student_a = User.objects.create_user(
            username="student_a",
            first_name="Aarav",
            email="aarav@example.com",
            password="Password123!"
        )
        Profile.objects.create(
            user=self.student_a,
            age=20,
            email_verified=True,
            roles=['student']
        )

        # Student B (for privacy / tenant isolation tests)
        self.student_b = User.objects.create_user(
            username="student_b",
            first_name="Meera",
            email="meera@example.com",
            password="Password123!"
        )
        Profile.objects.create(
            user=self.student_b,
            age=21,
            email_verified=True,
            roles=['student']
        )

        # Approved College 1 & Admin
        self.college_1 = Institution.objects.create(
            name="National Tech University",
            city="Chennai",
            contact_email="admin@ntu.edu",
            website="https://ntu.edu",
            approval_status=OrganizationStatus.APPROVED,
            verified=True
        )
        self.college_admin = User.objects.create_user(
            username="ntu_admin",
            email="admin@ntu.edu",
            password="Password123!"
        )
        Profile.objects.create(user=self.college_admin, age=35, email_verified=True)
        CollegeMembership.objects.create(
            user=self.college_admin,
            institution=self.college_1,
            role=CollegeMembership.Role.ADMIN,
            status=MembershipStatus.ACTIVE
        )

        # Approved College 2 & Pending College 3
        self.college_2 = Institution.objects.create(
            name="Southern Science Institute",
            city="Madurai",
            contact_email="admin@ssi.edu",
            website="https://ssi.edu",
            approval_status=OrganizationStatus.APPROVED,
            verified=True
        )
        self.college_pending = Institution.objects.create(
            name="Unverified Academy",
            city="Salem",
            contact_email="info@unverified.edu",
            approval_status=OrganizationStatus.PENDING,
            verified=False
        )

        # Approved Company & Opportunity
        self.company_user = User.objects.create_user(
            username="recruiter_1",
            email="hr@cloudworks.io",
            password="Password123!"
        )
        Profile.objects.create(user=self.company_user, age=30, email_verified=True)
        self.company = Company.objects.create(
            name="CloudWorks India",
            city="Bengaluru",
            contact_email="hr@cloudworks.io",
            recruitment_email="jobs@cloudworks.io",
            website="https://cloudworks.io",
            created_by=self.company_user,
            approval_status=OrganizationStatus.APPROVED
        )
        self.opportunity = Opportunity.objects.create(
            company=self.company,
            opportunity_type=OpportunityType.INTERNSHIP,
            title="Python Backend Intern",
            description="Build Django REST APIs and scalable services.",
            required_skills=["Python", "Django", "SQL"],
            recruitment_email="jobs@cloudworks.io",
            careers_url="https://cloudworks.io/careers/python-intern",
            status=OpportunityStatus.APPROVED
        )

        # Academy Program & Record
        self.program = Program.objects.create(
            slug="python-foundations",
            module="academy",
            title="Python Foundations",
            description="Core Python programming.",
            category="Engineering"
        )

    def test_unauthenticated_blocked(self):
        resp = self.client.get('/api/student/dashboard/')
        self.assertIn(resp.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_profile_update_and_completion_percentage(self):
        self.client.force_login(self.student_a)

        # Reject insecure HTTP resume URL
        bad_resp = self.client.patch(
            '/api/student/profile/',
            data={'resume_url': 'http://insecure.example.com/cv.pdf'},
            content_type='application/json'
        )
        self.assertEqual(bad_resp.status_code, status.HTTP_400_BAD_REQUEST)

        # Valid profile update
        resp = self.client.patch(
            '/api/student/profile/',
            data={
                'city': 'Chennai',
                'qualification': 'B.E. Computer Science',
                'skills': ['Python', 'Django', 'TypeScript'],
                'interests': ['Backend Engineering'],
                'career_goals': 'Become a backend engineer.',
                'resume_url': 'https://example.com/aarav-resume.pdf',
                'bio': 'Passionate CS student.'
            },
            content_type='application/json'
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        # Photo, graduation year and verified mobile are still missing.
        self.assertEqual(resp.data['profile_completion']['percentage'], 75)
        self.assertIn('Profile photo', resp.data['profile_completion']['missing'])
        self.assertIn('Education graduation year', resp.data['profile_completion']['missing'])
        self.assertEqual(resp.data['user']['skills'], ['Python', 'Django', 'TypeScript'])

        # Dashboard reflects completion and skill-matched recommendation
        dash = self.client.get('/api/student/dashboard/')
        self.assertEqual(dash.status_code, status.HTTP_200_OK)
        recs = dash.data['opportunities']['recommended']
        self.assertTrue(any(r['id'] == str(self.opportunity.pk) and r['match_score'] > 0 for r in recs))

    def test_college_affiliation_flow_and_single_active_constraint(self):
        self.client.force_login(self.student_a)

        # 1. Search approved colleges (pending college must NOT appear)
        search_resp = self.client.get('/api/student/colleges/')
        self.assertEqual(search_resp.status_code, status.HTTP_200_OK)
        names = [c['name'] for c in search_resp.data['colleges']]
        self.assertIn("National Tech University", names)
        self.assertNotIn("Unverified Academy", names)

        # 2. Submit membership request to College 1
        req_resp = self.client.post(
            '/api/student/colleges/request/',
            data={'institution_id': self.college_1.pk},
            content_type='application/json'
        )
        self.assertEqual(req_resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(req_resp.data['status'], MembershipStatus.PENDING)
        membership_id = req_resp.data['membership_id']

        # 3. College Admin approves Student A -> Notification generated
        self.client.force_login(self.college_admin)
        approve_resp = self.client.post(
            f'/api/college/students/{membership_id}/review/',
            data={'action': 'approve'},
            content_type='application/json'
        )
        self.assertEqual(approve_resp.status_code, status.HTTP_200_OK)
        self.assertTrue(
            Notification.objects.filter(
                user=self.student_a,
                message__icontains="approved"
            ).exists()
        )

        # 4. Student A cannot request College 2 while active at College 1
        self.client.force_login(self.student_a)
        conflict_resp = self.client.post(
            '/api/student/colleges/request/',
            data={'institution_id': self.college_2.pk},
            content_type='application/json'
        )
        self.assertEqual(conflict_resp.status_code, status.HTTP_409_CONFLICT)

        # 5. Student A leaves College 1, then can request College 2
        leave_resp = self.client.post('/api/student/colleges/leave/', data={}, content_type='application/json')
        self.assertEqual(leave_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(leave_resp.data['status'], MembershipStatus.INACTIVE)

        req2_resp = self.client.post(
            '/api/student/colleges/request/',
            data={'institution_id': self.college_2.pk},
            content_type='application/json'
        )
        self.assertEqual(req2_resp.status_code, status.HTTP_201_CREATED)

    def test_assigned_batches_and_learning_progress(self):
        CollegeMembership.objects.create(
            user=self.student_a,
            institution=self.college_1,
            role=CollegeMembership.Role.STUDENT,
            status=MembershipStatus.ACTIVE
        )
        batch = TrainingBatch.objects.create(
            institution=self.college_1,
            name="2026 Python Cohort",
            program=self.program,
            status='in_progress',
            capacity=30
        )

        # Admin enrolls Student A in batch -> Notification created
        self.client.force_login(self.college_admin)
        enroll_resp = self.client.post(
            f'/api/college/batches/{batch.pk}/enroll/',
            data={'action': 'enroll', 'student_ids': [self.student_a.pk]},
            content_type='application/json'
        )
        self.assertEqual(enroll_resp.status_code, status.HTTP_200_OK)
        self.assertTrue(
            Notification.objects.filter(
                user=self.student_a,
                message__icontains="2026 Python Cohort"
            ).exists()
        )

        # Student A enrolls in Academy program and completes 1 lesson
        self.client.force_login(self.student_a)
        rec = Record.objects.create(user=self.student_a, program=self.program, status='enrolled', data={'lessons': [0]})

        batches_resp = self.client.get('/api/student/batches/')
        self.assertEqual(batches_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(batches_resp.data['results']), 1)
        self.assertEqual(batches_resp.data['results'][0]['progress']['lessons_completed'], 1)
        self.assertGreater(batches_resp.data['results'][0]['progress']['percentage'], 0)

        # Student B cannot see Student A's batch
        self.client.force_login(self.student_b)
        b_batches = self.client.get('/api/student/batches/')
        self.assertEqual(len(b_batches.data['results']), 0)

    def test_saved_opportunities_and_external_click_vs_applied(self):
        self.client.force_login(self.student_a)

        # Bookmark opportunity
        save_resp = self.client.post(
            f'/api/student/opportunities/{self.opportunity.pk}/save/',
            data={'action': 'save'},
            content_type='application/json'
        )
        self.assertEqual(save_resp.status_code, status.HTTP_200_OK)
        self.assertTrue(save_resp.data['saved'])

        # External link click MUST NOT mark status as 'applied'
        click_resp = self.client.post(
            f'/api/student/opportunities/{self.opportunity.pk}/track/',
            data={'action': 'click'},
            content_type='application/json'
        )
        self.assertEqual(click_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(click_resp.data['status'], OpportunityApplicationLog.Status.CLICKED)
        self.assertEqual(click_resp.data['external_click_count'], 1)

        # Manually update status to 'applied'
        apply_resp = self.client.post(
            f'/api/student/opportunities/{self.opportunity.pk}/track/',
            data={'action': 'update_status', 'status': 'applied', 'notes': 'Submitted via company portal.'},
            content_type='application/json'
        )
        self.assertEqual(apply_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(apply_resp.data['status'], 'applied')

        # Another external click must NOT overwrite 'applied' status
        click2_resp = self.client.post(
            f'/api/student/opportunities/{self.opportunity.pk}/track/',
            data={'action': 'click'},
            content_type='application/json'
        )
        self.assertEqual(click2_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(click2_resp.data['status'], 'applied')
        self.assertEqual(click2_resp.data['external_click_count'], 2)

        # Tenant isolation: Student B sees empty saved & applications lists
        self.client.force_login(self.student_b)
        self.assertEqual(self.client.get('/api/student/opportunities/saved/').data['count'], 0)
        self.assertEqual(self.client.get('/api/student/opportunities/applications/').data['count'], 0)

    def test_student_certificates_isolation(self):
        rec = Record.objects.create(user=self.student_a, program=self.program, status='completed', data={'lessons': [0, 1, 2], 'score': 3})
        cert = Certificate.objects.create(record=rec, issued_by=self.college_admin)

        self.client.force_login(self.student_a)
        a_certs = self.client.get('/api/student/certificates/')
        self.assertEqual(a_certs.status_code, status.HTTP_200_OK)
        self.assertEqual(len(a_certs.data['results']), 1)
        self.assertEqual(a_certs.data['results'][0]['id'], str(cert.id))

        # Student B cannot see Student A's certificate in private endpoint
        self.client.force_login(self.student_b)
        b_certs = self.client.get('/api/student/certificates/')
        self.assertEqual(len(b_certs.data['results']), 0)

        # Public verification endpoint returns minimal info (first_name, program, issued_at)
        verify = self.client.get(f'/api/certificates/{cert.id}/')
        self.assertEqual(verify.status_code, status.HTTP_200_OK)
        self.assertEqual(verify.data['name'], 'Aarav')
        self.assertNotIn('email', verify.data)
