.PHONY: install dev lint format test run clean

install:
	pip install -r requirements.txt

dev:
	pip install -r requirements-dev.txt
	pre-commit install

lint:
	ruff check app tests

format:
	ruff format app tests
	ruff check --fix app tests

test:
	pytest tests/

run:
	uvicorn app.main:app --reload

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .ruff_cache
