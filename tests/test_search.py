"""Kandidatenaufzaehlung: was Proposition (3.1) an einer Karte tun koennte.

Hier wird nichts verifiziert. Ein Kandidat ist ein Vorschlag, und was ihn zu
einem Beleg macht, ist ``BCWStep.build`` gefolgt von ``verify()`` -- SEA-1. Die
Tests pruefen entsprechend Mechanik und Vollstaendigkeit gegenueber dem Vorrat,
nicht Korrektheit im Sinne eines Zertifikats.

Die Kontrolle an echten Daten steht in ``test_bcw17.py`` und
``test_alpoege15.py``, wo die bekannten Schritte liegen.
"""

import pytest
import sympy as sp

from kellermap import (
    Candidate,
    PolynomialMap,
    anchors,
    enumerate_candidates,
    over_field,
)
from kellermap.bcw import BCWStep, Carried, Fresh

x, y, z = sp.symbols("x y z")
u, v = sp.symbols("u v")


@pytest.fixture
def flat() -> PolynomialMap:
    """Eine Komponente mit einem einzigen zusammengesetzten Monom."""
    return PolynomialMap((x, y), (x + x**2 * y**3, y))


@pytest.fixture
def carried() -> PolynomialMap:
    """Koordinate 1 traegt ``x**2``."""
    return PolynomialMap((x, y), (x + x**2 * y**3, y + x**2))


# --------------------------------------------------------------------------
# Der Vorrat begrenzt, und wie
# --------------------------------------------------------------------------


def test_an_empty_pool_leaves_only_the_carriers(flat: PolynomialMap) -> None:
    """Koordinate 1 ist ein Traeger, traegt aber den Wert null.

    Ein Anker ist sie damit nicht: durch null wird nicht geteilt, und ein
    Produkt mit null ist keine Teilsumme, die irgendetwas entfernt.
    """
    assert flat.carrier_indices == (1,)
    assert enumerate_candidates(flat, []) == ()


def test_a_pool_value_anchors_a_candidate(flat: PolynomialMap) -> None:
    found = enumerate_candidates(flat, [x * y])

    assert len(found) == 1
    assert found[0].index == 0
    assert found[0].values(flat) == (x * y, x * y**2)


def test_a_value_the_ring_cannot_hold_is_dropped(flat: PolynomialMap) -> None:
    """So faellt die Abhaengigkeit zwischen Traegern von selbst heraus.

    ``w6 = w1 x`` wird erst umwandelbar, wenn ``w1`` als Generator existiert.
    Hier steht ``z`` fuer ein solches noch nicht eingefuehrtes ``w``.
    """
    assert anchors(flat, [x * y, y * z]) == (x * y, Carried(1))
    assert enumerate_candidates(flat, [y * z]) == ()


def test_a_carrier_is_an_anchor_without_any_pool(carried: PolynomialMap) -> None:
    found = enumerate_candidates(carried, [])

    assert [(c.index, c.left, c.right) for c in found] == [(0, Carried(1), y**3)]
    assert found[0].m == 1


def test_the_target_component_is_not_offered_as_a_carrier(
    carried: PolynomialMap,
) -> None:
    """Der Konstruktor von ``BCWStep`` lehnt einen solchen Platz ab.

    Ein Kandidat, der ihn vorschlaegt, waere nicht baubar, und ein Aufzaehler,
    der Nichtbaubares vorschlaegt, verschiebt die Pruefung nur nach hinten.
    """
    assert all(
        not (isinstance(slot, Carried) and slot.index == candidate.index)
        for candidate in enumerate_candidates(carried, [x, y, x * y])
        for slot in candidate.slots
    )


# --------------------------------------------------------------------------
# SEA-10: echte Teile des Kofaktors
# --------------------------------------------------------------------------


def test_a_proper_part_of_the_cofactor_is_offered() -> None:
    """Die Messung hinter SEA-10, an einem kleinen Fall.

    Der groesste Kofaktor ist ``y + z``; der Aufzaehler bietet auch ``y`` und
    ``z`` einzeln an, weil Schritt zwei der ``alpoege15``-Kette genau so einen
    Term liegen laesst.
    """
    source = PolynomialMap((x, y, z), (x + x * y + x * z, y, z))

    cofactors = {
        candidate.values(source)[1]
        for candidate in enumerate_candidates(source, [x])
        if candidate.index == 0
    }

    assert cofactors == {y + z, y, z}


def test_every_selection_is_checked_in_its_own_right() -> None:
    """Terme aus dem Kofaktor zu streichen ist keine sichere Operation.

    ``(x - y) * (x + y) = x**2 - y**2`` ist eine Teilsumme, ``x*y`` ist im
    Produkt ausgeloescht. Der Teil ``x`` allein liefert ``x**2 - x*y``, und
    ``-x*y`` steht nicht in der Komponente. Wer die Pruefung vom groessten
    Kofaktor erbt, bietet hier einen Kandidaten an, der nicht existiert.
    """
    source = PolynomialMap((x, y), (x + x**2 - y**2, y))

    products = {
        candidate.product(source) for candidate in enumerate_candidates(source, [x - y])
    }

    assert products == {x**2 - y**2}


