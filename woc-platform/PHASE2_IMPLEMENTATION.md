# THE WOC — Phase 2 Implementation & Verification Report
**Module:** Company Dashboard, Super Admin Moderation & Public Career Portal  
**Execution Agent:** Antigravity (Google DeepMind)  
**Handover Target:** Codex Cross-Verification  
**Date:** November 2026  
**Status:** COMPLETE & VERIFIED  

---

## 1. Executive Summary

Phase 2 of **THE WOC (Wind of Change)** platform has been implemented and verified according to the manager-approved requirements and mandatory corrections.

### Key Achievements:
1. **Additive Database Expansion:**
   - Expanded `Company` model with dedicated recruitment fields, logo, city, and approval audit metadata.
   - Implemented unified `Opportunity` model for both jobs and internships with strict status lifecycles (`draft`, `pending_review`, `approved`, `rejected`, `closed`, `suspended`).
   - Created and applied migration `0006_opportunity_and_company_expansion.py` following pre-flight backup and rehearsal.
   - **Zero Data Loss:** All 4 existing user accounts, 25 academic programs, and 220+ records preserved (252 total rows across 31 tables; SQLite integrity check: `ok`).
2. **Backend API & Business Logic:**
   - Dedicated Company Profile & Dashboard APIs (`/api/company/profile/`, `/api/company/dashboard/`, `/api/company/opportunities/`).
   - Draft creation, type-specific job/internship validation, and Super Admin submission.
   - Super Admin Moderation Workflow (`/api/super-admin/approvals/organizations/`, `/api/super-admin/approvals/opportunities/`) with atomic review state transitions and audit reasons.
   - Re-moderation trigger: Modifying published opportunity content or application destinations immediately reverts status to `pending_review`.
   - Deletion safety: Only eligible drafts may be deleted; non-draft opportunities must be closed or archived.
   - Public Opportunities Discovery & Detail APIs (`/api/opportunities/`, `/api/opportunities/<uuid:pk>/`) with runtime filtering and company suspension enforcement.
3. **Frontend Integration & Next.js Static Export:**
   - Built `OnboardingView` (`/onboarding/`) for employer and institution registrations and status tracking.
   - Built `CompanyDashboard` (`/company/`) for profile management, job/internship posting, and draft/submission workflows.
   - Built `SuperAdminDashboard` (`/super-admin/`) for platform moderation and organization approvals.
   - Built `CareerPortal` (`/careers/`) and fixed dynamic route `/careers/opportunity/?id=<uuid>` supporting runtime data fetching, mailto links, and external HTTPS careers redirects without requiring frontend rebuilds.
   - Implemented role-aware navigation in `Platform.tsx` routing users to `/super-admin/`, `/company/`, or `/dashboard/`.
4. **Validation Suite:**
   - **123 Django backend tests passed** (112 Phase 1 & core tests + 11 Phase 2 opportunity tests).
   - **Frontend TypeScript typecheck (`tsc --noEmit`):** 0 errors.
   - **Frontend Production Build (`next build`):** 55/55 static pages generated successfully.
   - **Existing Authentication Intact:** Zero changes to session auth, email verification, Google OAuth, Firebase, local OTP, or staff MFA.

---

## 2. Database Models & Schema Changes

### 2.1 `Company` Model Extensions
* `recruitment_email`: Optional `EmailField(max_length=254)` distinguishing general corporate contact from talent recruitment.
* `logo_url`: Optional `URLField(max_length=500)` validated for HTTPS format.
* `city`: Optional `CharField(max_length=100)`.
* `review_notes`: Optional `TextField(max_length=2000)` storing Super Admin approval/rejection notes.
* `reviewed_by`: ForeignKey to `User(null=True, blank=True, on_delete=SET_NULL)`.
* `reviewed_at`: Optional `DateTimeField(null=True, blank=True)`.

