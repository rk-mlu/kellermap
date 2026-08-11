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


def test_steps_removing_two_coordinates_go_where_the_allowance_is(
    one_step: tuple[PolynomialMap, PolynomialMap],
) -> None:
    """Zuerst, wenn die Erlaubnis reichlich ist; zuletzt, wenn sie knapp ist.

    Reichlich: ein Zug, der zwei Koordinaten entfernt, kommt fuer dieselbe
    Tiefe doppelt so weit. Knapp: bei ``pairs = 1`` ist der eine solche Schritt
    nach REV-8 der letzte des Abtrags, und ihn zuerst zu versuchen gibt die
    einzige Erlaubnis frueh aus.

    Gemessen an ``alpoege15``, wo die eine Reihenfolge in acht Karten findet und
    die andere in zweitausend nicht.
    """
    _, target = one_step

    plentiful = list(moves(target, spare=0, pairs=16))
    scarce = list(moves(target, spare=0, pairs=1))

    assert len(plentiful[0].dropped) == 2
    assert len(scarce[-1].dropped) == 2
    assert not any(
        len(step.dropped) == 2 for step in moves(target, spare=0, last=False)
    )


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


def test_a_carried_slot_is_rebuilt_as_a_carried_slot(
    two_steps: tuple[PolynomialMap, PolynomialMap],
) -> None:
    source, target = two_steps

    outcome = peel(source, target)

    assert outcome.reduction is not None
    assert len(outcome.reduction.steps) == 2
    assert outcome.reduction.steps[1].m == 1


def test_a_conjugated_target_is_reached_exactly(
    one_step: tuple[PolynomialMap, PolynomialMap],
) -> None:
    """SEA-5 ist wieder Gleichheit, und das reicht seit BCW-11.

    Die Schrittfamilie ist unter Diagonalkonjugation abgeschlossen: was frueher
    nur bis auf ein ``D`` erreicht wurde, ist selbst eine Kette. Der Abtrag
    findet sie, weil er den Koeffizienten loest statt ihn zu suchen.
    """
    source, target = one_step
    flipped = conjugate(target, (1, 1, 1, -1))

    outcome = peel(source, flipped)

    assert outcome.reduction is not None
    assert outcome.reduction.target.reordered(flipped.variables) == flipped


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
    assert outcome.reduction.target.reordered(target.variables) == target

    # Die Dimensionsfolge wird nicht festgeschrieben. Der Abtrag findet *eine*
    # Kette, nicht *die* Kette, und eine Aenderung an der Zugreihenfolge darf
    # eine andere finden, ohne dass ein Test dagegensteht.
    dimensions = outcome.reduction.dimensions()

    assert dimensions[0] == 3
    assert dimensions[-1] == 15
    assert all(
        earlier <= later
        for earlier, later in zip(dimensions, dimensions[1:], strict=False)
    )


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


def test_a_source_without_carriers_cannot_take_a_single_coordinate() -> None:
    """Eine Beschneidung aus der Quelle, nicht aus einer Regel ueber Keller.

    Der letzte Schritt einer Kette, der eine Koordinate einfuehrt, hat einen
    ``Carried``-Platz, und der liegt nicht auf der Zielkomponente -- seine
    Komponente ist also vor und nach dem Schritt dieselbe und macht ihn zum
    Traeger auch der Quelle. Eine Quelle ohne Traeger ist so nicht erreichbar,
    und ein Abtrag, der bei einer Koordinate zu viel steht, ist am Ende.

    Alpoeges Abbildung hat keine Traeger, also greift das dort ueberall.
    """
    carrying = over_field(PolynomialMap((x, y), (x + x**3 * y**3, y + x**2)))
    single = BCWStep.build(carrying, 0, Carried(1), Fresh(x * y**3, u), 1).target

    assert carrying.carrier_indices == (1,)
    assert peel(carrying, single).reduction is not None

    without = over_field(PolynomialMap((x, y), (x + x**2 * y**3, y + x * y)))
    both = BCWStep.build(without, 0, Fresh(x * y, u), Fresh(x * y**2, v), 1).target

    assert without.carrier_indices == ()
    assert peel(without, both).reduction is not None

    # Ein anderes Ziel derselben Gestalt zwingt die Suche, auch die Zuege zu
    # betrachten, die eine Koordinate allein abtragen. Sie fuehren auf eine
    # Koordinate mehr als die Quelle und werden verworfen, statt einen Schritt
    # zu suchen, den es dort nicht geben kann.
    stranger = over_field(PolynomialMap((x, y), (x + x**2 * y**5, y + x * y)))

    assert stranger.carrier_indices == ()
    assert peel(stranger, both).reduction is None


