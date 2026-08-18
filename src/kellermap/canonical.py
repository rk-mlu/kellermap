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
what the coefficient domains of this project were until 0.5: ``QQ``,
``QQ[T]``, ``QQ(T)`` and their nestings.

It is not enough for a point over a number field, and that was measured rather
than foreseen. ``sqrt(2) + sqrt(3)`` and ``sqrt(5 + 2*sqrt(6))`` are the same
number, and ``cancel`` treats a radical as an atom and reports them as two.
Both directions of that are serious. COL-4 says a ``Collision`` whose points
coincide cannot be built, and one could be: two spellings of one point passed
the constructor, so the counterexample it certifies would have had two
"distinct" preimages that are one. And COL-3 rejected a correct image written
as a nested radical, which is the false negative its own wording warns about
one class of number earlier.

``sqrtdenest(expand(...))`` runs first since 0.5 and closes that case. What it
claims is therefore:

* rational functions, decided by ``cancel`` as before;
* square roots, including nested ones, denested by ``sqrtdenest``.

What it does not claim, and this is the honest boundary rather than a defect:

* a cube root or any radical of higher index. ``sqrtdenest`` denests square
  roots and nothing else, so two spellings of one such number may still be
  reported as two;
* an algebraic number of degree above two in general.

Gao's map, which is why this was measured, has a collision over ``Q(sqrt(-23))``
-- a quadratic extension, inside what is claimed. A later example over a cubic
extension would need this decided again, and the answer would be a measurement
and not this sentence. ``sp.minimal_polynomial`` is a decision procedure for
algebraic numbers and was measured: it costs twenty times ``cancel`` and does
not answer for ``k(T)`` at all, so it would have to sit behind a case
distinction, and then the case distinction decides rather than the procedure.

The cost, measured by alternating the two on the path that transports a
collision through the eight steps of the BCW17 chain, three pairs taken back to
back: 0.032/0.034, 0.027/0.043, 0.025/0.033 seconds. Between a quarter and a
half more on that path, which is the only one where it shows; over the whole
suite the difference is not measurable. A single absolute number would not
reproduce here, so the pairs stand rather than an average.
"""

from __future__ import annotations

from typing import Any, cast

import sympy as sp


def canonical(value: sp.Expr | Any) -> sp.Expr:
    """Return the value in the normal form this package compares in.

    Applied when a coordinate enters, so that everything stored downstream is
    already comparable by ``==`` -- which is what keeps equality and hashing
    consistent with each other.

    A normal form and not an equality test, and that is why the module reads
    as it does. COL-6 ties the hash of a ``Collision`` to its equality as a
    set, so a procedure that decides ``a == b`` pairwise and produces no normal
    form would leave the two disagreeing. ``expr.equals`` and
    ``minimal_polynomial`` are both of that kind.
    """
    return cast(
        sp.Expr,
        sp.cancel(sp.together(sp.sqrtdenest(sp.expand(sp.sympify(value))))),
    )


def is_zero(value: sp.Expr | Any) -> bool:
    """Return whether the value is zero, clearing denominators first."""
    return bool(canonical(value) == 0)


def agree(left: sp.Expr | Any, right: sp.Expr | Any) -> bool:
    """Return whether two expressions denote the same value."""
    return is_zero(sp.sympify(left) - sp.sympify(right))
