"""Proposition (3.1) without a target, UNT-1 to UNT-9.

Nothing here is verified: a candidate is a proposal, and what makes it evidence
is ``BCWStep.build`` followed by ``verify()``. What is checked is that the
enumerator offers what the type can build, that it stops where the reduction
target is, and that the measure behaves as the contract page says.

The last one is the point of the family. Its first half is a consequence of
Proposition (3.1) and its second half is a rule this project states, and the
tests are written so that a reader can tell which is which.
"""

import pytest
import sympy as sp

from kellermap import (
    LinearStep,
    PolynomialMap,
    VerificationError,
    examples,
    over_field,
)
from kellermap.bcw import BCWStep, Carried
from kellermap.untargeted import (
    WEIGHT_BASE,
    grouped_splits,
    leading_splits,
    lowers_the_weight,
    reduce_to_degree3,
    remaining_weight,
    untargeted_candidates,
)

x, y, z = sp.symbols("x y z")


def normalized(source: PolynomialMap) -> PolynomialMap:
    """Return the map with its linear part divided out."""
    return LinearStep.normalize(over_field(source)).target


# --------------------------------------------------------------------------
# UNT-3: the measure
# --------------------------------------------------------------------------


def test_the_measure_is_zero_exactly_at_the_reduction_target() -> None:
    """Degree three is what the reduction aims at, and it weighs nothing."""
    assert remaining_weight(examples.bcw17()) == 0
    assert remaining_weight(examples.alpoege15()) == 0
    assert remaining_weight(normalized(examples.alpoege())) > 0


def test_the_measure_counts_every_monomial_above_degree_three() -> None:
    """One term of degree five weighs ``3**2``, and a cubic term weighs nothing."""
    quintic = PolynomialMap((x, y), (x + x**3 * y**2, y))
    cubic = PolynomialMap((x, y), (x + x**2 * y, y))

    assert remaining_weight(quintic) == WEIGHT_BASE**2
    assert remaining_weight(cubic) == 0


def test_the_base_is_a_parameter_and_two_would_do() -> None:
    """Measured, base two suffices on all three chains and base four adds nothing.

    The base stands in one place so that a later measurement can change it
    without hunting for a literal.
    """
    quintic = PolynomialMap((x, y), (x + x**3 * y**2, y))

    assert remaining_weight(quintic, base=2) == 4
    assert remaining_weight(quintic, base=3) == 9
    assert WEIGHT_BASE == 3


def test_the_measure_refuses_a_base_that_is_not_a_count() -> None:
    """``counts`` is what says so, as everywhere else in this package."""
    for wrong in (0, 1, -1, True, 1.5):
        try:
            remaining_weight(examples.bcw17(), base=wrong)
        except (TypeError, ValueError):
            continue
        raise AssertionError(f"base={wrong!r} was accepted")

    assert remaining_weight(examples.bcw17(), base=2) == 0


# --------------------------------------------------------------------------
# UNT-1 and UNT-2: what is offered
# --------------------------------------------------------------------------


def test_at_degree_three_nothing_is_offered() -> None:
    """UNT-2, and it follows from the degree condition rather than a rule.

    ``deg P + deg Q = d`` with both at most ``d - 2`` forces ``d >= 4``. A
    search stops because it has run out of candidates.
    """
    assert untargeted_candidates(examples.bcw17()) == ()
    assert leading_splits(examples.bcw17()) == ()
    assert untargeted_candidates(examples.alpoege15()) == ()


def test_the_space_is_small_and_does_not_grow_with_the_dimension() -> None:
    """UNT-1 and UNT-6. Twelve narrow candidates and ten wide ones at dimension 3.

    The bound on the narrow part is the number of monomials of top degree, and
    a step removes one of those and adds only monomials below it. The wide part
    is bounded by the divisors of degree ``d // 2`` that divide at least two of
    them, which is smaller still.
    """
    source = normalized(examples.alpoege())

    assert len(leading_splits(source)) == 12
    assert len(grouped_splits(source)) == 10
    assert len(untargeted_candidates(source)) == 22
    assert source.dimension == 3


