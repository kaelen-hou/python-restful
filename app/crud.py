from typing import Any

from sqlalchemy.orm import Session

from app.database import TaskDB, utc_now
from app.models import TaskCreate, TaskStatus, TaskUpdate


def create_task(db: Session, task: TaskCreate) -> TaskDB:
    db_task = TaskDB(
        title=task.title,
        description=task.description,
        status=task.status,
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task


def get_tasks(
    db: Session,
    status: TaskStatus | None = None,
    search: str | None = None,
    skip: int = 0,
    limit: int = 100,
) -> list[Any]:
    query = db.query(TaskDB)
    if status is not None:
        query = query.filter(TaskDB.status == status)
    if search is not None:
        query = query.filter(TaskDB.title.ilike(f"%{search}%"))
    return query.offset(skip).limit(limit).all()


def get_task(db: Session, task_id: int) -> TaskDB | None:
    result: TaskDB | None = db.query(TaskDB).filter(TaskDB.id == task_id).first()
    return result


def update_task(db: Session, task_id: int, task: TaskUpdate) -> TaskDB | None:
    db_task = get_task(db, task_id)
    if db_task is None:
        return None

    update_data = task.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_task, field, value)

    db_task.updated_at = utc_now()  # type: ignore[assignment]
    db.commit()
    db.refresh(db_task)
    return db_task


def delete_task(db: Session, task_id: int) -> bool:
    db_task = get_task(db, task_id)
    if db_task is None:
        return False

    db.delete(db_task)
    db.commit()
    return True
