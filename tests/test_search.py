"""Candidate enumeration: what Proposition (3.1) could do on a map.

Nothing is verified here. A candidate is a proposal, and what makes it evidence
is ``BCWStep.build`` followed by ``verify()``, which is SEA-1. The tests
accordingly check the mechanism and completeness relative to the pool, and not
correctness in the sense of a certificate.

The control on real data stands in ``test_bcw17.py`` and
``test_alpoege15.py``, where the known steps are.
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
    """A component with a single composite monomial."""
    return PolynomialMap((x, y), (x + x**2 * y**3, y))


@pytest.fixture
def carried() -> PolynomialMap:
    """Coordinate 1 carries ``x**2``."""
    return PolynomialMap((x, y), (x + x**2 * y**3, y + x**2))


# --------------------------------------------------------------------------
# How the pool bounds the search
# --------------------------------------------------------------------------


def test_an_empty_pool_leaves_only_the_carriers(flat: PolynomialMap) -> None:
    """Coordinate 1 is a carrier but carries the value zero.

    That does not make it an anchor: one does not divide by zero, and a product
    with zero is not a partial sum that removes anything.
    """
    assert flat.carrier_indices == (1,)
    assert enumerate_candidates(flat, []) == ()


def test_a_pool_value_anchors_a_candidate(flat: PolynomialMap) -> None:
    found = enumerate_candidates(flat, [x * y])

    assert len(found) == 1
    assert found[0].index == 0
    assert found[0].values(flat) == (x * y, x * y**2)


def test_a_value_the_ring_cannot_hold_is_dropped(flat: PolynomialMap) -> None:
    """This makes the dependency between carriers drop out by itself.

    ``w6 = w1 x`` becomes convertible only once ``w1`` exists as a generator.
    Here ``z`` stands for such a ``w`` that has not been introduced yet.
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
    """The constructor of ``BCWStep`` rejects such a slot.

    A candidate proposing it could not be built, and an enumerator that
    proposes what cannot be built only postpones the check.
    """
    assert all(
        not (isinstance(slot, Carried) and slot.index == candidate.index)
        for candidate in enumerate_candidates(carried, [x, y, x * y])
        for slot in candidate.slots
    )


# --------------------------------------------------------------------------
# SEA-10: proper parts of the cofactor
# --------------------------------------------------------------------------


def test_a_proper_part_of_the_cofactor_is_offered() -> None:
    """The measurement behind SEA-10, on a small case.

    The largest cofactor is ``y + z``. The enumerator also offers ``y`` and
    ``z`` on their own, because step two of the ``alpoege15`` chain leaves
    exactly such a term behind.
    """
    source = PolynomialMap((x, y, z), (x + x * y + x * z, y, z))

    cofactors = {
        candidate.values(source)[1]
        for candidate in enumerate_candidates(source, [x])
        if candidate.index == 0
    }

    assert cofactors == {y + z, y, z}


def test_every_selection_is_checked_in_its_own_right() -> None:
    """Dropping terms from the cofactor is not a safe operation.

    ``(x - y) * (x + y) = x**2 - y**2`` is a partial sum, and ``x*y`` cancels in
    the product. The part ``x`` on its own gives ``x**2 - x*y``, and ``-x*y``
    does not stand in the component. Inheriting the check from the largest
    cofactor offers a candidate here that does not exist.
    """
    source = PolynomialMap((x, y), (x + x**2 - y**2, y))

    products = {
        candidate.product(source) for candidate in enumerate_candidates(source, [x - y])
    }

    assert products == {x**2 - y**2}


def test_the_selection_limit_keeps_only_the_largest_cofactor() -> None:
    """A bound against a pathological case and not against the data."""
    source = PolynomialMap((x, y, z), (x + x * y + x * z + x * y * z, y, z))

    unlimited = enumerate_candidates(source, [x])
    limited = enumerate_candidates(source, [x], selection_limit=2)

    assert len(unlimited) == 7
    assert len(limited) == 1
    assert limited[0].values(source)[1] == y * z + y + z


