from typing import Annotated

from fastapi import Depends
from habit_events import EventBus
from sqlalchemy.orm import Session

from habit_core.db import get_db
from habit_core.events import get_event_bus

DbSession = Annotated[Session, Depends(get_db)]
EventBusDep = Annotated[EventBus, Depends(get_event_bus)]
