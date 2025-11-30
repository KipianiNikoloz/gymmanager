# REPORT — Assignment 2 (Final, Comprehensive)

## Table of Contents
1. Baseline (Assignment 1) and Objectives
2. Architecture Overview
3. Development Timeline (Plan vs. Execution)
4. Implemented Improvements (Assignment 2)
5. Testing & Quality
6. CI/CD & Deployment
7. Observability (Monitoring & Metrics)
8. Database & Migrations (Postgres Readiness)
9. Security, Secrets, and Configuration
10. Stakeholders & SMART Goals
11. Risks, Gaps, and Mitigations
12. API Usage & Production Validation
13. Lessons Learned & Potential Improvements
14. Summary

---

## 1. Baseline (Assignment 1) and Objectives
Baseline (from assignment1-milestone.md):
- Layered FastAPI service with JWT auth, gyms/customers CRUD, Alembic migrations, SQLite default, and a solid test suite.
- No Docker, no CI/CD, no observability beyond `/health`.
- Mailer existed but was limited; coverage not enforced in CI; no production deployment.

Objectives (from assignment-2-plan.md):
- Improve code quality and testing (≥70% coverage, SOLID, remove smells).
- Add CI with coverage gate, build; add CD with Docker and cloud deploy (main-only).
- Add monitoring/metrics and health checks.
- Document run/test/deploy; produce REPORT.md.
- Move toward production readiness (Postgres, secrets hygiene, observability).

---

## 2. Architecture Overview
- **Layers:** Routers (HTTP) → Services (business) → Domain (models/schemas) → DB (session/base/migrations) → Core (config, security, mailer, logging, metrics).
- **Key modules:**
  - HTTP: `app/api/routers/auth.py`, `customers.py`, `gyms.py`
  - Business: `app/services/auth.py`, `customers.py`, `gyms.py`
  - Domain: `app/domain/models.py`, `schemas.py`
  - Core: `config.py`, `security.py`, `mailer.py`, `logging.py`, `metrics.py`
  - DB: `session.py`, `base.py`, Alembic versions
  - Entrypoint: `app/main.py`
- **Config:** Env-driven (`.env`, Azure app settings); `API_PREFIX` normalized; `WEBSITES_PORT=8000` for Azure.
- **Observability:** `/health`, `/metrics` (Prometheus), Grafana dashboard JSON in `docs/monitoring/`.

---

## 3. Development Timeline (Plan vs. Execution)
- Prefix normalization: completed; routers/OAuth token URL derive from `get_api_prefix()`.
- Mailer restoration + service tests: completed; welcome mails restored with background-capable scheduling; tests added.
- Customer filtering/pagination: SQL-based age filters, limit/offset with validation.
- Observability: Prometheus middleware + `/metrics`, sample Prometheus config, Grafana dashboard JSON, metrics tests (including error path).
- Docker/CI/CD: Dockerfile, .dockerignore, GitHub Actions pipeline with coverage gate, build/push to ACR, deploy to Azure staging, migrations per env, slot swap on `main`, rollback hook.
- Postgres readiness: `asyncpg` added; docs and CI/CD migrations use Postgres URLs; guidance in README/plan/report.
- Docs: README overhauled; REPORT expanded; monitoring docs added.

---

## 4. Implemented Improvements (Assignment 2)
- **Code quality/SOLID:**
  - API prefix normalization to avoid config drift.
  - Explicit cascade handling in service layer for cross-backend consistency.
  - Mailer failures non-blocking; background scheduling supported.
  - SQL-based filtering/pagination with validation.
- **Testing:**
  - Added service-layer tests (auth/customers), metrics tests (incl. error paths), token expiry test, cascade delete test, pagination/age validation tests.
  - Coverage ~88% locally; CI gate at 70%.
- **Observability:**
  - Prometheus metrics middleware; `/metrics` + dashboard JSON; `/health` maintained.
- **Deployment:**
  - Dockerized app; CI builds/pushes to ACR; Azure Web App staging/production slots; migrations per env; swap on `main`.
  - Rollback path via workflow_dispatch.
- **Docs:**
  - README with local/prod run, API testing guide, Docker/CI/CD/monitoring/Postgres.
  - REPORT (this document) finalized.

---

## 5. Testing & Quality
- **Scope:** Integration tests (auth, gyms, customers), service tests (auth/customers), metrics tests, security (expired token), cascade deletion.
- **Fixtures:** Isolated SQLite test DB, dependency overrides, mailer stub with background scheduling.
- **Coverage:** ~87–88% locally; CI enforces 70% minimum.
- **Future test targets:** Router/deps coverage, DB/session edge cases, Postgres migration smoke tests in CI (optional).

---

## 6. CI/CD & Deployment
- **Workflow:** `.github/workflows/ci-cd.yml`
  - Test + coverage gate (`coverage report --fail-under=70`).
  - Build/push image to ACR `gymmanageracrnikoloz.azurecr.io/gymmanager:<sha>`.
  - Alembic migrations using `DATABASE_URL_STAGING` / `DATABASE_URL_PRODUCTION`.
  - Deploy to Azure Web App staging slot; swap to production on `main`.
  - Rollback via workflow_dispatch with `rollback_image`.
