"""Report lines that read like German.

``AGENTS.md`` requires English everywhere in the repository. Until work package
2 of milestone 0.5 it granted one exception, for test docstrings and test
comments. The exception is withdrawn: every audit of milestone 0.4 read the
tests, a test is the sharpest statement of what an obligation means, and half
of them could not be read by a reviewer who does not read German.

Withdrawing the rule and translating 1847 lines are two different sizes of
work. The rule is withdrawn here. The translation runs module by module, and
``NOT_YET_TRANSLATED`` below is what is left of it. The list only shrinks, and
the test at the end of this module makes that mechanical: a module that has
been translated and left in the list fails, so the list cannot rot into a
permanent exemption.

This check is a heuristic and says so. A language cannot be recognised
reliably from a word list. What it catches is the shape the defect takes here:
a German sentence, or the tail of one left behind when a block was replaced
only in part.

Two decisions in it are the finding of work package 1 rather than a
preference.

One occurrence is enough, and the word list is long. The inventory that
prepared work package 1 counted lines carrying at least two words from a much
shorter list, and it let six German lines through. Measured against that
inventory, the two causes were separate. Four fragments scored zero because no
word of theirs was in the list at all: ``# scheitern kann.``,
``# bezeichnen liesse.``, ``# umdeuten, statt sie mitzunehmen.`` and
``# SymPys aeltere Domains tragen ihre Koeffizienten als``. One scored exactly
one and was hidden by the threshold:
``# x1*x2 liegt seit Schritt 3 als Komponente 8 vor.``. Four of the six reached
a delivered package and were found by the maintainer.

Both causes are addressed, because either alone would have left some of the six
in place.

The word list is curated against English, and every collision found is
recorded here. ``stand``, ``mit``, ``also``, ``hat``, ``war``, ``man`` and
``die`` are German words that are also English words, so they are not in the
list. ``mit`` was removed after it flagged ``MIT License`` in
``pyproject.toml``, and ``stand`` after it flagged ``the gates below stand in
AGENTS.md``.

An earlier version also flagged any word containing ``ae``, ``oe`` or ``ue``,
on the reasoning that a repository restricted to ASCII writes German umlauts
that way. Measured, that rule produced 573 reports over the library alone:
``does``, ``coefficient``, ``value`` and ``sequence`` all contain one of the
three. It is not here.

This module exempts itself. Its word list is German by necessity, and a check
that reports its own definition is unusable. That is the only exemption which
survives the end of work package 2.
"""

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent

SCANNED = (
    "src/kellermap/*.py",
    "src/kellermap/bcw/*.py",
    "scripts/*.py",
    "tests/*.py",
    "pyproject.toml",
    "Makefile",
    ".gitignore",
    ".github/workflows/ci.yml",
)

# Die Uebersetzung laeuft modulweise. Was hier steht, ist der Rest.
NOT_YET_TRANSLATED = frozenset(
    {
        "test_admissible_shapes.py",
        "test_alpoege15.py",
        "test_alpoege19.py",
        "test_bcw17.py",
        "test_bcw_step.py",
        "test_documentation.py",
        "test_invariants.py",
        "test_packaging.py",
        "test_peeling.py",
        "test_polynomial_map.py",
        "test_reduction.py",
        "test_scripts.py",
        "test_search.py",
        "test_translation.py",
    }
)

# This module holds the word list and would report every line of it.
EXEMPT = frozenset({Path(__file__).name})

WORDS = (
    "der das den dem des ein eine einen einem einer und oder aber nicht kein "
    "keine keinen keinem ist sind waren wird werden wuerde wuerden waere waeren "
    "haette haetten haben sich dass weil wenn nur schon noch auch nach vor ueber "
    "unter zum zur beim vom als wie steht statt kann koennen konnte "
    "muss muessen soll sollen darf duerfen laesst lassen liess liesse gibt "
    "damit dann sonst jede jeder jedes jedem alle allen allem derselbe denselben "
    "dieselbe demselben dieser diesem diese dieses hier dort etwa sie ihre ihren "
    "ihrem seit zwei drei vier fuenf sechs sieben acht neun zehn liegt liegen "
    "tragen traegt scheitern scheitert umdeuten mitzunehmen bezeichnen "
    "Schritt Schritte Komponente Koeffizient Koeffizienten Zeile Grund"
).split()

GERMAN_WORD = re.compile(r"\b(" + "|".join(WORDS) + r")\b", re.IGNORECASE)

# Endings that are common in German and effectively absent from English.
GERMAN_ENDING = re.compile(r"\b\w{4,}(ung|ungen|keit|heit|schaft|lich|isch|ieren)\b")


