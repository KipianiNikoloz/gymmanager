# FastAPI Gym Manager

A production-ready FastAPI backend tailored for gym management. The service follows a layered architecture so you can plug in a modern frontend (e.g. SvelteKit) and grow features without tangling API logic.

## Getting Started

1. Copy the example environment file and adjust credentials as needed:
   ```bash
   cp .env.example .env
   ```
   Set `CORS_ORIGINS` to your frontend origins (comma-separated). For local Svelte development the default `http://localhost:5173` is ready to go.
2. Install dependencies inside your virtual environment:
   ```bash
   uv pip install -r requirements.txt
   ```
3. Apply database migrations:
   ```bash
   alembic upgrade head
   ```
4. Start the development server:
   ```bash
   uvicorn app.main:app --reload
   ```
5. Visit `http://127.0.0.1:8000/health` to confirm the API is running.

## Project Structure

- `app/core` – configuration, logging, mail adapters, and security helpers
- `app/api` – thin FastAPI routers that delegate to services (prefixed under `/api/v1`)
- `app/services` – business logic for auth, gyms, and customers
- `app/db` – SQLAlchemy engine/session helpers and declarative base
- `app/domain` – SQLAlchemy models and Pydantic schemas
- `alembic` – migration environment for database evolution
- `tests` – pytest suite with async fixtures and HTTPX-based integration tests

## API Quick Reference

Authenticate, then call secured endpoints with the bearer token:
```bash
# create a gym
curl -X POST http://127.0.0.1:8000/api/v1/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"name":"Demo Gym","email":"owner@example.com","password":"Password123","monthly_fee_cents":7500,"currency":"USD"}'

# login and grab the token
token=$(curl -s -X POST http://127.0.0.1:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d 'username=owner@example.com&password=Password123' | jq -r .access_token)

# list customers with filters
curl http://127.0.0.1:8000/api/v1/customers?search=alex -H "Authorization: Bearer $token"
```

All endpoints return consistent JSON error payloads (`{"detail": ..., "status_code": ...}`) and server-side errors are logged through the centralized logging config.

## Frontend Integration

- CORS is driven by `CORS_ORIGINS`, so point it at your Svelte dev server (default `http://localhost:5173`).
- The `/api/v1` namespace keeps REST routing predictable for the frontend.
- Responses use JSON exclusively; authentication relies on bearer tokens stored client-side (prefer `Authorization` headers in your fetch logic).

## Testing & Quality

Run the full async test suite (mailer interactions are stubbed):
```bash
pytest -q
```
Check coverage when needed:
```bash
pytest --cov=app --cov-report=term-missing
```

## Logging & Monitoring

Logging is configured via `app/core/logging.py` and enabled automatically when the app starts. Tune `LOGGING_CONFIG` or wire in structured logging before deploying.

## Next Steps

Stage 7 finalizes production polish. From here you can:
- Connect a Svelte frontend and start consuming the REST endpoints
- Swap the console mail adapter for SMTP by switching `MAILER_BACKEND`
- Extend services with additional business workflows (billing, analytics, etc.)
