"""The 19-dimensional cubic Keller map from a source outside this project.

Fixed input like BCW17, and for the same reason: the source publishes the map
and not its factorization. Unlike for BCW17 the sequence of steps cannot be
read off either. It was reconstructed in 0.4 and stands below.

Up to 0.4 this said that the ``w`` numbering is not the order of introduction,
because ``G5`` uses the later ``w13`` and ``w9``. That was a wrong inference.
``G5`` is the component of ``w2``, and that is not an introduced value but the
residue of a later step, as shown below. After this correction every dependency
points at a smaller index, and ``w1`` to ``w16`` is a valid order of
introduction. Nothing is proved by that: it is one of about 7.26e10 valid
orders. It is only the obvious one again.

The source describes its procedure as seventeen elementary steps with sixteen
carrier variables, so not two per step. The ``P_j`` confirm this: ``x^2``,
``xy``, ``y^2``, ``yz``, ``xz``, ``x^2 y``, ``xy^2`` and ``y^2 z`` are building
blocks that more than one step uses. Since 0.3 ``BCWStep`` can express such a
step.

Reconstructing the sequence of steps was milestone 0.4. ``STEPS`` below holds
it, and ``test_the_peel_finds_a_chain_to_this_map`` shows that the backward
search finds a second valid chain. Provenance and the order of events:
``docs/references.md``.

The collision is not taken from the table of the source. It is reconstructed
from ``w_j = -P_j`` and compared with the table afterwards. The two routes are
independent.

The components below are transcribed from the rendered text version, in which
the exponents were lost: ``w32`` is ``w3^2``. On 3 August 2026 the
transcription was checked against the machine-readable dump the source links
to. All nineteen components agree as polynomials, the order of the variables
agrees, and all three points agree in all nineteen coordinates. The dump itself
is deliberately not in the repository; the reasons stand in
``docs/references.md``.

Incidentally this is the measurement that carries the design decision about the
Schur complement. Over the carrier block ``determinant()`` takes fractions of a
second, while ``sp.Matrix(F.jacobian()).det()`` does not finish within a
quarter of an hour at 19 variables.

On the provenance see ``docs/references.md``. The source is a self-published
note and carries no authority here. What makes the data usable is solely that
the checks below recompute it.
"""

import pytest
import sympy as sp

from kellermap import Collision, PolynomialMap, Reduction, examples, peel
from kellermap.bcw import BCWStep, Carried, Fresh

pytest.importorskip(
    "tests.data",
    reason=(
        "The nineteen-dimensional map is somebody else's mathematics and its "
        "licence could not be established, so this project does not "
        "distribute it. tests/data.py is in the repository and excluded from "
        "the source archive; without it this module has nothing to check."
    ),
)

from tests.data import (  # noqa: E402, F401
    ALPOEGE_IMAGE,
    ALPOEGE_POINTS,
    CARRIERS,
    COMPONENTS,
    PUBLISHED_POINTS,
    VARIABLES,
    W2_INTRODUCED,
    w,
    w1,
    w2,
    w3,
    w4,
    w5,
    w6,
    w7,
    w8,
    w9,
    w10,
    w11,
    w12,
    w13,
    w14,
    w15,
    w16,
    x,
    y,
    z,
)

# ``tests/data.py`` holds SymPy constants and nothing else, so that
# ``scripts/reconstruct_alpoege19.py`` can read the map without the library it
# checks. The map itself is built here.
ALPOEGE19 = PolynomialMap(VARIABLES, COMPONENTS)

# The three points from the source, for comparison with the reconstruction.


# The carrier components have the form w_j + P_j.


