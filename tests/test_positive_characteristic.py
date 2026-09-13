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

from itertools import product

import pytest
import sympy as sp

from kellermap import (
    Collision,
    LinearStep,
    PolynomialMap,
    VerificationError,
    conjugate,
    search,
)
from kellermap.bcw.step import BCWStep, Fresh


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
    bookkeeping compared ``-1`` against ``1``. Two fields here rather than
    four: ``GF(7)`` alone is 2016 matrices and belongs in the slow suite.
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


def test_evaluation_does_not_cost_one_multiplication_per_degree() -> None:
    """A sparse high power evaluates by exponentiation.

    Not a timing: the value is what is asserted. `0.7.0rc7` multiplied once
    per unit of exponent, which the public API sets no bound on.
    """
    ring, x = sp.ring("x", sp.QQ)
    source = PolynomialMap.from_ring(ring, (x**64,))

    assert source(sp.Integer(2)) == sp.ImmutableMatrix([[2**64]])


def test_a_zero_exponent_is_skipped_rather_than_raised_to() -> None:
    """``domain.zero ** 0`` raises over every composite domain here.

    So a monomial that omits a variable must skip it, and a point with a zero
    coordinate is the case that finds out.
    """
    ring, x, y = sp.ring("x,y", sp.QQ.poly_ring(sp.Symbol("T")))
    source = PolynomialMap.from_ring(ring, (x + y**2, y))

    assert source(sp.Integer(0), sp.Integer(0)) == sp.ImmutableMatrix([[0], [0]])
