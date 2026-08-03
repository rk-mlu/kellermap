"""What "the same value" means for expressions outside a polynomial ring.

Almost everything in this package is compared inside a ``PolyRing``, where the
question does not arise: the domain canonicalizes on the way in, so
``(T^2 - 1)/(T - 1)`` is already ``T + 1`` by the time anything looks at it,
and two equal elements are the same object in the same normal form.

``Collision`` is the exception, and it is the exception on purpose. Its
coordinates are points, not polynomials; they belong to the coefficient field
rather than to the ring, and forcing them through a domain would tie a
collision to one map, which COL-5 exists to prevent. So they arrive as SymPy
expressions and are compared as expressions -- and ``expand`` is the wrong tool
for that, because it does not clear a denominator. Over ``k(T)`` it reports two
spellings of one point as two points, which is COL-4 read backwards.

``cancel(together(...))`` decides equality for rational functions, which is
exactly what the coefficient domains of this project are: ``QQ``, ``QQ[T]``,
``QQ(T)`` and their nestings. It is not a general simplifier and does not
pretend to be one; an expression outside that class is outside what this
package claims to handle.

The cost is about five microseconds per comparison, so there is no reason for
a second, cheaper answer to the same question elsewhere.
"""

from __future__ import annotations

from typing import Any, cast

import sympy as sp


def canonical(value: sp.Expr | Any) -> sp.Expr:
    """Return the value in the normal form this package compares in.

    Applied when a coordinate enters, so that everything stored downstream is
    already comparable by ``==`` -- which is what keeps equality and hashing
    consistent with each other.
    """
    return cast(sp.Expr, sp.cancel(sp.together(sp.sympify(value))))


def is_zero(value: sp.Expr | Any) -> bool:
    """Return whether the value is zero, clearing denominators first."""
    return bool(canonical(value) == 0)


def agree(left: sp.Expr | Any, right: sp.Expr | Any) -> bool:
    """Return whether two expressions denote the same value."""
    return is_zero(sp.sympify(left) - sp.sympify(right))
