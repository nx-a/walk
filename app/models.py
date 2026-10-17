from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Mapping


class DogStatus(Enum):
    """Состояние собаки по числу завершённых прогулок. Цвет задаётся в CSS по коду."""

    NOT_WALKED = ("not_walked", "Не выгулена")
    WALKED_ONCE = ("walked_once", "Был выгул")
    WALKED = ("walked", "Погуляла")

    def __init__(self, code: str, label: str) -> None:
        self.code = code
        self.label = label

    @classmethod
    def from_walks(cls, walks_count: int) -> DogStatus:
        if walks_count <= 0:
            return cls.NOT_WALKED
        if walks_count == 1:
            return cls.WALKED_ONCE
        return cls.WALKED


class Entity:
    """База доменных объектов: сборка из строки RealDictCursor."""

    @classmethod
    def from_row(cls, row: Mapping[str, Any]):
        return cls(**{name: row[name] for name in cls.__dataclass_fields__})


@dataclass
class Kennel(Entity):
    id: int
    number: str
    capacity: int
    dogs_count: int

    @property
    def free_places(self) -> int:
        return max(self.capacity - self.dogs_count, 0)


@dataclass
class Dog(Entity):
    id: int
    name: str
    breed: str
    age: int | None
    kennel_id: int | None
    kennel_number: str | None
    walks_count: int
    on_walk: bool

    @property
    def status(self) -> DogStatus:
        return DogStatus.from_walks(self.walks_count)


@dataclass
class Helper(Entity):
    id: int
    name: str
    phone: str
    walks_count: int
    on_walk: bool


@dataclass
class Walk(Entity):
    id: int
    dog_id: int
    dog_name: str
    helper_id: int
    helper_name: str
    started_at: datetime
    ended_at: datetime | None

    @property
    def is_active(self) -> bool:
        return self.ended_at is None

    @property
    def duration_minutes(self) -> int | None:
        if self.ended_at is None:
            return None
        return int((self.ended_at - self.started_at).total_seconds() // 60)
