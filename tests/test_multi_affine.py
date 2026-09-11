"""The multi-affine refinement of Theorem 2.1(b), UNT-12, HOM-11 and HOM-12.

Two things are checked here and they are different in kind.

UNT-12 is a walk, and nothing it proposes is evidence until ``BCWStep.build``
and ``verify()`` have run. What is checked is that every step it offers lowers
its measure, that the shapes it must not produce are absent from what it
builds, and that it arrives.

HOM-11 and HOM-12 are obligations of a step, and both are unreachable after
HOM-1: a target equal to the formula's output satisfies them. So the negative
controls here are on ``squared_terms``, which is what both read, and not on
``verify()``. A test that forced a step into a state HOM-1 rules out would be
the kind ``AGENTS.md`` forbids.
"""

import pytest
import sympy as sp

from kellermap import (
    LinearStep,
    PolynomialMap,
    Reduction,
    examples,
    over_field,
    peel,
    reduce_to_degree3,
    reduce_to_multi_affine,
    remaining_excess,
)
from kellermap.bcw import BCWStep
from kellermap.bcw.grading import squared_terms
from kellermap.bcw.homogenization import HomogenizationStep
from kellermap.bcw.step import Carried, Fresh
from kellermap.bcw.unipotent import UnipotentStep
from kellermap.context import ReductionContext
from kellermap.untargeted import EXCESS_BASE, multi_affine_steps

x, y, z, w = sp.symbols("x y z w")


def cube() -> PolynomialMap:
    """The smallest case of the refinement, and the one the roadmap names."""
    return over_field(PolynomialMap((x, y), (x + y**3, y)))


def square() -> PolynomialMap:
    """A bare square, where both factors are the same variable."""
    return over_field(PolynomialMap((x, y), (x + y**2, y)))


# ----------------------------------------------------------------------
# squared_terms, which HOM-12 and UNT-12 both read
# ----------------------------------------------------------------------


def test_a_multi_affine_map_has_no_squared_term() -> None:
    """The predicate is empty exactly where the property holds."""
    flat = PolynomialMap((x, y, z), (x + y * z, y, z))

    assert squared_terms(flat) == ()


def test_a_squared_term_is_reported_with_its_component() -> None:
    """One pair per term, the component index and the exponent vector."""
    assert squared_terms(cube()) == ((0, (0, 3)),)


def test_the_exempt_variable_does_not_count() -> None:
    """HOM-12 exempts the parameter, which is what ``exempt`` is for."""
    parameterised = PolynomialMap((x, y), (x + y**2, y))

    assert squared_terms(parameterised, exempt=(y,)) == ()
    assert squared_terms(parameterised) == ((0, (0, 2)),)


def test_a_bought_coordinate_is_not_exempt() -> None:
    """Theorem 2.1(b) exempts ``T`` and nothing else.

    The negative control for HOM-12. A map that is multi-affine in the
    variables a source began with and squares a coordinate an earlier stage
    bought satisfies the reading this project carried until 0.7 and not the
    theorem. Exempting only the last variable still reports it.
    """
    bought = PolynomialMap((x, y, z), (x + y * z**2, y, z))

    assert squared_terms(bought, exempt=(x,)) == ((0, (0, 1, 2)),)


# ----------------------------------------------------------------------
# The measure, UNT-12
# ----------------------------------------------------------------------


def test_the_measure_is_zero_exactly_when_the_map_is_multi_affine() -> None:
    assert remaining_excess(PolynomialMap((x, y, z), (x + y * z, y, z))) == 0
    assert remaining_excess(cube()) == EXCESS_BASE**2
    assert remaining_excess(square()) == EXCESS_BASE


@pytest.mark.parametrize("base", [0, 1, 2])
def test_a_base_below_three_is_refused(base: int) -> None:
    """The measure has to fall at every step, and that is the whole reason.

    A step puts at most two squaring terms in place of one, each with an excess
    at least one lower, so the measure falls only while
    ``base ** e > 2 * base ** (e - 1)``, which is ``base > 2``.

    Being zero exactly on a multi-affine map is not the reason, and this
    docstring said it was. That holds at one and at two, where every term is
    positive, and fails only at zero, which is the case an audit of
    ``0.7.0rc1`` reached. An audit of ``0.7.0rc3`` found the wrong reason still
    standing here and in ``docs/api.md`` after the code and the contract page
    had been corrected.
    """
    with pytest.raises(ValueError, match="at least 3"):
        remaining_excess(cube(), base)


