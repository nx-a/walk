.DEFAULT_GOAL := run

-include .env
export
PYTHON ?= python3
VENV := .venv

.PHONY: venv db run up down

venv:
	$(PYTHON) -m venv $(VENV)
	$(VENV)/bin/pip install -r requirements.txt

# Только PostgreSQL в Docker (порт 5433)
db:
	docker compose up -d db

# Локальный запуск API + SPA на http://localhost:8000
run: db
	$(VENV)/bin/uvicorn app.main:app --reload --port 8000

# Всё в Docker: http://localhost:8010
up:
	docker compose up -d --build

down:
	docker compose down
