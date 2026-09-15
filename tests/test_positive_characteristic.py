"""Keller maps over a field of positive characteristic.

The core API has no characteristic-zero bound, and BCW state their section for
a commutative ring, so a map over ``GF(2)`` is inside what this library claims.
An audit of ``0.7.0rc5`` found one over ``GF(2)`` breaking four public
operations at once, all from the same cause: ``PolyElement.diff`` leaves a term
with a zero coefficient in the sparse dictionary there, and such a polynomial
compares unequal to the same polynomial without it.

The map below is the audit's. Its Jacobian is the identity, so it is a Keller
map, and every component displaces its variable by that variable squared, so
BCW-10 admits none of them as a carried factor. Those two facts pull the two
carrier notions apart, which is why they cannot be one predicate.
"""

from __future__ import annotations

from itertools import product

import pytest
import sympy as sp

from kellermap import (
    Collision,
    LinearAutomorphism,
    LinearStep,
    PolynomialMap,
    VerificationError,
    conjugate,
    search,
)
from kellermap.bcw.step import BCWStep, Fresh
from kellermap.polynomial_map import _evaluate_at


def squares() -> PolynomialMap:
    """``(x + x^2, y + y^2, z + z^2)`` over ``GF(2)``."""
    ring, x, y, z = sp.ring("x,y,z", sp.GF(2))

    return PolynomialMap.from_ring(ring, (x + x**2, y + y**2, z + z**2))


def test_the_jacobian_is_the_identity() -> None:
    """A zero-coefficient term in an entry would not show here.

    ``sp.Matrix`` normalizes on the way in, so this passed while everything
    reading the entries directly did not. It is the control that says the
    derivatives themselves are right and their storage was not.
    """
    assert squares().jacobian() == sp.eye(3)


def test_the_unipotent_block_is_every_coordinate() -> None:
    """The diagonal of that Jacobian is one, so the block is the whole map.

    It was empty, because the entry compared unequal to the ring's one.
    """
    assert squares().carrier_indices == (0, 1, 2)


def test_no_coordinate_is_a_carried_factor() -> None:
    """BCW-10 asks that ``F_j - X_j`` be free of ``X_j``, and ``X_j^2`` is not.

    This is where the two notions part, and it cannot be decided by the
    derivative: over ``GF(2)`` the derivative of ``X_j^2`` is zero, so the
    diagonal entry is one and the displacement still depends on the variable.
    The equivalence the property used to claim holds in characteristic zero
    only, and it was a claim this test would have caught.
    """
    assert squares().carrier_indices_for_factors == ()


def test_the_determinant_is_one() -> None:
    """It raised ``ExactQuotientFailed`` from inside the Schur complement."""
    assert squares().determinant() == 1


def test_a_search_from_the_map_to_itself_reports_a_non_answer() -> None:
    """Equal endpoints are a non-answer and not an error, REV-11's shape.

    It raised the same ``ExactQuotientFailed``, through the determinant.
    """
    outcome = search(squares(), squares(), {})

    assert outcome.reduction is None
    assert outcome.exhausted is True


def test_a_step_over_the_field_builds_and_verifies() -> None:
    """``BCWStep.verify`` reaches the determinant too."""
    source = squares()
    first, second = sp.symbols("u v")
    step = BCWStep.build(
        source, 0, Fresh(sp.Symbol("x"), first), Fresh(sp.Symbol("x"), second), 0
    )
    step.verify()

    assert step.m == 2
    assert step.target.dimension == 5


def test_characteristic_zero_is_unchanged() -> None:
    """The normalization is a no-op where the derivative was already sparse."""
    x, y = sp.symbols("x y")
    source = PolynomialMap((x, y), (x + y**2, y))

    assert source.carrier_indices == (0, 1)
    assert source.carrier_indices_for_factors == (0, 1)
    assert source.determinant() == 1


# --------------------------------------------------------------------------
# The audit of ``0.7.0rc6``: four operations deciding in characteristic zero
# --------------------------------------------------------------------------


def artin_schreier() -> PolynomialMap:
    """``x + x^2`` over ``GF(2)``, the classical counterexample in char 2.

    Jacobian one, and it identifies ``0`` and ``1``. The map the audit used to
    reach the evaluation, and the reason COL-7 exists rather than a
    characteristic-aware ``Collision``.
    """
    ring, x = sp.ring("x", sp.GF(2))

    return PolynomialMap.from_ring(ring, (x + x**2,))


