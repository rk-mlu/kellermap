"""Keller maps this repository writes out more than once.

Two criteria decide what is here, and both are counted rather than judged. A
map belongs in this module if it is written out in more than one place, and if
it is a Keller map -- its Jacobian determinant is a non-zero constant. The tree
holds 119 distinct ``PolynomialMap`` constructions, 25 of them repeated, and
the determinant sorts those 25 into the ones below and six that are not Keller
maps at all.

The six stay where they are used. They are written the way they are *because*
they are not Keller maps: they exercise degree growth, non-injectivity and a
non-constant determinant, and a module named ``examples`` beside a library
about Keller maps would say otherwise about them.

Provenance. Everything here except ``alpoege`` was written for this project's
own tests and documentation. ``alpoege`` is somebody else's mathematics; see
``docs/references.md`` for the source and for what the agreement of a chain
with it does and does not establish. Distributing a map does not change who
computed it, so ``Provenance.SUPPLIED``, BCW-9 and SEA-5 mean here exactly what
they mean anywhere else.

Functions rather than constants, so that importing ``kellermap`` does not build
maps nobody asked for. Each returns the map over the domain its coefficients
imply -- mostly ``ZZ``, and ``ZZ[T]`` where a parameter appears. Use
``over_field`` where a field is needed.

The symbols are fixed and part of what each function is. That is deliberate:
the repetitions this module removes were repetitions of one spelling, symbol
names included, and a caller who needs other names is not repeating anything.

Usage::

    from kellermap import examples

    source = examples.factorable_shear()
"""

from __future__ import annotations

import sympy as sp

from .collision import Collision
from .polynomial_map import PolynomialMap

R = sp.Rational
"""Short name for the rational coefficients the reference reductions carry."""

# --------------------------------------------------------------------------
# Two coordinates
# --------------------------------------------------------------------------


def sum_and_difference() -> PolynomialMap:
    """Return ``(x + y, x - y)``, a linear map with determinant ``-2``.

    Linear, invertible and not unimodular, which is why it is useful: a check
    that only holds for determinant one fails on it.
    """
    x, y = sp.symbols("x y")

    return PolynomialMap((x, y), (x + y, x - y))


def shear() -> PolynomialMap:
    """Return ``(x + y, y)``, the simplest non-identity elementary map."""
    x, y = sp.symbols("x y")

    return PolynomialMap((x, y), (x + y, y))


def quadratic_shear() -> PolynomialMap:
    """Return ``(x + y**2, y)``.

    In ``MA^1`` and not in ``MA^2``: the displacement has order two.
    """
    x, y = sp.symbols("x y")

    return PolynomialMap((x, y), (x + y**2, y))


def cubic_shear() -> PolynomialMap:
    """Return ``(x + y**3, y)``, one filtration stage above the quadratic one."""
    x, y = sp.symbols("x y")

    return PolynomialMap((x, y), (x + y**3, y))


def lower_shear() -> PolynomialMap:
    """Return ``(x, y + x**2)``, the quadratic shear on the other coordinate.

    Useful beside ``quadratic_shear`` wherever a check might depend on which
    coordinate carries the displacement.
    """
    x, y = sp.symbols("x y")

    return PolynomialMap((x, y), (x, y + x**2))


def doubled_shear() -> PolynomialMap:
    """Return ``(2 X1 + X2**2, X2)``, determinant ``2``.

    A Keller map whose determinant is a unit only over a field, which is where
    the difference between ``ZZ`` and ``QQ`` becomes visible.
    """
    first, second = sp.symbols("X1 X2")

    return PolynomialMap((first, second), (2 * first + second**2, second))


# --------------------------------------------------------------------------
# With a parameter in the coefficient domain
# --------------------------------------------------------------------------


def parametric_shear() -> PolynomialMap:
    """Return ``(x + T y**2, y)`` over ``ZZ[T]``.

    ``T`` is a parameter of the coefficient domain and not a coordinate. The
    distinction is the one COL-2, BCW-3 and TRA-2 all turn on.
    """
    x, y, parameter = sp.symbols("x y T")

    return PolynomialMap((x, y), (x + parameter * y**2, y))


def parametric_swap() -> PolynomialMap:
    """Return ``(T x + y, x)`` over ``ZZ[T]``, determinant ``-1``.

    Linear, and its determinant is constant while its entries are not.
    """
    x, y, parameter = sp.symbols("x y T")

    return PolynomialMap((x, y), (parameter * x + y, x))


