# Phase 1 — roles, permissions and organization foundation

Scope: backend foundation only. No company dashboard, opportunity publishing, recruitment workflow, college training management, placement workflow or production deployment is included. Those remain in their approved later phases.

## Implemented

- Extended existing `Institution` with organization contact/profile and pending/approved/rejected/suspended review state.
- Added `Company`, `CollegeMembership` and `CompanyMembership`.
- Database constraints enforce one active student-college membership per user and one pending/active administrator per college/company. Inactive administrator history can remain without blocking a replacement. Normalized membership tables permit future staff expansion; expanding the initial administrator limit will require an explicit constraint migration.
- Existing accounts remain the only authentication identities. Existing email/password, verification, SMTP, local screen OTP, SMS, Firebase, Google and staff MFA logic was not changed.
- Groups seed baseline/global role labels. Existing superusers retain Super Admin access. A delegated Super Admin requires both the `super_admin` group and explicit `core.manage_organizations` permission. `is_staff` or a profile JSON label alone never grants platform-wide authority.
- Organization authority comes from active, approved organization memberships. Global college/company group membership alone does not grant tenant access. Revocation or suspension removes effective access on the next request.
- New organization submissions create pending organizations and pending administrator memberships. They do not change a user into Django staff or grant administrative access.
- Pending submitters can inspect their own registration status. Operational organization reads require an approved active membership or Super Admin authority.
- Foundation models are visible in Django admin only to authorized Super Admin staff, and are read-only during Phase 1. Approval/editing workflows are deferred to Phase 2.
- All list/detail organization reads are tenant-scoped, with pagination. Onboarding writes are limited to 20 per hour per user in addition to existing user throttles. Production multi-worker throttling requires a shared cache configuration in the later deployment phase.

## API contract

All endpoints use the existing Django session. POST requests require the existing CSRF token. Obtain it from `/api/csrf/`; send session cookies and `X-CSRFToken` as the existing frontend API helper does.

| Endpoint | Methods | Purpose |
| --- | --- | --- |
| `/api/access/` | GET | Effective roles, permissions and own organization memberships/statuses |
| `/api/onboarding/college/` | GET, POST | Own college onboarding submissions; create a pending college |
| `/api/onboarding/company/` | GET, POST | Own company onboarding submissions; create a pending company |
| `/api/organizations/colleges/` | GET | Paginated authorized college list |
| `/api/organizations/colleges/<id>/` | GET | Authorized college details; foreign tenant IDs return 404 |
| `/api/organizations/companies/` | GET | Paginated authorized company list |
| `/api/organizations/companies/<uuid>/` | GET | Authorized company details; foreign tenant IDs return 404 |

College onboarding accepts `name`, `city`, `contact_email`, optional HTTPS `website`, and optional `address`. Company onboarding accepts `name`, HTTPS `website`, `contact_email`, optional `city`, and optional `description`. URLs containing embedded credentials are rejected. Unknown fields, client role grants, owner IDs, approval status and reviewer fields are rejected.

Lists return `count`, `next`, `previous`, and `results`. Successful onboarding returns HTTP 201 and `approval_status: pending`. A repeated same-name pending/active submission by the same administrator returns HTTP 409. No approval, invitation, publication, member activation or destructive endpoint is exposed yet.

Existing `/api/me/` and successful login responses retain their existing user fields and additionally expose `authorization`. Their `roles` value is computed from authorized server state; the stored legacy `Profile.roles` is not rewritten. The original `/dashboard/` remains the safe destination. Future dashboard URLs and frontend role redirection will be enabled only when those pages actually exist.

## Migrations and preservation

`0004_organization_foundation` adds tables, fields, constraints and the custom organization-management permission. `0005_seed_organization_roles` creates role groups, maps existing explicit verified college ownership to approved/active membership, keeps unverified ownership pending, and recognizes existing superusers. It does not infer student affiliations from free-text institution names, promote ordinary staff, reset accounts or change passwords or verification flags.