def test_evaluation_happens_in_the_coefficient_domain() -> None:
    """``F(1) = 0`` over ``GF(2)`` and not ``2``.

    Substituting into ``x**2 + x`` gives ``2``, which is the answer in
    characteristic zero and no answer at all here. ``0.7.0rc6`` gave it, and
    COL-3 discarded a true collision on the strength of it.
    """
    F = artin_schreier()  # noqa: N806

    assert F(sp.Integer(0)) == sp.ImmutableMatrix([[0]])
    assert F(sp.Integer(1)) == sp.ImmutableMatrix([[0]])


def test_evaluation_outside_the_domain_still_substitutes() -> None:
    """The fallback, and the case it exists for.

    Gao's collision carries a radical the domain ``QQ`` does not hold, so a
    point need not lie in the coefficient domain. A field into which ``QQ``
    embeds has characteristic zero, so substitution is right there.
    """
    x, y = sp.symbols("x y")
    source = PolynomialMap((x, y), (x + y**2, y))

    assert source(sp.sqrt(2), sp.Integer(1)) == sp.ImmutableMatrix(
        [[1 + sp.sqrt(2)], [1]]
    )
    assert source(sp.Symbol("s"), sp.Symbol("t")) == sp.ImmutableMatrix(
        [[sp.Symbol("s") + sp.Symbol("t") ** 2], [sp.Symbol("t")]]
    )


def test_COL7_refuses_a_collision_against_a_map_of_positive_characteristic() -> None:  # noqa: N802
    """The points collide; the type declines to certify it.

    ``F(0) = F(1) = 0`` really does hold, and it is the Artin-Schreier fact
    that makes the Jacobian conjecture false in characteristic ``p``. COL-7
    refuses the statement rather than the arithmetic.
    """
    F = artin_schreier()  # noqa: N806

    with pytest.raises(VerificationError, match=r"\[COL-7\]") as failure:
        Collision.at(F, ((0,), (1,)))

    assert "characteristic" in failure.value.message

    with pytest.raises(VerificationError, match=r"\[COL-7\]"):
        Collision(((0,), (1,)), (0,)).verify(F)


def test_COL7_leaves_characteristic_zero_alone() -> None:  # noqa: N802
    """The negative control. Otherwise the obligation could refuse everything."""
    x, y = sp.symbols("x y")
    source = PolynomialMap((x, y), (x * y, sp.Integer(0) * x))

    assert Collision.at(source, ((1, 0), (2, 0))).image == (0, 0)


def test_SEA13_matches_a_pool_value_written_another_way() -> None:  # noqa: N802
    """An exact match is an exact match, whatever the spelling.

    Over ``GF(2)`` the pool values ``3z^2`` and ``5z^2`` are the factor
    ``z^2``. ``0.7.0rc6`` charged a rewrite for each, ran out with the default
    of one, and called the space exhausted after eleven maps.
    """
    ring, x, y, z = sp.ring("x,y,z", sp.GF(2))
    source = PolynomialMap.from_ring(ring, (x + z**4, y + z**2, z))
    first, second = sp.symbols("u v")
    zed = sp.Symbol("z")
    target = BCWStep.build(
        source, 0, Fresh(zed**2, first), Fresh(zed**2, second), 1
    ).target

    plain = search(source, target, {first: zed**2, second: zed**2})
    spelled = search(source, target, {first: 3 * zed**2, second: 5 * zed**2})

    assert plain.reduction is not None
    assert spelled.reduction is not None


def test_SEA13_matches_a_rational_spelling_over_a_fraction_field() -> None:  # noqa: N802
    """The same over ``QQ(T)``, where the domain cancels on the way in."""
    parameter = sp.Symbol("T")
    ring, x, y, z = sp.ring("x,y,z", sp.QQ.frac_field(parameter))
    source = PolynomialMap.from_ring(
        ring, (x + (parameter + 1) ** 2 * z**4, y + z**2, z)
    )
    first, second = sp.symbols("u v")
    zed = sp.Symbol("z")
    value = (parameter + 1) * zed**2
    target = BCWStep.build(
        source, 0, Fresh(value, first), Fresh(value, second), 1
    ).target

    folded = (parameter**2 - 1) / (parameter - 1) * zed**2

    assert search(source, target, {first: value, second: value}).reduction is not None
    assert search(source, target, {first: folded, second: folded}).reduction is not None