# --------------------------------------------------------------------------
# The derived level
# --------------------------------------------------------------------------


def test_the_level_follows_from_the_orders(flat: PolynomialMap) -> None:
    """``H`` shifts the fresh coordinates by the factors."""
    candidate = enumerate_candidates(flat, [x * y])[0]

    assert candidate.filtration_level(flat) == 1


def test_a_factor_of_order_one_drops_the_level() -> None:
    """A factor of order one pushes ``H`` down to ``EA^0``."""
    source = PolynomialMap((x, y), (x + x**2 * y + x**2 * y**2, y))

    levels = {
        str(c.values(source)[1]): c.filtration_level(source)
        for c in enumerate_candidates(source, [x * y])
    }

    assert levels == {"x*y + x": 0, "x": 0, "x*y": 1}


def test_without_a_fresh_slot_the_level_is_one() -> None:
    """``H`` is then the identity and lies in every ``EA^d``."""
    source = PolynomialMap((x, y, z), (x + y**2 * z**2, y + y**2, z + z**2))

    candidate = Candidate(0, Carried(1), Carried(2))

    assert candidate.m == 0
    assert candidate.filtration_level(source) == 1


# --------------------------------------------------------------------------
# Names come from outside
# --------------------------------------------------------------------------


def test_factors_take_the_names_in_slot_order(flat: PolynomialMap) -> None:
    candidate = enumerate_candidates(flat, [x * y])[0]

    assert candidate.factors((u, v)) == (Fresh(x * y, u), Fresh(x * y**2, v))


def test_a_carried_slot_consumes_no_name(carried: PolynomialMap) -> None:
    candidate = enumerate_candidates(carried, [])[0]

    assert candidate.factors((u,)) == (Carried(1), Fresh(y**3, u))


def test_too_few_names_are_refused(flat: PolynomialMap) -> None:
    """Better to refuse than to invent a name nobody handed out."""
    candidate = enumerate_candidates(flat, [x * y])[0]

    with pytest.raises(ValueError, match="fewer names were supplied"):
        candidate.factors((u,))


# --------------------------------------------------------------------------
# SEA-2 and the bridge to the certificate
# --------------------------------------------------------------------------


def test_the_enumeration_is_a_pure_function(carried: PolynomialMap) -> None:
    first = enumerate_candidates(carried, [x, y, x * y])
    second = enumerate_candidates(carried, [x, y, x * y])

    assert first == second


def test_swapping_the_slots_is_not_offered_twice(flat: PolynomialMap) -> None:
    """Swapped slots give the same step up to the naming."""
    products = [
        candidate.product(flat) for candidate in enumerate_candidates(flat, [x * y])
    ]

    assert products == [x**2 * y**3]


def test_a_candidate_builds_and_verifies(flat: PolynomialMap) -> None:
    """The transition SEA-1 means: a proposal, then a certificate."""
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
    """``H`` would otherwise lie outside ``EA^0`` and BCW-6 would refuse.

    Moving the refusal from the enumerator to the constructor does not make it
    safer, only later.
    """
    source = PolynomialMap((x, y), (x + x * y + x, y))

    assert anchors(source, [sp.Integer(2)]) == (Carried(1),)
    assert all(
        candidate.values(source)[1] != 1
        for candidate in enumerate_candidates(source, [x])
    )


def test_a_carried_cofactor_moves_to_the_first_slot() -> None:
    """Carriers first, the order in which the reference chains stand."""
    source = PolynomialMap((x, y), (x + x**3 * y, y + x**2))

    found = enumerate_candidates(source, [x * y])

    assert [(c.index, c.left, c.right) for c in found] == [(0, Carried(1), x * y)]


# --------------------------------------------------------------------------
# Conjugation with a diagonal of signs
# --------------------------------------------------------------------------


def test_conjugation_is_an_involution(flat: PolynomialMap) -> None:
    """``D`` is its own inverse."""
    signs = (1, -1)

    assert conjugate(conjugate(flat, signs), signs) == flat


