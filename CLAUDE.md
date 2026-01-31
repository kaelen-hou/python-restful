# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
make install          # Install production dependencies
make dev              # Install dev dependencies + pre-commit hooks
make test             # Run tests with coverage
make lint             # Check code with ruff
make format           # Auto-format code
make run              # Start dev server (localhost:8000)

# Run single test
python -m pytest tests/test_tasks.py::TestCreateTask::test_create_task_valid -v

# Database migrations
alembic revision --autogenerate -m "description"
alembic upgrade head
```

## Architecture

FastAPI REST API for task management with SQLite storage, JWT auth, and rate limiting.

```
app/
├── main.py           # FastAPI app, middleware, exception handlers
├── config.py         # Pydantic settings (loads from .env)
├── models.py         # Pydantic schemas (TaskCreate, TaskUpdate, TaskResponse)
├── database.py       # SQLAlchemy engine, session, TaskDB model
├── crud.py           # Database operations
├── auth.py           # JWT auth (access + refresh tokens)
├── rate_limit.py     # Slowapi rate limiter instance
├── logging_config.py # JSON logging with request ID
└── routers/
    └── v1.py         # Versioned API routes (/api/v1/*)
```

**Request flow:** Middleware (logging, CORS) → Rate limiter → Route (v1.py) → Auth check → CRUD → Response

## Conventions

- Use `X | None` syntax for optional types (Python 3.10+), not `Optional[X]`
- Use timezone-aware datetimes: `datetime.now(UTC)` via `utc_now()` in database.py
- FastAPI `Depends()` in function defaults is allowed (B008 ignored in ruff)
- All API routes under `/api/v1/` prefix for versioning
- Tests reset rate limiter via `limiter.reset()` in fixtures
- Config via pydantic-settings, loaded from `.env` file
