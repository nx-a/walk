"""Сервисы: бизнес-правила приюта. Каждый публичный метод — одна транзакция."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, ClassVar, Generic, TypeVar

from psycopg2 import errors as pg_errors
from psycopg2.extensions import cursor as Cursor

from .db import Database
from .errors import ConflictError, NotFoundError, ValidationError
from .models import Entity, Walk
from .repositories import (
    BaseRepository,
    DogRepository,
    HelperRepository,
    KennelRepository,
    WalkRepository,
)

T = TypeVar("T", bound=Entity)

# Допуск на расхождение часов клиента и сервера при проверке «не в будущем»
CLOCK_SKEW = timedelta(minutes=1)


def utc(dt: datetime) -> datetime:
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt


def now() -> datetime:
    return datetime.now(timezone.utc)


class CrudService(Generic[T]):
    repository: ClassVar[type[BaseRepository]]
    entity_name: ClassVar[str]
    not_found_word: ClassVar[str] = "не найден"
    delete_conflict_message: ClassVar[str] = "Объект используется и не может быть удалён"

    def __init__(self, db: Database) -> None:
        self.db = db

    def _repo(self, cur: Cursor) -> BaseRepository[T]:
        return self.repository(cur)

    def _not_found(self, entity_id: int) -> NotFoundError:
        return NotFoundError(f"{self.entity_name} #{entity_id} {self.not_found_word}")

    def _get_or_raise(self, repo: BaseRepository[T], entity_id: int) -> T:
        entity = repo.get(entity_id)
        if entity is None:
            raise self._not_found(entity_id)
        return entity

    # Хуки для правил конкретной сущности
    def _before_create(self, cur: Cursor, data: dict[str, Any]) -> None: ...

    def _before_update(self, cur: Cursor, entity_id: int, data: dict[str, Any]) -> None: ...

    def list(self) -> list[T]:
        with self.db.transaction() as cur:
            return self._repo(cur).list()

    def get(self, entity_id: int) -> T:
        with self.db.transaction() as cur:
            return self._get_or_raise(self._repo(cur), entity_id)

    def create(self, data: dict[str, Any]) -> T:
        with self.db.transaction() as cur:
            self._before_create(cur, data)
            repo = self._repo(cur)
            return repo.get(repo.create(data))

    def update(self, entity_id: int, data: dict[str, Any]) -> T:
        with self.db.transaction() as cur:
            repo = self._repo(cur)
            if not repo.lock(entity_id):
                raise self._not_found(entity_id)
            self._before_update(cur, entity_id, data)
            repo.update(entity_id, data)
            return repo.get(entity_id)

    def delete(self, entity_id: int) -> None:
        try:
            with self.db.transaction() as cur:
                if not self._repo(cur).delete(entity_id):
                    raise self._not_found(entity_id)
        except pg_errors.ForeignKeyViolation:
            raise ConflictError(self.delete_conflict_message) from None


class KennelService(CrudService):
    repository = KennelRepository
    entity_name = "Будка"
    not_found_word = "не найдена"

    def create(self, data: dict[str, Any]) -> Any:
        try:
            return super().create(data)
        except pg_errors.UniqueViolation:
            raise ConflictError(f"Будка с номером «{data['number']}» уже есть") from None

    def update(self, entity_id: int, data: dict[str, Any]) -> Any:
        try:
            return super().update(entity_id, data)
        except pg_errors.UniqueViolation:
            raise ConflictError(f"Будка с номером «{data['number']}» уже есть") from None

    def _before_update(self, cur: Cursor, entity_id: int, data: dict[str, Any]) -> None:
        capacity = data.get("capacity")
        if capacity is None:
            return
        occupied = KennelRepository(cur).count_dogs(entity_id)
        if capacity < occupied:
            raise ConflictError(
                f"В будке уже {occupied} соб., вместимость не может быть меньше"
            )


class DogService(CrudService):
    repository = DogRepository
    entity_name = "Собака"
    not_found_word = "не найдена"
    delete_conflict_message = "У собаки есть прогулки — удалить нельзя"

    def _check_kennel(self, cur: Cursor, kennel_id: int | None, dog_id: int | None) -> None:
        if kennel_id is None:
            return
        kennels = KennelRepository(cur)
        if not kennels.lock(kennel_id):
            raise NotFoundError(f"Будка #{kennel_id} не найдена")
        kennel = kennels.get(kennel_id)
        if kennels.count_dogs(kennel_id, exclude_dog_id=dog_id) >= kennel.capacity:
            raise ConflictError(f"Будка №{kennel.number} заполнена ({kennel.capacity} мест)")

    def _before_create(self, cur: Cursor, data: dict[str, Any]) -> None:
        self._check_kennel(cur, data.get("kennel_id"), None)

    def _before_update(self, cur: Cursor, entity_id: int, data: dict[str, Any]) -> None:
        if "kennel_id" in data:
            self._check_kennel(cur, data["kennel_id"], entity_id)


class HelperService(CrudService):
    repository = HelperRepository
    entity_name = "Помощник"
    delete_conflict_message = "У помощника есть прогулки — удалить нельзя"


class WalkService(CrudService):
    repository = WalkRepository
    entity_name = "Прогулка"
    not_found_word = "не найдена"

    def search(self, **filters: Any) -> list[Walk]:
        with self.db.transaction() as cur:
            return WalkRepository(cur).search(**filters)

    def create(self, data: dict[str, Any]) -> Walk:
        started_at = utc(data.get("started_at") or now())
        ended_at = utc(data["ended_at"]) if data.get("ended_at") else None
        self._validate_times(started_at, ended_at)

        with self.db.transaction() as cur:
            dog_id, helper_id = data["dog_id"], data["helper_id"]
            # Блокируем собаку и помощника, чтобы параллельные запросы не создали пересечение
            if not DogRepository(cur).lock(dog_id):
                raise NotFoundError(f"Собака #{dog_id} не найдена")
            if not HelperRepository(cur).lock(helper_id):
                raise NotFoundError(f"Помощник #{helper_id} не найден")

            walks = WalkRepository(cur)
            self._check_overlap(walks, dog_id, helper_id, started_at, ended_at)
            walk_id = walks.create(
                {"dog_id": dog_id, "helper_id": helper_id,
                 "started_at": started_at, "ended_at": ended_at}
            )
            return walks.get(walk_id)

    def finish(self, walk_id: int, ended_at: datetime | None = None) -> Walk:
        ended_at = utc(ended_at or now())
        with self.db.transaction() as cur:
            walks = WalkRepository(cur)
            if not walks.lock(walk_id):
                raise self._not_found(walk_id)
            walk = walks.get(walk_id)
            if not walk.is_active:
                raise ConflictError("Прогулка уже завершена")
            self._validate_times(walk.started_at, ended_at)
            walks.update(walk_id, {"ended_at": ended_at})
            return walks.get(walk_id)

    @staticmethod
    def _validate_times(started_at: datetime, ended_at: datetime | None) -> None:
        limit = now() + CLOCK_SKEW
        if started_at > limit:
            raise ValidationError("Начало прогулки не может быть в будущем")
        if ended_at is not None:
            if ended_at <= started_at:
                raise ValidationError("Конец прогулки должен быть позже начала")
            if ended_at > limit:
                raise ValidationError("Конец прогулки не может быть в будущем")

    @staticmethod
    def _check_overlap(
        walks: WalkRepository,
        dog_id: int,
        helper_id: int,
        started_at: datetime,
        ended_at: datetime | None,
    ) -> None:
        if clash := walks.find_overlap("dog_id", dog_id, started_at, ended_at):
            raise ConflictError(
                f"{clash.dog_name} в это время уже гуляет (прогулка #{clash.id}, с {clash.helper_name})"
            )
        if clash := walks.find_overlap("helper_id", helper_id, started_at, ended_at):
            raise ConflictError(
                f"{clash.helper_name} в это время уже выгуливает {clash.dog_name} (прогулка #{clash.id})"
            )
