import hashlib
import logging
import socket
from smtplib import SMTPException
from datetime import timedelta
from django.conf import settings
from django.core import signing
from django.core.mail import send_mail
from django.utils import timezone
from .models import EmailDeliveryLog, AuthAuditLog, PasswordResetToken, Notification

logger = logging.getLogger(__name__)

class MessageDeliveryError(Exception):
    pass

def get_client_ip(request):
    if not request:
        return None
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')

def get_user_agent(request):
    if not request:
        return ''
    return request.META.get('HTTP_USER_AGENT', '')[:255]

def log_auth_event(user, event_type, request=None, metadata=None):
    try:
        AuthAuditLog.objects.create(
            user=user if getattr(user, 'is_authenticated', False) or user else None,
            event_type=event_type,
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
            metadata=metadata or {}
        )
    except Exception as exc:
        logger.warning(f"Failed to record auth audit log: {exc}")

def create_in_app_notification(user, message):
    """Creates and persists an in-app notification in the database."""
    try:
        return Notification.objects.create(
            user=user,
            message=str(message)[:250],
            read=False
        )
    except Exception as exc:
        logger.warning(f"Failed to create notification: {exc}")
        return None

def safe_send_mail(subject, plain_text, recipient_email, html_message, template_name, max_retries=2):
    """
    Sends transactional email with transient error retry mechanism and persists delivery logs.
    """
    preview_backend = any(name in settings.EMAIL_BACKEND for name in ['console.EmailBackend', 'filebased.EmailBackend'])
    if not settings.DEBUG and preview_backend:
        EmailDeliveryLog.objects.create(recipient=recipient_email,subject=subject,template_name=template_name,status='failed',error_message='A live SMTP backend must be configured.')
        return False
    status = 'sent'
    error_msg = ''
    attempt = 0
    while attempt <= max_retries:
        try:
            accepted = send_mail(
                subject=subject,
                message=plain_text,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient_email],
                html_message=html_message,
                fail_silently=False
            )
            if accepted != 1:
                raise SMTPException('Email provider did not accept the message.')
            status = 'sent'
            error_msg = ''
            break
        except (socket.timeout, socket.error, ConnectionError, SMTPException) as exc:
            attempt += 1
            if attempt > max_retries:
                status = 'failed'
                error_msg = f"Failed after {attempt} attempts: {exc}"
                logger.error(f"Email retry exhausted for {recipient_email}: {exc}")
            else:
                logger.warning(f"Email delivery attempt {attempt} failed for {recipient_email}, retrying: {exc}")
        except Exception as exc:
            status = 'failed'
            error_msg = str(exc)
            logger.error(f"Email delivery error to {recipient_email}: {exc}")
            break

    try:
        EmailDeliveryLog.objects.create(
            recipient=recipient_email,
            subject=subject,
            template_name=template_name,
            status=status,
            error_message=error_msg
        )
    except Exception as exc:
        logger.warning(f"Failed to record email delivery log: {exc}")

    return status == 'sent'

