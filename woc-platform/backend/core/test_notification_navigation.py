from datetime import timedelta
from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from core.models import Profile,Notification,Institution,CampusEvent


class NotificationNavigationTests(TestCase):
 def setUp(self):
  self.user=User.objects.create_user(username='notification-student')
  Profile.objects.create(user=self.user,roles=['student'])
  self.other=User.objects.create_user(username='other-student')
  Profile.objects.create(user=self.other,roles=['student'])
  self.client.force_login(self.user)
 def test_mark_only_owned_displayed_ids(self):
  visible=Notification.objects.create(user=self.user,message='Profile update')
  hidden=Notification.objects.create(user=self.user,message='Older update')
  other=Notification.objects.create(user=self.other,message='Private update')
  result=self.client.patch('/api/notifications/',{'ids':[visible.pk,other.pk]},content_type='application/json')
  self.assertEqual(result.status_code,200)
  visible.refresh_from_db();hidden.refresh_from_db();other.refresh_from_db()
  self.assertTrue(visible.read);self.assertFalse(hidden.read);self.assertFalse(other.read)
  self.assertEqual(result.json()['unread_count'],1)
 def test_links_and_unsafe_external_target_fallback(self):
  college=Institution.objects.create(name='Test College',city='Chennai',approval_status='approved')
  event=CampusEvent.objects.create(institution=college,title='Student Hackathon',description='Test event',event_type='technical',venue='Hall',visibility='public',event_date=timezone.now()+timedelta(days=1))
  Notification.objects.create(user=self.user,message="Test College: Registration confirmed for 'Student Hackathon'.")
  Notification.objects.create(user=self.user,message='Mobile verified',target_url='https://evil.example/')
  Notification.objects.create(user=self.other,message='Another account')
  response=self.client.get('/api/notifications/').json()
  self.assertEqual(len(response['results']),2)
  self.assertIn(f'/dashboard/?tab=engagement&event={event.pk}',[n['target_url'] for n in response['results']])
  self.assertTrue(all(n['target_url'].startswith('/dashboard/') for n in response['results']))
  response=self.client.get('/api/student/engagement/',{'event':str(event.pk)})
  self.assertEqual(response.status_code,200)
  self.assertEqual(response.json()['upcoming_events'][0]['id'],str(event.pk))
 def test_read_payload_and_event_target_are_scoped(self):
  self.assertEqual(self.client.patch('/api/notifications/',{'ids':['bad']},content_type='application/json').status_code,400)
  self.assertEqual(self.client.get('/api/student/engagement/',{'event':'not-a-uuid'}).status_code,200)
  college=Institution.objects.create(name='Other College',city='Chennai',approval_status='approved')
  event=CampusEvent.objects.create(institution=college,title='Private event',event_type='sports',description='Private',venue='Hall',visibility='college',event_date=timezone.now()+timedelta(days=1))
  result=self.client.get('/api/student/engagement/',{'event':str(event.pk)}).json()
  self.assertNotIn(str(event.pk),[n['id'] for n in result['upcoming_events']])
