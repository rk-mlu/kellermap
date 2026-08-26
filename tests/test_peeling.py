"""Peeling: a chain taken off the target, REV-1 to REV-12.

A peel is not a certificate. What is checked here is the mechanism, that is
removability, undoing and the sign, and the bridge back: that the structure
found is rebuilt forwards, verified and compared with the target before it is
called a ``Reduction``.
"""

import pytest
import sympy as sp

from kellermap import (
    PolynomialMap,
    VerificationError,
    enumerate_candidates,
    examples,
    over_field,
    search,
)
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
    """Source and target of a chain of one step with two fresh slots."""
    source = over_field(PolynomialMap((x, y), (x + x**2 * y**3, y)))
    target = BCWStep.build(source, 0, Fresh(x * y, u), Fresh(x * y**2, v), 1).target

    return source, target


@pytest.fixture
def two_steps() -> tuple[PolynomialMap, PolynomialMap]:
    """Two steps, the second with a ``Carried`` slot."""
    source = over_field(
        PolynomialMap((x, y), (x + x**3 * y**3 + x**2 * y**3, y)),
    )
    first = BCWStep.build(source, 0, Fresh(x * y, u), Fresh(x * y**2, v), 1)
    second = BCWStep.build(first.target, 0, Carried(2), Fresh(x**2 * y**2, t), 1)

    return source, second.target


# --------------------------------------------------------------------------
# REV-2: what can have been introduced last
# --------------------------------------------------------------------------


def test_a_fresh_coordinate_occurs_in_exactly_two_components(
    one_step: tuple[PolynomialMap, PolynomialMap],
) -> None:
    """In its own component and in the rest of the target component."""
    _, target = one_step

    assert removable(target) == {u: x, v: x}


def test_the_criterion_filters_and_the_undoing_decides(
    two_steps: tuple[PolynomialMap, PolynomialMap],
) -> None:
    """REV-2 is a cheap filter, REV-3 is the actual check.

    The second step aims at the same component as the first, so ``u`` still
    stands in exactly two components and is offered. It is not peeled off all
    the same: the step that created ``u`` and ``v`` was not the last one, and
    undoing shows this, because ``u`` is still there afterwards.
    """
    _, target = two_steps

    assert u in removable(target)
    assert undo(target, Undo(x, (u, v), (u, v), sp.Integer(1))) is None


def test_the_criterion_is_what_makes_the_direction_cheap() -> None:
    """Six of sixteen for the published map.

    Going forward, the enumerator offers over a hundred candidates on a map of
    this size. Here they are the coordinates that can have been introduced last
    at all.
    """
    fifteen = examples.alpoege15()

    assert 0 < len(removable(fifteen)) < fifteen.dimension - 3


# --------------------------------------------------------------------------
# REV-3: undoing
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
    """The second half of REV-3, and the actual check.

    ``v`` cannot be peeled off while ``u`` is still there: the step that
    created both was not the last one.
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
    """REV-4: the factor is decided by the coordinate disappearing."""
    _, target = one_step

    assert undo(target, Undo(x, (u, v), (u, v), sp.Integer(-1))) is None


# --------------------------------------------------------------------------
# The moves
# --------------------------------------------------------------------------


def test_steps_removing_two_coordinates_go_where_the_allowance_is(
    one_step: tuple[PolynomialMap, PolynomialMap],
) -> None:
    """First when the allowance is ample, last when it is scarce.

    Ample: a move that removes two coordinates gets twice as far for the same
    depth. Scarce: at ``pairs = 1`` the single such step is the last one of the
    peel under REV-8, and trying it first spends the only allowance early.

    Measured on ``alpoege15``, where one order finds it in eight maps and the
    other does not find it in two thousand.
    """
    _, target = one_step

    plentiful = list(moves(target, spare=0, pairs=16))
    scarce = list(moves(target, spare=0, pairs=1))

    assert len(plentiful[0].dropped) == 2
    assert len(scarce[-1].dropped) == 2

    # And ``pairs`` is a count and not a position: with none of these moves
    # allowed none is offered, with one allowed one is, wherever the map
    # stands.
    assert not any(len(step.dropped) == 2 for step in moves(target, spare=0, pairs=0))
    assert any(len(step.dropped) == 2 for step in scarce)


def test_without_a_spare_no_step_that_removes_nothing_is_offered() -> None:
    source = over_field(PolynomialMap((x, y), (x + x**5, y + x**2)))
    target = BCWStep.build(source, 0, Carried(1), Fresh(x**3, u), 1).target

    assert all(step.dropped for step in moves(target, spare=0))
    assert any(not step.dropped for step in moves(target, spare=1))


# --------------------------------------------------------------------------
# The bridge back
# --------------------------------------------------------------------------


def test_a_peel_returns_a_chain_that_was_built_forwards(
    one_step: tuple[PolynomialMap, PolynomialMap],
) -> None:
    """REV-5: the structure is rebuilt and verified, not adopted."""
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
    """SEA-5 is plain equality again, and since BCW-11 that is enough.

    The family of steps is closed under diagonal conjugation: what used to be
    reached only up to a ``D`` is itself a chain. The peel finds it, because it
    solves for the coefficient instead of searching for it.
    """
    source, target = one_step
    flipped = conjugate(target, (1, 1, 1, -1))

    outcome = peel(source, flipped)

    assert outcome.reduction is not None
    assert outcome.reduction.target.reordered(flipped.variables) == flipped


def test_a_target_that_is_not_reachable_is_reported_as_such(
    one_step: tuple[PolynomialMap, PolynomialMap],
) -> None:
    """REV-7: not a proof of non-existence, but an exhausted space."""
    source, target = one_step
    other = over_field(PolynomialMap((x, y), (x + y**7, y)))

    outcome = peel(other, target)

    assert outcome.reduction is None
    assert outcome.exhausted


def test_a_budget_that_runs_out_says_less(
    one_step: tuple[PolynomialMap, PolynomialMap],
) -> None:
    """REV-6, as in SEA-11."""
    source, target = one_step

    outcome = peel(source, target, budget=1)

    assert outcome.reduction is None
    assert not outcome.exhausted
    assert outcome.examined == 1
    assert outcome.deepest == 0


# --------------------------------------------------------------------------
# On real data
# --------------------------------------------------------------------------


@pytest.mark.slow
def test_peeling_recovers_a_chain_to_the_fifteen_dimensional_map() -> None:
    """The acceptance condition, on the map whose answer is known.

    Nothing is supplied but source and target: no pool, no names, no sign
    convention. That is REV-1, and it is the difference from the forward
    search, which makes the same find only with a pool value that the target
    map no longer carries.
    """
    from kellermap import LinearStep

    target = examples.alpoege15()
    source = LinearStep.normalize(over_field(examples.alpoege())).target

    outcome = peel(source, target, budget=200)

    assert outcome.reduction is not None
    assert outcome.reduction.verify() is None
    assert len(outcome.reduction.steps) == 7
    assert outcome.reduction.target.reordered(target.variables) == target

    # The sequence of dimensions is not pinned down. The peel finds *a* chain
    # and not *the* chain, and a change to the order of moves may find another
    # one without a test standing against it.
    dimensions = outcome.reduction.dimensions()

    assert dimensions[0] == 3
    assert dimensions[-1] == 15
    assert all(
        earlier <= later
        for earlier, later in zip(dimensions, dimensions[1:], strict=False)
    )


# --------------------------------------------------------------------------
# Moves that are discarded
# --------------------------------------------------------------------------


def test_two_removable_coordinates_with_different_targets_are_not_paired() -> None:
    """A step has exactly one target component.

    Two coordinates standing in different components cannot come from one and
    the same step.
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
    """The constructor of ``BCWStep`` rejects such a slot.

    An enumerator that offers what cannot be built only postpones the
    rejection.
    """
    source = over_field(PolynomialMap((x, y, z), (x + x**5, y + x**2, z + x**3)))
    target = BCWStep.build(source, 0, Carried(1), Carried(2), 1).target

    assert all(step.target not in step.slots for step in moves(target, spare=1))


