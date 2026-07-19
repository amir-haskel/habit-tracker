from fastapi import APIRouter, status

from habit_tracker.api.deps import DbSession
from habit_tracker.schemas.habit import HabitCreate, HabitRead, HabitUpdate
from habit_tracker.services.habit_service import HabitService

router = APIRouter(prefix="/habits", tags=["habits"])


@router.post("", response_model=HabitRead, status_code=status.HTTP_201_CREATED)
def create_habit(data: HabitCreate, db: DbSession) -> HabitRead:
    habit = HabitService(db).create_habit(data)
    return HabitRead.model_validate(habit)


@router.get("", response_model=list[HabitRead])
def list_habits(db: DbSession, include_archived: bool = False) -> list[HabitRead]:
    habits = HabitService(db).list_habits(include_archived=include_archived)
    return [HabitRead.model_validate(habit) for habit in habits]


@router.get("/{habit_id}", response_model=HabitRead)
def get_habit(habit_id: int, db: DbSession) -> HabitRead:
    habit = HabitService(db).get_habit(habit_id)
    return HabitRead.model_validate(habit)


@router.patch("/{habit_id}", response_model=HabitRead)
def update_habit(habit_id: int, data: HabitUpdate, db: DbSession) -> HabitRead:
    habit = HabitService(db).update_habit(habit_id, data)
    return HabitRead.model_validate(habit)


@router.post("/{habit_id}/archive", response_model=HabitRead)
def archive_habit(habit_id: int, db: DbSession) -> HabitRead:
    habit = HabitService(db).archive_habit(habit_id)
    return HabitRead.model_validate(habit)
