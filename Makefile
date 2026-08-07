.PHONY: all format lint typecheck test test-slow test-all coverage docs \
        reconstruct check check-full build-test test-minimum lock-check \
        dist-check release clean

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

# fail_under = 100 steht in pyproject.toml, das Ziel scheitert also, sobald
# eine Anweisung ungeprueft bleibt. Unerreichbare Verteidigungszweige tragen
# `# pragma: no cover` samt Begruendung; die Quote misst, was messbar ist.
coverage:
	uv run pytest --cov --cov-report=term-missing --cov-report=html

# Nur die ausfuehrbaren Beispiele aus docs/.
docs:
	uv run pytest docs

# Die zweiten, von der Bibliothek unabhaengigen Rechnungen. Sie stehen in
# AGENTS.md seit 0.2 unter den Gates, wurden aber von keinem Ziel aufgerufen
# und liefen daher nur von Hand. Ein Nachweis, den niemand faehrt, ist keiner.
reconstruct:
	uv run python scripts/reconstruct_bcw17.py
	uv run python scripts/reconstruct_alpoege15.py

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
# also loest `import kellermap` in den Tests auf das installierte Wheel auf.
build-test:
	@echo "--> Raeume alte Builds auf..."
	rm -rf dist build_env min_env
	@echo "--> Baue Wheel und sdist..."
	uv build
	@echo "--> Erstelle frische venv (build_env)..."
	# Gepruefte Untergrenze aus requires-python: die aelteste unterstuetzte
	# Version bricht eher als die neueste. Die neueste deckt die CI ab.
	uv venv --python 3.10 build_env
	@echo "--> Installiere Wheel und pytest..."
	VIRTUAL_ENV=build_env uv pip install dist/*.whl pytest
	@echo "--> Pruefe PEP-561-Marker im installierten Paket..."
	build_env/bin/python -c "import kellermap, pathlib, sys; sys.exit(None if (pathlib.Path(kellermap.__file__).parent / 'py.typed').exists() else 'py.typed fehlt im Wheel: kellermap waere fuer Typpruefer stromabwaerts untypisiert')"
	@echo "--> Fahre die Testsuite gegen das installierte Paket..."
	build_env/bin/python -m pytest -q
	@echo "Erfolg: Wheel gebaut, installiert und geprueft."

# Aufloesung auf die kleinsten erlaubten Versionen statt auf die neuesten.
# Ohne dieses Ziel bleibt die Untergrenze in pyproject.toml eine Behauptung:
# entwickelt wird gegen aktuelle Pakete, und eine zu niedrige Angabe faellt
# erst dem Anwender auf. sympy>=1.13 stand vier Releases lang unbemerkt drin.
test-minimum:
	@echo "--> Erstelle venv auf der aeltesten unterstuetzten Python-Version..."
	rm -rf min_env
	uv venv --python 3.10 min_env
	@echo "--> Installiere die kleinsten erlaubten Abhaengigkeiten..."
	# Bewusst ohne --locked: der Lockfile pinnt die aufgeloesten, nicht die
	# kleinsten Versionen. Er wird hier gerade umgangen.
	VIRTUAL_ENV=min_env uv pip install --resolution lowest-direct -e .
	# pytest in einem zweiten Schritt und ohne die Regel: geprueft werden die
	# Untergrenzen, die dieses Paket zusagt, nicht die des Testlaeufers. Auf
	# derselben Zeile waere pytest eine direkte Abhaengigkeit, und
	# --resolution lowest-direct zoege pytest 2.0.0 von 2011, das sich mit
	# heutigem setuptools nicht mehr bauen laesst.
	@echo "--> Installiere den Testlaeufer (normale Aufloesung)..."
	VIRTUAL_ENV=min_env uv pip install pytest
	@echo "--> Zeige die aufgeloesten Versionen..."
	min_env/bin/python -c "import sympy; print(f'    sympy {sympy.__version__}')"
	@echo "--> Fahre die Testsuite..."
	min_env/bin/python -m pytest -q
	@echo "Erfolg: die deklarierte Untergrenze traegt."

# Prueft die Artefakte, die tatsaechlich hochgeladen wuerden. twine liest die
# Metadaten so, wie PyPI sie liest; ein unvollstaendiges README oder eine
# unlesbare Beschreibung faellt sonst erst beim Upload auf, wo die
# Versionsnummer schon vergeben ist.
dist-check:
	@echo "--> Pruefe die gebauten Artefakte..."
	uv run --with twine twine check dist/*

# Prueft, ob uv.lock zu pyproject.toml passt, ohne ihn zu veraendern.
# Ein veralteter Lockfile faellt sonst erst in der CI auf, wo `uv sync
# --locked` fehlschlaegt.
lock-check:
	uv lock --check

# Alle Freigabe-Gates vor einem Tag.
release: lock-check check-full coverage reconstruct build-test dist-check test-minimum

# --------------------------------------------------------------------------

clean:
	find . -type d -name "__pycache__" -prune -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf .ruff_cache
	rm -rf htmlcov
	rm -f .coverage
	rm -rf dist build_env min_env
