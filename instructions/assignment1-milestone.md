# Assignment 1 — Milestone (Current State)

**Date:** 2025-11-26
**Repo/Branch:** gymmanager / feature/readme
**Milestone goal:** Document the current stage of the application as the baseline for future work.

---

## 1. Project Snapshot
- Purpose / problem statement: Async FastAPI backend for gym owners to manage their gym account and member records, exposing REST endpoints ready for a frontend.
- Intended users: Gym owners/managers and frontend clients consuming the API; testers working against the backend.
- Tech stack (languages, frameworks, runtime, tooling): Python 3.11+; FastAPI + Starlette; SQLAlchemy 2.0 (async) with Alembic; Pydantic v2; JWT via PyJWT; passlib[bcrypt]; mailer abstraction (console/SMTP); pytest + httpx + pytest-asyncio; SQLite default.
- How to run the project now (install, dev, tests): Create venv and `pip install -r requirements.txt`; copy `.env.example` to `.env` and set DB/SMTP/CORS/JWT secrets (default DB `sqlite+aiosqlite:///./app.db`); run `alembic upgrade head`; start `uvicorn app.main:app --reload`; health at `/health`, docs at `/docs`; tests via `pytest -q` (not executed in this audit because the workspace is read-only).

---

## 2. Repository Structure
- `app/main.py` entrypoint wiring routers, CORS, and JSON error handlers; exposes `/health`.
- `app/api/` FastAPI layer (`routers/auth.py`, `routers/gyms.py`, `routers/customers.py`, shared deps in `deps.py`).
- `app/services/` business logic (`auth.py`, `gyms.py`, `customers.py` with filtering and auto-deactivation).
- `app/domain/` SQLAlchemy models (`models.py`) and Pydantic schemas (`schemas.py`).
- `app/core/` shared config (`config.py`), logging setup, mailer adapters/proxy, and security helpers (bcrypt + JWT).
- `app/db/` SQLAlchemy declarative base and async session factory; `alembic/` migration env plus 4 version scripts evolving gyms/customers.
- `tests/` async integration tests for auth/gyms/customers/mailer using httpx ASGI transport.
- `requirements.txt`, `README.md`, `.env.example`, `codebase` (text dump of structure/content), local artifacts (`app.db`, `venv/`, `.pytest_cache`) present in working tree but meant to be ignored.

---

## 3. What Has Been Implemented
### 3.1 Core Features
- ✅ Health check at `/health` for uptime verification (`app/main.py`).
- ✅ Gym authentication: signup with hashed passwords and login issuing bearer JWTs via OAuth2 password flow (`app/api/routers/auth.py`, `app/services/auth.py`, `app/core/security.py`).
- ✅ Gym self-management: read/update/delete current gym at `/api/v1/gyms/me` (`app/api/routers/gyms.py`, `app/services/gyms.py`).
- ✅ Customer management: create/get/update/delete scoped to owning gym; enforces 404 when accessing another gym’s customer (`app/api/routers/customers.py`, `app/services/customers.py`).
- ✅ Customer search & filtering: active flag, free-text search, first/last/email filters, and age-range filtering derived from `date_of_birth`; auto-deactivates memberships whose `membership_end` is in the past on read paths (`app/services/customers.py`).
- 🟡 Email notifications: mailer abstraction with console/SMTP backends and retry/throttling; currently used for customer welcome emails, but gym signup welcome mail was removed during the service refactor and is no longer sent (`app/core/mailer.py`, `app/services/customers.py`).
- ✅ API hardening: central JSON error responses, CORS driven by `CORS_ORIGINS`, and basic logging bootstrap (`app/main.py`, `app/core/logging.py`, `app/core/config.py`).
- ✅ Database schema & migrations: gyms with description/type, customers with split names and optional DOB, timestamps, and FK cascade; Alembic scripts `202410050001`–`202410050004` align the schema (`alembic/versions/*.py`).
- 🟡 Test suite: async pytest coverage for auth, gyms, customers, and mailer behaviors (`tests/*.py`); not executed in this audit due to read-only constraints.

### 3.2 UI / UX (if applicable)
- 🔴 No frontend assets in repo; relies on FastAPI-generated Swagger/ReDoc only.

### 3.3 Backend / Logic (if applicable)
- ✅ Service layer separates HTTP from business logic (auth/signup/login, gym updates/deletes, customer CRUD/filtering/expiry) in `app/services/*`.
- 🟡 Mailer proxy provides retries/throttling but errors only log to stderr and gym signup flow no longer triggers mail.
- ✅ Dependency overrides allow test DB sessions and mailer stubbing for isolation (`tests/conftest.py`).

