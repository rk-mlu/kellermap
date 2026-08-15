"""Python files are pure ASCII.

The agreement covers source code, tests and scripts, and not the
documentation. ``docs/`` and ``README.md`` may carry umlauts and typographic
characters, ``.py`` files may not. There they read ``Alpoege``,
``Section 4`` and ``F o G``.

Until 0.4 nothing enforced this. ``ruff`` checks only confusable characters,
under RUF001 to RUF003. A ring operator is not one of them, and exactly one had
stood unnoticed in the docstring of ``PolynomialMap.compose`` since 0.3. A rule
without a gate is a request.

``src``, ``tests`` and ``scripts`` are named explicitly rather than walking the
tree from the root. ``make build-test`` and ``make test-minimum`` create virtual
environments in the working directory, and the third-party packages in them are
neither our files nor our agreement.
"""

import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# The directories the agreement covers.
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
    """Otherwise the test silently checks nothing.

    A typing slip in ``CHECKED`` or a moved directory would let the main test
    run over an empty list and still turn green.
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
        "Python files are pure ASCII. Umlauts and typographic characters "
        "belong in docs/ and README.md:\n" + "\n".join(reports)
    )


def test_the_check_finds_a_non_ascii_character(tmp_path: Path) -> None:
    """A negative control. Without it the passing case says nothing.

    Exactly the case that went through until 0.4: the ring operator in a
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
    """Not every character carries a Unicode name.

    The report must not fail on that, otherwise a defect in the reporter hides
    the finding it is meant to report.
    """
    report = describe(ROOT / "src" / "example.py", [(3, 5, "\x85")])

    assert "unnamed" in report
