"""Reading a displacement by degree, for Section 4 and for Theorem 2.1(b).

Both steps take a displacement apart by total degree and put it back together
differently. The second scales every part by one parameter, ``X + T N``, which
is how UNI-9 reaches the nilpotence of a Jacobian without a matrix power. The
third scales each part by the power of the parameter its own degree is short
of, ``N_(1) T^2 + N_(2) T + N_(3)``, which is the homogenization itself. The
two constructions differ in the exponents and in nothing else, so what they
share lives here rather than in either of them.

``scaled_displacement`` is the first, and it is also the shape the second is
built from. ``homogeneous_part`` is what both read.

``squared_terms`` reads the same displacement by degree in each single
variable rather than by total degree. That is the other half of Theorem
2.1(b), and it is here for the reason the two constructions above are: three
places need it and none of them owns it. HOM-12 asks it of a target, UNT-12
asks it of a source, and the walk that reaches the property measures itself
by it.

See ``docs/contracts.md``: UNI-9 uses the first construction, HOM-1 the
second, HOM-3 the first again on the other side of the step, and HOM-11,
HOM-12 and UNT-12 the third.
"""

from __future__ import annotations

from collections.abc import Iterable

import sympy as sp
from sympy.polys.rings import PolyElement

from ..polynomial_map import PolynomialMap


def homogeneous_part(polynomial: PolyElement, degree: int) -> PolyElement:
    """Return the part of ``polynomial`` homogeneous of ``degree``.

    Total degree in the generators of the ring, so a parameter of the
    coefficient domain does not count towards it. That is the reading DOM-2
    fixes and the one ``PolynomialMap.degree`` uses: ``T x`` over ``k[T]`` is
    linear in ``x``. Reading the parameter as a variable would put a term in
    the wrong part and, in the homogenization, lift it by the wrong power.
    """
    ring = polynomial.ring
    terms = [
        (monomial, coefficient)
        for monomial, coefficient in polynomial.iterterms()
        if sum(monomial) == degree
    ]

    return ring.from_terms(terms) if terms else ring.zero


def squared_terms(
    polynomial_map: PolynomialMap,
    exempt: Iterable[sp.Symbol] = (),
) -> tuple[tuple[int, tuple[int, ...]], ...]:
    """Return every term of the displacement that squares a variable.

    One pair per term: the index of the component and the exponent vector.
    Empty exactly when the map is multi-affine, which is what Theorem 2.1(b)
    asks for besides the cubic homogeneous form.

    ``exempt`` names the variables that do not count. The theorem exempts the
    homogenizing parameter and nothing else -- not the coordinates the earlier
    stages buy -- so HOM-12 passes the one generator ``HomogenizationStep``
    introduces and UNT-12 passes none.

    The order is the ring's, made total by sorting, so that a walk over the
    result does not depend on which monomial a dictionary offered first.
    """
    # Materialized once. ``set(exempt)`` inside the comprehension is rebuilt
    # per generator, and a one-shot iterable is empty from the second onward:
    # an audit of ``0.7.0rc1`` passed a generator and every variable counted.
    # The signature promises ``Iterable`` and this is what honours it.
    spared = set(exempt)
    positions = {
        index
        for index, variable in enumerate(polynomial_map.variables)
        if variable in spared
    }

    found = []
    for index, component in enumerate(polynomial_map.displacement().to_polynomials()):
        for monomial in sorted(component.itermonoms()):
            if any(
                exponent >= 2
                for position, exponent in enumerate(monomial)
                if position not in positions
            ):
                found.append((index, monomial))

    return tuple(found)


def scaled_displacement(polynomial_map: PolynomialMap) -> PolynomialMap:
    """Return ``(X + T (F - X), T)``, one coordinate wider than ``F``.

    Its Jacobian is block triangular, with ``I + T J(N)`` above and a one in
    the corner, so its determinant is ``det(I + T J(N))``. That determinant
    being one says that the characteristic polynomial of ``J(N)`` is
    ``lambda^m``, and Cayley-Hamilton over a commutative ring then gives
    ``J(N)^m = 0``.

    So this is how both steps ask whether a displacement has nilpotent
    Jacobian: one determinant, in place of a matrix power that does not
    terminate at the dimensions this milestone works in.

    The fresh coordinate is named by the same policy as everything else, so it
    can collide neither with a coordinate nor with a parameter of the
    coefficient domain.
    """
    widened = polynomial_map.extend(1)
    ring = widened.ring
    parameter = ring.gens[-1]

    displacement = widened.displacement().to_polynomials()

    return PolynomialMap.from_ring(
        ring,
        tuple(
            generator + parameter * component
            for generator, component in zip(ring.gens, displacement, strict=True)
        )[:-1]
        + (parameter,),
    )