### 3.4 Data Layer (if applicable)
- ✅ SQLAlchemy models for gyms/customers with relationships and timestamp helpers (`app/domain/models.py`).
- ✅ Pydantic schemas for request/response validation with sensible field constraints (`app/domain/schemas.py`).
- ✅ Alembic async env pulls DB URL from settings; migrations cover table creation, new columns, and name split/DOB additions (`alembic/env.py`, `alembic/versions/*`).

---

## 4. Git History Insights
- Phase 1 (6a2b79f): Project skeleton with config, health check, initial README and pyproject.
- Phase 2 (01d99be): Added Alembic setup, ORM models/schemas, async DB session, switched to requirements.txt.
- Phase 3 (4329864): Introduced gym auth with password hashing and JWT issuance.
- Phase 4 (ca65a71): Added gym/customer CRUD endpoints and migrations for description/type and split names.
- Phase 5 (a8650cf): Implemented mailer adapters (console/SMTP) and hooked emails into signup and customer creation.
- Phase 6 (179d54b): Added async pytest suite and mailer tweaks for UTC-safe throttling.
- Phase 7 (a28b65d): Refactored to service layer, added filtering/age logic and auto-deactivation, added DOB migration; removed tracked coverage file.
- Phase 8 (5cb0a6f): Frontend-integration polish—logging, JSON error handlers, CORS parsing, README upgrades.
- Phase 9 (9962d05): Expanded README with full setup and API walkthrough.

---

## 5. Current Gaps / Issues
- Real-looking SMTP credentials live in `.env` in the repo root; secrets should be rotated and removed from working copies.
- Working tree carries local artifacts (`app.db`, `venv/`, `.pytest_cache`); risk of accidental commit and noise for contributors.
- Routers hard-code `/api/v1` while `api_prefix` exists in settings; config drift risk if prefix changes.
- Welcome email on gym signup was lost in the service refactor (a28b65d); mailer currently only fires on customer creation.
- Customer listing performs age filtering in Python after loading all rows; no pagination—could be slow at scale.
- Auto-deactivation only triggers on read paths; expired members remain active until fetched, and `membership_end` equality still counts as active.
- No CI defined; tests not run in this audit, so runtime regressions may be hidden.
- Security hardening pending: default `JWT_SECRET` is weak, no rate limiting/brute-force protection, and bcrypt 72-char limit not surfaced to clients.

---

## 6. Recommended Next Steps (Priority Order)
1. Sanitize secrets: purge/rotate SMTP credentials, ensure `.env` stays untracked, and keep `.env.example` non-sensitive; update `README.md` with secret-handling guidance; DoD: secrets rotated and no sensitive values in the repo.
2. Reinstate and test signup notifications: send welcome mail in `app/services/auth.signup_gym` (or background task), add pytest asserting mailer calls, and handle mail failures gracefully; DoD: tests green and mailer behavior verified for both gym signup and customer creation.
3. Wire configurable API prefix: apply `settings.api_prefix` to router prefixes and OAuth token URL, update docs, and add a regression test; DoD: changing `API_PREFIX` in `.env` reconfigures routes without code edits.
4. Optimize customer listing: move age filtering into SQL, add pagination/query limits, and index filterable columns; DoD: updated queries with params/tests and performance covered.
5. Establish CI and quality gates: add GitHub Actions (pytest + coverage), enforce `.coverage` in `.gitignore`, and document the test command; DoD: passing pipeline visible on PRs.
6. Plan production hardening: switch default DB to Postgres for deployment, add password/JWT secret policy checks, and consider background job for membership expiry; DoD: config supports Postgres, policy checks implemented, and expiry automation designed or shipped.

---

## Appendix
- Commands/scripts reference: `python -m venv venv && source venv/bin/activate` (or PowerShell equivalent); `pip install -r requirements.txt`; `alembic upgrade head`; `uvicorn app.main:app --reload`; `pytest -q`.
- Environment variables/secrets: JWT_SECRET, JWT_ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, DATABASE_URL, CORS_ORIGINS, MAILER_BACKEND, MAILER_RATE_LIMIT_SECONDS, MAILER_MAX_RETRIES, MAILER_RETRY_DELAY_SECONDS, SMTP_HOST/PORT/USERNAME/PASSWORD/USE_TLS/USE_SSL/SMTP_FROM_EMAIL, API_PREFIX.
- Helpful links: https://fastapi.tiangolo.com , https://alembic.sqlalchemy.org , https://docs.pytest.org .