def send_verification_email(user, request=None):
    """Generates a secure single-use verification token and dispatches branded email."""
    token = signing.dumps({'user': user.id, 'email': user.email, 'ts': timezone.now().isoformat()}, salt='verify-email')
    verify_url = f"{settings.FRONTEND_URL}/verify/?token={token}"
    subject = "Verify your WOC email address"
    name = user.first_name or "Student"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"></head>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #F6F4EE; margin: 0; padding: 40px 20px;">
      <div style="max-width: 560px; margin: 0 auto; background: #FFFFFF; border-radius: 8px; border: 1px solid #E8E5DF; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.04);">
        <div style="background-color: #AB0C2F; padding: 28px 32px; color: #FFFFFF;">
          <h1 style="margin: 0; font-size: 24px; font-weight: 700; letter-spacing: -0.02em;">THE WOC</h1>
          <p style="margin: 4px 0 0; font-size: 13px; opacity: 0.85; letter-spacing: 0.05em;">WIND OF CHANGE</p>
        </div>
        <div style="padding: 32px; color: #2B2A27; line-height: 1.6;">
          <h2 style="margin-top: 0; font-size: 20px; color: #1D1C1A;">Verify your student account</h2>
          <p>Hello {name},</p>
          <p>Thank you for joining <strong>THE WOC</strong> community. Please verify your email address to complete your registration and activate your student account.</p>
          <div style="margin: 32px 0;">
            <a href="{verify_url}" style="background-color: #AB0C2F; color: #FFFFFF; padding: 14px 28px; text-decoration: none; border-radius: 6px; font-weight: 600; font-size: 15px; display: inline-block;">Verify Email Address</a>
          </div>
          <p style="font-size: 13px; color: #6D695F;">This verification link will expire in 24 hours. For your security, this link can only be used once.</p>
          <p style="font-size: 13px; color: #6D695F; word-break: break-all;">If the button above does not work, copy and paste this link into your browser:<br><a href="{verify_url}" style="color: #AB0C2F;">{verify_url}</a></p>
          <hr style="border: none; border-top: 1px solid #EAE7E1; margin: 24px 0;" />
          <p style="font-size: 12px; color: #8C887E; margin: 0;">If you did not create an account on THE WOC platform, you can safely ignore this email.</p>
        </div>
      </div>
    </body>
    </html>
    """
    
    plain_text = f"""Hello {name},

Thank you for joining THE WOC community. Please verify your email address to complete your registration and activate your student account.

Verify your email: {verify_url}

This link expires in 24 hours and can only be used once.

If you did not create an account on THE WOC, please ignore this email.
"""

    if not safe_send_mail("Verify your WOC email address", plain_text, user.email, html_content, 'email_verification'):
        raise MessageDeliveryError('Your verification email could not be sent. Please try resending it shortly.')
    return verify_url

def send_welcome_email(user):
    """Sends a welcome confirmation email once email verification is completed."""
    subject = "Welcome to THE WOC!"
    name = user.first_name or "Student"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"></head>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #F6F4EE; margin: 0; padding: 40px 20px;">
      <div style="max-width: 560px; margin: 0 auto; background: #FFFFFF; border-radius: 8px; border: 1px solid #E8E5DF; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.04);">
        <div style="background-color: #AB0C2F; padding: 28px 32px; color: #FFFFFF;">
          <h1 style="margin: 0; font-size: 24px; font-weight: 700; letter-spacing: -0.02em;">THE WOC</h1>
          <p style="margin: 4px 0 0; font-size: 13px; opacity: 0.85; letter-spacing: 0.05em;">WIND OF CHANGE</p>
        </div>
        <div style="padding: 32px; color: #2B2A27; line-height: 1.6;">
          <h2 style="margin-top: 0; font-size: 20px; color: #1D1C1A;">Your email is verified!</h2>
          <p>Hello {name},</p>
          <p>Your account is now fully active. You can explore our 8 campus modules, enroll in practical courses, register for campus events, and participate in student innovation challenges.</p>
          <div style="margin: 32px 0;">
            <a href="{settings.FRONTEND_URL}/dashboard/" style="background-color: #AB0C2F; color: #FFFFFF; padding: 14px 28px; text-decoration: none; border-radius: 6px; font-weight: 600; font-size: 15px; display: inline-block;">Go to Student Dashboard</a>
          </div>
          <hr style="border: none; border-top: 1px solid #EAE7E1; margin: 24px 0;" />
          <p style="font-size: 12px; color: #8C887E; margin: 0;">BE THE CHANGE. BUILD YOUR FUTURE. — THE WOC Team</p>
        </div>
      </div>
    </body>
    </html>
    """
    
    plain_text = f"""Hello {name},

Your email address has been verified successfully. Your account on THE WOC is now active.

Access your dashboard: {settings.FRONTEND_URL}/dashboard/

BE THE CHANGE. BUILD YOUR FUTURE.
"""

    return safe_send_mail(subject, plain_text, user.email, html_content, 'welcome')

