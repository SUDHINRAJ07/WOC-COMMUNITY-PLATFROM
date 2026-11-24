# Live email and MSG91 OTP setup

The login and registration screens support email/password and mobile OTP. SMS provider acceptance is checked before an OTP challenge becomes usable. An accepted provider request does not guarantee inbox or handset delivery.

## MSG91

1. Open your MSG91 account's OTP section. Create/approve an OTP template containing `##OTP##`, then copy its template ID. Complete any sender/template requirements shown by MSG91 for your account and destination countries.
2. Create/copy the account auth key. Add these values securely to the backend server environment, never to frontend variables or source control:

   ```dotenv
   SMS_PROVIDER=msg91
   SMS_DEV_MODE=false
   MSG91_AUTH_KEY=<private MSG91 auth key>
   MSG91_TEMPLATE_ID=<approved OTP template ID>
   ```

3. Ensure the account can send to the intended recipients and has the required sending balance/permissions. Restart the backend. Test using a number you control. Code expiry is five minutes; resending has a 60-second cooldown.

Official API reference: https://docs.msg91.com/otp/sendotp

## Email

Use a transactional SMTP service authorized to send from your WOC address. Configure `EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend`, `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS`, and `DEFAULT_FROM_EMAIL` on the backend. Complete the provider's sender/domain verification. Console mail is a local preview, not delivery to an inbox. SMTP credentials already present locally must be configured independently on the production server.

## Production URL and security

- Set `DEBUG=false`, a strong private `DJANGO_SECRET_KEY`, explicit `ALLOWED_HOSTS`, and `FRONTEND_URL` to the actual HTTPS website URL so verification/reset links work on recipients' devices.
- Set `NEXT_PUBLIC_API_URL` to the live backend's HTTPS `/api` URL before building the frontend; set `NEXT_PUBLIC_DEMO_MODE=false`.
- Configure the actual frontend origin in `CORS_ALLOWED_ORIGINS` and `CSRF_TRUSTED_ORIGINS`. Prefer frontend/backend behind the same site with `/api` proxied to Django. A frontend-only static tunnel does not serve Django APIs.
- Apply migrations and restart the backend. Keep `SESSION_COOKIE_SECURE=true` and `CSRF_COOKIE_SECURE=true` in production.
- Google sign-in is optional and only displayed when configured. Set its client credentials and exact redirect URI separately if needed. Staff use email plus authenticator; phone/Google cannot bypass staff MFA.
- Never enable preview/demo modes for a live service. No real SMS is sent in explicitly enabled local test mode, and the UI labels that mode.

Live delivery must be validated with a consenting test recipient after provider credentials are configured. Never paste private keys into chat or commit `.env`.
