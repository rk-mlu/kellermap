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