def test_the_number_of_pair_steps_is_bounded(
    one_step: tuple[PolynomialMap, PolynomialMap],
) -> None:
    """``pairs`` ist die Arithmetik von REV-8 als Regel.

    Mit ``a`` Schritten, die zwei Generatoren einfuehren, ``b`` mit einem und
    ``c`` mit keinem gilt ``2a + b = n`` und ``S = n - a + c``. Die Schrittzahl
    festzulegen legt damit ``a`` fest. Ohne einen solchen Schritt ist eine
    Kette, die einen braucht, nicht ungefunden, sondern unerreichbar.
    """
    source, target = one_step

    assert peel(source, target, pairs=1).reduction is not None

    without = peel(source, target, pairs=0)

    assert without.reduction is None
    assert without.exhausted


def test_both_slots_may_name_the_same_coordinate() -> None:
    """BCW-6 laesst das seit 0.3 zu, der Abtrag hat es nicht aufgezaehlt.

    ``G`` ist dann ``X_i - X_j**2``. ``combinations`` allein bietet nur
    verschiedene Paare an, also war eine Kette mit einem solchen Schritt nicht
    ungefunden, sondern unerreichbar. Gefunden hat den Fehler ein externes
    Audit, nicht ein Test.
    """
    source = over_field(PolynomialMap((x, y), (x + x**4, y + x**2)))
    target = BCWStep.build(source, 0, Carried(1), Carried(1), 1).target

    assert any(step.slots[0] == step.slots[1] for step in moves(target, spare=1))

    outcome = peel(source, target, spare=1)

    assert outcome.reduction is not None
    assert outcome.reduction.verify() is None
    assert outcome.reduction.target == target


def test_the_degree_never_rises_above_the_source() -> None:
    """Vorwaerts faellt der Grad nie, rueckwaerts steigt er also nie darueber.

    Beweisbar und keine Entscheidung: die neuen Terme eines Schritts haben Grad
    hoechstens ``1 + deg Q <= deg(P Q)``, solange kein Faktor konstant ist, und
    Konstanten sind ausgeschlossen. Ein Abtrag, der ueber den Grad der Quelle
    hinauslaeuft, kann sie nicht mehr erreichen.
    """
    source = over_field(PolynomialMap((x, y), (x + x**2 * y**3, y)))
    target = BCWStep.build(source, 0, Fresh(x * y, u), Fresh(x * y**2, v), 1).target
    lower = over_field(PolynomialMap((x, y), (x + y**2, y)))

    assert target.degree() < source.degree()
    assert lower.degree() < target.degree()

    outcome = peel(lower, target)

    assert outcome.reduction is None
    assert outcome.exhausted


def test_the_ring_survives_the_peel() -> None:
    """Der Koeffizientenbereich und die Monomordnung gehoeren dem Ziel.

    Bis 0.4.0rc1 wurden die Zwischenkarten aus Ausdruecken neu gebaut, und
    beides wurde dabei neu abgeleitet: ``QQ`` kam als ``ZZ`` zurueck und
    ``grlex`` als das, was die Ausdruecke nahelegten. Eine gueltige Kette
    konnte so unauffindbar erscheinen. Ein externes Audit hat es gemeldet.
    """
    parameter = sp.Symbol("T")
    source = over_field(PolynomialMap((x, y), (x + parameter * x**2 * y**3, y)))
    target = BCWStep.build(source, 0, Fresh(x * y, u), Fresh(x * y**2, v), 1).target

    outcome = peel(source, target)

    assert outcome.reduction is not None
    assert outcome.reduction.target.ring.domain == target.ring.domain
    assert outcome.reduction.target.ring.order == target.ring.order
    assert outcome.reduction.target.reordered(target.variables) == target


