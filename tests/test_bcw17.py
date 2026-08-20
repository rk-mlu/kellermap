"""A cubic Keller map in dimension 17, derived from Alpoege's.

This map has degree 3 and constant Jacobian determinant 1, and it inherits the
collision of Alpoege's map. It is therefore itself a counterexample to the
Jacobian conjecture and not merely a Keller map. The tests below compute all of
that themselves.

Up to version 0.2 it was a regression candidate: that it arises from Alpoege's
map *by a BCW reduction* was asserted and not shown. The section "Derivation"
below shows it now, as a ``Reduction`` of eight steps, verified step by step,
which carries the collision along.

What is evidence here and what is not
-------------------------------------
The intermediate maps in dimensions 5 to 15 are published nowhere. They
therefore *cannot* be supplied, and their steps are ``CONSTRUCTED``: BCW-1
compares the implementation with itself there. Under RED-7 the whole chain
carries the weaker provenance for that reason.

The external fact is the endpoint, and that is where the check bites. The last
step is given the fixed components as its target, so its BCW-1 compares an
externally computed map with ``G o F^[2] o H``. The same holds for the
collision, which is held against ``BCW17_COLLISION`` at the end of the chain,
and for the variable names, which the ``ReductionContext`` produces and the
table does not prescribe. If it names them anything but x4 to x17, the last
step fails.

The factorization itself is not searched for but read off the fixed
components: components 4 to 17 have the form ``X_j + P``, and these ``P`` are
the factors. Finding them is the business of 0.3. A recomputation of the same
chain in plain SymPy, independent of this library, stands in
``scripts/reconstruct_bcw17.py``.
"""

import math

import pytest
import sympy as sp

from kellermap import (
    Collision,
    PolynomialMap,
    Provenance,
    Reduction,
    ReductionContext,
    VerificationError,
    enumerate_candidates,
    examples,
    over_field,
)
from kellermap.bcw import BCWStep, Fresh
from kellermap.reduction import LinearStep
from kellermap.untargeted import lowers_the_weight

BCW17 = examples.bcw17()
X = BCW17.variables
COMPONENTS = BCW17.components
BCW17_COLLISION = examples.bcw17_collision().points
BCW17_IMAGE = sp.Matrix(examples.bcw17_collision().image)
ALPOEGE_COLLISION = examples.alpoege_collision().points

_1, _2, _3, _4, _5, _6, _7, _8, _9, _10, _11, _12, _13, _14, _15, _16, _17 = X


R = sp.Rational

# The three preimages arise from Alpoege's rational collision by carrying the
# stabilisation variables x4 to x17 along in topological order.


# The 14 stabilisation coordinates x4 to x17 of BCW Proposition (3.1). Their
# Jacobian block is unipotent, which is what the determinant strategy uses.
CARRIER_INDICES = tuple(range(3, 17))


@pytest.fixture(scope="module")
def bcw17() -> PolynomialMap:
    """``PolynomialMap`` is immutable, so module scope is enough.

    Building the ring costs noticeable time in dimension 17. This way it is
    paid once instead of once per test.
    """
    return PolynomialMap(variables=X, components=COMPONENTS)


def test_reordering_the_generators_changes_no_value(bcw17: PolynomialMap) -> None:
    """SEA-4 on the second fixed map, in dimension 17.

    The same control as for ALPOEGE15, on other data: reordering rewrites the
    presentation, and the way back gives the
    Original.
    """
    shuffled = X[8:] + X[:8]

    moved = bcw17.reordered(shuffled)

    assert moved.variables == shuffled
    assert moved != bcw17
    assert moved.reordered(X) == bcw17
    assert moved.determinant() == bcw17.determinant()
    assert moved.degree() == bcw17.degree()
    assert moved.filtration_degree() == bcw17.filtration_degree()


def test_bcw17_is_not_injective(bcw17: PolynomialMap) -> None:
    """The substance: three distinct preimages of one point."""
    points = tuple(tuple(map(sp.nsimplify, p)) for p in BCW17_COLLISION)

    assert len(set(points)) == 3

    images = [sp.expand(bcw17(*point)) for point in points]

    assert all(image == BCW17_IMAGE for image in images)


def test_bcw17_has_degree_three(bcw17: PolynomialMap) -> None:
    """The reduction target of BCW Proposition (3.1)."""
    assert bcw17.dimension == 17
    assert bcw17.degree() == 3