# --------------------------------------------------------------------------
# Three coordinates
# --------------------------------------------------------------------------


def factorable_shear() -> PolynomialMap:
    """Return ``(x1 + x2**2 x3**2, x2, x3)``.

    The displacement factors in more than one way, which is what makes it the
    standard source for a ``BCWStep``: ``x2**2 x3**2`` splits as
    ``x2 * (x2 x3**2)``, as ``(x2 x3) * (x2 x3)``, and so on.
    """
    first, second, third = sp.symbols("x1 x2 x3")

    return PolynomialMap(
        (first, second, third), (first + second**2 * third**2, second, third)
    )


def unit_translation() -> PolynomialMap:
    """Return ``(x1 + 1, x2, x3)``.

    Outside ``MA^0``: its displacement has order zero, so its filtration degree
    is ``-1`` and ``LinearStep.normalize`` refuses it. The source a
    ``TranslationStep`` is for.
    """
    first, second, third = sp.symbols("x1 x2 x3")

    return PolynomialMap((first, second, third), (first + 1, second, third))


def alpoege() -> PolynomialMap:
    """Return Alpoege's three-dimensional counterexample, of degree 7.

    Determinant ``-2``, so a Keller map and not normalized. Every chain in this
    repository starts here: ``bcw17``, ``alpoege15`` and the published
    nineteen-dimensional map are all reductions of it.

    Somebody else's mathematics. ``docs/references.md`` records the source, the
    licensed presentation the values were checked against, and what agreement
    with a reduction of it does and does not establish.
    """
    first, second, third = sp.symbols("x1 x2 x3")

    return PolynomialMap(
        (first, second, third),
        (
            (1 + first * second) ** 3 * third
            + second**2 * (1 + first * second) * (4 + 3 * first * second),
            second
            + 3 * first * (1 + first * second) ** 2 * third
            + 3 * first * second**2 * (4 + 3 * first * second),
            2 * first - 3 * first**2 * second - first**3 * third,
        ),
    )


# --------------------------------------------------------------------------
# Four coordinates
# --------------------------------------------------------------------------


def paired_shear() -> PolynomialMap:
    """Return ``(X1, X2, X3 + X2**2, X4 + X2**2)``.

    Two coordinates carrying the same value. Whatever reads a carrier has to
    say which coordinate it means, and this is where that shows.
    """
    names = sp.symbols("X1:5")

    return PolynomialMap(
        names, (names[0], names[1], names[2] + names[1] ** 2, names[3] + names[1] ** 2)
    )


def product_shear() -> PolynomialMap:
    """Return ``(X1 - X3 X4, X2, X3, X4)``.

    The shape a ``BCWStep`` leaves behind: one component short a product of two
    other coordinates. Useful as a target whose factorization is evident.
    """
    names = sp.symbols("X1:5")

    return PolynomialMap(
        names, (names[0] - names[2] * names[3], names[1], names[2], names[3])
    )


# --------------------------------------------------------------------------
# The reference reductions
# --------------------------------------------------------------------------


def bcw17() -> PolynomialMap:
    """Return the seventeen-dimensional cubic reduction of Alpoege's map.

    Seven Proposition (3.1) steps, each introducing two coordinates, so its
    factors can be read off the components pairwise. Determinant ``1``: the
    chain begins with the linear normalization, which divides out the ``-2`` of
    the map it reduces.

    Not output of this library: the components are the maintainer's own hand
    computation, checked against ``scripts/reconstruct_bcw17.py``. External to
    the library and not to the project, which is the distinction
    ``docs/references.md`` records and BCW-9 turns on.
    """
    names = sp.symbols("x1:18")
    _1, _2, _3, _4, _5, _6, _7, _8, _9, _10, _11, _12, _13, _14, _15, _16, _17 = names
    return PolynomialMap(
        names,
        (
            -3 * _1**2 * _2 / 2 - _1**2 * _4 + _1 * _3 * _5 / 2 + _1 - _4 * _5,
            12 * _1 * _2**2
            - _1 * _2 * _9
            - 6 * _1 * _3 * _8
            + 3 * _1 * _3
            + 3 * _1 * _7 * _8
            - 3 * _2**2 * _6
            + _2
            + _3 * _6 * _8
            - _6 * _7
            - _8 * _9,
            -3 * _1 * _10 * _3
            + _1 * _12 * _3
            - _1 * _15 * _2
            + 3 * _1 * _2 * _3
            - _10 * _11
            + _10 * _13 * _14
            - 7 * _10 * _2
            + _11 * _14 * _2
            - _12 * _13
            + 3 * _12 * _2
            - _14 * _15
            + 4 * _2**2
            + _3,
            -_1 * _3 / 2 + _4,
            _1**2 + _5,
            3 * _1**2 * _2 + _6,
            _1 * _2 * _3 + 3 * _2**2 + _7,
            _1 * _2 + _8,
            6 * _1 * _3 - 3 * _1 * _7 - _3 * _6 + _9,
            _1 * _2**2 + _10,
            -(_1**2) * _16
            + 3 * _1 * _2**2
            + 3 * _1 * _3
            + _11
            - _16 * _17
            - _17 * _2 * _3
            + 7 * _2,
            _1 * _10 * _2 + _12,
            -_1 * _3 + _13 - 3 * _2,
            _1 * _2 + _14,
            -_10 * _13 - _11 * _2 + _15,
            _16 + _2 * _3,
            _1**2 + _17,
        ),
    )