def test_a_parameter_of_the_domain_is_a_legal_coefficient() -> None:
    """BCW-11 laesst jede Konstante des Bereichs zu, und ``T`` ist eine.

    Ein Test auf ``free_symbols`` haette ``T`` fuer eine Koordinate gehalten
    und den Schritt verworfen. Konversion statt Inspektion, wie BCW-3 und
    TRA-2.
    """
    parameter = sp.Symbol("T")
    source = over_field(PolynomialMap((x, y), (x + parameter * x**2 * y**3, y)))
    target = BCWStep.build(
        source, 0, Fresh(x * y, u), Fresh(x * y**2, v), 1, parameter
    ).target

    outcome = peel(source, target)

    assert outcome.reduction is not None
    assert outcome.reduction.steps[0].coefficient == parameter
    assert outcome.reduction.target.reordered(target.variables) == target


def test_a_move_is_offered_once_per_constant() -> None:
    """Mehrere gemeinsame Monome geben oft dieselbe Konstante.

    Jedes gab bis 0.4.0rc2 einen eigenen Zug: an der Wurzel der
    veroeffentlichten Abbildung sechsunddreissig Kandidaten gegen sechzehn
    verschiedene, zehn davon dreifach. Ein externes Audit hat es gezaehlt.
    """
    source = over_field(PolynomialMap((x, y), (x + x**5 + x**7, y + x**2)))
    target = BCWStep.build(source, 0, Carried(1), Carried(1), 1).target

    offered = list(moves(target, spare=1))

    assert offered
    assert len(offered) == len(set(offered))


def test_a_state_is_walked_once() -> None:
    """Unabhaengige Schritte vertauschen, also fuehren viele Wege zur selben
    Karte, und der Teilbaum darunter ist jedes Mal derselbe.

    Was ausser der Karte in den Schluessel gehoert, ist das noch Verfuegbare:
    dieselbe Karte mit einem Ersatzschritt uebrig ist nicht derselbe Zustand.
    """
    p, q = sp.symbols("p q")
    source = over_field(PolynomialMap((x, y), (x + x**2 * y**3, y + x**3 * y**2)))
    first = BCWStep.build(source, 0, Fresh(x * y, u), Fresh(x * y**2, v), 1).target
    target = BCWStep.build(first, 1, Fresh(x * y**2, p), Fresh(x * y, q), 1).target

    # Die beiden Schritte liegen auf verschiedenen Komponenten und vertauschen,
    # also fuehren zwei Wege zur selben Karte. Ein Ziel, das nicht erreichbar
    # ist, laesst den Abtrag den Raum ganz ablaufen und dabei darauf stossen.
    elsewhere = over_field(PolynomialMap((x, y), (x + y**5, y + x**5)))

    exhausted = peel(elsewhere, target, budget=2000)

    assert exhausted.reduction is None
    assert exhausted.exhausted
    assert peel(source, target, budget=200).reduction is not None


# --------------------------------------------------------------------------
# Der m = 0 Zweig rechnet im Ring
# --------------------------------------------------------------------------


def test_a_constant_outside_the_domain_is_not_a_move() -> None:
    """Ueber ``ZZ`` ist ``1/2`` keine Konstante, auch wenn sie so aussieht.

    Gegenbeispiel eines externen Audits. Die beiden gemeinsamen Monome geben
    ``1`` und ``1/2``; der zweite wurde als Zug ausgegeben, und der Abtrag
    stuerzte beim Rueckrechnen ab, weil das Ergebnis nicht mehr ueber ``ZZ``
    lag. Die gueltige Kette war die ganze Zeit im Raum.
    """
    a, b, s = sp.symbols("a b s")
    source = PolynomialMap((s, a, b, x), (s + a * x + x**3, a, b + 2 * x, x))
    step = BCWStep.build(source, 0, Carried(1), Carried(2), 1, 1)

    assert source.ring.domain.is_ZZ
    assert step.verify() is None
    assert all(candidate.factor == 1 for candidate in moves(step.target, spare=1))

    outcome = peel(source, step.target, spare=1)

    assert outcome.reduction is not None
    assert outcome.reduction.steps[0].coefficient == 1


