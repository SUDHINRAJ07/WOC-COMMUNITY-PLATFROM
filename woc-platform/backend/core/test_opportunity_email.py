import tempfile
from datetime import timedelta
from unittest.mock import patch
from django.contrib.auth.models import User
from django.core import mail
from django.core.files.base import ContentFile
from django.test import TestCase,override_settings
from django.utils import timezone
from django.core.cache import cache
from core.models import Profile,Company,Opportunity,OpportunityApplicationLog


@override_settings(DEBUG=True,EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',DEFAULT_FROM_EMAIL='WOC <sender@example.com>')
class OpportunityEmailTests(TestCase):
 def setUp(self):
  cache.clear()
  self.files=tempfile.TemporaryDirectory();self.addCleanup(self.files.cleanup)
  settings=self.settings(MEDIA_ROOT=self.files.name);settings.enable();self.addCleanup(settings.disable)
  self.user=User.objects.create_user(username='applicant',email='student@example.com',first_name='Student Name')
  self.profile=Profile.objects.create(user=self.user,roles=['student'],email_verified=True,institution='Test College',skills=['Python'])
  self.profile.resume_file.save('resume.pdf',ContentFile(b'%PDF-1.4\nTest resume'),save=True)
  owner=User.objects.create_user(username='employer',email='hr@example.com')
  Profile.objects.create(user=owner,roles=[])
  self.company=Company.objects.create(name='Test Employer',website='https://example.com',contact_email='hr@example.com',created_by=owner,approval_status='approved')
  self.opp=Opportunity.objects.create(company=self.company,title='Developer',description='A developer opportunity for testing the application relay.',opportunity_type='job',status='approved',recruitment_email='careers@example.com')
  self.url=f'/api/student/opportunities/{self.opp.pk}/apply/'
  self.client.force_login(self.user)
 def apply(self,**payload):return self.client.post(self.url,{'consent':True,**payload},content_type='application/json')
 def test_preview_and_send_attached_resume_once(self):
  preview=self.client.get(self.url).json()
  self.assertEqual(preview['student']['email'],self.user.email)
  self.assertNotIn('address',preview['student'])
  response=self.apply()
  self.assertEqual(response.status_code,200)
  self.assertEqual(len(mail.outbox),1)
  message=mail.outbox[0]
  self.assertEqual(message.to,['careers@example.com'])
  self.assertEqual(message.reply_to,[self.user.email])
  self.assertEqual(message.attachments[0].filename,'Resume.pdf')
  self.assertIn(b'%PDF-',message.attachments[0].content)
  self.assertIn('Test College',message.body)
  log=OpportunityApplicationLog.objects.get(user=self.user,opportunity=self.opp)
  self.assertEqual(log.status,'applied');self.assertEqual(log.email_delivery_state,'sent')
  self.assertEqual(log.external_click_count,0)
  self.assertEqual(self.apply().status_code,409)
  self.assertEqual(len(mail.outbox),1)
 def test_consent_and_recipient_tampering_rejected(self):
  self.assertEqual(self.apply(consent=False).status_code,400)
  self.assertEqual(self.apply(recipient='attacker@example.com').status_code,400)
  self.assertFalse(OpportunityApplicationLog.objects.exists())
 def test_verified_email_and_pdf_required(self):
  self.profile.email_verified=False;self.profile.save()
  self.assertEqual(self.apply().status_code,403)
  self.profile.email_verified=True;self.profile.resume_file='';self.profile.save()
  self.assertEqual(self.apply().status_code,400)
  self.profile.resume_file.save('bad.pdf',ContentFile(b'not a PDF'),save=True)
  self.assertEqual(self.apply().status_code,400)
 def test_sample_website_only_and_expired_rejected(self):
  self.company.contact_email='company1@woc-demo.test';self.company.save()
  self.assertFalse(self.client.get(self.url).json()['can_send'])
  self.assertEqual(self.apply().status_code,400)
  self.company.contact_email='hr@example.com';self.company.save()
  self.opp.recruitment_email='';self.opp.careers_url='https://example.com/careers';self.opp.save()
  self.assertEqual(self.apply().status_code,400)
  self.opp.deadline=timezone.localdate()-timedelta(days=1);self.opp.save()
  self.assertEqual(self.apply().status_code,404)
 def test_unauthorized_and_suspended_rejected(self):
  self.client.logout();self.assertEqual(self.client.get(self.url).status_code,403)
  self.client.force_login(self.company.created_by);self.assertEqual(self.client.get(self.url).status_code,403)
  self.client.force_login(self.user)
  self.company.approval_status='suspended';self.company.save()
  self.assertEqual(self.apply().status_code,404)
 def test_delivery_uncertainty_never_claims_submission(self):
  with patch('django.core.mail.message.EmailMessage.send',side_effect=TimeoutError):
   self.assertEqual(self.apply().status_code,503)
  log=OpportunityApplicationLog.objects.get(user=self.user,opportunity=self.opp)
  self.assertIsNone(log.email_submitted_at)
  self.assertNotEqual(log.status,'applied')
  self.assertEqual(self.apply().status_code,409)

 def test_production_preview_mail_backend_is_rejected(self):
  with self.settings(DEBUG=False):
   self.assertEqual(self.apply().status_code,503)
  self.assertFalse(OpportunityApplicationLog.objects.exists())
