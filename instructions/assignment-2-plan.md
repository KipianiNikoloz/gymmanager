# Assignment 2 Plan

**Date:** 2025-11-26  
**Repo/Branch analyzed:** gymmanager / feature/readme  
**Goal:** Deliver all Assignment 2 requirements with production-quality standards.

---

## 0. Current Baseline Summary (from Assignment 1)
- App purpose and primary user flows: FastAPI backend for gym owners to sign up/login, manage their gym profile, and CRUD customers with filtering/auto-deactivation on expired memberships.
- Architecture overview: Layered FastAPI app — routers (`app/api/routers/*.py`) thin over services (`app/services/*.py`), domain models/schemas (`app/domain/*.py`), DB infrastructure (`app/db/session.py`, `app/db/base.py`), core utilities (config/logging/mailer/security in `app/core/*`). Alembic migrations in `alembic/versions/*`.
- Tech stack + tooling: Python 3.11+, FastAPI, SQLAlchemy async, Alembic, Pydantic v2, PyJWT, passlib[bcrypt], httpx, pytest + pytest-asyncio/pytest-cov; SQLite default. No Docker/CI today.
- Current test status + existing CI/CD/monitoring: Async integration-style tests in `tests/` for auth/gyms/customers/mailer; no CI configs; no Dockerfile; no metrics; `/health` already exists (`app/main.py`); coverage data not retained (coverage file removed in commit a28b65d).

---

