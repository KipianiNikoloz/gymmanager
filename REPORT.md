# REPORT — Assignment 2 Progress

## 1. Overview
- Scope: Improve code quality, testing, automation, deployment, and monitoring for the FastAPI gym manager backend.
- Repo/branch: gymmanager / feature/readme.
- Current sprint focus: configurable API prefix refactor, restore signup mailer behavior, documentation alignment, and testing assessment.

## 2. Refactors & SOLID Alignment
- API prefix normalization: routers and OAuth token URL now derive from `app/core/config.get_api_prefix()`, eliminating hard-coded `/api/v1` paths and reducing config drift (files: `app/api/deps.py`, `app/api/routers/auth.py`, `app/api/routers/customers.py`, `app/api/routers/gyms.py`, tests updated accordingly).
- Config utility: added `get_api_prefix()` to centralize prefix normalization (file: `app/core/config.py`).
- Service responsibility: gym signup service now handles welcome mail dispatch with error logging while keeping HTTP layer thin (file: `app/services/auth.py`).
- Remaining refactor needs:
  - Age filtering currently done in Python post-query; should move to SQL and add pagination.
  - Metrics/monitoring and Docker/CI/CD still absent (planned).
  - README examples still default to /api/v1 but now documented as configurable via `API_PREFIX`.

## 3. Testing Status & Coverage
- Test types present: integration-style tests using httpx + ASGI transport for auth, gyms, customers; mailer behavior stubbed; service-layer unit tests added.
- New coverage: signup mailer behavior asserted (`tests/test_auth.py`); service-layer coverage added (`tests/test_services.py`) for signup mailer, duplicate rejection, auth success/failure, age filtering, and auto-deactivation.
- Coverage level: last run reported ~87% (see `coverage.xml`); coverage gate (>=70%) will be enforced in CI later.
- Gaps:
  - No metrics/health tests yet.
  - Age filtering still computed in Python (needs SQL/pagination).
  - No e2e/system tests with Docker.

## 4. CI/CD & Automation
- Current state: No GitHub Actions or other CI present; no coverage gate; no build/deploy jobs.
- Plan: Add `.github/workflows/ci.yml` with test + coverage fail-under 70%, docker build, and main-only deploy to chosen cloud (Render/Fly). Secrets to be stored in platform secrets.
- Deployment: Dockerfile and `.dockerignore` not yet added; target platform TBD (recommend Render/Fly).

## 5. Monitoring & Health
- Existing: `/health` endpoint only.
- Missing: `/metrics`, Prometheus scrape config, Grafana artifact/screenshot. To be added with Prometheus client middleware and configs.

## 6. Documentation
- README updated to note configurable `API_PREFIX`; still needs sections for Docker, CI/CD, monitoring, and updated run/test/deploy instructions after future tasks.
- REPORT.md (this document) captures current progress; will be extended with coverage results, CI/CD details, monitoring setup, deployment notes, SMART goals, and a brief stakeholder analysis as they land.

## 7. Risks & Actions
- Secrets in repo: `.env` contains real-looking SMTP creds; should be rotated and excluded from commits, relying on `.env.example` + platform secrets.
- Config drift: Resolved for API prefix; ensure README and examples stay synchronized.
- Testing debt: Need unit coverage for services and new metrics; ensure coverage >=70% before CI gate.
- Observability/deploy debt: Metrics, Docker, and CI/CD still pending; prioritize next sprints.

## 8. Next Steps (Immediate)
1) Re-run coverage after SQL age filtering + pagination; capture coverage summary.
2) Introduce Dockerfile + .dockerignore; add GitHub Actions workflow with coverage gate and build.
3) Add metrics middleware and `/metrics`; provide `prometheus.yml` and Grafana artifact.
4) Update README with run/test/deploy/monitor instructions; include coverage report summary file once generated.
5) Remove/rotate any committed secrets; rely on `.env.example` + platform secrets.
