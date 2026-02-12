import re

from pydantic import BaseModel, Field, field_validator


class TrainScheduleCreate(BaseModel):
    id: str
    schedule: list[int]

    @field_validator("id")
    @classmethod
    def validate_train_id(cls, v: str) -> str:
        # Train IDs must be 1-6 alphabetic characters
        if not v:
            raise ValueError("Train ID cannot be empty")
        if len(v) > 6:
            raise ValueError("Train ID must be at most 6 characters")
        if not re.match(r"^[A-Za-z]+$", v):
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
