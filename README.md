# Task CRUD API

A production-ready RESTful API for task management built with FastAPI and SQLite.

## Features

- JWT authentication with refresh tokens
- Rate limiting (100 req/min, 10/min for login)
- CORS support
- Structured JSON logging with request IDs
- Database migrations (Alembic)
- 96% test coverage
- Docker support

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run server
uvicorn app.main:app --reload

# Run with Docker
docker-compose up
```

API docs: http://localhost:8000/docs

## Configuration

Copy `.env.example` to `.env` and configure:

```bash
DATABASE_URL=sqlite:///./tasks.db
SECRET_KEY=your-secret-key
DEBUG=false
ALLOWED_ORIGINS=["http://localhost:3000"]
RATE_LIMIT=100/minute
```

## Authentication

```bash
# Login (demo: admin/admin)
curl -X POST http://localhost:8000/api/v1/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin"}'

# Response includes access_token (30 min) and refresh_token (7 days)

# Use access token
curl http://localhost:8000/api/v1/tasks \
  -H "Authorization: Bearer <access_token>"

# Refresh token
curl -X POST http://localhost:8000/api/v1/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "<refresh_token>"}'
```

## API Endpoints

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | /health | Health check | No |
| POST | /api/v1/login | Get tokens | No |
| POST | /api/v1/refresh | Refresh access token | No |
| POST | /api/v1/tasks | Create task | Yes |
| GET | /api/v1/tasks | List tasks | Yes |
| GET | /api/v1/tasks/{id} | Get task | Yes |
| PUT | /api/v1/tasks/{id} | Update task | Yes |
| DELETE | /api/v1/tasks/{id} | Delete task | Yes |

### Query Parameters (GET /api/v1/tasks)

| Param | Type | Description |
|-------|------|-------------|
| status | string | Filter: pending, in_progress, completed |
| search | string | Search in title (case-insensitive) |
| skip | int | Pagination offset (default: 0) |
| limit | int | Max results 1-100 (default: 100) |

## Development

```bash
make dev        # Install dev dependencies
make test       # Run tests with coverage
make lint       # Check code
make format     # Auto-format code
```

## Database Migrations

```bash
# Create migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head
```
