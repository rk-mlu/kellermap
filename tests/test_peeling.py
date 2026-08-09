"""Abtragen: eine Kette vom Ziel her, REV-1 bis REV-7.

Ein Abtrag ist kein Zertifikat. Was hier geprueft wird, ist die Mechanik --
Entfernbarkeit, das Rueckrechnen, das Vorzeichen -- und die Bruecke zurueck:
dass die gefundene Struktur vorwaerts neu gebaut, geprueft und mit dem Ziel
verglichen wird, bevor sie eine ``Reduction`` heisst.
"""

import pytest
import sympy as sp

from kellermap import PolynomialMap, examples, over_field
from kellermap.bcw import BCWStep, Carried, Fresh
from kellermap.peeling import (
    PeelOutcome,
    Undo,
    factor,
    moves,
    peel,
    removable,
    undo,
)
from kellermap.search import conjugate

x, y, z = sp.symbols("x y z")
u, v, t = sp.symbols("u v t")


@pytest.fixture
def one_step() -> tuple[PolynomialMap, PolynomialMap]:
    """Quelle und Ziel einer Kette aus einem Schritt mit zwei frischen Plaetzen."""
    source = over_field(PolynomialMap((x, y), (x + x**2 * y**3, y)))
    target = BCWStep.build(source, 0, Fresh(x * y, u), Fresh(x * y**2, v), 1).target

    return source, target


@pytest.fixture
def two_steps() -> tuple[PolynomialMap, PolynomialMap]:
    """Zwei Schritte, der zweite mit einem ``Carried``-Platz."""
    source = over_field(
        PolynomialMap((x, y), (x + x**3 * y**3 + x**2 * y**3, y)),
    )
    first = BCWStep.build(source, 0, Fresh(x * y, u), Fresh(x * y**2, v), 1)
    second = BCWStep.build(first.target, 0, Carried(2), Fresh(x**2 * y**2, t), 1)

    return source, second.target


# --------------------------------------------------------------------------
# REV-2: was zuletzt eingefuehrt worden sein kann
# --------------------------------------------------------------------------


def test_a_fresh_coordinate_occurs_in_exactly_two_components(
    one_step: tuple[PolynomialMap, PolynomialMap],
) -> None:
    """In der eigenen und im Rest der Zielkomponente."""
    _, target = one_step

    assert removable(target) == {u: x, v: x}


def test_the_criterion_filters_and_the_undoing_decides(
    two_steps: tuple[PolynomialMap, PolynomialMap],
) -> None:
    """REV-2 ist ein billiger Filter, REV-3 die eigentliche Pruefung.

    Der zweite Schritt zielt hier auf dieselbe Komponente wie der erste, also
    steht ``u`` weiterhin in genau zwei Komponenten und wird angeboten.
    Abgetragen wird es trotzdem nicht: der Schritt, der ``u`` und ``v``
    angelegt hat, war nicht der letzte, und das faellt beim Rueckrechnen auf,
    weil ``u`` danach noch dasteht.
    """
    _, target = two_steps

    assert u in removable(target)
    assert undo(target, Undo(x, (u, v), (u, v), sp.Integer(1))) is None


def test_the_criterion_is_what_makes_the_direction_cheap() -> None:
    """Sechs von sechzehn bei der veroeffentlichten Abbildung.

    Vorwaerts bietet der Aufzaehler an einer Karte dieser Groesse ueber hundert
    Kandidaten an; hier sind es die Koordinaten, die ueberhaupt zuletzt
    eingefuehrt worden sein koennen.
    """
    fifteen = examples.alpoege15()

    assert 0 < len(removable(fifteen)) < fifteen.dimension - 3


# --------------------------------------------------------------------------
# REV-3: das Rueckrechnen
# --------------------------------------------------------------------------


def test_undoing_needs_no_inverse(
    one_step: tuple[PolynomialMap, PolynomialMap],
) -> None:
    source, target = one_step

    reached = undo(target, Undo(x, (u, v), (u, v), sp.Integer(1)))

    assert reached is not None
    assert reached == source


def test_a_coordinate_that_survives_the_undoing_is_refused(
    two_steps: tuple[PolynomialMap, PolynomialMap],
) -> None:
    """Die zweite Haelfte von REV-3, und die eigentliche Pruefung.

    ``v`` laesst sich nicht abtragen, solange ``u`` noch da ist: der Schritt,
    der beide angelegt hat, ist nicht der letzte gewesen.
    """
    _, target = two_steps

    assert undo(target, Undo(x, (u, v), (u, v), sp.Integer(1))) is None


def test_a_slot_the_map_does_not_have_is_refused(
    one_step: tuple[PolynomialMap, PolynomialMap],
) -> None:
    _, target = one_step

    assert undo(target, Undo(x, (u, sp.Symbol("nowhere")), (u,), sp.Integer(1))) is None
    assert undo(target, Undo(sp.Symbol("nowhere"), (u, v), (u,), sp.Integer(1))) is None