def test_a_step_that_removes_nothing_is_offered_per_cancelling_constant() -> None:
    """Otherwise every product of two carriers with every constant is a move.

    Until 0.4.0rc6 the name and the reasoning of this test rested on a
    condition that 0.4.0rc4 removed, namely that undoing has to shorten the
    component. It lengthens it most of the time. What actually bounds the
    moves stands in REV-10: the constants offered are those that cancel one of
    the shared monomials.
    """
    source = over_field(PolynomialMap((x, y, z), (x + x**5, y + x**2, z + x**3)))
    target = BCWStep.build(source, 0, Carried(1), Carried(2), 1).target

    offered = [step for step in moves(target, spare=1) if not step.dropped]

    assert offered
    assert all(step.factor == 1 for step in offered)


def test_contradictory_signs_leave_no_diagonal() -> None:
    """REV-4 and SEA-5 together: ``D`` is solved for and not chosen.

    A step whose three coordinates all survive to the end binds fixed signs
    only. Peeled off with ``-``, it demands ``-1`` from a product that has to
    be ``+1``, and there is no ``D``. The chain is discarded rather than bent
    into shape.
    """
    source = over_field(PolynomialMap((x, y, z), (x + x**5, y + x**2, z + x**3)))
    target = BCWStep.build(source, 0, Carried(1), Carried(2), 1).target
    flipped = conjugate(target, (1, -1, 1))

    outcome = peel(source, flipped, spare=1)

    assert outcome.reduction is None
    assert outcome.exhausted


def test_a_carrier_may_also_be_a_target_and_is_then_not_its_own_slot() -> None:
    """A carrier component with more than two terms is both at once.

    It is a candidate target of one step and a slot of another. Both at once
    would be a slot on the component the step aims at, and the constructor of
    ``BCWStep`` rejects that.
    """
    source = over_field(
        PolynomialMap((x, y, z), (x + x**5, y + x**2 + x**3, z + x**3)),
    )
    target = BCWStep.build(source, 0, Carried(1), Carried(2), 1).target

    assert 1 in target.carrier_indices
    assert len(sp.Add.make_args(target.components[1])) > 2
    assert all(step.target not in step.slots for step in moves(target, spare=1))