@pytest.mark.parametrize("base", [True, 1.5])
def test_a_base_that_is_not_an_integer_is_refused(base: object) -> None:
    """The return type says ``int``, and ``1.5`` made it a float."""
    with pytest.raises(TypeError):
        remaining_excess(cube(), base)  # type: ignore[arg-type]


def test_the_exempt_variables_may_be_any_iterable() -> None:
    """A one-shot iterable is empty from the second generator onward.

    ``set(exempt)`` stood inside the comprehension and was rebuilt per
    generator, so an audit of ``0.7.0rc1`` passed a generator and every
    variable counted. The signature promises ``Iterable``.
    """
    parameterised = PolynomialMap((x, y), (x + y**2, y))

    assert squared_terms(parameterised, exempt=(y,)) == ()
    assert squared_terms(parameterised, exempt=[y]) == ()
    assert squared_terms(parameterised, exempt=(v for v in (y,))) == ()


def test_the_count_of_squared_terms_would_not_serve_as_the_measure() -> None:
    """The first step on ``y**3`` replaces one squared monomial by two.

    This is why the measure weighs the excess instead of counting the terms,
    and it is the case the contract page names under UNT-12.
    """
    source = cube()
    first = multi_affine_steps(source, ReductionContext())[0].target

    assert len(squared_terms(source)) == 1
    assert len(squared_terms(first)) == 2
    assert remaining_excess(first) < remaining_excess(source)


# ----------------------------------------------------------------------
# What the walk offers
# ----------------------------------------------------------------------


def test_every_step_offered_lowers_the_measure() -> None:
    """UNT-12 where the measure is applied, over both source maps."""
    for source in (cube(), over_field(examples.alpoege13())):
        before = remaining_excess(source)
        offered = multi_affine_steps(source, ReductionContext())

        assert offered
        for step in offered:
            assert remaining_excess(step.target) < before


def test_a_split_that_moves_the_square_is_not_offered() -> None:
    """``x**2 y`` splits two ways and only one of them clears the square.

    ``y * x**2`` puts the square into a fresh component and into the residue,
    so the measure does not fall and the split is left out. ``x * (x y)``
    clears it. Both are enumerated; one survives.
    """
    source = over_field(PolynomialMap((x, y), (x + x**2 * y, y)))
    offered = multi_affine_steps(source, ReductionContext())

    assert len(offered) == 1
    assert remaining_excess(offered[0].target) == 0


def test_no_step_squares_a_coordinate_against_itself() -> None:
    """The two shapes UNT-12 cannot use, over a whole chain.

    A repeated fresh slot, BCW-12, and two carried slots on one coordinate
    both give ``X_u ** 2``. Neither is withdrawn as an obligation; a
    multi-affine walk does not offer them, and this is what says so.
    """
    outcome = reduce_to_multi_affine(over_field(examples.alpoege13()))
    assert outcome.reduction is not None

    for step in outcome.reduction.steps:
        assert remaining_excess(step.target) < remaining_excess(step.source)


def test_two_equal_factors_take_two_coordinates() -> None:
    """``y * y`` with no carrier needs two fresh coordinates and not one.

    ``Candidate`` would share the generator by BCW-12 and produce ``X_u ** 2``,
    which is why the walk builds its factors itself.
    """
    outcome = reduce_to_multi_affine(square())
    assert outcome.reduction is not None

    step = outcome.reduction.steps[0]
    assert step.source.dimension + 2 == step.target.dimension
    assert squared_terms(step.target) == ()


def test_a_second_carrier_of_a_value_is_offered_when_the_first_will_not_do() -> None:
    """Two coordinates can hold one value and the split decides which serves.

    After two steps on ``(x + y**3, y)`` the coordinates two and four both
    hold ``y``. The third step needs one of them against a factor containing
    the other, so exactly one of the two works. Keeping only the first made
    the walk buy a coordinate it already had.
    """
    outcome = reduce_to_multi_affine(cube())
    assert outcome.reduction is not None

    middle = outcome.reduction.steps[1].target
    holding = [
        index
        for index in middle.carrier_indices
        if sp.expand(middle.components[index] - middle.variables[index]) == y
    ]

    assert len(holding) == 2
    assert outcome.reduction.steps[2].target.dimension == middle.dimension + 1


