"""Was die Dokumentation ueber den Code sagt, wird hier nachgeschlagen.

Jedes Audit dieses Meilensteins hat Dokumentationswidersprueche gefunden, und
jedes Mal wurden sie einzeln behoben. Der Grund, warum das nicht reicht: eine
Verpflichtung wird umgeschrieben, und die Stellen, die sie erwaehnen, bleiben
stehen. Niemand faellt darueber, weil nichts sie nachrechnet.

Die Tests hier rechnen sie nach. Sie pruefen nicht, ob ein Text gut ist -- das
kann kein Test --, sondern ob die Behauptungen darin noch stimmen: ob eine
zitierte Verpflichtung existiert, ob eine Zusammenfassung wie ``REV-1 to REV-11``
die tatsaechliche Zahl nennt, ob eine Signatur im normativen Entwurf zur
gebauten passt, und ob eine Formel den Koeffizienten traegt, den ``G`` seit
BCW-11 hat.

Sie ersetzen kein Audit. Was sie ersetzen, ist die Frage "haben wir diesmal
alle Stellen gefunden".
"""

import inspect
import re
from pathlib import Path

import pytest

from kellermap.bcw import BCWStep

ROOT = Path(__file__).resolve().parent.parent
CONTRACTS = (ROOT / "docs" / "contracts.md").read_text(encoding="utf-8")

PROSE = sorted(
    [ROOT / "README.md", *(ROOT / "docs").glob("*.md")],
    key=lambda path: path.name,
)
CODE = sorted(
    [
        *(ROOT / "src" / "kellermap").rglob("*.py"),
        *(ROOT / "scripts").glob("*.py"),
        *(ROOT / "tests").glob("*.py"),
    ],
    key=lambda path: path.name,
)

# Ein Bezeichner wie ``BCW-11`` am Anfang einer Verpflichtung: fett, mit
# Gedankenstrich dahinter. Zurueckgezogene stehen weiter auf der Seite und
# zaehlen mit, denn ein Verweis auf sie ist kein Fehler.
DEFINED = re.compile("^\\*\\*([A-Z]{2,4}-\\d+) \u2014", re.MULTILINE)
CITED = re.compile(r"\b([A-Z]{2,4}-\d+)\b")
RANGE = re.compile(r"\b([A-Z]{2,4})-(\d+) to ([A-Z]{2,4})-(\d+)\b")

FAMILIES = {"COL", "RC", "BCW", "LIN", "TRA", "RED", "SEA", "REV"}


def obligations() -> dict[str, set[int]]:
    """Return the numbers of every obligation the contract page defines."""
    found: dict[str, set[int]] = {}
    for identifier in DEFINED.findall(CONTRACTS):
        family, number = identifier.rsplit("-", 1)
        found.setdefault(family, set()).add(int(number))

    return found


DEFINITIONS = obligations()


def test_the_page_defines_every_family() -> None:
    """Sonst prueft der Rest dieses Moduls gegen eine leere Menge."""
    assert FAMILIES <= set(DEFINITIONS)
    assert all(numbers for numbers in DEFINITIONS.values())


@pytest.mark.parametrize("path", PROSE + CODE, ids=lambda path: path.name)
def test_every_cited_obligation_exists(path: Path) -> None:
    """Ein Verweis auf eine Verpflichtung, die es nicht gibt, ist ein Fehler.

    Er entsteht beim Umnummerieren und beim Erfinden aus dem Gedaechtnis, und
    beides ist in diesem Meilenstein vorgekommen.
    """
    text = path.read_text(encoding="utf-8")
    unknown = {
        identifier
        for identifier in CITED.findall(text)
        if identifier.rsplit("-", 1)[0] in FAMILIES
        and int(identifier.rsplit("-", 1)[1])
        not in DEFINITIONS[identifier.rsplit("-", 1)[0]]
    }

    assert not unknown, f"{path.name} cites {sorted(unknown)}, which do not exist"


@pytest.mark.parametrize("path", PROSE + CODE, ids=lambda path: path.name)
def test_every_open_ended_range_reaches_the_last_obligation(path: Path) -> None:
    """Ein Bereich, der *alle* nennen will, muss bis zur letzten laufen.

    Genau diese Zusammenfassungen veralten, wenn eine Verpflichtung dazukommt:
    der Satz sieht weiterhin richtig aus und ist falsch.

    Nicht jeder Bereich will alle nennen. ``verify`` prueft ``BCW-1 to BCW-7``
    und nicht mehr, und das ist eine Aussage und kein Versehen. Erfasst werden
    deshalb nur die Bereiche, deren Umgebung sie als vollstaendig ausgibt --
    ``see``, ``under``, ``state``, ``cover``. Wer eine Auswahl meint, schreibt
    sie ohne diese Woerter, und wer es nicht tut, faellt hier auf.
    """
    text = path.read_text(encoding="utf-8")
    claiming = re.compile(
        r"(?:see|under|states?|cover(?:s|ed)?|obligations? of)[^.]{0,40}?"
        r"([A-Z]{2,4})-1 to ([A-Z]{2,4})-(\d+)",
        re.IGNORECASE,
    )
    stale = [
        f"{first}-1 to {second}-{high}"
        for first, second, high in claiming.findall(text)
        if first == second
        and first in FAMILIES
        and int(high) != max(DEFINITIONS[first])
    ]

    assert not stale, (
        f"{path.name} presents {stale} as the whole family, which now runs to "
        f"{ {family: max(numbers) for family, numbers in DEFINITIONS.items()} }"
    )


def test_the_class_sketch_matches_the_constructor() -> None:
    """Der normative Entwurf in ``contracts.md`` gegen die gebaute Signatur.

    Das Feld ``coefficient`` fehlte dort zwei Release-Kandidaten lang, nachdem
    BCW-11 es eingefuehrt hatte.
    """
    sketch = CONTRACTS[CONTRACTS.index("class BCWStep") :]
    sketch = sketch[: sketch.index("```")]
    built = set(inspect.signature(BCWStep.build).parameters) - {"cls", "source"}

    for parameter in built:
        assert parameter in sketch or parameter.replace("filtration_", "") in sketch, (
            f"the class sketch does not mention {parameter}"
        )


@pytest.mark.parametrize("path", PROSE + CODE, ids=lambda path: path.name)
def test_no_formula_writes_G_without_its_coefficient(path: Path) -> None:
    """``G`` skaliert das entfernte Produkt seit BCW-11.

    Die ungewichtete Formel stand nach der Aenderung noch an vier Stellen, und
    drei Audits haben sie nacheinander gefunden. Gesucht wird die Gestalt
    ``X... - A B`` ohne Faktor davor, in Text und in Docstrings.
    """
    text = path.read_text(encoding="utf-8")
    # Ein *Produkt* hinter dem Minus, denn genau das ist ``G``. Eine einzelne
    # Groesse ist die Verschiebung eines ``TranslationStep`` und hat keinen
    # Koeffizienten.
    unweighted = re.findall(
        r"X_?\{?\w*\}?\s*(?:\|--?>|->|\\mapsto|\u2192)\s*X_?\{?\w*\}?\s*-\s*"
        r"(?!coefficient\b|lambda\b|\\lambda\b|c\s+X|c\s*\*)"
        r"[A-Za-z]\w*\s*(?:\*|\s)\s*[A-Za-z]\w*",
        text,
    )

    assert not unweighted, f"{path.name} writes G unweighted: {unweighted[:3]}"
