import logging
from collections.abc import Callable
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import create_tables, get_db
from app.logging_config import generate_request_id, request_id_var, setup_logging
from app.rate_limit import limiter
from app.routers import v1

settings = get_settings()
setup_logging(settings.debug)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Task API",
    description="A RESTful API for task management",
    version="1.0.0",
)
app.state.limiter = limiter
app.add_exception_handler(
    RateLimitExceeded,
    _rate_limit_exceeded_handler,  # type: ignore[arg-type]
)

# Prometheus metrics
Instrumentator().instrument(app).expose(app, endpoint="/metrics", tags=["system"])


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
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
async def log_requests(request: Request, call_next: Callable[[Request], Any]) -> Response:
    request_id = generate_request_id()
    request_id_var.set(request_id)
    logger.info(f"Request started: {request.method} {request.url.path}")
    response: Response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    logger.info(f"Request completed: {request.method} {request.url.path} - {response.status_code}")
    return response


@app.get("/health", tags=["system"])
def health_check(db: Session = Depends(get_db)) -> dict[str, str]:
    """Check API and database health status."""
    try:
        db.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception:
        raise HTTPException(status_code=503, detail="Database unavailable") from None


# Include versioned API router
app.include_router(v1.router)