def test_two_coordinates_that_disagree_on_the_factor_are_not_one_step() -> None:
    """A step has one factor and not two.

    Here two separate steps each create one coordinate on the same target
    component. Both are removable afterwards and are offered as a pair, but
    they demand different constants, so they do not come from one common
    step.
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
    """A pruning that comes from the source and not from a rule about Keller.

    The last step of a chain that introduces a coordinate has a ``Carried``
    slot, and that slot does not lie on the target component. Its component is
    therefore the same before and after the step, which makes it a carrier of
    the source as well. A source without carriers is not reachable this way,
    and a peel standing one coordinate too high is finished.

    Alpoege's map has no carriers, so this applies everywhere there.
    """
    carrying = over_field(PolynomialMap((x, y), (x + x**3 * y**3, y + x**2)))
    single = BCWStep.build(carrying, 0, Carried(1), Fresh(x * y**3, u), 1).target

    assert carrying.carrier_indices == (1,)
    assert peel(carrying, single).reduction is not None

    without = over_field(PolynomialMap((x, y), (x + x**2 * y**3, y + x * y)))
    both = BCWStep.build(without, 0, Fresh(x * y, u), Fresh(x * y**2, v), 1).target

    assert without.carrier_indices == ()
    assert peel(without, both).reduction is not None

    # Another target of the same shape forces the search to consider the moves
    # that peel off one coordinate alone as well. They lead to one coordinate
    # more than the source and are discarded, rather than searching for a step
    # that cannot exist there.
    stranger = over_field(PolynomialMap((x, y), (x + x**2 * y**5, y + x * y)))

    assert stranger.carrier_indices == ()
    assert peel(stranger, both).reduction is None


def test_the_number_of_pair_steps_is_bounded(
    one_step: tuple[PolynomialMap, PolynomialMap],
) -> None:
    """``pairs`` is the arithmetic of REV-8 as a rule.

    With ``a`` steps introducing two generators, ``b`` introducing one and
    ``c`` introducing none, ``2a + b = n`` and ``S = n - a + c`` hold. Fixing
    the number of steps therefore fixes ``a``. Without such a step, a chain
    that needs one is not unfound but unreachable.
    """
    source, target = one_step

    assert peel(source, target, pairs=1).reduction is not None

    without = peel(source, target, pairs=0)

    assert without.reduction is None
    assert without.exhausted


def test_both_slots_may_name_the_same_coordinate() -> None:
    """BCW-6 has allowed this since 0.3, and the peel did not enumerate it.

    ``G`` is then ``X_i - X_j**2``. ``combinations`` alone offers distinct
    pairs only, so a chain with such a step was not unfound but unreachable.
    An external audit found the defect, not a test.
    """
    source = over_field(PolynomialMap((x, y), (x + x**4, y + x**2)))
    target = BCWStep.build(source, 0, Carried(1), Carried(1), 1).target

    assert any(step.slots[0] == step.slots[1] for step in moves(target, spare=1))

    outcome = peel(source, target, spare=1)

    assert outcome.reduction is not None
    assert outcome.reduction.verify() is None
    assert outcome.reduction.target == target


def test_the_degree_never_rises_above_the_source() -> None:
    """Going forward the degree never falls, so backwards it never rises above.

    Provable and not a decision: the new terms of a step have degree at most
    ``1 + deg Q <= deg(P Q)`` as long as no factor is constant, and constants
    are excluded. A peel that runs above the degree of the source can no longer
    reach it.
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
    """The coefficient domain and the monomial order belong to the target.

    Until 0.4.0rc1 the intermediate maps were rebuilt from expressions, and
    both were derived anew in the process: ``QQ`` came back as ``ZZ`` and
    ``grlex`` as whatever the expressions suggested. A valid chain could appear
    unreachable this way. An external audit reported it.
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
    """BCW-11 admits every constant of the domain, and ``T`` is one.

    A test on ``free_symbols`` would have taken ``T`` for a coordinate and
    discarded the step. Conversion and not inspection, as in BCW-3 and
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
    """Several shared monomials often give the same constant.

    Until 0.4.0rc2 each of them gave a move of its own: at the root of the
    published map, thirty-six candidates against sixteen distinct ones, ten of
    them threefold. An external audit counted it.
    """
    source = over_field(PolynomialMap((x, y), (x + x**5 + x**7, y + x**2)))
    target = BCWStep.build(source, 0, Carried(1), Carried(1), 1).target

    offered = list(moves(target, spare=1))

    assert offered
    assert len(offered) == len(set(offered))


def test_the_two_bounds_prune() -> None:
    """REV-8 and REV-9 prune measurably, and this test notices when they stop.

    Both bounds are provable and not heuristics, so removing them may change no
    result, only the number of maps examined. That is exactly why no test that
    checks results alone notices their failure, and a mutation probe confirmed
    this up to 0.4.0rc13: both could be switched off without the suite turning
    red.

    The number below is measured and not an estimate. Without REV-9 it is 50,
    without REV-8 it is 57, without both it is 58. It stands here so that it
    shows when one of the two stops pruning.
    """
    source = over_field(PolynomialMap((x, y), (x + x**2 * y**3, y + x**3 * y**2)))
    first = BCWStep.build(source, 0, Fresh(x * y, u), Fresh(x * y**2, v), 1).target
    p, q = sp.symbols("p q")
    target = BCWStep.build(first, 1, Fresh(x * y**2, p), Fresh(x * y, q), 1).target
    elementary = over_field(PolynomialMap((x, y), (x + y**5, y)))

    outcome = peel(elementary.compose(source), target, budget=5000)

    assert outcome.reduction is None
    assert outcome.exhausted
    assert outcome.examined == 49


def test_a_state_is_walked_once() -> None:
    """Independent steps commute, so many paths lead to the same map, and the
    subtree below it is the same every time.

    What belongs in the key besides the map is what is still available. The
    same map with one spare step left is not the same state.
    """
    p, q = sp.symbols("p q")
    source = over_field(PolynomialMap((x, y), (x + x**2 * y**3, y + x**3 * y**2)))
    first = BCWStep.build(source, 0, Fresh(x * y, u), Fresh(x * y**2, v), 1).target
    target = BCWStep.build(first, 1, Fresh(x * y**2, p), Fresh(x * y, q), 1).target

    # The two steps lie on different components and commute, so two paths lead
    # to the same map. A target that is not reachable makes the peel walk the
    # whole space and run into it on the way.
    #
    # The source is built from ``source`` by composing with an elementary
    # automorphism. That has determinant one, so the source has the same
    # determinant as the target and is not answered in advance by ``settled``.
    # Until 0.4.0rc10 a map with a different determinant stood here. Since
    # BCW-7 is checked in ``settled``, the peel would no longer have run at all
    # and the test would no longer reach the revisit it checks.
    elementary = over_field(PolynomialMap((x, y), (x + y**5, y)))
    elsewhere = elementary.compose(source)

    assert elsewhere.determinant() == target.determinant()

    exhausted = peel(elsewhere, target, budget=2000)

    assert exhausted.reduction is None
    assert exhausted.exhausted
    assert peel(source, target, budget=200).reduction is not None


