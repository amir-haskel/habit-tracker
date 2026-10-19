from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI, HTTPException

from notifications.api_deps import DbSession
from notifications.config import settings
from notifications.db import Base, engine
from notifications.models import Notification  # noqa: F401 — ensure table is registered
from notifications.repository import NotificationRepository
from notifications.schemas import NotificationRead


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    Base.metadata.create_all(bind=engine)
    if settings.event_bus == "aws":
        # Embedded consumer: one process owns the SQLite store this phase.
        from notifications.consumer import start_consumer_thread

        start_consumer_thread()
    yield


app = FastAPI(title="Notifications", version="0.1.0", lifespan=lifespan)
router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=list[NotificationRead])
def list_notifications(db: DbSession, unread_only: bool = False) -> list[NotificationRead]:
    items = NotificationRepository(db).list(unread_only=unread_only)
    return [NotificationRead.model_validate(item) for item in items]


@router.get("/unread-count")
def unread_count(db: DbSession) -> dict[str, int]:
    return {"count": NotificationRepository(db).unread_count()}


@router.post("/{notification_id}/read", response_model=NotificationRead)
def mark_read(notification_id: int, db: DbSession) -> NotificationRead:
    repo = NotificationRepository(db)
    item = repo.get(notification_id)
    if item is None:
        raise HTTPException(status_code=404, detail=f"Notification {notification_id} not found")
    return NotificationRead.model_validate(repo.mark_read(item))


app.include_router(router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