def test_one_factorization_can_yield_two_candidates() -> None:
    """UNT-12 counts a candidate per factorization *and* slot assignment.

    It said per factorization until ``0.7.0rc3``, which was the count before
    the walk stopped choosing a slot assignment greedily. Here ``y**2`` has one
    factorization and two admissible assignments: the carrier for one slot and
    a purchase for the other, either way round.
    """
    source = over_field(PolynomialMap((x, y, z), (x + y**2, y, z + y)))
    offered = multi_affine_steps(source, ReductionContext())

    assert len(squared_terms(source)) == 1
    assert len(offered) == 2
    for step in offered:
        assert remaining_excess(step.target) < remaining_excess(source)


def test_the_untargeted_walk_sees_a_carrier_on_a_cycle() -> None:
    """``reduce_to_degree3`` asked for the unipotent block until ``0.7.0rc4``.

    On this map all four coordinates satisfy BCW-10 and two of them lie on a
    dependency cycle, so ``carrier_indices`` holds two. A single step using the
    first coordinate twice drops the degree from four to three without buying
    anything; the walk bought a coordinate instead. An audit of ``0.7.0rc3``
    found it.
    """
    source = over_field(
        PolynomialMap(
            (x, y, z, w),
            (x + y**2, y + x + z, z + 2 * x + y**2, w + y**4),
        )
    )

    assert source.carrier_indices == (2, 3)
    assert source.carrier_indices_for_factors == (0, 1, 2, 3)

    outcome = reduce_to_degree3(source)
    assert outcome.reduction is not None
    outcome.reduction.verify()

    assert outcome.reduction.target.dimension == source.dimension
    assert outcome.reduction.target.degree() == 3


def test_a_peel_does_not_call_a_space_exhausted_over_a_cycle() -> None:
    """The pruning rule of ``peel`` turned the narrower set into a wrong claim.

    ``_stranded`` prunes a branch that stands one coordinate above the source
    when the source has no carrier, because a further step could then only buy.
    On a linear map whose coordinates depend on each other in a cycle,
    ``carrier_indices`` is empty and every coordinate satisfies BCW-10, so the
    premise was false and the peel reported an exhausted space with a verified
    chain inside its bounds. An audit of ``0.7.0rc3`` found it.
    """
    generators = sp.symbols("x0:4")
    source = over_field(
        PolynomialMap(
            generators,
            (
                generators[0] - 2 * generators[1] - generators[3],
                generators[0] + generators[1] - generators[2] + generators[3],
                -2 * generators[0] + generators[2] - 2 * generators[3],
                -2 * generators[0] + 2 * generators[1] + generators[2] + generators[3],
            ),
        )
    )

    assert source.determinant() == 1
    assert source.carrier_indices == ()
    assert source.carrier_indices_for_factors == (0, 1, 2, 3)

    first = BCWStep.build(
        source,
        0,
        Carried(1),
        Fresh(generators[2] * generators[3], sp.Symbol("u")),
        filtration_level=0,
    )
    second = BCWStep.build(
        first.target,
        1,
        Carried(2),
        Fresh(generators[0] * generators[1], sp.Symbol("v")),
        filtration_level=0,
    )
    Reduction((first, second)).verify()

    outcome = peel(source, second.target, budget=1000, rising=2, pairs=0)

    assert outcome.reduction is not None
    assert outcome.exhausted is False


def test_a_carrier_on_a_dependency_cycle_is_offered() -> None:
    """BCW-10 is the condition, and ``carrier_indices`` asks for more.

    That set is deliberately not maximal: it drops every coordinate on a
    dependency cycle, which is what makes the block it picks out unipotent.
    Here the first coordinate holds ``y`` and lies on a cycle, so asking the
    stronger question bought a coordinate the map already had. An audit of
    ``0.7.0rc2`` found it reaching six where five is enough.
    """
    source = over_field(
        PolynomialMap((x, y, z, w), (x + y, y + x + z, z + 2 * x + y, w + y**2))
    )

    assert source.determinant() == 1
    assert source.carrier_indices == (2, 3)

    outcome = reduce_to_multi_affine(source)
    assert outcome.reduction is not None
    outcome.reduction.verify()

    assert outcome.reduction.target.dimension == 5
    assert squared_terms(outcome.reduction.target) == ()


def test_a_carrier_is_used_where_one_is_safe() -> None:
    """UNT-9's saving, in this walk: a factor a coordinate holds costs nothing.

    ``x`` is carried, so the step that clears ``x**2 y`` buys one coordinate
    rather than two.
    """
    source = over_field(PolynomialMap((x, y, z), (x + x**2 * y, y, z + x)))
    offered = multi_affine_steps(source, ReductionContext())

    assert offered
    cheapest = min(step.target.dimension for step in offered)
    assert cheapest == source.dimension + 1