def test_conjugation_preserves_what_a_certificate_claims() -> None:
    """Degree, order, filtration degree and the Keller determinant survive.

    That is why SEA-5 with a reported ``D`` is still a statement about the same
    map and not about a different one.
    """
    source = over_field(examples.cubic_shear())

    moved = conjugate(source, (1, -1))

    assert moved != source
    assert moved.degree() == source.degree()
    assert moved.order() == source.order()
    assert moved.filtration_degree() == source.filtration_degree()
    assert moved.determinant() == source.determinant() == 1


def test_a_non_constant_determinant_moves_with_the_coordinates() -> None:
    """It survives as a function and not as a polynomial.

    For a Keller map that is the same constant, which is the case SEA-5 is
    about. Otherwise the two differ by the signs.
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
    """A zero is not a change of coordinates."""
    with pytest.raises(ValueError, match="non-zero entries"):
        conjugate(flat, wrong)


def test_an_entry_other_than_a_sign_is_admitted(flat: PolynomialMap) -> None:
    """Until 0.4 ``D`` was restricted to ``+-1``, and that was too narrow.

    A diagonal with arbitrary non-zero entries is just as much a change of
    coordinates. The peel went from depth six to eleven with it.
    """
    keller = over_field(PolynomialMap((x, y), (x + y**3, y)))
    scaled = conjugate(keller, (2, 1))

    assert scaled.components == (x + 2 * y**3, y)
    assert scaled.determinant() == keller.determinant() == 1
    assert conjugate(scaled, (sp.Rational(1, 2), 1)) == keller


def test_a_non_unit_over_a_ring_is_refused(flat: PolynomialMap) -> None:
    """Over ``ZZ`` there is no inverse of two."""
    with pytest.raises(ValueError, match="not a unit"):
        conjugate(flat, (2, 1))


# --------------------------------------------------------------------------
# Reading D off
# --------------------------------------------------------------------------


def test_the_diagonal_is_read_off(flat: PolynomialMap) -> None:
    signs = (1, -1)

    found = diagonal_matching(conjugate(flat, signs), flat)

    assert found is not None
    assert conjugate(conjugate(flat, signs), found) == flat


def test_maps_of_different_shape_have_no_diagonal(flat: PolynomialMap) -> None:
    """Different monomials, so no choice of signs repairs it."""
    other = PolynomialMap((x, y), (x + x**2 * y**2, y))

    assert diagonal_matching(other, flat) is None


def test_a_different_magnitude_has_no_diagonal(flat: PolynomialMap) -> None:
    """``D`` can turn signs and not coefficients."""
    other = PolynomialMap((x, y), (x + 2 * x**2 * y**3, y))

    assert diagonal_matching(other, flat) is None


def test_an_inconsistent_system_has_no_diagonal() -> None:
    """Two monomials demand the same product with different signs."""
    source = PolynomialMap((x, y), (x + x * y**2 + x**3, y))
    other = PolynomialMap((x, y), (x + x * y**2 - x**3, y))

    assert diagonal_matching(other, source) is None


def test_a_different_generator_order_is_refused(flat: PolynomialMap) -> None:
    """SEA-4 first: reorder, then compare."""
    with pytest.raises(ValueError, match="different generators"):
        diagonal_matching(flat.reordered((y, x)), flat)


# --------------------------------------------------------------------------
# The search
# --------------------------------------------------------------------------


@pytest.fixture
def two_step() -> tuple[PolynomialMap, PolynomialMap, dict]:
    """Source, target and pool of a chain whose answer is known."""
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
    """Since WP 10 SEA-5 is plain equality again, and for that the forward
    search lacks something the peel does not lack.

    The family of steps is closed under diagonal conjugation, so a chain to the
    conjugated target does exist. Its steps carry different coefficients and
    different factor values, and both come here from a pool read off the
    unconjugated target. The peel solves for them instead, see
    ``test_peeling.py``.
    """
    source, target, pool = two_step
    flipped = conjugate(target, (1, 1, 1, -1))

    assert search(source, flipped, pool).reduction is None
    assert search(source, target, pool).reduction is not None


def test_a_value_outside_the_pool_is_unreachable(two_step: tuple) -> None:
    """Without rewrites not unfound, but unreachable.

    That is the price of SEA-8. ``rewrites`` relaxes it, and does so by name.
    See the tests further down.
    """
    source, target, _ = two_step

    outcome = search(source, target, {u: x, v: x * y**2}, rewrites=0)

    assert outcome.reduction is None
    assert outcome.exhausted


def test_a_budget_that_runs_out_says_less(two_step: tuple) -> None:
    """SEA-6 with even less content: ``exhausted`` tells the cases apart."""
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
    """The endpoint decides and not the chain."""
    source = over_field(PolynomialMap((x, y), (x + x**2 * y**3, y)))
    reachable = BCWStep.build(source, 0, Fresh(x * y, u), Fresh(x * y**2, v), 1).target
    wrong = PolynomialMap(
        reachable.variables,
        (reachable.components[0] + u * v,) + tuple(reachable.components[1:]),
    )

    assert search(source, wrong, {u: x * y, v: x * y**2}).reduction is None


def test_a_chain_that_would_raise_the_degree_is_not_walked() -> None:
    """Pruning: along both reference chains the degree never falls.

    The rule is a decision about the search and not a statement about Keller
    maps. A certificate requires no progress.
    """
    source = over_field(PolynomialMap((x, y), (x + x**2 * y**3, y)))
    target = BCWStep.build(source, 0, Fresh(x * y, u), Fresh(x * y**2, v), 1).target

    assert target.degree() <= source.degree()
    assert search(source, target, {u: x * y, v: x * y**2}).reduction is not None


def test_a_target_of_the_wrong_dimension_is_not_reached() -> None:
    """Every name spent, and the dimension does not match."""
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
    """Coordinate 1 carries ``x**2``, so there are ``m = 1`` moves."""
    return over_field(PolynomialMap((x, y), (x + x**3 * y**3, y + x**2)))


def test_a_carried_slot_consumes_no_name_in_the_search(
    with_carrier: PolynomialMap,
) -> None:
    """A step that reuses an existing carrier costs no dimension and no name
    from the pool."""
    target = BCWStep.build(with_carrier, 0, Carried(1), Fresh(x * y**3, u), 1).target

    outcome = search(with_carrier, target, {u: x * y**3})

    assert outcome.reduction is not None
    assert outcome.reduction.steps[0].left == Carried(1)
    assert outcome.reduction.target == target


def test_a_step_past_the_target_dimension_is_not_walked(
    with_carrier: PolynomialMap,
) -> None:
    """Pruning: the dimension may not exceed that of the target.

    The pool holds two names here and the target has room for one, so the
    ``m = 2`` move is built, checked and then discarded.
    """
    target = BCWStep.build(with_carrier, 0, Carried(1), Fresh(x * y**3, u), 1).target

    outcome = search(with_carrier, target, {u: x * y**3, v: x**2})

    assert outcome.reduction is None
    assert outcome.exhausted
    assert target.dimension == with_carrier.dimension + 1


# --------------------------------------------------------------------------
# Steps that introduce no generator
# --------------------------------------------------------------------------


@pytest.fixture
def spare_case() -> tuple[PolynomialMap, PolynomialMap]:
    """Source and target of a chain of a single ``m = 0`` step.

    Coordinate 1 carries ``x**2``, coordinate 2 carries ``x**3``, and component
    0 contains their product. The step reuses both carriers and spends no
    name.
    """
    source = over_field(PolynomialMap((x, y, z), (x + x**5, y + x**2, z + x**3)))
    target = BCWStep.build(source, 0, Carried(1), Carried(2), 1).target

    return source, target


def test_a_chain_may_end_with_a_step_that_introduces_nothing(
    spare_case: tuple[PolynomialMap, PolynomialMap],
) -> None:
    """The endpoint is checked as soon as every name is handed out, and the
    search continues afterwards while a spare step is left.

    Without this, a chain whose last step creates no generator would be
    unreachable. The published nineteen-dimensional map needs at least one such
    step: its dimension grows by sixteen over seventeen steps.
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
    """A negative control: ``spare`` is the bound on the length of a chain.

    Every other step spends a name, so a chain has at most
    ``len(pool) + spare`` steps. Without a spare step the chain here is not
    unfound but inexpressible.
    """
    source, target = spare_case

    outcome = search(source, target, {}, spare=0)

    assert outcome.reduction is None
    assert outcome.exhausted