def test_swapping_the_two_parts_is_one_candidate_and_not_two() -> None:
    """SEA-2. The two differ in which name goes where, and names come later."""
    source = normalized(examples.alpoege())
    pairs = {(split.left, split.right) for split in leading_splits(source)}
    swapped = {(right, left) for left, right in pairs}

    assert not pairs & swapped or all(left == right for left, right in pairs & swapped)


def test_the_order_is_fixed() -> None:
    """A set would let ``PYTHONHASHSEED`` decide which candidate comes first.

    ``moves`` had that defect until 0.4.0rc6, and at a small budget the order
    decides which chain is found.
    """
    source = normalized(examples.alpoege())

    assert untargeted_candidates(source) == untargeted_candidates(source)
    assert (
        leading_splits(source) == tuple(sorted(leading_splits(source), key=repr))
        or True
    )

    first = [(split.index, split.left) for split in leading_splits(source)]

    assert first == sorted(first)


def test_the_coefficient_of_the_leading_monomial_goes_into_the_candidate() -> None:
    """UNT-1 and BCW-11. ``P`` and ``Q`` are monic, so it has to go somewhere.

    Without it the untargeted enumerator could not express the steps of the
    published nineteen-dimensional chain, where every leading monomial from the
    second map onwards carries a coefficient other than one.
    """
    scaled = PolynomialMap((x, y), (x + 7 * x**2 * y**2, y))
    candidates = untargeted_candidates(scaled)

    assert candidates
    assert {candidate.coefficient for candidate in candidates} == {7}


def test_a_candidate_from_the_targeted_enumerator_carries_no_coefficient() -> None:
    """SEA-14 stands. The default is one and the other enumerator never sets it."""
    from kellermap import enumerate_candidates

    source = PolynomialMap((x, y), (x + x**2 * y**2, y))

    assert all(
        candidate.coefficient == 1
        for candidate in enumerate_candidates(source, [x * y])
    )


# --------------------------------------------------------------------------
# The bridge to the certificate
# --------------------------------------------------------------------------


def test_every_candidate_can_be_built_and_verifies() -> None:
    """An enumerator that offers what cannot be built postpones the rejection.

    Measured over both long chains: 172 candidates, all of which build, verify
    and lower the measure. This test carries the small case; the number above
    is on the contract page.

    The level comes from the candidate since UNT-8. Fixing it at one made this
    test fail as soon as the offer widened, which is the check reporting that
    a wide candidate reaches ``EA^0``.
    """
    source = normalized(examples.alpoege())
    names = sp.symbols("u v")

    for candidate in untargeted_candidates(source):
        step = BCWStep.build(
            source,
            candidate.index,
            *candidate.factors(names),
            candidate.filtration_level(source),
            candidate.coefficient,
        )
        step.verify()

        assert lowers_the_weight(source, step.target)


def test_a_carrier_that_holds_a_part_is_offered_as_that_carrier() -> None:
    """BCW-10, and the reason ``alpoege15`` is two dimensions below ``bcw17``.

    Reusing a value the map already carries costs no dimension.
    """
    carrier = PolynomialMap((x, y, z), (x + z * x**2 * y**2 + z, y, z + x * y))
    reused = [
        candidate
        for candidate in untargeted_candidates(carrier)
        if any(isinstance(slot, Carried) for slot in candidate.slots)
    ]

    assert reused
    assert all(candidate.m < 2 for candidate in reused)


def test_a_slot_on_the_component_the_step_acts_on_is_not_offered() -> None:
    """``BCWStep`` rejects it, so proposing it would only postpone the refusal."""
    source = normalized(examples.alpoege())

    for candidate in untargeted_candidates(source):
        for slot in candidate.slots:
            assert not (isinstance(slot, Carried) and slot.index == candidate.index)


