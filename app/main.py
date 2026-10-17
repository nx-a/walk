from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from psycopg2 import errors as pg_errors

from .api import Services, router
from .config import settings
from .db import Database
from .errors import ShelterError

logging.basicConfig(level=logging.INFO)


class ShelterApp:
    """Сборка приложения: БД, сервисы, роуты, статика SPA."""

    def __init__(self) -> None:
        self.db = Database(settings.database_url, settings.pool_min, settings.pool_max)
        self.app = FastAPI(title="Приют: выгул собак", lifespan=self._lifespan)
        self.app.state.services = Services(self.db)
        self._register_error_handlers()
        # API — до статики, иначе mount("/") перехватит /api/*
        self.app.include_router(router)
        self.app.mount("/", StaticFiles(directory=settings.static_dir, html=True), name="spa")

    @asynccontextmanager
    async def _lifespan(self, _app: FastAPI):
        self.db.connect()
        self.db.apply_schema(settings.schema_path)
        try:
            yield
        finally:
            self.db.close()

    def _register_error_handlers(self) -> None:
        @self.app.exception_handler(ShelterError)
        async def shelter_error(_: Request, exc: ShelterError):
            return JSONResponse({"detail": exc.message}, status_code=exc.status_code)

        @self.app.exception_handler(pg_errors.IntegrityError)
        async def integrity_error(_: Request, exc: pg_errors.IntegrityError):
            return JSONResponse(
                {"detail": f"Нарушение целостности данных: {exc.diag.message_primary}"},
                status_code=409,
            )


app = ShelterApp().app