def lift(point: tuple[sp.Expr, ...]) -> tuple[sp.Expr, ...]:
    """Extend a point of k^3 to a point of k^19.

    A preimage of the stabilised map satisfies ``w_j = -P_j``. The system is
    triangular, because the dependency graph of the carriers is acyclic and the
    Jacobian block would not be unipotent otherwise, so the iteration from zero
    terminates. That it does is checked and not assumed.
    """
    values = dict(zip((x, y, z), point, strict=True))
    values.update({variable: sp.Integer(0) for variable in w})

    for _ in range(len(w) + 1):
        updated = {
            variable: sp.expand(-CARRIERS[variable].xreplace(values)) for variable in w
        }
        if updated == {variable: values[variable] for variable in w}:
            break
        values.update(updated)
    else:  # pragma: no cover
        raise AssertionError("the carrier system did not terminate")

    return tuple(values[variable] for variable in VARIABLES)


# --------------------------------------------------------------------------
# The map itself
# --------------------------------------------------------------------------


def test_dimension_and_degree() -> None:
    assert ALPOEGE19.dimension == 19
    assert ALPOEGE19.degree() == 3


def test_the_determinant_is_minus_two() -> None:
    """Constant, so a Keller map, and not normalised.

    BCW17 has determinant 1, because the step of Proposition (1.1) comes first
    there. Here it is absent.
    """
    assert ALPOEGE19.determinant() == -2


def test_it_lies_in_MA0_but_not_in_MA1() -> None:  # noqa: N802
    assert ALPOEGE19.is_in_MA(0)
    assert not ALPOEGE19.is_in_MA(1)


def test_the_linear_part_is_alpoeges_own() -> None:
    """Further evidence that no normalisation took place.

    The linear part is Alpoege's ``[[0,0,1],[0,1,0],[2,0,0]]``, extended by the
    identity on the carriers.
    """
    linear = sp.Matrix(
        ALPOEGE19.jacobian().xreplace(
            {variable: sp.Integer(0) for variable in VARIABLES}
        )
    )

    assert linear[:3, :3] == sp.Matrix([[0, 0, 1], [0, 1, 0], [2, 0, 0]])
    assert linear[3:, 3:] == sp.eye(16)
    assert linear.det() == -2


def test_the_carrier_block_is_the_stabilization() -> None:
    """The sixteen trailing coordinates carry the reduction."""
    assert ALPOEGE19.carrier_indices == tuple(range(3, 19))


def test_the_factors_cannot_be_read_off_pairwise() -> None:
    """This is why the map stands here and not as a Reduction.

    For BCW17 the factors can be read off the components in pairs, because step
    k creates the variables 2k+2 and 2k+3. Here the component of ``w2`` reaches
    for ``w9`` and ``w13``, so there is no such pattern.

    Up to 0.4 the test was called ``..._numbering_is_not_the_introduction_order``
    and thereby claimed more than it shows. The component of ``w2`` is a residue
    and not an introduced value, so it says nothing about when it was
    introduced.
    """
    assert {w9, w13} <= CARRIERS[w2].free_symbols


def test_the_carriers_are_shared_building_blocks() -> None:
    """Seventeen steps, sixteen variables: not two per step.

    Since 0.3 such a step can be written down as a ``BCWStep`` with a
    ``Carried`` slot. What is missing is the sequence of steps.
    """
    monomials = {CARRIERS[w7], CARRIERS[w9], CARRIERS[w13]}

    assert monomials == {y**2, x * y, x**2}
    # x^2 reappears as a building block in several later carriers.
    assert w13 in CARRIERS[w2].free_symbols


# --------------------------------------------------------------------------
# The collision
# --------------------------------------------------------------------------


def test_the_reconstruction_reproduces_the_published_points() -> None:
    """Two independent routes, the same numbers.

    The points come from ``w_j = -P_j`` here and not from the table of the
    source. The table serves for comparison only.
    """
    lifted = tuple(lift(point) for point in ALPOEGE_POINTS)
    expected = tuple(
        tuple(sp.nsimplify(coordinate) for coordinate in point)
        for point in PUBLISHED_POINTS
    )

    assert lifted == expected


def test_the_collision_verifies() -> None:
    collision = Collision.at(ALPOEGE19, [lift(point) for point in ALPOEGE_POINTS])

    assert len(collision) == 3
    assert collision.dimension == 19
    assert collision.verify(ALPOEGE19) is None


