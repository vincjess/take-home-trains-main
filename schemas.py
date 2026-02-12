import re

from pydantic import BaseModel, Field, field_validator

TRAIN_ID_MIN_LENGTH = 1
TRAIN_ID_MAX_LENGTH = 6
TRAIN_ID_PATTERN = rf"^[A-Za-z]{{{TRAIN_ID_MIN_LENGTH},{TRAIN_ID_MAX_LENGTH}}}$"
TRAIN_ID_RE = re.compile(TRAIN_ID_PATTERN)


class TrainScheduleCreate(BaseModel):
    id: str
    schedule: list[int]

    @field_validator("id")
    @classmethod
    def validate_train_id(cls, v: str) -> str:
        # Train IDs must be 1-6 alphabetic characters
        if not v:
            raise ValueError("Train ID cannot be empty")
        if len(v) > TRAIN_ID_MAX_LENGTH:
            raise ValueError(
                f"Train ID must be at most {TRAIN_ID_MAX_LENGTH} characters"
            )
        if not TRAIN_ID_RE.fullmatch(v):
            raise ValueError("Train ID must contain only alphabetic characters")
        return v.upper()

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
