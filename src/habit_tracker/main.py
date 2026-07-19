from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from habit_tracker.api.routers.habits import router as habits_router
from habit_tracker.api.routers.logs import router as logs_router
from habit_tracker.api.routers.stats import router as stats_router
from habit_tracker.api.routers.streaks import router as streaks_router
from habit_tracker.db import Base, engine
from habit_tracker.exceptions import NotFoundError, ValidationError


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Habit Tracker", version="0.1.0", lifespan=lifespan)
app.include_router(habits_router)
app.include_router(logs_router)
app.include_router(streaks_router)
app.include_router(stats_router)


@app.exception_handler(NotFoundError)
async def handle_not_found(request: Request, exc: NotFoundError) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(ValidationError)
async def handle_validation_error(request: Request, exc: ValidationError) -> JSONResponse:
    return JSONResponse(status_code=400, content={"detail": str(exc)})


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
