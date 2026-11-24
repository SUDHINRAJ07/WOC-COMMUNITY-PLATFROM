from django.contrib.auth import login
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import IntegrityError, transaction
from django.middleware.csrf import get_token
from django.utils import timezone
from django.views.decorators.csrf import csrf_protect
from firebase_admin import exceptions as firebase_exceptions
from google.auth.exceptions import GoogleAuthError
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .firebase_phone import PhoneProofError, verify_phone_proof
from .models import OAuthIdentity, Profile
from .auth_services import log_auth_event
from .views import user_data


def proof_or_response(request):
    try:
        return verify_phone_proof(request.data.get('id_token')), None
    except PhoneProofError as exc:
        return None, Response({'error': str(exc)}, status=400)
    except (ImproperlyConfigured, firebase_exceptions.FirebaseError, GoogleAuthError, OSError, ValueError):
        return None, Response({'error': 'Firebase verification is unavailable. Check server configuration and try again.'}, status=503)


@csrf_protect
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def link_phone(request):
    proof, error = proof_or_response(request)
    if error is not None:
        return error
    try:
        with transaction.atomic():
            profile = Profile.objects.select_for_update().get(user=request.user)
            if Profile.objects.filter(phone_number=proof['phone']).exclude(pk=profile.pk).exists():
                return Response({'error': 'This number is already linked to another account.'}, status=409)
            identity, _ = OAuthIdentity.objects.get_or_create(
                provider_uid=proof['uid'], defaults={'provider': 'firebase_phone', 'user': request.user})
            if identity.provider != 'firebase_phone' or identity.user_id != request.user.pk:
                return Response({'error': 'This phone identity is already linked to another account.'}, status=409)
            # Retain identity history but make old numbers ineligible for login.
            for previous in OAuthIdentity.objects.filter(user=request.user, provider='firebase_phone').exclude(pk=identity.pk):
                previous.extra_data = {**previous.extra_data, 'active': False}
                previous.save(update_fields=['extra_data', 'updated_at'])
            identity.extra_data = {'active': True, 'phone': proof['phone'], 'project': settings.FIREBASE_PROJECT_ID}
            identity.save(update_fields=['extra_data', 'updated_at'])
            profile.phone_number = proof['phone']
            profile.phone_verified = True
            profile.phone_verified_at = timezone.now()
            profile.save(update_fields=['phone_number', 'phone_verified', 'phone_verified_at'])
    except Profile.DoesNotExist:
        return Response({'error': 'A WOC student profile is required.'}, status=403)
    except IntegrityError:
        return Response({'error': 'This number or identity is already linked to another account.'}, status=409)
    log_auth_event(request.user, 'firebase_phone_linked', request)
    return Response({'message': 'Mobile number verified.', 'user': user_data(request.user)})


@csrf_protect
@api_view(['POST'])
@permission_classes([AllowAny])
def phone_login(request):
    proof, error = proof_or_response(request)
    if error is not None:
        return error
    with transaction.atomic():
        # Same lock order as linking, so a concurrent number change cannot race login.
        profile = Profile.objects.select_for_update().select_related('user').filter(
            phone_number=proof['phone'], phone_verified=True).first()
        identity = OAuthIdentity.objects.filter(provider='firebase_phone', provider_uid=proof['uid']).first()
        if not profile or not identity or identity.user_id != profile.user_id or identity.extra_data.get('active') is not True or identity.extra_data.get('phone') != proof['phone']:
            return Response({'error': 'Sign up or sign in with Email/Google first, then link this mobile number in your profile.'}, status=403)
        user = profile.user
        if not user.is_active or user.is_staff or user.is_superuser:
            return Response({'error': 'Use email sign-in and the required authenticator for this account.'}, status=403)
        if request.user.is_authenticated and request.user.pk != user.pk:
            return Response({'error': 'Sign out before signing in to a different account.'}, status=403)
        login(request, user)
    log_auth_event(user, 'firebase_phone_login', request)
    return Response({'user': user_data(user), 'csrfToken': get_token(request)})


@csrf_protect
@api_view(['POST'])
@permission_classes([AllowAny])
def legacy_phone_disabled(request):
    return Response({'error': 'Use Firebase phone verification. Create your WOC account through Email/Google first.'}, status=410)