- **Secrets (GitHub):** ACR login server/user/pass, `AZURE_CREDENTIALS`, `AZURE_RESOURCE_GROUP`, `AZURE_WEBAPP_NAME`, DB URLs for staging/prod, app secrets (JWT, SMTP).
- **Azure app settings (slots):** `WEBSITES_PORT=8000`, `WEBSITES_CONTAINER_START_TIME_LIMIT=300`, `DATABASE_URL`, `JWT_SECRET`, `MAILER_BACKEND` (console recommended unless SMTP configured), `API_PREFIX=/api/v1`.
- **Manual deploy (if needed):** Build/push, set container on slot, set app settings, restart, validate `/health`, swap.

---

## 7. Observability (Monitoring & Metrics)
- **Metrics:** `/metrics` exposes `http_requests_total` and `http_request_duration_seconds` (labeled by method/path/status); error-path metrics covered in tests.
- **Health:** `/health` for liveness.
- **Prometheus:** Sample config at `docs/monitoring/prometheus.yml`.
- **Grafana:** Dashboard JSON at `docs/monitoring/grafana-dashboard.json` (import and bind Prometheus datasource).

---

## 8. Database & Migrations (Postgres Readiness)
- **Driver:** `asyncpg` added for Postgres.
- **URL format:** `postgresql+asyncpg://user:password@host:5432/dbname?sslmode=require`.
- **Migrations:** `alembic upgrade head` locally and in CI/CD (staging/prod URLs).
- **Recommendation:** Use Postgres for production; avoid SQLite in production; keep schema in sync via Alembic.
- **Optional:** Add docker-compose for local Postgres and CI migration smoke tests.

---

## 9. Security, Secrets, and Configuration
- **Secrets hygiene:** `.env` local only; use `.env.example` as template; keep secrets in GitHub/Azure; rotate ACR credentials if exposed.
- **Auth:** JWT HS256, bcrypt hashing; token expiry enforced; expired token test added.
- **Mailer:** Console by default; SMTP optional; failures logged and non-blocking.
- **Config:** `API_PREFIX` env-driven; CORS configured; error handlers centralized.

---

## 10. Stakeholders & SMART Goals
- **Stakeholders:** Gym owners/managers (API consumers via frontend), DevOps (deploy/CI/CD), QA (tests/coverage), Ops/SRE (monitoring), Security (secrets, auth).
- **SMART goals (delivered):**
  - Coverage ≥70% enforced in CI (achieved ~88% locally).
  - Automated build/test/deploy to Azure staging with swap to production on `main`.
  - Observability via `/metrics` and documented Prometheus/Grafana setup.
  - Dockerized service with ACR images used by Azure Web App; migrations run per environment.

---

## 11. Risks, Gaps, and Mitigations
- **Secrets exposure:** Mitigate with platform secrets, ACR credential rotation, keep `.env` untracked.
- **Deploy instability (slot swap):** Ensure correct image tags exist in ACR, staging healthy (`/health`), proper app settings, adequate startup timeout.
- **DB mismatch:** Run migrations per environment; add Postgres migration smoke tests; keep settings consistent.
- **SMTP reliability:** Use console until SMTP is confirmed; errors are logged only.
- **Coverage drift:** CI gate prevents drops; maintain tests for new features.

---

## 12. API Usage & Production Validation
- **Base URLs:** Staging `https://gymmanager-nikolozkipiani-staging.azurewebsites.net`; Production `https://gymmanager-nikolozkipiani.azurewebsites.net`.
- **Core endpoints:** `/api/v1/auth/signup`, `/api/v1/auth/login`, `/api/v1/gyms/me`, `/api/v1/customers` (with search/filters/pagination), `/health`, `/metrics`.
- **Testing in prod/staging:** Obtain token via environment-specific login; issue authenticated requests; validate `/health`; review `/metrics` for live telemetry.

---

## 13. Lessons Learned & Potential Improvements
- **Lessons:** Prefix normalization prevents config drift; explicit cascades improve cross-backend behavior; background mail scheduling needs clear testing; staging health must be validated before swaps.
- **Improvements:**
  - Add DB check to `/health` with timeout and tests.
  - Add docker-compose for local Postgres + Prometheus/Grafana.
  - Add Postgres migration smoke tests in CI (optional job).
  - Consider rate limiting/throttling; richer role-based auth if needed.
  - Add cursor-based pagination for large datasets.

---

## 14. Summary
Assignment 2 delivered a production-ready backend: SOLID-aligned layers, robust auth/customer workflows with filtering and expiry handling, mailer with background capability, observability via Prometheus, strong test suite with coverage gate, Dockerization, and CI/CD to Azure (staging/production slots, migrations). Documentation now covers local/prod setup, monitoring, deployment/rollback, and Postgres readiness. Remaining hygiene tasks are secret management and ensuring staging/production slots stay aligned with valid image tags and Postgres URLs.
