"""What the source archive ships, and what it does not.

Until 0.4.0rc15 the content of the sdist depended on the state of the working
directory. ``pyproject.toml`` listed what was not to be shipped, and a list of
exclusions cannot be completed against names nobody has chosen yet. An
environment named ``.venv314`` stood in none of the three lists,
``pyproject.toml``, ``.gitignore`` and the Makefile, and ``uv build`` failed
with "Invalid tar file", because a virtual environment contains absolute
symlinks. An external audit built it.

Since then it is a positive list. What is not in it is not shipped.

Two environments are laid down, and the difference between them is the point.
``.venv314`` is the reported name, which ``.gitignore`` has covered as well
since 0.4.0rc15, and the build tool reads ``.gitignore``. A test with that
environment alone could therefore be green without the positive list doing
anything. ``venv314`` without the dot is covered by no ignore list. It alone
decides whether the list in ``pyproject.toml`` holds, and against the old list
of exclusions it demonstrably ships and breaks the build.

The build really runs, and it runs in full. ``uv build --sdist`` alone would
not have shown the reported error: it arises when the archive is unpacked for
the wheel build and not when it is packed.

Two builds together cost about one and a half seconds, so none of this sits
behind a slow marker. A packaging defect should surface on the day it is
introduced and not in the nightly chain.
"""

import shutil
import subprocess
import tarfile
from collections.abc import Iterator
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent

# What the archive is to carry at the top. The build tool produces ``PKG-INFO``
# itself, which is why it does not stand in ``pyproject.toml``.
SHIPPED = {
    "PKG-INFO",
    "src",
    "tests",
    "docs",
    "scripts",
    ".github",
    "AGENTS.md",
    "CHANGELOG.md",
    "CITATION.cff",
    "CONTRIBUTING.md",
    "LICENSE",
    "Makefile",
    "README.md",
    "pyproject.toml",
    "uv.lock",
    ".gitignore",
    ".python-version",
}

LEAVE_OUT = shutil.ignore_patterns(
    ".git",
    ".venv*",
    "venv*",
    "__pycache__",
    "*.egg-info",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".coverage*",
    "htmlcov",
    "dist",
    "build",
    "build_env",
    "min_env",
)


def fake_environment(root: Path, name: str) -> None:
    """Lay down what makes a virtual environment break a tar file.

    Not a real environment. An absolute symlink to a path that exists is the
    whole of it, plus the ``.gitignore`` that ``uv venv`` leaves behind, which
    is the second thing that leaked. Building one for real would tie this test
    to an interpreter being installed on the machine that runs it.
    """
    (root / name / "bin").mkdir(parents=True)
    (root / name / "pyvenv.cfg").write_text("home = /usr/bin\n", encoding="utf-8")
    (root / name / ".gitignore").write_text("*\n", encoding="utf-8")
    (root / name / "bin" / "python").symlink_to("/usr/bin/python3.14")


def build(uv: str, copy: Path) -> subprocess.CompletedProcess[str]:
    """Run a full build in ``copy``: the archive, and the wheel built from it."""
    return subprocess.run(  # noqa: S603
        [uv, "build"],
        cwd=copy,
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.fixture(scope="module")
def uv() -> str:
    found = shutil.which("uv")

    if found is None:  # pragma: no cover - present in every project setup
        pytest.skip("uv is not on PATH; this gate needs the builder")

    return found


@pytest.fixture(scope="module")
def project(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """A copy of the repository with two stray environments beside it."""
    copy = tmp_path_factory.mktemp("packaging") / "project"
    shutil.copytree(ROOT, copy, ignore=LEAVE_OUT)
    fake_environment(copy, ".venv314")
    fake_environment(copy, "venv314")

    return copy


@pytest.fixture(scope="module")
def archive(uv: str, project: Path) -> Iterator[tarfile.TarFile]:
    finished = build(uv, project)

    assert finished.returncode == 0, finished.stderr

    built = sorted((project / "dist").glob("*.tar.gz"))

    assert len(built) == 1, built

    with tarfile.open(built[0]) as opened:
        yield opened


def entries(archive: tarfile.TarFile) -> list[str]:
    """Return every path in the archive, with the version directory stripped."""
    return [name.split("/", 1)[1] for name in archive.getnames() if "/" in name]


def test_a_stray_environment_does_not_break_the_build(
    archive: tarfile.TarFile,
) -> None:
    """The reported error.

    That the fixture delivered an archive at all is the statement. The test
    stands here so that a failure is called by its name.
    """
    assert archive.getnames()


def test_nothing_from_an_environment_ships(archive: tarfile.TarFile) -> None:
    """And not a single file out of either of them.

    The first attempt repaired the build and shipped ``.venv314/.gitignore``
    all the same: without a leading slash a pattern of the positive list holds
    at every level, and ``uv venv`` places such a file in every environment.
    What is checked is therefore the content and not the return value.
    """
    inside = [name for name in entries(archive) if "venv" in name]

    assert not inside, inside


def test_the_archive_carries_exactly_what_is_promised(
    archive: tarfile.TarFile,
) -> None:
    """The negative control for the positive list.

    A positive list can also fail by shipping too little, and an archive
    without content contains no environment either. The test above alone would
    be satisfied by that.
    """
    top = {name.split("/", 1)[0] for name in entries(archive)}

    assert top == SHIPPED


def test_the_sources_and_the_fixed_data_are_where_they_belong(
    archive: tarfile.TarFile,
) -> None:
    """Samples in depth, in both directions."""
    inside = set(entries(archive))

    assert "src/kellermap/__init__.py" in inside
    assert "src/kellermap/py.typed" in inside
    assert "tests/test_packaging.py" in inside
    assert "docs/contracts.md" in inside

    # Mathematics from another source, licence not establishable; see
    # pyproject.toml.
    assert "tests/data.py" not in inside

    assert not [name for name in inside if "__pycache__" in name]


def test_an_exclusion_list_lets_an_unforeseen_name_through(
    uv: str,
    tmp_path: Path,
) -> None:
    """Why it is a positive list and not a longer list of exclusions.

    The build runs here against the list that stood in ``pyproject.toml`` up to
    0.4.0rc15. ``venv314`` is in none of its lines and in no ignore list, it
    ships, and unpacking the archive for the wheel build fails on the absolute
    symlink inside it. Exactly the error the audit reported, only under a name
    that a longer list of exclusions would not have foreseen either.

    Without this test the suite says nothing about whether the positive list
    achieves anything: ``.gitignore``, which the build tool reads, now catches
    the reported name by itself.
    """
    copy = tmp_path / "project"
    shutil.copytree(ROOT, copy, ignore=LEAVE_OUT)
    fake_environment(copy, "venv314")

    text = (copy / "pyproject.toml").read_text(encoding="utf-8")
    head = text.index("[tool.hatch.build.targets.sdist]")
    (copy / "pyproject.toml").write_text(
        text[:head] + "[tool.hatch.build.targets.sdist]\n"
        'exclude = [\n    "**/__pycache__",\n    "dist",\n    ".venv",\n'
        '    "build_env",\n    "min_env",\n    "tests/data.py",\n]\n',
        encoding="utf-8",
    )

    finished = build(uv, copy)

    assert finished.returncode != 0
    assert "venv314" in finished.stderr