def test_a_carrier_inside_the_other_factor_is_passed_over() -> None:
    """``u`` cannot supply ``P`` when ``u`` occurs in ``Q``.

    The residue carries ``X_u Q``, which would square ``u``. The factor is
    offered fresh instead of refused, so the step survives and costs a
    dimension.
    """
    source = over_field(PolynomialMap((x, y, z), (x + y**2 * z, y, z + y)))
    offered = multi_affine_steps(source, ReductionContext())

    assert offered
    for step in offered:
        assert squared_terms(step.target) == () or remaining_excess(
            step.target
        ) < remaining_excess(source)


# ----------------------------------------------------------------------
# The walk
# ----------------------------------------------------------------------


def test_the_smallest_case_arrives_and_verifies() -> None:
    """``(x + y**3, y)`` is the case Theorem 2.1(b) is smallest on.

    Three steps to dimension six, which is the chain ``docs/roadmap.md``
    writes out. Until the carrier selector was corrected the walk took the
    same three steps to dimension seven, because it kept one coordinate per
    value and the one it kept was unusable at the third.
    """
    outcome = reduce_to_multi_affine(cube())
    assert outcome.reduction is not None

    outcome.reduction.verify()
    target = outcome.reduction.target

    assert len(outcome.reduction.steps) == 3
    assert target.dimension == 6
    assert squared_terms(target) == ()
    assert target.degree() == 3
    assert target.determinant() == 1
    assert outcome.exhausted is False


def test_the_degree_does_not_rise_along_the_walk() -> None:
    """A part of a split has degree below the monomial it comes from.

    So every term a step introduces has degree at most that of the term it
    removes, and the cubic half of Theorem 2.1(b) survives the refinement.
    """
    outcome = reduce_to_multi_affine(over_field(examples.alpoege12()))
    assert outcome.reduction is not None

    for step in outcome.reduction.steps:
        assert step.target.degree() <= 3


def test_a_multi_affine_source_is_the_base_case() -> None:
    """Nothing to build, as UNT-5 has it at degree three."""
    outcome = reduce_to_multi_affine(PolynomialMap((x, y), (x + x * y, y)))

    assert outcome.reduction is None
    assert outcome.examined == 0
    assert outcome.exhausted is True


def test_a_source_above_degree_three_is_refused_by_name() -> None:
    """The normal form is cubic as well, and the other walk is what lowers a degree."""
    source = over_field(PolynomialMap((x, y), (x + x**2 * y**3, y)))

    with pytest.raises(ValueError, match="reduce_to_degree3"):
        reduce_to_multi_affine(source)


def test_a_context_of_the_wrong_type_is_refused_before_the_base_case() -> None:
    """Whether an argument is well formed must not depend on the data."""
    with pytest.raises(TypeError, match="ReductionContext"):
        reduce_to_multi_affine(
            PolynomialMap((x, y), (x + x * y, y)),
            context="not a context",  # type: ignore[arg-type]
        )


def test_a_budget_of_zero_reports_a_cut_off_walk() -> None:
    """An exhausted space is a claim, and a cut-off one is not."""
    outcome = reduce_to_multi_affine(cube(), budget=0)

    assert outcome.reduction is None
    assert outcome.exhausted is False


def test_a_budget_that_runs_out_between_siblings_stops_the_loop() -> None:
    """The check sits inside the loop, as it does for the other two walks."""
    outcome = reduce_to_multi_affine(over_field(examples.alpoege13()), budget=1)

    assert outcome.reduction is None
    assert outcome.examined == 1
    assert outcome.exhausted is False


def test_a_negative_budget_is_refused() -> None:
    with pytest.raises(ValueError):
        reduce_to_multi_affine(cube(), budget=-1)


def test_a_source_that_is_not_a_map_is_refused() -> None:
    with pytest.raises(TypeError):
        reduce_to_multi_affine("not a map")  # type: ignore[arg-type]


# ----------------------------------------------------------------------
# HOM-11 and HOM-12
# ----------------------------------------------------------------------


