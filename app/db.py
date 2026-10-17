import logging
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

import psycopg2
from psycopg2.extensions import cursor as Cursor
from psycopg2.extras import RealDictCursor
from psycopg2.pool import ThreadedConnectionPool

log = logging.getLogger(__name__)


class Database:
    """Пул соединений psycopg2 и транзакции поверх него."""

    def __init__(self, dsn: str, minconn: int = 1, maxconn: int = 10) -> None:
        self._dsn = dsn
        self._minconn = minconn
        self._maxconn = maxconn
        self._pool: ThreadedConnectionPool | None = None

    def connect(self, retries: int = 15, delay: float = 1.0) -> None:
        for attempt in range(1, retries + 1):
            try:
                self._pool = ThreadedConnectionPool(self._minconn, self._maxconn, self._dsn)
                return
            except psycopg2.OperationalError as exc:
                if attempt == retries:
                    raise
                log.warning("БД недоступна (%s), попытка %d/%d", exc, attempt, retries)
                time.sleep(delay)

    def close(self) -> None:
        if self._pool is not None:
            self._pool.closeall()
            self._pool = None

    @contextmanager
    def transaction(self) -> Iterator[Cursor]:
        """Курсор в рамках одной транзакции: commit при успехе, rollback при ошибке."""
        if self._pool is None:
            raise RuntimeError("Database is not connected")
        conn = self._pool.getconn()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                yield cur
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            self._pool.putconn(conn)

    def apply_schema(self, path: Path) -> None:
        with self.transaction() as cur:
            cur.execute(path.read_text(encoding="utf-8"))
