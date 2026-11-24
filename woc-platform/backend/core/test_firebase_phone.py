import os
import time
import json
from io import StringIO
from pathlib import Path
from unittest.mock import patch, Mock

from django.contrib.auth.models import User
from django.core.exceptions import ImproperlyConfigured
from django.core.management import call_command
from django.db import IntegrityError
from django.test import TestCase, SimpleTestCase, Client, override_settings
from firebase_admin import auth

from .firebase_phone import verify_phone_proof, PhoneProofError
from .models import Profile, OAuthIdentity, PhoneOTPChallenge, Program


def claims(**changes):
    now = int(time.time())
    return {'aud': 'woc-29231', 'iss': 'https://securetoken.google.com/woc-29231',
            'sub': 'student-firebase-uid', 'phone_number': '+919876543210',
            'firebase': {'sign_in_provider': 'phone'}, 'auth_time': now,
            'iat': now, 'exp': now + 3600, **changes}


@override_settings(FIREBASE_PROJECT_ID='woc-29231', FIREBASE_PHONE_MAX_AGE=300)
class FirebaseProofTests(SimpleTestCase):
    def verify(self, data):
        with patch('core.firebase_phone.firebase_app', return_value=Mock()) as app, patch('core.firebase_phone.auth.verify_id_token', return_value=data) as verify:
            result = verify_phone_proof('signed-id-token')
            verify.assert_called_once_with('signed-id-token', app=app.return_value, check_revoked=True)
            return result

    def test_valid_phone_proof_and_revocation_check(self):
        self.assertEqual(self.verify(claims()), {'phone': '+919876543210', 'uid': 'firebase_phone:woc-29231:student-firebase-uid'})

    def test_invalid_claims_are_rejected(self):
        for changes in [dict(aud='another-project'), dict(iss='https://attacker.test'),
                        dict(firebase={'sign_in_provider': 'google.com'}), dict(firebase=None), dict(phone_number=None),
                        dict(phone_number='9876543210'), dict(sub=''), dict(exp=time.time()-1),
                        dict(iat=time.time()+60), dict(auth_time=time.time()-301),
                        dict(auth_time=time.time()+60), dict(auth_time='now')]:
            with self.subTest(changes=changes), self.assertRaises(PhoneProofError):
                self.verify(claims(**changes))

    def test_refreshing_token_does_not_refresh_phone_proof(self):
        with self.assertRaises(PhoneProofError):
            self.verify(claims(iat=int(time.time()), auth_time=int(time.time())-3600))

    def test_missing_or_oversized_token_does_not_contact_firebase(self):
        with patch('core.firebase_phone.firebase_app') as app:
            for token in [None, '', {}, 'x'*16385]:
                with self.assertRaises(PhoneProofError):
                    verify_phone_proof(token)
            app.assert_not_called()

    def test_revoked_expired_disabled_or_invalid_tokens_rejected(self):
        for error in [auth.RevokedIdTokenError('revoked'), auth.ExpiredIdTokenError('expired', cause=None),
                      auth.UserDisabledError('disabled'), auth.InvalidIdTokenError('invalid')]:
            with self.subTest(error=error), patch('core.firebase_phone.firebase_app'), patch('core.firebase_phone.auth.verify_id_token', side_effect=error), self.assertRaises(PhoneProofError):
                verify_phone_proof('invalid-token')

    def test_emulator_tokens_are_not_accepted(self):
        with patch.dict(os.environ, {'FIREBASE_AUTH_EMULATOR_HOST': 'localhost:9099'}), self.assertRaises(ImproperlyConfigured):
            verify_phone_proof('emulator-token')

    def test_admin_app_requires_expected_project(self):
        with patch.dict(os.environ, {}, clear=True), patch('core.firebase_phone.firebase_admin.get_app', return_value=Mock(project_id='other-project')), self.assertRaises(ImproperlyConfigured):
            verify_phone_proof('token')


class FirebasePhoneEndpointTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('student@example.test', 'student@example.test', 'StrongPass!2026')
        Profile.objects.create(user=self.user, age=20, email_verified=True)
        self.client.force_login(self.user)
        self.proof = {'phone': '+919876543210', 'uid': 'firebase_phone:woc-29231:uid-one'}
        self.verifier = patch('core.firebase_views.verify_phone_proof', return_value=self.proof)
        self.verify = self.verifier.start()
        self.addCleanup(self.verifier.stop)

    def post(self, path='phone/firebase-verify/', **data):
        return self.client.post('/api/'+path, {'id_token': 'firebase-token', **data}, content_type='application/json')

    def test_authenticated_link_persists_trusted_claims_and_identity(self):
        r = self.post(phone_number='+919999999999', phone_verified=False)
        self.assertEqual(r.status_code, 200)
        profile = Profile.objects.get(user=self.user)
        self.assertEqual(profile.phone_number, self.proof['phone'])
        self.assertTrue(profile.phone_verified)
        self.assertIsNotNone(profile.phone_verified_at)
        self.assertEqual(self.client.get('/api/me/').json()['user']['phone_number'], self.proof['phone'])
        self.assertTrue(OAuthIdentity.objects.get(provider_uid=self.proof['uid']).extra_data['active'])

    def test_anonymous_link_rejected_before_firebase_call(self):
        self.client.logout()
        self.assertEqual(self.post().status_code, 403)
        self.verify.assert_not_called()

    def test_csrf_required_for_link_and_login(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)
        for path in ['phone/firebase-verify/', 'auth/firebase-phone/']:
            self.assertEqual(client.post('/api/'+path, {'id_token': 'token'}).status_code, 403)
        self.verify.assert_not_called()

    def test_link_and_login_work_with_real_session_csrf_flow(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)
        token = client.get('/api/csrf/').json()['csrfToken']
        self.assertEqual(client.post('/api/phone/firebase-verify/', {'id_token':'token'}, HTTP_X_CSRFTOKEN=token).status_code, 200)
        client.logout()
        token = client.get('/api/csrf/').json()['csrfToken']
        r = client.post('/api/auth/firebase-phone/', {'id_token':'token'}, HTTP_X_CSRFTOKEN=token)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(client.session['_auth_user_id'], str(self.user.pk))

    def test_duplicate_phone_link_rejected(self):
        other = User.objects.create_user('other')
        Profile.objects.create(user=other, age=20, phone_number=self.proof['phone'], phone_verified=True)
        self.assertEqual(self.post().status_code, 409)
        self.assertFalse(OAuthIdentity.objects.exists())

    def test_identity_cannot_be_transferred_between_accounts(self):
        other = User.objects.create_user('other')
        OAuthIdentity.objects.create(user=other, provider='firebase_phone', provider_uid=self.proof['uid'])
        self.assertEqual(self.post().status_code, 409)
        self.assertFalse(Profile.objects.get(user=self.user).phone_verified)

    def test_database_collision_rolls_back_link(self):
        with patch('core.firebase_views.Profile.save', side_effect=IntegrityError('collision')):
            self.assertEqual(self.post().status_code, 409)
        self.assertFalse(OAuthIdentity.objects.exists())

    def test_link_is_idempotent(self):
        self.assertEqual(self.post().status_code, 200)
        self.assertEqual(self.post().status_code, 200)
        self.assertEqual(OAuthIdentity.objects.count(), 1)

    def test_other_user_id_in_request_cannot_redirect_link(self):
        other = User.objects.create_user('other')
        Profile.objects.create(user=other, age=20)
        self.assertEqual(self.post(user_id=other.pk).status_code, 200)
        self.assertFalse(Profile.objects.get(user=other).phone_verified)

    def test_unlinked_login_does_not_create_account(self):
        self.client.logout()
        self.assertEqual(self.post('auth/firebase-phone/').status_code, 403)
        self.assertEqual(User.objects.count(), 1)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_legacy_verified_phone_requires_firebase_link(self):
        Profile.objects.filter(user=self.user).update(phone_number=self.proof['phone'], phone_verified=True)
        self.client.logout()
        self.assertEqual(self.post('auth/firebase-phone/').status_code, 403)

    def test_linked_phone_login_uses_existing_account(self):
        self.post(); self.client.logout()
        response = self.post('auth/firebase-phone/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['user']['id'], self.user.pk)
        self.assertEqual(User.objects.count(), 1)

    def test_staff_superuser_and_inactive_accounts_cannot_use_phone_login(self):
        self.post(); self.client.logout()
        for changes in [{'is_staff':True}, {'is_superuser':True}, {'is_active':False}]:
            User.objects.filter(pk=self.user.pk).update(is_staff=False, is_superuser=False, is_active=True)
            User.objects.filter(pk=self.user.pk).update(**changes)
            self.assertEqual(self.post('auth/firebase-phone/').status_code, 403)
            self.assertNotIn('_auth_user_id', self.client.session)

    def test_number_change_invalidates_previous_phone_login(self):
        self.post()
        old = dict(self.proof)
        self.verify.return_value = {'phone': '+919876543211', 'uid': 'firebase_phone:woc-29231:uid-two'}
        self.assertEqual(self.post().status_code, 200)
        self.client.logout(); self.verify.return_value = old
        self.assertEqual(self.post('auth/firebase-phone/').status_code, 403)
        self.assertEqual(OAuthIdentity.objects.count(), 2)
        previous = OAuthIdentity.objects.get(provider_uid=old['uid'])
        self.assertFalse(previous.extra_data['active'])
        self.assertEqual(previous.extra_data['phone'], old['phone'])

    def test_invalid_firebase_proof_never_falls_back_to_sms(self):
        self.verify.side_effect = PhoneProofError('Invalid proof')
        with patch('core.views.send_sms_otp') as sms:
            self.assertEqual(self.post().status_code, 400)
            sms.assert_not_called()
        self.assertFalse(Profile.objects.get(user=self.user).phone_verified)
        self.assertEqual(PhoneOTPChallenge.objects.count(), 0)

    def test_missing_server_config_returns_actionable_error(self):
        self.verify.side_effect = ImproperlyConfigured('private detail')
        response = self.post()
        self.assertEqual(response.status_code, 503)
        self.assertNotIn('private detail', str(response.content))

    def test_different_signed_in_account_cannot_be_switched_silently(self):
        self.post()
        other = User.objects.create_user('other')
        Profile.objects.create(user=other, age=20)
        self.client.force_login(other)
        self.assertEqual(self.post('auth/firebase-phone/').status_code, 403)
        self.assertEqual(self.client.session['_auth_user_id'], str(other.pk))

    def test_email_password_login_still_uses_django_session(self):
        self.client.logout()
        response = self.client.post('/api/login/', {'email': self.user.email, 'password': 'StrongPass!2026'}, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.session['_auth_user_id'], str(self.user.pk))
        self.verify.assert_not_called()

    def test_staff_email_login_still_requires_and_accepts_real_totp(self):
        from django_otp.plugins.otp_totp.models import TOTPDevice
        from django_otp.oath import totp
        User.objects.filter(pk=self.user.pk).update(is_staff=True)
        device = TOTPDevice.objects.create(user=self.user, name='staff', confirmed=True)
        self.client.logout()
        credentials = {'email': self.user.email, 'password': 'StrongPass!2026'}
        rejected = self.client.post('/api/login/', {**credentials, 'otp': 'invalid'}, content_type='application/json')
        self.assertEqual(rejected.status_code, 403)
        self.assertNotIn('_auth_user_id', self.client.session)
        # Reset the device's deliberate failure throttle before testing a valid token.
        device.refresh_from_db(); device.throttle_reset()
        code = totp(device.bin_key, step=device.step, t0=device.t0, digits=device.digits, drift=device.drift)
        accepted = self.client.post('/api/login/', {**credentials, 'otp': str(code).zfill(device.digits)}, content_type='application/json')
        self.assertEqual(accepted.status_code, 200)
        self.assertEqual(self.client.session['otp_device_id'], device.persistent_id)
        self.verify.assert_not_called()


class ProgramCatalogPreservationTests(TestCase):
    def test_all_25_programs_remain_available_in_catalogue(self):
        source = Path(__file__).resolve().parents[2] / 'frontend' / 'data' / 'catalog.json'
        items = json.loads(source.read_text(encoding='utf-8'))
        self.assertEqual(len(items), 25)
        # Seed only Django's isolated test database, never the application database.
        call_command('seed_catalogue', stdout=StringIO())
        self.assertEqual(Program.objects.count(), 25)
        self.assertEqual(set(Program.objects.values_list('slug', flat=True)), {p['slug'] for p in items})
        self.assertEqual(self.client.get('/api/programs/').status_code, 200)