def test_a_spare_step_is_refused_mid_chain_as_well(
    spare_case: tuple[PolynomialMap, PolynomialMap],
) -> None:
    """The bound does not apply only at the end of the chain.

    Names are still open here, so the search continues, and the ``m = 0`` moves
    are discarded all the same.
    """
    source, target = spare_case

    outcome = search(source, target, {u: x**4}, spare=0)

    assert outcome.reduction is None
    assert outcome.exhausted


def test_the_outcome_says_how_far_a_failed_search_got(two_step: tuple) -> None:
    """On a failure this is the only statement about *what* happened.

    A search that never gets beyond a few steps reports something different
    from one that hands out the last name and fails at the endpoint.
    """
    source, target, pool = two_step

    reached = search(source, target, pool)
    stopped = search(source, target, {u: x, v: x * y**2}, rewrites=0)

    assert reached.deepest == 1
    assert stopped.reduction is None
    assert stopped.deepest == 0


# --------------------------------------------------------------------------
# Coordinates that are overwritten later
# --------------------------------------------------------------------------


@pytest.fixture
def rewritten() -> tuple[PolynomialMap, PolynomialMap, dict]:
    """A chain whose second fresh coordinate is rewritten later.

    Step one creates ``u`` and ``v``, and step two aims at the component of
    ``v``. In the target ``v`` therefore no longer carries the value it was
    introduced with, and a pool read off the target does not contain that
    value. Exactly the case ``alpoege15`` shows on real data.
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
    """SEA-13: the pool bounds the anchor and not every fresh slot.

    A slot whose factor the pool does not know is given a free name. It can
    then reach the target only if a later step rewrites its component, which is
    what happens here.
    """
    source, target, pool = rewritten

    outcome = search(source, target, pool, rewrites=1)

    assert outcome.reduction is not None
    assert outcome.reduction.verify() is None
    assert outcome.reduction.target == target


def test_without_a_rewrite_that_chain_is_out_of_reach(rewritten: tuple) -> None:
    """A negative control. The failure says nothing about existence."""
    source, target, pool = rewritten

    outcome = search(source, target, pool, rewrites=0)

    assert outcome.reduction is None
    assert outcome.exhausted


def test_a_matching_value_takes_its_own_name(two_step: tuple) -> None:
    """A factor the pool knows costs no rewrite.

    Otherwise the branching could not be paid for: every fresh slot would then
    have as many moves as there are free names.
    """
    source, target, pool = two_step

    outcome = search(source, target, pool, rewrites=0)

    assert outcome.reduction is not None
    assert outcome.reduction.target == target


def test_the_diagonal_is_read_off_an_overdetermined_system() -> None:
    """Every monomial of every component is one equation, so there are far more
    equations than unknowns, and the later ones reduce against the earlier.

    Since WP 10 ``diagonal_matching`` carries no obligation: SEA-5 is plain
    equality again, because the coefficient stands in the step. It still
    answers the diagnostic question of how two chains that are the same
    reduction differ.
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
    """The same three cases as for the peel, and the same promise.

    ``search(F, F)`` raised the internal error of RED-1, a target of equal
    dimension over other generators raised a ``ValueError`` out of
    ``reordered``, and a budget spent exactly counted as a cut-off search. An
    external audit built all three. ``contracts.md`` has promised since 0.3
    that an unsuccessful search raises nothing.
    """
    elsewhere = PolynomialMap(sp.symbols("p q"), sp.symbols("p q"))

    assert search(flat, flat, {}).reduction is None
    assert search(flat, flat, {}).exhausted
    assert search(flat, elsewhere, {}).reduction is None
    assert search(flat, elsewhere, {}).exhausted