def test_a_parameter_coefficient_is_found_at_m_zero() -> None:
    """``S*a*x - T*a*x`` ist ein Monom und nicht zwei Summanden.

    Zweites Gegenbeispiel desselben Audits. Die Kuerzung wurde an
    ``sp.Add.make_args`` gemessen, also sah dieser Schritt nicht wie eine
    Kuerzung aus, und der Abtrag meldete einen erschoepften Raum nach einem
    einzigen Zustand. Im Ring gezaehlt ist es ein Term mit Koeffizient
    ``S - T``.
    """
    a, b, s = sp.symbols("a b s")
    parameters = sp.symbols("S T")
    source = PolynomialMap(
        (s, a, b, x),
        (s + (parameters[0] - parameters[1]) * a * x + x**3, a, b + x, x),
    )
    step = BCWStep.build(source, 0, Carried(1), Carried(2), 1, -parameters[1])

    assert str(source.ring.domain) == "ZZ[S,T]"
    assert step.verify() is None

    outcome = peel(source, step.target, spare=1)

    assert outcome.reduction is not None
    assert outcome.reduction.steps[0].coefficient == -parameters[1]
    assert outcome.reduction.target.reordered(step.target.variables) == step.target


def test_the_order_of_the_moves_does_not_depend_on_the_hash_seed() -> None:
    """``moves`` sagt eine feste Reihenfolge zu, und ein ``set`` hat keine.

    Die deduplizierten Konstanten wurden unmittelbar aus einer Menge heraus
    ausgegeben, also entschied ``PYTHONHASHSEED``, welcher Zug zuerst kam --
    und bei knappem Budget damit, welche Kette gefunden wird. Sie werden jetzt
    kanonisch sortiert. Dieser Test prueft die Zusage im Prozess; die
    Unabhaengigkeit vom Seed selbst ist ausserhalb messbar.
    """
    a, b, s = sp.symbols("a b s")
    first, second = sp.symbols("S T")
    source = PolynomialMap(
        (s, a, b, x),
        (
            s
            + (first + second) * a * x
            + (first - second) * a * b
            + first * x**3
            + x**5,
            a,
            b + x,
            x,
        ),
    )
    target = BCWStep.build(source, 0, Carried(1), Carried(2), 1, -second).target

    constants = [
        candidate.factor
        for candidate in moves(target, spare=1)
        if not candidate.dropped
    ]

    assert constants == sorted(constants, key=sp.default_sort_key)
    assert [str(constant) for constant in constants] == ["-S", "-S - 2*T", "-S - 2*T"]


def test_a_step_that_left_no_trace_of_its_constant_is_out_of_reach() -> None:
    """REV-10, und eine Grenze des Suchraums statt eines Fehlers.

    Der Schritt entfernt ``a*b`` genau, also bleibt in der Zielkomponente kein
    Monom, das die Konstante verriete. Jede Konstante gibt eine Abbildung; der
    Abtrag muesste raten. Gegenbeispiel eines externen Audits, hier als Grenze
    festgehalten -- der Schritt ist gueltig und wird nicht gefunden.
    """
    a, b, s = sp.symbols("a b s")
    source = PolynomialMap((s, a, b, x), (s + a * b + x**3, a, b, x))
    step = BCWStep.build(source, 0, Carried(1), Carried(2), 1, 1)

    assert step.verify() is None
    assert step.target.components == (s + x**3, a, b, x)

    outcome = peel(source, step.target, spare=1)

    assert outcome.reduction is None
    assert outcome.exhausted


def test_a_self_fresh_step_with_a_zero_factor_is_found() -> None:
    """Die Konstante steckt dann in ``u**2`` und nicht in ``u``.

    ``factor`` sah nur auf den Grad eins, also war dieser Schritt unauffindbar
    und der Kommentar nannte den Fall unerreichbar. Ein Nullfaktor ist kein
    Sonderfall: eine getragene Koordinate ohne Wert kommt in denselben Karten
    vor, und der Konstruktor laesst beides zu.
    """
    source = over_field(PolynomialMap((x, y), (x + y**3, y)))
    step = BCWStep.build(source, 0, Fresh(0, u), Fresh(0, u), 1, 3)

    assert step.verify() is None

    outcome = peel(source, step.target)

    assert outcome.reduction is not None
    assert outcome.reduction.steps[0].coefficient == 3
    assert outcome.reduction.target.reordered(step.target.variables) == step.target


