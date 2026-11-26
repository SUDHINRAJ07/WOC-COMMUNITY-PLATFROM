from datetime import timedelta
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase, Client
from django.utils import timezone
from rest_framework import status

from core.models import (
    Profile, Institution, CollegeMembership, OrganizationStatus, MembershipStatus,
    CampusEvent, EventRegistration, StudentClub, ClubMembership,
    CampusLeadership, CampusAnnouncement, Notification
)


class Phase6EngagementTests(TestCase):
    def setUp(self):
        self.client = Client()

        # College A & Admin
        self.college_a = Institution.objects.create(
            name="Alpha Tech College", city="Chennai",
            approval_status=OrganizationStatus.APPROVED, verified=True
        )
        self.admin_a = User.objects.create_user(username="admin_a6", email="admin_a6@alpha.edu", password="Password123!")
        Profile.objects.create(user=self.admin_a, age=35, email_verified=True)
        CollegeMembership.objects.create(
            user=self.admin_a, institution=self.college_a,
            role=CollegeMembership.Role.ADMIN, status=MembershipStatus.ACTIVE
        )

        # College B & Student B
        self.college_b = Institution.objects.create(
            name="Beta Arts College", city="Madurai",
            approval_status=OrganizationStatus.APPROVED, verified=True
        )
        self.student_b = User.objects.create_user(username="student_b6", first_name="Bala", email="b6@beta.edu", password="Password123!")
        Profile.objects.create(user=self.student_b, age=20, email_verified=True, roles=['student'])
        CollegeMembership.objects.create(
            user=self.student_b, institution=self.college_b,
            role=CollegeMembership.Role.STUDENT, status=MembershipStatus.ACTIVE
        )

        # Student A (at College A)
        self.student_a = User.objects.create_user(username="student_a6", first_name="Ananya", email="a6@alpha.edu", password="Password123!")
        Profile.objects.create(user=self.student_a, age=20, email_verified=True, roles=['student'])
        CollegeMembership.objects.create(
            user=self.student_a, institution=self.college_a,
            role=CollegeMembership.Role.STUDENT, status=MembershipStatus.ACTIVE
        )

        # Super Admin
        self.super_admin = User.objects.create_superuser(username="super6", email="super6@woc.org", password="Password123!")
        Profile.objects.create(user=self.super_admin, age=40, email_verified=True)

    def test_campus_events_visibility_capacity_attendance_and_notifications(self):
        self.client.force_login(self.admin_a)
        future = (timezone.now() + timedelta(days=5)).isoformat()

        # Create college-only event (capacity 1) & public event
        ev_college = self.client.post('/api/college/events/', data={
            'title': 'Alpha Hackathon', 'event_type': 'competition',
            'description': 'Internal 24h hackathon.', 'venue': 'Main Auditorium',
            'event_date': future, 'capacity': 1, 'visibility': 'college'
        }, content_type='application/json')
        self.assertEqual(ev_college.status_code, status.HTTP_201_CREATED)
        ev_college_id = ev_college.data['id']

        ev_public = self.client.post('/api/college/events/', data={
            'title': 'Open AI Webinar', 'event_type': 'webinar',
            'description': 'Public webinar for all students.', 'venue': 'Online',
            'event_date': future, 'capacity': 50, 'visibility': 'public'
        }, content_type='application/json')
        self.assertEqual(ev_public.status_code, status.HTTP_201_CREATED)
        ev_public_id = ev_public.data['id']

        # Student B (College B) blocked from College A's college-only event, allowed on public event
        self.client.force_login(self.student_b)
        self.assertEqual(self.client.post(f'/api/student/events/{ev_college_id}/register/').status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.client.post(f'/api/student/events/{ev_public_id}/register/').status_code, status.HTTP_201_CREATED)

        # Student A registers for college-only event -> notification created
        self.client.force_login(self.student_a)
        reg_res = self.client.post(f'/api/student/events/{ev_college_id}/register/')
        self.assertEqual(reg_res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Notification.objects.filter(user=self.student_a, message__icontains='Alpha Hackathon').exists())

        # Admin A marks attendance & achievement
        self.client.force_login(self.admin_a)
        reg_obj = EventRegistration.objects.get(event_id=ev_college_id, student=self.student_a)
        att_res = self.client.post(
            f'/api/college/events/{ev_college_id}/participants/{reg_obj.pk}/',
            data={'status': 'attended', 'achievement': '1st Place Winner'},
            content_type='application/json'
        )
        self.assertEqual(att_res.status_code, status.HTTP_200_OK)

        # Student A sees achievement & stats in engagement overview
        self.client.force_login(self.student_a)
        eng = self.client.get('/api/student/engagement/').data
        self.assertEqual(eng['stats']['attended_events'], 1)
        self.assertEqual(eng['achievements'][0]['title'], '1st Place Winner')

    def test_clubs_leadership_limited_permissions_and_revocation(self):
        self.client.force_login(self.admin_a)
        club_res = self.client.post('/api/college/clubs/', data={
            'name': 'Alpha Robotics Club', 'category': 'technical',
            'description': 'Build autonomous bots.'
        }, content_type='application/json')
        self.assertEqual(club_res.status_code, status.HTTP_201_CREATED)
        club_id = club_res.data['id']

        # Student B from College B cannot join College A's club
        self.client.force_login(self.student_b)
        self.assertEqual(self.client.post(f'/api/student/clubs/{club_id}/join/').status_code, status.HTTP_403_FORBIDDEN)

        # Student A requests to join & Admin A approves
        self.client.force_login(self.student_a)
        self.assertEqual(self.client.post(f'/api/student/clubs/{club_id}/join/').status_code, status.HTTP_201_CREATED)

        self.client.force_login(self.admin_a)
        membership = ClubMembership.objects.get(club_id=club_id, student=self.student_a)
        self.assertEqual(
            self.client.post(f'/api/college/clubs/{club_id}/members/{membership.pk}/review/', data={'action': 'approve'}, content_type='application/json').status_code,
            status.HTTP_200_OK
        )

        # Assign Student A as Club Leader
        lead_res = self.client.post('/api/college/leadership/', data={
            'student_id': self.student_a.pk,
            'role': 'club_leader',
            'club_id': club_id,
            'title': 'Robotics Lead',
            'responsibilities': 'Lead weekly robotics workshops.'
        }, content_type='application/json')
        self.assertEqual(lead_res.status_code, status.HTTP_201_CREATED)
        lead_id = lead_res.data['id']

        # Student A can post club announcement, but CANNOT access college admin endpoints
        self.client.force_login(self.student_a)
        self.assertEqual(self.client.get('/api/college/events/').status_code, status.HTTP_403_FORBIDDEN)
        ann_res = self.client.post('/api/student/leadership/announcements/', data={
            'club_id': club_id, 'title': 'Bot Meetup Friday', 'content': 'Lab 3 at 4 PM.'
        }, content_type='application/json')
        self.assertEqual(ann_res.status_code, status.HTTP_201_CREATED)

        # Revoke leadership -> Student A can no longer post club announcements
        self.client.force_login(self.admin_a)
        self.assertEqual(self.client.post(f'/api/college/leadership/{lead_id}/revoke/').status_code, status.HTTP_200_OK)

        self.client.force_login(self.student_a)
        self.assertEqual(
            self.client.post('/api/student/leadership/announcements/', data={
                'club_id': club_id, 'title': 'Unauthorized', 'content': 'Should fail.'
            }, content_type='application/json').status_code,
            status.HTTP_403_FORBIDDEN
        )

    def test_super_admin_oversight_and_moderation(self):
        club = StudentClub.objects.create(
            institution=self.college_a, name="Temp Club",
            category='cultural', description="Desc"
        )
        self.client.force_login(self.super_admin)
        ov = self.client.get('/api/super-admin/engagement/')
        self.assertEqual(ov.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(ov.data['summary']['total_clubs'], 1)

        mod = self.client.post('/api/super-admin/engagement/moderate/', data={
            'kind': 'club', 'target_id': str(club.pk), 'action': 'suspend', 'note': 'Policy violation'
        }, content_type='application/json')
        self.assertEqual(mod.status_code, status.HTTP_200_OK)
        club.refresh_from_db()
        self.assertEqual(club.status, StudentClub.Status.SUSPENDED)
