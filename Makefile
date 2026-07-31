.PHONY: all format lint typecheck test test-slow test-all coverage check check-full clean

all: check

# --------------------------------------------------------------------------
# Einzelschritte
# --------------------------------------------------------------------------

format:
	uv run ruff format .
	uv run ruff check . --fix

lint:
	uv run ruff format --check .
	uv run ruff check .

typecheck:
	uv run mypy src

# Standardlauf. Der slow-Marker ist in pyproject.toml per addopts abgewaehlt.
test:
	uv run pytest

# Nur die langsamen Tests, derzeit der exakte Determinantennachweis in
# Dimension 17 (rund eine Minute).
test-slow:
	uv run pytest -m slow

# Alles, ohne Markerfilter.
test-all:
	uv run pytest -m ""

coverage:
	uv run pytest --cov --cov-report=term-missing --cov-report=html

# --------------------------------------------------------------------------
# Sammelziele
# --------------------------------------------------------------------------

# Fuer den Arbeitsablauf und den PR-Job: Sekunden.
check: lint typecheck test

# Vor einem Release und fuer den naechtlichen Job: schliesst die langsamen
# Tests ein, damit der exakte Keller-Nachweis nicht dauerhaft ungeprueft bleibt.
check-full: lint typecheck test-all

# --------------------------------------------------------------------------

clean:
	find . -type d -name "__pycache__" -prune -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf .ruff_cache
	rm -rf htmlcov
	rm -f .coverage
