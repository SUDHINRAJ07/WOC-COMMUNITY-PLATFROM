# WOC local API

Base URL: `http://127.0.0.1:8317/api`. JSON requests and responses. Session authentication with credentials; obtain a token from `GET /csrf/` and send `X-CSRFToken` for every write, including registration and login. Both localhost and 127.0.0.1 frontend origins are allowed on port 4317.

| Endpoint | Method | Behaviour |
|---|---|---|
| `/health/` | GET | Readiness and integration status |
| `/csrf/` | GET | CSRF token |
| `/register/` | POST | Name, email, password, age, institution, terms, guardian_consent |
| `/verify/` | POST | Signed email token, expires after 24 hours |
| `/login/` | POST | Email and password; staff must also provide `otp` |
| `/logout/` | POST | End authenticated session |
| `/me/` | GET/PATCH | Read account; edit name, institution and bio only |
| `/programs/` | GET | Catalogue; optional `module` and `q` filters |
| `/records/` | GET/POST | Own records; create `{program: slug, data: {...}}` |
| `/learning/<uuid>/` | POST | Lesson completion or assessed project submission |
| `/notifications/` | GET | Own notifications |
| `/enquiries/` | POST | Persist name, email, kind and message |
| `/admin/records/` | GET/PATCH | Staff-only reviews; status changes audited |
| `/certificates/<uuid>/` | GET | Public, unpredictable-reference completion verification |

Duplicate program registrations return 400. Capacity is checked in a transaction; PostgreSQL is recommended for concurrent production workloads. Users cannot assign their own roles or staff status. Student records are filtered to the authenticated owner. Public catalogue queries are capped at 100 items and staff record queries at 200 for this pilot; cursor pagination remains a production extension.


## Updated authentication flows

- `POST /phone/send-otp/`: `{phone, country_code, purpose}`. Purpose is `register`, `login`, or authenticated `verification`. Provider acceptance is required; unavailable delivery returns 503 without a usable challenge. Explicit local preview returns `delivery_mode: test` and is never enabled for production.
- `POST /auth/phone/`: `{action, challenge_id, otp}`; registration additionally requires `name`, `age`, `institution`, `terms` and under-18 `guardian_consent`. Only verified existing mobile accounts can use mobile sign-in; staff use email and TOTP. Challenges expire after five minutes, allow three failed attempts, and cannot cross purposes or be reused.
- `POST /register/`: if account creation succeeds but SMTP fails, returns 201 with `delivery_status: failed` and a delivery error. The UI allows resending; it does not claim that mail was sent.
- `POST /resend-verification/`, `POST /password-reset/request/`: delivery failures return 503.
- Google authorization-code callbacks require matching session state. Existing-account linking uses a short-lived server-side linking ticket, not a second exchange of an already-used authorization code. Staff cannot bypass MFA with Google.

See `AUTH-DEPLOYMENT.md` for MSG91, SMTP and HTTPS production configuration. SMS provider acceptance and SMTP acceptance do not prove receipt; validate delivery with a consenting test recipient after configuration.
