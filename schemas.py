import re
from typing import Annotated

from pydantic import AfterValidator, BaseModel, Field, field_validator

TRAIN_ID_MAX_LENGTH = 6
TRAIN_ID_RE = re.compile(rf"^[A-Za-z]{{1,{TRAIN_ID_MAX_LENGTH}}}$")


def validate_train_id(v: str) -> str:
    """Validate and normalize train ID."""
    if not TRAIN_ID_RE.fullmatch(v):
        raise ValueError("Train ID must be 1-6 alphabetic characters")
    return v.upper()


TrainId = Annotated[str, AfterValidator(validate_train_id)]


class TrainScheduleCreate(BaseModel):
    id: TrainId
    schedule: list[int]

    @field_validator("schedule")
    @classmethod
    def validate_schedule(cls, v: list[int]) -> list[int]:
        if not v:
            raise ValueError("Schedule cannot be empty")
        for t in v:
            if t < 0 or t > 1439:
                raise ValueError(f"Schedule time {t} must be between 0 and 1439")
        return sorted(set(v))


class TrainScheduleResponse(BaseModel):
    id: str
    schedule: list[int]


class NextTrainResponse(BaseModel):
    time: int | None = None
    trains: list[str] = Field(default_factory=list)


class ErrorResponse(BaseModel):
    detail: str