def send_password_reset_email(user, request=None):
    """Generates a secure single-use 1-hour password reset token and dispatches branded email."""
    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode('utf-8')).hexdigest()
    
    # Invalidate any existing unused tokens for this user
    PasswordResetToken.objects.filter(user=user, used=False).update(used=True)
    
    # Create new 1-hour token
    PasswordResetToken.objects.create(
        user=user,
        token_hash=token_hash,
        expires_at=timezone.now() + timedelta(hours=1)
    )
    
    reset_url = f"{settings.FRONTEND_URL}/reset-password/?token={raw_token}"
    subject = "Reset your WOC password"
    name = user.first_name or "Student"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"></head>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #F6F4EE; margin: 0; padding: 40px 20px;">
      <div style="max-width: 560px; margin: 0 auto; background: #FFFFFF; border-radius: 8px; border: 1px solid #E8E5DF; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.04);">
        <div style="background-color: #AB0C2F; padding: 28px 32px; color: #FFFFFF;">
          <h1 style="margin: 0; font-size: 24px; font-weight: 700; letter-spacing: -0.02em;">THE WOC</h1>
          <p style="margin: 4px 0 0; font-size: 13px; opacity: 0.85; letter-spacing: 0.05em;">WIND OF CHANGE</p>
        </div>
        <div style="padding: 32px; color: #2B2A27; line-height: 1.6;">
          <h2 style="margin-top: 0; font-size: 20px; color: #1D1C1A;">Password Reset Request</h2>
          <p>Hello {name},</p>
          <p>We received a request to reset the password for your <strong>THE WOC</strong> account. Click the button below to choose a new password:</p>
          <div style="margin: 32px 0;">
            <a href="{reset_url}" style="background-color: #AB0C2F; color: #FFFFFF; padding: 14px 28px; text-decoration: none; border-radius: 6px; font-weight: 600; font-size: 15px; display: inline-block;">Reset Password</a>
          </div>
          <p style="font-size: 13px; color: #6D695F;">For your security, this password reset link will expire in <strong>1 hour</strong> and can only be used once.</p>
          <p style="font-size: 13px; color: #6D695F; word-break: break-all;">If the button above does not work, copy and paste this link into your browser:<br><a href="{reset_url}" style="color: #AB0C2F;">{reset_url}</a></p>
          <hr style="border: none; border-top: 1px solid #EAE7E1; margin: 24px 0;" />
          <p style="font-size: 12px; color: #8C887E; margin: 0;">If you did not request a password reset, you can safely ignore this email. Your current password remains unchanged.</p>
        </div>
      </div>
    </body>
    </html>
    """
    
    plain_text = f"""Hello {name},

We received a request to reset the password for your THE WOC account.

Reset your password: {reset_url}

This link will expire in 1 hour and can only be used once.

