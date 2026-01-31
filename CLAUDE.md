# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
make install          # Install production dependencies
make dev              # Install dev dependencies + pre-commit hooks
make test             # Run all tests
make lint             # Check code with ruff
make format           # Auto-format code
make run              # Start dev server (localhost:8000)

# Run single test
python -m pytest tests/test_tasks.py::TestCreateTask::test_create_task_valid -v
```

## Architecture

FastAPI REST API for task management with SQLite storage.

```
app/
├── main.py      # FastAPI routes, app entry point
├── models.py    # Pydantic schemas (TaskCreate, TaskUpdate, TaskResponse, TaskStatus enum)
├── database.py  # SQLAlchemy engine, session, TaskDB model
└── crud.py      # Database operations (create/get/update/delete)
```

**Request flow:** Route (main.py) → CRUD function (crud.py) → SQLAlchemy model (database.py) → Response via Pydantic schema (models.py)

## Conventions

- Use `X | None` syntax for optional types (Python 3.10+), not `Optional[X]`
- Use timezone-aware datetimes: `datetime.now(UTC)` via `utc_now()` helper in database.py
- FastAPI `Depends()` in function defaults is allowed (B008 ignored in ruff config)
- Tests use in-memory SQLite with fresh database per test via fixtures in conftest.py
