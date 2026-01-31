# Task CRUD API

A RESTful API for task management built with FastAPI and SQLite.

## Setup

```bash
pip install -r requirements.txt
```

## Run the Server

```bash
uvicorn app.main:app --reload
```

API documentation available at http://localhost:8000/docs

## Run Tests

```bash
pytest tests/ -v
```

## Authentication

All `/tasks` endpoints require JWT authentication.

```bash
# Get token (demo user: admin/admin)
curl -X POST http://localhost:8000/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin"}'

# Use token
curl http://localhost:8000/tasks \
  -H "Authorization: Bearer <token>"
```

## API Endpoints

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| POST | /login | Get JWT token | No |
| POST | /tasks | Create a task | Yes |
| GET | /tasks | List tasks | Yes |
| GET | /tasks/{id} | Get a task | Yes |
| PUT | /tasks/{id} | Update a task | Yes |
| DELETE | /tasks/{id} | Delete a task | Yes |

### Query Parameters (GET /tasks)

| Param | Type | Description |
|-------|------|-------------|
| status | string | Filter by status: pending, in_progress, completed |
| skip | int | Offset for pagination (default: 0) |
| limit | int | Max results 1-100 (default: 100) |

## Task Schema

```json
{
  "id": 1,
  "title": "Task title",
  "description": "Optional description",
  "status": "pending|in_progress|completed",
  "created_at": "2024-01-01T00:00:00",
  "updated_at": "2024-01-01T00:00:00"
}
```