def test_BCW12_compares_the_two_slots_in_the_ring() -> None:  # noqa: N802
    """``y`` and ``-y`` are one element of ``GF(2)[x,y,z]``.

    ``0.7.0rc6`` asked ``kellermap.canonical``, which has no characteristic,
    and refused a step whose two slots are the same value.
    """
    ring, x, y, z = sp.ring("x,y,z", sp.GF(2))
    source = PolynomialMap.from_ring(ring, (x + y**2 * z**2, y, z))
    name = sp.Symbol("w")
    product = sp.Symbol("y") * sp.Symbol("z")

    step = BCWStep.build(source, 0, Fresh(product, name), Fresh(-product, name), 1)
    step.verify()

    assert step.m == 1
    assert step.target.dimension == 4


def test_LIN3_and_LIN6_hold_over_every_invertible_two_by_two() -> None:  # noqa: N802
    """The audit's enumeration, as a regression.

    Over ``GF(5)`` 392 of the 480 invertible matrices failed to normalize,
    because the elimination formed ``1/2`` as a rational and the determinant
    bookkeeping compared ``-1`` against ``1``.

    Two fields and not four: ``GF(7)`` alone is 2016 matrices, and the two
    here reach every shape the elimination has -- a pivot needing a swap, a
    pivot needing a reciprocal, and a determinant a transposition accounts
    for with the wrong sign. ``GF(3)`` and ``GF(7)`` are in neither suite,
    which is a choice and not an omission; this docstring said ``GF(7)``
    belongs in the slow suite until ``0.7.0rc8``, where nothing had put it
    there.
    """
    for modulus in (2, 5):
        ring = sp.ring("x,y", sp.GF(modulus))[0]
        first, second = ring.gens
        invertible = 0
        for entries in product(range(modulus), repeat=4):
            matrix = sp.Matrix(2, 2, list(entries))
            if matrix.det() % modulus == 0:
                continue
            invertible += 1
            source = PolynomialMap.from_ring(
                ring,
                tuple(
                    sum(
                        (
                            matrix[row, column] * ring.gens[column]
                            for column in range(2)
                        ),
                        ring.zero,
                    )
                    for row in range(2)
                ),
            )
            LinearStep.normalize(source).verify()

        assert invertible == {2: 6, 5: 480}[modulus]

    assert (first, second) == ring.gens


def test_conjugate_refuses_an_entry_that_is_zero_in_the_field() -> None:
    """``2`` is zero over ``GF(2)``, and the refusal is this function's to make.

    ``0.7.0rc6`` compared the entry to zero as an expression, so it reached
    SymPy's raw ``NotInvertible: zero divisor`` from inside the division.
    """
    with pytest.raises(ValueError, match="non-zero entries"):
        conjugate(squares(), (1, 2, 1))


def adversarial() -> PolynomialMap:
    """``(x + y^2, y + x^2)`` over ``GF(2)``.

    The audit's second map, and the one that already worked in ``0.7.0rc6``
    while nothing held it there. Its Jacobian is not the identity and its two
    displacements are free of their own variables, so it separates the carrier
    notions the other way round from ``squares()``.
    """
    ring, x, y = sp.ring("x,y", sp.GF(2))

    return PolynomialMap.from_ring(ring, (x + y**2, y + x**2))


def test_the_adversarial_map_is_a_keller_map_over_the_field() -> None:
    """Determinant one: ``1 - 4xy`` is ``1`` in characteristic two.

    Working and untested is a control that can be lost without anything
    saying so, which is why this is here rather than in a comment.
    """
    source = adversarial()

    assert source.determinant() == 1
    assert source.carrier_indices_for_factors == (0, 1)


def test_a_step_on_the_adversarial_map_builds_and_verifies() -> None:
    """Both coordinates hold a factor, so BCW-10's third clause admits them.

    Level zero and not one: both factors have order one, so ``H`` displaces
    the fresh coordinates by something of order one and reaches ``EA^0``.
    """
    source = adversarial()
    step = BCWStep.build(
        source,
        0,
        Fresh(sp.Symbol("y"), sp.Symbol("u")),
        Fresh(sp.Symbol("y"), sp.Symbol("v")),
        0,
    )
    step.verify()

    assert step.m == 2
    assert step.target.dimension == 4


