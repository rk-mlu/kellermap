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

from .polynomial_map import PolynomialMap

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
