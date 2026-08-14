"""Was das Quellarchiv ausliefert, und was nicht.

Der Inhalt des sdist hing bis 0.4.0rc15 vom Zustand des Arbeitsverzeichnisses
ab. ``pyproject.toml`` zaehlte auf, was nicht mitsollte, und eine
Ausschlussliste ist gegen Namen, die noch niemand gewaehlt hat, nicht zu
vervollstaendigen: eine Umgebung namens ``.venv314`` stand in keiner der drei
Listen -- ``pyproject.toml``, ``.gitignore``, ``Makefile`` -- und ``uv build``
brach mit "Invalid tar file" ab, weil in einer virtuellen Umgebung absolute
Symlinks stehen. Ein externes Audit hat es gebaut.

Seither ist es eine Positivliste. Was dort nicht steht, faehrt nicht mit.

Zwei Umgebungen werden gelegt, und der Unterschied zwischen ihnen ist der
Punkt. ``.venv314`` ist der gemeldete Name; ihn deckt seit 0.4.0rc15 auch
``.gitignore`` ab, und das Bauwerkzeug liest ``.gitignore``. Ein Test mit nur
dieser Umgebung koennte also gruen sein, ohne dass die Positivliste irgendetwas
tut. ``venv314`` ohne Punkt deckt keine Ignorierliste ab. An ihr allein haengt,
ob die Liste in ``pyproject.toml`` traegt, und mit der alten Ausschlussliste
faehrt sie nachweislich mit und bricht den Bau.

Gebaut wird wirklich, und zwar vollstaendig. ``uv build --sdist`` allein haette
den gemeldeten Fehler nicht gezeigt: er entsteht beim Auspacken des Archivs
fuer den Wheel-Bau, nicht beim Packen.

Zwei Baeue kosten zusammen etwa eineinhalb Sekunden, also steht nichts davon
hinter einem langsamen Marker. Ein Paketierungsfehler faellt an dem Tag auf,
an dem er entsteht, und nicht in der naechtlichen Kette.
"""

import shutil
import subprocess
import tarfile
from collections.abc import Iterator
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent

# Was das Archiv oben tragen soll. ``PKG-INFO`` erzeugt das Bauwerkzeug selbst
# und steht deshalb nicht in ``pyproject.toml``.
SHIPPED = {
    "PKG-INFO",
    "src",
    "tests",
    "docs",
    "scripts",
    ".github",
    "AGENTS.md",
    "CHANGELOG.md",
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

    if found is None:  # pragma: no cover - auf jeder Umgebung des Projekts da
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
    """Der gemeldete Fehler.

    Dass die Vorrichtung ueberhaupt ein Archiv geliefert hat, ist die Aussage;
    der Test steht hier, damit ein Fehlschlag beim Namen genannt wird.
    """
    assert archive.getnames()


def test_nothing_from_an_environment_ships(archive: tarfile.TarFile) -> None:
    """Und zwar keine einzige Datei aus einer der beiden.

    Der erste Versuch reparierte den Bau und lieferte trotzdem
    ``.venv314/.gitignore`` aus: ohne fuehrenden Schraegstrich gilt ein Muster
    der Positivliste auf jeder Ebene, und ``uv venv`` legt eine solche Datei in
    jede Umgebung. Geprueft wird deshalb der Inhalt und nicht der Rueckgabewert.
    """
    inside = [name for name in entries(archive) if "venv" in name]

    assert not inside, inside


def test_the_archive_carries_exactly_what_is_promised(
    archive: tarfile.TarFile,
) -> None:
    """Die Gegenkontrolle zur Positivliste.

    Eine Positivliste kann auch daran scheitern, dass sie zu wenig ausliefert,
    und ein Archiv ohne Inhalt enthaelt auch keine Umgebung. Der Test oben
    allein waere damit erfuellt.
    """
    top = {name.split("/", 1)[0] for name in entries(archive)}

    assert top == SHIPPED


def test_the_sources_and_the_fixed_data_are_where_they_belong(
    archive: tarfile.TarFile,
) -> None:
    """Stichproben in die Tiefe, in beide Richtungen."""
    inside = set(entries(archive))

    assert "src/kellermap/__init__.py" in inside
    assert "src/kellermap/py.typed" in inside
    assert "tests/test_packaging.py" in inside
    assert "docs/contracts.md" in inside

    # Fremde Mathematik ohne ermittelbare Lizenz, siehe pyproject.toml.
    assert "tests/data.py" not in inside

    assert not [name for name in inside if "__pycache__" in name]


def test_an_exclusion_list_lets_an_unforeseen_name_through(
    uv: str,
    tmp_path: Path,
) -> None:
    """Warum es eine Positivliste ist und keine laengere Ausschlussliste.

    Der Bau laeuft hier gegen die Liste, die bis 0.4.0rc15 in
    ``pyproject.toml`` stand. ``venv314`` steht in keiner ihrer Zeilen und in
    keiner Ignorierliste, faehrt mit, und das Auspacken des Archivs fuer den
    Wheel-Bau bricht an dem absoluten Symlink darin ab. Genau der Fehler, den
    das Audit gemeldet hat, nur unter einem Namen, den auch eine erweiterte
    Ausschlussliste nicht vorhergesehen haette.

    Ohne diesen Test sagt die Sammlung nichts darueber, ob die Positivliste
    etwas leistet: den gemeldeten Namen faengt inzwischen schon ``.gitignore``
    ab, das das Bauwerkzeug mitliest.
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