# --------------------------------------------------------------------------
# The audit of ``0.7.0rc7``: the fallback over composite domains
# --------------------------------------------------------------------------

COMPOSITE_DOMAINS = [
    sp.QQ.poly_ring(sp.Symbol("T")),
    sp.QQ.frac_field(sp.Symbol("T")),
    sp.ZZ.poly_ring(sp.Symbol("T")),
    sp.GF(3).poly_ring(sp.Symbol("T")),
    sp.GF(3).frac_field(sp.Symbol("T")),
]


@pytest.mark.parametrize("domain", COMPOSITE_DOMAINS, ids=str)
def test_evaluation_falls_back_over_a_composite_domain(domain: object) -> None:
    """A point outside the domain substitutes, whatever the domain is made of.

    The regression `0.7.0rc7` shipped. Its fallback caught ``CoercionFailed``,
    which is what the atomic domains raise; every polynomial and fraction
    domain raises a bare ``ValueError`` instead, and a fraction field raises
    ``NotImplementedError`` for an argument that is not an expression. So the
    fallback became a crash exactly where it was needed, and the test that
    covered it used ``QQ``, which raises the one exception that was caught.
    """
    ring, x = sp.ring("x", domain)
    source = PolynomialMap.from_ring(ring, (x**2,))
    free = sp.Symbol("s")

    assert source(free) == sp.ImmutableMatrix([[free**2]])
    assert source(sp.sqrt(2)) == sp.ImmutableMatrix([[2]])


@pytest.mark.parametrize("domain", COMPOSITE_DOMAINS, ids=str)
def test_a_point_inside_a_composite_domain_still_evaluates_there(
    domain: object,
) -> None:
    """The control. A widened fallback must not swallow the domain path.

    The domain's own parameter is a point of it, so this is the case that has
    to keep going through the domain rather than through substitution.
    """
    parameter = sp.Symbol("T")
    ring, x = sp.ring("x", domain)
    source = PolynomialMap.from_ring(ring, (x**2,))

    assert source(parameter) == sp.ImmutableMatrix([[parameter**2]])


def test_a_collision_over_a_fraction_field_verifies() -> None:
    """COL-7 admits `QQ(T)`, and `0.7.0rc7` crashed before reaching it.

    Characteristic zero, points carrying a radical the domain does not hold,
    and a coefficient domain that is not atomic: the three conditions the
    fallback exists for, together.
    """
    ring, x = sp.ring("x", sp.QQ.frac_field(sp.Symbol("T")))
    source = PolynomialMap.from_ring(ring, (x**2,))

    collision = Collision.at(source, ((sp.sqrt(2),), (-sp.sqrt(2),)))

    assert collision.image == (2,)
    collision.verify(source)


class CountingValue:
    """A coefficient-domain value that records how it is combined.

    Enough of the protocol for ``_evaluate_at`` and no more: it multiplies,
    it exponentiates, and it adds into a running total whose left operand is
    a real domain element, so the reflected forms are needed too.
    """

    multiplications = 0
    powers = 0

    def __init__(self, value: object) -> None:
        self.value = value

    def __mul__(self, other: object) -> CountingValue:
        type(self).multiplications += 1
        return CountingValue(self.value * _plain(other))

    __rmul__ = __mul__

    def __pow__(self, exponent: int) -> CountingValue:
        type(self).powers += 1
        return CountingValue(self.value**exponent)

    def __add__(self, other: object) -> CountingValue:
        return CountingValue(self.value + _plain(other))

    __radd__ = __add__


def _plain(value: object) -> object:
    """Return the underlying value, whichever side of the operator it is."""
    return value.value if isinstance(value, CountingValue) else value