def test_the_generators_keep_their_identity() -> None:
    """Der Ring wird geklont und nicht aus gedruckten Namen neu geparst.

    ``Symbol("x", positive=True)`` und ``Symbol("x")`` sind fuer SymPy zwei
    Symbole, also passte eine Komponente nicht mehr in den neu gebauten Ring;
    ``Symbol("x space")`` wurde sogar in zwei Generatoren zerlegt. Beides von
    einem externen Audit gebaut.
    """
    for first, second in (
        (sp.Symbol("x", positive=True), sp.Symbol("y", real=True)),
        (sp.Symbol("x space"), sp.Symbol("y")),
    ):
        source = over_field(
            PolynomialMap((first, second), (first + second**3, second)),
        )
        step = BCWStep.build(source, 0, Fresh(second, u), Fresh(second**2, v), 0)

        outcome = peel(source, step.target, budget=20)

        assert outcome.reduction is not None
        assert outcome.reduction.target.variables[:2] == (first, second)


def test_a_ratio_outside_the_domain_is_not_a_constant() -> None:
    """Auch fuer Zuege, die eine Koordinate abtragen, entscheidet die Domaene.

    Von Hand gebaut und kein Schritt: das kanonische Monom traegt im Produkt
    den Koeffizienten zwei und in der Zielkomponente eins, und ueber ``ZZ``
    gibt es dazu keine Konstante.
    """
    a, b, s = sp.symbols("a b s")
    made_up = PolynomialMap((s, a, b, x), (s - a * b, a + x, 2 * b + x**3, x))

    assert made_up.ring.domain.is_ZZ
    assert factor(made_up, s, (b, a), (a,)) is None
    assert factor(over_field(made_up), s, (b, a), (a,)) == sp.Rational(1, 2)


def test_a_source_coordinate_matching_the_pattern_is_not_peeled() -> None:
    """REV-2 ist ein Muster, keine Gewissheit.

    ``z`` steht hier zufaellig in genau zwei Komponenten, wird also probeweise
    abgetragen -- und die Karte danach enthaelt die Quelle nicht mehr. Alles
    Weitere setzt voraus, dass sie es tut, und lief in einen ``KeyError``. Der
    richtige Zug steht spaeter in derselben Liste und wurde nie erreicht.
    Gegenbeispiel eines externen Audits.
    """
    source = PolynomialMap((x, y, z), (x + y**3, y, z + y))
    step = BCWStep.build(source, 0, Carried(2), Fresh(y**2, u), 0)

    assert step.verify() is None

    outcome = peel(source, step.target, budget=20, pairs=1)

    assert outcome.reduction is not None
    assert outcome.reduction.target.reordered(step.target.variables) == step.target


def test_a_candidate_that_does_not_verify_is_discarded() -> None:
    """Eine erfolglose Suche gibt keinen Zertifikatsfehler nach aussen.

    Der Abtrag baut hier einen Kandidaten mit einem Faktor vom Grad null. ``H``
    liegt dann in ``EA^-1``, und BCW-6 lehnt das zu Recht ab -- die Vermutung
    war falsch, also faellt der Kandidat weg. Der Fehler schlug bis 0.4.0rc4
    aus ``peel`` heraus. Nullfaktoren bleiben dabei zulaessig: der
    Self-Fresh-Fall oben braucht sie.
    """
    source = PolynomialMap((x, y), (x + y**3, y))
    target = PolynomialMap(
        (x, y, u, v),
        (x + y**3 - (u + 1) * (v + y), y, u + 1, v + y),
    )

    outcome = peel(source, target, budget=20)

    assert outcome.reduction is None
    assert outcome.exhausted


def test_a_constant_that_cancels_no_monomial_is_not_tried() -> None:
    """Die zweite Haelfte von REV-10.

    Ziel und Produkt teilen hier das Monom ``a*b``, aber der Koeffizient des
    Schritts ist ``1`` und der einzige Kandidat, der ein Monom zum Verschwinden
    braechte, ist ``-1``. Der Schritt ist gueltig und wird nicht gefunden.
    Gegenbeispiel eines externen Audits, hier als Grenze festgehalten.
    """
    a, b, s = sp.symbols("a b s")
    source = PolynomialMap((s, a, b, x), (s + 2 * a * b + x**3, a, b, x))
    step = BCWStep.build(source, 0, Carried(1), Carried(2), 1, 1)

    assert step.verify() is None
    assert step.target.components == (s + a * b + x**3, a, b, x)
    assert {candidate.factor for candidate in moves(step.target, spare=1)} == {-1}

    outcome = peel(source, step.target, spare=1)

    assert outcome.reduction is None
    assert outcome.exhausted
