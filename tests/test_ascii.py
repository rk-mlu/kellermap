"""Python-Dateien sind reines ASCII.

Die Verabredung gilt fuer Quellcode, Tests und Skripte, nicht fuer die
Dokumentation: ``docs/`` und ``README.md`` duerfen Umlaute und typografische
Zeichen tragen, ``.py``-Dateien nicht. Dort steht ``Alpoege``, ``ueber``,
``Section 4`` und ``F o G``.

Bis 0.4 erzwang das nichts. ``ruff`` prueft mit RUF001 bis RUF003 nur
verwechselbare Zeichen; ein Ringoperator faellt nicht darunter, und genau
einer stand seit 0.3 unbemerkt im Docstring von ``PolynomialMap.compose``.
Eine Regel ohne Gate ist eine Bitte.

Geprueft werden ``src``, ``tests`` und ``scripts`` namentlich und nicht der
Baum ab der Wurzel. ``make build-test`` und ``make test-minimum`` legen
virtuelle Umgebungen im Arbeitsverzeichnis an, und deren Fremdpakete waeren
weder unsere Dateien noch unsere Verabredung.
"""

import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Die Verzeichnisse, fuer die die Verabredung gilt.
CHECKED = ("src", "tests", "scripts")


def non_ascii(text: str) -> list[tuple[int, int, str]]:
    """Return ``(line, column, character)`` for every character above 127.

    Lines and columns are counted from one, so that the result can be pasted
    into an editor.
    """
    return [
        (number, column, character)
        for number, line in enumerate(text.splitlines(), start=1)
        for column, character in enumerate(line, start=1)
        if ord(character) > 127
    ]


def python_files() -> list[Path]:
    """Return every Python file the agreement covers, in a stable order."""
    return sorted(
        path
        for directory in CHECKED
        for path in (ROOT / directory).rglob("*.py")
        if "__pycache__" not in path.parts
    )


def describe(path: Path, findings: list[tuple[int, int, str]]) -> str:
    """Return a report that names the character and where it sits."""
    return "\n".join(
        f"{path.relative_to(ROOT)}:{line}:{column}: "
        f"{character!r} ({unicodedata.name(character, 'unnamed')})"
        for line, column, character in findings
    )


def test_the_directories_are_there() -> None:
    """Sonst prueft der Test still nichts.

    Ein Tippfehler in ``CHECKED`` oder ein verschobenes Verzeichnis liesse den
    Hauptteil ueber eine leere Liste laufen und trotzdem gruen werden.
    """
    assert all((ROOT / directory).is_dir() for directory in CHECKED)
    assert len(python_files()) > 20


def test_every_python_file_is_pure_ascii() -> None:
    reports = [
        describe(path, findings)
        for path in python_files()
        if (findings := non_ascii(path.read_text(encoding="utf-8")))
    ]

    assert not reports, (
        "Python-Dateien sind reines ASCII; Umlaute und typografische Zeichen "
        "gehoeren nach docs/ und README.md:\n" + "\n".join(reports)
    )


def test_the_check_finds_a_non_ascii_character(tmp_path: Path) -> None:
    """Negativkontrolle: ohne sie sagt der Erfolgsfall nichts.

    Genau der Fall, der bis 0.4 durchging -- der Ringoperator in einem
    Docstring.
    """
    source = tmp_path / "offending.py"
    source.write_text('"""Return ``self \u2218 other``."""\n', encoding="utf-8")

    findings = non_ascii(source.read_text(encoding="utf-8"))

    assert findings == [(1, 18, "\u2218")]
    assert "RING OPERATOR" in describe(ROOT / "src", findings)


def test_the_check_passes_a_pure_ascii_file(tmp_path: Path) -> None:
    source = tmp_path / "clean.py"
    source.write_text('"""Return ``self o other``."""\n', encoding="utf-8")

    assert non_ascii(source.read_text(encoding="utf-8")) == []


def test_an_unnamed_character_is_still_reported() -> None:
    """Nicht jedes Zeichen traegt einen Unicode-Namen.

    Der Bericht darf daran nicht scheitern, sonst verdeckt ein Fehler im
    Melder den Fund, den er melden soll.
    """
    report = describe(ROOT / "src" / "example.py", [(3, 5, "\x85")])

    assert "unnamed" in report