def test_the_selection_limit_keeps_only_the_largest_cofactor() -> None:
    """Eine Schranke gegen einen pathologischen Fall, nicht gegen die Daten."""
    source = PolynomialMap((x, y, z), (x + x * y + x * z + x * y * z, y, z))

    unlimited = enumerate_candidates(source, [x])
    limited = enumerate_candidates(source, [x], selection_limit=2)

    assert len(unlimited) == 7
    assert len(limited) == 1
    assert limited[0].values(source)[1] == y * z + y + z


# --------------------------------------------------------------------------
# Die abgeleitete Stufe
# --------------------------------------------------------------------------


def test_the_level_follows_from_the_orders(flat: PolynomialMap) -> None:
    """``H`` verschiebt die frischen Koordinaten um die Faktoren."""
    candidate = enumerate_candidates(flat, [x * y])[0]

    assert candidate.filtration_level(flat) == 1


def test_a_factor_of_order_one_drops_the_level() -> None:
    """Ein Faktor der Ordnung eins druckt ``H`` auf ``EA^0``."""
    source = PolynomialMap((x, y), (x + x**2 * y + x**2 * y**2, y))

    levels = {
        str(c.values(source)[1]): c.filtration_level(source)
        for c in enumerate_candidates(source, [x * y])
    }

    assert levels == {"x*y + x": 0, "x": 0, "x*y": 1}


def test_without_a_fresh_slot_the_level_is_one() -> None:
    """``H`` ist dann die Identitaet und liegt in jedem ``EA^d``."""
    source = PolynomialMap((x, y, z), (x + y**2 * z**2, y + y**2, z + z**2))

    candidate = Candidate(0, Carried(1), Carried(2))

    assert candidate.m == 0
    assert candidate.filtration_level(source) == 1


# --------------------------------------------------------------------------
# Namen kommen von aussen
# --------------------------------------------------------------------------


def test_factors_take_the_names_in_slot_order(flat: PolynomialMap) -> None:
    candidate = enumerate_candidates(flat, [x * y])[0]

    assert candidate.factors((u, v)) == (Fresh(x * y, u), Fresh(x * y**2, v))


def test_a_carried_slot_consumes_no_name(carried: PolynomialMap) -> None:
    candidate = enumerate_candidates(carried, [])[0]

    assert candidate.factors((u,)) == (Carried(1), Fresh(y**3, u))


def test_too_few_names_are_refused(flat: PolynomialMap) -> None:
    """Lieber ablehnen als einen Namen erfinden, den niemand vergeben hat."""
    candidate = enumerate_candidates(flat, [x * y])[0]

    with pytest.raises(ValueError, match="fewer names were supplied"):
        candidate.factors((u,))


# --------------------------------------------------------------------------
# SEA-2 und die Bruecke zum Zertifikat
# --------------------------------------------------------------------------


def test_the_enumeration_is_a_pure_function(carried: PolynomialMap) -> None:
    first = enumerate_candidates(carried, [x, y, x * y])
    second = enumerate_candidates(carried, [x, y, x * y])

    assert first == second


def test_swapping_the_slots_is_not_offered_twice(flat: PolynomialMap) -> None:
    """Vertauschte Plaetze geben denselben Schritt bis auf die Benennung."""
    products = [
        candidate.product(flat) for candidate in enumerate_candidates(flat, [x * y])
    ]

    assert products == [x**2 * y**3]


def test_a_candidate_builds_and_verifies(flat: PolynomialMap) -> None:
    """Der Uebergang, den SEA-1 meint: Vorschlag, dann Zertifikat."""
    source = over_field(flat)
    candidate = enumerate_candidates(source, [x * y])[0]

    step = BCWStep.build(
        source,
        candidate.index,
        *candidate.factors((u, v)),
        candidate.filtration_level(source),
    )

    assert step.verify() is None
    assert step.target.degree() < source.degree()


def test_a_constant_is_no_anchor_and_no_cofactor() -> None:
    """``H`` laege sonst ausserhalb von ``EA^0`` und BCW-6 lehnte ab.

    Die Ablehnung vom Aufzaehler zum Konstruktor zu verschieben macht sie
    nicht sicherer, nur spaeter.
    """
    source = PolynomialMap((x, y), (x + x * y + x, y))

    assert anchors(source, [sp.Integer(2)]) == (Carried(1),)
    assert all(
        candidate.values(source)[1] != 1
        for candidate in enumerate_candidates(source, [x])
    )


def test_a_carried_cofactor_moves_to_the_first_slot() -> None:
    """Traeger zuerst -- die Reihenfolge, in der die Referenzketten stehen."""
    source = PolynomialMap((x, y), (x + x**3 * y, y + x**2))

    found = enumerate_candidates(source, [x * y])

    assert [(c.index, c.left, c.right) for c in found] == [(0, Carried(1), x * y)]