def test_evaluation_does_not_cost_one_multiplication_per_degree() -> None:
    """The complexity is asserted, not the value alone.

    `0.7.0rc7` multiplied once per unit of exponent, which the public API sets
    no bound on. `0.7.0rc8` fixed that and tested it by evaluating ``x**64``
    and checking the answer -- which the linear version also returns, so an
    audit of `0.7.0rc8` put the old body back and the test stayed green. A
    test that a faster implementation passes and a slower one passes too is a
    test of the result and not of the claim above it.

    So the point is a value that counts. Sixty-four units of exponent cost one
    exponentiation and a single multiplication into the term; the linear form
    costs sixty-four multiplications and no exponentiation, which is what the
    bounds below separate.
    """
    ring, x = sp.ring("x", sp.QQ)
    polynomial = (x**64).copy()
    CountingValue.multiplications = 0
    CountingValue.powers = 0

    result = _evaluate_at(polynomial, [CountingValue(sp.QQ(2))], sp.QQ)

    assert _plain(result) == sp.QQ(2**64)
    assert CountingValue.powers == 1
    assert CountingValue.multiplications <= 4

    ring2, y = sp.ring("y", sp.QQ)
    source = PolynomialMap.from_ring(ring2, (y**64,))

    assert source(sp.Integer(2)) == sp.ImmutableMatrix([[2**64]])


def test_conjugation_does_not_divide_once_per_degree() -> None:
    """The same shape in `conjugate`, which `0.7.0rc8` left behind.

    Only the evaluator was looked at, so the scaling loop kept dividing once
    per unit of exponent. Asserted on the value rather than on a count,
    because the reciprocal is formed outside the loop and the result is what
    a caller sees; the loop itself is checked by the mutation probe.
    """
    ring, x = sp.ring("x", sp.QQ)
    source = PolynomialMap.from_ring(ring, (x + x**64,))

    changed = conjugate(source, (2,))

    assert changed.components == (x.as_expr() + x.as_expr() ** 64 / 2**63,)


def test_a_zero_exponent_is_skipped_rather_than_raised_to() -> None:
    """``domain.zero ** 0`` raises over every composite domain here.

    So a monomial that omits a variable must skip it, and a point with a zero
    coordinate is the case that finds out.
    """
    ring, x, y = sp.ring("x,y", sp.QQ.poly_ring(sp.Symbol("T")))
    source = PolynomialMap.from_ring(ring, (x + y**2, y))

    assert source(sp.Integer(0), sp.Integer(0)) == sp.ImmutableMatrix([[0], [0]])


def test_conjugate_accepts_a_unit_of_a_domain_that_is_not_a_field() -> None:
    """``2`` is a unit of ``QQ[T]`` and ``i`` is a unit of ``ZZ[i]``.

    `0.7.0rc7` tested the entry against ``1`` and ``-1``, which are the units
    of ``ZZ`` and of nothing else here, and told a caller over ``QQ[T]`` to
    call ``over_field`` in order to obtain a reciprocal that domain already
    had.
    """
    parameter = sp.Symbol("T")
    over_polynomials, x = sp.ring("x", sp.QQ.poly_ring(parameter))
    first = PolynomialMap.from_ring(over_polynomials, (x + x**2,))

    assert conjugate(first, (2,)).components == (x.as_expr() ** 2 / 2 + x.as_expr(),)

    gaussian, y = sp.ring("y", sp.ZZ_I)
    second = PolynomialMap.from_ring(gaussian, (y + y**2,))

    assert not gaussian.domain.is_Field
    assert conjugate(second, (sp.I,)).components[0].has(sp.I)


def test_conjugate_still_refuses_a_non_unit() -> None:
    """The negative control, on both halves of what changed.

    ``2`` is not a unit of ``ZZ`` and ``T`` is not a unit of ``QQ[T]``, so
    widening the test must not have widened it to everything.
    """
    over_integers, x = sp.ring("x", sp.ZZ)
    with pytest.raises(ValueError, match="not a unit"):
        conjugate(PolynomialMap.from_ring(over_integers, (x + x**2,)), (2,))

    parameter = sp.Symbol("T")
    over_polynomials, y = sp.ring("y", sp.QQ.poly_ring(parameter))
    with pytest.raises(ValueError, match="not a unit"):
        conjugate(PolynomialMap.from_ring(over_polynomials, (y + y**2,)), (parameter,))


def test_the_factor_product_comes_back_normalized_over_a_finite_field() -> None:
    """``matrix()`` answers with the matrix it was given, not a congruent one.

    Over ``GF(2)`` the factorization of ``[[1, 1], [1, 0]]`` returned
    ``[[1, 1], [1, 2]]`` in `0.7.0rc7`. No certificate was wrong, since LIN-6
    converts before it compares, but a public method answered with entries
    outside the domain's normal form.
    """
    for modulus in (2, 5):
        ring = sp.ring("a,b", sp.GF(modulus))[0]
        domain = ring.domain
        for entries in product(range(modulus), repeat=4):
            given = sp.Matrix(2, 2, list(entries))
            if given.det() % modulus == 0:
                continue
            normalized = sp.Matrix(
                2,
                2,
                [
                    domain.to_sympy(domain.from_sympy(given[row, column]))
                    for row in range(2)
                    for column in range(2)
                ],
            )

            factored = LinearAutomorphism.factorize(ring, given)

            assert sp.Matrix(factored.matrix(ring)) == normalized