def test_a_budget_spent_exactly_is_not_a_cut_off() -> None:
    """A budget spent exactly is not a cut-off but an end.

    For that the target has to reach the walk. Until 0.4.0rc10 the source
    ``flat`` stood here with the target ``x**5 + x + x**2*y**3``. The two have
    different determinants, and since ``settled`` checks BCW-7 as well, the
    endpoints answer the pair before the search. The test then no longer checks
    what its name says.

    The pair here has the same determinant and the same origin and is
    unreachable all the same, so the walk runs and exhausts itself after
    exactly one map.
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
    """``examined`` promises ``int``, and ``budget=1.5`` gave ``examined = 1.5``.

    ``True`` stands beside it, because ``bool`` is a subclass of ``int``: a
    budget of one map, almost certainly a typing slip and not the intention. An
    external audit measured the floating point case.
    """
    for bound in ("budget", "spare", "rewrites", "selection_limit"):
        for value in (1.5, True):
            with pytest.raises(TypeError, match="must be integers"):
                search(flat, flat.extend(2), {}, **{bound: value})


def test_the_enumerator_refuses_a_bad_limit_of_its_own(flat: PolynomialMap) -> None:
    """The enumerator is public and was not checked through ``search``.

    Until 0.4.0rc9 ``selection_limit=-1`` silently yielded candidates, while
    the same value gave a ``ValueError`` through ``search``. An external audit
    made the direct call.
    """
    with pytest.raises(ValueError, match="must not be negative"):
        enumerate_candidates(flat, [x], selection_limit=-1)

    with pytest.raises(TypeError, match="must be integers"):
        enumerate_candidates(flat, [x], selection_limit=1.5)

    # Zero is allowed and means something: every quotient has more terms than
    # the limit, so it is offered undivided. The test records only that the
    # check does not confuse zero with a negative number.
    assert enumerate_candidates(flat, [x], selection_limit=0)


@pytest.fixture
def with_idle_moves() -> PolynomialMap:
    """A Keller map on which ``m = 0`` moves exist.

    Two carriers, ``a`` for ``x**2`` and ``b`` for ``y**2``, and a component
    containing their product. Without such moves the descent has nothing to do
    and a missing answer in advance does not show. That is why ``flat`` does
    not show the finding below.
    """
    a, b, s = sp.symbols("a b s")

    return PolynomialMap(
        (s, a, b, x, y),
        (s + x**2 * y**2 + x**4, a + x**2, b + y**2, x, y),
    )


def test_equal_endpoints_are_settled_before_the_search(
    with_idle_moves: PolynomialMap,
) -> None:
    """REV-11 before the search and not inside it, as in the peel.

    Until 0.4.0rc8 the test stood only in ``_finish``, that is in the descent.
    The non-answer case was therefore fixed before the start, and the budget
    still decided whether ``exhausted`` became true: false at a budget of one,
    true at a budget of four. An external audit built the map on which this is
    visible.
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
    """The second case of REV-11, and it now costs nothing either.

    Equal dimension means that every step introduces no generator, and such a
    step leaves the generators alone. No chain crosses from one set to the
    other.
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
    """The negative control: the test in advance must not swallow the search.

    The same generators, the same dimension, a different map. There is
    something to search for here, and the descent has to run.
    """
    a, b, s = sp.symbols("a b s")
    elsewhere = PolynomialMap(
        (s, a, b, x, y),
        (s + x**2 * y**2, a + x**2, b + y**2, x, y),
    )

    outcome = search(with_idle_moves, elsewhere, {}, budget=100)

    assert outcome.examined > 0


def test_a_chain_over_other_generators_is_a_non_answer() -> None:
    """And no ``ValueError`` out of ``reordered``.

    The chain really comes into existence here: the source stands below the
    target, but the pool carries names other than the target's. The descent
    therefore builds a chain of the right dimension over the wrong set of
    generators, and ``reordered`` rejects it correctly.

    Until 0.4.0rc9 a source over entirely different generators stood here.
    Since 0.4.0rc10 ``settled`` answers that case before the search and it no
    longer reaches the endpoint comparison, so the test no longer checked the
    place it is meant to check. An external audit prompted the extension of
    ``settled``. This version closes the gap that extension tore open here.
    """
    first, second = sp.symbols("p q")
    source = over_field(PolynomialMap((x, y), (x + x**2 * y**3, y)))
    target = BCWStep.build(source, 0, Fresh(x * y, u), Fresh(x * y**2, v), 1).target

    assert set(source.variables) <= set(target.variables)

    outcome = search(source, target, {first: x * y, second: x * y**2})

    assert outcome.reduction is None
    assert outcome.exhausted


def test_an_endpoint_no_step_can_reach_is_settled_before_the_walk() -> None:
    """Three invariants a ``BCWStep`` cannot change.

    A step introduces two, one or no coordinate and removes none. It takes its
    factors and its coefficient from the coefficient domain of its source. And
    it keeps every coordinate it was given. The non-answer is therefore fixed
    before the walk in all three cases.

    Until 0.4.0rc9 they were searched depending on the budget: at a budget of
    zero the space was called unexhausted, at a budget of one exhausted,
    although there was nothing to decide either time. An external audit
    measured the table.
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
    """BCW-7 requires a step to preserve the determinant.

    Every element of ``EA_n(k)`` has determinant one, and a step is a product of
    such elements with the stable extension. The non-answer is therefore fixed
    before the walk, and until 0.4.0rc10 it was searched depending on the
    budget. An external audit built the pair.
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
    """A step builds ``G o F^[m] o H`` and both factors fix the origin.

    Under BCW-6 ``H`` lies at least in ``EA^0`` and ``G`` in ``EA^1``, and the
    extension by identity coordinates appends zeros. So ``target(0) = 0`` holds
    exactly when ``source(0) = 0``, in both directions. An external audit built
    the pair.
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
    """The same exception, whether ``settled`` answers or the walk runs.

    Until 0.4.0rc11 ``settled`` stood before the argument check. On equal
    endpoints it returned before the pool was looked at, so
    ``search(F, F, None)`` gave a result while the same pool against endpoints
    that had to be walked raised. Whether a call is valid may not depend on how
    far the search gets. An external audit built it.

    The parameter ``label`` appears in the test name only and makes visible
    which of the two routes is reported when one of them breaks.
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
    """The negative control: the check must not reject everything.

    RC-4 requires symbols, pairwise distinct by name and disjoint from the
    ``reserved_names`` of the source ring. A name that satisfies this has to
    pass, even when ``settled`` answers immediately afterwards.
    """
    source = PolynomialMap((x, y), (x + y**3, y))

    assert search(source, source, {sp.Symbol("w"): x * y}).exhausted
    assert search(source, source.extend(2), {sp.Symbol("w"): x * y}).examined > 0


def test_a_reachable_extension_is_not_settled_away() -> None:
    """The negative control: the test in advance must not swallow a real search.

    More coordinates, the same domain, every generator of the source contained.
    There is something to search for here, and both directions have to run.
    """
    source = over_field(PolynomialMap((x, y), (x + x**2 * y**3, y)))
    target = BCWStep.build(source, 0, Fresh(x * y, u), Fresh(x * y**2, v), 1).target

    assert search(source, target, {u: x * y, v: x * y**2}).examined > 0
    assert peel(source, target, budget=50).examined > 0


def test_the_outcome_reports_its_ring_when_printed() -> None:
    """DOM-4, in the repr. ``PeelOutcome`` and ``ReductionOutcome`` do the same."""
    source = PolynomialMap((x, y), (x + x**2 * y**2, y))
    printed = repr(search(source, source.extend(2), {sp.Symbol("u"): x * y}, budget=5))

    assert printed.startswith("SearchOutcome(reduction=")
    assert "domain=ZZ" in printed
    assert "_domain" not in printed
