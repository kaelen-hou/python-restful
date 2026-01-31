from fastapi import Depends, FastAPI, HTTPException, Query, status
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
from app.database import create_tables, get_db
from app.models import TaskCreate, TaskResponse, TaskStatus, TaskUpdate

app = FastAPI(title="Task API", description="A RESTful API for task management")

create_tables()


@app.post("/login", response_model=Token)
def login(request: LoginRequest):
    if request.username != DEMO_USER["username"] or not verify_password(
        request.password, DEMO_USER["hashed_password"]
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    access_token = create_access_token(data={"sub": request.username})
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(
    task: TaskCreate,
    db: Session = Depends(get_db),
    _: str = Depends(get_current_user),
):
    return crud.create_task(db, task)


@app.get("/tasks", response_model=list[TaskResponse])
def list_tasks(
    status: TaskStatus | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    _: str = Depends(get_current_user),
):
    return crud.get_tasks(db, status=status, skip=skip, limit=limit)


@app.get("/tasks/{task_id}", response_model=TaskResponse)
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    _: str = Depends(get_current_user),
):
    db_task = crud.get_task(db, task_id)
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return db_task


@app.put("/tasks/{task_id}", response_model=TaskResponse)
def update_task(
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
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    _: str = Depends(get_current_user),
):
    if not crud.delete_task(db, task_id):
        raise HTTPException(status_code=404, detail="Task not found")