If you did not request a password reset, you can safely ignore this email.
"""

    if not safe_send_mail(subject, plain_text, user.email, html_content, 'password_reset'):
        raise MessageDeliveryError('The reset email could not be sent. Please try again shortly.')
    return reset_url

def send_registration_confirmation_email(user, program, record):
    """Sends a branded confirmation email when a student registers for a program."""
    name = user.first_name or "Student"
    subject = f"Registration Confirmed: {program.title} | THE WOC"
    dashboard_url = f"{settings.FRONTEND_URL}/dashboard/"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"></head>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #F6F4EE; margin: 0; padding: 40px 20px;">
      <div style="max-width: 580px; margin: 0 auto; background: #FFFFFF; border-radius: 8px; border: 1px solid #E8E5DF; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.04);">
        <div style="background-color: #AB0C2F; padding: 28px 32px; color: #FFFFFF;">
          <h1 style="margin: 0; font-size: 24px; font-weight: 700; letter-spacing: -0.02em;">THE WOC</h1>
          <p style="margin: 4px 0 0; font-size: 13px; opacity: 0.85; letter-spacing: 0.05em;">REGISTRATION CONFIRMATION</p>
        </div>
        <div style="padding: 32px; color: #2B2A27; line-height: 1.6;">
          <h2 style="margin-top: 0; font-size: 20px; color: #1D1C1A;">You are registered, {name}!</h2>
          <p>We received your registration for <strong>{program.title}</strong>. Your application details have been saved in your WOC student profile.</p>
          <div style="background-color: #F9F8F5; border: 1px solid #EAE7E1; border-radius: 6px; padding: 18px 22px; margin: 24px 0;">
            <p style="margin: 0 0 8px; font-size: 14px;"><strong>Program:</strong> {program.title}</p>
            <p style="margin: 0 0 8px; font-size: 14px;"><strong>Module:</strong> {program.module.capitalize()} ({program.category})</p>
            <p style="margin: 0 0 8px; font-size: 14px;"><strong>Location / Mode:</strong> {program.location}</p>
            <p style="margin: 0 0 8px; font-size: 14px;"><strong>Status:</strong> {record.status.replace('_', ' ').capitalize()}</p>
            <p style="margin: 0; font-size: 12px; color: #8C887E;">Reference ID: {record.id}</p>
          </div>
          <div style="margin: 28px 0;">
            <a href="{dashboard_url}" style="background-color: #AB0C2F; color: #FFFFFF; padding: 14px 28px; text-decoration: none; border-radius: 6px; font-weight: 600; font-size: 15px; display: inline-block;">View in My Dashboard</a>
          </div>
          <p style="font-size: 13px; color: #6D695F;">You can review your registration status, learning progress, and certificates anytime through your dashboard.</p>
          <hr style="border: none; border-top: 1px solid #EAE7E1; margin: 24px 0;" />
          <p style="font-size: 12px; color: #8C887E; margin: 0;">BE THE CHANGE. BUILD YOUR FUTURE. — THE WOC Team</p>
        </div>
      </div>
    </body>
    </html>
    """
    
    plain_text = f"""Hello {name},

Your registration for {program.title} has been confirmed.

Module: {program.module.capitalize()} ({program.category})
Status: {record.status}
Reference ID: {record.id}

View your dashboard: {dashboard_url}

BE THE CHANGE. BUILD YOUR FUTURE.
"""

    return safe_send_mail(subject, plain_text, user.email, html_content, 'registration_confirmation')

def send_status_update_email(user, program, status):
    """Sends a branded email notification when a student application or record status is updated."""
    name = user.first_name or "Student"
    status_label = status.replace('_', ' ').capitalize()
    subject = f"Application Update: {program.title} is {status_label} | THE WOC"
    dashboard_url = f"{settings.FRONTEND_URL}/dashboard/"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"></head>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #F6F4EE; margin: 0; padding: 40px 20px;">
      <div style="max-width: 580px; margin: 0 auto; background: #FFFFFF; border-radius: 8px; border: 1px solid #E8E5DF; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.04);">
        <div style="background-color: #AB0C2F; padding: 28px 32px; color: #FFFFFF;">
          <h1 style="margin: 0; font-size: 24px; font-weight: 700; letter-spacing: -0.02em;">THE WOC</h1>
          <p style="margin: 4px 0 0; font-size: 13px; opacity: 0.85; letter-spacing: 0.05em;">APPLICATION STATUS UPDATE</p>
        </div>
        <div style="padding: 32px; color: #2B2A27; line-height: 1.6;">
          <h2 style="margin-top: 0; font-size: 20px; color: #1D1C1A;">Hello {name},</h2>
          <p>The status of your registration for <strong>{program.title}</strong> has been updated to:</p>
          <div style="background-color: #F9F8F5; border-left: 4px solid #AB0C2F; border-radius: 4px; padding: 14px 18px; margin: 20px 0;">
            <span style="font-size: 18px; font-weight: 700; color: #AB0C2F;">{status_label}</span>
          </div>
          <p>Please check your student dashboard for further details or next steps regarding this program.</p>
          <div style="margin: 28px 0;">
            <a href="{dashboard_url}" style="background-color: #AB0C2F; color: #FFFFFF; padding: 14px 28px; text-decoration: none; border-radius: 6px; font-weight: 600; font-size: 15px; display: inline-block;">Check Dashboard</a>
          </div>
          <hr style="border: none; border-top: 1px solid #EAE7E1; margin: 24px 0;" />
          <p style="font-size: 12px; color: #8C887E; margin: 0;">BE THE CHANGE. BUILD YOUR FUTURE. — THE WOC Team</p>
        </div>
      </div>
    </body>
    </html>
    """
    
    plain_text = f"""Hello {name},

