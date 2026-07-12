from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Student(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    service_type: str = "clase particular"
    tutor_name: str = ""
    parent_name: str = ""
    email: str = ""
    whatsapp: str = ""
    hourly_rate: float = Field(default=0.0)
    status: str = "Activo"
    created_at: datetime = Field(default_factory=datetime.now)

    @field_validator("hourly_rate")
    @classmethod
    def validate_hourly_rate(cls, value: float) -> float:
        if value < 0:
            raise ValueError("hourly rate cannot be negative")
        return round(value, 2)


class Session(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    student_id: str
    date: datetime
    duration_hours: float
    summary: str
    next_session: str
    total_amount: float = Field(default=0.0)
    folio: str = ""
    session_number: int = 1
    report_path: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)

    @field_validator("duration_hours")
    @classmethod
    def validate_duration(cls, value: float) -> float:
        if value <= 0:
            raise ValueError("duration must be positive")
        return round(value, 2)
