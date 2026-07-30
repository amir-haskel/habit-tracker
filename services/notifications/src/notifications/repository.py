from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from notifications.models import HabitRef, Notification


class NotificationRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    # --- notifications ---
    def add(self, notification: Notification) -> Notification:
        self._db.add(notification)
        self._db.commit()
        self._db.refresh(notification)
        return notification

    def list(self, unread_only: bool = False, limit: int = 100) -> list[Notification]:
        stmt = select(Notification).order_by(Notification.created_at.desc()).limit(limit)
        if unread_only:
            stmt = stmt.where(Notification.read.is_(False))
        return list(self._db.scalars(stmt))

    def get(self, notification_id: int) -> Notification | None:
        return self._db.get(Notification, notification_id)

    def mark_read(self, notification: Notification) -> Notification:
        notification.read = True
        self._db.commit()
        self._db.refresh(notification)
        return notification

    def unread_count(self) -> int:
        stmt = select(Notification).where(Notification.read.is_(False))
        return len(list(self._db.scalars(stmt)))

    # --- habit read-model ---
    def upsert_habit_ref(self, habit_id: int, name: str) -> HabitRef:
        ref = self._db.get(HabitRef, habit_id)
        if ref is None:
            ref = HabitRef(habit_id=habit_id, name=name)
            self._db.add(ref)
        else:
            ref.name = name
            ref.archived = False
        self._db.commit()
        return ref

    def mark_habit_archived(self, habit_id: int) -> None:
        ref = self._db.get(HabitRef, habit_id)
        if ref is not None:
            ref.archived = True
            self._db.commit()

    def habit_name(self, habit_id: int) -> str:
        ref = self._db.get(HabitRef, habit_id)
        return ref.name if ref is not None else f"habit #{habit_id}"