# --------------------------------------------------------------------------
# The m = 0 branch computes in the ring
# --------------------------------------------------------------------------


def test_a_constant_outside_the_domain_is_not_a_move() -> None:
    """Over ``ZZ`` the value ``1/2`` is not a constant, however it looks.

    A counterexample from an external audit. The two shared monomials give
    ``1`` and ``1/2``. The second was emitted as a move, and the peel crashed
    while undoing, because the result no longer lay over ``ZZ``. The valid
    chain was in the space the whole time.
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


def test_a_factor_outside_the_domain_is_not_that_step() -> None:
    """``undo`` computes in the ring, so a factor has to be a constant of it.

    Until the ring arithmetic, ``undo`` added ``factor * left * right`` as an
    expression and rebuilt the map with ``from_expr``, which raised
    ``CoercionFailed`` out of a search. It now gives the answer ``moves`` gives
    for the same reason: no step over this ring carries that constant, so this
    was not that step.

    The map is over ``ZZ`` and ``1/2`` is not in it. The dropped coordinates
    would go, so nothing else refuses the step.
    """
    u, v = sp.symbols("u v")
    current = PolynomialMap((x, y, u, v), (x - u * v / 2, y, u, v))
    halved = Undo(target=x, slots=(u, v), dropped=(u, v), factor=sp.Rational(1, 2))

    assert current.ring.domain.is_QQ
    assert undo(current, halved) is not None

    over_integers = PolynomialMap((x, y, u, v), (x - u * v, y, u, v))

    assert over_integers.ring.domain.is_ZZ
    assert undo(over_integers, halved) is None
    assert undo(over_integers, Undo(x, (u, v), (u, v), sp.Integer(1))) is not None


def test_a_parameter_coefficient_is_found_at_m_zero() -> None:
    """``S*a*x - T*a*x`` is one monomial and not two summands.

    The second counterexample of the same audit. Cancellation was measured on
    ``sp.Add.make_args``, so this step did not look like a cancellation, and
    the peel reported an exhausted space after a single state. Counted in the
    ring it is one term with coefficient
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
    """``moves`` promises a fixed order, and a ``set`` has none.

    The deduplicated constants were emitted straight out of a set, so
    ``PYTHONHASHSEED`` decided which move came first and, at a small budget,
    which chain is found. They are sorted canonically
    now. This test checks the promise within one process. Independence of the
    seed itself is measurable outside it.
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
    """REV-10, and a boundary of the search space rather than a defect.

    The step removes ``a*b`` exactly, so no monomial is left in the target
    component that would reveal the constant. Every constant gives a map, and
    the peel would have to guess. A counterexample from an external audit,
    recorded here as a boundary: the step is valid and is not found.
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
    """The constant then sits in ``u**2`` and not in ``u``.

    ``factor`` looked at degree one only, so this step was unreachable and the
    comment called the case impossible. A factor of zero is not a special case:
    a carried coordinate without a value occurs in the same maps, and the
    constructor admits both.
    """
    source = over_field(PolynomialMap((x, y), (x + y**3, y)))
    step = BCWStep.build(source, 0, Fresh(0, u), Fresh(0, u), 1, 3)

    assert step.verify() is None

    outcome = peel(source, step.target)

    assert outcome.reduction is not None
    assert outcome.reduction.steps[0].coefficient == 3
    assert outcome.reduction.target.reordered(step.target.variables) == step.target


def test_the_generators_keep_their_identity() -> None:
    """The ring is cloned and not parsed anew from printed names.

    ``Symbol("x", positive=True)`` and ``Symbol("x")`` are two symbols for
    SymPy, so a component no longer fitted into the rebuilt ring.
    ``Symbol("x space")`` was even split into two generators. An external audit
    built both.
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
    """For moves that peel one coordinate the domain decides as well.

    Built by hand and not a step: the canonical monomial carries coefficient
    two in the product and one in the target component, and over ``ZZ`` there
    is no constant for that.
    """
    a, b, s = sp.symbols("a b s")
    made_up = PolynomialMap((s, a, b, x), (s - a * b, a + x, 2 * b + x**3, x))

    assert made_up.ring.domain.is_ZZ
    assert factor(made_up, s, (b, a), (a,)) is None
    assert factor(over_field(made_up), s, (b, a), (a,)) == sp.Rational(1, 2)


def test_a_source_coordinate_matching_the_pattern_is_not_peeled() -> None:
    """REV-2 is a pattern and not a certainty.

    Here ``z`` happens to stand in exactly two components and is therefore
    peeled off on trial, and the map after that no longer contains the source.
    Everything below assumes that it does, and it ran into a ``KeyError``. The
    right move stands later in the same list and was never reached. A
    counterexample from an external audit.
    """
    source = PolynomialMap((x, y, z), (x + y**3, y, z + y))
    step = BCWStep.build(source, 0, Carried(2), Fresh(y**2, u), 0)

    assert step.verify() is None

    outcome = peel(source, step.target, budget=20, pairs=1)

    assert outcome.reduction is not None
    assert outcome.reduction.target.reordered(step.target.variables) == step.target


def test_a_candidate_that_does_not_verify_is_discarded() -> None:
    """An unsuccessful search reports no certificate error to the outside.

    The peel builds a candidate here with a factor of degree zero. ``H`` then
    lies in ``EA^-1``, and BCW-6 rejects that correctly. The conjecture was
    wrong, so the candidate is dropped. Until 0.4.0rc4 the error escaped from
    ``peel``. Factors of zero stay admissible: the self-fresh case above needs
    them.

    A factor of degree zero is a non-zero constant, and the fresh coordinate
    then carries it as a constant term. The target therefore lies outside
    ``MA^0`` of necessity. ``settled`` has checked this since 0.4.0rc10, so the
    source has to move the origin as well. Otherwise the pair is answered
    before the peel and the test no longer reaches the branch it checks. Both
    maps have determinant one.
    """
    source = PolynomialMap((x, y), (x + y**3 + 1, y))
    target = PolynomialMap(
        (x, y, u, v),
        (x + y**3 + 1 - (u + 1) * (v + y), y, u + 1, v + y),
    )

    assert not source.is_in_MA(0) and not target.is_in_MA(0)

    outcome = peel(source, target, budget=20)

    assert outcome.reduction is None
    assert outcome.exhausted


def test_a_constant_that_cancels_no_monomial_is_not_tried() -> None:
    """The second half of REV-10.

    Target and product share the monomial ``a*b`` here, but the coefficient of
    the step is ``1`` and the only candidate that would make a monomial vanish
    is ``-1``. The step is valid and is not found. A counterexample from an
    external audit, recorded here as a boundary.
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


