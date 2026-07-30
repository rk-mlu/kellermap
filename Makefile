.PHONY: all format lint test typecheck check clean

all: check

format:
	uv run black .
	uv run ruff check . --fix

lint:
	uv run ruff check .

test:
	uv run pytest

typecheck:
	uv run mypy src

check:
	uv run black --check .
	uv run ruff check .
	uv run mypy src
	uv run pytest

clean:
	find . -name "__pycache__" -type d -exec rm -rf {} +
	find . -name "*.pyc" -delete
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf .ruff_cache
	rm -rf .coverage
	rm -rf htmlcov
