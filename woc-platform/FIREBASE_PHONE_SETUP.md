# WOC Firebase Phone Authentication

Firebase verifies phone ownership. Django owns WOC accounts, authorization, session cookies and CSRF. The existing theme, styles, imagery and motion are unchanged.

## Account flow

1. Create an account through the existing Email or Google flow and sign in to WOC.
2. Open Profile settings → Mobile Number Verification → Send Verification OTP.
3. Firebase performs reCAPTCHA and sends/verifies the phone OTP.
4. The browser submits the resulting ID token to `POST /api/phone/firebase-verify/` using the WOC session and CSRF token.
5. Django verifies the token with `check_revoked=True`, the project, audience, issuer, phone provider, phone claim, expiry and recent `auth_time` (five minutes). It saves the existing Profile phone fields and binds the Firebase identity to that WOC user.
6. Subsequent Mobile OTP login uses `POST /api/auth/firebase-phone/`. Both the verified phone and its active Firebase identity must already belong to the same existing WOC account. Unknown phones never create accounts. Staff, superusers and inactive users cannot use phone login.

Changing a number requires another fresh OTP. The old identity is retained as inactive, and the old number no longer permits login. Accounts linked through the former SMS provider must verify once through Firebase while signed in before Firebase mobile login becomes available. Existing account records remain intact.

Legacy phone-only accounts with no Email/Google sign-in method need authorized account recovery before linking if they no longer have a WOC session. A matching phone number alone never silently migrates or unlocks those accounts.

The old `/api/auth/phone/`, `/api/phone/send-otp/`, `/api/phone/resend-otp/` and `/api/phone/verify-otp/` endpoints now return HTTP 410. Their records and provider helper code remain for historical compatibility; they are not fallback paths. Firebase failure never calls MSG91.

## Frontend configuration

Copy the Firebase Web app values from Firebase Console → Project settings → Your apps into `frontend/.env.local` (ignored by Git):

```dotenv
NEXT_PUBLIC_FIREBASE_API_KEY=<Firebase Web API key>
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=<Firebase Web auth domain>
NEXT_PUBLIC_FIREBASE_PROJECT_ID=woc-29231
NEXT_PUBLIC_FIREBASE_APP_ID=<Firebase Web app ID>
NEXT_PUBLIC_DEMO_MODE=false
```

Keep the existing `NEXT_PUBLIC_API_URL` appropriate to the environment. These Firebase Web values are public client configuration, not Admin credentials. Next.js embeds public configuration at build time: restart development and rebuild after changing it. Missing values produce a clear error when requesting OTP; static builds can still run without live credentials.

Each mounted phone flow uses an isolated, in-memory Firebase Auth instance. Resending replaces the reCAPTCHA instance; cancellation/unmount destroys it and the temporary Firebase app. Firebase sign-in never independently creates a WOC session.

## Backend configuration

Install `backend/requirements.lock.txt` using the backend virtual environment. Configure `backend/.env` or the deployment environment:

```dotenv
FIREBASE_PROJECT_ID=woc-29231
GOOGLE_APPLICATION_CREDENTIALS=C:/secure/woc-firebase-admin.json
```

Use a service account for this Firebase project with the permissions needed to verify tokens and read Auth users for revocation checking, or use an appropriate Application Default Credentials workload identity. Keep private JSON outside the repository and frontend. Do not paste private keys into chat. Restart Django after configuration changes. No database migration or reset is required.

`FIREBASE_AUTH_EMULATOR_HOST` is explicitly rejected by this API so emulator tokens cannot accidentally be accepted as live proof, even when Django DEBUG is enabled. Unit tests mock verification; they do not require emulator settings or credentials.

## Console settings and actual SMS

- Confirm the Web app and Admin credentials belong to `woc-29231`.
- Authentication → Sign-in method: enable Phone.
- Configure SMS region policy to allow India, and only other destinations you intend to support.
- Add the actual hosted application domain to authorized domains. Current Phone Auth documentation says localhost is not allowed as a hosted domain for phone authentication; a localhost entry alone is not proof of live readiness.
- Real verification SMS requires eligible billing (Blaze), available quota and Firebase abuse checks. reCAPTCHA requires network access and suitable browser/domain configuration.
- Firebase Console fictional test numbers use their configured test codes and send no SMS. Explicit WOC demo mode is also browser-only, uses the clearly labelled preview code and never verifies a real phone or saves a backend account.
- Do not disable app verification in production. Phone verification is not an event-notification SMS subscription.