def test_the_image_is_alpoeges_own_padded_with_zeros() -> None:
    """No normalisation, so the image does not move either."""
    collision = Collision.at(ALPOEGE19, [lift(point) for point in ALPOEGE_POINTS])

    assert (
        collision.image
        == tuple(sp.nsimplify(c) for c in ALPOEGE_IMAGE) + (sp.Integer(0),) * 16
    )


def test_the_points_extend_alpoeges_in_their_first_three_coordinates() -> None:
    collision = Collision.at(ALPOEGE19, [lift(point) for point in ALPOEGE_POINTS])

    assert tuple(point[:3] for point in collision.points) == tuple(
        tuple(sp.nsimplify(coordinate) for coordinate in point)
        for point in ALPOEGE_POINTS
    )


def test_the_first_point_is_the_origin_over_alpoeges() -> None:
    """P1 is zero on every carrier, because every P_j vanishes there."""
    assert lift(ALPOEGE_POINTS[0])[3:] == (sp.Integer(0),) * 16


# --------------------------------------------------------------------------
# A piece of the sequence of steps
# --------------------------------------------------------------------------

# The component of w2 is not an introduced carrier value but the residue of a
# later step. Proposition (3.1) leaves in the target component
#
#     (F_i - P Q) - X_a Q - P X_b - X_a X_b,
#
# and with the two carrier coordinates w13 and w9 as slots, which carry x^2
# and x y, the introduced value of w2 is exactly P Q = x^3 y, which cancels
# against the first term. What is left are the three residual terms.


def test_the_component_of_w2_is_the_residue_of_a_carried_step() -> None:
    """A step with two ``Carried`` slots, so ``m = 0``.

    The map grows from dimension 3 to 19, so the sum of the ``m`` over
    seventeen steps is sixteen and at least one of them has ``m = 0``. This is
    one, and it is the only one the data yield.
    """
    left, right = CARRIERS[w13], CARRIERS[w9]

    residue = sp.expand(
        (W2_INTRODUCED - left * right) - w13 * right - left * w9 - w13 * w9
    )

    assert left == x**2
    assert right == x * y
    assert residue == sp.expand(CARRIERS[w2])


def test_the_removed_product_is_the_value_w2_was_introduced_with() -> None:
    """The ``-P Q`` term is missing from the residue, because it cancels.

    That is exactly what makes the introduced value readable: it has to be
    ``P Q``.
    """
    assert sp.expand(CARRIERS[w13] * CARRIERS[w9]) == W2_INTRODUCED


def test_a_perturbed_residue_is_not_the_component() -> None:
    """A negative control: without it the agreement above says nothing."""
    for perturbation in (w13 * w9, w13 * x * y, w9 * x**2):
        broken = sp.expand(CARRIERS[w2] + perturbation)

        assert broken != sp.expand(CARRIERS[w2])
        assert broken != sp.expand(
            (W2_INTRODUCED - CARRIERS[w13] * CARRIERS[w9])
            - w13 * CARRIERS[w9]
            - CARRIERS[w13] * w9
            - w13 * w9
        )


def test_w2_is_the_only_carrier_that_shows_the_signature() -> None:
    """The residue of a step carries a monomial in two carrier variables.

    This is not a rule of thumb. Both slot coordinates of a step are carrier
    variables, because ``Carried`` requires a carrier and ``Fresh`` creates
    one, and the components of x, y and z are not carriers here and are
    therefore not eligible as slots. A residue has to carry the signature. A
    value such as ``w6 = w1 x`` does name a carrier variable, but only one.

    What the test does not rule out: that the ``-X_a X_b`` term cancels against
    a term of the introduced value, the way the ``-P Q`` term cancels at
    ``w2``. A component overwritten in that way would look untouched. The test
    shows that only ``w2`` carries the signature, not that only ``w2`` was
    overwritten.
    """
    rewritten = [
        variable
        for variable, value in CARRIERS.items()
        if any(
            sum(1 for exponent in monomial[3:] if exponent) >= 2
            for monomial in sp.Poly(value, *VARIABLES).monoms()
        )
    ]

    assert rewritten == [w2]


