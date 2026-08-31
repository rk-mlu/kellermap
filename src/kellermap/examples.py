"""Keller maps this repository writes out more than once.

Two criteria decide what is here, and both are counted rather than judged. A
map belongs in this module if it is written out in more than one place, and if
it is a Keller map -- its Jacobian determinant is a non-zero constant. Work
package 8 of milestone 0.5 counted the tree against both, and
``docs/roadmap.md`` records what it found then, which is fewer maps than stand
here now. The figures are not repeated here: a
count in a docstring that nothing recomputes goes stale without saying so, and
this one had.

The maps that are repeated and are *not* Keller maps stay where they are used.
They are written the way they are *because* they are not Keller maps: they
exercise degree growth, non-injectivity and a non-constant determinant, and a
module named ``examples`` beside a library about Keller maps would say
otherwise about them.

Provenance, and this module has four kinds of it.

``alpoege`` and ``gao_quartic`` are the two published counterexamples this
project starts from. ``thompson24_homogeneous`` and ``spacerat11`` are
published reductions of the first one, taken from the papers that print them.
All four are somebody else's mathematics, each docstring names the source and
its licence, and ``docs/provenance.md`` sorts them and says what the agreement
of a chain with one of them does and does not establish.

``alpoege13`` and ``alpoege12`` are reductions this project found, of the
published map. Everything else was written for this project's own tests and
documentation.

Distributing a map does not change who computed it, so
``Provenance.SUPPLIED``, BCW-9 and SEA-5 mean here exactly what they mean
anywhere else. Where a source could not be distributed, it is not here:
``tests/data.py`` holds the data whose terms could not be established, and the
source archive excludes it.

Functions rather than constants, so that importing ``kellermap`` does not build
maps nobody asked for. Each returns the map over the domain its coefficients
imply: ``ZZ`` for most of them, ``QQ`` where a reduction carries rational
coefficients, and ``ZZ[T]`` for the two that take a parameter. Use
``over_field`` where a field is needed.

A name carries the dimension, and the stage where that is not degree three.
``alpoege19`` is degree three in nineteen variables and the compression of
milestone 0.6 reaches a cubic homogeneous map in nineteen from another route,
so a bare dimension would name two different kinds of thing.

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

    Somebody else's mathematics: Shuhong Gao, *Counterexamples to the Jacobian
    conjecture in dimensions greater than two*, arXiv:2608.00222v1, Section
    3.5. Licensed CC BY 4.0, https://creativecommons.org/licenses/by/4.0/.

    The title is the paper's own. This docstring called it *Keller maps of
    arbitrary geometric degree* until an external audit checked it against the
    arXiv listing; that phrase was assembled from the abstract and is not a
    title. Attribution is what the licence asks for first, so a wrong one is
    worse here than a wrong word elsewhere.

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


def spacerat11() -> PolynomialMap:
    """Return the published eleven-variable cubic reduction of Alpoege's map.

    Degree three, determinant -2, and it carries Alpoege's collision. The
    smallest dimension at degree three this project knows of, one below
    ``alpoege12``.

    Not normalized: the linear part of its displacement is not zero and the
    determinant is not one, so ``UNI-2`` refuses it and ``LinearStep.normalize``
    comes first, as for ``alpoege13``. That is not a defect of the
    transcription. The map stands in Alpoege's own coordinates, which is also
    where a chain reaches it.

    Third-party. Transcribed from Section 6 of arXiv:2608.05392v1, licensed
    CC BY 4.0, https://creativecommons.org/licenses/by/4.0/, where it is
    printed as ``Phi``. That paper cites a GitHub gist by Spacerat, dated the
    day of Alpoege's announcement, as the source of the calculation, and the
    gist carries no licence, so every value here comes from the paper. Changes:
    the generators are renamed and the components reordered to the order the
    generators induce. The formulas are not altered.

    The name follows the convention this module uses for third-party maps,
    author and dimension, and the author is the name the literature attributes
    it to. ``docs/references.md`` says what is known about that attribution and
    what is not.

    This map is reachable from ``alpoege()`` by six ``BCWStep``s, which
    ``scripts/reconstruct_spacerat11.py`` replays. It is in this module all the
    same: the chain was found by ``peel``, which is given the target, so
    deriving the map needs the map.
    """
    x = sp.symbols("x1:12")

    return PolynomialMap(
        x,
        (
            3 * x[0] * x[1] * x[2]
            + x[0] * x[1] * x[8]
            - 3 * x[1] ** 2 * x[3]
            + 7 * x[1] ** 2 * x[6]
            + 4 * x[1] ** 2
            - x[2] * x[3] * x[6]
            - 2 * x[2] * x[3]
            + x[2] * x[6] ** 2
            + x[2]
            - x[3] * x[5]
            - x[5] * x[6] ** 2
            - x[6] * x[8],
            12 * x[0] * x[1] ** 2
            + x[0] * x[1] * x[7]
            + 3 * x[0] * x[2]
            - 3 * x[0] * x[5] * x[6]
            - 3 * x[1] ** 2 * x[4]
            + x[1]
            - x[2] * x[4] * x[6]
            - 2 * x[2] * x[4]
            - x[4] * x[5]
            - x[6] * x[7],
            x[0] ** 2 * x[10]
            - 3 * x[0] ** 2 * x[1]
            - x[0] * x[9] * x[2]
            + 2 * x[0]
            - x[9] * x[10],
            2 * x[0] * x[1] * x[6] + x[3] - x[6] ** 2,
            3 * x[0] ** 2 * x[1] + x[4],
            x[0] * x[1] * x[2] + 3 * x[1] ** 2 + 2 * x[2] + x[5],
            -x[0] * x[1] + x[6],
            3 * x[0] * x[5] + x[2] * x[4] + x[7],
            -x[0] * x[1] * x[2]
            + x[0] * x[1] * x[5]
            - 7 * x[1] ** 2
            + x[2] * x[3]
            - x[2] * x[6]
            + x[5] * x[6]
            + x[8],
            -(x[0] ** 2) + x[9],
            x[0] * x[2] + x[10],
        ),
    )


def spacerat11_collision() -> Collision:
    """Return the three points ``spacerat11`` sends to one image.

    Printed in Section 6 of the same paper, in the same coordinates, and the
    first three of each are Alpoege's own three points. The image is computed
    from them rather than written down, as for ``alpoege13``.
    """
    return Collision.at(
        spacerat11(),
        (
            (0, 0, R(-1, 4), 0, 0, R(1, 2), 0, 0, 0, 0, 0),
            (
                1,
                R(-3, 2),
                R(13, 2),
                R(-9, 4),
                R(9, 2),
                -10,
                R(-3, 2),
                R(3, 4),
                R(-153, 8),
                1,
                R(-13, 2),
            ),
            (
                -1,
                R(3, 2),
                R(13, 2),
                R(-9, 4),
                R(-9, 2),
                -10,
                R(-3, 2),
                R(-3, 4),
                R(-153, 8),
                1,
                R(13, 2),
            ),
        ),
    )


def thompson24_homogeneous() -> PolynomialMap:
    """Return Thompson's twenty-four-variable cubic homogeneous Keller map.

    Degree three, homogeneous, determinant one, and a two-point collision whose
    image is the first of the two points. The published normal form at BCW's
    third stage, and the input the compression of milestone 0.6 is checked
    against: applied to this map with this collision, the hull has to run
    2, 4, 11, 20, 20.

    Third-party material. Transcribed from the ancillary file
    ``anc/check_quartic_40.py`` of arXiv:2608.12543v1, licensed CC BY 4.0,
    https://creativecommons.org/licenses/by/4.0/, which prints it as ``H`` and
    cites Zenodo 21466221 for it. Changes: the displacement is written as a map
    here, ``id + H``, and the generators are renamed. The formulas are not
    altered. ``docs/references.md`` records the rest.

    The name carries the stage and not only the dimension. Every other figure
    in this module is at degree three, which is BCW's first stage; this one is
    cubic homogeneous, which is the third, and ``alpoege19`` already occupies
    the number nineteen at the first. A bare dimension would read as the same
    kind of thing.

    The twenty-dimensional restriction that file also prints is *not* here. It
    is the answer the compression has to arrive at, and an answer stored beside
    the code that computes it is not a control;
    ``scripts/reconstruct_prellberg40.py`` keeps it, and the same subspace was
    found independently by Macfarlane, whose own values stay in
    ``tests/data.py`` because that repository carries no licence.
    """
    x = sp.symbols("x1:25")

    return PolynomialMap(
        x,
        (
            x[0]
            - x[13] * x[14] * x[23]
            - x[20] * x[23] ** 2
            - 3 * x[22] * x[23] ** 2 / 2,
            3 * x[0] * x[23] * x[2]
            - x[9] * x[10] * x[23]
            + 3 * x[17] * x[23] ** 2
            + x[1]
            - x[23] * x[5] * x[6],
            -x[11] * x[12] * x[23]
            + x[18] * x[23] ** 2
            + 4 * x[1] ** 2 * x[23]
            + 3 * x[21] * x[23] ** 2
            - x[23] * x[3] * x[4]
            - x[23] * x[7] * x[8]
            + x[2],
            -x[15] * x[16] * x[23] - x[19] * x[23] ** 2 + x[3],
            3 * x[1] ** 2 * x[23] + x[21] * x[23] ** 2 + x[4],
            x[22] * x[23] ** 2 + x[5],
            9 * x[1] ** 2 * x[23] + 3 * x[21] * x[23] ** 2 + x[6],
            x[22] * x[23] ** 2 + x[7],
            3 * x[1] * x[23] * x[2] - x[1] * x[23] * x[4] + x[8],
            x[0] * x[1] * x[23] + x[9],
            6 * x[0] * x[23] * x[2]
            - x[0] * x[23] * x[6]
            + x[10]
            - 3 * x[23] * x[2] * x[5],
            x[0] * x[1] * x[23] + x[11],
            -x[0] * x[23] * x[8] + x[12] + 7 * x[1] ** 2 * x[23] - x[23] * x[2] * x[3],
            x[0] * x[23] * x[2] + x[13],
            -(x[0] ** 2) * x[23] / 2 + x[14],
            x[15] + x[1] ** 2 * x[23],
            x[0] ** 2 * x[23] + x[16],
            2 * x[0] * x[9] * x[2]
            - x[0] * x[9] * x[6] / 3
            + x[0] * x[10] * x[1] / 3
            - 4 * x[0] * x[1] ** 2
            - x[9] * x[2] * x[5]
            + x[17]
            + 3 * x[1] ** 2 * x[5],
            -x[0] * x[11] * x[8]
            + x[0] * x[12] * x[1]
            + 7 * x[11] * x[1] ** 2
            - x[11] * x[2] * x[3]
            + x[18]
            + 3 * x[1] ** 2 * x[3]
            + 3 * x[1] * x[2] * x[7]
            - x[1] * x[4] * x[7],
            -(x[0] ** 2) * x[15] - x[16] * x[1] ** 2 + x[19],
            x[0] ** 2 * x[13] / 2 - x[0] * x[14] * x[2] + x[20],
            -x[0] * x[1] * x[2] + x[21],
            -(x[0] ** 2) * x[1] + x[22],
            x[23],
        ),
    )


def thompson24_homogeneous_collision() -> Collision:
    """Return the two points ``thompson24_homogeneous`` sends to one image.

    From the same file, where they are given in the twenty coordinates of the
    restriction and mapped up by the embedding. The image is computed from the
    points rather than written down, as for ``alpoege13``, and it is the first
    of them.
    """
    return Collision.at(
        thompson24_homogeneous(),
        (
            (0, 0, R(-1, 4)) + (0,) * 20 + (1,),
            (
                1,
                R(-3, 2),
                R(13, 2),
                R(-9, 4),
                3,
                R(3, 2),
                9,
                R(3, 2),
                R(99, 4),
                R(3, 2),
                R(-3, 4),
                R(3, 2),
                R(-45, 8),
                R(-13, 2),
                R(1, 2),
                R(-9, 4),
                -1,
                R(-15, 8),
                R(567, 16),
                R(-9, 2),
                R(13, 2),
                R(-39, 4),
                R(-3, 2),
                1,
            ),
        ),
    )


def alpoege12() -> PolynomialMap:
    """Return the twelve-dimensional cubic reduction of Alpoege's map.

    Degree three, determinant one, and it carries Alpoege's collision. One
    dimension below ``alpoege13``, in ten steps where that takes seven, and
    already in ``MA^1``: the linear part of its displacement is zero, so
    Section 4 applies to it without a normalization first.

    Found by an external search driver against version 0.5 of this library,
    outside the repository and using only the public API. The driver ran for
    about two hours with a beam of two thousand states per dimension and a hard
    dimension bound of twelve. It examined 404117 states, of which 396559 were
    distinct, and pruned 345074 by the beam and 79202 by the bound. A negative
    result from such a run says nothing, and this one is not negative.

    Twelve is not the smallest published dimension at degree three. Eleven was
    reached in July 2026, by a different construction, and
    ``docs/references.md`` says what that is and what it means for this map.
    No minimality and no priority is claimed here.
    """
    x = sp.symbols("x1:13")

    return PolynomialMap(
        x,
        (
            -3 * x[0] ** 2 * x[1] / 2
            + x[0] ** 2 * x[8] / 2
            + x[0] * x[11] * x[2] / 2
            + x[0]
            + x[11] * x[8] / 2,
            -3 * x[0] * x[9] * x[2]
            + 12 * x[0] * x[1] ** 2
            - 9 * x[0] * x[1] * x[3]
            - 3 * x[0] * x[1] * x[4]
            - x[0] * x[1] * x[6]
            - 6 * x[0] * x[2] * x[5]
            + 3 * x[0] * x[2]
            - 3 * x[9] * x[8]
            + 9 * x[1] * x[5] ** 2
            + x[1]
            - 9 * x[3] * x[5]
            - 3 * x[4] * x[5]
            - 3 * x[5] ** 2 * x[8]
            - x[5] * x[6],
            -x[0] * x[10] * x[2]
            + 3 * x[0] * x[1] * x[2]
            - x[0] * x[1] * x[7]
            - x[10] * x[8]
            - 7 * x[1] ** 2 * x[5]
            + 4 * x[1] ** 2
            + 6 * x[1] * x[3] * x[5]
            + x[1] * x[4] * x[5]
            + 3 * x[1] * x[5] * x[8]
            + x[2]
            - 3 * x[3] ** 2
            - x[3] * x[4]
            - x[3] * x[5] * x[8]
            - x[5] * x[7],
            x[0] * x[1] ** 2 + x[3],
            -x[0] * x[1] * x[8] - x[0] * x[2] * x[5] + x[4] - x[5] * x[8],
            x[0] * x[1] + x[5],
            -3 * x[0] * x[2] * x[5] + 6 * x[0] * x[2] - 9 * x[1] * x[5] + x[6],
            3 * x[0] * x[1] * x[2]
            - x[0] * x[2] * x[3]
            + 7 * x[1] ** 2
            - 6 * x[1] * x[3]
            - x[1] * x[4]
            + x[7],
            x[0] * x[2] + x[8],
            x[9] + x[5] ** 2,
            x[10] - 3 * x[1] * x[5] + x[3] * x[5],
            x[0] ** 2 + x[11],
        ),
    )


def alpoege12_collision() -> Collision:
    """Return the three points ``alpoege12`` sends to one image.

    Alpoege's three points, carried through the ten steps. The image is
    computed from them rather than written down, as for ``alpoege13``.
    """
    return Collision.at(
        alpoege12(),
        (
            (0, 0, R(-1, 4), 0, 0, 0, 0, 0, 0, 0, 0, 0),
            (
                1,
                R(-3, 2),
                R(13, 2),
                R(-9, 4),
                R(39, 4),
                R(3, 2),
                -30,
                R(9, 2),
                R(-13, 2),
                R(-9, 4),
                R(-27, 8),
                -1,
            ),
            (
                -1,
                R(3, 2),
                R(13, 2),
                R(9, 4),
                R(-39, 4),
                R(3, 2),
                30,
                R(9, 2),
                R(13, 2),
                R(-9, 4),
                R(27, 8),
                -1,
            ),
        ),
    )


def alpoege13() -> PolynomialMap:
    """Return the thirteen-dimensional cubic reduction of Alpoege's map.

    Degree three, determinant one, and it carries Alpoege's collision, so it is
    itself a counterexample to the Jacobian conjecture and not merely a Keller
    map. The tests compute all of that rather than assert it.

    Two dimensions below ``alpoege15`` and four below ``bcw17``, in seven steps
    where those take eight.

    The first map here that a search found rather than a person. Work package
    11 of milestone 0.5 widened what an untargeted enumerator offers to factors
    that are sums, and 11.1 ordered the offer by what a step removes;
    ``reduce_to_degree3`` then produced this chain with no target and no pool.

    What that establishes and what it does not is in ``docs/references.md``. It
    is not a claim of minimality, the search being greedy, and not of priority
    either: the literature was checked and thirteen variables at degree three
    were reached a month earlier, by another route. This docstring said the
    check was still outstanding after it had been made.
    ``scripts/reconstruct_alpoege13.py`` recomputes the chain in plain SymPy
    without this library.
    """
    x = sp.symbols("x1:14")

    return PolynomialMap(
        x,
        (
            x[0] ** 2 * x[10] / 2
            - 3 * x[0] ** 2 * x[1] / 2
            + x[0] * x[11] * x[2] / 2
            + x[0]
            + x[10] * x[11] / 2,
            -x[0] * x[9] * x[1]
            + 12 * x[0] * x[1] ** 2
            + 3 * x[0] * x[2]
            + x[0] * x[6] * x[7]
            - x[9] * x[7]
            - 9 * x[1] ** 2 * x[5]
            + x[1]
            + 3 * x[2] * x[5] * x[7]
            - 6 * x[2] * x[5]
            - x[5] * x[6],
            -x[0] * x[12] * x[2]
            + 3 * x[0] * x[1] * x[2]
            - x[0] * x[1] * x[8]
            - 3 * x[0] * x[2] * x[3]
            - x[10] * x[12]
            - x[10] * x[3] * x[7]
            + 4 * x[1] ** 2
            + 3 * x[1] * x[3] * x[7]
            - 7 * x[1] * x[3]
            + x[1] * x[4] * x[7]
            + x[2]
            - x[3] * x[4]
            - x[7] * x[8],
            x[0] * x[1] ** 2 + x[3],
            -x[0] * x[10] * x[1]
            + 3 * x[0] * x[1] ** 2
            - x[0] * x[2] * x[7]
            + 3 * x[0] * x[2]
            - x[10] * x[7]
            + 7 * x[1]
            + x[4],
            x[0] ** 2 * x[1] + x[5],
            3 * x[0] * x[1] * x[2] + 9 * x[1] ** 2 + 6 * x[2] + x[6],
            x[0] * x[1] + x[7],
            -x[0] * x[2] * x[3] - 3 * x[1] * x[3] - x[1] * x[4] + x[8],
            -x[0] * x[6] + x[9] - 3 * x[2] * x[5],
            x[0] * x[2] + x[10],
            x[0] ** 2 + x[11],
            x[12] + x[3] * x[7],
        ),
    )


def alpoege13_collision() -> Collision:
    """Return the three points ``alpoege13`` sends to one image.

    Alpoege's three points, carried through the seven steps. The image is
    computed from them, which is what ``Collision.at`` does and what makes it a
    claim this library can be wrong about.
    """
    return Collision.at(
        alpoege13(),
        (
            (0, 0, R(-1, 4), 0, 0, 0, R(3, 2), 0, 0, 0, 0, 0, 0),
            (
                1,
                R(-3, 2),
                R(13, 2),
                R(-9, 4),
                -6,
                R(3, 2),
                -30,
                R(3, 2),
                R(9, 2),
                R(-3, 4),
                R(-13, 2),
                -1,
                R(27, 8),
            ),
            (
                -1,
                R(3, 2),
                R(13, 2),
                R(9, 4),
                6,
                R(-3, 2),
                -30,
                R(3, 2),
                R(9, 2),
                R(3, 4),
                R(13, 2),
                -1,
                R(-27, 8),
            ),
        ),
    )