def test_a_pair_step_far_from_the_source_is_still_offered() -> None:
    """``pairs`` counts the moves and does not prescribe their position.

    Until 0.4.0rc5 a move that removes two coordinates was suppressed while the
    map stood more than two coordinates above the source, on the grounds that
    with a single allowance it had to be the last one peeled. That is wrong
    when its factor uses a coordinate introduced by an earlier step: it cannot
    then be commuted to the front. ``pairs=1`` therefore also meant a position,
    and the space was wrongly held to be exhausted. A counterexample from an
    external audit.
    """
    a, b = sp.symbols("a b")
    source = PolynomialMap((x, y, z), (x + y**8, y, z + y**2))
    first = BCWStep.build(source, 0, Carried(2), Fresh(y**6, u), 1)
    second = BCWStep.build(first.target, 0, Fresh(u * y, a), Fresh(y**2, b), 1)

    assert first.verify() is None
    assert second.verify() is None
    assert [step.m for step in (first, second)] == [1, 2]

    outcome = peel(source, second.target, budget=2000, spare=0, pairs=1)

    assert outcome.reduction is not None
    assert outcome.reduction.target.reordered(second.target.variables) == second.target


def test_a_chain_of_no_steps_is_not_representable() -> None:
    """REV-11. Equal endpoints are admissible input and not a chain.

    RED-1 requires at least one step, so that source and target of a
    ``Reduction`` are defined. A peel that finds the source already at the
    target therefore has nothing to build, and until 0.4.0rc5 it raised a
    ``ValueError`` out of a public function.
    """
    source = PolynomialMap((x, y), (x + y**3, y))

    outcome = peel(source, source, budget=10)

    assert outcome.reduction is None
    assert outcome.exhausted


def test_a_target_on_other_generators_is_a_non_answer() -> None:
    """And no ``ValueError`` out of ``reordered``.

    Two maps of one dimension over different generators are an admissible pair
    of arguments. Until 0.4.0rc5 the budget decided whether a result or an
    error came back.

    Since 0.4.0rc9 the answer is fixed before the descent and costs no map.
    Before that, one map was examined to say the same thing.
    """
    source = PolynomialMap((x, y), (x + y**3, y))
    elsewhere = PolynomialMap((u, v), (u + v**3, v))

    outcome = peel(source, elsewhere, budget=10)

    assert outcome.reduction is None
    assert outcome.exhausted
    assert outcome.examined == 0


def test_the_endpoints_are_checked_before_they_are_read() -> None:
    """``peel(None, F)`` raised an ``AttributeError`` out of ``settled``.

    That names an implementation, since ``NoneType`` has no ``dimension``, and
    not the argument that was wrong, while the error table in ``api.md``
    promises a ``TypeError`` for an argument of the wrong type. An external
    audit built it.

    Both cases stand here: one that ``settled`` would answer, and one that the
    peel would have to walk. The exception has to be the same.
    """
    source = PolynomialMap((x, y), (x + y**3, y))

    for target in (source, source.extend(2)):
        with pytest.raises(TypeError, match="must be polynomial maps"):
            peel(None, target)  # type: ignore[arg-type]

        with pytest.raises(TypeError, match="must be polynomial maps"):
            peel(source, None)  # type: ignore[arg-type]

    assert peel(source, source).exhausted
    assert peel(source, source.extend(2), budget=20).examined > 0


def test_a_bound_that_is_not_a_whole_number_is_refused_by_the_peel() -> None:
    """``examined`` promises ``int``, and ``budget=1.5`` gave ``examined = 1.5``.

    ``True`` stands beside it, because ``bool`` is a subclass of ``int``. The
    peel shares both cases with the forward search, since the check stands in
    one place.
    """
    source = PolynomialMap((x, y), (x + y**3, y))

    for bound in ("budget", "spare", "pairs", "rising"):
        for value in (1.5, True):
            with pytest.raises(TypeError, match="must be integers"):
                peel(source, source.extend(2), **{bound: value})


