"""Die Treiberskripte, soweit sie ohne einen Suchlauf pruefbar sind.

``scripts/`` haelt zweierlei. Die ``reconstruct_*``-Skripte sind Gates und
laufen als ganze Programme; sie brauchen hier nichts. Die ``search_*``-Skripte
sind lange Laeufe mit gedrucktem Verlauf, und sie hatten bis 0.4.0rc9 gar keinen
Test -- ein externes Audit hat es angemerkt und dabei einen Haenger gefunden.

Geprueft wird, was ohne einen vollen Lauf entscheidbar ist: die Runden des
sich verdoppelnden Budgets, und dass die Mutationsprobe das Repository nicht
anfasst. Der Rest der Skripte faehrt eine Suche oder zwoelf Testlaeufe und
gehoert deshalb nicht in die schnelle Sammlung.

Die Skripte sind kein Paket. Sie werden ueber ihren Pfad geladen, so wie
``scripts/_common.py`` die feste Eingabe unter ``tests/`` laedt.
"""

import hashlib
import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parent.parent


def load(name: str) -> ModuleType:
    """Return a module under ``scripts/`` by path.

    Der Eintrag in ``sys.modules`` steht vor ``exec_module`` und nicht danach.
    ``dataclasses`` schlaegt beim Aufbau einer Klasse ``sys.modules[__module__]``
    nach, um die Namen der aufgeschobenen Annotationen aufzuloesen, und findet
    ohne den Eintrag ``None``. ``mutation_probe`` hat eine solche Klasse, die
    Suchtreiber haben keine -- der Fehler kam also erst mit der zweiten
    geladenen Datei.
    """
    path = ROOT / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"{name}_script", path)

    assert spec is not None and spec.loader is not None

    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    return module


@pytest.fixture(scope="module")
def driver() -> ModuleType:
    return load("search_alpoege19")


def test_the_budget_doubles_and_stops_at_the_ceiling(driver: ModuleType) -> None:
    """Die Runde, die die Decke ueberschreitet, wird nicht mehr gefahren."""
    assert list(driver.rounds(1, 8)) == [1, 2, 4, 8]
    assert list(driver.rounds(3, 10)) == [3, 6]
    assert list(driver.rounds(5, 5)) == [5]


def test_a_first_budget_of_zero_is_refused(driver: ModuleType) -> None:
    """Der Haenger, und warum die Pruefung hier steht und nicht in der Suche.

    Null verdoppelt sich zu null, also lief ``while budget <= ceiling`` ohne
    Ende und ohne eine Zeile zu drucken. Beide Treiber hatten die Schleife
    ausgeschrieben und beide hingen; ein externes Audit musste einen Lauf nach
    einer Sekunde abbrechen.

    Fuer ``search`` und ``peel`` ist null ein zulaessiges Budget -- es
    untersucht nichts und meldet das --, also darf die Pruefung nicht dorthin.
    """
    with pytest.raises(ValueError, match="at least one"):
        list(driver.rounds(0, 100))

    with pytest.raises(ValueError, match="at least one"):
        list(driver.rounds(-1, 100))


def test_a_ceiling_below_the_first_budget_is_refused(driver: ModuleType) -> None:
    """Sonst meldet der Treiber keine Kette unter einer nie versuchten Decke."""
    with pytest.raises(ValueError, match="must not lie below"):
        list(driver.rounds(100, 10))


def test_the_check_happens_before_the_first_round(driver: ModuleType) -> None:
    """Ein Erzeuger prueft sonst erst, wenn jemand ihn abfragt.

    Hier ist das gutartig, weil beide Aufrufer sofort darueber laufen. Der Test
    haelt fest, dass es so bleibt: der Fehler kommt beim ersten ``next`` und
    nicht nach einem gefahrenen Suchlauf.
    """
    rounds = driver.rounds(0, 100)

    with pytest.raises(ValueError, match="at least one"):
        next(rounds)