def test_bcw17_lies_in_MA0_but_not_MA1(bcw17: PolynomialMap) -> None:
    """F = X + H with ord(H) = 1: the linear part is not normalised yet.

    Components 11 and 13 carry the linear terms 7*x2 and -3*x2, so F lies in
    MA^0 and not in MA^1. This is exactly the state before the first step of
    BCW Section 4, which replaces F by F'' = F'_(1)^-1 o F'.
    """
    assert bcw17.displacement().order() == 1
    assert bcw17.is_in_MA(0)
    assert not bcw17.is_in_MA(1)


def test_bcw17_linear_part_is_invertible(bcw17: PolynomialMap) -> None:
    """J(F)(0) has to be invertible, otherwise the normalisation step of
    Section 4 cannot be carried out."""
    linear_part = bcw17.jacobian().xreplace({v: sp.Integer(0) for v in X})

    assert linear_part.det() == 1


# --------------------------------------------------------------------------
# The Keller property
# --------------------------------------------------------------------------


def test_bcw17_determinant_is_one(bcw17: PolynomialMap) -> None:
    """The Keller property, exactly and as a polynomial identity.

    This test used to sit behind an environment variable, because the 17 by 17
    determinant over QQ[x1..x17] took about a minute. Since ``determinant``
    computes the unipotent carrier block away through the Schur complement,
    milliseconds are left of it.
    """
    assert bcw17.determinant() == 1


def test_bcw17_carrier_block_is_the_stabilization_block(
    bcw17: PolynomialMap,
) -> None:
    """Where the speed-up comes from.

    The stabilisation coordinates are exactly those BCW appends: each has the
    form X_k + P with P in the remaining variables, and the dependencies among
    them are acyclic. The test records that the detection finds this structure
    and not merely some block by accident.
    """
    assert bcw17.carrier_indices == CARRIER_INDICES

    head = bcw17.dimension - len(CARRIER_INDICES)

    assert head == 3


def test_bcw17_determinant_is_not_constant_after_a_perturbation() -> None:
    """A control: the test above does not pass because it checks nothing.

    An additional cubic term in the first component leaves the carrier block
    untouched but changes the Schur complement. If the strategy were wrong, it
    would still find 1 here.
    """
    perturbed = PolynomialMap(
        variables=X,
        components=(COMPONENTS[0] + _2**3,) + COMPONENTS[1:],
    )

    assert perturbed.carrier_indices == CARRIER_INDICES
    assert perturbed.determinant() != 1


@pytest.mark.slow
def test_bcw17_determinant_strategies_agree(bcw17: PolynomialMap) -> None:
    """A cross-check of the two determinant strategies at full size.

    Under "Cross-representation tests" ``architecture.md`` requires holding
    this project's ``DomainMatrix`` integration against an independently
    computed result. Here the comparison runs the other way round: the
    ``DomainMatrix`` path is the reference and the Schur complement is the
    optimisation. Reaching for the private method is deliberate. The public API
    chooses the strategy itself, and that choice is what has to be bypassed
    here.

    Marked ``slow``: the reference path takes about a minute. That is the price
    of not checking the optimisation against itself.
    """
    reference = bcw17._determinant_by_domain_matrix(bcw17._jacobian_polynomials)

    assert reference.as_expr() == bcw17.determinant() == 1


# --------------------------------------------------------------------------
# Derivation: the chain from Alpoege to here
# --------------------------------------------------------------------------


# The seven applications of Proposition (3.1): the target component
# (zero-based), the two factors, and the EA level H reaches. The fresh
# variables are deliberately absent here. The ReductionContext hands them out,
# and that it arrives at x4 to x17 in this order is part of what the last step
# checks.
STEPS = (
    (0, -_1 * _3 / 2, _1**2, 1),
    (1, 3 * _1**2 * _2, _1 * _2 * _3 + 3 * _2**2, 1),
    (1, _1 * _2, 6 * _1 * _3 - 3 * _1 * _7 - _3 * _6, 1),
    (2, _1 * _2**2, _1**2 * _2 * _3 + 3 * _1 * _2**2 + 3 * _1 * _3 + 7 * _2, 0),
    (2, _1 * _2 * _10, -_1 * _3 - 3 * _2, 0),
    (2, _1 * _2, -_10 * _13 - _2 * _11, 1),
    (10, _2 * _3, _1**2, 1),
)


@pytest.fixture(scope="module")
def alpoege() -> PolynomialMap:
    """Over QQ, because the normalisation needs a reciprocal at once."""
    return over_field(examples.alpoege())


@pytest.fixture(scope="module")
def normalization(alpoege: PolynomialMap) -> LinearStep:
    """F'' = F'_(1)^-1 o F', the linear normalisation of BCW Section 4."""
    return LinearStep.normalize(alpoege)


