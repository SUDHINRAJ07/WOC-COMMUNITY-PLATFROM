# WOC — Local signup and login

The Django backend is connected again using the preserved SQLite database. Existing accounts, administrator MFA devices, program records and frontend styling are preserved. No database reset or new schema migration is needed.

## Run

Use `START.bat` in the repository root. It starts or reuses both localhost services:

- Website: http://127.0.0.1:4317/
- Backend health: http://127.0.0.1:8317/api/health/

To run manually, start `.venv/Scripts/python.exe manage.py runserver 127.0.0.1:8317` from `backend`, and `npm run dev` from `frontend` in another terminal. `stop-woc.ps1` stops recorded WOC servers. Rebuild from `frontend` with `npm run build` after changing frontend code when using the static launcher.

## Email accounts

Create an account with name, age, institution, email, a strong password and required consent. The account is saved on the server and can be used repeatedly with the same email/password. Passwords are hashed by Django. Local configuration sets `EMAIL_VERIFICATION_REQUIRED=false`, so no verification email is needed to sign in. This does not claim that the email address is verified: the email verification flag remains false until actual verification.

## Mobile OTP accounts — local development only

Choose Mobile OTP on signup, enter student details and a phone number, then request a code. A random six-digit development code appears on the same screen; no SMS or Firebase request is made. Enter it to create the account and start a real Django session. On a later Mobile OTP login, request a fresh code for the same number to access the existing account. Unknown numbers on the login screen do not create accounts.

Codes expire after five minutes, permit at most three incorrect attempts, are single-use, have a 60-second resend cooldown and are bound to the requesting browser session. Resending invalidates the previous browser challenge. Only OTP hashes are stored in the database.

`WOC_LOCAL_SCREEN_OTP=true` is explicitly set in the private local backend `.env`. On-screen OTP is rejected when DEBUG is false, the request host or address is not loopback, or forwarded proxy headers are present. It must not be used for a public deployment; live SMS is a separate provider-backed setup. Leave it disabled (`false`) outside direct local development. Staff and superuser accounts cannot use mobile OTP to bypass their authenticator.

## Preserved functionality

Django session cookies, CSRF protection, profile fields, notifications, program registrations, learning data and staff administration remain in place. All 25 frontend program entries and existing theme CSS are unchanged. The private original backend/database snapshot remains under the Git-ignored `.local-backups/backend-removed-2026-11-26/` folder at the repository root. It is never committed.

The earlier Firebase code remains isolated from the local screen-OTP route. Firebase credentials are not required for this flow. No live SMS, email delivery or Google-provider verification is claimed by this local implementation. No payments or deployment were performed.


## Student profile suggestion catalog

After migrations on a new database, run `python manage.py import_profile_suggestions` from `backend` using its virtual environment. This idempotent offline import reads the bundled compressed catalog and updates only `ProfileSuggestion` reference rows. It does not create approved colleges or memberships. The authenticated `/api/profile/suggestions/?kind=institution&q=alpha` endpoint searches the database; supported kinds are institution, state, city, qualification and skill. City queries support a state filter. Existing profile values and custom entries remain supported.

The bundled snapshot contains 53,366 AISHE-derived college names (via the independently maintained indian-institutions-data repository), 36 States/UTs and 7,329 GeoNames city/town entries. It is not a guarantee of current/exhaustive college coverage. Location data uses the GeoNames cities500 extract, so very small places may be absent. Source URLs, source commit, download date and checksum are recorded in `backend/core/data/profile-suggestions-sources.json`; the college snapshot license is retained alongside it. Location data attribution: https://www.geonames.org/ (Creative Commons Attribution). Qualification and skill entries are a curated WOC vocabulary, not an official taxonomy. All network downloads happen during maintenance, never while a student types.

### Signup email OTP
Set `EMAIL_SIGNUP_OTP_REQUIRED=true` in the private backend environment to require a five-minute, single-use email code for new email/password registrations. Existing accounts remain unchanged when `EMAIL_VERIFICATION_REQUIRED=false`; new accounts are individually marked as requiring verification and cannot bypass it at password login. Keep `EMAIL_VERIFICATION_REQUIRED=true` only if all existing unverified accounts should also be blocked. Google authentication and mobile OTP are separate, unchanged flows.

Configure `EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend`, `EMAIL_HOST=smtp.gmail.com`, `EMAIL_PORT=587`, `EMAIL_USE_TLS=true`, `EMAIL_USE_SSL=false`, a sender Gmail address in `EMAIL_HOST_USER`, its private Google App Password in `EMAIL_HOST_PASSWORD`, and a matching `DEFAULT_FROM_EMAIL`. Never commit the actual `.env` or credentials. Configure production environment variables separately; a Git push does not copy local secrets. Signup responses never expose the OTP or a development verification link. Legacy link-verification endpoints remain available for previously issued links.

Render Free blocks outbound SMTP ports 25/465/587. Gmail SMTP therefore requires an SMTP-capable host/paid Render instance; a free Render deployment needs a separately configured HTTPS email API instead. Do not claim live delivery based solely on local tests or provider acceptance.
