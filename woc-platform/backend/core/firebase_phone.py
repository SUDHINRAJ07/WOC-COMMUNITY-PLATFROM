"""Firebase proves phone ownership; Django remains the WOC session authority."""
import os
import re
import threading
import time

import firebase_admin
from firebase_admin import auth
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

_lock = threading.Lock()


class PhoneProofError(ValueError):
    pass


def firebase_app():
    # Never accept unsigned Auth emulator tokens in the real API, including DEBUG.
    if os.environ.get('FIREBASE_AUTH_EMULATOR_HOST'):
        raise ImproperlyConfigured('Firebase Auth emulator is not supported by this API.')
    project = settings.FIREBASE_PROJECT_ID
    if not project:
        raise ImproperlyConfigured('Configure FIREBASE_PROJECT_ID and server application credentials.')
    with _lock:
        try:
            app = firebase_admin.get_app('woc-phone')
        except ValueError:
            app = firebase_admin.initialize_app(options={'projectId': project}, name='woc-phone')
    if app.project_id != project:
        raise ImproperlyConfigured('Firebase project configuration changed. Restart the backend.')
    return app


def verify_phone_proof(token):
    if not isinstance(token, str) or not token or len(token) > 16384:
        raise PhoneProofError('A Firebase ID token is required.')
    app = firebase_app()
    try:
        claims = auth.verify_id_token(token, app=app, check_revoked=True)
    except (auth.InvalidIdTokenError, auth.UserDisabledError, ValueError) as exc:
        raise PhoneProofError('Phone verification expired or was rejected. Request a new OTP.') from exc
    project = settings.FIREBASE_PROJECT_ID
    now = time.time()
    if claims.get('aud') != project or claims.get('iss') != f'https://securetoken.google.com/{project}':
        raise PhoneProofError('Phone identity belongs to a different Firebase project.')
    provider = claims.get('firebase')
    if not isinstance(provider, dict) or provider.get('sign_in_provider') != 'phone':
        raise PhoneProofError('Verify your mobile number with a phone OTP.')
    phone, uid = claims.get('phone_number'), claims.get('sub')
    if not isinstance(phone, str) or not re.fullmatch(r'\+[1-9]\d{7,14}', phone):
        raise PhoneProofError('A verified phone identity is required.')
    if not isinstance(uid, str) or not 1 <= len(uid) <= 128:
        raise PhoneProofError('Invalid phone identity.')
    # Refreshing an old ID token must not authorize linking/changing a phone.
    for field in ('auth_time', 'iat', 'exp'):
        if type(claims.get(field)) not in (int, float):
            raise PhoneProofError('Invalid phone verification time.')
    if claims['exp'] <= now or claims['iat'] > now + 30 or not -30 <= now - claims['auth_time'] <= settings.FIREBASE_PHONE_MAX_AGE:
        raise PhoneProofError('Fresh phone verification is required. Request a new OTP.')
    return {'phone': phone, 'uid': f'firebase_phone:{project}:{uid}'}