# --------------------------------------------------------------------------
# The audit of ``0.7.0rc8``: a pivot has to be a unit, not merely non-zero
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "entries",
    [(2, 1, 1, 1), (2, 1, 3, 2)],
    ids=["swap suffices", "needs a Euclidean combination"],
)
def test_a_unimodular_matrix_over_the_integers_factors(
    entries: tuple[int, ...],
) -> None:
    """`GL_2(ZZ)` is not `over_field()` territory.

    Both matrices have determinant one and both were refused in `0.7.0rc8`
    with a message about needing the field of fractions. The first needs only
    a swap to reach a unit pivot; the second needs the Euclidean algorithm run
    with row operations, which is the case the swap alone does not cover.
    """
    ring = sp.ring("x,y", sp.ZZ)[0]
    given = sp.Matrix(2, 2, list(entries))

    assert given.det() == 1

    factored = LinearAutomorphism.factorize(ring, given)

    assert sp.Matrix(factored.matrix(ring)) == given


def test_every_unimodular_two_by_two_over_the_integers_factors() -> None:
    """The audit's enumeration, as a regression.

    104 unimodular matrices with entries from -2 to 2, of which `0.7.0rc8`
    refused 16. The reconstruction is asserted for each, since a factorization
    that is returned but does not multiply back is worse than a refusal.
    """
    ring = sp.ring("x,y", sp.ZZ)[0]
    unimodular = 0

    for entries in product(range(-2, 3), repeat=4):
        given = sp.Matrix(2, 2, list(entries))
        if abs(given.det()) != 1:
            continue
        unimodular += 1

        assert (
            sp.Matrix(LinearAutomorphism.factorize(ring, given).matrix(ring)) == given
        )

    assert unimodular == 104


def test_a_determinant_that_is_not_a_unit_is_still_refused() -> None:
    """The negative control, and the reason the message changed.

    `[[2, 0], [0, 1]]` has determinant two, which is not a unit of `ZZ`, so no
    folding of the column produces a unit pivot and `over_field` really is the
    advice. The refusal now names the column rather than a reciprocal that the
    elimination happened to form first.
    """
    ring = sp.ring("x,y", sp.ZZ)[0]

    with pytest.raises(ValueError, match="No unit pivot was reached"):
        LinearAutomorphism.factorize(ring, sp.Matrix([[2, 0], [0, 1]]))


def test_a_domain_without_a_euclidean_algorithm_still_reaches_a_unit() -> None:
    """`ZZ[T]` is not a principal ideal domain and the bounded search runs there.

    `0.7.0rc9` gated the whole of the pivot work on `domain.is_PID`, so this
    matrix was refused although its determinant is one and `R1 <- R1 - R2`
    gives the unit pivot straight away. An audit of `0.7.0rc9` gave it.

    The negative control is the second matrix, whose determinant `2 - T**2` is
    not a unit of `ZZ[T]`: no combination can help, and the refusal stands.
    """
    parameter = sp.Symbol("T")
    ring = sp.ring("x,y", sp.ZZ.poly_ring(parameter))[0]

    assert not ring.domain.is_PID

    given = sp.Matrix([[parameter, parameter + 1], [parameter - 1, parameter]])

    assert sp.expand(given.det()) == 1
    assert sp.Matrix(LinearAutomorphism.factorize(ring, given).matrix(ring)) == given

    with pytest.raises(ValueError, match="No unit pivot was reached"):
        LinearAutomorphism.factorize(ring, sp.Matrix([[2, parameter], [parameter, 1]]))


def test_normalize_accepts_a_unimodular_linear_part_over_the_integers() -> None:
    """The boundary `LinearStep.normalize` documents is the determinant.

    It said "the domain has to be a field" and checked nothing, so which `ZZ`
    maps normalized depended on which entry the elimination met first.
    """
    ring = sp.ring("x,y", sp.ZZ)[0]
    first, second = ring.gens
    source = PolynomialMap.from_ring(ring, (2 * first + second, first + second))

    LinearStep.normalize(source).verify()