def alpoege15() -> PolynomialMap:
    """Return the fifteen-dimensional cubic reduction of Alpoege's map.

    Seven steps as well, two of which reuse a carrier and so introduce one
    coordinate rather than two -- which is what takes it to fifteen instead of
    seventeen. Its seventh step rewrites component 10, so the value that
    coordinate was introduced with is not the value it carries here.

    Same provenance as ``bcw17``, checked against
    ``scripts/reconstruct_alpoege15.py``.
    """
    names = sp.symbols("x1:16")
    _1, _2, _3, _4, _5, _6, _7, _8, _9, _10, _11, _12, _13, _14, _15 = names
    return PolynomialMap(
        names,
        (
            -3 * _1**2 * _2 / 2 - _1**2 * _4 + _1 * _3 * _5 / 2 + _1 - _4 * _5,
            12 * _1 * _2**2
            - _1 * _2 * _9
            - 6 * _1 * _3 * _8
            + 3 * _1 * _3
            + 3 * _1 * _7 * _8
            - 3 * _2**2 * _6
            + _2
            + _3 * _6 * _8
            - _6 * _7
            - _8 * _9,
            -3 * _1 * _10 * _3
            + _1 * _12 * _3
            - _1 * _14 * _2
            + 3 * _1 * _2 * _3
            - _10 * _11
            + _10 * _13 * _8
            - 7 * _10 * _2
            + _11 * _2 * _8
            - _12 * _13
            + 3 * _12 * _2
            - _14 * _8
            + 4 * _2**2
            + _3,
            -_1 * _3 / 2 + _4,
            _1**2 + _5,
            3 * _1**2 * _2 + _6,
            _1 * _2 * _3 + 3 * _2**2 + _7,
            _1 * _2 + _8,
            6 * _1 * _3 - 3 * _1 * _7 - _3 * _6 + _9,
            _1 * _2**2 + _10,
            -(_1**2) * _15
            + 3 * _1 * _2**2
            + 3 * _1 * _3
            + _11
            - _15 * _5
            - _2 * _3 * _5
            + 7 * _2,
            _1 * _10 * _2 + _12,
            -_1 * _3 + _13 - 3 * _2,
            -_10 * _13 - _11 * _2 + _14,
            _15 + _2 * _3,
        ),
    )


# --------------------------------------------------------------------------
# The collisions these maps carry
# --------------------------------------------------------------------------


def alpoege_collision() -> Collision:
    """Return the three points Alpoege's map sends to one image.

    Somebody else's mathematics, like the map itself. The points are the
    datum; the image is computed from them, which is what ``Collision.at``
    does and what makes it a claim this library can be wrong about.
    """
    return Collision.at(
        alpoege(),
        (
            (0, 0, R(-1, 4)),
            (1, R(-3, 2), R(13, 2)),
            (-1, R(3, 2), R(13, 2)),
        ),
    )