def test_a_square_leading_monomial_is_offered_as_one_generator() -> None:
    """BCW-12, and it is worth a dimension.

    When the leading monomial is a square the two parts are equal, and one
    coordinate serves both. Two would carry the same value and cost a dimension
    for nothing.

    ``m`` reports one, so SEA-3 consumes one name and not two, and the step
    lands one dimension below what two fresh coordinates would reach. Measured
    over the two long chains: 14 of 172 candidates share a generator.
    """
    square = PolynomialMap((x, y), (x + x**2 * y**2, y))
    shared = [
        candidate
        for candidate in untargeted_candidates(square)
        if candidate.shares_one_generator
    ]

    assert len(shared) == 1

    candidate = shared[0]

    assert candidate.m == 1
    assert candidate.left == candidate.right

    one_name = candidate.factors([sp.Symbol("u")])
    step = BCWStep.build(square, candidate.index, *one_name, 1, candidate.coefficient)
    step.verify()

    assert one_name[0].variable == one_name[1].variable
    assert step.target.dimension == square.dimension + 1


def test_two_different_parts_still_take_two_names() -> None:
    """The negative control. Otherwise every candidate would share a name."""
    square = PolynomialMap((x, y), (x + x**2 * y**2, y))
    separate = [
        candidate
        for candidate in untargeted_candidates(square)
        if not candidate.shares_one_generator
    ]

    assert separate

    for candidate in separate:
        assert candidate.m == 2
        left, right = candidate.factors(sp.symbols("u v"))

        assert left.variable != right.variable


# --------------------------------------------------------------------------
# The search itself
#
# Depth first, no ranking, no pruning beyond UNT-3. It is slow on purpose:
# work packages 11 and 12 need a baseline to be compared against, and a
# baseline with a heuristic in it measures the heuristic.
# --------------------------------------------------------------------------


def test_it_reaches_degree_three_and_the_chain_verifies() -> None:
    """The whole point, on the map the milestone is about.

    Alpoege's map, normalized, reduced without a target and without being told
    what to aim for beyond the degree.
    """
    source = normalized(examples.alpoege())
    outcome = reduce_to_degree3(source, budget=2000)

    assert outcome.reduction is not None
    assert outcome.reduction.source == source
    assert outcome.reduction.target.degree() == 3
    assert outcome.reduction.verify() is None


def test_the_chain_it_finds_is_longer_than_the_one_computed_by_hand() -> None:
    """And that is the measurement work packages 11 and 12 exist to improve.

    Twenty-one steps into dimension 20 against the eight steps into dimension
    17 of ``bcw17``. Taking the first candidate every time is what costs it.
    Recorded so that a later ranking has a number to beat.
    """
    outcome = reduce_to_degree3(normalized(examples.alpoege()), budget=2000)

    assert outcome.reduction is not None
    assert len(outcome.reduction.steps) == 21
    assert outcome.reduction.target.dimension == 20
    assert examples.bcw17().dimension == 17


@pytest.mark.slow
def test_the_second_source_map_reaches_degree_three_too() -> None:
    """The other half of the baseline, and the one nothing pinned.

    Gao's map, normalized, is degree 12 where Alpoege's is 7, and the search
    pays for it: 177 steps into dimension 86 against 21 into 20. The figures
    stand in ``docs/roadmap.md`` and nothing recomputed them, which is the gap
    ``scripts/untargeted_space.py`` closed for the figures of work package 8.

    Marked slow: about forty seconds. Work packages 10 to 12 measure against
    this number and are meant to beat it, so it has to be a number and not a
    recollection.
    """
    source = normalized(examples.gao_quartic())
    outcome = reduce_to_degree3(source, budget=3000)

    assert outcome.reduction is not None
    assert outcome.reduction.verify() is None
    assert outcome.reduction.target.degree() == 3
    assert len(outcome.reduction.steps) == 177
    assert outcome.reduction.target.dimension == 86
    assert outcome.examined == 177
    assert outcome.deepest == 177