@pytest.fixture(scope="module")
def reduction(
    alpoege: PolynomialMap, normalization: LinearStep, bcw17: PolynomialMap
) -> Reduction:
    """The complete chain, with a supplied target in the last step."""
    context = ReductionContext()
    steps: list[LinearStep | BCWStep] = [normalization]
    current = normalization.target

    for position, (index, P, Q, level) in enumerate(STEPS):
        fresh = context.variables(current.ring, 2)
        last = position == len(STEPS) - 1
        slots = (Fresh(P, fresh[0]), Fresh(Q, fresh[1]))
        step = (
            BCWStep(current, bcw17, index, *slots, level)
            if last
            else BCWStep.build(current, index, *slots, level)
        )
        steps.append(step)
        current = step.target

    return Reduction(steps)


def test_the_reduction_verifies(reduction: Reduction) -> None:
    """Eight steps, each checked on its own, and every seam between them."""
    assert reduction.verify() is None
    assert len(reduction) == 8


def test_the_reduction_reaches_bcw17(
    reduction: Reduction, bcw17: PolynomialMap
) -> None:
    """The endpoint is the fixed map and not merely one like it."""
    assert reduction.target == bcw17


def test_the_last_step_is_the_one_that_can_fail(reduction: Reduction) -> None:
    """Only there does an externally computed map stand on one side.

    The intermediate maps are published nowhere and therefore cannot be
    supplied. Their steps check the implementation against itself.
    """
    assert reduction[-1].provenance is Provenance.SUPPLIED
    assert reduction.provenance is Provenance.CONSTRUCTED


def test_a_perturbed_target_would_be_caught(
    reduction: Reduction, bcw17: PolynomialMap
) -> None:
    """A control: the check in the last step really bites.

    One sign wrong in the first component and BCW-1 fails. Without this test
    there would be no way to see whether the last step checks anything or
    merely happens to pass.
    """
    last = reduction[-1]
    perturbed = PolynomialMap(
        X, (bcw17.components[0] + _4 * _5,) + bcw17.components[1:]
    )
    broken = BCWStep(
        last.source,
        perturbed,
        last.index,
        Fresh(last.P, last.variables[0]),
        Fresh(last.Q, last.variables[1]),
    )

    with pytest.raises(VerificationError) as failure:
        Reduction(list(reduction[:-1]) + [broken]).verify()

    assert failure.value.obligation == "BCW-1"
    assert failure.value.step == 7


def test_the_dimensions_and_degrees(reduction: Reduction) -> None:
    """3 to 17 in seven steps of two each, degree 7 to 3."""
    assert reduction.dimensions() == (3, 3, 5, 7, 9, 11, 13, 15, 17)
    assert reduction.degrees() == (7, 7, 7, 7, 7, 5, 4, 4, 3)


def test_the_context_names_x4_to_x17(reduction: Reduction) -> None:
    """The names come from the context and not from the table."""
    allocated = tuple(
        variable
        for step in reduction
        if isinstance(step, BCWStep)
        for variable in step.variables
    )

    assert allocated == X[3:]


def test_the_collision_is_transported(
    reduction: Reduction, alpoege: PolynomialMap
) -> None:
    """The actual purpose: three points in k^3 become three in k^17."""
    carried = reduction.transport(Collision.at(alpoege, ALPOEGE_COLLISION))

    assert carried == Collision(
        tuple(tuple(map(sp.nsimplify, point)) for point in BCW17_COLLISION),
        tuple(BCW17_IMAGE),
    )


def test_the_determinant_is_settled_by_the_linear_step(
    reduction: Reduction, alpoege: PolynomialMap
) -> None:
    """Under LIN-3 the only place where they may change."""
    assert alpoege.determinant() == -2
    assert reduction[0].transformation.determinant() == R(-1, 2)
    assert all(
        step.target.determinant() == 1
        for step in reduction
        if isinstance(step, BCWStep)
    )


def test_the_filtration_explains_MA0(reduction: Reduction) -> None:  # noqa: N802
    """Why BCW17 lies in MA^0 and not in MA^1.

    Exactly two of the seven steps reach only EA^0, because their Q carries a
    linear term: 7*x2 and -3*x2. These are exactly the two linear terms that
    stand in components 11 and 13.
    """
    levels = [step.filtration_level for step in reduction if isinstance(step, BCWStep)]

    assert levels == [1, 1, 1, 0, 0, 1, 1]
    assert reduction.filtration_level() == 0
    assert reduction[0].filtration_level == math.inf