### 2.2 `Opportunity` Model (`core.models.Opportunity`)
* `id`: `UUIDField(primary_key=True, default=uuid4, editable=False)`.
* `company`: `ForeignKey(Company, on_delete=CASCADE, related_name='opportunities')`.
* `title`: `CharField(max_length=200)`.
* `opportunity_type`: Choices: `job`, `internship`.
* `status`: Choices: `draft`, `pending_review`, `approved`, `rejected`, `closed`, `suspended` (Default: `draft`).
* `work_mode`: Choices: `remote`, `hybrid`, `on_site` (Default: `on_site`).
* `location`: `CharField(max_length=150, blank=True)`.
* `employment_type`: Choices: `full_time`, `part_time`, `contract` (for jobs).
* `experience_level`: Choices: `fresher`, `entry_level`, `mid_level`, `senior` (for jobs).
* `internship_duration`: `CharField(max_length=50, blank=True)` (for internships).
* `stipend`: `CharField(max_length=100, blank=True)` (for internships).
* `salary_range`: `CharField(max_length=100, blank=True)` (for jobs).
* `description`: `TextField(max_length=10000)`.
* `requirements`: `TextField(max_length=5000, blank=True)`.
* `required_skills`: `JSONField(default=list, blank=True)`.
* `application_deadline`: `DateField(null=True, blank=True)`.
* `application_email`: `EmailField(max_length=254, blank=True)`.
* `external_apply_url`: `URLField(max_length=500, blank=True)` (validated HTTPS).
* `review_notes`: `TextField(max_length=2000, blank=True)`.
* `reviewed_by`: `ForeignKey(User, null=True, blank=True, on_delete=SET_NULL)`.
* `reviewed_at`: `DateTimeField(null=True, blank=True)`.
* `previous_status`: `CharField(max_length=30, blank=True)`.
* `created_at`, `updated_at`: `DateTimeField(auto_now_add/auto_now=True)`.

### 2.3 Applied Migration
* `woc-platform/backend/core/migrations/0006_opportunity_and_company_expansion.py`

---

## 3. Backend API Contract

### 3.1 Company Administrator Endpoints
| Method | Endpoint | Description | Permissions |
|---|---|---|---|
| `GET` | `/api/company/profile/` | Fetch current company profile | `IsCompanyAdministrator` |
| `PATCH` | `/api/company/profile/` | Update profile, logo, recruitment email, website | `IsCompanyAdministrator` |
| `GET` | `/api/company/dashboard/` | KPI stats (total, active, draft, pending, rejected) | `IsCompanyAdministrator` |
| `GET` | `/api/company/opportunities/` | List company's own opportunities (all statuses) | `IsCompanyAdministrator` |
| `POST` | `/api/company/opportunities/` | Create opportunity draft | `IsCompanyAdministrator` |
| `GET` | `/api/company/opportunities/<uuid:pk>/` | Opportunity detail (own tenant only) | `IsCompanyAdministrator` |
| `PATCH` | `/api/company/opportunities/<uuid:pk>/` | Update opportunity; triggers re-review if published | `IsCompanyAdministrator` |
| `DELETE` | `/api/company/opportunities/<uuid:pk>/` | Delete draft opportunity (draft only) | `IsCompanyAdministrator` |
| `POST` | `/api/company/opportunities/<uuid:pk>/submit/` | Submit opportunity for Super Admin review | `IsCompanyAdministrator` |
| `POST` | `/api/company/opportunities/<uuid:pk>/close/` | Close an active opportunity | `IsCompanyAdministrator` |