The status of your registration for {program.title} has been updated to: {status_label}.

View your dashboard: {dashboard_url}

BE THE CHANGE. BUILD YOUR FUTURE.
"""

    return safe_send_mail(subject, plain_text, user.email, html_content, 'status_update')

import re
import secrets
import json
import urllib.request
import urllib.parse
from django.contrib.auth.hashers import make_password, check_password

def normalize_phone_number(raw_phone, default_country='+91'):
    """Normalizes phone number to E.164 format with +91 default support."""
    if not raw_phone:
        raise ValueError('Mobile number is required.')
    cleaned = re.sub(r'[\s\-\(\)]', '', str(raw_phone).strip())
    if cleaned.startswith('00'):
        cleaned = '+' + cleaned[2:]
    if cleaned.startswith('+'):
        if not re.match(r'^\+[1-9]\d{7,14}$', cleaned):
            raise ValueError('Invalid international mobile number format.')
        return cleaned
    # If 10 digits without country prefix, apply default country code
    if re.match(r'^[6-9]\d{9}$', cleaned):
        country_code = default_country if default_country.startswith('+') else f"+{default_country}"
        return f"{country_code}{cleaned}"
    if re.match(r'^\d{8,14}$', cleaned):
        country_code = default_country if default_country.startswith('+') else f"+{default_country}"
        return f"{country_code}{cleaned}"
    raise ValueError('Enter a valid 10-digit mobile number.')

def mask_phone_number(phone):
    """Masks a phone number for display e.g. +91 98****3210."""
    p = str(phone).strip()
    if len(p) <= 6:
        return p
    return f"{p[:5]}****{p[-3:]}"

def generate_secure_otp():
    """Generates a cryptographically secure 6-digit random OTP."""
    return f"{secrets.SystemRandom().randint(100000, 999999)}"

def send_sms_otp(phone_number, otp):
    """Return a test preview or require confirmed provider acceptance; never fake live delivery."""
    provider = getattr(settings, 'SMS_PROVIDER', 'msg91').lower()
    preview = settings.DEBUG and getattr(settings, 'SMS_DEV_MODE', False) and provider == 'test_mode'
    if preview:
        return {'mode': 'test'}
    if provider == 'msg91':
        key = getattr(settings, 'MSG91_AUTH_KEY', '')
        template = getattr(settings, 'MSG91_TEMPLATE_ID', '')
        if not key or not template:
            raise MessageDeliveryError('Mobile OTP is not available yet. Please use email or contact WOC.')
        query = urllib.parse.urlencode({'template_id': template, 'mobile': phone_number.lstrip('+'), 'otp': otp, 'otp_length': 6, 'otp_expiry': 5})
        req = urllib.request.Request('https://control.msg91.com/api/v5/otp?' + query, data=b'{}', method='POST')
        req.add_header('authkey', key)
        req.add_header('Content-Type', 'application/json')
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                result = json.loads(response.read().decode('utf-8'))
            if result.get('type') != 'success':
                raise MessageDeliveryError('SMS could not be sent. Check the number and try again shortly.')
            return {'mode': 'live'}
        except MessageDeliveryError:
            raise
        except Exception:
            logger.warning('MSG91 delivery request failed for %s', mask_phone_number(phone_number))
            raise MessageDeliveryError('SMS could not be sent. Please try again shortly.')
    if provider == 'twilio':
        import base64
        sid = getattr(settings, 'TWILIO_ACCOUNT_SID', '')
        token = getattr(settings, 'TWILIO_AUTH_TOKEN', '')
        sender = getattr(settings, 'TWILIO_PHONE_NUMBER', '')
        if not sid or not token or not sender:
            raise MessageDeliveryError('Mobile OTP is not available yet. Please use email or contact WOC.')
        body = urllib.parse.urlencode({'To': phone_number, 'From': sender, 'Body': f'Your WOC verification code is {otp}. Valid for 5 minutes.'}).encode()
        req = urllib.request.Request(f'https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json', data=body, method='POST')
        req.add_header('Authorization', 'Basic ' + base64.b64encode(f'{sid}:{token}'.encode()).decode())
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                result = json.loads(response.read().decode())
            if result.get('status') not in ['queued', 'accepted', 'sending', 'sent', 'delivered']:
                raise ValueError('Provider rejected SMS')
            return {'mode': 'live'}
        except Exception:
            raise MessageDeliveryError('SMS could not be sent. Please try again shortly.')
    raise MessageDeliveryError('Mobile OTP is not available yet. Please use email or contact WOC.')


class AccountLinkingRequiredError(Exception):
    def __init__(self, message, email, sub):
        super().__init__(message)
        self.email = email
        self.sub = sub

def build_google_auth_url(request):
    """Builds the official Google OAuth 2.0 authorization URL."""
    client_id = getattr(settings, 'GOOGLE_CLIENT_ID', '')
    if not client_id:
        raise ValueError("Google Client ID is not configured on the server.")
    redirect_uri = getattr(settings, 'GOOGLE_REDIRECT_URI', f"{settings.FRONTEND_URL}/verify/?google_callback=true")
    state = signing.dumps({'nonce': secrets.token_urlsafe(24)}, salt='google-oauth-state')
    request.session['google_oauth_state'] = state
    params = {
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'response_type': 'code',
        'scope': 'openid email profile',
        'access_type': 'online',
        'state': state,
        'prompt': 'select_account'
    }
    return f"https://accounts.google.com/o/oauth2/v2/auth?{urllib.parse.urlencode(params)}"

def verify_google_id_token(id_token_str):
    """Verifies a Google ID token with Google's public tokeninfo endpoint."""
    if not id_token_str or not isinstance(id_token_str, str):
        raise ValueError("ID token is required.")
    
    # Safe Mocked OAuth for tests and local development testing
    if getattr(settings, 'DEBUG', False) and getattr(settings, 'AUTH_TEST_MODE', False) and id_token_str.startswith('mock-google-token:'):
        parts = id_token_str.split(':')
        mock_email = parts[1] if len(parts) > 1 else 'mockstudent@gmail.com'
        mock_sub = parts[2] if len(parts) > 2 else 'google-mock-sub-12345'
        mock_name = parts[3] if len(parts) > 3 else 'Mock Google User'
        return {
            'sub': mock_sub,
            'email': mock_email.lower(),
            'name': mock_name,
            'email_verified': True,
            'picture': ''
        }

    try:
        url = f"https://oauth2.googleapis.com/tokeninfo?id_token={urllib.parse.quote(id_token_str)}"
        req = urllib.request.Request(url, method='GET')
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode('utf-8'))
    except Exception as exc:
        logger.error(f"Google ID token verification failed: {exc}")
        raise ValueError("Invalid or expired Google ID token.")

    if data.get('error') or data.get('error_description'):
        raise ValueError(data.get('error_description', 'Invalid Google token.'))
    
    iss = data.get('iss')
    if iss not in ['accounts.google.com', 'https://accounts.google.com']:
        raise ValueError("Invalid token issuer.")
    
    expected_aud = getattr(settings, 'GOOGLE_CLIENT_ID', '')
    if not expected_aud or data.get('aud') != expected_aud:
        raise ValueError("Token audience does not match this application.")
    
    email = data.get('email', '').strip().lower()
    email_verified = data.get('email_verified') in (True, 'true', 'True', 1)
    if not email or not email_verified:
        raise ValueError("Google account email is not verified.")
    
    sub = data.get('sub')
    if not sub:
        raise ValueError("Missing subject identifier in Google token.")
    
    return {
        'sub': sub,
        'email': email,
        'name': data.get('name', ''),
        'picture': data.get('picture', ''),
        'email_verified': True
    }