def test_the_wrong_factor_does_not_undo(
    one_step: tuple[PolynomialMap, PolynomialMap],
) -> None:
    """REV-4: der Faktor entscheidet sich am Verschwinden der Koordinate."""
    _, target = one_step

    assert undo(target, Undo(x, (u, v), (u, v), sp.Integer(-1))) is None


# --------------------------------------------------------------------------
# Die Zuege
# --------------------------------------------------------------------------


def test_steps_removing_two_coordinates_come_first(
    one_step: tuple[PolynomialMap, PolynomialMap],
) -> None:
    """Sie kommen fuer dieselbe Tiefe doppelt so weit."""
    _, target = one_step

    offered = list(moves(target, spare=0))

    assert len(offered[0].dropped) == 2


def test_without_a_spare_no_step_that_removes_nothing_is_offered() -> None:
    source = over_field(PolynomialMap((x, y), (x + x**5, y + x**2)))
    target = BCWStep.build(source, 0, Carried(1), Fresh(x**3, u), 1).target

    assert all(step.dropped for step in moves(target, spare=0))
    assert any(not step.dropped for step in moves(target, spare=1))


# --------------------------------------------------------------------------
# Die Bruecke zurueck
# --------------------------------------------------------------------------


def test_a_peel_returns_a_chain_that_was_built_forwards(
    one_step: tuple[PolynomialMap, PolynomialMap],
) -> None:
    """REV-5: die Struktur wird neu gebaut und geprueft, nicht uebernommen."""
    source, target = one_step

    outcome = peel(source, target)

    assert isinstance(outcome, PeelOutcome)
    assert outcome.reduction is not None
    assert outcome.reduction.verify() is None
    assert outcome.reduction.source == source
    assert outcome.reduction.target == target
    assert outcome.signs == (1,) * 4


def test_a_carried_slot_is_rebuilt_as_a_carried_slot(
    two_steps: tuple[PolynomialMap, PolynomialMap],
) -> None:
    source, target = two_steps

    outcome = peel(source, target)

    assert outcome.reduction is not None
    assert len(outcome.reduction.steps) == 2
    assert outcome.reduction.steps[1].m == 1


def test_the_diagonal_is_reported_and_not_absorbed(
    one_step: tuple[PolynomialMap, PolynomialMap],
) -> None:
    """SEA-5 unveraendert: das Ziel wird bis auf ein ausgewiesenes ``D`` erreicht."""
    source, target = one_step
    flipped = conjugate(target, (1, 1, 1, -1))

    outcome = peel(source, flipped)

    assert outcome.reduction is not None
    assert outcome.signs is not None
    reached = outcome.reduction.target.reordered(flipped.variables)
    assert conjugate(reached, outcome.signs) == flipped


def test_a_target_that_is_not_reachable_is_reported_as_such(
    one_step: tuple[PolynomialMap, PolynomialMap],
) -> None:
    """REV-7: kein Beweis der Nichtexistenz, sondern ein erschoepfter Raum."""
    source, target = one_step
    other = over_field(PolynomialMap((x, y), (x + y**7, y)))

    outcome = peel(other, target)

    assert outcome.reduction is None
    assert outcome.exhausted


def test_a_budget_that_runs_out_says_less(
    one_step: tuple[PolynomialMap, PolynomialMap],
) -> None:
    """REV-6, wie SEA-11."""
    source, target = one_step

    outcome = peel(source, target, budget=1)

    assert outcome.reduction is None
    assert not outcome.exhausted
    assert outcome.examined == 1
    assert outcome.deepest == 0


# --------------------------------------------------------------------------
# An echten Daten
# --------------------------------------------------------------------------


@pytest.mark.slow
def test_peeling_recovers_a_chain_to_the_fifteen_dimensional_map() -> None:
    """Die Abnahmebedingung, an der Abbildung, deren Antwort bekannt ist.

    Nichts wird vorgegeben ausser Quelle und Ziel: kein Vorrat, keine Namen,
    keine Vorzeichenkonvention. Das ist REV-1, und es ist der Unterschied zur
    Vorwaertssuche, die denselben Fund nur mit einem Vorratswert schafft, den
    die Zielabbildung nicht mehr traegt.
    """
    from kellermap import LinearStep

    target = examples.alpoege15()
    source = LinearStep.normalize(over_field(examples.alpoege())).target

    outcome = peel(source, target, budget=200)

    assert outcome.reduction is not None
    assert outcome.reduction.verify() is None
    assert len(outcome.reduction.steps) == 7
    assert outcome.reduction.dimensions() == (3, 5, 7, 9, 11, 12, 14, 15)
    assert outcome.signs == (1,) * 15
    reached = outcome.reduction.target.reordered(target.variables)
    assert conjugate(reached, outcome.signs) == target