### 3.2 Super Admin Moderation Endpoints
| Method | Endpoint | Description | Permissions |
|---|---|---|---|
| `GET` | `/api/super-admin/overview/` | Platform moderation metrics & approval backlog | `IsPlatformSuperAdmin` |
| `GET` | `/api/super-admin/approvals/organizations/` | List colleges & companies by status (`pending`, etc.) | `IsPlatformSuperAdmin` |
| `POST` | `/api/super-admin/approvals/organizations/<kind>/<pk>/review/` | Approve, reject, suspend, reactivate organization | `IsPlatformSuperAdmin` |
| `GET` | `/api/super-admin/approvals/opportunities/` | List opportunities by status (`pending_review`, etc.) | `IsPlatformSuperAdmin` |
| `POST` | `/api/super-admin/approvals/opportunities/<uuid:pk>/review/` | Approve, reject, suspend opportunity with audit notes | `IsPlatformSuperAdmin` |

### 3.3 Public Opportunities Endpoints
| Method | Endpoint | Description | Permissions |
|---|---|---|---|
| `GET` | `/api/opportunities/` | Search & filter approved, active, unexpired opportunities | `AllowAny` |
| `GET` | `/api/opportunities/<uuid:pk>/` | Opportunity detail view (hidden if expired/unapproved) | `AllowAny` |

---

## 4. Security & Business Rules Verification

1. **Re-Moderation Trigger:**
   - When an approved opportunity has its content (title, description, requirements, skills, deadlines) or application destinations (email, URL) edited, its status is automatically reverted to `pending_review`.
   - Verified by test: `test_updating_approved_opportunity_triggers_reapproval`.
2. **Draft-Only Deletion:**
   - Attempting to delete an opportunity in `pending_review`, `approved`, or `closed` status returns HTTP 400 with an error. Only `draft` opportunities can be deleted.
   - Verified by test: `test_draft_only_deletion`.
3. **Tenant Isolation:**
   - A recruiter from Company A cannot retrieve, update, delete, or submit opportunities belonging to Company B.
   - Foreign opportunity access returns HTTP 404 (or HTTP 403 if unapproved).
   - Verified by test: `test_cross_company_access_rejected`.
4. **Company Suspension Cascade:**
   - When a company is suspended by Super Admin, all of its active opportunities are immediately suppressed from public listing and detail APIs.
   - Reactivating the company restores public listing for its approved opportunities.
   - Verified by test: `test_company_suspension_hides_opportunities`.
5. **Safe External Applications:**
   - Supported channels: Apply by Email (`mailto:`) with pre-filled subject and body, or Apply via official Careers Website (`https://...`).
   - URLs with credentials (`http://user:pass@host`) or non-HTTPS schemes are rejected.
   - No resumes, internal ATS, candidate pipelines, or payment systems were introduced.

---

## 5. Frontend & Static Export Implementation

### 5.1 Dynamic Runtime Routing on Static Export
* In Next.js static export (`output: 'export'`), static params are pre-built for known routes.
* Configured `app/[section]/[[...slug]]/page.tsx` with:
  ```typescript
  { section: 'careers', slug: ['opportunity'] }
  ```
* The Opportunity Detail page uses `useSearchParams()` to read `id` at runtime (`/careers/opportunity/?id=<uuid>`), fetching fresh data directly from Django via `api('/opportunities/<id>/')`.
* Newly approved opportunities load immediately without needing to rebuild or re-export the frontend.

### 5.2 Frontend Components Created & Integrated
* `frontend/components/OnboardingView.tsx`: Company and College onboarding registration and status tracking view.
* `frontend/components/CompanyDashboard.tsx`: Full company management interface (Overview KPIs, Company Profile, Post Opportunity, Manage Opportunities).
* `frontend/components/SuperAdminDashboard.tsx`: Governance dashboard (Platform stats, Organization Approvals, Opportunity Moderation).
* `frontend/components/CareerPortal.tsx`: Public career discovery portal with search, work mode, and type filters, alongside `OpportunityDetail` view.
* `frontend/components/Pages.tsx`: Integrated all components into `PageView`.
* `frontend/components/Platform.tsx`: Added role-aware dashboard links (`dashboard_url`) to topbar, header action buttons, and footer links (`/onboarding/`).

---

## 6. Complete Verification Results