def test_the_numbering_is_a_valid_introduction_order() -> None:
    """Every dependency points at a smaller index, after the correction.

    The introduced value of ``w2`` is ``x^3 y`` and names no carrier variable.
    The two that its published component names stand there as a residue. So
    ``w1`` to ``w16`` is a valid topological order of the dependency graph.

    This does not prove that it was the order. It refutes the only evidence
    against it that the source yields.
    """
    values = dict(CARRIERS)
    values[w2] = W2_INTRODUCED

    for position, variable in enumerate(w):
        used = {
            w.index(symbol) for symbol in values[variable].free_symbols if symbol in w
        }

        assert all(earlier < position for earlier in used), variable


def test_the_uncorrected_value_of_w2_is_what_broke_the_reading() -> None:
    """A negative control: with the value as read off, the ordering fails.

    And it fails at exactly one place. Without this control the test above says
    nothing about the correction. It could be green even if the value as read
    off had fitted just as well.
    """
    offenders = [
        variable
        for position, variable in enumerate(w)
        if any(
            w.index(symbol) >= position
            for symbol in CARRIERS[variable].free_symbols
            if symbol in w
        )
    ]

    assert offenders == [w2]


def test_the_pool_read_off_the_map_misses_that_value() -> None:
    """What the finding means for the search.

    SEA-8 lets an anchor come from the pool, and the pool is read off the target
    map. The value ``w2`` was introduced with does not stand there: an
    enumerator reaches this step only through its partner. The condition under
    which a pool read off the target holds stands under SEA-8 in
    ``docs/contracts.md``.
    """
    assert W2_INTRODUCED not in set(CARRIERS.values())


# --------------------------------------------------------------------------
# What can have been introduced last
# --------------------------------------------------------------------------


def occurrences(variable: sp.Symbol) -> list[int]:
    """Return the components a carrier variable occurs in."""
    return [
        index
        for index, component in enumerate(COMPONENTS)
        if variable in sp.expand(component).free_symbols
    ]


def test_six_coordinates_could_have_been_introduced_last() -> None:
    """A step leaves its fresh coordinate in exactly two places.

    In its own component, as ``X_u + P``, and in the residue of the target
    component. If it occurs nowhere else it can be the one introduced last. If
    it occurs more often, a later step used it and it cannot be.

    Six of sixteen satisfy this. That is why searching backwards is cheaper
    than searching forwards: there are six candidates for the last step here,
    while going forward the enumerator offers over a hundred on a map of this
    size.
    """
    last = {
        variable
        for variable in w
        if len(occurrences(variable)) == 2
        and VARIABLES.index(variable) in occurrences(variable)
    }

    assert last == {w[9], w[10], w[11], w[13], w[14], w[15]}


def test_the_target_of_each_such_step_is_read_off_too() -> None:
    """The second component is the one the introducing step aimed at.

    Three of the six aim at ``x``, two at ``y`` and one at ``z``. None aims at
    a carrier component, which fits what marks ``w2`` as the only carrier
    component that was overwritten.
    """
    targets = {
        variable: [
            index
            for index in occurrences(variable)
            if index != VARIABLES.index(variable)
        ][0]
        for variable in (w[9], w[10], w[11], w[13], w[14], w[15])
    }

    assert [targets[w[j]] for j in (9, 10, 11)] == [0, 0, 0]
    assert [targets[w[j]] for j in (13, 14)] == [1, 1]
    assert targets[w[15]] == 2


# --------------------------------------------------------------------------
# The sequence of steps
# --------------------------------------------------------------------------

# Reconstructed by an external audit of this project in August 2026 and
# recomputed independently here before it was written down. It uses three
# extensions of Proposition (3.1): a reused carrier (BCW-10), a coefficient
# (BCW-11) and a step whose two slots name one fresh variable (BCW-12).
#
# An entry is (target coordinate, slot, slot, coefficient). A slot is
# ("fresh", variable, value) or ("carried", variable). Positions belong to the
# chain and names do not, which is why no index appears here as a number.
FRESH, CARRIED = "fresh", "carried"

