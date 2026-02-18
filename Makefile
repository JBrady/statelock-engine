PYTHON ?= python3
PIP ?= $(PYTHON) -m pip

.PHONY: setup setup-dev run test lint up down logs up-prod down-prod

setup:
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

setup-dev:
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements-dev.txt

run:
	uvicorn main:app --reload

test:
	pytest

lint:
	ruff check .

up:
	cp -n .env.example .env || true
	docker compose up -d

up-prod:
	cp -n .env.example .env || true
	docker compose -f docker-compose.prod.yml up -d --build

down:
	docker compose down

down-prod:
	docker compose -f docker-compose.prod.yml down

logs:
	docker compose logs -f statelock-engine
