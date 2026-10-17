"""Репозитории: только SQL. Работают с курсором открытой транзакции."""

from __future__ import annotations

from datetime import datetime
from typing import Any, ClassVar, Generic, TypeVar

from psycopg2 import sql
from psycopg2.extensions import cursor as Cursor

from .models import Dog, Entity, Helper, Kennel, Walk

T = TypeVar("T", bound=Entity)


class BaseRepository(Generic[T]):
    table: ClassVar[str]
    model: ClassVar[type]
    # SELECT, отдающий все поля модели; алиас основной таблицы — "t"
    select_sql: ClassVar[str]
    order_by: ClassVar[str] = "t.id"
    writable_fields: ClassVar[tuple[str, ...]]

    def __init__(self, cur: Cursor) -> None:
        self.cur = cur

    def _fetch(self, where: str = "", params: tuple = ()) -> list[T]:
        query = f"{self.select_sql} {where} ORDER BY {self.order_by}"
        self.cur.execute(query, params)
        return [self.model.from_row(row) for row in self.cur.fetchall()]

    def list(self) -> list[T]:
        return self._fetch()

    def get(self, entity_id: int) -> T | None:
        rows = self._fetch("WHERE t.id = %s", (entity_id,))
        return rows[0] if rows else None

    def lock(self, entity_id: int) -> bool:
        """SELECT ... FOR UPDATE — сериализует конкурентные проверки по этой строке."""
        self.cur.execute(
            sql.SQL("SELECT id FROM {} WHERE id = %s FOR UPDATE").format(sql.Identifier(self.table)),
            (entity_id,),
        )
        return self.cur.fetchone() is not None

    def create(self, data: dict[str, Any]) -> int:
        fields = [f for f in self.writable_fields if f in data]
        query = sql.SQL("INSERT INTO {} ({}) VALUES ({}) RETURNING id").format(
            sql.Identifier(self.table),
            sql.SQL(", ").join(map(sql.Identifier, fields)),
            sql.SQL(", ").join(sql.Placeholder() * len(fields)),
        )
        self.cur.execute(query, [data[f] for f in fields])
        return self.cur.fetchone()["id"]

    def update(self, entity_id: int, data: dict[str, Any]) -> bool:
        fields = [f for f in self.writable_fields if f in data]
        if not fields:
            return self.get(entity_id) is not None
        query = sql.SQL("UPDATE {} SET {} WHERE id = %s").format(
            sql.Identifier(self.table),
            sql.SQL(", ").join(
                sql.SQL("{} = %s").format(sql.Identifier(f)) for f in fields
            ),
        )
        self.cur.execute(query, [data[f] for f in fields] + [entity_id])
        return self.cur.rowcount > 0

    def delete(self, entity_id: int) -> bool:
        self.cur.execute(
            sql.SQL("DELETE FROM {} WHERE id = %s").format(sql.Identifier(self.table)),
            (entity_id,),
        )
        return self.cur.rowcount > 0


class KennelRepository(BaseRepository[Kennel]):
    table = "kennels"
    model = Kennel
    writable_fields = ("number", "capacity")
    order_by = "t.number"
    select_sql = """
        SELECT t.id, t.number, t.capacity,
               (SELECT count(*) FROM dogs d WHERE d.kennel_id = t.id)::int AS dogs_count
        FROM kennels t
    """

    def count_dogs(self, kennel_id: int, exclude_dog_id: int | None = None) -> int:
        self.cur.execute(
            "SELECT count(*) AS n FROM dogs WHERE kennel_id = %s AND id IS DISTINCT FROM %s",
            (kennel_id, exclude_dog_id),
        )
        return self.cur.fetchone()["n"]


class DogRepository(BaseRepository[Dog]):
    table = "dogs"
    model = Dog
    writable_fields = ("name", "breed", "age", "kennel_id")
    order_by = "t.name, t.id"
    select_sql = """
        SELECT t.id, t.name, t.breed, t.age, t.kennel_id, k.number AS kennel_number,
               (SELECT count(*) FROM walks w
                 WHERE w.dog_id = t.id AND w.ended_at IS NOT NULL)::int AS walks_count,
               EXISTS (SELECT 1 FROM walks w
                        WHERE w.dog_id = t.id AND w.ended_at IS NULL) AS on_walk
        FROM dogs t
        LEFT JOIN kennels k ON k.id = t.kennel_id
    """


class HelperRepository(BaseRepository[Helper]):
    table = "helpers"
    model = Helper
    writable_fields = ("name", "phone")
    order_by = "t.name, t.id"
    select_sql = """
        SELECT t.id, t.name, t.phone,
               (SELECT count(*) FROM walks w
                 WHERE w.helper_id = t.id AND w.ended_at IS NOT NULL)::int AS walks_count,
               EXISTS (SELECT 1 FROM walks w
                        WHERE w.helper_id = t.id AND w.ended_at IS NULL) AS on_walk
        FROM helpers t
    """


class WalkRepository(BaseRepository[Walk]):
    table = "walks"
    model = Walk
    writable_fields = ("dog_id", "helper_id", "started_at", "ended_at")
    order_by = "t.ended_at IS NOT NULL, t.started_at DESC"
    select_sql = """
        SELECT t.id, t.dog_id, d.name AS dog_name, t.helper_id, h.name AS helper_name,
               t.started_at, t.ended_at
        FROM walks t
        JOIN dogs d ON d.id = t.dog_id
        JOIN helpers h ON h.id = t.helper_id
    """

    def search(
        self,
        dog_id: int | None = None,
        helper_id: int | None = None,
        active: bool | None = None,
    ) -> list[Walk]:
        conditions, params = [], []
        if dog_id is not None:
            conditions.append("t.dog_id = %s")
            params.append(dog_id)
        if helper_id is not None:
            conditions.append("t.helper_id = %s")
            params.append(helper_id)
        if active is not None:
            conditions.append("t.ended_at IS NULL" if active else "t.ended_at IS NOT NULL")
        where = "WHERE " + " AND ".join(conditions) if conditions else ""
        return self._fetch(where, tuple(params))

    def find_overlap(
        self,
        column: str,
        value: int,
        started_at: datetime,
        ended_at: datetime | None,
        exclude_id: int | None = None,
    ) -> Walk | None:
        """Пересекающаяся прогулка той же собаки/помощника. NULL в конце = ещё идёт."""
        if column not in ("dog_id", "helper_id"):
            raise ValueError(column)
        rows = self._fetch(
            f"""WHERE t.{column} = %s AND t.id IS DISTINCT FROM %s
                AND tstzrange(t.started_at, t.ended_at)
                    && tstzrange(%s::timestamptz, %s::timestamptz)""",
            (value, exclude_id, started_at, ended_at),
        )
        return rows[0] if rows else None