@pytest.mark.parametrize("modulus", [4, 6, 8, 9, 10, 12])
def test_conjugate_refuses_every_zero_divisor_as_a_value_error(modulus: int) -> None:
    """CNJ-1. `sp.GF(4)` is `Z/4Z` and not a field.

    A non-zero non-unit reached SymPy's raw `NotInvertible` in `0.7.0rc8`. The
    units of the same ring are the control: they have to keep working, or the
    refusal has merely been widened to everything.
    """
    ring, x = sp.ring("x", sp.GF(modulus))
    source = PolynomialMap.from_ring(ring, (x + x**3,))

    for entry in range(2, modulus):
        if sp.gcd(entry, modulus) == 1:
            conjugate(source, (entry,))
            continue
        with pytest.raises(ValueError):
            conjugate(source, (entry,))


@pytest.mark.parametrize("modulus", [4, 6])
def test_every_invertible_matrix_over_a_residue_ring_factors(modulus: int) -> None:
    """FAC-1 over a ring that is not an integral domain.

    `0.7.0rc9` gated the pivot work on `domain.is_PID`, and SymPy reports that
    for `Z/6Z`. The fold then divided by a zero divisor and `NotInvertible`
    escaped: an audit counted 48 invertible matrices over `Z/6Z` refused that
    way, 320 over `Z/10Z` and 768 over `Z/12Z`.

    Two moduli and not six: `Z/4Z` has zero divisors and a prime-power
    modulus, `Z/6Z` has two distinct prime factors, and between them they
    reach both shapes. The larger moduli are 13296 matrices and belong in
    neither suite.
    """
    ring = sp.ring("x,y", sp.GF(modulus))[0]
    domain = ring.domain
    invertible = 0

    for entries in product(range(modulus), repeat=4):
        given = sp.Matrix(2, 2, list(entries))
        if sp.gcd(int(given.det()) % modulus, modulus) != 1:
            continue
        invertible += 1
        normalized = sp.Matrix(
            2,
            2,
            [
                domain.to_sympy(domain.from_sympy(given[row, column]))
                for row in range(2)
                for column in range(2)
            ],
        )

        factored = LinearAutomorphism.factorize(ring, given)

        assert sp.Matrix(factored.matrix(ring)) == normalized

    assert invertible == {4: 96, 6: 288}[modulus]


def test_a_shear_over_a_residue_ring_normalizes() -> None:
    """The second half of the same blocker.

    `LinearStep.normalize` inverted through `domain.get_field()`, which for
    `Z/4Z` returns that ring again, so a shear of unit determinant raised
    `DMNotAField`. The advice to call `over_field` cannot help where the
    widening is not one. Nothing inverts a matrix now: the normalization
    factors the linear part and inverts the factorization.
    """
    ring = sp.ring("x,y", sp.GF(4))[0]
    first, second = ring.gens
    source = PolynomialMap.from_ring(ring, (first + 2 * second, second))

    LinearStep.normalize(source).verify()


def test_a_column_of_non_units_over_a_residue_ring_factors_in_three() -> None:
    """The search works past a column that holds no unit at all.

    Over `Z/6Z` the first column here is `(2, 2, 3)`: no entry is a unit, and
    subtracting one row from another clears an entry without reaching one
    either, so the search has to carry on rather than stop at the first
    combination. A `2x2` cannot show that -- a first column of two equal
    non-units has a determinant that is not a unit -- so the case begins at
    dimension three.

    It does not cover the skip for a divisor driven to zero, which is what
    this test was written for and does not do. That branch carries a pragma
    and `linear.py` says what is and is not known about reaching it.
    """
    ring = sp.ring("x,y,z", sp.GF(6))[0]
    domain = ring.domain
    given = sp.Matrix([[2, 3, 4], [2, 4, 3], [3, 3, 5]])

    assert sp.gcd(int(given.det()) % 6, 6) == 1

    factored = LinearAutomorphism.factorize(ring, given)
    normalized = sp.Matrix(
        3,
        3,
        [
            domain.to_sympy(domain.from_sympy(given[row, column]))
            for row in range(3)
            for column in range(3)
        ],
    )

    assert sp.Matrix(factored.matrix(ring)) == normalized