def exchange_google_code(code, redirect_uri=None):
    """Exchanges an authorization code for Google tokens and verifies the ID token."""
    client_id = getattr(settings, 'GOOGLE_CLIENT_ID', '')
    client_secret = getattr(settings, 'GOOGLE_CLIENT_SECRET', '')
    if not client_id or not client_secret:
        raise ValueError("Google OAuth credentials are not fully configured.")
    
    target_redirect = redirect_uri or getattr(settings, 'GOOGLE_REDIRECT_URI', f"{settings.FRONTEND_URL}/verify/?google_callback=true")
    token_url = "https://oauth2.googleapis.com/token"
    data = urllib.parse.urlencode({
        'code': code,
        'client_id': client_id,
        'client_secret': client_secret,
        'redirect_uri': target_redirect,
        'grant_type': 'authorization_code'
    }).encode('utf-8')
    
    try:
        req = urllib.request.Request(token_url, data=data, method='POST')
        req.add_header('Content-Type', 'application/x-www-form-urlencoded')
        with urllib.request.urlopen(req, timeout=10) as resp:
            resp_data = json.loads(resp.read().decode('utf-8'))
    except Exception as exc:
        logger.error(f"Google code exchange failed: {exc}")
        raise ValueError("Failed to exchange Google authorization code.")
    
    id_token_str = resp_data.get('id_token')
    if not id_token_str:
        raise ValueError("Google did not return an ID token.")
    
    return verify_google_id_token(id_token_str)

