"""
Train Schedule API Service

A FastAPI-based web service for managing train schedules at a station.
"""

import uvicorn
from fastapi import APIRouter, FastAPI, HTTPException, Path, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from db import Database
from schemas import (
    ErrorResponse,
    NextTrainResponse,
    TRAIN_ID_PATTERN,
    TrainScheduleCreate,
    TrainScheduleResponse,
)
from service import TrainService


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Return clean error messages for validation failures."""
    errors = exc.errors()
    if errors:
        msg = errors[0].get("msg", "Validation error")
        if msg.startswith("Value error, "):
            msg = msg[13:]
        return JSONResponse(status_code=422, content={"detail": msg})
    return JSONResponse(status_code=422, content={"detail": "Validation error"})


app = FastAPI(
    title="Train Schedule API",
    description="API for managing train schedules at a station",
    version="1.0.0",
    exception_handlers={RequestValidationError: validation_exception_handler},
)

db = Database()
train_service = TrainService(db)


@app.get("/")
def health_check() -> str:
    return "OK"


router = APIRouter(prefix="/trains", tags=["trains"])


@router.post(
    "",
    response_model=TrainScheduleResponse,
    status_code=201,
    responses={400: {"model": ErrorResponse}},
)
def add_train(train_data: TrainScheduleCreate) -> TrainScheduleResponse:
    """Add or update a train schedule."""
    train_service.upsert_schedule(train_data.id, train_data.schedule)
    return TrainScheduleResponse(id=train_data.id, schedule=train_data.schedule)


@router.get(
    "/next",
    response_model=NextTrainResponse,
)
def get_next_simultaneous(
    after: int | None = Query(
        None,
        ge=0,
        le=1439,
        description="Current time in minutes from midnight. If omitted, returns the earliest simultaneous arrival.",
    ),
    min_trains: int = Query(
        2,
        ge=2,
        description="Minimum number of trains required for a simultaneous arrival.",
    ),
) -> NextTrainResponse:
    """Get the next time when multiple trains arrive simultaneously."""
    result = train_service.find_next_simultaneous(after, min_trains)
    return NextTrainResponse(time=result["time"], trains=result["trains"])


@router.get(
    "/{train_id}",
    response_model=list[int],
    responses={404: {"model": ErrorResponse}},
)
def get_schedule(
    train_id: str = Path(
        ...,
        pattern=TRAIN_ID_PATTERN,
        description="Train identifier (1-6 alphabetic characters)",
    ),
) -> list[int]:
    """Get the schedule for a specific train."""
    schedule = train_service.get_schedule(train_id.upper())
    if schedule is None:
        raise HTTPException(
            status_code=404, detail=f"Train '{train_id.upper()}' not found"
        )
    return schedule


app.include_router(router)


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=5000, reload=True)
