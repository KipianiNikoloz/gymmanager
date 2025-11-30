# Gym Manager — FastAPI Backend

This repository contains a production‑ready FastAPI backend for gym management, built with:
- FastAPI (async)
- SQLAlchemy 2.0 (async) + Alembic
- Pydantic v2
- JWT authentication (HS256)
- Layered architecture (routers → services → domain/db → core)

The instructions below reproduce the backend from scratch, run it locally, and verify all endpoints and tests.


## 0) Prerequisites

- OS: Windows, macOS, or Linux
- Python: 3.11+
- Git (recommended)

Windows note: use PowerShell for the commands shown.


## 1) Clone the repository

```powershell
# from any folder
git clone <this-repo-url> gymmanager
cd gymmanager
```

Key layout:
- `app/` — application code
  - `core/` (config, security, mailer, logging)
  - `api/routers/` (auth, gyms, customers — thin HTTP layer)
  - `services/` (business logic)
  - `db/` (SQLAlchemy base + async session)
  - `domain/` (ORM models + Pydantic schemas)
- `alembic/` — migration environment
- `tests/` — async pytest suite


## 2) Backend — environment & dependencies

Create a virtual environment and install requirements:

```powershell
python -m venv venv
./venv/Scripts/Activate.ps1
pip install -r requirements.txt
```

Create a `.env` file:

```powershell
Copy-Item .env.example .env
```

Edit `.env` if needed (defaults work):
```
JWT_SECRET=changeme
DATABASE_URL=sqlite+aiosqlite:///./app.db
```
Notes
- Change `DATABASE_URL` to your DB of choice later (e.g., Postgres).


## 3) Backend — initialize database (Alembic)

```powershell
alembic upgrade head
```
This applies all migrations and creates `gyms` and `customers`.

Troubleshooting
- If `alembic` not found: `pip install alembic` (already in requirements) and ensure the venv is active.


## 4) Run the API

```powershell
uvicorn app.main:app --reload
```

Health check:
```
GET http://127.0.0.1:8000/health -> {"status":"ok"}
```

OpenAPI docs:
- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc


## 5) Quick API walkthrough (curl)

All examples assume the default `API_PREFIX=/api/v1`. If you change `API_PREFIX`, update the paths below accordingly.

Sign up a gym:
```powershell
curl -s -X POST http://127.0.0.1:8000/api/v1/auth/signup ^
  -H "Content-Type: application/json" ^
  -d '{
    "name": "Downtown Gym",
    "email": "owner@example.com",
    "password": "Password123",
    "monthly_fee_cents": 7500,
    "currency": "USD"
  }'
```

Login (OAuth2 form; username = email). Copy `access_token` from the JSON response:
```bash
curl -s -X POST http://127.0.0.1:8000/api/v1/auth/login \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'username=owner@example.com&password=Password123'
```

Current gym:
```powershell
curl -H "Authorization: Bearer <TOKEN>" http://127.0.0.1:8000/api/v1/gyms/me
```

Create a customer:
```powershell
curl -s -X POST http://127.0.0.1:8000/api/v1/customers ^
  -H "Authorization: Bearer <TOKEN>" ^
  -H "Content-Type: application/json" ^
  -d '{
    "first_name": "Alex",
    "last_name": "Doe",
    "email": "alex@example.com",
    "active": true
  }'
```

List with filters:
```powershell
curl -s -H "Authorization: Bearer <TOKEN>" ^
  "http://127.0.0.1:8000/api/v1/customers?search=alex&active=true&limit=50&offset=0&min_age=18&max_age=80"
```

Update (activate/deactivate/edit):
```powershell
curl -s -X PATCH http://127.0.0.1:8000/api/v1/customers/1 ^
  -H "Authorization: Bearer <TOKEN>" ^
  -H "Content-Type: application/json" ^
  -d '{"active": false}'
```

Delete:
```powershell
curl -s -X DELETE http://127.0.0.1:8000/api/v1/customers/1 ^
  -H "Authorization: Bearer <TOKEN>"
```

Delete gym (cascades customers):
```powershell
curl -s -X DELETE http://127.0.0.1:8000/api/v1/gyms/me ^
  -H "Authorization: Bearer <TOKEN>"
```


## 6) Tests & coverage

Run tests:
```powershell
pytest -q
```

Coverage:
```powershell
pytest --cov=app --cov-report=term-missing
```

Notes
- Tests use an isolated SQLite DB (`./test.db`) and override `get_db` so they don’t affect your local data.
- Mail is stubbed in tests; no external SMTP required. If you see SMTP errors, ensure tests use the provided fixtures.
- Service-level tests are included; aim for ≥70% coverage (enforced in CI in upcoming steps). Recent local run: ~87% (see `coverage.xml` when generated).


## 7) Configuration reference

- `JWT_SECRET` — secret key for HMAC JWT
- `JWT_ALGORITHM` — default `HS256`
- `ACCESS_TOKEN_EXPIRE_MINUTES` — e.g., `60`
- `DATABASE_URL` — e.g., `sqlite+aiosqlite:///./app.db`
- Mailer (optional):
  - `MAILER_BACKEND` — `console` (default) or `smtp`
  - `MAILER_RATE_LIMIT_SECONDS`, `MAILER_MAX_RETRIES`, `MAILER_RETRY_DELAY_SECONDS`
  - `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_USE_TLS`, `SMTP_USE_SSL`, `SMTP_FROM_EMAIL`


## 8) Troubleshooting

- Alembic cannot read config / encoding issues
  - Ensure `alembic.ini` is UTF‑8 (without BOM). Recreate if necessary.

- bcrypt 72‑byte password constraint
  - Passwords are validated (≤72 chars). Avoid extremely long inputs.

- 401 Unauthorized after login
  - Ensure you’re sending `Authorization: Bearer <token>` on every request to protected routes.


## 9) Next steps

- Switch to Postgres for production; set `DATABASE_URL` accordingly.
- Add CI (pytest + coverage) and CD (migrations on deploy).
- Replace console mailer with SMTP (set `MAILER_BACKEND=smtp` + SMTP_* vars).
- Extend services (e.g., billing, analytics) while keeping routers thin.

---

Happy building!