# --------------------------------------------------------------------------
# Zuege, die verworfen werden
# --------------------------------------------------------------------------


def test_two_removable_coordinates_with_different_targets_are_not_paired() -> None:
    """Ein Schritt hat genau eine Zielkomponente.

    Zwei Koordinaten, die in verschiedenen Komponenten stehen, koennen nicht
    von demselben Schritt stammen.
    """
    p, q = sp.symbols("p q")
    source = over_field(PolynomialMap((x, y), (x + x**2 * y**3, y + x**3 * y**2)))
    first = BCWStep.build(source, 0, Fresh(x * y, u), Fresh(x * y**2, v), 1).target
    second = BCWStep.build(first, 1, Fresh(x * y**2, p), Fresh(x * y, q), 1).target

    assert set(removable(second).values()) == {x, y}
    assert all(
        len(step.dropped) < 2
        or removable(second)[step.dropped[0]] == (removable(second)[step.dropped[1]])
        for step in moves(second, spare=0)
    )


def test_a_step_that_removes_nothing_does_not_use_its_own_target() -> None:
    """Der Konstruktor von ``BCWStep`` lehnt einen solchen Platz ab.

    Ein Aufzaehler, der Nichtbaubares anbietet, verschiebt die Ablehnung nur.
    """
    source = over_field(PolynomialMap((x, y, z), (x + x**5, y + x**2, z + x**3)))
    target = BCWStep.build(source, 0, Carried(1), Carried(2), 1).target

    assert all(step.target not in step.slots for step in moves(target, spare=1))


def test_a_step_that_removes_nothing_must_shorten_its_target() -> None:
    """Sonst waere jedes Produkt zweier Traeger ein Zug.

    Das Rueckrechnen macht die Komponente laenger statt kuerzer, wenn dort
    nichts entfernt wurde.
    """
    source = over_field(PolynomialMap((x, y, z), (x + x**5, y + x**2, z + x**3)))
    target = BCWStep.build(source, 0, Carried(1), Carried(2), 1).target

    offered = [step for step in moves(target, spare=1) if not step.dropped]

    assert offered
    assert all(step.factor == 1 for step in offered)


def test_contradictory_signs_leave_no_diagonal() -> None:
    """REV-4 und SEA-5 zusammen: ``D`` ist geloest, nicht gewaehlt.

    Ein Schritt, dessen drei Koordinaten alle bis zum Ende ueberleben, bindet
    nur festgelegte Vorzeichen. Wird er mit ``-`` abgetragen, verlangt er
    ``-1`` von einem Produkt, das ``+1`` sein muss, und es gibt kein ``D``.
    Die Kette wird verworfen statt zurechtgebogen.
    """
    source = over_field(PolynomialMap((x, y, z), (x + x**5, y + x**2, z + x**3)))
    target = BCWStep.build(source, 0, Carried(1), Carried(2), 1).target
    flipped = conjugate(target, (1, -1, 1))

    outcome = peel(source, flipped, spare=1)

    assert outcome.reduction is None
    assert outcome.exhausted


def test_a_carrier_may_also_be_a_target_and_is_then_not_its_own_slot() -> None:
    """Eine Traegerkomponente mit mehr als zwei Termen ist beides zugleich.

    Sie kommt als Ziel eines Schritts in Frage und als Platz eines anderen;
    beides zugleich waere ein Platz auf der Komponente, auf die der Schritt
    zielt, und den lehnt der Konstruktor von ``BCWStep`` ab.
    """
    source = over_field(
        PolynomialMap((x, y, z), (x + x**5, y + x**2 + x**3, z + x**3)),
    )
    target = BCWStep.build(source, 0, Carried(1), Carried(2), 1).target

    assert 1 in target.carrier_indices
    assert len(sp.Add.make_args(target.components[1])) > 2
    assert all(step.target not in step.slots for step in moves(target, spare=1))


def test_two_coordinates_that_disagree_on_the_factor_are_not_one_step() -> None:
    """Ein Schritt hat einen Faktor, nicht zwei.

    Hier legen zwei getrennte Schritte je eine Koordinate auf derselben
    Zielkomponente an. Beide sind danach entfernbar und werden als Paar
    angeboten -- aber sie verlangen verschiedene Konstanten, also stammen sie
    nicht von einem gemeinsamen Schritt.
    """
    source = over_field(
        PolynomialMap((x, y), (x + x**2 * y**3 + x**3 * y**5, y + x**2)),
    )
    first = BCWStep.build(source, 0, Carried(1), Fresh(y**3, u), 1).target
    target = BCWStep.build(first, 0, Carried(1), Fresh(x * y**5, v), 1).target

    assert set(removable(target)) == {u, v}
    assert factor(target, x, (u, v), (u, v)) is None
    assert factor(target, x, (y, u), (u,)) == 1