def test_the_homogenization_of_a_multi_affine_chain_reaches_theorem_2_1_b() -> None:
    """The endpoint, with every step verified.

    The refinement, the linear normalization, the unipotent reduction and the
    homogenization. HOM-11 and HOM-12 are what say that the property arrived,
    and this checks the same two facts from outside the step.
    """
    refined = reduce_to_multi_affine(cube()).reduction
    assert refined is not None
    refined.verify()

    normalized = LinearStep.normalize(refined.target)
    normalized.verify()
    unipotent = UnipotentStep.build(normalized.target)
    unipotent.verify()
    homogenized = HomogenizationStep.build(unipotent.target)
    homogenized.verify()

    target = homogenized.target
    parameter = homogenized.variable
    position = target.dimension - 1

    assert squared_terms(target, exempt=(parameter,)) == ()
    assert (
        max(
            monomial[position]
            for component in target.displacement().to_polynomials()
            for monomial in component.itermonoms()
        )
        <= 2
    )


def test_the_two_stages_between_do_not_lose_the_property() -> None:
    """Neither carries an obligation for it, and both preserve it.

    ``LinearStep.normalize`` composes a constant matrix on the left and
    ``UnipotentStep`` builds its target out of homogeneous parts of the
    source's displacement and one linear block. This is the test that would
    fail if either stopped doing so.
    """
    refined = reduce_to_multi_affine(cube()).reduction
    assert refined is not None

    normalized = LinearStep.normalize(refined.target).target
    assert squared_terms(normalized) == ()

    unipotent = UnipotentStep.build(normalized).target
    assert squared_terms(unipotent) == ()


def test_a_source_that_is_not_multi_affine_leaves_hom_12_silent() -> None:
    """The hypothesis is a property the source is not required to have.

    So the obligation says nothing about every map this project carried before
    0.7, and a step over such a source verifies with a target that squares a
    variable. That is the obligation working and not failing.
    """
    source = over_field(examples.alpoege13())
    normalized = LinearStep.normalize(source).target
    unipotent = UnipotentStep.build(normalized).target

    assert squared_terms(unipotent)

    step = HomogenizationStep.build(unipotent)
    step.verify()

    assert squared_terms(step.target, exempt=(step.variable,))


def test_a_step_built_by_hand_still_verifies_the_new_obligations() -> None:
    """A supplied target that is the formula's output passes both.

    There is no negative control through ``verify()`` here, and the reason is
    on the contract page: HOM-1 runs first and a target that breaks HOM-11 or
    HOM-12 breaks HOM-1 too. The controls are on ``squared_terms`` above.
    """
    refined = reduce_to_multi_affine(cube()).reduction
    assert refined is not None
    normalized = LinearStep.normalize(refined.target).target
    unipotent = UnipotentStep.build(normalized).target

    built = HomogenizationStep.build(unipotent)
    supplied = HomogenizationStep(unipotent, built.target, built.variable)
    supplied.verify()

    assert supplied.target == built.target


def test_the_walk_reaches_the_three_maps_of_the_milestone() -> None:
    """The figures UNT-12 reports, recomputed.

    The most expensive thing this module does, at some seconds for the three
    chains together, and it stays in the fast suite. The docstring used to call
    it marked slow and it carries no marker; an audit of ``0.7.0rc3`` found the
    two disagreeing. The marker is not added, because deselecting this would
    leave the figures on three pages with nothing checking them; the sentence
    that claimed it goes instead.
    """
    reached = {}
    for name in ("alpoege13", "alpoege12", "spacerat11"):
        source = over_field(getattr(examples, name)())
        outcome = reduce_to_multi_affine(source)
        assert outcome.reduction is not None
        outcome.reduction.verify()
        reached[name] = outcome.reduction.target.dimension

        assert squared_terms(outcome.reduction.target) == ()
        assert outcome.reduction.target.degree() == 3

    assert reached == {"alpoege13": 19, "alpoege12": 23, "spacerat11": 24}


def test_a_bcw_step_that_squares_a_carrier_is_still_buildable() -> None:
    """UNT-12 narrows the walk and withdraws no obligation.

    BCW-10 admits two carried slots on one coordinate, and the ten-step chain
    of ``alpoege12`` uses that shape. It still builds and still verifies; what
    changed is that one walk does not offer it.
    """
    source = over_field(PolynomialMap((x, y), (x + y**2, y)))
    shared = sp.Symbol("u")
    carried = BCWStep.build(
        source, 0, Fresh(y, shared), Fresh(y, shared), filtration_level=0
    )
    carried.verify()

    assert squared_terms(carried.target)
