"""Pydantic-схемы запросов и ответов API."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from .models import Dog, DogStatus


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# --- Будки ---

class KennelIn(BaseModel):
    number: str = Field(min_length=1, max_length=20)
    capacity: int = Field(1, ge=1, le=20)


class KennelOut(ORMModel):
    id: int
    number: str
    capacity: int
    dogs_count: int
    free_places: int


# --- Собаки ---

class DogIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    breed: str = Field("", max_length=100)
    age: int | None = Field(None, ge=0, le=30)
    kennel_id: int | None = None


class StatusOut(BaseModel):
    code: str
    label: str

    @classmethod
    def of(cls, status: DogStatus) -> StatusOut:
        return cls(code=status.code, label=status.label)


class DogOut(ORMModel):
    id: int
    name: str
    breed: str
    age: int | None
    kennel_id: int | None
    kennel_number: str | None
    walks_count: int
    on_walk: bool
    status: StatusOut

    @classmethod
    def of(cls, dog: Dog) -> DogOut:
        return cls.model_validate({**dog.__dict__, "status": StatusOut.of(dog.status)})


# --- Помощники ---

class HelperIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    phone: str = Field("", max_length=30)


class HelperOut(ORMModel):
    id: int
    name: str
    phone: str
    walks_count: int
    on_walk: bool


# --- Прогулки ---

class WalkIn(BaseModel):
    dog_id: int
    helper_id: int
    started_at: datetime | None = Field(None, description="По умолчанию — сейчас")
    ended_at: datetime | None = Field(None, description="Пусто — прогулка ещё идёт")


class WalkFinishIn(BaseModel):
    ended_at: datetime | None = Field(None, description="По умолчанию — сейчас")


class WalkOut(ORMModel):
    id: int
    dog_id: int
    dog_name: str
    helper_id: int
    helper_name: str
    started_at: datetime
    ended_at: datetime | None
    is_active: bool
    duration_minutes: int | None