## 1. Requirements-to-Gaps Matrix
### 1.1 Code Quality & Testing
- **Requirement**: Refactor to remove code smells and follow SOLID; add unit+integration tests; ≥70% coverage; include test report.
- **Current status:** 🟡 (tests exist; SOLID mostly followed; coverage/report missing).
- **Evidence:** Services split (app/services/*); tests (tests/*.py); coverage file deleted (a28b65d); no reports in repo.
- **Gap to close:** Add targeted unit tests for services and utilities, expand integration tests, generate coverage report >=70% committed; add test report artifact; address hard-coded `/api/v1` in routers vs `api_prefix`; tidy shared concerns (mailer use on signup).

### 1.2 Continuous Integration (CI)
- **Requirement**: Pipeline runs tests, coverage gate ≥70%, builds app; fails on test/coverage failure.
- **Current status:** 🔴
- **Evidence:** No `.github/workflows` or other CI configs.
- **Gap to close:** Add CI workflow (e.g., GitHub Actions) with test+coverage gate and build stage.

### 1.3 Deployment Automation (CD)
- **Requirement**: Dockerize app; add deployment step to cloud; main-only deploy with secrets.
- **Current status:** 🔴
- **Evidence:** No Dockerfile/.dockerignore; no deploy scripts/configs.
- **Gap to close:** Create Dockerfile/.dockerignore; choose cloud target and add deploy job triggered on main.

### 1.4 Monitoring & Health Checks
- **Requirement**: `/health`; metrics (request count, latency, errors); minimal Prometheus/Grafana setup/config/screenshots.
- **Current status:** 🟡
- **Evidence:** `/health` in `app/main.py`; no metrics or Prometheus config.
- **Gap to close:** Add metrics middleware/exporter; provide Prometheus scrape config and sample dashboard/screenshot location.

### 1.5 Documentation
- **Requirement**: Update README with run/test/deploy; add REPORT.md (~5–6 pages) summarizing improvements.
- **Current status:** 🟡
- **Evidence:** README.md current (Assignment 1 focus); no REPORT.md.
- **Gap to close:** Expand README with CI/CD/Docker/monitoring instructions; add REPORT.md with required sections and coverage results.

---

## 2. Work Plan (Prioritized Roadmap)
1. **Refine settings and route prefix alignment**  
   - **Requirement(s):** Code Quality  
   - **Why:** Prevent config drift; adhere to clean architecture and SRP.  
   - **Implementation details:** Use `settings.api_prefix` in router registration and OAuth2 `tokenUrl` (`app/api/deps.py`, `app/api/routers/*.py`, `app/main.py`).  
   - **Tests:** Adjust existing integration tests to use prefix; add unit test for prefix application.  
   - **DoD:** All routes respect configurable prefix; tests pass. ✅ (completed)

2. **Service-layer unit tests & mailer behavior restoration**  
   - **Requirement(s):** Code Quality & Testing  
   - **Why:** Increase coverage; restore expected signup email; solidify business logic.  
   - **Implementation details:**  
     - Reintroduce welcome email in `app/services/auth.signup_gym` (reuse `app/core/mailer.get_mailer`).  
     - Add unit tests for `services/auth.py` and `services/customers.py` (age filter, auto-deactivation, welcome email dispatch).  
   - **Tests:** New unit tests with stubbed mailer; update fixtures if needed.  
   - **DoD:** Signup sends mail; tests cover behaviors; coverage increases. ✅

3. **Metrics and health hardening**  
   - **Requirement(s):** Monitoring & Health Checks  
   - **Why:** Observability requirement; production readiness.  
   - **Implementation details:**  
      - Add middleware exposing request count/latency/error metrics (e.g., `prometheus_client` with ASGI middleware) in `app/main.py` or new `app/core/metrics.py`.  
      - Expose `/metrics` endpoint; extend `/health` to include DB connectivity check (lightweight).  
    - **Tests:** Integration tests hitting `/metrics` (parse key metrics) and `/health` (status, optional DB check mocked).  
    - **DoD:** Metrics endpoint present; health returns 200 with expected shape; tests pass; Grafana dashboard artifact present. ✅

4. **Dockerization**  
   - **Requirement(s):** Deployment Automation (CD)  
   - **Why:** Enable reproducible builds and deploy.  
   - **Implementation details:**  
     - Create multi-stage Dockerfile (python:3.11-slim, install deps, non-root user, run via uvicorn).  
     - Add `.dockerignore` (venv, __pycache__, tests, .git, *.db, *.coverage).  
   - **Tests:** Manual `docker build` and `docker run` command documented; optional smoke test in CI build stage.  
    - **DoD:** Image builds locally; app serves `/health` in container. ✅

5. **CI pipeline with coverage gate**  
   - **Requirement(s):** CI, Testing  
   - **Why:** Automate quality gates.  
   - **Implementation details:**  
     - GitHub Actions workflow `.github/workflows/ci.yml`: checkout, setup Python 3.11, cache pip, install deps, run `pytest --cov=app --cov-report=term --cov-report=xml`, fail if coverage <70% (use `coverage xml` + `coverage report --fail-under=70`), build docker image.  
   - **Tests:** Pipeline itself; ensure coverage command passes locally.  
   - **DoD:** CI fails on test/coverage issues; docker build stage succeeds. 🟡 (workflow added; pending validation with secrets)

6. **CD deploy job (main-only)**  
   - **Requirement(s):** CD  
   - **Why:** Automated deployment per assignment.  
   - **Implementation details:**  
     - Extend CI workflow with deploy job gated on `main` branch.  
     - Choose target (e.g., Render or Fly.io): include config file (`render.yaml` or `fly.toml`) and use registry push if needed.  
     - Use secrets for env vars (JWT_SECRET, DATABASE_URL, SMTP_*).  
   - **Tests:** Deploy job dry-run locally if possible; document manual verification.  
   - **DoD:** Deploy job defined, main-only, uses secrets; docs updated.

7. **Prometheus/Grafana minimal setup**  
   - **Requirement(s):** Monitoring  
   - **Why:** Meet metrics visibility requirement.  
   - **Implementation details:**  
     - Add `prometheus.yml` with scrape target pointing to app `/metrics`.  
     - Provide Grafana dashboard JSON or screenshot placeholder path (`docs/monitoring/`).  
   - **Tests:** Validate metrics endpoint scrape locally (curl + prometheus_client text).  
   - **DoD:** Config present; instructions/screenshots captured.

8. **Test report and coverage artifacts**  
   - **Requirement(s):** Testing, Documentation  
   - **Why:** Evidence for coverage threshold.  
   - **Implementation details:**  
     - Generate `coverage.xml` and `htmlcov/` in CI; save summary into `reports/test-report.md` or similar.  
     - Ensure `.gitignore` excludes heavy artifacts but include summary report.  
   - **Tests:** N/A (process output).  
   - **DoD:** Report file in repo with coverage number (>=70%).

9. **Documentation updates & REPORT.md**  
   - **Requirement(s):** Documentation, Deployment, Monitoring  
   - **Why:** Usability and audit trail.  
   - **Implementation details:**  
     - README: add sections for docker build/run, CI/CD, metrics/Prometheus, running tests with coverage, deployment steps.  
     - REPORT.md (~5–6 pages): describe refactors, SOLID alignment, test strategy + coverage, CI/CD design, monitoring setup, results/known gaps; include SMART goals and a brief stakeholder analysis (per feedback).  
     - Document database migration plans (SQLite → Postgres) for deployment environments.  
   - **Tests:** N/A.  
   - **DoD:** README and REPORT.md committed; instructions accurate.

10. **Database migration readiness (SQLite → Postgres)**  
    - **Requirement(s):** Deployment/Production readiness  
    - **Why:** Production deployments should use Postgres; ensure smooth transition from dev SQLite.  
    - **Implementation details:**  
      - Add ENV guidance in README for Postgres `DATABASE_URL` (e.g., `postgresql+asyncpg://user:pass@host:5432/db`).  
      - Confirm Alembic migrations are compatible with Postgres; adjust types if needed.  
      - Provide a simple migration checklist (provision DB, run `alembic upgrade head`, update secrets/CI/CD to point to Postgres).  
      - (Optional) Add docker-compose snippet for local Postgres if needed.  
    - **Tests:** Smoke test against a Postgres instance (can be via docker-compose locally).  
    - **DoD:** README and REPORT describe Postgres setup; migrations verified to run on Postgres. 🟡 (env guidance added; pending Postgres smoke test)

---

## 3. CI/CD Design
- Platform: GitHub Actions (native, free for public, easy secrets management).
- Pipeline stages:  
  1) Lint/type (optional if tools added later), 2) Test with coverage, 3) Coverage gate (`coverage report --fail-under=70`), 4) Build (docker), 5) Deploy (main-only).
- Coverage enforcement: `coverage report --fail-under=70` and/or `pytest --cov-fail-under=70`.
- Branch/trigger rules: On pull_request (tests+coverage+build, no deploy), on push to main (tests+coverage+build+deploy).
- Secrets: Stored in GitHub Actions secrets (JWT_SECRET, DATABASE_URL, SMTP creds, cloud deploy token/registry). Referenced via `env:` in workflow.
- File path: `.github/workflows/ci.yml` (single workflow with conditional deploy).

---

## 4. Dockerization & Deployment
- Dockerfile: Multi-stage (builder installs deps with `pip install --no-cache-dir -r requirements.txt`; final image copies app, creates non-root user, sets `UVICORN_WORKERS`, exposes 8000, entrypoint `uvicorn app.main:app --host 0.0.0.0 --port 8000`).
- .dockerignore: `.git`, `venv/`, `__pycache__/`, `*.pyc`, `*.db`, `.coverage`, `htmlcov/`, `tests/`, `*.log`.
- Local run: `docker build -t gymmanager:local .` then `docker run -p 8000:8000 --env-file .env gymmanager:local`.
- Cloud target: Recommend Render (simple Docker deploy) or Fly.io; include `render.yaml` or `fly.toml` with service/port 8000 and env vars; deploy step pushes image and triggers deploy on main.
- Rollback: Rely on platform releases (Render/Fly built-in rollback); keep previous image tags; document manual rollback command.

---

## 5. Monitoring & Health
- `/health` spec: `GET /health` returns `{ "status": "ok", "db": "ok" }` (db check best-effort with timeout); remains lightweight.
- Metrics spec:  
  - `http_requests_total` (counter) labeled by method, path template, status.  
  - `http_request_duration_seconds` (histogram/summary) same labels.  
  - `http_requests_in_progress` (gauge) optional.  
  - Error counter derived via status >=500.  
- Implementation: Add Prometheus middleware/exposer via `prometheus_client` or `starlette_exporter` in `app/main.py` (prefer dedicated `app/core/metrics.py` to register). Expose `/metrics` unauthenticated text format.
- Prometheus/Grafana setup:  
  - `prometheus.yml` scraping `http://app:8000/metrics` (or localhost for dev).  
  - Store Grafana dashboard JSON or screenshots under `docs/monitoring/` (include sample panels for request rate/latency/errors).  
  - Document docker-compose snippet if needed for local Prometheus+Grafana.

---

## 6. Documentation & Report Plan
- README updates: prerequisites; run (venv and Docker); migrations; testing with coverage; interpreting coverage gate; CI/CD behavior; metrics/Prometheus usage; deploy steps and required secrets.
- REPORT.md outline:  
  - Overview and objectives.  
  - Refactors and SOLID alignment (prefix handling, mailer restoration, service tests).  
  - Test strategy, coverage numbers, summary of added tests, link to test report.  
  - CI/CD design and outcomes.  
  - Dockerization and deployment target.  
  - Monitoring/metrics design and how to consume them.  
  - Results, risks, next steps.  
- Screenshots/configs: place under `docs/monitoring/` or `docs/screenshots/` (reference in README/REPORT).

---

## 7. Risk Log & Mitigations
- Refactor breakage (prefix change, mailer): Mitigate with expanded integration tests and unit tests; staged commits.
- Coverage gate failures: Run locally before push; incremental testing; allow dry-run pipeline.
- Deployment failures: Use main-only deploy; keep manual trigger override; document rollback.
- Metrics overhead: Use lightweight middleware; sample histograms sensibly; allow disable via env if needed.
- Secret handling: Ensure `.env` ignored; use GitHub secrets; document rotation.

---

## 8. Final “Done” Checklist
- All Assignment 2 requirements implemented and validated.
- Tests pass locally and in CI; coverage ≥70% with report checked in.
- CI pipeline enforces tests+coverage, builds docker image; deploy job gated to main with secrets configured.
- Docker image builds and runs; cloud deploy config present; main branch auto-deploys.
- `/health` and `/metrics` live and covered by tests; Prometheus config and Grafana artifact provided.
- README updated with run/test/deploy/monitor instructions; REPORT.md completed (5–6 pages) with evidence and coverage.
- No secrets committed; `.env` ignored; configs parameterized.
- Code adheres to SOLID, clear layering, and cleanliness; self-review completed.
