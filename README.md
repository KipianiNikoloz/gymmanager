# Gym Manager — FastAPI Backend (Assignment 2 Final)

Production-ready FastAPI backend for gym management. Provides JWT-based auth for gym owners, gym profile management, customer CRUD with filtering/pagination/expiry handling, SMTP-capable mailer, Prometheus metrics, and CI/CD to Azure with staging/production slots. This README is the definitive guide to replicate, run, test, deploy, and monitor the service.

## Table of Contents
- Project Snapshot
- Architecture & Key Modules
- Local Setup & Replication
- Environment Variables
- Database (SQLite vs Postgres)
- Migrations (Alembic)
- Testing & Coverage
- API Testing Guide (local, staging, production)
- Docker
- CI/CD (GitHub Actions → Azure)
- Deploy & Rollback (Azure)
- Monitoring (Prometheus/Grafana)
- Production URLs & Usage
- Secrets & Configuration
- Troubleshooting & Known Issues

## Project Snapshot
- Stack: FastAPI (async), SQLAlchemy 2.0 async, Alembic, Pydantic v2, JWT (HS256), passlib[bcrypt], Prometheus metrics, Docker.
- Quality: Tests with coverage gate (70% in CI); recent local coverage ~88%.
- Deployment: Azure Web App for Containers (staging + production slots), ACR for images, GitHub Actions for CI/CD with migrations per environment.

## Architecture & Key Modules
- Routers: `app/api/routers/auth.py`, `customers.py`, `gyms.py` (thin HTTP, `API_PREFIX`-aware).
- Services: `app/services/auth.py`, `customers.py`, `gyms.py` (business logic, mail, filtering, deletion).
- Domain: `app/domain/models.py`, `schemas.py` (ORM models + Pydantic schemas).
- Core: `app/core/config.py` (env settings/prefix), `security.py` (JWT/password), `mailer.py` (console/SMTP), `logging.py`, `metrics.py` (Prometheus).
- DB: `app/db/session.py`, `base.py`; migrations in `alembic/versions`.
- Entrypoint: `app/main.py` (CORS, error handlers, health, metrics, router wiring).

## Local Setup & Replication
Prereqs: Python 3.11+, Git, (optional) Docker.
```bash
git clone <repo-url> gymmanager && cd gymmanager
python -m venv venv
./venv/Scripts/activate  # Windows PowerShell
# source venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
cp .env.example .env
# edit .env: set JWT_SECRET, DATABASE_URL (sqlite or Postgres)
alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
Health: http://127.0.0.1:8000/health  
Docs: http://127.0.0.1:8000/docs  
Metrics: http://127.0.0.1:8000/metrics

## Environment Variables (core)
- `JWT_SECRET` (required)
- `JWT_ALGORITHM` (default HS256)
- `ACCESS_TOKEN_EXPIRE_MINUTES` (default 60)
- `DATABASE_URL` (e.g., `sqlite+aiosqlite:///./app.db` or `postgresql+asyncpg://user:pass@host:5432/db?sslmode=require`)
- `MAILER_BACKEND` (`console` recommended unless SMTP is configured)
- SMTP: `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_FROM_EMAIL`, `SMTP_USE_TLS`, `SMTP_USE_SSL`
- `API_PREFIX` (default `/api/v1`)
- Azure app settings: `WEBSITES_PORT=8000`, `WEBSITES_CONTAINER_START_TIME_LIMIT=300`

## Database (SQLite vs Postgres)
- Dev/tests: SQLite (`sqlite+aiosqlite:///./app.db` or `./test.db` via overrides).
- Production: Postgres with `asyncpg`. Example:  
  `DATABASE_URL=postgresql+asyncpg://user:password@host:5432/dbname?sslmode=require`
- Ensure DB exists; run migrations after changing DB.

## Migrations (Alembic)
```bash
alembic upgrade head
```
Runs against `DATABASE_URL`. For CI/CD, migrations run per environment (staging/prod) using `DATABASE_URL_STAGING` / `DATABASE_URL_PRODUCTION`.

## Testing & Coverage
```bash
pytest --cov=app --cov-report=term-missing --cov-report=xml
```
- Uses isolated SQLite (`./test.db`) with dependency overrides.
- Mailer is stubbed; no external SMTP required.
- CI enforces fail-under 70% (recent local ~88%).
- Added tests: service-layer auth/customers, metrics (incl. error path), token expiry, cascade delete, pagination/age validation.