def handle_google_user(google_info, link_password=None, current_user=None):
    """
    Safely creates or links a user from verified Google OAuth credentials.
    CRITICAL: Does NOT automatically link to an existing user based solely on email
    unless the user proves ownership via password or active session.
    """
    from django.contrib.auth.models import User
    from django.db import transaction
    from .models import OAuthIdentity, Profile

    sub = str(google_info['sub']).strip()
    email = str(google_info['email']).strip().lower()
    name = str(google_info.get('name', '')).strip() or 'Google Student'

    # 1. Existing OAuth identity mapping found
    existing_identity = OAuthIdentity.objects.select_related('user__profile').filter(provider='google', provider_uid=sub).first()
    if existing_identity:
        return existing_identity.user, 'logged_in'

    # 2. Check if a local WOC user with this email already exists
    existing_user = User.objects.filter(email=email).first()
    if existing_user:
        # If user is already authenticated as this user, link safely
        if current_user and current_user.is_authenticated and current_user.id == existing_user.id:
            OAuthIdentity.objects.create(
                user=existing_user,
                provider='google',
                provider_uid=sub,
                email=email,
                extra_data=google_info
            )
            return existing_user, 'linked'

        # If link password was provided, verify ownership
        if link_password:
            if existing_user.check_password(link_password):
                OAuthIdentity.objects.create(
                    user=existing_user,
                    provider='google',
                    provider_uid=sub,
                    email=email,
                    extra_data=google_info
                )
                return existing_user, 'linked'
            else:
                raise ValueError("Incorrect WOC password. Account linking rejected.")

        # Require explicit password verification to prevent insecure account takeover
        raise AccountLinkingRequiredError(
            "An account with this email already exists. Enter your WOC password to link your Google account.",
            email=email,
            sub=sub
        )

    # 3. New user signup via Google
    with transaction.atomic():
        user = User.objects.create_user(username=email, email=email, first_name=name)
        user.set_unusable_password()
        user.save()
        Profile.objects.create(
            user=user,
            age=18,
            guardian_consent=True,
            institution='',
            roles=['student'],
            auth_provider='google',
            email_verified=True,
            email_verified_at=timezone.now()
        )
        OAuthIdentity.objects.create(
            user=user,
            provider='google',
            provider_uid=sub,
            email=email,
            extra_data=google_info
        )
        send_welcome_email(user)
        return user, 'created'


