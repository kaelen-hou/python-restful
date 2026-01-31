import logging

from fastapi import Depends, FastAPI, HTTPException, Query, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from sqlalchemy import text
from sqlalchemy.orm import Session

from app import crud
from app.auth import (
    DEMO_USER,
    LoginRequest,
    Token,
    create_access_token,
    get_current_user,
    verify_password,
)
from app.config import get_settings
from app.database import create_tables, get_db
from app.logging_config import generate_request_id, request_id_var, setup_logging
from app.models import TaskCreate, TaskResponse, TaskStatus, TaskUpdate

settings = get_settings()
setup_logging(settings.debug)
logger = logging.getLogger(__name__)

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(title="Task API", description="A RESTful API for task management")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "internal_server_error", "detail": "An unexpected error occurred"},
    )


# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

create_tables()


@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = generate_request_id()
    request_id_var.set(request_id)
    logger.info(f"Request started: {request.method} {request.url.path}")
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    logger.info(f"Request completed: {request.method} {request.url.path} - {response.status_code}")
    return response


@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception:
        raise HTTPException(status_code=503, detail="Database unavailable") from None


@app.post("/login", response_model=Token)
@limiter.limit("10/minute")
def login(request: Request, login_request: LoginRequest):
    if login_request.username != DEMO_USER["username"] or not verify_password(
        login_request.password, DEMO_USER["hashed_password"]
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    access_token = create_access_token(data={"sub": login_request.username})
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(settings.rate_limit)
def create_task(
    request: Request,
    task: TaskCreate,
    db: Session = Depends(get_db),
    _: str = Depends(get_current_user),
):
    return crud.create_task(db, task)


@app.get("/tasks", response_model=list[TaskResponse])
@limiter.limit(settings.rate_limit)
def list_tasks(
    request: Request,
    status: TaskStatus | None = None,
    search: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    _: str = Depends(get_current_user),
):
    return crud.get_tasks(db, status=status, search=search, skip=skip, limit=limit)


@app.get("/tasks/{task_id}", response_model=TaskResponse)
@limiter.limit(settings.rate_limit)
def get_task(
    request: Request,
    task_id: int,
    db: Session = Depends(get_db),
    _: str = Depends(get_current_user),
):
    db_task = crud.get_task(db, task_id)
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return db_task


@app.put("/tasks/{task_id}", response_model=TaskResponse)
@limiter.limit(settings.rate_limit)
def update_task(
    request: Request,
    task_id: int,
    task: TaskUpdate,
    db: Session = Depends(get_db),
    _: str = Depends(get_current_user),
):
    db_task = crud.update_task(db, task_id, task)
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return db_task


@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit(settings.rate_limit)
def delete_task(
    request: Request,
    task_id: int,
    db: Session = Depends(get_db),
    _: str = Depends(get_current_user),
):
    if not crud.delete_task(db, task_id):
        raise HTTPException(status_code=404, detail="Task not found")