def test_the_two_EA0_steps_are_the_linear_terms(  # noqa: N802
    reduction: Reduction, bcw17: PolynomialMap
) -> None:
    """The connection between the certificate and the fixed map."""
    modest = [
        step
        for step in reduction
        if isinstance(step, BCWStep) and step.filtration_level == 0
    ]

    assert [step.variables for step in modest] == [(_10, _11), (_12, _13)]
    assert 7 * _2 in bcw17.components[10].args
    assert -3 * _2 in bcw17.components[12].args


# --------------------------------------------------------------------------
# The linear step on its own
# --------------------------------------------------------------------------


def test_normalization_explains_the_determinant(
    alpoege: PolynomialMap, normalization: LinearStep
) -> None:
    """Why BCW17 has determinant 1 and Alpoege has -2.

    The linear part of Alpoege has determinant -2 itself, so the normalisation
    divides it out. Stabilisation and elementary factors cannot change the
    determinant afterwards.
    """
    assert alpoege.determinant() == -2
    assert normalization.target.determinant() == 1


def test_normalization_reaches_MA1(  # noqa: N802
    alpoege: PolynomialMap, normalization: LinearStep
) -> None:
    """The hypothesis of Proposition (3.1).

    Alpoege lies in MA^0 only. Not until the normalisation is the linear part
    the identity and the map in MA^1.
    """
    assert not alpoege.is_in_MA(1)
    assert normalization.target.is_in_MA(1)


def test_normalization_is_a_transposition_and_a_dilation(
    normalization: LinearStep,
) -> None:
    """And therefore not elementary: EA_n(k) has determinant 1 only."""
    assert len(normalization.transformation) == 2
    assert not normalization.transformation.is_elementary


def test_normalization_explains_the_image(
    alpoege: PolynomialMap, normalization: LinearStep
) -> None:
    """Why the collision image is (0, 0, -1/4) and not (-1/4, 0, 0).

    The linear part swaps the first and third coordinate, and so does its
    inverse. Left composition leaves every preimage where it was.
    """
    moved = normalization.transport(Collision.at(alpoege, ALPOEGE_COLLISION))

    assert moved.points == Collision.at(alpoege, ALPOEGE_COLLISION).points
    assert moved.image == tuple(BCW17_IMAGE)[:3]


def test_the_collision_extends_alpoeges(bcw17: PolynomialMap) -> None:
    """The collision points continue Alpoege's points.

    The connection between the two maps is therefore more than an assertion:
    the same three preimages, extended by 14 stabilisation coordinates.
    """
    heads = {tuple(map(sp.nsimplify, p))[:3] for p in BCW17_COLLISION}
    alpoege_points = {tuple(map(sp.nsimplify, point)) for point in ALPOEGE_COLLISION}

    assert heads == alpoege_points
    assert bcw17.dimension - 3 == 14


def test_the_enumerator_contains_every_step_of_this_chain(
    reduction: Reduction,
) -> None:
    """The control for the candidate enumerator, on known steps.

    The pool comes from the target map: the values its carrier coordinates
    hold. For every step of the chain the enumerator has to offer, on the map
    before it, a candidate with the same target component and the same two
    factors, and the derived EA level has to be that of the step.

    An enumerator that passes over a step known to exist is incomplete in a way
    that a failure of the search alone would not show.
    """
    final = reduction.target
    pool = [
        sp.expand(final.components[index] - final.variables[index])
        for index in final.carrier_indices
    ]

    steps = [step for step in reduction.steps if isinstance(step, BCWStep)]
    assert len(steps) == 7

    for position, step in enumerate(steps, start=1):
        wanted = sorted(str(sp.expand(value)) for value in (step.P, step.Q))
        found = [
            candidate
            for candidate in enumerate_candidates(step.source, pool)
            if candidate.index == step.index
            and sorted(str(sp.expand(v)) for v in candidate.values(step.source))
            == wanted
        ]

        assert found, f"step {position} is missing from the enumeration"
        assert found[0].filtration_level(step.source) == step.filtration_level


def test_every_step_lowers_the_untargeted_measure(reduction: Reduction) -> None:
    """UNT-3, on a chain whose steps are known to be right.

    The evidence behind the measure is that it falls along the chains this
    repository carries. Stating it here rather than in ``test_untargeted.py``
    puts it where the chain is, and a chain that stopped satisfying it would
    fail beside the tests that say what it is.

    The linear normalisation is not a BCW step and is not asked to lower
    anything. It divides out the linear part and leaves the degree alone.
    """
    for step in reduction.steps:
        if not isinstance(step, BCWStep):
            continue

        assert lowers_the_weight(step.source, step.target), step
