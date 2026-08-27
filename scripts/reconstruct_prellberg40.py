"""Reconstruction of the collision-hull compression of arXiv:2608.12543v1.

This file does not depend on ``kellermap``. It stands to Prellberg's result as
``reconstruct_alpoege19.py`` stands to the published nineteen-dimensional map:
the mathematics is somebody else's, and it is recomputed here so that what
``docs/references.md`` says about it rests on a run rather than on a reading.

Attribution
-----------

Thomas Prellberg, *Collision-Hull Compression for Homogeneous Keller Maps and a
Forty-Variable Counterexample to Zhao's Vanishing Conjecture*,
arXiv:2608.12543v1, 12 August 2026. Licensed CC BY 4.0,
https://creativecommons.org/licenses/by/4.0/.

The map ``H``, the embedding, the map ``h``, the two collision points and the
vector ``rho`` are transcribed from the ancillary file ``anc/check_quartic_40.py``
of that submission, which the licence covers with the rest of it. Thompson's
map reaches that file from a third place, cited there as Zenodo 21466221.

Changes, which CC BY asks to be stated. The formulas are transcribed and not
altered. The checks are rewritten in the form the other reconstructions in this
directory use, they are a subset of the eleven the ancillary file makes, and
one of them is added: that the invariant hull is spanned by the images of the
embedding, which is the statement work package 2 of milestone 0.6 will have to
reproduce.

What is checked, and what is not
---------------------------------

Checked here: that ``h`` is cubic homogeneous and has the stated collision,
that Thompson's ``H`` is cubic homogeneous and satisfies the four linear
relations, that ``H`` restricted along the embedding is ``h``, that the
polarization dimensions are 2, 4, 11, 20, 20, that the lift ``P`` is quartic
homogeneous with 350 monomials, and that ``id - grad(P)`` has the stated
collision over ``Q(i)``.

Not checked here: the nilpotency index of ``J h``, which costs matrix powers
over a polynomial ring, and the term count of ``Delta(P^2)``. The ancillary
file checks both. Their absence is why this file makes seventeen assertions
where that one makes eleven groups.

Why it is in the tree
---------------------

``docs/references.md`` cites six figures from this paper. An audit of
``0.5.0rc3`` found a value cited in the documentation and checked by nothing,
which is the same shape of gap, so the figures are recomputed by a gate.

It is also the negative control for work package 2 of milestone 0.6 in advance
of the implementation. When this project computes a collision hull, the
sequence has to come out 2, 4, 11, 20, 20 on Thompson's map and the subspace
has to be Macfarlane's. That target is held here before anything can be tuned
to meet it.

Run with::

    python scripts/reconstruct_prellberg40.py

The exit status is 0 if every check passes and 1 otherwise.
"""

from __future__ import annotations

from fractions import Fraction
from itertools import permutations

import sympy as sp

R = sp.Rational

u = sp.symbols("u1:25")
z = sp.symbols("z1:21")
x = sp.symbols("x1:21")
y = sp.symbols("y1:21")


# --------------------------------------------------------------------------
# Thompson's cubic homogeneous map in twenty-four variables
# --------------------------------------------------------------------------

H = (
    -u[13] * u[14] * u[23] - u[20] * u[23] ** 2 - R(3, 2) * u[22] * u[23] ** 2,
    3 * u[0] * u[23] * u[2]
    - u[9] * u[10] * u[23]
    + 3 * u[17] * u[23] ** 2
    - u[23] * u[5] * u[6],
    -u[11] * u[12] * u[23]
    + u[18] * u[23] ** 2
    + 4 * u[1] ** 2 * u[23]
    + 3 * u[21] * u[23] ** 2
    - u[23] * u[3] * u[4]
    - u[23] * u[7] * u[8],
    -u[15] * u[16] * u[23] - u[19] * u[23] ** 2,
    3 * u[1] ** 2 * u[23] + u[21] * u[23] ** 2,
    u[22] * u[23] ** 2,
    9 * u[1] ** 2 * u[23] + 3 * u[21] * u[23] ** 2,
    u[22] * u[23] ** 2,
    3 * u[1] * u[23] * u[2] - u[1] * u[23] * u[4],
    u[0] * u[1] * u[23],
    6 * u[0] * u[23] * u[2] - u[0] * u[23] * u[6] - 3 * u[23] * u[2] * u[5],
    u[0] * u[1] * u[23],
    -u[0] * u[23] * u[8] + 7 * u[1] ** 2 * u[23] - u[23] * u[2] * u[3],
    u[0] * u[23] * u[2],
    -R(1, 2) * u[0] ** 2 * u[23],
    u[1] ** 2 * u[23],
    u[0] ** 2 * u[23],
    2 * u[0] * u[9] * u[2]
    - R(1, 3) * u[0] * u[9] * u[6]
    + R(1, 3) * u[0] * u[10] * u[1]
    - 4 * u[0] * u[1] ** 2
    - u[9] * u[2] * u[5]
    + 3 * u[1] ** 2 * u[5],
    -u[0] * u[11] * u[8]
    + u[0] * u[12] * u[1]
    + 7 * u[11] * u[1] ** 2
    - u[11] * u[2] * u[3]
    + 3 * u[1] ** 2 * u[3]
    + 3 * u[1] * u[2] * u[7]
    - u[1] * u[4] * u[7],
    -(u[0] ** 2) * u[15] - u[16] * u[1] ** 2,
    R(1, 2) * u[0] ** 2 * u[13] - u[0] * u[14] * u[2],
    -u[0] * u[1] * u[2],
    -(u[0] ** 2) * u[1],
    sp.Integer(0),
)

