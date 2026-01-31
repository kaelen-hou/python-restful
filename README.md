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

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | /tasks | Create a task |
| GET | /tasks | List all tasks |
| GET | /tasks/{id} | Get a task |
| PUT | /tasks/{id} | Update a task |
| DELETE | /tasks/{id} | Delete a task |

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