def test_equal_endpoints_do_not_yield_a_cycle() -> None:
    """REV-11 before the search and not inside it.

    Until 0.4.0rc6 the test in the descent prevented the empty ``Reduction``
    only. The search continued and could return to the source: a cyclic chain
    of two ``m = 0`` steps with the coefficients ``1`` and ``-1``,
    mathematically correct and against the library's own promise. A
    counterexample from an external audit.
    """
    a, b, s = sp.symbols("a b s")
    source = PolynomialMap((s, a, b, x), (s + a * b, a + x, b, x))

    outcome = peel(source, source, budget=100, spare=2, pairs=0)

    assert outcome.reduction is None
    assert outcome.exhausted
    assert outcome.examined == 0


def test_a_budget_spent_exactly_is_not_a_cut_off() -> None:
    """``exhausted`` says whether the search saw the end, not whether budget is left.

    There is exactly one state here and no move. Until 0.4.0rc6 the space was
    not exhausted at a budget of one and was exhausted at a budget of two,
    although everything had been seen in both cases.
    """
    source = PolynomialMap((x, y), (x + y**3, y))
    elsewhere = PolynomialMap((x, y), (x + y**5, y))

    tight = peel(source, elsewhere, budget=1)
    loose = peel(source, elsewhere, budget=2)

    assert tight.examined == loose.examined == 1
    assert tight.exhausted and loose.exhausted


def test_the_degree_may_rise_along_a_valid_chain() -> None:
    """REV-12, and the refutation of a proof written beside it.

    It read: the new terms have degree at most ``1 + deg Q``, so the degree
    never falls going forward. That holds for new factors and fails as soon as
    a factor is a component the map already has. This chain runs
    ``3, 4, 3``. A counterexample from an external audit.
    """
    a, b, s = sp.symbols("a b s")
    source = PolynomialMap((s, a, b, x, y), (s + x**3, a + x**2, b + y**2, x, y))
    first = BCWStep.build(source, 0, Carried(1), Carried(2), 1, 1)
    second = BCWStep.build(
        first.target, 0, Fresh(a + x**2, u), Fresh(b + y**2, v), 0, -1
    )

    assert first.verify() is None
    assert second.verify() is None
    assert (source.degree(), first.target.degree(), second.target.degree()) == (3, 4, 3)

    assert peel(source, second.target, spare=1, pairs=1).reduction is None
    assert peel(source, second.target, spare=1, pairs=1, rising=1).reduction is not None


def test_exhausted_does_not_depend_on_budget_once_the_space_is_seen() -> None:
    """``exhausted`` depends on whether anything stayed unchecked, and on nothing else.

    Until 0.4.0rc7 the store of seen states was consulted after the budget
    check, so a state known long since failed on the budget and the space was
    held to be unexhausted although everything had been seen. An external audit
    measured this on two commuting moves.

    What is checked here is the property and not that example: as soon as a
    budget sees the whole space, larger budgets change neither ``examined`` nor
    ``exhausted``. The example of the audit could not be rebuilt after the
    correction, which suggests the correction and does not prove it, and is why
    the property stands here.
    """
    source = over_field(PolynomialMap((x, y), (x + x**2 * y**3, y)))
    target = BCWStep.build(source, 0, Fresh(x * y, u), Fresh(x * y**2, v), 1).target
    elsewhere = over_field(PolynomialMap((x, y), (x + y**5, y)))

    settled = [peel(elsewhere, target, budget=size) for size in range(1, 12)]
    once = next(outcome for outcome in settled if outcome.exhausted)

    assert all(
        outcome.examined == once.examined and outcome.exhausted
        for outcome in settled
        if outcome.examined >= once.examined
    )


def test_generators_of_one_name_are_told_apart() -> None:
    """``Symbol("x", positive=True)`` and ``Symbol("x", real=True)`` are two.

    The test before the search in REV-11 compared the printed names, took them
    for the same map and called ``reordered``, which rejected them correctly.
    That gave a ``ValueError`` exactly where REV-11 promises a non-answer.
    """
    positive, real = sp.Symbol("x", positive=True), sp.Symbol("x", real=True)
    source = PolynomialMap((positive, y), (positive + y**3, y))
    target = PolynomialMap((real, y), (real + y**3, y))

    outcome = peel(source, target, budget=10)

    assert outcome.reduction is None
    assert outcome.exhausted


def test_a_negative_bound_is_refused() -> None:
    """A negative budget gave ``examined = -1``, which counts nothing."""
    source = PolynomialMap((x, y), (x + y**3, y))

    for bound in ("budget", "spare", "pairs", "rising"):
        with pytest.raises(ValueError, match="must not be negative"):
            peel(source, source, **{bound: -1})


# --------------------------------------------------------------------------
# DOM-1 to DOM-4: the coefficient ring as a stated space
#
# Three narrowings used to end in an exhausted space, which SEA-6 and REV-7
# make a result rather than a defect. The space itself was never named.
# --------------------------------------------------------------------------


@pytest.fixture
def integral() -> PolynomialMap:
    """A map over ``ZZ``, and its twin over ``QQ`` is one call away."""
    return PolynomialMap((x, y), (x + y**3, y))


def test_without_over_the_ring_comes_from_the_source(integral: PolynomialMap) -> None:
    """DOM-1. The default is what both functions used before ``over`` existed."""
    rational = over_field(integral)

    assert peel(integral, integral.extend(2), budget=5).domain == sp.ZZ
    assert peel(rational, rational.extend(2), budget=5).domain == sp.QQ
    assert search(integral, integral.extend(2), {}, budget=5).domain == sp.ZZ


def test_with_over_the_ring_is_the_one_named(integral: PolynomialMap) -> None:
    """DOM-1, and DOM-4: the outcome carries it either way."""
    peeled = peel(integral, integral.extend(2), budget=5, over=sp.ZZ)
    searched = search(integral, integral.extend(2), {}, budget=5, over=sp.ZZ)

    assert peeled.domain == sp.ZZ
    assert searched.domain == sp.ZZ


