# WOC email and mobile OTP on EC2

The Django process must load the backend environment file or equivalent service environment. Editing the frontend environment does not configure message delivery. Keep existing database settings, Django secret key and organization data unchanged.

## Private backend environment

Set these entries in the existing `backend/.env` on EC2 (not in Git):

```dotenv
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=true
EMAIL_USE_SSL=false
EMAIL_TIMEOUT=20
EMAIL_HOST_USER=your-sender@gmail.com
EMAIL_HOST_PASSWORD=your-private-google-app-password
DEFAULT_FROM_EMAIL="WOC - Wind of Change <your-sender@gmail.com>"
EMAIL_SIGNUP_OTP_REQUIRED=true
EMAIL_VERIFICATION_REQUIRED=false

SMS_PROVIDER=ninzasms
SMS_TEST_MODE=false
SMS_DEV_MODE=false
WOC_LOCAL_SCREEN_OTP=false
NINZASMS_API_KEY=your-private-ninzasms-api-key
NINZASMS_SENDER_ID=your-numeric-ninzasms-account-user-id
NINZASMS_API_URL=https://ninzasms.in.net/auth/send_sms.php
```

Use the sender email and corresponding App Password already configured privately; do not use the regular Gmail account password. NinzaSMS documents `sender_id` as its numeric account user ID; confirm this in your account. It is not an arbitrary brand name. Ensure the account's SMS route and credit balance are active.

Keep `DEBUG=false` and existing secure production settings. `EMAIL_VERIFICATION_REQUIRED=false` preserves existing account access; new signups individually require email verification when `EMAIL_SIGNUP_OTP_REQUIRED=true`. Do not re-enable screen-visible or simulated OTPs to work around live delivery failures.

## Check without sending messages

From the EC2 backend directory with the existing virtual environment activated:

```bash
python manage.py check_otp_config
python manage.py check_otp_config --probe-smtp
```

The first command checks settings without showing credentials. The second authenticates to SMTP without sending an email. A successful connection is not evidence of inbox delivery or SMS delivery. If Django is managed by systemd/Docker, run checks with the same environment and interpreter used by that service. An already exported service variable can override a `.env` entry because python-dotenv does not overwrite process variables by default.

Allow outbound HTTPS TCP 443 for NinzaSMS and outbound TCP 587 for Gmail STARTTLS in EC2 security group/firewall/network rules. No inbound SMTP rule is needed. Do not disable certificate verification. EC2's default port-25 restriction is avoided by using 587.

Restart the existing backend application service after changing its environment. Use its actual systemd unit, process supervisor or Docker service; do not start another development server or reset the database. No migration is required for these OTP fixes.

## Delivery confirmation

1. Use an email address you control for a new signup. Confirm the email arrives and verify the code. Incorrect/expired/reused codes must fail; the account is verified only after a matching valid code.
2. Sign out and log back in using the same email/password: no repeat signup OTP is needed.
3. Use a mobile number you control. Request one SMS, confirm receipt, then complete OTP verification. NinzaSMS API acceptance alone does not prove handset delivery.
4. If delivery fails, inspect the backend error and provider delivery report. NinzaSMS `status: 0` is an error even with HTTP 200. Never print OTPs, API keys or App Passwords in logs or support messages.

Sources: https://ninzasms.in.net/otp-api and https://docs.aws.amazon.com/ses/latest/dg/send-email-smtp-software-package.html