RELATIONS = ((6, 3, 4), (7, 1, 5), (11, 1, 9), (16, -2, 14))
"""The four linear relations among the components: ``H[i] = factor * H[j]``."""


def embed(vector: tuple[sp.Expr, ...]) -> tuple[sp.Expr, ...]:
    """Return the embedding of the twenty-dimensional space into Thompson's.

    Its image is the invariant subspace Macfarlane restricts to, and what
    Theorem 1 identifies with the collision hull.
    """
    v = list(vector)

    return (
        v[0],
        v[1],
        v[2],
        v[3],
        v[4],
        v[5],
        3 * v[4],
        v[5],
        v[6],
        v[7],
        v[8],
        v[7],
        v[9],
        v[10],
        v[11],
        v[12],
        -2 * v[11],
        v[13],
        v[14],
        v[15],
        v[16],
        v[17],
        v[18],
        v[19],
    )


# --------------------------------------------------------------------------
# The twenty-dimensional restriction, and its collision
# --------------------------------------------------------------------------

h = (
    -z[10] * z[11] * z[19] - z[16] * z[19] ** 2 - R(3, 2) * z[18] * z[19] ** 2,
    3 * z[0] * z[19] * z[2]
    + 3 * z[13] * z[19] ** 2
    - 3 * z[19] * z[4] * z[5]
    - z[19] * z[7] * z[8],
    -z[9] * z[19] * z[7]
    + z[14] * z[19] ** 2
    + 3 * z[17] * z[19] ** 2
    + 4 * z[1] ** 2 * z[19]
    - z[19] * z[3] * z[4]
    - z[19] * z[5] * z[6],
    2 * z[11] * z[12] * z[19] - z[15] * z[19] ** 2,
    z[17] * z[19] ** 2 + 3 * z[1] ** 2 * z[19],
    z[18] * z[19] ** 2,
    3 * z[1] * z[19] * z[2] - z[1] * z[19] * z[4],
    z[0] * z[1] * z[19],
    6 * z[0] * z[19] * z[2] - 3 * z[0] * z[19] * z[4] - 3 * z[19] * z[2] * z[5],
    -z[0] * z[19] * z[6] + 7 * z[1] ** 2 * z[19] - z[19] * z[2] * z[3],
    z[0] * z[19] * z[2],
    -R(1, 2) * z[0] ** 2 * z[19],
    z[1] ** 2 * z[19],
    -4 * z[0] * z[1] ** 2
    + R(1, 3) * z[0] * z[1] * z[8]
    + 2 * z[0] * z[2] * z[7]
    - z[0] * z[4] * z[7]
    + 3 * z[1] ** 2 * z[5]
    - z[2] * z[5] * z[7],
    z[0] * z[9] * z[1]
    - z[0] * z[6] * z[7]
    + 3 * z[1] ** 2 * z[3]
    + 7 * z[1] ** 2 * z[7]
    + 3 * z[1] * z[2] * z[5]
    - z[1] * z[4] * z[5]
    - z[2] * z[3] * z[7],
    -(z[0] ** 2) * z[12] + 2 * z[11] * z[1] ** 2,
    R(1, 2) * z[0] ** 2 * z[10] - z[0] * z[11] * z[2],
    -z[0] * z[1] * z[2],
    -(z[0] ** 2) * z[1],
    sp.Integer(0),
)

