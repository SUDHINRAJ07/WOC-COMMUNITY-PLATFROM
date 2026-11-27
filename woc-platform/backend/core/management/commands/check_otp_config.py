from django.conf import settings
from django.core.mail import get_connection
from django.core.management.base import BaseCommand, CommandError
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from urllib.parse import urlsplit


class Command(BaseCommand):
    help = 'Check Gmail SMTP and NinzaSMS settings without printing secrets or sending OTPs.'

    def add_arguments(self, parser):
        parser.add_argument('--probe-smtp', action='store_true', help='Test SMTP connection/authentication; sends no email.')

    def handle(self, *args, **options):
        missing = []
        if settings.EMAIL_BACKEND != 'django.core.mail.backends.smtp.EmailBackend':
            missing.append('EMAIL_BACKEND must use smtp.EmailBackend')
        for key in ['EMAIL_HOST', 'EMAIL_HOST_USER', 'EMAIL_HOST_PASSWORD', 'NINZASMS_API_KEY']:
            value = str(getattr(settings, key, '')).strip()
            if not value or value.startswith('your_'):
                missing.append(key)
        try:
            validate_email(settings.EMAIL_HOST_USER)
        except ValidationError:
            missing.append('EMAIL_HOST_USER must be a valid sender email')
        if not settings.EMAIL_USE_TLS or settings.EMAIL_USE_SSL or settings.EMAIL_PORT != 587:
            missing.append('Gmail STARTTLS needs port 587, EMAIL_USE_TLS=true and EMAIL_USE_SSL=false')
        if settings.SMS_PROVIDER.lower() != 'ninzasms':
            missing.append('SMS_PROVIDER=ninzasms')
        sender = str(settings.NINZASMS_SENDER_ID).strip()
        if not sender.isdigit() or int(sender) <= 0:
            missing.append('NINZASMS_SENDER_ID must be your numeric NinzaSMS account user ID')
        url = urlsplit(settings.NINZASMS_API_URL)
        if url.scheme != 'https' or not url.hostname or url.username or url.password:
            missing.append('NINZASMS_API_URL must be an HTTPS API endpoint without embedded credentials')
        if settings.SMS_TEST_MODE or settings.SMS_DEV_MODE or settings.WOC_LOCAL_SCREEN_OTP:
            missing.append('Disable SMS_TEST_MODE, SMS_DEV_MODE and WOC_LOCAL_SCREEN_OTP for live SMS')
        if not settings.EMAIL_SIGNUP_OTP_REQUIRED:
            missing.append('EMAIL_SIGNUP_OTP_REQUIRED=true')
        if missing:
            raise CommandError('OTP configuration incomplete: ' + '; '.join(missing))
        self.stdout.write(self.style.SUCCESS('Required OTP settings present. Secret values hidden. No SMS or email sent.'))
        if settings.DEBUG:
            self.stdout.write(self.style.WARNING('DEBUG=true: set DEBUG=false on EC2 production.'))
        if options['probe_smtp']:
            try:
                with get_connection() as connection:
                    connection.open()
            except Exception as exc:
                raise CommandError(f'SMTP connection/authentication failed ({type(exc).__name__}). Check EC2 outbound access and sender credentials.') from None
            self.stdout.write(self.style.SUCCESS('SMTP connection/authentication passed; inbox delivery not tested.'))