Official references: [Web Phone Auth](https://firebase.google.com/docs/auth/web/phone-auth), [Admin ID-token verification](https://firebase.google.com/docs/auth/admin/verify-id-tokens), [Auth limits](https://firebase.google.com/docs/auth/limits).

## Validation commands

From `backend`: `.venv/Scripts/python.exe manage.py test`.

From `frontend`: `npm run test:phone`, `npm run typecheck`, `npm run build`.

Backend tests use a separate test database. The Firebase tests cover token validation, revocation configuration, fresh authentication, ownership, duplicate/race rejection, CSRF, session login and number changes. Existing regression tests cover Email/Google, staff MFA, notifications and program workflows. Frontend tests mock the Firebase SDK to exercise initialization, captcha lifecycle, send/resend, wrong/correct OTP, retries, configuration errors, cancellation and the signup/login rendering. These are automated integration/unit checks, not an end-to-end test against Firebase's live service.

For live acceptance, use an approved authorized hosted environment with the real configuration, sign in to an existing non-staff WOC account, verify a consented actual phone, confirm the OTP arrives, verify the persisted badge after refresh, sign out and test linked phone login. Then verify number-change and duplicate-link behavior. Do not deploy merely to perform this check without approval.

**Live SMS delivery is unverified until that actual-phone acceptance test succeeds.** No billing, deployment, private credentials or actual SMS delivery is configured by this implementation.

## Changed files

Frontend:
- `frontend/lib/firebase-phone.ts` — Firebase client lifecycle, phone validation and error mapping.
- `frontend/lib/use-firebase-phone.ts` — component lifecycle integration and cleanup.
- `frontend/components/Pages.tsx` — existing phone-verification UI and signup guidance.
- `frontend/components/MobileAuthForm.tsx` — existing Mobile OTP UI connected to linked-account login.
- `frontend/tests/firebase-phone.test.cjs` — mocked SDK and rendering tests.
- `frontend/package.json` — added `test:phone`; retained the previously installed Firebase dependency.
- `frontend/.env.example` — public Firebase configuration placeholders.

Backend:
- `backend/core/firebase_phone.py` — Admin initialization and phone-proof verification.
- `backend/core/firebase_views.py` — linking, existing-account login and retired legacy endpoints.
- `backend/config/urls.py` — API routing.
- `backend/config/settings.py` — expected project and fresh-proof window.
- `backend/core/test_firebase_phone.py` — security, persistence, session and catalogue tests.
- `backend/core/tests.py` and `backend/core/test_auth_delivery.py` — replaced obsolete legacy phone-auth expectations; retained unrelated regressions.
- `backend/requirements.txt` and `backend/requirements.lock.txt` — Firebase Admin dependency and resolved environment.
- `backend/.env.example` — Admin configuration example.

Other: `.gitignore` protects local frontend config and common Admin credential filenames; this setup guide documents the integration. `frontend/package-lock.json` already contained the user's Firebase installation changes before implementation and was preserved.

## Implementation validation results

- Django full suite: **61 tests passed** (isolated test database), including email/password login and staff login with a generated TOTP code.
- Frontend mocked Firebase/rendering suite: **9 tests passed**.
- TypeScript: **passed**.
- Next.js production build: **passed; 51 pages generated**. The initial sandbox build hit a Windows directory permission error; the approved unrestricted rerun and final build passed.
- Django system checks: **passed**; migration dry-run: **no changes detected**.
- Python dependency integrity: **no broken requirements**; Firebase Admin **7.8.0** installed and pinned in the lock file.
- Existing local backend health: **OK**. Restarted the existing `--noreload` development server; the Firebase link route is registered and returns HTTP 403 for anonymous access. Existing local login page returns HTTP 200.
- Catalogue: **25 entries**, unchanged; existing theme CSS and model definitions unchanged.
- Actual Firebase test-number end-to-end flow: **not run**.
- Actual-phone SMS delivery: **not run / unverified**. Firebase Web configuration, Admin credentials and Console billing/domain/region settings still need to be supplied and verified.

Dependency installation encountered slow PyPI transfers. The two large Windows wheels were downloaded from official PyPI URLs, checked against PyPI SHA-256 hashes, and installed successfully; the lock file contains portable version pins rather than local file paths.