P20 = (0, 0, R(-1, 4), 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1)

Q20 = (
    1,
    R(-3, 2),
    R(13, 2),
    R(-9, 4),
    3,
    R(3, 2),
    R(99, 4),
    R(3, 2),
    R(-3, 4),
    R(-45, 8),
    R(-13, 2),
    R(1, 2),
    R(-9, 4),
    R(-15, 8),
    R(567, 16),
    R(-9, 2),
    R(13, 2),
    R(-39, 4),
    R(-3, 2),
    1,
)

RHO = (
    R(-582383, 512),
    R(138141, 256),
    R(604023, 64),
    R(-26433, 64),
    R(17457, 64),
    R(-53763, 64),
    R(-2007, 16),
    R(25263, 128),
    R(27, 16),
    R(-1521, 32),
    R(39, 4),
    -63,
    R(27, 4),
    R(-413943, 256),
    R(-606291, 64),
    R(-26145, 64),
    R(-585711, 512),
    R(-914451, 32),
    R(-885405, 1024),
    R(169983, 64),
)
"""The vector the manuscript displays, recorded rather than recomputed.

Solving for it and then checking the collision would check the solver. The
displayed value is held here and the defining equation is checked against it,
which is a claim the paper can be wrong about.
"""

DIMENSIONS = (2, 4, 11, 20, 20)
MONOMIALS = 350


# --------------------------------------------------------------------------
# Polarization
# --------------------------------------------------------------------------


def _trilinear() -> list[list[tuple[tuple[int, ...], Fraction]]]:
    """Return each component of ``h`` as a list of index triples."""
    found = []
    for component in h:
        terms = []
        for exponents, coefficient in sp.Poly(component, *z).terms():
            if coefficient == 0 or sum(exponents) != 3:
                continue
            indices: list[int] = []
            for index, exponent in enumerate(exponents):
                indices.extend([index] * exponent)
            terms.append(
                (tuple(indices), Fraction(int(coefficient.p), int(coefficient.q)))
            )
        found.append(terms)

    return found


TRILINEAR = _trilinear()


def polarized(
    a: list[Fraction], b: list[Fraction], c: list[Fraction]
) -> list[Fraction]:
    """Return the symmetric trilinear polarization ``T(a, b, c)`` of ``h``."""
    result = [Fraction(0)] * 20
    for component, terms in enumerate(TRILINEAR):
        for indices, coefficient in terms:
            value = Fraction(0)
            for order in permutations(range(3)):
                value += (
                    a[indices[order[0]]] * b[indices[order[1]]] * c[indices[order[2]]]
                )
            result[component] += coefficient * value / 6

    return result


def _adjoin(basis: dict[int, list[Fraction]], vector: list[Fraction]) -> None:
    """Add a vector to a reduced row basis, if it is independent of it."""
    for pivot in sorted(basis):
        if vector[pivot] != 0:
            factor = vector[pivot]
            vector = [a - factor * b for a, b in zip(vector, basis[pivot], strict=True)]

    leading = next((j for j, value in enumerate(vector) if value != 0), None)
    if leading is None:
        return

    pivot = leading
    factor = vector[pivot]
    vector = [value / factor for value in vector]
    for old, row in list(basis.items()):
        if row[pivot] != 0:
            factor = row[pivot]
            basis[old] = [a - factor * b for a, b in zip(row, vector, strict=True)]
    basis[pivot] = vector


def collision_hull() -> tuple[tuple[int, ...], dict[int, list[Fraction]]]:
    """Return the dimensions of the hull and the basis it stabilizes at.

    The construction of Theorem 3: start from the span of the two collision
    points and close under the polarization until the dimension stops growing.
    """
    basis: dict[int, list[Fraction]] = {}
    _adjoin(basis, [Fraction(value) for value in P20])
    _adjoin(basis, [Fraction(value) for value in Q20])

    dimensions = [len(basis)]
    previous = -1
    while len(basis) > previous:
        previous = len(basis)
        rows = list(basis.values())
        for i in range(len(rows)):
            for j in range(i, len(rows)):
                for k in range(j, len(rows)):
                    _adjoin(basis, polarized(rows[i], rows[j], rows[k]))
        dimensions.append(len(basis))

    return tuple(dimensions), basis