STEPS = (
    (x, (FRESH, w1, y**2 * z), (FRESH, w2, x**3 * y), 1),
    (y, (CARRIED, w2), (FRESH, w4, y * z), 3),
    (x, (CARRIED, w4), (FRESH, w5, x**2 * y), 3),
    (y, (CARRIED, w5), (FRESH, w8, x * w4), -3),
    (y, (CARRIED, w5), (FRESH, w7, y**2), 9),
    (x, (CARRIED, w8), (FRESH, w9, x * y), -3),
    (x, (CARRIED, w7), (CARRIED, w9), 7),
    (y, (CARRIED, w4), (FRESH, w13, x**2), 6),
    (w2, (CARRIED, w9), (CARRIED, w13), 1),
    (z, (CARRIED, w13), (FRESH, w16, x * z), -1),
    (y, (CARRIED, w13), (FRESH, w15, y * w8), 3),
    (y, (CARRIED, w13), (FRESH, w14, y * w7), -9),
    (x, (CARRIED, w5), (FRESH, w6, x * w1), -1),
    (x, (CARRIED, w9), (FRESH, w12, x * w6), 1),
    (x, (FRESH, w3, x * y**2), (FRESH, w3, x * y**2), 3),
    (x, (CARRIED, w9), (FRESH, w11, y * w3), -6),
    (x, (CARRIED, w7), (FRESH, w10, z * w2), -1),
)


def alpoege_in_published_coordinates() -> PolynomialMap:
    """Return the source of the chain: Alpoege's map, renamed.

    Not the linear normalization. The published map's linear part is Alpoege's
    own, so the chain starts at the unnormalized map -- and over ``ZZ``, since
    every coefficient in it is an integer and a Keller map over a ring is not
    the same object as the one over its field of fractions.
    """
    source = examples.alpoege()
    rename = dict(zip(source.variables, VARIABLES[:3], strict=True))

    return PolynomialMap(
        VARIABLES[:3],
        tuple(sp.expand(component.subs(rename)) for component in source.components),
    )


def build(steps: tuple = STEPS) -> Reduction:
    """Return the chain, built step by step with ``BCWStep``.

    The filtration level is derived and not chosen: ``H`` displaces the fresh
    coordinates by the factors, so its degree is one below the smallest order
    among them, and BCW-6 caps the declared level at one.
    """
    current, built = alpoege_in_published_coordinates(), []

    for target, left, right, coefficient in steps:
        slots, orders = [], []
        for slot in (left, right):
            if slot[0] == CARRIED:
                slots.append(Carried(current.variables.index(slot[1])))
                continue
            slots.append(Fresh(slot[2], slot[1]))
            orders.append(
                min(
                    sum(monomial)
                    for monomial in sp.Poly(
                        sp.expand(slot[2]), *current.variables
                    ).monoms()
                )
            )

        step = BCWStep.build(
            current,
            current.variables.index(target),
            slots[0],
            slots[1],
            1 if all(order >= 2 for order in orders) else 0,
            coefficient,
        )
        built.append(step)
        current = step.target

    return Reduction(tuple(built))


@pytest.mark.slow
def test_the_chain_is_a_verified_reduction() -> None:
    """The goal of milestone 0.4, as a certificate and not as a recomputation.

    Seventeen steps, each checked against BCW-1 to BCW-12, and at the end the
    published map itself. The chain is ``CONSTRUCTED``, so under BCW-9 its own
    verification is not evidence. The evidence is the endpoint, compared with
    data this project did not compute.
    """
    chain = build()

    assert chain.verify() is None
    assert len(chain.steps) == 17
    assert chain.source == alpoege_in_published_coordinates()
    assert chain.target.reordered(VARIABLES) == ALPOEGE19