# --------------------------------------------------------------------------
# Die Mutationsprobe
#
# Sie hat bis 0.4.0rc13 das echte ``src/`` veraendert und per ``rmtree`` und
# ``copytree`` zurueckgelegt. Ein externes Audit fand nach einem als
# erfolgreich gemeldeten Lauf drei Mutationen im Baum stehen. Die Tests hier
# pruefen die Zusage, die daraus geworden ist: das Repository wird nicht
# beschrieben.
# --------------------------------------------------------------------------


@pytest.fixture(scope="module")
def probe() -> ModuleType:
    return load("mutation_probe")


def source_hashes() -> dict[str, str]:
    """Return a hash per Python file of the repository, path and content."""
    return {
        str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(ROOT.rglob("*.py"))
        if ".venv" not in path.parts and "__pycache__" not in path.parts
    }


def test_a_whole_sweep_leaves_the_repository_untouched(probe: ModuleType) -> None:
    """Die Regression zum Befund.

    Ein ganzer Durchlauf ueber alle zwoelf Proben, mit einem Platzhalter
    anstelle der Testsammlung: der Umbau, den er prueft, betrifft das Kopieren
    und Zuruecklegen und nicht das Ausfuehren. Vorher und nachher derselbe
    Hash ueber jede Python-Datei des Repositorys.

    Der Platzhalter meldet ``CAUGHT``, damit der Durchlauf keine Fehlmeldung
    zaehlt; was er meldet, ist fuer diesen Test ohne Belang.
    """
    before = source_hashes()

    missed = probe.sweep(probe.PROBES, run=lambda root: (True, "stub"))

    assert missed == 0
    assert source_hashes() == before


def test_every_fragment_still_matches_the_code_it_aims_at(probe: ModuleType) -> None:
    """Eine Probe, deren Fragment verschwunden ist, prueft nichts mehr.

    ``apply`` bricht in dem Fall ab, und weil der Durchlauf oben jede der
    zwoelf Proben anwendet, ist er zugleich die Frischepruefung des ganzen
    Satzes. Dieser Test sagt es noch einmal fuer sich, damit ein Fehlschlag
    lesbar ist.
    """
    for entry in probe.PROBES:
        text = (ROOT / entry.path).read_text(encoding="utf-8")

        assert entry.old in text, f"{entry.obligation}: {entry.what}"


def test_a_fragment_that_is_gone_stops_the_run(probe: ModuleType, tmp_path) -> None:  # type: ignore[no-untyped-def]
    """Und meldet, welche Probe nachzuziehen ist."""
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "thing.py").write_text("kept = 1\n", encoding="utf-8")
    gone = probe.Probe("COL-1", "a promise", "src/thing.py", "absent", "broken")

    with pytest.raises(SystemExit, match="not in src/thing.py any more"):
        probe.apply(gone, tmp_path)


def test_a_fragment_is_written_back_exactly(probe: ModuleType, tmp_path) -> None:  # type: ignore[no-untyped-def]
    """Zurueckgelegt wird die eine Datei, und kein Verzeichnis geloescht."""
    (tmp_path / "src").mkdir()
    path = tmp_path / "src" / "thing.py"
    path.write_text("kept = 1\nchecked = True\n", encoding="utf-8")
    entry = probe.Probe("COL-1", "a promise", "src/thing.py", "checked = True", "pass")

    original = probe.apply(entry, tmp_path)

    assert path.read_text(encoding="utf-8") == "kept = 1\npass\n"

    probe.restore(entry, tmp_path, original)

    assert path.read_text(encoding="utf-8") == "kept = 1\nchecked = True\n"