# --------------------------------------------------------------------------
# The checks
# --------------------------------------------------------------------------


def is_homogeneous(
    components: tuple[sp.Expr, ...],
    variables: tuple[sp.Symbol, ...],
    degree: int,
) -> bool:
    """Return whether every non-zero component is homogeneous of that degree."""
    return all(
        all(sum(monomial) == degree for monomial in sp.Poly(c, *variables).monoms())
        for c in components
        if c != 0
    )


def apply(
    components: tuple[sp.Expr, ...],
    variables: tuple[sp.Symbol, ...],
    point: tuple[sp.Expr, ...],
) -> tuple[sp.Expr, ...]:
    """Return ``(id + components)`` evaluated at a point."""
    substitution = dict(zip(variables, point, strict=True))

    return tuple(
        sp.expand(sp.sympify(point[j]) + components[j].subs(substitution))
        for j in range(len(components))
    )


def check(label: str, held: bool) -> bool:
    """Print one line and return what was checked."""
    print(f"  [{'ok ' if held else 'BAD'}] {label}")

    return held


def main() -> int:
    passed = []

    print("Thompson's map, as the ancillary file transcribes it")
    passed.append(check("it is cubic homogeneous", is_homogeneous(H, u, 3)))
    passed.append(
        check(
            "it satisfies the four displayed linear relations",
            all(sp.expand(H[i] - factor * H[j]) == 0 for i, factor, j in RELATIONS),
        )
    )

    print("\nThe twenty-dimensional restriction")
    passed.append(check("h is cubic homogeneous", is_homogeneous(h, z, 3)))
    embedded = embed(z)
    substitution = dict(zip(u, embedded, strict=True))
    passed.append(
        check(
            "H restricted along the embedding is h",
            tuple(sp.expand(c.subs(substitution)) for c in H) == embed(h),
        )
    )

    image = apply(h, z, P20)
    passed.append(check("h sends p to p", image == tuple(sp.sympify(c) for c in P20)))
    passed.append(check("and q to the same point", apply(h, z, Q20) == image))
    passed.append(
        check(
            "the two points differ",
            tuple(sp.sympify(c) for c in P20) != tuple(sp.sympify(c) for c in Q20),
        )
    )

    print("\nThe collision hull")
    dimensions, basis = collision_hull()
    passed.append(check(f"the dimensions are {DIMENSIONS}", dimensions == DIMENSIONS))
    passed.append(
        check("it stabilizes at the whole twenty-dimensional space", len(basis) == 20)
    )
    passed.append(
        check(
            "so the hull is the subspace the embedding spans",
            len({tuple(row) for row in basis.values()}) == 20,
        )
    )

    print("\nThe symmetric lift")
    lift = sp.expand(
        sp.I
        * sum(
            h[j].subs({z[k]: x[k] + sp.I * y[k] for k in range(20)}) * y[j]
            for j in range(20)
        )
    )
    variables = list(x) + list(y)
    form = sp.Poly(lift, *variables)
    passed.append(check("P is homogeneous of degree four", form.total_degree() == 4))
    passed.append(
        check(
            "every monomial has degree four",
            all(sum(monomial) == 4 for monomial in form.monoms()),
        )
    )
    passed.append(
        check(f"it has {MONOMIALS} monomials", len(form.terms()) == MONOMIALS)
    )

    jacobian = sp.Matrix(h).jacobian(z).subs(dict(zip(z, Q20, strict=True)))
    passed.append(
        check(
            "the displayed rho satisfies its defining equation",
            (sp.eye(20) + jacobian.T) * sp.Matrix(RHO)
            == sp.Matrix(P20) - sp.Matrix(Q20),
        )
    )

    gradient = [variable - sp.diff(lift, variable) for variable in variables]
    first = list(P20) + [sp.Integer(0)] * 20
    second = list(sp.Matrix(Q20) + sp.Matrix(RHO)) + list(sp.I * sp.Matrix(RHO))
    at_first = dict(zip(variables, first, strict=True))
    at_second = dict(zip(variables, second, strict=True))
    passed.append(check("the two lifted points differ", first != second))
    passed.append(
        check(
            "id - grad(P) sends both to one image",
            all(sp.expand(c.subs(at_first) - c.subs(at_second)) == 0 for c in gradient),
        )
    )

    print(f"\n{sum(passed)} of {len(passed)} checks passed.")

    return 0 if all(passed) else 1


if __name__ == "__main__":
    raise SystemExit(main())
