"""Kandidatenaufzaehlung: was Proposition (3.1) an einer Karte tun koennte.

Hier wird nichts verifiziert. Ein Kandidat ist ein Vorschlag, und was ihn zu
einem Beleg macht, ist ``BCWStep.build`` gefolgt von ``verify()`` -- SEA-1. Die
Tests pruefen entsprechend Mechanik und Vollstaendigkeit gegenueber dem Vorrat,
nicht Korrektheit im Sinne eines Zertifikats.

Die Kontrolle an echten Daten steht in ``test_bcw17.py`` und
``test_alpoege15.py``, wo die bekannten Schritte liegen.
"""

from collections.abc import Callable

import pytest
import sympy as sp

from kellermap import (
    Candidate,
    PolynomialMap,
    SearchOutcome,
    anchors,
    conjugate,
    diagonal_matching,
    enumerate_candidates,
    examples,
    over_field,
    peel,
    search,
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


# --------------------------------------------------------------------------
# Konjugation mit einer Vorzeichendiagonale
# --------------------------------------------------------------------------


def test_conjugation_is_an_involution(flat: PolynomialMap) -> None:
    """``D`` ist zu sich selbst invers."""
    signs = (1, -1)

    assert conjugate(conjugate(flat, signs), signs) == flat


def test_conjugation_preserves_what_a_certificate_claims() -> None:
    """Grad, Ordnung, Filtrationsgrad und die Keller-Determinante ueberleben.

    Deshalb ist SEA-5 mit einem ausgewiesenen ``D`` noch eine Aussage ueber
    dieselbe Abbildung und nicht ueber eine andere.
    """
    source = over_field(examples.cubic_shear())

    moved = conjugate(source, (1, -1))

    assert moved != source
    assert moved.degree() == source.degree()
    assert moved.order() == source.order()
    assert moved.filtration_degree() == source.filtration_degree()
    assert moved.determinant() == source.determinant() == 1


def test_a_non_constant_determinant_moves_with_the_coordinates() -> None:
    """Sie ueberlebt als Funktion, nicht als Polynom.

    Fuer eine Keller-Abbildung ist das dieselbe Konstante -- der Fall, um den
    es bei SEA-5 geht. Sonst unterscheiden sich die beiden um die Vorzeichen.
    """
    source = PolynomialMap((x, y), (x + x**2 * y**3, y))

    moved = conjugate(source, (1, -1))

    assert source.determinant() == 1 + 2 * x * y**3
    assert moved.determinant() == 1 - 2 * x * y**3


def test_the_identity_diagonal_changes_nothing(flat: PolynomialMap) -> None:
    assert conjugate(flat, (1, 1)) == flat


@pytest.mark.parametrize("wrong", [(1,), (1, 1, 1), (0, 1), (1, 0)])
def test_a_diagonal_must_be_invertible_and_the_right_length(
    flat: PolynomialMap, wrong: tuple[int, ...]
) -> None:
    """Eine Null ist kein Koordinatenwechsel."""
    with pytest.raises(ValueError, match="non-zero entries"):
        conjugate(flat, wrong)


def test_an_entry_other_than_a_sign_is_admitted(flat: PolynomialMap) -> None:
    """Bis 0.4 war ``D`` auf ``+-1`` beschraenkt, und das war zu eng.

    Eine Diagonale mit beliebigen Eintraegen ungleich null ist genauso ein
    Koordinatenwechsel. Das Abtragen kam damit von Tiefe sechs auf elf.
    """
    keller = over_field(PolynomialMap((x, y), (x + y**3, y)))
    scaled = conjugate(keller, (2, 1))

    assert scaled.components == (x + 2 * y**3, y)
    assert scaled.determinant() == keller.determinant() == 1
    assert conjugate(scaled, (sp.Rational(1, 2), 1)) == keller


def test_a_non_unit_over_a_ring_is_refused(flat: PolynomialMap) -> None:
    """Ueber ``ZZ`` gibt es kein Inverses zu zwei."""
    with pytest.raises(ValueError, match="not a unit"):
        conjugate(flat, (2, 1))


# --------------------------------------------------------------------------
# Das Ablesen von D
# --------------------------------------------------------------------------


def test_the_diagonal_is_read_off(flat: PolynomialMap) -> None:
    signs = (1, -1)

    found = diagonal_matching(conjugate(flat, signs), flat)

    assert found is not None
    assert conjugate(conjugate(flat, signs), found) == flat


def test_maps_of_different_shape_have_no_diagonal(flat: PolynomialMap) -> None:
    """Andere Monome, also keine Vorzeichenwahl, die es richtet."""
    other = PolynomialMap((x, y), (x + x**2 * y**2, y))

    assert diagonal_matching(other, flat) is None


def test_a_different_magnitude_has_no_diagonal(flat: PolynomialMap) -> None:
    """``D`` kann Vorzeichen drehen, keine Koeffizienten."""
    other = PolynomialMap((x, y), (x + 2 * x**2 * y**3, y))

    assert diagonal_matching(other, flat) is None


def test_an_inconsistent_system_has_no_diagonal() -> None:
    """Zwei Monome fordern dasselbe Produkt mit verschiedenem Vorzeichen."""
    source = PolynomialMap((x, y), (x + x * y**2 + x**3, y))
    other = PolynomialMap((x, y), (x + x * y**2 - x**3, y))

    assert diagonal_matching(other, source) is None


def test_a_different_generator_order_is_refused(flat: PolynomialMap) -> None:
    """SEA-4 zuerst: umsortieren, dann vergleichen."""
    with pytest.raises(ValueError, match="different generators"):
        diagonal_matching(flat.reordered((y, x)), flat)


# --------------------------------------------------------------------------
# Die Suche
# --------------------------------------------------------------------------


@pytest.fixture
def two_step() -> tuple[PolynomialMap, PolynomialMap, dict]:
    """Quelle, Ziel und Vorrat einer Kette, deren Antwort bekannt ist."""
    source = over_field(PolynomialMap((x, y), (x + x**2 * y**3, y)))
    target = BCWStep.build(source, 0, Fresh(x * y, u), Fresh(x * y**2, v), 1).target

    return source, target, {u: x * y, v: x * y**2}


def test_the_search_recovers_a_known_chain(two_step: tuple) -> None:
    source, target, pool = two_step

    outcome = search(source, target, pool)

    assert outcome.reduction is not None
    assert outcome.reduction.verify() is None
    assert outcome.reduction.target == target


def test_a_conjugated_target_is_out_of_reach_of_the_pool(two_step: tuple) -> None:
    """SEA-5 ist seit WP 10 wieder Gleichheit, und der Vorwaertssuche fehlt
    dafuer etwas, das dem Abtrag nicht fehlt.

    Die Schrittfamilie ist unter Diagonalkonjugation abgeschlossen, also *gibt*
    es eine Kette zum konjugierten Ziel -- ihre Schritte tragen aber andere
    Koeffizienten und andere Faktorwerte, und beide kommen hier aus einem
    Vorrat, der vom unkonjugierten Ziel abgelesen wurde. Der Abtrag loest sie
    stattdessen; siehe ``test_peeling.py``.
    """
    source, target, pool = two_step
    flipped = conjugate(target, (1, 1, 1, -1))

    assert search(source, flipped, pool).reduction is None
    assert search(source, target, pool).reduction is not None


def test_a_value_outside_the_pool_is_unreachable(two_step: tuple) -> None:
    """Ohne Umschreibungen nicht ungefunden, sondern unerreichbar.

    Das ist der Preis von SEA-8. ``rewrites`` lockert ihn, und zwar benannt:
    siehe die Tests weiter unten.
    """
    source, target, _ = two_step

    outcome = search(source, target, {u: x, v: x * y**2}, rewrites=0)

    assert outcome.reduction is None
    assert outcome.exhausted


def test_a_budget_that_runs_out_says_less(two_step: tuple) -> None:
    """SEA-6 mit noch weniger Gehalt: ``exhausted`` unterscheidet die Faelle."""
    source, target, pool = two_step

    outcome = search(source, target, pool, budget=1)

    assert outcome.reduction is None
    assert not outcome.exhausted
    assert outcome.examined == 1


def test_an_exhausted_space_is_reported_as_such(two_step: tuple) -> None:
    source, target, pool = two_step

    outcome = search(source, target, pool)

    assert outcome.exhausted is False or outcome.reduction is not None


def test_a_wrong_target_of_the_right_shape_is_not_found() -> None:
    """Der Endpunkt entscheidet, nicht die Kette."""
    source = over_field(PolynomialMap((x, y), (x + x**2 * y**3, y)))
    reachable = BCWStep.build(source, 0, Fresh(x * y, u), Fresh(x * y**2, v), 1).target
    wrong = PolynomialMap(
        reachable.variables,
        (reachable.components[0] + u * v,) + tuple(reachable.components[1:]),
    )

    assert search(source, wrong, {u: x * y, v: x * y**2}).reduction is None


def test_a_chain_that_would_raise_the_degree_is_not_walked() -> None:
    """Beschneidung: entlang beider Referenzketten faellt der Grad nie.

    Die Regel ist eine Entscheidung ueber die Suche, keine Aussage ueber
    Keller-Abbildungen -- ein Zertifikat verlangt keinen Fortschritt.
    """
    source = over_field(PolynomialMap((x, y), (x + x**2 * y**3, y)))
    target = BCWStep.build(source, 0, Fresh(x * y, u), Fresh(x * y**2, v), 1).target

    assert target.degree() <= source.degree()
    assert search(source, target, {u: x * y, v: x * y**2}).reduction is not None


def test_a_target_of_the_wrong_dimension_is_not_reached() -> None:
    """Alle Namen verbraucht, aber die Dimension passt nicht."""
    source = over_field(PolynomialMap((x, y), (x + x**2 * y**3, y)))
    target = BCWStep.build(source, 0, Fresh(x * y, u), Fresh(x * y**2, v), 1).target
    wider = target.extend(2)

    assert search(source, wider, {u: x * y, v: x * y**2}).reduction is None


def test_the_outcome_carries_what_was_examined(two_step: tuple) -> None:
    source, target, pool = two_step

    outcome = search(source, target, pool)

    assert isinstance(outcome, SearchOutcome)
    assert outcome.examined >= 1


@pytest.fixture
def with_carrier() -> PolynomialMap:
    """Koordinate 1 traegt ``x**2``, also gibt es ``m = 1``-Zuege."""
    return over_field(PolynomialMap((x, y), (x + x**3 * y**3, y + x**2)))


def test_a_carried_slot_consumes_no_name_in_the_search(
    with_carrier: PolynomialMap,
) -> None:
    """Ein Schritt, der einen vorhandenen Traeger wiederbenutzt, kostet keine
    Dimension und keinen Namen aus dem Vorrat."""
    target = BCWStep.build(with_carrier, 0, Carried(1), Fresh(x * y**3, u), 1).target

    outcome = search(with_carrier, target, {u: x * y**3})

    assert outcome.reduction is not None
    assert outcome.reduction.steps[0].left == Carried(1)
    assert outcome.reduction.target == target


def test_a_step_past_the_target_dimension_is_not_walked(
    with_carrier: PolynomialMap,
) -> None:
    """Beschneidung: die Dimension darf die des Ziels nicht ueberschreiten.

    Der Vorrat haelt hier zwei Namen und das Ziel hat nur Platz fuer einen, so
    dass der ``m = 2``-Zug gebaut, geprueft und dann verworfen wird.
    """
    target = BCWStep.build(with_carrier, 0, Carried(1), Fresh(x * y**3, u), 1).target

    outcome = search(with_carrier, target, {u: x * y**3, v: x**2})

    assert outcome.reduction is None
    assert outcome.exhausted
    assert target.dimension == with_carrier.dimension + 1


# --------------------------------------------------------------------------
# Schritte, die keinen Generator einfuehren
# --------------------------------------------------------------------------


@pytest.fixture
def spare_case() -> tuple[PolynomialMap, PolynomialMap]:
    """Quelle und Ziel einer Kette aus einem einzigen ``m = 0``-Schritt.

    Koordinate 1 traegt ``x**2``, Koordinate 2 traegt ``x**3``, und Komponente
    0 enthaelt deren Produkt. Der Schritt benutzt beide Traeger wieder und
    verbraucht keinen Namen.
    """
    source = over_field(PolynomialMap((x, y, z), (x + x**5, y + x**2, z + x**3)))
    target = BCWStep.build(source, 0, Carried(1), Carried(2), 1).target

    return source, target


def test_a_chain_may_end_with_a_step_that_introduces_nothing(
    spare_case: tuple[PolynomialMap, PolynomialMap],
) -> None:
    """Der Endpunkt wird geprueft, sobald alle Namen vergeben sind -- und die
    Suche laeuft danach weiter, solange ein Ersatzschritt uebrig ist.

    Ohne das waere eine Kette unerreichbar, deren letzter Schritt keinen
    Generator anlegt. Die veroeffentlichte neunzehndimensionale Abbildung
    braucht mindestens einen solchen Schritt: ihre Dimension waechst um
    sechzehn ueber siebzehn Schritte.
    """
    source, target = spare_case

    outcome = search(source, target, {}, spare=1)

    assert outcome.reduction is not None
    assert outcome.reduction.verify() is None
    assert outcome.reduction.target == target
    assert len(outcome.reduction.steps) == 1


def test_without_a_spare_step_that_chain_is_out_of_reach(
    spare_case: tuple[PolynomialMap, PolynomialMap],
) -> None:
    """Negativkontrolle: ``spare`` ist die Schranke fuer die Kettenlaenge.

    Jeder andere Schritt verbraucht einen Namen, also hat eine Kette hoechstens
    ``len(pool) + spare`` Schritte. Ohne Ersatzschritt ist die Kette hier nicht
    ungefunden, sondern nicht ausdrueckbar.
    """
    source, target = spare_case

    outcome = search(source, target, {}, spare=0)

    assert outcome.reduction is None
    assert outcome.exhausted


def test_a_spare_step_is_refused_mid_chain_as_well(
    spare_case: tuple[PolynomialMap, PolynomialMap],
) -> None:
    """Die Schranke gilt nicht erst am Ende der Kette.

    Hier sind noch Namen offen, also laeuft die Suche weiter, und die
    ``m = 0``-Zuege werden trotzdem verworfen.
    """
    source, target = spare_case

    outcome = search(source, target, {u: x**4}, spare=0)

    assert outcome.reduction is None
    assert outcome.exhausted


def test_the_outcome_says_how_far_a_failed_search_got(two_step: tuple) -> None:
    """Bei einem Fehlschlag ist das die einzige Angabe zum *Was*.

    Eine Suche, die nie ueber wenige Schritte hinauskommt, berichtet etwas
    anderes als eine, die den letzten Namen vergibt und am Endpunkt scheitert.
    """
    source, target, pool = two_step

    reached = search(source, target, pool)
    stopped = search(source, target, {u: x, v: x * y**2}, rewrites=0)

    assert reached.deepest == 1
    assert stopped.reduction is None
    assert stopped.deepest == 0


# --------------------------------------------------------------------------
# Koordinaten, die spaeter ueberschrieben werden
# --------------------------------------------------------------------------


@pytest.fixture
def rewritten() -> tuple[PolynomialMap, PolynomialMap, dict]:
    """Eine Kette, deren zweite frische Koordinate spaeter umgeschrieben wird.

    Schritt eins legt ``u`` und ``v`` an, Schritt zwei zielt auf die Komponente
    von ``v``. Im Ziel traegt ``v`` daher nicht mehr den Wert, mit dem es
    eingefuehrt wurde, und ein aus dem Ziel abgelesener Vorrat enthaelt diesen
    Wert nicht. Genau der Fall, den ``alpoege15`` an echten Daten zeigt.
    """
    t = sp.Symbol("t")
    source = over_field(
        PolynomialMap((x, y), (x + x**2 * y**3 + x**2 * y**5, y)),
    )
    middle = BCWStep.build(source, 0, Fresh(x * y, u), Fresh(x * y**2, v), 1).target
    target = BCWStep.build(middle, 3, Carried(2), Fresh(y, t), 0).target
    pool = {
        name: sp.expand(target.components[target.variables.index(name)] - name)
        for name in (u, v, t)
    }

    return source, target, pool


def test_a_coordinate_outside_the_pool_may_take_a_free_name(
    rewritten: tuple,
) -> None:
    """SEA-13: der Vorrat begrenzt den Anker, nicht jeden frischen Platz.

    Ein Platz, dessen Faktor der Vorrat nicht kennt, bekommt einen freien
    Namen. Er kann das Ziel dann nur erreichen, wenn ein spaeterer Schritt
    seine Komponente umschreibt -- was hier geschieht.
    """
    source, target, pool = rewritten

    outcome = search(source, target, pool, rewrites=1)

    assert outcome.reduction is not None
    assert outcome.reduction.verify() is None
    assert outcome.reduction.target == target


def test_without_a_rewrite_that_chain_is_out_of_reach(rewritten: tuple) -> None:
    """Negativkontrolle. Der Fehlschlag sagt nichts ueber die Existenz."""
    source, target, pool = rewritten

    outcome = search(source, target, pool, rewrites=0)

    assert outcome.reduction is None
    assert outcome.exhausted


def test_a_matching_value_takes_its_own_name(two_step: tuple) -> None:
    """Ein Faktor, den der Vorrat kennt, kostet keine Umschreibung.

    Sonst waere die Verzweigung nicht zu bezahlen: jeder frische Platz haette
    dann so viele Zuege wie es freie Namen gibt.
    """
    source, target, pool = two_step

    outcome = search(source, target, pool, rewrites=0)

    assert outcome.reduction is not None
    assert outcome.reduction.target == target


def test_the_diagonal_is_read_off_an_overdetermined_system() -> None:
    """Jedes Monom jeder Komponente ist eine Gleichung, also viel mehr als
    Unbekannte -- die spaeteren reduzieren gegen die frueheren.

    ``diagonal_matching`` traegt seit WP 10 keine Verpflichtung mehr: SEA-5 ist
    wieder Gleichheit, weil der Koeffizient im Schritt steht. Es beantwortet
    weiterhin die Diagnosefrage, worin sich zwei Ketten unterscheiden, die
    dieselbe Reduktion sind.
    """
    source = PolynomialMap(
        (x, y, z),
        (x + y**2 + y * z + z**3, y + x * z + x**2, z + x * y),
    )
    moved = conjugate(source, (1, -1, 1))

    found = diagonal_matching(moved, source)

    assert found == (1, -1, 1)
    assert conjugate(moved, found) == source


def test_the_forward_search_raises_nothing_when_it_finds_nothing(
    flat: PolynomialMap,
) -> None:
    """Dieselben drei Faelle wie beim Abtrag, und dieselbe Zusage.

    ``search(F, F)`` warf den internen Fehler von RED-1, ein gleichdimensionales
    Ziel auf anderen Generatoren einen ``ValueError`` aus ``reordered``, und ein
    genau aufgebrauchtes Budget galt als abgeschnittene Suche. Ein externes
    Audit hat alle drei gebaut; ``contracts.md`` sagt seit 0.3 zu, dass eine
    erfolglose Suche nichts wirft.
    """
    elsewhere = PolynomialMap(sp.symbols("p q"), sp.symbols("p q"))

    assert search(flat, flat, {}).reduction is None
    assert search(flat, flat, {}).exhausted
    assert search(flat, elsewhere, {}).reduction is None
    assert search(flat, elsewhere, {}).exhausted


def test_a_budget_spent_exactly_is_not_a_cut_off() -> None:
    """Ein genau aufgebrauchtes Budget ist kein Abschnitt, sondern ein Ende.

    Das Ziel muss dafuer den Walk erreichen. Bis 0.4.0rc10 stand hier die
    Quelle ``flat`` mit dem Ziel ``x**5 + x + x**2*y**3``; die beiden haben
    verschiedene Determinanten, und seit ``settled`` BCW-7 mitprueft,
    beantworten die Endpunkte das Paar vor der Suche. Der Test prueft dann
    nicht mehr, was sein Name sagt.

    Das Paar hier hat dieselbe Determinante und denselben Ursprung und ist
    trotzdem unerreichbar, also laeuft der Walk und erschoepft sich nach genau
    einer Karte.
    """
    source = PolynomialMap((x, y), (x + y**3, y))
    target = PolynomialMap((x, y), (x + y**5, y))

    assert target.determinant() == source.determinant()
    assert target.is_in_MA(0) == source.is_in_MA(0)

    tight = search(source, target, {}, budget=1)
    loose = search(source, target, {}, budget=2)

    assert tight.examined == loose.examined == 1
    assert tight.exhausted and loose.exhausted


def test_a_negative_bound_is_refused_by_the_search(flat: PolynomialMap) -> None:
    for bound in ("budget", "spare", "rewrites", "selection_limit"):
        with pytest.raises(ValueError, match="must not be negative"):
            search(flat, flat, {}, **{bound: -1})


def test_a_bound_that_is_not_a_whole_number_is_refused(flat: PolynomialMap) -> None:
    """``examined`` sagt ``int`` zu, und ``budget=1.5`` gab ``examined = 1.5``.

    ``True`` steht daneben, weil ``bool`` eine Unterklasse von ``int`` ist: ein
    Budget von einer Karte, fast sicher ein Tippfehler und nicht die Absicht.
    Ein externes Audit hat den Fliesskommafall gemessen.
    """
    for bound in ("budget", "spare", "rewrites", "selection_limit"):
        for value in (1.5, True):
            with pytest.raises(TypeError, match="must be integers"):
                search(flat, flat.extend(2), {}, **{bound: value})


def test_the_enumerator_refuses_a_bad_limit_of_its_own(flat: PolynomialMap) -> None:
    """Der Aufzaehler ist oeffentlich und wurde nicht ueber ``search`` geprueft.

    Bis 0.4.0rc9 lieferte ``selection_limit=-1`` still Kandidaten, waehrend
    derselbe Wert an ``search`` einen ``ValueError`` gab. Ein externes Audit hat
    den direkten Aufruf gemacht.
    """
    with pytest.raises(ValueError, match="must not be negative"):
        enumerate_candidates(flat, [x], selection_limit=-1)

    with pytest.raises(TypeError, match="must be integers"):
        enumerate_candidates(flat, [x], selection_limit=1.5)

    # Null ist erlaubt und heisst etwas: jeder Quotient hat mehr Terme als die
    # Schranke, also wird er ungeteilt angeboten. Der Test schreibt nur fest,
    # dass die Pruefung ihn nicht mit einer negativen Zahl verwechselt.
    assert enumerate_candidates(flat, [x], selection_limit=0)


@pytest.fixture
def with_idle_moves() -> PolynomialMap:
    """Eine Keller-Abbildung, an der es ``m = 0``-Zuege gibt.

    Zwei Traeger, ``a`` fuer ``x**2`` und ``b`` fuer ``y**2``, und eine
    Komponente, die deren Produkt enthaelt. Ohne solche Zuege hat der Abstieg
    nichts zu tun und eine fehlende Vorabantwort faellt nicht auf -- das ist
    der Grund, warum ``flat`` den Befund unten nicht zeigt.
    """
    a, b, s = sp.symbols("a b s")

    return PolynomialMap(
        (s, a, b, x, y),
        (s + x**2 * y**2 + x**4, a + x**2, b + y**2, x, y),
    )


def test_equal_endpoints_are_settled_before_the_search(
    with_idle_moves: PolynomialMap,
) -> None:
    """REV-11 vor der Suche und nicht in ihr, wie im Abtrag.

    Bis 0.4.0rc8 stand der Test nur in ``_finish``, also im Abstieg. Der
    Nichtantwort-Fall stand damit schon vor Beginn fest, und trotzdem entschied
    das Budget, ob ``exhausted`` wahr wurde: mit Budget eins falsch, mit Budget
    vier wahr. Ein externes Audit hat die Abbildung gebaut, an der es sichtbar
    ist.
    """
    assert with_idle_moves.determinant() == 1

    for budget in (0, 1, 4, 100):
        outcome = search(with_idle_moves, with_idle_moves, {}, budget=budget)

        assert outcome.reduction is None
        assert outcome.examined == 0
        assert outcome.deepest == 0
        assert outcome.exhausted


def test_a_target_of_one_dimension_on_other_generators_is_settled_too(
    with_idle_moves: PolynomialMap,
) -> None:
    """Der zweite Fall von REV-11, und er kostet jetzt ebenfalls nichts.

    Gleiche Dimension heisst, dass jeder Schritt keinen Generator einfuehrt,
    und ein solcher Schritt laesst die Generatoren in Ruhe. Keine Kette kann
    von der einen Menge in die andere.
    """
    p, q, r, t, w = sp.symbols("p q r t w")
    elsewhere = PolynomialMap(
        (p, q, r, t, w),
        (p + t**2 * w**2 + t**4, q + t**2, r + w**2, t, w),
    )

    outcome = search(with_idle_moves, elsewhere, {}, budget=100)

    assert outcome.reduction is None
    assert outcome.examined == 0
    assert outcome.exhausted


def test_a_different_target_of_one_dimension_is_still_searched(
    with_idle_moves: PolynomialMap,
) -> None:
    """Die Gegenkontrolle: der Vorabtest darf die Suche nicht verschlucken.

    Dieselben Generatoren, dieselbe Dimension, eine andere Karte. Hier gibt es
    etwas zu suchen, und der Abstieg hat zu laufen.
    """
    a, b, s = sp.symbols("a b s")
    elsewhere = PolynomialMap(
        (s, a, b, x, y),
        (s + x**2 * y**2, a + x**2, b + y**2, x, y),
    )

    outcome = search(with_idle_moves, elsewhere, {}, budget=100)

    assert outcome.examined > 0


def test_a_chain_over_other_generators_is_a_non_answer() -> None:
    """Und kein ``ValueError`` aus ``reordered``.

    Die Kette entsteht hier wirklich: die Quelle steht unter dem Ziel, der
    Vorrat traegt aber andere Namen als das Ziel. Der Abstieg baut also eine
    Kette der richtigen Dimension ueber der falschen Generatormenge, und
    ``reordered`` lehnt sie zu Recht ab.

    Bis 0.4.0rc9 stand hier eine Quelle ueber voellig anderen Generatoren.
    Dieser Fall wird seit 0.4.0rc10 von ``settled`` vor der Suche beantwortet und
    erreicht den Endpunktvergleich nicht mehr, also pruefte der Test die
    Stelle nicht mehr, die er pruefen soll. Ein externes Audit hat die
    Erweiterung von ``settled`` veranlasst; die Luecke, die sie hier reisst,
    schliesst diese Fassung.
    """
    first, second = sp.symbols("p q")
    source = over_field(PolynomialMap((x, y), (x + x**2 * y**3, y)))
    target = BCWStep.build(source, 0, Fresh(x * y, u), Fresh(x * y**2, v), 1).target

    assert set(source.variables) <= set(target.variables)

    outcome = search(source, target, {first: x * y, second: x * y**2})

    assert outcome.reduction is None
    assert outcome.exhausted


def test_an_endpoint_no_step_can_reach_is_settled_before_the_walk() -> None:
    """Drei Invarianten, die ein ``BCWStep`` nicht aendern kann.

    Ein Schritt fuehrt zwei, eine oder keine Koordinate ein und entfernt
    keine; er nimmt Faktoren und Koeffizient aus dem Koeffizientenbereich
    seiner Quelle; und er behaelt jede Koordinate, die er bekommen hat. Damit
    steht die Nichtantwort in allen drei Faellen vor dem Walk fest.

    Bis 0.4.0rc9 wurden sie budgetabhaengig durchsucht: mit Budget null hiess
    der Raum unerschoepft, mit Budget eins erschoepft, obwohl beide Male
    nichts zu entscheiden war. Ein externes Audit hat die Tabelle gemessen.
    """
    p, q = sp.symbols("p q")
    source = PolynomialMap((x, y), (x + y**3, y))
    smaller = PolynomialMap((x,), (x,))
    without_y = PolynomialMap((x, p, q), (x + p**3, p, q))
    over_qq = over_field(source)

    assert source.ring.domain != over_qq.ring.domain

    for target in (smaller, without_y, over_qq):
        for budget in (0, 1, 200):
            outcome = search(source, target, {}, budget=budget)
            unpicked = peel(source, target, budget=budget)

            assert outcome.examined == unpicked.examined == 0
            assert outcome.exhausted and unpicked.exhausted


def test_an_endpoint_of_another_determinant_is_settled_before_the_walk() -> None:
    """BCW-7 verlangt, dass ein Schritt die Determinante erhaelt.

    Jedes Element von ``EA_n(k)`` hat Determinante eins, und ein Schritt ist
    ein Produkt solcher Elemente mit der stabilen Erweiterung. Damit steht die
    Nichtantwort vor dem Walk fest, und bis 0.4.0rc10 wurde sie budgetabhaengig
    durchsucht. Ein externes Audit hat das Paar gebaut.
    """
    source = PolynomialMap((x, y), (x, y))
    target = PolynomialMap((x, y), (2 * x, y))

    assert source.determinant() != target.determinant()
    assert source.is_in_MA(0) and target.is_in_MA(0)
    assert set(source.variables) == set(target.variables)
    assert source.ring.domain == target.ring.domain

    for budget in (0, 1, 200):
        assert search(source, target, {}, budget=budget).examined == 0
        assert search(source, target, {}, budget=budget).exhausted
        assert peel(source, target, budget=budget).examined == 0
        assert peel(source, target, budget=budget).exhausted


def test_an_endpoint_that_moves_the_origin_is_settled_before_the_walk() -> None:
    """Ein Schritt baut ``G o F^[m] o H`` und beide Faktoren fixieren den Ursprung.

    ``H`` liegt nach BCW-6 mindestens in ``EA^0``, ``G`` in ``EA^1``, und die
    Erweiterung um Identitaetskoordinaten haengt Nullen an. Also ist
    ``target(0) = 0`` genau dann, wenn ``source(0) = 0``, und zwar in beide
    Richtungen. Ein externes Audit hat das Paar gebaut.
    """
    source = PolynomialMap((x, y), (x, y))
    target = PolynomialMap((x, y), (x + 1, y))

    assert source.is_in_MA(0) and not target.is_in_MA(0)
    assert source.determinant() == target.determinant()

    for budget in (0, 1, 200):
        for first, second in ((source, target), (target, source)):
            assert search(first, second, {}, budget=budget).examined == 0
            assert search(first, second, {}, budget=budget).exhausted
            assert peel(first, second, budget=budget).examined == 0
            assert peel(first, second, budget=budget).exhausted


@pytest.mark.parametrize(
    ("label", "target_of"),
    [
        ("settled", lambda source: source),
        ("walked", lambda source: source.extend(2)),
    ],
)
def test_the_arguments_are_checked_whatever_the_endpoints_do(
    label: str,
    target_of: Callable[[PolynomialMap], PolynomialMap],
) -> None:
    """Dieselbe Ausnahme, ob ``settled`` antwortet oder der Walk laeuft.

    Bis 0.4.0rc11 stand ``settled`` vor der Argumentpruefung. Bei gleichen
    Endpunkten kehrte es zurueck, bevor der Vorrat angesehen wurde, also gab
    ``search(F, F, None)`` ein Ergebnis, waehrend derselbe Vorrat gegen
    Endpunkte, die gelaufen werden mussten, warf. Ob ein Aufruf gueltig ist,
    darf nicht davon abhaengen, wie weit die Suche kommt. Ein externes Audit
    hat es gebaut.

    Der Parameter ``label`` steht nur im Testnamen und macht sichtbar, welcher
    der beiden Wege gemeldet wird, wenn einer bricht.
    """
    source = PolynomialMap((x, y), (x + y**3, y))
    target = target_of(source)

    with pytest.raises(TypeError, match="must be a mapping"):
        search(source, target, None)  # type: ignore[arg-type]

    with pytest.raises(TypeError, match="must be symbols"):
        search(source, target, {"w": x * y})  # type: ignore[dict-item]

    with pytest.raises(ValueError, match="must be fresh"):
        search(source, target, {x: x * y})

    with pytest.raises(ValueError, match="distinct by name"):
        search(
            source,
            target,
            {sp.Symbol("w"): x * y, sp.Symbol("w", positive=True): x * y**2},
        )

    with pytest.raises(TypeError, match="must be polynomial maps"):
        search(None, target, {})  # type: ignore[arg-type]

    with pytest.raises(TypeError, match="must be polynomial maps"):
        search(source, None, {})  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="must not be negative"):
        search(source, target, {}, budget=-1)