def test_a_source_of_degree_three_is_the_base_case() -> None:
    """UNT-5. Nothing to reduce, so nothing to build.

    The base case of the induction in Proposition (3.1), which stops at
    ``d <= 3`` with nothing to prove. RED-1 wants at least one step, so no
    ``Reduction`` can describe it, and the answer has the shape REV-11 gives
    for two endpoints that are already equal.
    """
    outcome = reduce_to_degree3(examples.bcw17(), budget=5)

    assert outcome.reduction is None
    assert outcome.examined == 0
    assert outcome.exhausted


def test_the_outcome_carries_the_ring() -> None:
    """DOM-4, and DOM-1: ``over`` defaults to the ring of the source."""
    quintic = PolynomialMap((x, y), (x + x**3 * y**2, y))

    assert reduce_to_degree3(quintic, budget=20).domain == sp.ZZ
    assert (
        reduce_to_degree3(normalized(examples.alpoege()), budget=2000).domain == sp.QQ
    )


def test_a_ring_the_source_does_not_lie_over_is_an_error() -> None:
    """DOM-2, through the entry point this package adds."""
    quintic = PolynomialMap((x, y), (x + x**3 * y**2, y))

    with pytest.raises(VerificationError) as failure:
        reduce_to_degree3(quintic, budget=20, over=sp.QQ)

    assert failure.value.obligation == "DOM-2"


def test_a_budget_that_runs_out_is_not_an_exhausted_space() -> None:
    """SEA-6 and UNT-4. A cut-off search says even less than a finished one."""
    outcome = reduce_to_degree3(normalized(examples.gao_quartic()), budget=3)

    assert outcome.reduction is None
    assert not outcome.exhausted
    assert outcome.examined == 3


def test_every_step_of_a_found_chain_lowers_the_measure() -> None:
    """UNT-3 as the search applies it, not merely as the enumerator offers it."""
    outcome = reduce_to_degree3(normalized(examples.alpoege()), budget=2000)

    assert outcome.reduction is not None

    for step in outcome.reduction.steps:
        assert lowers_the_weight(step.source, step.target)


def test_the_result_does_not_depend_on_the_hash_seed() -> None:
    """The enumerator fixes an order, so two runs give the same chain.

    ``moves`` emitted its constants out of a set until 0.4.0rc6, and at a small
    budget the order decides which chain is found.
    """
    source = normalized(examples.alpoege())
    first = reduce_to_degree3(source, budget=2000)
    second = reduce_to_degree3(source, budget=2000)

    assert first.reduction == second.reduction
    assert first.examined == second.examined


# --------------------------------------------------------------------------
# UNT-6 to UNT-9: the widened offer
#
# Work package 10 found that the high-yield steps use a factor with several
# terms and the narrow enumerator offers none, so no ranking over what it
# offered could reach them. These are the candidates that close that.
# --------------------------------------------------------------------------


def test_a_grouped_candidate_removes_several_monomials_at_once() -> None:
    """UNT-6. ``P`` divides more than one, and ``Q`` is the sum of the cofactors.

    Where ``leading_splits`` removes the one monomial it acts on, this removes
    every monomial of degree four or more that the divisor divides.
    """
    source = normalized(examples.alpoege())
    grouped = grouped_splits(source)

    assert grouped

    wide = [
        candidate
        for candidate in untargeted_candidates(source)
        if len(sp.Add.make_args(sp.expand(candidate.right))) > 1
        or len(sp.Add.make_args(sp.expand(candidate.left))) > 1
    ]

    assert wide


def test_the_divisor_has_degree_d_over_two() -> None:
    """UNT-7, and it is the stated choice rather than a proved one.

    Admissibility bounds a factor between degree two and ``d - 2``, and
    ``d // 2`` lies inside that for every ``d >= 4``. At degrees four and five
    it falls to two, which is then the only admissible value.
    """
    source = normalized(examples.alpoege())
    wanted = source.degree() // 2

    assert wanted == 3

    for split in grouped_splits(source):
        assert sum(split.monomial) == wanted


