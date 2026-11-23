# THE WOC — Wind of Change

Acadia-inspired student ecosystem with original generated campus photography, the reviewed crimson `#AB0C2F` / cream `#F6F4EE` palette, Outfit typography and reduced-motion-aware transitions.

## Run locally

Open PowerShell in this directory and run `./start-woc.ps1`. The launcher opens hidden, project-owned server processes and writes their PIDs and logs under `.run/`. Visit **http://127.0.0.1:4317**. Backend: **http://127.0.0.1:8317/api/health/**. Run `./stop-woc.ps1` to stop only these project processes.

Requirements: Node 20.9+ and Python 3.12+. Dependencies are already installed in this workspace. On another machine, run `npm ci` in `frontend`, create `backend/.venv`, then install `backend/requirements.lock.txt`, migrate and run `seed_catalogue`.

Frontend commands: `npm run dev`, `npm run typecheck`, `npm run build`. The launcher uses the static production build to avoid development-only origin restrictions. Build output is `frontend/out`.

Backend commands, from `backend`:

```powershell
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py seed_catalogue
.\.venv\Scripts\python.exe manage.py test core
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8317
```

## Accounts and administration

Local account registration requires email verification. Development email is printed to the backend console, and the local registration screen provides a development-only verification link. No default passwords or staff users are shipped. Create your own staff account with `manage.py createsuperuser`, then run `manage.py configure_admin_mfa <username>` locally and add the private URI to your authenticator. Staff login requires a TOTP code. Django administration is at port 8317 `/admin/`.

The public-facing private hosted showcase uses explicitly labelled browser-only demo state. Its accounts, enquiries and registrations are not connected to the local Django database. Never enter a real password into demo mode. The full local app uses HTTP-only Django session cookies and CSRF protection on anonymous and authenticated writes.

## Included

- Homepage with all requested subject areas, a three-slide image hero, manual controls, optional pausable autoplay, scroll entrances, hover effects, sticky header, accessible native dropdowns and mobile navigation.
- Eight module landing pages; 25 sample program detail pages; catalogue search/category filtering; editorial guides; contact, privacy, terms and certificate verification pages.
- Student dashboard sections for all eight modules, profile editing, notifications and certificate records.
- Django persisted registrations with uniqueness/capacity checks, under-18 permission declaration, team-size validation, solo/group selection and startup idea submission.
- Free sample learning workflow with lesson progress, assessment, project text, staff approval and verifiable completion records.
- Staff review interface, audit entries and Django content administration. Staff MFA support is installed and enforced at login.
- PostgreSQL environment configuration; SQLite fallback for immediate local use. Redis/Celery, S3 libraries are installed but no external services are provisioned.

## Remaining production work

This is a working pilot foundation, not the entire production system described in the master prompt. The following are intentionally not represented as completed: payment provider/webhooks/refunds; production SMTP; external PostgreSQL/Redis/S3 provisioning; verified guardian consent; employer KYC; real course videos and trainer content; object-scoped recruiter/trainer/college/mentor dashboards; fixture generation and scoring UI; judge workflows; QR ticket generation/check-in; upload scanning; signed agreements; dedicated per-domain Django apps; live CMS publishing into the statically exported catalogue; and automated deletion/retention requests. The current backend uses a shared `core` domain schema rather than claiming fifteen separately implemented apps.

Before real enrolment, configure these services, replace sample content, approve terms/privacy/safeguarding policies, define operating rules, complete penetration/accessibility testing and deploy Django using a production WSGI/ASGI server behind HTTPS. Django `runserver` is for local review only. Configure `DEBUG=false` and a unique secret key. No payments or jobs are guaranteed, and the sample catalogue does not represent signed partners or achieved outcomes.

## Image provenance

Three original photographs were generated using the built-in ImageGen tool: campus courtyard, innovation lab, and cultural festival. The festival image was edited only to correct the glasses-wearing woman’s raised hand. Originals remain preserved separately; optimized WebP copies are used by the site. The existing ZIP was inspected for design tokens and motion settings, not copied as the application source.

See `ASSET-PROMPTS.md` for the generation briefs and `backend/API.md` for endpoints.