Before application, the database was backed up using SQLite's online backup API and checked with `PRAGMA integrity_check`. The migration plan and SQL were inspected. SQLite implements some schema changes by copying/rebuilding tables; preservation was checked in a rehearsal database rather than assuming those operations were harmless.

Private artifacts are under the repository root `.local-backups/phase1-organization-foundation/` and are ignored by Git. They include the original database, pre-existing work fingerprints, migration plan/SQL, and a rehearsal result. The rehearsal additionally exercised synthetic verified/unverified legacy colleges without adding those fixtures to the working database.

Rollback must be performed with the application stopped and after backing up any new data. Reversing the schema migrations drops the newly introduced organization tables, so it is not a lossless rollback once onboarding data exists. Restore a verified pre-migration database together with compatible source, or export/reconcile new organization data before a schema rollback. The data migration intentionally does not delete groups on reversal. Do not overwrite or delete the existing private snapshots.

## Changed files

Modified: `backend/core/models.py`, `backend/core/admin.py`, `backend/core/views.py` (user serialization only), and `backend/config/urls.py` (new routes only).

Created: `backend/core/apps.py`, `backend/core/organization_signals.py`, `backend/core/organization_access.py`, `backend/core/organization_serializers.py`, `backend/core/organization_views.py`, `backend/core/test_organization_foundation.py`, migrations `0004` and `0005`, and this document.

Pre-existing uncommitted changes were snapshotted before work. Frontend source files, theme, animations, catalog data, dependencies, authentication provider configuration and existing authentication view functions remain unchanged during Phase 1.

## Phase 2 — requires separate approval

1. Add audited Super Admin organization approval/rejection/suspension and safe membership activation services.
2. Build company onboarding/status/profile/dashboard UI using the existing theme and components.
3. Add company-owned job/internship opportunities with draft, review, published, rejected and closed states and deadline handling.
4. Require Super Admin approval for each posting. Material changes to approved content or application destinations must return the posting to review.
5. Provide runtime public opportunity list/detail APIs and a static-compatible detail page so new postings do not require a frontend rebuild.
6. Apply externally through validated recruitment email or an official HTTPS careers URL. No internal applications, candidate database, shortlist or interview workflow.
7. If outbound clicks are enabled, label them as clicks only, never applications or placements.
8. Add scoped permissions, moderation and external-link validation tests, then review before proceeding to later phases.

## Phase 1 validation results

- Full Django regression suite: **112 tests passed**, including **36 organization-foundation tests**, existing authentication/provider-isolation tests, and the isolated localhost HTTP session test. No real SMS/email delivery was exercised.
- Final revoked-member onboarding visibility checks: **4 targeted tests passed** after tightening that read scope.
- Database migration rehearsal: **210 original rows preserved**, with additional synthetic legacy-ownership cases tested only in the private copy.
- Working database migrations `0004` and `0005`: **applied successfully** after a second, fresh backup immediately before application.
- Post-migration integrity: **OK**. All **220 rows present immediately before application** were preserved in their original columns. Existing **4 users and 25 programs** remain. The fresh backup includes intervening normal local activity after the earlier snapshot.
- Django system checks and migration consistency: **passed**, no pending migrations and no ungenerated model changes.
- All **75 frontend source fingerprints unchanged**. Existing authentication view function bodies are unchanged; only user-response serialization gained role/authorization metadata.
- Existing pre-modified files outside the intentionally extended URL/user-serialization files were checked against their initial fingerprints and remain unchanged.
- Local backend health: **OK**; new protected endpoints return **403** anonymously; existing frontend login returns **200**.
- Frontend build/typecheck was not repeated because Phase 1 changes no frontend source or dependencies.
- PostgreSQL, production multi-worker concurrency/shared-cache behavior, and public deployment remain later-phase validation; no production readiness or provider delivery claim is made.

There are no new provider credentials or dependencies for Phase 1. Approval interfaces, organization staff invitations/activation, jobs, college course assignments and placement outcomes are intentionally unavailable until their respective approved phases. Organization memberships marked inactive are excluded from onboarding profile reads as well as operational access; own membership status history remains available in authorization metadata.