def test_a_fresh_pool_name_is_accepted() -> None:
    """Die Gegenkontrolle: die Pruefung darf nicht alles ablehnen.

    RC-4 verlangt Symbole, paarweise verschieden nach Namen und disjunkt zu
    ``reserved_names`` des Quellrings. Ein Name, der das erfuellt, hat
    durchzugehen -- auch dann, wenn ``settled`` gleich danach antwortet.
    """
    source = PolynomialMap((x, y), (x + y**3, y))

    assert search(source, source, {sp.Symbol("w"): x * y}).exhausted
    assert search(source, source.extend(2), {sp.Symbol("w"): x * y}).examined > 0


def test_a_reachable_extension_is_not_settled_away() -> None:
    """Die Gegenkontrolle: der Vorabtest darf keine echte Suche verschlucken.

    Mehr Koordinaten, gleicher Bereich, die Generatoren der Quelle alle
    enthalten -- hier ist etwas zu suchen, und beide Richtungen haben zu
    laufen.
    """
    source = over_field(PolynomialMap((x, y), (x + x**2 * y**3, y)))
    target = BCWStep.build(source, 0, Fresh(x * y, u), Fresh(x * y**2, v), 1).target

    assert search(source, target, {u: x * y, v: x * y**2}).examined > 0
    assert peel(source, target, budget=50).examined > 0