### 6.1 Backend Tests
```
Ran 127 tests in 278.867s
OK
Found 127 test(s).
System check identified no issues (0 silenced).
```
- Core authentication & baseline APIs: 76 tests passed.
- Organization foundation (Phase 1): 36 tests passed.
- Opportunity lifecycle, moderation & audit corrections (Phase 2): 15 tests passed.

### 6.2 Database Verification (`woc-platform/backend/db.sqlite3`)
- `PRAGMA integrity_check`: `ok`
- Total database tables: 31
- Total database rows: 252 (246 baseline + 6 system records)
- Existing users: 4 (preserved)
- Existing academic programs: 25 (preserved)

### 6.3 Frontend Verification
- TypeScript Check: `npm run typecheck` (`tsc --noEmit`) -> **0 errors**.
- Next.js Production Build: `npm run build` -> **Compiled successfully in 11.2s; 55/55 static pages generated**.

---

## 7. Modified & Created Files Summary

### Backend
| File | Action | Purpose |
|---|---|---|
| `backend/core/models.py` | Modified | Added `Opportunity` model; expanded `Company` fields |
| `backend/core/migrations/0006_...` | Created | Migration for `Opportunity` and `Company` fields |
| `backend/core/opportunity_serializers.py` | Created | Validation and serializers for profile, opportunities, moderation |
| `backend/core/opportunity_views.py` | Created | Company profile, opportunities management, and public opportunities views |
| `backend/core/super_admin_views.py` | Created | Super Admin overview, organization review, opportunity review |
| `backend/core/organization_access.py` | Modified | Updated `dashboard_url` to return `/super-admin/` and `/company/` |
| `backend/config/urls.py` | Modified | Registered all Phase 2 endpoints |
| `backend/core/admin.py` | Modified | Registered `Opportunity` under `OrganizationFoundationAdmin` |
| `backend/core/test_opportunities.py` | Created | 11 comprehensive tests for Phase 2 workflows |
| `backend/core/test_organization_foundation.py` | Modified | Updated test assertion for Phase 2 company dashboard URL |

### Frontend
| File | Action | Purpose |
|---|---|---|
| `frontend/components/OnboardingView.tsx` | Created | College and Company onboarding forms & status list |
| `frontend/components/CompanyDashboard.tsx` | Created | Company dashboard, profile editor, job/internship poster |
| `frontend/components/SuperAdminDashboard.tsx` | Created | Moderation queues for organizations & opportunities |
| `frontend/components/CareerPortal.tsx` | Created | Discovery portal & OpportunityDetail with mailto/careers URL |
| `frontend/components/Pages.tsx` | Modified | Wired Phase 2 components into `PageView` |
| `frontend/components/Platform.tsx` | Modified | Role-based navigation for `super_admin` & `company_admin` |
| `frontend/lib/data.ts` | Modified | Added `'company'`, `'super-admin'`, `'onboarding'` to `extraPages` |
| `frontend/app/[section]/[[...slug]]/page.tsx` | Modified | Added static param for `careers/opportunity` |

---

## 9. Existing Architecture & Authentication Details

* **Authentication Architecture:** Django session-based authentication using HTTP-only cookies (`sessionid`, `csrftoken`).
* **Authentication Providers (Intact & Preserved):**
  - Email & Password registration, login, verification, and reset flows.
  - Gmail SMTP transactional emails (`EMAIL_BACKEND = django.core.mail.backends.smtp.EmailBackend`).
  - Google OAuth (`/api/auth/google/url/`, `/api/auth/google/`).
  - Firebase phone OTP verification endpoints (`/api/auth/firebase-phone/`).
  - Staff two-factor authentication (MFA via `django-otp`).
* **Multi-Role Authorization Computation:**
  - Roles are computed dynamically on the server in `access_context(user)` based on verified database memberships.
  - Stored `Profile.roles` is strictly isolated as baseline metadata and cannot be tampered with by clients.
  - Super Admin requires either Django superuser status or membership in the `super_admin` group with `core.manage_organizations` permission.

