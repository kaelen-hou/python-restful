import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app import crud
from app.auth import (
    DEMO_USER,
    LoginRequest,
    RefreshRequest,
    Token,
    create_access_token,
    create_refresh_token,
    get_current_user,
    verify_password,
    verify_refresh_token,
)
from app.config import get_settings
from app.database import get_db
from app.models import TaskCreate, TaskResponse, TaskStatus, TaskUpdate
from app.rate_limit import limiter

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(prefix="/api/v1", tags=["v1"])


@router.post("/login", response_model=Token, summary="Authenticate user")
@limiter.limit("10/minute")
def login(request: Request, login_request: LoginRequest):
    """
    Authenticate with username and password to receive JWT tokens.

    - **username**: User's username
    - **password**: User's password

    Returns access token (30 min) and refresh token (7 days).
    """
    if login_request.username != DEMO_USER["username"] or not verify_password(
        login_request.password, DEMO_USER["hashed_password"]
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    access_token = create_access_token(data={"sub": login_request.username})
    refresh_token = create_refresh_token(data={"sub": login_request.username})
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/refresh", response_model=Token, summary="Refresh access token")
@limiter.limit("30/minute")
def refresh(request: Request, refresh_request: RefreshRequest):
    """
    Get a new access token using a valid refresh token.

    - **refresh_token**: Valid refresh token from login

    Returns new access token and the same refresh token.
    """
    username = verify_refresh_token(refresh_request.refresh_token)
    access_token = create_access_token(data={"sub": username})
    return {
        "access_token": access_token,
        "refresh_token": refresh_request.refresh_token,
        "token_type": "bearer",
    }


@router.post(
    "/tasks",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new task",
)
@limiter.limit(settings.rate_limit)
def create_task(
    request: Request,
    task: TaskCreate,
    db: Session = Depends(get_db),
    _: str = Depends(get_current_user),
):
    """
    Create a new task with the following fields:

    - **title**: Task title (required, max 200 chars)
    - **description**: Optional description
    - **status**: pending, in_progress, or completed (default: pending)
    """
    return crud.create_task(db, task)


@router.get("/tasks", response_model=list[TaskResponse], summary="List all tasks")
@limiter.limit(settings.rate_limit)
def list_tasks(
    request: Request,
    status: TaskStatus | None = Query(None, description="Filter by status"),
    search: str | None = Query(None, description="Search in title (case-insensitive)"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=100, description="Max records to return"),
    db: Session = Depends(get_db),
    _: str = Depends(get_current_user),
):
    """
    Retrieve a list of tasks with optional filtering and pagination.
    """
    return crud.get_tasks(db, status=status, search=search, skip=skip, limit=limit)


@router.get("/tasks/{task_id}", response_model=TaskResponse, summary="Get a task by ID")
@limiter.limit(settings.rate_limit)
def get_task(
    request: Request,
    task_id: int,
    db: Session = Depends(get_db),
    _: str = Depends(get_current_user),
):
    """
    Retrieve a single task by its ID.
    """
    db_task = crud.get_task(db, task_id)
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return db_task


@router.put("/tasks/{task_id}", response_model=TaskResponse, summary="Update a task")
@limiter.limit(settings.rate_limit)
def update_task(
    request: Request,
    task_id: int,
    task: TaskUpdate,
    db: Session = Depends(get_db),
    _: str = Depends(get_current_user),
):
    """
    Update an existing task. All fields are optional.
    """
    db_task = crud.update_task(db, task_id, task)
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return db_task


@router.delete(
    "/tasks/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a task",
)
@limiter.limit(settings.rate_limit)
def delete_task(
    request: Request,
    task_id: int,
    db: Session = Depends(get_db),
    _: str = Depends(get_current_user),
):
    """
    Permanently delete a task by its ID.
    """
    if not crud.delete_task(db, task_id):
        raise HTTPException(status_code=404, detail="Task not found")