def test_an_endpoint_over_another_ring_is_an_error(integral: PolynomialMap) -> None:
    """DOM-2, for both endpoints and both searches.

    The caller has described two spaces, and no search over either answers what
    they asked. Before ``over`` this was an exhausted space: true about a space
    nobody meant, and the defect that cost a release.
    """
    rational = over_field(integral)

    for call in (
        lambda: peel(rational, integral.extend(2), budget=5, over=sp.ZZ),
        lambda: search(rational, integral.extend(2), {}, budget=5, over=sp.ZZ),
        lambda: peel(integral, over_field(integral.extend(2)), budget=5, over=sp.ZZ),
        lambda: search(
            integral, over_field(integral.extend(2)), {}, budget=5, over=sp.ZZ
        ),
    ):
        with pytest.raises(VerificationError) as failure:
            call()

        assert failure.value.obligation == "DOM-2"
        assert "ZZ" in failure.value.message
        assert "QQ" in failure.value.message


def test_the_message_names_the_argument(integral: PolynomialMap) -> None:
    """Both rings side by side, and which argument brought the other one.

    A message saying only that the rings differ leaves the caller to work out
    which of their two maps was the odd one.
    """
    with pytest.raises(VerificationError) as source_failure:
        peel(over_field(integral), integral.extend(2), budget=5, over=sp.ZZ)

    with pytest.raises(VerificationError) as target_failure:
        peel(integral, over_field(integral.extend(2)), budget=5, over=sp.ZZ)

    assert "source" in source_failure.value.message
    assert "target" in target_failure.value.message


def test_a_pool_value_outside_the_ring_is_an_error(integral: PolynomialMap) -> None:
    """DOM-2 for the third narrowing, and without ``over`` as well.

    ``1/2 * y**2`` over ``ZZ`` is not a constant that fails to convert but a
    polynomial that does not exist there. It used to yield no candidate and say
    nothing, exactly as a value describing nothing would.

    Unconditional, unlike the endpoints. Two endpoints over different rings
    each describe a map and REV-11 answers the pair; a value with coefficients
    outside the domain describes nothing.
    """
    bad = {sp.Symbol("u"): sp.Rational(1, 2) * y**2}

    for named in ({"over": sp.ZZ}, {}):
        with pytest.raises(VerificationError) as failure:
            search(integral, integral.extend(2), bad, budget=5, **named)

        assert failure.value.obligation == "DOM-2"
        assert "u" in failure.value.message


def test_the_enumerator_refuses_the_same_value(integral: PolynomialMap) -> None:
    """The precedent of 0.4.0rc9, applied to the pool.

    ``enumerate_candidates`` is public. ``selection_limit`` was checked in
    ``search`` and not here until an audit found it; the pool value was the
    same shape of gap.
    """
    with pytest.raises(VerificationError) as failure:
        enumerate_candidates(integral, [sp.Rational(1, 2) * y**2])

    assert failure.value.obligation == "DOM-2"


def test_a_value_naming_a_later_coordinate_stays_admissible(
    integral: PolynomialMap,
) -> None:
    """The negative control, and the case the first version of this refused.

    ``w6 = w1 x`` becomes convertible only once ``w1`` exists as a generator,
    and a value like it yielding no candidate is how the dependency between
    carriers falls out by itself. What is checked are the coefficients and not
    the generators.
    """
    later = sp.Symbol("z")

    assert enumerate_candidates(integral, [y * later]) == ()
    assert search(integral, integral.extend(2), {sp.Symbol("u"): y * later}, budget=5)


def test_the_pool_is_checked_before_the_endpoints_answer(
    integral: PolynomialMap,
) -> None:
    """Otherwise the check moves with the endpoints, which is the rc11 finding.

    Equal endpoints are answered by ``settled`` without a walk, so the search
    never reaches the enumerator. A bad pool has to raise there too, or the
    same call is valid or invalid depending on what it was asked to search.
    """
    with pytest.raises(VerificationError) as failure:
        search(integral, integral, {sp.Symbol("u"): sp.Rational(1, 2) * y**2})

    assert failure.value.obligation == "DOM-2"


def test_a_pool_value_inside_the_ring_is_not(integral: PolynomialMap) -> None:
    """The negative control. Otherwise the check above refuses every pool."""
    outcome = search(
        integral,
        integral.extend(2),
        {sp.Symbol("u"): y**2},
        budget=5,
        over=sp.ZZ,
    )

    assert outcome.domain == sp.ZZ


@pytest.mark.parametrize(
    ("label", "domain", "value"),
    [
        ("ZZ[T]", sp.ZZ[sp.Symbol("T")], sp.Symbol("T") * y),
        ("ZZ(T)", sp.ZZ.frac_field(sp.Symbol("T")), sp.Symbol("T") * y),
        (
            "QQ[X3][S]",
            sp.QQ[sp.Symbol("X3")][sp.Symbol("S")],
            sp.Symbol("S") * sp.Symbol("X3") * y,
        ),
    ],
)
def test_a_parameter_of_the_domain_is_not_a_later_coordinate(
    label: str,
    domain: object,
    value: sp.Expr,
) -> None:
    """The regression an external audit of work package 7 built.

    ``polynomials_over`` widens the ring by whatever symbols a pool value
    mentions, so that a value naming a coordinate the source does not have yet
    stays admissible. An indeterminate of the coefficient domain is neither a
    generator nor a later coordinate, and widening by it asks SymPy for
    ``ZZ[T][x, y, T]``, which raises ``GeneratorsError``.

    This worked in 0.4 and DOM-1 promises it keeps working. The nested domain
    is here because the domains nest: reading ``domain.symbols`` alone finds
    ``S`` and misses ``X3``.

    ``label`` appears in the test name only, so that a failure says which
    domain broke.
    """
    ring = sp.polys.rings.ring([x, y], domain)[0]
    source = PolynomialMap.from_ring(
        ring, (ring.from_expr(x) + ring.from_expr(y) ** 3, ring.from_expr(y))
    )
    pool = {sp.Symbol("u"): value}

    assert enumerate_candidates(source, [value]) is not None
    assert search(source, source.extend(2), pool, budget=5).exhausted
    assert (
        search(source, source.extend(2), pool, budget=5, over=domain).domain == domain
    )


