"""Die Treiberskripte, soweit sie ohne einen Suchlauf pruefbar sind.

``scripts/`` haelt zweierlei. Die ``reconstruct_*``-Skripte sind Gates und
laufen als ganze Programme; sie brauchen hier nichts. Die ``search_*``-Skripte
sind lange Laeufe mit gedrucktem Verlauf, und sie hatten bis 0.4.0rc9 gar keinen
Test -- ein externes Audit hat es angemerkt und dabei einen Haenger gefunden.

Geprueft wird nur, was ohne Suche entscheidbar ist: die Runden des sich
verdoppelnden Budgets. Der Rest der Skripte faehrt eine Suche und gehoert
deshalb nicht in die schnelle Sammlung.

Die Skripte sind kein Paket. Sie werden ueber ihren Pfad geladen, so wie
``scripts/_common.py`` die feste Eingabe unter ``tests/`` laedt.
"""

import importlib.util
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parent.parent


def load(name: str) -> ModuleType:
    """Return a module under ``scripts/`` by path."""
    path = ROOT / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"{name}_script", path)

    assert spec is not None and spec.loader is not None

    module = importlib.util.module_from_spec(spec)
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
