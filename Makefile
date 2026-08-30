.PHONY: all format lint typecheck test test-slow test-all coverage docs \
        reconstruct measure check check-full build-test test-minimum lock-check \
        dist-check release clean

all: check

# --------------------------------------------------------------------------
# Individual steps
# --------------------------------------------------------------------------

format:
	uv run ruff format .
	uv run ruff check . --fix

lint:
	uv run ruff format --check .
	uv run ruff check .

typecheck:
	uv run mypy src
	uv run mypy --strict scripts

# Default run. The slow marker is deselected in pyproject.toml via addopts.
test:
	uv run pytest

# Only the slow tests, at present the exact determinant proof in dimension 17,
# about one minute.
test-slow:
	uv run pytest -m slow

# Everything, with no marker filter.
test-all:
	uv run pytest -m ""

# fail_under = 100 stands in pyproject.toml, so this target fails as soon as
# one statement stays unchecked. Unreachable defensive branches carry
# `# pragma: no cover` with the reason. The figure measures what is
# measurable.
coverage:
	uv run pytest --cov --cov-report=term-missing --cov-report=html

# Only the executable examples from docs/.
docs:
	uv run pytest docs

# The second computations, independent of the library. They have stood in
# AGENTS.md among the gates since 0.2, but no target called them, so they ran
# only by hand. A check nobody runs is not a check.
reconstruct:
	uv run python scripts/reconstruct_bcw17.py
	uv run python scripts/reconstruct_alpoege15.py
	uv run python scripts/reconstruct_alpoege19.py
	uv run python scripts/reconstruct_alpoege13.py
	uv run python scripts/reconstruct_alpoege12.py
	uv run python scripts/reconstruct_spacerat11.py
	uv run python scripts/reconstruct_macfarlane13.py
	uv run python scripts/reconstruct_prellberg40.py

measure:
	uv run python scripts/untargeted_space.py

# --------------------------------------------------------------------------
# Collected targets
# --------------------------------------------------------------------------

# For the working loop and the pull request job: seconds.
check: lint typecheck test

# Before a release and for the nightly job. Includes the slow tests, so that
# the exact Keller proof does not stay unchecked indefinitely.
check-full: lint typecheck test-all

# --------------------------------------------------------------------------
# Build and test in an isolated environment
# --------------------------------------------------------------------------

# What is checked is the package and not the working tree. The virtual
# environment does not see src/, so `import kellermap` in the tests resolves to
# the installed wheel.
#
# The cleanup below concerns the two environments this target creates itself
# and no longer the content of the archive. Since 0.4.0rc15 that content
# depends on the positive list in pyproject.toml and not on the state of the
# directory: a virtual environment that happens to lie beside the project is
# not shipped, whatever it is called. Before that it was, and one named
# .venv314 broke `uv build`.
build-test:
	@echo "--> Removing old builds..."
	rm -rf dist build_env min_env
	@echo "--> Building wheel and sdist..."
	uv build
	@echo "--> Creating a fresh venv (build_env)..."
	# The checked lower bound from requires-python: the oldest supported
	# version breaks more often than the newest. The CI covers the newest.
	uv venv --python 3.10 build_env
	@echo "--> Installing the wheel and pytest..."
	VIRTUAL_ENV=build_env uv pip install dist/*.whl pytest
	@echo "--> Checking the PEP 561 marker in the installed package..."
	build_env/bin/python -c "import kellermap, pathlib, sys; sys.exit(None if (pathlib.Path(kellermap.__file__).parent / 'py.typed').exists() else 'py.typed is missing from the wheel: kellermap would be untyped for type checkers downstream')"
	@echo "--> Running the test suite against the installed package..."
	build_env/bin/python -m pytest -q
	@echo "Success: wheel built, installed and checked."

# Resolution to the smallest permitted versions rather than to the newest.
# Without this target the lower bound in pyproject.toml stays an assertion:
# development happens against current packages, and a bound that is too low is
# noticed first by a user. sympy>=1.13 stood there unnoticed for four
# releases.
test-minimum:
	@echo "--> Creating a venv on the oldest supported Python version..."
	rm -rf min_env
	uv venv --python 3.10 min_env
	@echo "--> Installing the smallest permitted dependencies..."
	# Deliberately without --locked: the lockfile pins the resolved versions
	# and not the smallest ones. It is being bypassed here on purpose.
	VIRTUAL_ENV=min_env uv pip install --resolution lowest-direct -e .
	# pytest in a second step and without the rule. What is checked are the
	# lower bounds this package declares and not those of the test runner. On
	# the same line pytest would be a direct dependency, and
	# --resolution lowest-direct would pull pytest 2.0.0 from 2011, which no
	# longer builds with current setuptools.
	@echo "--> Installing the test runner (normal resolution)..."
	VIRTUAL_ENV=min_env uv pip install pytest
	@echo "--> Showing the resolved versions..."
	min_env/bin/python -c "import sympy; print(f'    sympy {sympy.__version__}')"
	@echo "--> Running the test suite..."
	min_env/bin/python -m pytest -q
	@echo "Success: the declared lower bound holds."

# Checks the artefacts that would actually be uploaded. twine reads the
# metadata the way PyPI reads it. An incomplete README or an unreadable
# description would otherwise be noticed only at upload, where the version
# number is already taken.
dist-check:
	@echo "--> Checking the built artefacts..."
	uv run --with twine twine check dist/*

# Checks whether uv.lock matches pyproject.toml, without changing it. A stale
# lockfile would otherwise be noticed only in the CI, where `uv sync --locked`
# fails.
lock-check:
	uv lock --check

# All release gates before a tag.
release: lock-check check-full coverage reconstruct measure build-test dist-check test-minimum

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