## API Testing Guide
### Local (default base http://127.0.0.1:8000, API_PREFIX=/api/v1)
1) Sign up:
```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"name":"Demo Gym","email":"owner@example.com","password":"Password123","monthly_fee_cents":7500,"currency":"USD"}'
```
2) Login (get token):
```bash
TOKEN=$(curl -s -X POST http://127.0.0.1:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d 'username=owner@example.com&password=Password123' | jq -r .access_token)
```
3) Authenticated calls (example list customers):
```bash
curl -H "Authorization: Bearer $TOKEN" \
  "http://127.0.0.1:8000/api/v1/customers?search=alex&active=true&limit=50&offset=0&min_age=18&max_age=80"
```
4) Health/Metrics: `GET /health`, `GET /metrics`.

### Staging / Production
- Staging base: `https://gymmanager-nikolozkipiani-staging.azurewebsites.net`
- Production base: `https://gymmanager-nikolozkipiani.azurewebsites.net`
- Repeat the above requests with the appropriate base URL. Obtain tokens from the same environment.
- Validate `/health` and inspect `/metrics` for live telemetry.

### Notes
- Adjust paths if `API_PREFIX` changes.
- Pagination/filters: `limit`, `offset`, `search`, `first_name`, `last_name`, `email`, `active`, `min_age`, `max_age`.
- Errors: 400 on invalid age ranges; 422 on out-of-bounds pagination; 401/404 for auth/access issues.

## Docker
```bash
docker build -t gymmanager:local .
docker run -p 8000:8000 --env-file .env gymmanager:local
```
Manual prod push:
```bash
docker build -t gymmanageracrnikoloz.azurecr.io/gymmanager:latest .
docker push gymmanageracrnikoloz.azurecr.io/gymmanager:latest
```

## CI/CD (GitHub Actions → Azure)
- File: `.github/workflows/ci-cd.yml`
- Steps: test + coverage gate (70%), build/push to ACR, run Alembic migrations (staging/prod), deploy to staging slot, swap to production on `main`, rollback via workflow_dispatch.
- Required secrets:
  - `AZURE_CREDENTIALS`, `AZURE_RESOURCE_GROUP`, `AZURE_WEBAPP_NAME`
  - `AZURE_REGISTRY_LOGIN_SERVER`, `AZURE_REGISTRY_USERNAME`, `AZURE_REGISTRY_PASSWORD`
  - `DATABASE_URL_STAGING`, `DATABASE_URL_PRODUCTION`
  - `JWT_SECRET`, optional `API_PREFIX`, SMTP settings
- Azure app settings (slots): `WEBSITES_PORT=8000`, `WEBSITES_CONTAINER_START_TIME_LIMIT=300`, DB URL, JWT, MAILER_BACKEND (console recommended unless SMTP is configured).

## Deploy & Rollback (Azure)
1) Ensure image tag exists in ACR (CI or manual build/push).
2) Configure staging slot container to that tag + registry creds; set app settings.
3) Restart staging; verify `/health`.
4) Swap staging → production (CI on `main` does this automatically).
5) Rollback: trigger workflow_dispatch with `rollback_image=<acr>/gymmanager:<tag>`.

## Monitoring (Prometheus/Grafana)
- Metrics: `/metrics`; Health: `/health`.
- Prometheus config: `docs/monitoring/prometheus.yml`.
- Grafana: import `docs/monitoring/grafana-dashboard.json` (panels for request totals, p95 latency, error rate).

## Postgres (production)
- Use `postgresql+asyncpg://user:password@host:5432/dbname?sslmode=require`.
- Run `alembic upgrade head` after configuring.
- Set DB URL in staging and production slots; avoid SQLite in production.

## Production URLs & Usage
- Staging: `https://gymmanager-nikolozkipiani-staging.azurewebsites.net`
- Production: `https://gymmanager-nikolozkipiani.azurewebsites.net`
- Core endpoints: `/api/v1/auth/signup`, `/api/v1/auth/login`, `/api/v1/gyms/me`, `/api/v1/customers`
- Health: `/health`; Metrics: `/metrics`

## Secrets & Configuration
- Do NOT commit real secrets. Use `.env.example` locally; GitHub/Azure secrets for CI/runtime.
- Rotate ACR credentials if exposed. Prefer `MAILER_BACKEND=console` unless SMTP is required.

## Troubleshooting & Known Issues
- 401/404: Check bearer token and ownership scoping.
- Alembic: Confirm `DATABASE_URL` and UTF-8 `alembic.ini`.
- Azure container start: set `WEBSITES_PORT=8000`, correct image tag, use console mailer, check logs (`az webapp log tail`).
- Slow slot swap: ensure staging is healthy (`/health`), image pull is fast (ACR same region), and startup timeout is set.
