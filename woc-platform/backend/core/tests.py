from django.test import TestCase,Client
from django.contrib.auth.models import User
from .models import Profile,Program,Record,Certificate,AuditLog
class WorkflowTests(TestCase):
 def setUp(self):
  self.user=User.objects.create_user('learner@example.test','learner@example.test','LongPass!2026',first_name='Learner')
  Profile.objects.create(user=self.user,age=20,email_verified=True,roles=['student'])
  self.course=Program.objects.create(slug='sample-course',module='academy',title='Sample Course',description='Sample',category='Learning')
  self.client.force_login(self.user)
 def test_registration_duplicate_is_rejected(self):
  self.assertEqual(self.client.post('/api/records/',{'program':self.course.slug,'data':{}},content_type='application/json').status_code,201)
  self.assertEqual(self.client.post('/api/records/',{'program':self.course.slug,'data':{}},content_type='application/json').status_code,400)
 def test_student_cannot_access_admin(self):self.assertEqual(self.client.get('/api/admin/records/').status_code,403)
 def test_records_are_private(self):
  other=User.objects.create_user('other','other@example.test','AnotherPass!2026')
  Record.objects.create(user=other,program=self.course)
  self.assertEqual(self.client.get('/api/records/').json()['results'],[])
 def test_underage_registration_needs_permission(self):
  self.client.logout()
  response=self.client.post('/api/register/',{'name':'School student','email':'school@example.test','password':'LongPass!2026','age':16,'terms':True},content_type='application/json')
  self.assertEqual(response.status_code,400)
 def test_sports_team_size_validated(self):
  p=Program.objects.create(slug='cricket',module='sports',title='Cricket',description='Sample',category='Cricket',details={'min_players':11,'max_players':15})
  response=self.client.post('/api/records/',{'program':p.slug,'data':{'team':'Team','players':'Only one'}},content_type='application/json')
  self.assertEqual(response.status_code,400)
 def test_learning_requires_lessons_before_assessment(self):
  r=Record.objects.create(user=self.user,program=self.course,status='enrolled')
  response=self.client.post(f'/api/learning/{r.id}/',{'action':'assessment','answers':[1,0,2],'project':'A project with a detailed description.'},content_type='application/json')
  self.assertEqual(response.status_code,400)
 def test_full_learning_and_staff_issuance(self):
  r=Record.objects.create(user=self.user,program=self.course,status='enrolled')
  for i in range(3):self.assertEqual(self.client.post(f'/api/learning/{r.id}/',{'action':'lesson','lesson':i},content_type='application/json').status_code,200)
  self.client.post(f'/api/learning/{r.id}/',{'action':'assessment','answers':[1,0,2],'project':'I built a focused prototype and tested it with students.'},content_type='application/json')
  r.refresh_from_db();self.assertEqual(r.status,'awaiting_review');self.assertFalse(Certificate.objects.exists())
  self.user.is_staff=True;self.user.save()
  self.assertEqual(self.client.patch('/api/admin/records/',{'id':str(r.id),'status':'completed'},content_type='application/json').status_code,200)
  self.assertTrue(Certificate.objects.filter(record=r).exists());self.assertTrue(AuditLog.objects.exists())
 def test_anonymous_login_requires_csrf(self):
  client=Client(enforce_csrf_checks=True)
  response=client.post('/api/login/',{'email':self.user.email,'password':'LongPass!2026'},content_type='application/json')
  self.assertEqual(response.status_code,403)
