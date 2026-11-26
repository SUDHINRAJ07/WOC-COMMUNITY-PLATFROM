import datetime
from django.contrib.auth.models import User, Group
from django.test import TestCase, Client
from rest_framework import status

from core.models import (
    Institution, Company, CollegeMembership, CompanyMembership,
    OrganizationStatus, MembershipStatus, Program,
    TrainingBatch, CampusPlacement, CollegePartnership,
    Opportunity, OpportunityType, OpportunityStatus, EmploymentType, WorkMode
)


class CollegeManagementTests(TestCase):
    def setUp(self):
        self.client = Client()

        # College A & Admin
        self.college_a = Institution.objects.create(
            name="Alpha Engineering College",
            city="Chennai",
            contact_email="admin@alpha.edu",
            website="https://alpha.edu",
            approval_status=OrganizationStatus.APPROVED,
            verified=True
        )
        self.admin_a = User.objects.create_user(
            username="admin_a",
            email="admin@alpha.edu",
            password="Password123!"
        )
        CollegeMembership.objects.create(
            user=self.admin_a,
            institution=self.college_a,
            role=CollegeMembership.Role.ADMIN,
            status=MembershipStatus.ACTIVE
        )

        # College B & Admin (for tenant isolation tests)
        self.college_b = Institution.objects.create(
            name="Beta Institute of Tech",
            city="Coimbatore",
            contact_email="admin@beta.edu",
            website="https://beta.edu",
            approval_status=OrganizationStatus.APPROVED,
            verified=True
        )
        self.admin_b = User.objects.create_user(
            username="admin_b",
            email="admin@beta.edu",
            password="Password123!"
        )
        CollegeMembership.objects.create(
            user=self.admin_b,
            institution=self.college_b,
            role=CollegeMembership.Role.ADMIN,
            status=MembershipStatus.ACTIVE
        )

        # Partner Company Recruiter & Company
        self.company_user = User.objects.create_user(
            username="company_admin_user",
            email="hr@apextech.io",
            password="Password123!"
        )
        self.company = Company.objects.create(
            name="Apex Tech Corp",
            city="Chennai",
            contact_email="hr@apextech.io",
            recruitment_email="careers@apextech.io",
            website="https://apextech.io",
            created_by=self.company_user,
            approval_status=OrganizationStatus.APPROVED
        )
        CompanyMembership.objects.create(
            user=self.company_user,
            company=self.company,
            role=CompanyMembership.Role.ADMIN,
            status=MembershipStatus.ACTIVE
        )

        # Program
        self.program = Program.objects.create(
            slug="web-dev-pro",
            module="academy",
            title="Full Stack Web Development"
        )

        # Students
        self.student_1 = User.objects.create_user(
            username="student_one",
            first_name="Ravi",
            last_name="Kumar",
            email="ravi@alpha.edu",
            password="Password123!"
        )
        self.student_1_membership = CollegeMembership.objects.create(
            user=self.student_1,
            institution=self.college_a,
            role=CollegeMembership.Role.STUDENT,
            status=MembershipStatus.PENDING
        )

        self.student_2 = User.objects.create_user(
            username="student_two",
            first_name="Priya",
            last_name="Rajan",
            email="priya@alpha.edu",
            password="Password123!"
        )
        self.student_2_membership = CollegeMembership.objects.create(
            user=self.student_2,
            institution=self.college_a,
            role=CollegeMembership.Role.STUDENT,
            status=MembershipStatus.ACTIVE
        )

    def test_unauthenticated_blocked(self):
        resp = self.client.get('/api/college/dashboard/')
        self.assertIn(resp.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_student_cannot_access_college_admin(self):
        self.client.force_login(self.student_2)
        resp = self.client.get('/api/college/dashboard/')
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_college_overview_and_profile(self):
        self.client.force_login(self.admin_a)
        resp = self.client.get('/api/college/dashboard/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['college']['name'], "Alpha Engineering College")
        self.assertEqual(resp.data['metrics']['total_students'], 2)
        self.assertEqual(resp.data['metrics']['pending_requests'], 1)
        self.assertEqual(resp.data['metrics']['active_students'], 1)

        # Update profile
        patch_resp = self.client.patch(
            '/api/college/profile/',
            data={
                'phone': '+91 9876543210',
                'principal_name': 'Dr. K. Swaminathan',
                'description': 'Premier technological institution.',
                'city': 'Chennai Metro'
            },
            content_type='application/json'
        )
        self.assertEqual(patch_resp.status_code, status.HTTP_200_OK)
        self.college_a.refresh_from_db()
        self.assertEqual(self.college_a.phone, '+91 9876543210')
        self.assertEqual(self.college_a.principal_name, 'Dr. K. Swaminathan')
        self.assertEqual(self.college_a.city, 'Chennai Metro')

    def test_student_approval_and_single_active_college_constraint(self):
        self.client.force_login(self.admin_a)

        # 1. Approve student 1
        resp = self.client.post(
            f'/api/college/students/{self.student_1_membership.pk}/review/',
            data={'action': 'approve'},
            content_type='application/json'
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.student_1_membership.refresh_from_db()
        self.assertEqual(self.student_1_membership.status, MembershipStatus.ACTIVE)

        # 2. Student 1 requests membership at College B
        b_membership = CollegeMembership.objects.create(
            user=self.student_1,
            institution=self.college_b,
            role=CollegeMembership.Role.STUDENT,
            status=MembershipStatus.PENDING
        )

        # 3. Admin B attempts to approve Student 1 while active at College A -> Must be rejected with 409
        self.client.force_login(self.admin_b)
        b_resp = self.client.post(
            f'/api/college/students/{b_membership.pk}/review/',
            data={'action': 'approve'},
            content_type='application/json'
        )
        self.assertEqual(b_resp.status_code, status.HTTP_409_CONFLICT)
        self.assertIn("already has an active affiliation", b_resp.data['error'])

        # 4. Admin A deactivates Student 1
        self.client.force_login(self.admin_a)
        deact_resp = self.client.post(
            f'/api/college/students/{self.student_1_membership.pk}/review/',
            data={'action': 'deactivate'},
            content_type='application/json'
        )
        self.assertEqual(deact_resp.status_code, status.HTTP_200_OK)

        # 5. Now Admin B can approve Student 1
        self.client.force_login(self.admin_b)
        b_resp2 = self.client.post(
            f'/api/college/students/{b_membership.pk}/review/',
            data={'action': 'approve'},
            content_type='application/json'
        )
        self.assertEqual(b_resp2.status_code, status.HTTP_200_OK)
        b_membership.refresh_from_db()
        self.assertEqual(b_membership.status, MembershipStatus.ACTIVE)

    def test_training_batch_lifecycle_and_tenant_enrollment(self):
        self.client.force_login(self.admin_a)

        # Create batch
        create_resp = self.client.post(
            '/api/college/batches/',
            data={
                'name': 'Batch 2026 Alpha Web Dev',
                'program_id': self.program.slug,
                'capacity': 2,
                'status': 'upcoming'
            },
            content_type='application/json'
        )
        self.assertEqual(create_resp.status_code, status.HTTP_201_CREATED)
        batch_id = create_resp.data['id']

        # Enroll student 2 (active student of College A) -> OK
        enroll_resp = self.client.post(
            f'/api/college/batches/{batch_id}/enroll/',
            data={
                'action': 'enroll',
                'student_ids': [self.student_2.pk]
            },
            content_type='application/json'
        )
        self.assertEqual(enroll_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(enroll_resp.data['students']), 1)

        # Attempt to enroll student from College B into College A batch -> Forbidden/Error
        student_b = User.objects.create_user(username="student_b", email="b@beta.edu", password="Password123!")
        CollegeMembership.objects.create(
            user=student_b,
            institution=self.college_b,
            role=CollegeMembership.Role.STUDENT,
            status=MembershipStatus.ACTIVE
        )

        cross_enroll = self.client.post(
            f'/api/college/batches/{batch_id}/enroll/',
            data={
                'action': 'enroll',
                'student_ids': [student_b.pk]
            },
            content_type='application/json'
        )
        self.assertEqual(cross_enroll.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("not active students of this college", cross_enroll.data['error'])

    def test_campus_placement_management(self):
        self.client.force_login(self.admin_a)

        # Record campus placement for active student_2
        place_resp = self.client.post(
            '/api/college/placements/',
            data={
                'student_id': self.student_2.pk,
                'company_id': str(self.company.pk),
                'role_title': 'Junior Software Engineer',
                'placement_type': 'job',
                'compensation': '8 LPA',
                'status': 'offered'
            },
            content_type='application/json'
        )
        self.assertEqual(place_resp.status_code, status.HTTP_201_CREATED)
        placement_id = place_resp.data['id']

        # Update placement to accepted
        patch_resp = self.client.patch(
            f'/api/college/placements/{placement_id}/',
            data={'status': 'accepted'},
            content_type='application/json'
        )
        self.assertEqual(patch_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(patch_resp.data['status'], 'accepted')

    def test_corporate_partnership(self):
        self.client.force_login(self.admin_a)

        part_resp = self.client.post(
            '/api/college/partnerships/',
            data={
                'company_id': str(self.company.pk),
                'partnership_type': 'Campus Recruitment & Internship Partner',
                'status': 'active',
                'contact_person': 'Anita Sharma',
                'notes': 'Annual campus drive partner.'
            },
            content_type='application/json'
        )
        self.assertEqual(part_resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(part_resp.data['company']['name'], 'Apex Tech Corp')

        # Prevent duplicate partnership with same company
        dup_resp = self.client.post(
            '/api/college/partnerships/',
            data={
                'company_id': str(self.company.pk),
                'partnership_type': 'Duplicate'
            },
            content_type='application/json'
        )
        self.assertEqual(dup_resp.status_code, status.HTTP_409_CONFLICT)

    def test_tenant_isolation_between_colleges(self):
        # Admin A creates a batch in College A
        batch_a = TrainingBatch.objects.create(
            institution=self.college_a,
            name="Alpha AI Batch",
            capacity=30
        )

        # Admin B attempts to access or modify College A's batch -> 404
        self.client.force_login(self.admin_b)
        resp = self.client.get(f'/api/college/batches/{batch_a.pk}/')
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

        patch_resp = self.client.patch(
            f'/api/college/batches/{batch_a.pk}/',
            data={'name': 'Hacked Batch'},
            content_type='application/json'
        )
        self.assertEqual(patch_resp.status_code, status.HTTP_404_NOT_FOUND)