def test_over_must_be_a_domain() -> None:
    """A wrong type is a wrong argument and not a contradiction.

    The error table promises ``TypeError`` for an argument of the wrong type.
    ``over="ZZ"`` gave a ``VerificationError`` saying the source lies over
    ``ZZ`` and the search was asked for ``ZZ``, because the string prints the
    same. An external audit read that message.
    """
    source = PolynomialMap((x, y), (x + y**3, y))

    for wrong in ("ZZ", 17, [sp.ZZ]):
        for call in (
            lambda w=wrong: peel(source, source.extend(2), budget=5, over=w),
            lambda w=wrong: search(source, source.extend(2), {}, budget=5, over=w),
        ):
            with pytest.raises(TypeError, match="must be a SymPy domain"):
                call()


def test_the_outcome_does_not_share_its_domain(integral: PolynomialMap) -> None:
    """DOM-4 and RC-6 together: a domain is not a value object.

    Its ``gens`` are ``PolyElement``, so mutable dicts. A caller holding the
    one an outcome carries could change what a finished result reports.
    Measured by an external audit: clearing ``over.gens[0]`` turned the
    generators of an already returned outcome from ``(T,)`` into ``(0,)``.

    Both paths are checked, the one that takes ``over`` and the one that reads
    the source, because the default was the same object as well.
    """
    parameter = sp.Symbol("T")
    over = sp.ZZ[parameter]
    ring = sp.polys.rings.ring([x, y], over)[0]
    source = PolynomialMap.from_ring(
        ring, (ring.from_expr(x) + ring.from_expr(y) ** 3, ring.from_expr(y))
    )

    named = peel(source, source.extend(2), budget=5, over=over)
    before = str(named.domain.gens)

    assert named.domain is not over
    assert named.domain == over

    over.gens[0].clear()

    assert str(over.gens) != before
    assert str(named.domain.gens) == before


def test_the_default_domain_was_never_shared(integral: PolynomialMap) -> None:
    """And so it is not cloned again, which a first draft did.

    ``PolynomialMap.ring`` hands out a fresh view on every call and clones the
    domain with it, so the path that reads the source shares nothing. A clone
    there would be a defence against nothing. Measured, and recorded here
    because the assertion that looked like it checked this could not fail:
    ``source.ring.domain`` is a different object every time it is asked for.
    """
    parameter = sp.Symbol("T")
    ring = sp.polys.rings.ring([x, y], sp.ZZ[parameter])[0]
    source = PolynomialMap.from_ring(
        ring, (ring.from_expr(x) + ring.from_expr(y) ** 3, ring.from_expr(y))
    )
    view = source.ring.domain
    outcome = peel(source, source.extend(2), budget=5)
    before = str(outcome.domain.gens)

    assert source.ring.domain is not view

    view.gens[0].clear()

    assert str(outcome.domain.gens) == before


def test_without_over_the_endpoints_keep_the_answer_of_rev_eleven(
    integral: PolynomialMap,
) -> None:
    """DOM-3. A call written against 0.4 keeps its meaning.

    The asymmetry is deliberate. REV-11 is about what a pair of endpoints can
    be; DOM-2 is about a caller contradicting themselves, which cannot arise
    without ``over``.
    """
    outcome = peel(over_field(integral), integral.extend(2), budget=5)

    assert outcome.reduction is None
    assert outcome.exhausted
    assert outcome.examined == 0
    assert outcome.domain == sp.QQ


def test_the_ring_is_checked_before_the_endpoints_answer(
    integral: PolynomialMap,
) -> None:
    """Whether a call is valid must not depend on how far the search gets.

    Equal endpoints are answered by ``settled`` without a walk. A ring named
    against them still has to be checked, or the same wrong ``over`` would
    raise on one pair and pass on another.
    """
    rational = over_field(integral)

    with pytest.raises(VerificationError) as failure:
        peel(rational, rational, budget=5, over=sp.ZZ)

    assert failure.value.obligation == "DOM-2"


def test_a_found_chain_carries_the_ring(integral: PolynomialMap) -> None:
    """DOM-4 on a result rather than on a non-answer."""
    rational = over_field(integral)
    target = BCWStep.build(
        rational, 0, Fresh(y, sp.Symbol("u")), Fresh(y**2, sp.Symbol("v")), 1
    ).target
    outcome = peel(rational, target, budget=200)

    assert outcome.reduction is not None
    assert outcome.domain == sp.QQ


def test_the_outcome_reports_its_ring_when_printed() -> None:
    """DOM-4, in the repr, which the generated one cannot show.

    ``_domain`` is kept out of the generated ``repr`` so that the name a caller
    sees is the property, so the ring is put back by hand. An audit of
    ``0.5.0rc1`` found the underscore in the public signature; taking it out
    took the ring out of the repr with it.
    """
    source = PolynomialMap((x, y), (x + y**3, y))
    printed = repr(peel(source, source.extend(2), budget=5))

    assert printed.startswith("PeelOutcome(reduction=")
    assert "domain=QQ" in printed or "domain=ZZ" in printed
    assert "_domain" not in printed
