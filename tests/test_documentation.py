"""Was die Dokumentation ueber den Code sagt, wird hier nachgeschlagen.

Jedes Audit dieses Meilensteins hat Dokumentationswidersprueche gefunden, und
jedes Mal wurden sie einzeln behoben. Der Grund, warum das nicht reicht: eine
Verpflichtung wird umgeschrieben, und die Stellen, die sie erwaehnen, bleiben
stehen. Niemand faellt darueber, weil nichts sie nachrechnet.

Die Tests hier rechnen sie nach. Sie pruefen nicht, ob ein Text gut ist -- das
kann kein Test --, sondern ob die Behauptungen darin noch stimmen: ob eine
zitierte Verpflichtung existiert, ob eine Zusammenfassung wie ``REV-1 to REV-12``
die tatsaechliche Zahl nennt, ob eine Signatur im normativen Entwurf zur
gebauten passt, und ob eine Formel den Koeffizienten traegt, den ``G`` seit
BCW-11 hat.

Sie ersetzen kein Audit. Was sie ersetzen, ist die Frage "haben wir diesmal
alle Stellen gefunden".

Jede Pruefung steht seit 0.4.0rc9 zweimal: einmal ueber den Dateien des
Projekts und einmal ueber einem Text, in den der Fehler absichtlich
hineingeschrieben ist. Ohne den zweiten Teil ist nicht zu unterscheiden, ob
eine Pruefung etwas nachweist oder nur zufaellig durchlaeuft. Die erste Luecke,
die die Gegenkontrollen gefunden haben, war die eigene: ``FAMILIES`` liess eine
Familie aus.

Dieses Modul liest auch sich selbst, weil es unter ``CODE`` faellt. Ein
Beispiel der falschen Gestalt darf deshalb nicht woertlich hier stehen; die
Gegenkontrollen setzen ihre Texte zusammen.
"""

import inspect
import re
from pathlib import Path

import pytest

from kellermap.bcw import BCWStep

ROOT = Path(__file__).resolve().parent.parent
CONTRACTS = (ROOT / "docs" / "contracts.md").read_text(encoding="utf-8")

