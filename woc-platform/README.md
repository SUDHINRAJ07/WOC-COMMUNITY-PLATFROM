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
