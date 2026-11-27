import io
import tempfile
from datetime import timedelta
from PIL import Image
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.utils import timezone
from django.core.cache import cache
from core.models import Profile,Institution,CollegeMembership,CampusEvent


class EventPostTests(TestCase):
 def setUp(self):
  cache.clear()
  self.folder=tempfile.TemporaryDirectory();self.addCleanup(self.folder.cleanup)
  settings=self.settings(MEDIA_ROOT=self.folder.name);settings.enable();self.addCleanup(settings.disable)
  self.admin=User.objects.create_user(username='event-admin')
  Profile.objects.create(user=self.admin,roles=[])
  self.college=Institution.objects.create(name='Test College',city='Chennai',owner=self.admin,approval_status='approved')
  CollegeMembership.objects.create(user=self.admin,institution=self.college,role='college_admin',status='active')
  self.student=User.objects.create_user(username='event-student')
  Profile.objects.create(user=self.student,roles=['student'])
  CollegeMembership.objects.create(user=self.student,institution=self.college,role='student',status='active')
  self.other=User.objects.create_user(username='outsider')
  Profile.objects.create(user=self.other,roles=['student'])
  self.client.force_login(self.admin)
  self.data={'title':'Innovation Symposium','event_type':'symposium','description':'A college symposium with student projects and workshops.',
   'organizer_name':'Department of Computer Science','organizer_contact':'events@example.com','venue':'Main Auditorium',
   'event_date':(timezone.now()+timedelta(days=10)).isoformat(),'end_date':(timezone.now()+timedelta(days=11)).isoformat(),
   'registration_deadline':(timezone.now()+timedelta(days=9)).isoformat(),'visibility':'college','capacity':'100'}
 def poster(self):
  stream=io.BytesIO();Image.new('RGB',(30,40),'red').save(stream,format='PNG')
  return SimpleUploadedFile('poster.png',stream.getvalue(),content_type='image/png')
 def create(self,**changes):return self.client.post('/api/college/events/',{**self.data,'poster_image':self.poster(),**changes})
 def test_symposium_upload_and_student_feed(self):
  response=self.create();self.assertEqual(response.status_code,201,response.content)
  data=response.json();self.assertEqual(data['organizer_name'],self.data['organizer_name']);self.assertTrue(data['poster_url'])
  event=CampusEvent.objects.get(pk=data['id']);self.assertTrue(event.poster_image.name.endswith('.png'))
  self.client.force_login(self.student)
  response=self.client.get(data['poster_url']);self.assertEqual(response.status_code,200);response.close()
  self.assertEqual(self.client.get('/api/student/engagement/').status_code,200)
 def test_poster_privacy_and_moderation(self):
  data=self.create().json();self.client.force_login(self.other)
  self.assertEqual(self.client.get(data['poster_url']).status_code,404)
  self.client.logout();self.assertEqual(self.client.get(data['poster_url']).status_code,404)
  event=CampusEvent.objects.get(pk=data['id']);event.visibility='public';event.save()
  response=self.client.get(data['poster_url']);self.assertEqual(response.status_code,200);response.close()
  event.status='suspended';event.save();self.assertEqual(self.client.get(data['poster_url']).status_code,404)
 def test_invalid_upload_and_sports(self):
  bad=SimpleUploadedFile('fake.png',b'not an image',content_type='image/png')
  self.assertEqual(self.create(poster_image=bad).status_code,400)
  self.assertEqual(self.create(event_type='sports').status_code,201)
 def test_edit_preserves_image_and_validates_existing_dates(self):
  data=self.create().json();url=f"/api/college/events/{data['id']}/"
  self.assertEqual(self.client.patch(url,{'organizer_name':'Sports Committee'},content_type='application/json').status_code,200)
  event=CampusEvent.objects.get(pk=data['id']);self.assertTrue(event.poster_image)
  self.assertEqual(self.client.patch(url,{'end_date':(timezone.now()+timedelta(days=1)).isoformat()},content_type='application/json').status_code,400)
  self.client.force_login(self.other)
  self.assertEqual(self.client.patch(url,{'venue':'Other College'},content_type='application/json').status_code,403)

 def test_empty_optional_dates_and_replacement_upload(self):
  data=self.create(end_date='',registration_deadline='').json()
  self.assertIn('id',data)
  original=CampusEvent.objects.get(pk=data['id']).poster_image.name
  from rest_framework.test import APIClient
  client=APIClient();client.force_authenticate(self.admin)
  response=client.patch(f"/api/college/events/{data['id']}/",{'poster_image':self.poster(),'organizer_name':'College Event Team'},format='multipart')
  self.assertEqual(response.status_code,200,response.data)
  self.assertNotEqual(CampusEvent.objects.get(pk=data['id']).poster_image.name,original)