def suspicious(line: str) -> bool:
    """Return whether ``line`` reads like German."""
    return bool(GERMAN_WORD.search(line) or GERMAN_ENDING.search(line))


def german_lines(path: Path) -> list[tuple[int, str]]:
    """Return the suspicious lines of one file, with their numbers."""
    return [
        (number, line.strip())
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1)
        if suspicious(line)
    ]


def scanned() -> list[Path]:
    """Return every file the rule covers, in a stable order."""
    found: list[Path] = []
    for pattern in SCANNED:
        found += [
            path
            for path in ROOT.glob(pattern)
            if path.is_file()
            and "__pycache__" not in path.parts
            and path.name not in EXEMPT
        ]

    return sorted(set(found))


def translated() -> list[Path]:
    """Return the files the rule already covers in full."""
    return [path for path in scanned() if path.name not in NOT_YET_TRANSLATED]


# --------------------------------------------------------------------------
# The rule
# --------------------------------------------------------------------------


@pytest.mark.parametrize("path", translated(), ids=lambda path: path.name)
def test_no_line_reads_like_german(path: Path) -> None:
    """The rule of ``AGENTS.md``, for every file it already covers."""
    found = german_lines(path)
    shown = "\n".join(f"  {number}: {line[:80]}" for number, line in found[:5])

    assert not found, f"{path.name} has {len(found)} German lines:\n{shown}"


def test_every_file_is_either_covered_or_listed() -> None:
    """No file falls between the rule and the remainder.

    The list names modules, so a name that matches nothing is a leftover from a
    rename and would silently shrink what is checked.
    """
    names = {path.name for path in scanned()}

    assert NOT_YET_TRANSLATED <= names, sorted(NOT_YET_TRANSLATED - names)
    assert names == {path.name for path in translated()} | NOT_YET_TRANSLATED


def test_the_remainder_is_still_a_remainder() -> None:
    """A module that has been translated has to leave the list.

    Without this, the list is a permanent exemption that nobody notices. With
    it, the last module translated makes the list empty by force, and the
    exception ``AGENTS.md`` used to grant disappears with it.
    """
    finished = sorted(
        name for name in NOT_YET_TRANSLATED if not german_lines(ROOT / "tests" / name)
    )

    assert not finished, f"translated and still listed: {finished}"


def test_the_remainder_is_only_ever_tests() -> None:
    """Work package 1 covered everything outside ``tests/``.

    A file from ``src/`` or ``scripts/`` in the list would mean that repair
    came undone.
    """
    assert all(
        name.startswith("test_") or name == "data.py" for name in NOT_YET_TRANSLATED
    )


# --------------------------------------------------------------------------
# The negative controls
# --------------------------------------------------------------------------


def test_the_fragments_that_a_partial_replacement_leaves_are_caught() -> None:
    """The six cases of work package 1, four of which reached a delivery."""
    for line in (
        "# scheitern kann.",
        "# bezeichnen liesse.",
        "# umdeuten, statt sie mitzunehmen.",
        "# SymPys aeltere Domains tragen ihre Koeffizienten als",
        "# x1*x2 liegt seit Schritt 3 als Komponente 8 vor.",
        "'py.typed fehlt im Wheel: kellermap waere fuer Typpruefer untypisiert'",
    ):
        assert suspicious(line), line


def test_a_single_occurrence_is_enough() -> None:
    """A line with exactly one German word is German.

    A threshold of two would pass this one. It is the message of the py.typed
    check in the Makefile, and it survived the inventory of work package 1.
    """
    line = "'py.typed fehlt im Wheel: kellermap waere fuer Typpruefer untypisiert'"

    assert len(GERMAN_WORD.findall(line)) == 1
    assert suspicious(line)


def test_english_that_collides_with_german_is_left_alone() -> None:
    """The seven words dropped from the list, in the lines that dropped them."""
    for line in (
        '"License :: OSI Approved :: MIT License",',
        "# The two gates below stand in AGENTS.md among the release checks.",
        "# The coefficient value does not change; this sequence is unique.",
        "# A man also has a hat, and there was a war.",
        "# The die is cast.",
    ):
        assert not suspicious(line), line


def test_a_german_ending_is_caught_without_a_listed_word() -> None:
    """The second rule, on a sentence the word list alone would miss."""
    assert suspicious("# Kanonisierung.")
    assert not GERMAN_WORD.search("# Kanonisierung.")


def test_the_module_that_holds_the_list_is_not_scanned() -> None:
    """Otherwise the list reports itself and the gate is unusable."""
    assert Path(__file__).name in EXEMPT
    assert Path(__file__) not in scanned()