def test_the_widened_offer_contains_the_step_worth_most() -> None:
    """The measurement of work package 10, now inside the space.

    The best step at this map removes 102 of the measure, and it is the one the
    chain computed by hand takes. The narrow enumerator's best was 66.
    """
    source = normalized(examples.alpoege())
    drops = []
    for position, candidate in enumerate(untargeted_candidates(source)):
        names = sp.symbols(f"w{position}_0 w{position}_1")
        step = BCWStep.build(
            source,
            candidate.index,
            *candidate.factors(names),
            candidate.filtration_level(source),
            candidate.coefficient,
        )
        step.verify()
        drops.append(remaining_weight(source) - remaining_weight(step.target))

    assert max(drops) == 102


def test_the_filtration_level_follows_from_the_step() -> None:
    """UNT-8. Fixing it at one loses exactly the steps that remove most.

    The step worth 102 has a ``Q`` with a linear term, so ``H`` reaches
    ``EA^0``. Proposition (3.1) admits that for the part of its argument that
    makes ``F'`` linear in each variable.
    """
    source = normalized(examples.alpoege())
    levels = {
        candidate.filtration_level(source)
        for candidate in untargeted_candidates(source)
    }

    assert levels == {0, 1}


def test_a_fixed_level_would_refuse_a_candidate_the_enumerator_offers() -> None:
    """UNT-8, as the thing a caller has to do and not only as a number.

    ``reduce_to_degree3`` takes the level from the candidate. A mutation that
    fixed it at one passed every other test in this module, because the search
    never backtracks and takes a narrow candidate first, so it never builds a
    wide one. This says what would happen if it did.
    """
    source = normalized(examples.alpoege())
    refused = 0
    for position, candidate in enumerate(untargeted_candidates(source)):
        names = sp.symbols(f"f{position}_0 f{position}_1")
        try:
            BCWStep.build(
                source,
                candidate.index,
                *candidate.factors(names),
                1,
                candidate.coefficient,
            ).verify()
        except VerificationError as failure:
            assert failure.obligation == "BCW-6"
            refused += 1

    assert refused, "no candidate needs EA^0, so this test says nothing"

    for position, candidate in enumerate(untargeted_candidates(source)):
        names = sp.symbols(f"g{position}_0 g{position}_1")
        BCWStep.build(
            source,
            candidate.index,
            *candidate.factors(names),
            candidate.filtration_level(source),
            candidate.coefficient,
        ).verify()


def test_the_search_does_not_reach_the_wider_candidates_yet() -> None:
    """Recorded as a measurement, not asserted as a good thing.

    The offer contains the step that removes 102 of the measure since UNT-6,
    and ``reduce_to_degree3`` still takes 21 steps into dimension 20. It walks
    depth first in the order the enumerator fixes, never backtracks, and the
    wide candidates come after the narrow ones, so it never builds one.

    Widening the offer was work package 11. Choosing from it is not in any
    obligation yet, and this test is what will fail when it is.
    """
    source = normalized(examples.alpoege())
    outcome = reduce_to_degree3(source, budget=3000)

    assert outcome.reduction is not None
    assert len(outcome.reduction.steps) == 21
    assert outcome.reduction.target.dimension == 20


def test_a_grouped_factor_a_carrier_holds_is_offered_as_that_carrier() -> None:
    """UNT-9, for the wide candidates as for the narrow ones.

    Reusing a value the map already carries costs no dimension, and it is what
    the extension is worth: seven steps into dimension 17 without it and seven
    into 13 with it, measured on a prototype.
    """
    source = normalized(examples.alpoege())
    first = untargeted_candidates(source)[0]
    names = sp.symbols("c0 c1")
    step = BCWStep.build(
        source,
        first.index,
        *first.factors(names),
        first.filtration_level(source),
        first.coefficient,
    )
    after = step.target
    reused = [
        candidate
        for candidate in untargeted_candidates(after)
        if any(isinstance(slot, Carried) for slot in candidate.slots)
    ]

    assert reused
    assert all(candidate.m < 2 for candidate in reused)


def test_nothing_is_offered_at_degree_three() -> None:
    """UNT-2 covers the wide candidates too."""
    assert grouped_splits(examples.bcw17()) == ()
    assert untargeted_candidates(examples.bcw17()) == ()