def test_the_working_copy_carries_what_the_suite_reads(
    probe: ModuleType,
    tmp_path,  # type: ignore[no-untyped-def]
) -> None:
    """Die Sammlung liest mehr als ``src/``.

    ``test_documentation.py`` liest ``docs/`` und ``README.md``,
    ``test_readme.py`` fuehrt die Bloecke des README aus, und die feste
    Eingabe liegt unter ``tests/``. Fehlt eines davon in der Kopie, meldet
    jede Probe ``CAUGHT`` aus dem falschen Grund.
    """
    copy = probe.working_copy(tmp_path)

    for needed in ("src", "tests", "docs", "scripts", "README.md", "pyproject.toml"):
        assert (copy / needed).exists(), needed

    assert not (copy / ".venv").exists()
    assert copy.resolve() != ROOT.resolve()


# --------------------------------------------------------------------------
# Der Codefingerabdruck
#
# Er ist die Kontrolle der Arbeitspakete 1 und 2 von 0.5: eine Uebersetzung
# darf keine Anweisung beruehren. Ein Werkzeug, das eine Zusage nachweist,
# braucht selbst einen Nachweis, dass es anschlaegt.
# --------------------------------------------------------------------------


@pytest.fixture(scope="module")
def fingerprints() -> ModuleType:
    return load("code_fingerprint")


def written(directory: Path, body: str) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "sample.py"
    path.write_text(body, encoding="utf-8")

    return path


def test_a_changed_docstring_leaves_the_fingerprint_alone(
    fingerprints: ModuleType,
    tmp_path: Path,
) -> None:
    """Der Fall, den das Paket erzeugt."""
    first = written(
        tmp_path / "a",
        '"""Ein deutscher Docstring."""\n\n\ndef f(x: int) -> int:\n'
        '    """Gibt x zurueck."""\n    return x\n',
    )
    second = written(
        tmp_path / "b",
        '"""An English docstring."""\n\n\ndef f(x: int) -> int:\n'
        '    """Return x."""\n    return x\n',
    )

    assert fingerprints.fingerprint(first) == fingerprints.fingerprint(second)


def test_a_changed_comment_leaves_the_fingerprint_alone(
    fingerprints: ModuleType,
    tmp_path: Path,
) -> None:
    """Kommentare stehen nicht im Syntaxbaum und fallen von selbst heraus."""
    first = written(tmp_path / "a", "# Ein Kommentar.\nvalue = 1\n")
    second = written(tmp_path / "b", "# A comment.\nvalue = 1\n")

    assert fingerprints.fingerprint(first) == fingerprints.fingerprint(second)


def test_a_changed_instruction_changes_the_fingerprint(
    fingerprints: ModuleType,
    tmp_path: Path,
) -> None:
    """Die Gegenkontrolle. Ohne sie waere ein Werkzeug denkbar, das immer
    denselben Wert liefert und jede Uebersetzung freispricht.
    """
    first = written(tmp_path / "a", "def f(x: int) -> bool:\n    return x > 0\n")
    second = written(tmp_path / "b", "def f(x: int) -> bool:\n    return x >= 0\n")

    assert fingerprints.fingerprint(first) != fingerprints.fingerprint(second)


def test_a_string_that_is_not_a_docstring_is_kept(
    fingerprints: ModuleType,
    tmp_path: Path,
) -> None:
    """Nur die erste Anweisung eines Rumpfes faellt weg.

    Eine Fehlermeldung ist ein Wert, den der Code benutzt. Sie zu entfernen
    hiesse, eine geaenderte Meldung zu verschweigen statt sie zu ignorieren.
    """
    first = written(tmp_path / "a", 'def f() -> None:\n    raise ValueError("one")\n')
    second = written(tmp_path / "b", 'def f() -> None:\n    raise ValueError("two")\n')

    assert fingerprints.fingerprint(first) != fingerprints.fingerprint(second)


def test_a_body_of_only_a_docstring_stays_valid(
    fingerprints: ModuleType,
    tmp_path: Path,
) -> None:
    """Ein leerer Rumpf waere kein gueltiges Python mehr."""
    only = written(tmp_path / "a", 'def f() -> None:\n    """Nur ein Docstring."""\n')
    passed = written(tmp_path / "b", "def f() -> None:\n    pass\n")

    assert fingerprints.fingerprint(only) == fingerprints.fingerprint(passed)


