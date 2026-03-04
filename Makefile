.PHONY: setup run test seed

setup:
	python3 -m venv .venv
	. .venv/bin/activate && pip install -e '.[dev]'

run:
	. .venv/bin/activate && uvicorn app.main:app --reload

test:
	. .venv/bin/activate && pytest -q

seed:
	. .venv/bin/activate && python scripts/seed_demo.py
