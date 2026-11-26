import io
import json
import urllib.error
from datetime import timedelta
from unittest.mock import patch, MagicMock
from django.core import mail
from django.core.cache import cache
from django.contrib.auth.models import User
from django.contrib.auth.hashers import check_password
from django.test import TestCase, Client, override_settings
from django.utils import timezone

from core.models import Profile, PhoneOTPChallenge, EmailOTPChallenge, PasswordResetToken, EmailDeliveryLog


@override_settings(
    DEBUG=True,
    SMS_PROVIDER='ninzasms',
    SMS_TEST_MODE=False,
    NINZASMS_API_KEY='test-ninza-key',
    NINZASMS_SENDER_ID='16402',
    NINZASMS_API_URL='https://ninzasms.in.net/auth/send_sms.php',
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    DEFAULT_FROM_EMAIL='THE WOC <noreply@woc.org>',
    FRONTEND_URL='http://localhost:4317',
)
class Phase5AuthIntegrationTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = Client()
        self.user = User.objects.create_user(
            username='student5@example.com',
            first_name='Kavya',
            email='student5@example.com',
            password='OldPassword!2026'
        )
        Profile.objects.create(
            user=self.user,
            age=20,
            email_verified=False,
            roles=['student']
        )

    def _mock_response(self, payload):
        resp = MagicMock()
        resp.read.return_value = json.dumps(payload).encode('utf-8')
        resp.__enter__.return_value = resp
        resp.__exit__.return_value = False
        return resp

    def test_ninzasms_live_send_payload_and_verify(self):
        self.client.force_login(self.user)
        captured = {}

        def fake_urlopen(req, timeout=10):
            captured['url'] = req.full_url
            captured['headers'] = dict(req.header_items())
            captured['body'] = json.loads(req.data.decode('utf-8'))
            return self._mock_response({'return': True, 'message': ['SMS sent successfully']})

        with patch('urllib.request.urlopen', side_effect=fake_urlopen):
            res = self.client.post(
                '/api/phone/send-otp/',
                data={'phone': '9876543210', 'country_code': '+91', 'purpose': 'verification'},
                content_type='application/json'
            )

        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data['delivery_mode'], 'live')
        self.assertNotIn('development_otp', data)
        self.assertEqual(captured['url'], 'https://ninzasms.in.net/auth/send_sms.php')
        self.assertEqual(captured['headers'].get('Authorization'), 'Bearer test-ninza-key')
        self.assertEqual(captured['body']['sender_id'], 16402)
        self.assertEqual(captured['body']['numbers'], '9876543210')
        self.assertEqual(captured['body']['rout'], 'sms')
        sent_otp = captured['body']['variables_values']
        self.assertRegex(sent_otp, r'^\d{6}$')

        # Verify OTP updates phone_verified
        verify_res = self.client.post(
            '/api/phone/verify-otp/',
            data={'challenge_id': data['challenge_id'], 'otp': sent_otp},
            content_type='application/json'
        )
        self.assertEqual(verify_res.status_code, 200)
        self.user.profile.refresh_from_db()
        self.assertTrue(self.user.profile.phone_verified)
        self.assertEqual(self.user.profile.phone_number, '+919876543210')

    def test_ninzasms_error_handling_balance_auth_timeout(self):
        self.client.force_login(self.user)

        # 1. Insufficient balance response
        with patch('urllib.request.urlopen', return_value=self._mock_response({'return': False, 'message': 'Insufficient balance'})):
            res = self.client.post(
                '/api/phone/send-otp/',
                data={'phone': '9876543211', 'country_code': '+91', 'purpose': 'verification'},
                content_type='application/json'
            )
            self.assertEqual(res.status_code, 503)
            self.assertIn('balance', res.json()['error'].lower())

        # Clear cooldown by aging previous challenge
        PhoneOTPChallenge.objects.all().update(created_at=timezone.now() - timedelta(seconds=61))

        # 2. Invalid credentials HTTP 401
        err_401 = urllib.error.HTTPError(
            'https://ninzasms.in.net/auth/send_sms.php', 401, 'Unauthorized', {},
            io.BytesIO(b'{"message":"Invalid API key"}')
        )
        with patch('urllib.request.urlopen', side_effect=err_401):
            res2 = self.client.post(
                '/api/phone/send-otp/',
                data={'phone': '9876543211', 'country_code': '+91', 'purpose': 'verification'},
                content_type='application/json'
            )
            self.assertEqual(res2.status_code, 503)
            self.assertIn('credentials', res2.json()['error'].lower())

        PhoneOTPChallenge.objects.all().update(created_at=timezone.now() - timedelta(seconds=61))

        # 3. Timeout
        with patch('urllib.request.urlopen', side_effect=TimeoutError('timed out')):
            res3 = self.client.post(
                '/api/phone/send-otp/',
                data={'phone': '9876543211', 'country_code': '+91', 'purpose': 'verification'},
                content_type='application/json'
            )
            self.assertEqual(res3.status_code, 503)
            self.assertIn('timed out', res3.json()['error'].lower())

    def test_email_otp_send_verify_cooldown_and_attempts(self):
        self.client.force_login(self.user)
        mail.outbox.clear()

        # Send Email OTP
        res = self.client.post('/api/email/send-otp/', data={}, content_type='application/json')
        self.assertEqual(res.status_code, 200)
        challenge_id = res.json()['challenge_id']
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('THE WOC', mail.outbox[0].subject)
        self.assertTrue(EmailDeliveryLog.objects.filter(recipient='student5@example.com', template_name='email_otp', status='sent').exists())

        # Cooldown enforced
        res_cd = self.client.post('/api/email/resend-otp/', data={}, content_type='application/json')
        self.assertEqual(res_cd.status_code, 429)

        # Extract 6-digit OTP from email body
        import re
        match = re.search(r'\b(\d{6})\b', mail.outbox[0].body)
        self.assertIsNotNone(match)
        otp_code = match.group(1)

        # Wrong OTP increments attempts; 5 wrong attempts lock challenge
        wrong_otp = '000000' if otp_code != '000000' else '111111'
        for _ in range(5):
            bad = self.client.post(
                '/api/email/verify-otp/',
                data={'challenge_id': challenge_id, 'otp': wrong_otp},
                content_type='application/json'
            )
            self.assertEqual(bad.status_code, 400)
        locked = self.client.post(
            '/api/email/verify-otp/',
            data={'challenge_id': challenge_id, 'otp': otp_code},
            content_type='application/json'
        )
        self.assertEqual(locked.status_code, 400)
        self.assertIn('Maximum verification attempts', locked.json()['error'])

        # Resend invalidates previous & allows verification
        EmailOTPChallenge.objects.filter(pk=challenge_id).update(created_at=timezone.now() - timedelta(seconds=61))
        mail.outbox.clear()
        res2 = self.client.post('/api/email/resend-otp/', data={}, content_type='application/json')
        self.assertEqual(res2.status_code, 200)
        new_id = res2.json()['challenge_id']
        new_otp = re.search(r'\b(\d{6})\b', mail.outbox[0].body).group(1)

        ok = self.client.post(
            '/api/email/verify-otp/',
            data={'challenge_id': new_id, 'otp': new_otp},
            content_type='application/json'
        )
        self.assertEqual(ok.status_code, 200)
        self.user.profile.refresh_from_db()
        self.assertTrue(self.user.profile.email_verified)

    def test_password_reset_15_minute_expiry_single_use_and_no_enumeration(self):
        mail.outbox.clear()

        # Unknown email returns same generic 200 message (no enumeration)
        unk = self.client.post(
            '/api/password-reset/request/',
            data={'email': 'nobody@example.com'},
            content_type='application/json'
        )
        self.assertEqual(unk.status_code, 200)
        self.assertEqual(len(mail.outbox), 0)

        # Known email sends 15-minute reset link
        req = self.client.post(
            '/api/password-reset/request/',
            data={'email': 'student5@example.com'},
            content_type='application/json'
        )
        self.assertEqual(req.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        token_obj = PasswordResetToken.objects.get(user=self.user, used=False)
        remaining = token_obj.expires_at - timezone.now()
        self.assertLessEqual(remaining, timedelta(minutes=15, seconds=5))
        self.assertGreater(remaining, timedelta(minutes=14))

        raw_token = req.json()['development_reset_url'].split('token=')[1]

        # Confirm reset with valid password
        conf = self.client.post(
            '/api/password-reset/confirm/',
            data={'token': raw_token, 'password': 'NewStrongPass!2026', 'confirm_password': 'NewStrongPass!2026'},
            content_type='application/json'
        )
        self.assertEqual(conf.status_code, 200)

        # Single-use: second attempt fails
        reuse = self.client.post(
            '/api/password-reset/confirm/',
            data={'token': raw_token, 'password': 'AnotherPass!2026', 'confirm_password': 'AnotherPass!2026'},
            content_type='application/json'
        )
        self.assertEqual(reuse.status_code, 400)

        # Can log in with new password
        login_res = self.client.post(
            '/api/login/',
            data={'email': 'student5@example.com', 'password': 'NewStrongPass!2026'},
            content_type='application/json'
        )
        self.assertEqual(login_res.status_code, 200)