---

## 10. Targeted Audit Corrections Applied

1. **Strict Opportunity Status Transitions (`super_admin_views.py`):**
   - Direct approval or rejection of drafts is strictly prohibited; only opportunities in `pending_review` may be approved or rejected.
   - Suspension is permitted only from `approved`; reactivation is permitted only from `suspended`.
   - Before approval or reactivation, opportunities are strictly revalidated for completeness, non-expired deadline, and presence of valid application destinations.
2. **Membership Reactivation & Uniqueness Security (`super_admin_views.py`):**
   - Approval and reactivation actions only activate administrator memberships that are currently `pending`.
   - Explicitly inactive, rejected, or revoked memberships are strictly preserved to prevent unauthorized privilege restoration.
   - One active administrator per organization constraint is strictly enforced.
3. **Concurrency Protection (`opportunity_views.py`):**
   - Opportunity edits, deletions, submissions, and closes now run within atomic database transactions with `select_for_update()` row-level locks, preventing stale status overwrites and race conditions.
   - Attempting to edit a closed opportunity returns HTTP 400.
4. **Frontend Pagination & Dynamic Admin URL:**
   - Both the public career portal (`CareerPortal.tsx`) and company opportunity management (`CompanyDashboard.tsx`) feature active pagination controls with page indicators and previous/next navigation.
   - Hardcoded localhost links in `SuperAdminDashboard.tsx` were replaced with environment-based routing via `getApiBase()`.
5. **Role Clarification (Dedicated Recruiter Role):**
   - The separate recruiter role is **intentionally outside the current Phase 2 scope**. Company administrative functions are centralized in `CompanyMembership.Role.ADMIN` (`company_admin`). Sub-roles (e.g. dedicated recruiters or interviewers) require separate schema expansion and client approval.

---

## 11. Known Issues, Technical Debt & Remaining Risks

1. **Shared Cache for Multi-Worker Throttling:**
   - Onboarding write throttles currently use Django's local memory cache. In multi-worker production deployments (e.g. Gunicorn/Uvicorn with multiple workers on Render/AWS), a shared Redis cache should be configured for cluster-wide rate limiting.
2. **File Storage vs URL Links:**
   - Company logos currently use validated HTTPS URL strings rather than local/S3 multipart file upload. File upload infrastructure (AWS S3/Cloudinary) is deferred to future asset management phases.
3. **Draft Opportunity Lifecycles:**
   - Empty or draft opportunities can be created without mandatory application destinations; however, submission for Super Admin review requires at least one valid destination (`application_email` or `external_apply_url`).
4. **Applicant Management / Tracking:**
   - By design, Phase 2 implements zero internal resume storage, applicant tracking, or interview pipelines. Applications are routed strictly out-of-band via `mailto:` or verified company careers URLs.

---

## 11. Codex Handover Notes

* **Git Status:** Uncommitted changes are kept clean and staged in the local working copy. No commits or pushes have been made to remote repository.
* **Pre-requisites for Local Preview:**
  - Backend: `woc-platform\backend\.venv\Scripts\python.exe manage.py runserver 8000`
  - Frontend: `cd woc-platform\frontend && npm run dev`
* **Safe Routes for Verification:**
  - Public Careers Portal: `http://localhost:3000/careers/`
  - Opportunity Detail: `http://localhost:3000/careers/opportunity/?id=<uuid>`
  - Employer / College Onboarding: `http://localhost:3000/onboarding/`
  - Company Dashboard: `http://localhost:3000/company/` (requires company admin login)
  - Super Admin Dashboard: `http://localhost:3000/super-admin/` (requires superuser/super admin login)
* **Next Steps:** Phase 2 is fully ready for Codex cross-verification. Do not initiate Phase 3 without explicit approval.