def test_the_report_names_what_changed(fingerprints: ModuleType) -> None:
    """Ein Bericht, der nur die Zahl nennt, hilft beim Suchen nicht."""
    before = {"a.py": "1", "b.py": "2", "c.py": "3"}
    after = {"a.py": "1", "b.py": "9", "d.py": "4"}

    assert fingerprints.differences(before, after) == [
        "changed  b.py",
        "removed  c.py",
        "added    d.py",
    ]

    assert not fingerprints.differences(before, before)


def test_the_repository_is_covered(fingerprints: ModuleType) -> None:
    """``src``, ``tests`` und ``scripts``, und nichts aus ``__pycache__``."""
    covered = {str(path.relative_to(ROOT)) for path in fingerprints.sources()}

    assert "src/kellermap/peeling.py" in covered
    assert "tests/test_scripts.py" in covered
    assert "scripts/code_fingerprint.py" in covered
    assert not [name for name in covered if "__pycache__" in name]


# --------------------------------------------------------------------------
# The vocabulary instrument
#
# It reports prose words that do not occur in the English part of the
# repository. It is not a gate: over the translated modules it reports about a
# hundred words, all of them English. What it is good for is a list a reader
# scans once per module, and it is what found twenty-eight German lines that
# the word list of tests/test_language.py missed.
# --------------------------------------------------------------------------


@pytest.fixture(scope="module")
def foreign() -> ModuleType:
    return load("foreign_words")


def test_the_default_file_set_is_the_remainder(foreign: ModuleType) -> None:
    """The path that was never tried, and therefore never ran.

    Called without arguments the script examines the modules that
    ``tests/test_language.py`` still lists. That branch held a nested
    ``__import__`` call which raised ``AttributeError`` on every invocation.
    Nothing caught it, because every run during development passed a file name.
    """
    listed = foreign.remainder()

    assert listed, "the remainder is empty; this test outlived its purpose"
    assert all(path.parent.name == "tests" for path in listed)
    assert all(path.exists() for path in listed)


def test_the_script_runs_without_arguments(
    foreign: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """``main`` itself, and not only the function it calls.

    The defect was in ``main``, so a test of ``remainder`` alone would have
    passed while the script kept raising. It is driven here the way the
    maintainer drove it.
    """
    monkeypatch.setattr(foreign.sys, "argv", ["foreign_words.py"])

    assert foreign.main() == 0

    printed = capsys.readouterr().out
    listed = {path.name for path in foreign.remainder()}

    assert listed, "the remainder is empty; this test outlived its purpose"
    assert all(f"{name}:" in printed for name in listed)


def test_the_module_under_review_is_not_its_own_corpus(foreign: ModuleType) -> None:
    """A path comparison that mixed relative and absolute paths.

    Every module under review entered the English vocabulary it was measured
    against, so the report came back empty for every input. The paths are
    resolved before they are compared.
    """
    relative = Path("tests/test_peeling.py")
    absolute = ROOT / "tests" / "test_peeling.py"

    assert foreign.english({relative}) == foreign.english({absolute})

    # And the exemption really works: taking the module out of the corpus has
    # to remove words, otherwise the line above compares two equal defects.
    assert foreign.english({absolute}) < foreign.english(set())

    # The report on an examined module is therefore not empty.
    known = foreign.english({relative})
    words = {w.lower() for w in foreign.WORD.findall(foreign.prose(absolute))}

    assert words - known


def test_prose_excludes_code_and_quoted_code(foreign: ModuleType) -> None:
    """Identifiers are not words, whichever language they look like."""
    text = foreign.prose(ROOT / "src" / "kellermap" / "guards.py")

    assert "bound" in text
    assert "raise TypeError" not in text
    assert not foreign.QUOTED_CODE.search(text)