def bcw17_collision() -> Collision:
    """Return the collision of ``bcw17``, Alpoege's carried to seventeen
    coordinates."""
    return Collision(
        (
            (0, 0, R(-1, 4), 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
            (
                1,
                R(-3, 2),
                R(13, 2),
                R(13, 4),
                -1,
                R(9, 2),
                3,
                R(3, 2),
                R(-3, 4),
                R(-9, 4),
                -6,
                R(-27, 8),
                2,
                R(3, 2),
                R(9, 2),
                R(39, 4),
                -1,
            ),
            (
                -1,
                R(3, 2),
                R(13, 2),
                R(-13, 4),
                -1,
                R(-9, 2),
                3,
                R(3, 2),
                R(3, 4),
                R(9, 4),
                6,
                R(27, 8),
                -2,
                R(3, 2),
                R(9, 2),
                R(-39, 4),
                -1,
            ),
        ),
        tuple(sp.Matrix([0, 0, R(-1, 4)] + [0] * 14)),
    )


def alpoege15_collision() -> Collision:
    """Return the collision of ``alpoege15``."""
    return Collision(
        (
            (0, 0, R(-1, 4)) + (0,) * 12,
            (
                1,
                R(-3, 2),
                R(13, 2),
                R(13, 4),
                -1,
                R(9, 2),
                3,
                R(3, 2),
                R(-3, 4),
                R(-9, 4),
                -6,
                R(-27, 8),
                2,
                R(9, 2),
                R(39, 4),
            ),
            (
                -1,
                R(3, 2),
                R(13, 2),
                R(-13, 4),
                -1,
                R(-9, 2),
                3,
                R(3, 2),
                R(3, 4),
                R(9, 4),
                6,
                R(27, 8),
                -2,
                R(9, 2),
                R(-39, 4),
            ),
        ),
        (0, 0, R(-1, 4)) + (0,) * 12,
    )


def gao_quartic() -> PolynomialMap:
    """Return the three-dimensional map of geometric degree four.

    From arXiv:2608.00222, Section 3.5.

    Determinant ``2``, so a Keller map and not normalized. Component degrees 4,
    11 and 12. The second source map this project has, and the only one whose
    collision does not live over the rationals: two of its three points are
    over ``Q(sqrt(-23))``.

    Somebody else's mathematics: Gao, *Keller maps of arbitrary geometric
    degree*, arXiv:2608.00222v1, Section 3.5. Licensed CC BY 4.0,
    https://creativecommons.org/licenses/by/4.0/.

    Changed from the source: transcribed into SymPy from the closed form the
    paper gives, with the two quotients carried out. The mathematics is not
    altered, the presentation is. CC BY asks for attribution, a link and an
    indication of changes, and this repository said for a while that it asks
    for attribution alone.

    ``docs/references.md`` records what Theorem 3.5 claims, what was recomputed
    here, and what agreement with it does and does not establish.

    Written as the paper writes it. ``p``, ``q`` and ``gamma`` are its closed
    form, and the two quotients are its own: the paper states the divisibility
    and this transcribes it rather than the expanded result. That the divisions
    come out exact is the paper's claim and this project's check, so ``cancel``
    stands where it can fail and not in a comment.

    The name says geometric degree and not dimension, unlike ``bcw17`` and
    ``alpoege15``. Those are reductions and their dimension is what
    distinguishes them; the paper carries two maps in three variables, and the
    geometric degree, four here and three in Section 3.4, is what tells them apart.
    """
    first, second, third = sp.symbols("x y z")

    gamma = 2 - 4 * first * second - first**2 * third
    carrier = gamma * (1 + first * second)
    cubic = carrier**3 - 6 * carrier**2 + 6 * carrier
    quartic = R(3, 8) * carrier**4 - 2 * carrier**3 + R(3, 2) * carrier**2

    return PolynomialMap(
        (first, second, third),
        tuple(
            sp.cancel(sp.together(component))
            for component in (
                gamma * first,
                (cubic + 2 * gamma) / (gamma * first),
                (quartic + gamma * carrier) / (gamma * first) ** 2,
            )
        ),
    )


def gao_quartic_collision() -> Collision:
    """Return the three points ``gao_quartic`` sends to one image.

    Two of them are over ``Q(sqrt(-23))``, which is what makes this collision
    different from every other in this repository. It is inside what
    ``kellermap.canonical`` claims to decide, a quadratic extension; the module
    says where that claim stops.

    Somebody else's mathematics, like the map. The points are the datum and the
    image is computed from them, which is what ``Collision.at`` does and what
    makes it a claim this library can be wrong about. The paper's own sample
    point is the first of the three.
    """
    root = sp.sqrt(23) * sp.I

    return Collision.at(
        gao_quartic(),
        (
            (0, R(1, 2), R(-1, 4)),
            (2 * root / 23, R(1, 6) + 2 * root / 3, R(-253, 6) + root / 3),
            (-2 * root / 23, R(1, 6) - 2 * root / 3, R(-253, 6) - root / 3),
        ),
    )