@pytest.mark.slow
def test_the_chain_runs_as_recorded() -> None:
    """Dimensions and degrees, and what they say about the shape.

    The repetitions in the sequence of dimensions are the two steps that
    introduce no generator. The only jump by two is the first step, which has
    to, because Alpoege's map has no carriers.
    """
    chain = build()

    assert chain.dimensions() == (
        3,
        5,
        6,
        7,
        8,
        9,
        10,
        10,
        11,
        11,
        12,
        13,
        14,
        15,
        16,
        17,
        18,
        19,
    )
    assert chain.degrees() == (
        7,
        6,
        6,
        6,
        6,
        6,
        6,
        6,
        6,
        6,
        6,
        6,
        6,
        6,
        6,
        4,
        4,
        3,
    )
    assert sum(step.m for step in chain.steps) == 16
    assert [step.m for step in chain.steps].count(2) == 1
    assert [step.m for step in chain.steps].count(0) == 2


@pytest.mark.slow
def test_the_chain_carries_the_collision_to_the_published_points() -> None:
    """The second external piece of evidence, independent of the map.

    Alpoege's three points, transported through seventeen steps, give the
    fifty-seven coordinates of the published table.
    """
    chain = build()
    carried = chain.transport(
        Collision.at(alpoege_in_published_coordinates(), ALPOEGE_POINTS)
    )
    place = {variable: index for index, variable in enumerate(chain.target.variables)}

    reordered = tuple(
        tuple(sp.nsimplify(point[place[variable]]) for variable in VARIABLES)
        for point in carried.points
    )

    assert reordered == tuple(
        tuple(sp.nsimplify(value) for value in point) for point in PUBLISHED_POINTS
    )
    assert carried.verify(chain.target) is None


@pytest.mark.slow
def test_a_wrong_coefficient_does_not_reach_the_published_map() -> None:
    """A negative control: the coefficients are not ornament.

    Change a single one of them and the chain still builds and still verifies.
    It merely arrives somewhere else. That is exactly why the endpoint is the
    evidence and not ``verify()``.
    """
    target, left, right, coefficient = STEPS[6]
    perturbed = (*STEPS[:6], (target, left, right, coefficient + 1), *STEPS[7:])

    chain = build(perturbed)

    assert chain.verify() is None
    assert chain.target.reordered(VARIABLES) != ALPOEGE19


@pytest.mark.slow
def test_the_peel_finds_a_chain_to_this_map() -> None:
    """The search reaches the published map, without help.

    Eighteen examined maps. It is given source and target and nothing else: no
    pool of values, no names, no sign convention (REV-1). What bounds it is
    read off the target or follows from the arithmetic, and ``spare`` and
    ``pairs`` stand at the values that follow.

    Up to 0.4.0rc1 it found nothing, and the reason was not mathematical. The
    driver built the source over ``QQ`` with ``over_field`` while the target
    lies over ``ZZ``, and ``PolynomialMap`` counts the coefficient domain as
    part of its identity. An external audit found it. This test records that
    the domain agrees and that the search arrives.
    """
    source = alpoege_in_published_coordinates()

    assert source.ring.domain == ALPOEGE19.ring.domain

    outcome = peel(source, ALPOEGE19, budget=200, spare=2, pairs=1)

    assert outcome.reduction is not None
    assert outcome.reduction.verify() is None
    assert len(outcome.reduction.steps) == 17
    assert outcome.reduction.target.reordered(VARIABLES) == ALPOEGE19


@pytest.mark.slow
def test_the_chain_the_peel_finds_is_not_the_recorded_one() -> None:
    """A chain, not the chain.

    Both have seventeen steps and the same structure, with one step introducing
    two coordinates and two introducing none, and they introduce the
    coordinates in different orders. A test that pinned down the one found
    would stand in the way of this project's own obligation. This one records
    that there is more than one.
    """
    found = peel(
        alpoege_in_published_coordinates(), ALPOEGE19, budget=200, spare=2, pairs=1
    ).reduction
    recorded = build()

    assert found is not None
    assert len(found.steps) == len(recorded.steps)
    assert found.target.variables != recorded.target.variables
    assert found.target.reordered(VARIABLES) == recorded.target.reordered(VARIABLES)