# ``CONTRIBUTING.md`` steht hier, weil es Verpflichtungen zitiert. Ein
# veralteter Bezeichner in einer Anleitung ist derselbe Fehler wie einer in
# ``contracts.md``, und die Anleitung liest, wer neu dazukommt.
PROSE = sorted(
    [
        ROOT / "README.md",
        ROOT / "CONTRIBUTING.md",
        *(ROOT / "docs").glob("*.md"),
    ],
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

# Ein Bereich ``X-1 to X-n`` gilt als Zusammenfassung der ganzen Familie, wenn
# im selben Satz eines der Woerter aus ``CLAIMING_WORD`` steht. Die Woerter
# stehen nur hier und nicht zusaetzlich in einem Docstring: zwei Listen weichen
# voneinander ab, sobald jemand eine davon erweitert. Bis 0.4.0rc8 gab es sie,
# und sie wichen ab -- ``state`` stand im Docstring und nicht im Ausdruck,
# ``siehe`` und ``obligations of`` umgekehrt.
#
# Die Wortgrenzen sind noetig und nicht Zierde: ohne die vordere trifft
# ``state`` in ``overstated``, und der Ausdruck meldete den Aufruf einer
# Gegenkontrolle unten als veralteten Bereich.
CLAIMING_WORD = re.compile(
    r"\b(?:see|siehe|under|state[sd]?|cover(?:s|ed)?|obligations? of)\b",
    re.IGNORECASE,
)

# Der Bereich selbst. ``\s+`` und nicht ein Leerzeichen: die Zusammenfassungen
# in den Docstrings sind auf 79 Spalten umbrochen, und ``LIN-1 to\nLIN-6`` ist
# derselbe Satz.
WHOLE_FAMILY = re.compile(r"\b([A-Z]{2,4})-1\s+(?:to|bis)\s+([A-Z]{2,4})-(\d+)\b")

# Satzende: ein Punkt mit Leerraum dahinter, oder eine Leerzeile. Der Punkt in
# ``docs/contracts.md`` ist keines. Bis 0.4.0rc8 lief die Suche nach dem
# Signalwort ueber ein Fenster von vierzig Zeichen ohne Punkt, und genau dieser
# Dateiname stand darin: von elf Zusammenfassungen im Repository erreichte die
# Pruefung zwei, und alle drei Docstrings der Form "See ``docs/contracts.md``,
# X-1 to X-n" lagen ausserhalb.
SENTENCE_END = re.compile(r"\.\s|\n\s*\n")

# ``G`` in der Gestalt ``X... |-> X... - A B``, also mit einem *Produkt* hinter
# dem Minus und ohne Faktor davor. Eine einzelne Groesse ist die Verschiebung
# eines ``TranslationStep`` und hat keinen Koeffizienten.
UNWEIGHTED_G = re.compile(
    r"X_?\{?\w*\}?\s*(?:\|--?>|->|\\mapsto|\u2192)\s*X_?\{?\w*\}?\s*-\s*"
    r"(?!coefficient\b|lambda\b|\\lambda\b|c\s+X|c\s*\*)"
    r"[A-Za-z]\w*\s*(?:\*|\s)\s*[A-Za-z]\w*"
)

# Die Familien, die ``contracts.md`` fuehrt. Die Liste steht hier und wird
# nicht aus der Seite abgeleitet: sie ist die Zusage, welche Familien geprueft
# werden, und eine abgeleitete Liste koennte eine Familie verlieren, ohne dass
# etwas auffaellt. Die Schrittfamilie fehlte darin von 0.3 bis 0.4.0rc8, und
# weil beide Filter unten gegen ``FAMILIES`` sieben, war jede Zitierung dieser
# Familie in der Zeit ungeprueft.
FAMILIES = {"BCW", "COL", "LIN", "RC", "RED", "REV", "SEA", "STEP", "TRA"}

# Die Versionsnummer steht an drei Stellen: in ``pyproject.toml``, im
# Projektstand des README und als oberste Ueberschrift des Changelog. Die
# erste ist die verbindliche. ``tomllib`` gibt es auf 3.10 nicht, und diese
# eine Zeile braucht keinen Parser.
DECLARED_VERSION = re.compile(r'^version = "(.+)"$', re.MULTILINE)
README_VERSION = re.compile(r"^Current version: \*\*(.+)\*\*$", re.MULTILINE)
NEWEST_RELEASE = re.compile(r"^## (\S+)$", re.MULTILINE)


def obligations() -> dict[str, set[int]]:
    """Return the numbers of every obligation the contract page defines."""
    found: dict[str, set[int]] = {}
    for identifier in DEFINED.findall(CONTRACTS):
        family, number = identifier.rsplit("-", 1)
        found.setdefault(family, set()).add(int(number))

    return found


DEFINITIONS = obligations()


def unknown_citations(text: str) -> set[str]:
    """Return every obligation ``text`` cites that the contract page lacks."""
    found = set()
    for identifier in CITED.findall(text):
        family, number = identifier.rsplit("-", 1)
        if family in FAMILIES and int(number) not in DEFINITIONS[family]:
            found.add(identifier)

    return found


def overstated_ranges(text: str) -> list[str]:
    """Return every range in ``text`` that claims a family and falls short.

    A sentence at a time, so that an enumeration is covered to its end: one
    ``See`` in front of four ranges makes a claim about all four, and a
    pattern anchored at the signal word reaches only the first.
    """
    found = []
    for sentence in SENTENCE_END.split(text):
        if not CLAIMING_WORD.search(sentence):
            continue
        found += [
            f"{first}-1 to {second}-{high}"
            for first, second, high in WHOLE_FAMILY.findall(sentence)
            if first == second
            and first in FAMILIES
            and int(high) != max(DEFINITIONS[first])
        ]

    return found


def unweighted_formulas(text: str) -> list[str]:
    """Return every occurrence of ``G`` in ``text`` written without a factor."""
    return UNWEIGHTED_G.findall(text)


def class_sketch(name: str) -> str:
    """Return the normative code block for ``name`` from the contract page."""
    sketch = CONTRACTS[CONTRACTS.index(f"class {name}") :]

    return sketch[: sketch.index("```")]


def unmentioned_parameters(sketch: str, parameters: set[str]) -> set[str]:
    """Return the parameters of a constructor that ``sketch`` does not name.

    The second form covers ``filtration_level``, which the sketch carries as
    the field ``level``.
    """
    return {
        parameter
        for parameter in parameters
        if parameter not in sketch
        and parameter.replace("filtration_", "") not in sketch
    }


def only_match(pattern: "re.Pattern[str]", path: Path) -> str:
    """Return the one group ``pattern`` finds in ``path``, or fail saying so."""
    found = pattern.findall(path.read_text(encoding="utf-8"))

    assert found, f"{path.name} does not carry {pattern.pattern}"

    return str(found[0])


def releases(path: Path) -> list[str]:
    """Return every release heading of a changelog, newest first."""
    found = NEWEST_RELEASE.findall(path.read_text(encoding="utf-8"))

    assert found, f"{path.name} carries no release heading"

    return [str(name) for name in found]


def formula(arrow: str, subtracted: str) -> str:
    """Build one line of the form ``X_index <arrow> X_index - <subtracted>``.

    Assembled rather than written out. This module is one of the files the
    scan below reads, so a literal example of the wrong form would make the
    module fail its own check.
    """
    return f"X_index {arrow} X_index - {subtracted}"


# --------------------------------------------------------------------------
# Ueber den Dateien des Projekts
# --------------------------------------------------------------------------


def test_the_page_defines_exactly_the_families_that_are_checked() -> None:
    """Gleichheit und nicht Teilmenge.

    Als Teilmenge geschrieben durfte ``contracts.md`` eine Familie fuehren,
    die ``FAMILIES`` nicht kennt, und genau das war der Fall: die
    Schrittfamilie stand seit 0.3 auf der Seite und in keinem Filter. Der Test
    lief gruen, weil ``FAMILIES <= set(DEFINITIONS)`` von einer fehlenden
    Familie nicht verletzt wird. Eine neue Familie zwingt jetzt dazu, diese
    Zeile mitzupflegen.
    """
    assert FAMILIES == set(DEFINITIONS)
    assert all(numbers for numbers in DEFINITIONS.values())


@pytest.mark.parametrize("path", PROSE + CODE, ids=lambda path: path.name)
def test_every_cited_obligation_exists(path: Path) -> None:
    """Ein Verweis auf eine Verpflichtung, die es nicht gibt, ist ein Fehler.

    Er entsteht beim Umnummerieren und beim Erfinden aus dem Gedaechtnis, und
    beides ist in diesem Meilenstein vorgekommen.
    """
    unknown = unknown_citations(path.read_text(encoding="utf-8"))

    assert not unknown, f"{path.name} cites {sorted(unknown)}, which do not exist"


@pytest.mark.parametrize("path", PROSE + CODE, ids=lambda path: path.name)
def test_every_open_ended_range_reaches_the_last_obligation(path: Path) -> None:
    """Ein Bereich, der *alle* nennen will, muss bis zur letzten laufen.

    Genau diese Zusammenfassungen veralten, wenn eine Verpflichtung dazukommt:
    der Satz sieht weiterhin richtig aus und ist falsch.

    Nicht jeder Bereich will alle nennen. ``verify`` prueft die ersten sieben
    der zwoelf BCW-Verpflichtungen und nicht mehr, und das ist eine Aussage und
    kein Versehen. Erfasst werden deshalb nur die Bereiche, deren Umgebung sie
    als vollstaendig ausgibt; die Woerter, an denen das erkannt wird, stehen in
    ``CLAIMING_WORD``. Wer eine Auswahl meint, schreibt sie ohne
    diese Woerter, und wer es nicht tut, faellt hier auf.
    """
    stale = overstated_ranges(path.read_text(encoding="utf-8"))

    assert not stale, (
        f"{path.name} presents {stale} as the whole family, which now runs to "
        f"{ {family: max(numbers) for family, numbers in DEFINITIONS.items()} }"
    )


def test_the_class_sketch_matches_the_constructor() -> None:
    """Der normative Entwurf in ``contracts.md`` gegen die gebaute Signatur.

    Das Feld ``coefficient`` fehlte dort zwei Release-Kandidaten lang, nachdem
    BCW-11 es eingefuehrt hatte.
    """
    built = set(inspect.signature(BCWStep.build).parameters) - {"cls", "source"}
    missing = unmentioned_parameters(class_sketch("BCWStep"), built)

    assert not missing, f"the class sketch does not mention {sorted(missing)}"


@pytest.mark.parametrize("path", PROSE + CODE, ids=lambda path: path.name)
def test_no_formula_writes_G_without_its_coefficient(path: Path) -> None:
    """``G`` skaliert das entfernte Produkt seit BCW-11.

    Die ungewichtete Formel stand nach der Aenderung noch an vier Stellen, und
    drei Audits haben sie nacheinander gefunden.
    """
    unweighted = unweighted_formulas(path.read_text(encoding="utf-8"))

    assert not unweighted, f"{path.name} writes G unweighted: {unweighted[:3]}"


def test_the_three_places_that_carry_the_version_agree() -> None:
    """``pyproject.toml``, der Projektstand im README, die oberste Ueberschrift.

    Drei Kopien einer Zahl, von Hand gepflegt, und bis 0.4.0rc8 rechnete nichts
    sie gegeneinander. Verbindlich ist ``pyproject.toml``; die beiden anderen
    haben ihr zu folgen.
    """
    declared = only_match(DECLARED_VERSION, ROOT / "pyproject.toml")

    assert only_match(README_VERSION, ROOT / "README.md") == declared
    assert only_match(NEWEST_RELEASE, ROOT / "CHANGELOG.md") == declared


def test_no_release_appears_twice_in_the_changelog() -> None:
    """Die Version zu vergleichen genuegt nicht, wenn sie zweimal dasteht.

    In 0.4.0rc9 stand ``## 0.4.0rc9`` zweimal auf der Seite: ein erster
    Abschnitt mit den intern gefundenen Befunden und ein zweiter, der sie mit
    den Auditbefunden zusammenfuehrte. Der Vergleich oben blieb gruen, weil er
    die erste gefundene Ueberschrift nimmt. Ein externes Audit hat es gesehen.
    """
    headings = releases(ROOT / "CHANGELOG.md")

    assert headings[0] == only_match(DECLARED_VERSION, ROOT / "pyproject.toml")
    assert len(headings) == len(set(headings)), (
        f"these releases appear more than once: "
        f"{sorted({name for name in headings if headings.count(name) > 1})}"
    )


# --------------------------------------------------------------------------
# Die Gegenkontrollen
#
# Jede prueft, dass die Pruefung darueber anschlaegt, wenn der Fehler da ist,
# und dass sie die erlaubte Gestalt in Ruhe laesst. Eine Pruefung ohne
# Gegenkontrolle kann leer sein, ohne dass es jemand merkt.
# --------------------------------------------------------------------------


@pytest.mark.parametrize("family", sorted(FAMILIES))
def test_an_invented_obligation_is_caught_in_every_family(family: str) -> None:
    """Und zwar in jeder, nicht nur in denen, an die gerade gedacht wurde.

    Eine erfundene Nummer der Schrittfamilie lief bis 0.4.0rc8 durch dieses
    Gate, weil die Familie nicht in ``FAMILIES`` stand. Ueber die Familien zu
    parametrisieren macht das Auslassen einer einzelnen unmoeglich.
    """
    invented = f"{family}-99"

    assert 99 not in DEFINITIONS[family]
    assert unknown_citations(f"See {invented} for the rest.") == {invented}


@pytest.mark.parametrize("family", sorted(FAMILIES))
def test_a_real_obligation_is_not_caught(family: str) -> None:
    """Sonst faende die Pruefung alles und wiese nichts nach."""
    real = f"{family}-{min(DEFINITIONS[family])}"

    assert not unknown_citations(f"See {real} for the rest.")


def test_an_identifier_outside_the_families_is_not_examined() -> None:
    """Eine Verpflichtung sieht anders aus als eine Kodierung oder eine Norm."""
    assert not unknown_citations("Encoded as UTF-8, and see RFC-3629.")


@pytest.mark.parametrize("family", sorted(FAMILIES))
def test_a_range_that_stops_short_is_caught(family: str) -> None:
    """Der Fall, den ein Zuwachs an Verpflichtungen erzeugt."""
    last = max(DEFINITIONS[family])
    short = f"See {family}-1 to {family}-{last - 1}."

    assert overstated_ranges(short) == [f"{family}-1 to {family}-{last - 1}"]
    assert not overstated_ranges(f"See {family}-1 to {family}-{last}.")


def test_a_range_without_a_claiming_word_is_left_alone() -> None:
    """Eine Auswahl ist erlaubt und soll es bleiben.

    ``verify`` prueft sieben der zwoelf BCW-Verpflichtungen, und ein Satz
    darueber ist eine Aussage und kein veralteter Bereich.
    """
    last = max(DEFINITIONS["BCW"])

    assert not overstated_ranges(f"Check BCW-1 to BCW-{last - 5} and no more.")


def test_the_claiming_words_of_both_languages_are_recognised() -> None:
    """Der Ausdruck traegt beide, und beide kommen im Repository vor."""
    short = max(DEFINITIONS["REV"]) - 1

    for phrasing in (
        f"See REV-1 to REV-{short}",
        f"Siehe REV-1 bis REV-{short}",
        f"under REV-1 to REV-{short}",
        f"It states REV-1 to REV-{short}",
        f"which covers REV-1 to REV-{short}",
        f"the obligations of REV-1 to REV-{short}",
    ):
        assert overstated_ranges(phrasing), phrasing


def test_a_file_name_between_the_word_and_the_range_does_not_hide_it() -> None:
    """Der Satz, in dem die Zusammenfassungen der Quelldateien stehen.

    ``docs/contracts.md`` traegt zwei Punkte, und ein Fenster ohne Punkte
    endete davor. Drei Docstrings waren so ungeprueft.
    """
    short = max(DEFINITIONS["REV"]) - 1
    sentence = f"See ``docs/contracts.md``, REV-1 to REV-{short}, for the rest."

    assert overstated_ranges(sentence) == [f"REV-1 to REV-{short}"]


def test_an_enumeration_is_covered_to_its_end() -> None:
    """Ein Signalwort vor vier Bereichen sagt etwas ueber alle vier.

    ``reduction.py`` fuehrt genau eine solche Aufzaehlung. Ein Ausdruck, der
    beim Signalwort ansetzt, erreicht davon den ersten Bereich.
    """
    last = max(DEFINITIONS["RED"])
    sentence = (
        f"See the obligations, STEP-1 to STEP-{max(DEFINITIONS['STEP'])}, "
        f"LIN-1 to LIN-{max(DEFINITIONS['LIN'])} and RED-1 to RED-{last - 1}."
    )

    assert overstated_ranges(sentence) == [f"RED-1 to RED-{last - 1}"]


def test_a_range_wrapped_across_a_line_is_still_one_range() -> None:
    """Die Docstrings sind auf 79 Spalten umbrochen, mitten im Bereich."""
    short = max(DEFINITIONS["LIN"]) - 1

    assert overstated_ranges(f"See LIN-1 to\n    LIN-{short}.") == [
        f"LIN-1 to LIN-{short}"
    ]


def test_a_claiming_word_in_another_sentence_does_not_reach_over() -> None:
    """Sonst faerbt ein einziges ``see`` eine ganze Datei ein."""
    short = max(DEFINITIONS["SEA"]) - 1

    assert not overstated_ranges(f"See the page. Here SEA-1 to SEA-{short} is meant.")


def test_a_claiming_word_inside_another_word_does_not_count() -> None:
    """Die Wortgrenze im Ausdruck, mit dem Fall, der sie erzwungen hat.

    ``overstated`` enthaelt ``state``. Ohne die vordere Wortgrenze meldete der
    Ausdruck den Aufruf einer Gegenkontrolle als Befund, und das Modul fiel
    ueber die eigene Pruefung.
    """
    short = max(DEFINITIONS["REV"]) - 1

    assert not overstated_ranges(f"overstated_ranges REV-1 to REV-{short}")
    assert not overstated_ranges(f"understood REV-1 to REV-{short}")


def test_an_unweighted_G_is_caught() -> None:  # noqa: N802
    """Die Gestalt, die drei Audits nacheinander gefunden haben."""
    assert unweighted_formulas(formula("|-->", "A * B"))
    assert unweighted_formulas(formula("->", "P Q"))
    assert unweighted_formulas(formula("\u2192", "P*Q"))


def test_a_weighted_G_is_not_caught() -> None:  # noqa: N802
    """Die beiden Schreibweisen, die das Repository benutzt."""
    assert not unweighted_formulas(formula("|-->", "coefficient * A * B"))
    assert not unweighted_formulas(formula("|->", "c X_u X_v"))


def test_a_translation_is_not_a_G() -> None:  # noqa: N802
    """Eine einzelne Groesse hinter dem Minus ist die Verschiebung.

    ``TranslationStep`` verschiebt um eine Konstante, und die traegt keinen
    Koeffizienten. Faende der Ausdruck sie, waere TRA-1 nicht mehr
    aufschreibbar.
    """
    assert not unweighted_formulas(formula("|->", "c_index"))
    assert not unweighted_formulas(formula("|->", "shift"))


def test_a_missing_field_in_the_class_sketch_is_caught() -> None:
    """Der Fall vom Ende von 0.4: BCW-11 kam, das Feld fehlte im Entwurf."""
    assert unmentioned_parameters("class BCWStep: source target", {"coefficient"})
    assert not unmentioned_parameters("class BCWStep: coefficient", {"coefficient"})


def test_the_sketch_carries_the_filtration_level_as_level() -> None:
    """Die zweite Schreibweise ist eine Zusage und kein Zufallstreffer."""
    assert not unmentioned_parameters("level: int", {"filtration_level"})
    assert unmentioned_parameters("level: int", {"coefficient"})


def test_each_version_pattern_reads_its_own_file_and_not_another() -> None:
    """Die drei Ausdruecke duerfen nicht dieselbe Zeile finden.

    Faende ``README_VERSION`` nichts und lieferte der Vergleich trotzdem ein
    Ergebnis, waere die Pruefung darueber leer.
    """
    assert DECLARED_VERSION.findall('version = "9.9.9"\nother = "1"') == ["9.9.9"]
    assert not DECLARED_VERSION.findall('python_version = "3.10"')
    assert README_VERSION.findall("Current version: **9.9.9**") == ["9.9.9"]
    assert NEWEST_RELEASE.findall("## 9.9.9\n\n## 9.9.8") == ["9.9.9", "9.9.8"]


def test_a_changelog_with_one_release_twice_is_caught(tmp_path: Path) -> None:
    """Die Gegenkontrolle zu der Pruefung, die den Fall von 0.4.0rc9 gefunden haette."""
    doubled = tmp_path / "CHANGELOG.md"
    doubled.write_text("## 9.9.9\n\nfirst\n\n## 9.9.9\n\nsecond\n", encoding="utf-8")
    single = tmp_path / "single.md"
    single.write_text("## 9.9.9\n\n## 9.9.8\n", encoding="utf-8")

    names = releases(doubled)

    assert names == ["9.9.9", "9.9.9"]
    assert len(names) != len(set(names))

    other = releases(single)

    assert other == ["9.9.9", "9.9.8"]
    assert len(other) == len(set(other))


def test_a_changelog_without_a_release_heading_fails_loudly(tmp_path: Path) -> None:
    """Sonst laufen beide Pruefungen darueber gegen eine leere Liste."""
    empty = tmp_path / "CHANGELOG.md"
    empty.write_text("# Changelog\n\nNotable changes per release.\n", encoding="utf-8")

    with pytest.raises(AssertionError, match="no release heading"):
        releases(empty)


def test_a_version_pattern_that_finds_nothing_fails_loudly(tmp_path: Path) -> None:
    """Und nicht still, denn dann liefe der Vergleich gegen eine leere Liste."""
    empty = tmp_path / "pyproject.toml"
    empty.write_text("[project]\n", encoding="utf-8")

    with pytest.raises(AssertionError):
        only_match(DECLARED_VERSION, empty)
