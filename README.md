# FastAPI Gym Manager

Gym management software made for in-person gym management. Suited for gym owners

## Getting Started

1. Copy the example environment file and adjust credentials as needed:
   ```bash
   cp .env.example .env
   ```
2. Install dependencies (inside your virtual environment):
   ```bash
   uv pip install fastapi uvicorn[standard] sqlalchemy[asyncio] aiosqlite \
   pydantic pydantic-settings passlib[bcrypt] pyjwt alembic python-multipart \
   httpx pytest
   ```
3. Start the development server:
   ```bash
   uvicorn app.main:app --reload
   ```
4. Visit the health check at `http://127.0.0.1:8000/health` to confirm the API is running.

## Project Structure

The codebase follows a layered, feature-oriented layout:

- `app/core` – application-wide configuration and shared utilities
- `app/api` – API routers grouped by feature and versioned under `/api/v1`
- `app/db` – database engine, sessions, and migrations
- `app/domain` – business models and data schemas
- `alembic` – migration environment for database evolution

## Frontend Integration

CORS is preconfigured to allow requests from `http://localhost:5173`, enabling seamless development with a Vite/React frontend. Later stages will expose authenticated REST endpoints so a React or Next.js client can consume the API securely.