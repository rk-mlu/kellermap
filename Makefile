.PHONY: all format lint typecheck test test-slow test-all coverage docs \
        check check-full build-test release clean

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

# Nur die ausfuehrbaren Beispiele aus docs/.
docs:
	uv run pytest docs

# --------------------------------------------------------------------------
# Sammelziele
# --------------------------------------------------------------------------

# Fuer den Arbeitsablauf und den PR-Job: Sekunden.
check: lint typecheck test

# Vor einem Release und fuer den naechtlichen Job: schliesst die langsamen
# Tests ein, damit der exakte Keller-Nachweis nicht dauerhaft ungeprueft bleibt.
check-full: lint typecheck test-all

# --------------------------------------------------------------------------
# Build und Test in isolierter Umgebung
# --------------------------------------------------------------------------

# Geprueft wird das Paket, nicht der Arbeitsbaum: die venv sieht src/ nicht,
# also loest `import bcw` in den Tests auf das installierte Wheel auf.
build-test:
	@echo "--> Raeume alte Builds auf..."
	rm -rf dist build_env
	@echo "--> Baue Wheel und sdist..."
	uv build
	@echo "--> Erstelle frische venv (build_env)..."
	# Gepruefte Untergrenze aus requires-python: die aelteste unterstuetzte
	# Version bricht eher als die neueste. Die neueste deckt die CI ab.
	uv venv --python 3.10 build_env
	@echo "--> Installiere Wheel und pytest..."
	VIRTUAL_ENV=build_env uv pip install dist/*.whl pytest
	@echo "--> Pruefe PEP-561-Marker im installierten Paket..."
	build_env/bin/python -c "import bcw, pathlib, sys; sys.exit(None if (pathlib.Path(bcw.__file__).parent / 'py.typed').exists() else 'py.typed fehlt im Wheel: bcw waere fuer Typpruefer stromabwaerts untypisiert')"
	@echo "--> Fahre die Testsuite gegen das installierte Paket..."
	build_env/bin/python -m pytest -q
	@echo "Erfolg: Wheel gebaut, installiert und geprueft."

# Alle Freigabe-Gates vor einem Tag.
release: check-full build-test

# --------------------------------------------------------------------------

clean:
	find . -type d -name "__pycache__" -prune -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf .ruff_cache
	rm -rf htmlcov
	rm -f .coverage
	rm -rf dist build_env
