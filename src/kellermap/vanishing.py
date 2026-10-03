"""A witness to Zhao's Vanishing Conjecture, as far as it can be checked.

W. Zhao, *Hessian nilpotent polynomials and the Jacobian conjecture*, Trans.
Amer. Math. Soc. 359 (2007), 249-274. For a homogeneous quartic ``P`` whose
Hessian is nilpotent, the conjecture says that ``Delta^m(P^(m+1)) = 0`` for
all large ``m``. Theorem 3, part 4, of arXiv:2608.12543v3 shows that the
symmetric lift of a cubic homogeneous Keller map with a collision is a
counterexample: the sequence does not end.

What this module checks, and what it does not
---------------------------------------------

The witness is the lift and a collision of its gradient map. Its strength
comes from those two and from the theorems, not from a computation, because no
finite computation decides the conclusion: values at finitely many ``m`` are
consistent with the conjecture. ``docs/roadmap.md`` under "Version 0.8" says
what each finite check is worth.

``verify()`` checks the lift and the collision, which can fail on supplied
data, and two consequences of the theorems that cannot fail on a lift that
verifies: the hypothesis ``Delta^m(P^m) = 0`` up to a depth, and
``Delta(P^2) != 0``. Those two are cross-checks of this library's arithmetic
against Zhao's Theorem 4.3 and Corollary 3.9. The conclusion itself, VAN-5, is
stated and not computed.

The depth is two by default. Depth three needs ``P^3``, which has more than
three million monomials at forty variables and needed about four gigabytes on
the maintainer's machine.

See ``docs/contracts.md``, VAN-1 to VAN-5.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import sympy as sp
from sympy.polys.rings import PolyElement

from .collision import Collision
from .errors import VerificationError
from .lift import SymmetricLiftStep, _degree


def laplacian(polynomial: PolyElement) -> PolyElement:
    """Return the Laplacian of ``polynomial`` in all the generators of its ring.

    One pass over the monomials: each term contributes
    ``e * (e - 1) * c * X^(a - 2 e_j)`` for every generator ``X_j`` it carries
    to an exponent ``e >= 2``. Summing second derivatives one generator at a
    time builds forty intermediate polynomials at forty variables, and this
    builds one. ``scripts/reconstruct_prellberg40.py`` takes the derivatives
    instead, without this library, so the two methods are compared on the
    forty-variable form by the gates.
    """
    ring = polynomial.ring
    zero = ring.domain.zero
    terms: dict[tuple[int, ...], Any] = {}

    for monomial, coefficient in polynomial.items():
        for position, exponent in enumerate(monomial):
            if exponent < 2:
                continue
            lowered = monomial[:position] + (exponent - 2,) + monomial[position + 1 :]
            terms[lowered] = terms.get(lowered, zero) + coefficient * (
                exponent * (exponent - 1)
            )

    return ring.from_dict({m: c for m, c in terms.items() if c})


def check_hypothesis(form: PolyElement, depth: int) -> PolyElement | None:
    """Check ``Delta^m(P^m) = 0`` for ``1 <= m <= depth``, or raise VAN-3.

    Return ``P^2`` when it was computed, so that VAN-4 does not compute it a
    second time, and ``None`` at depth one.

    A function and not a method, because on a lift that verifies the check
    cannot fail. Its negative control therefore has to hand it a form that is
    not a lift, and this is the place it can be handed one.
    """
    power = form
    square = None
    for m in range(1, depth + 1):
        if m > 1:
            power = power * form
        if m == 2:
            square = power
        value = power
        for _ in range(m):
            value = laplacian(value)
        if value:
            raise VerificationError(
                "VAN-3",
                f"Delta^{m}(P^{m}) has {len(value)} monomials and is not zero, "
                "so the Hessian of P is not nilpotent (Zhao, Theorem 4.3). A "
                "lift that verifies cannot give this; the form is not one.",
            )

    return square


def check_conclusion_at_one(
    form: PolyElement, square: PolyElement | None = None
) -> None:
    """Check ``Delta(P^2) != 0``, or raise VAN-4.

    ``square`` is ``P^2`` when the caller has it. For the same reason as
    ``check_hypothesis``, a function: on a lift with a collision it cannot
    fail, and ``(x + i y)^4`` is the form its negative control uses.
    """
    if square is None:
        square = form**2

    if not laplacian(square):
        raise VerificationError(
            "VAN-4",
            "Delta(P^2) = 0. With a nilpotent Hessian that makes z + grad(P) "
            "the inverse of z - grad(P) (Zhao, Corollary 3.9), and an injective "
            "map has no collision.",
        )


@dataclass(frozen=True, eq=False)
class VanishingWitness:
    """The gradient form of a lift, with a collision of its gradient map.

    Parameters
    ----------
    lift
        A ``SymmetricLiftStep`` of a cubic homogeneous Keller map. VAN-1.
    collision
        A collision of ``lift.target``, which is ``id - grad(P)``. VAN-2.
        ``lift.transport`` produces one, and any other is accepted as well.
    depth
        How far VAN-3 checks the hypothesis, from one to the number of
        variables. Two by default; three is affordable on a large machine and
        ``docs/roadmap.md`` has the figures.

    The witness is not a step. It changes no map, so it has no ``transport``,
    no ``filtration_level`` and no provenance of its own. ``form`` is derived
    from the lift and not stored.
    """

    lift: SymmetricLiftStep
    collision: Collision
    depth: int = 2
    _verified: bool = field(default=False, init=False, repr=False)

    def __post_init__(self) -> None:
        if not isinstance(self.lift, SymmetricLiftStep):
            raise TypeError("The lift must be a SymmetricLiftStep.")
        if not isinstance(self.collision, Collision):
            raise TypeError("The collision must be a Collision.")
        if isinstance(self.depth, bool) or not isinstance(self.depth, int):
            raise TypeError("The depth must be an integer.")

        variables = self.lift.target.dimension
        if not 1 <= self.depth <= variables:
            raise ValueError(
                f"The depth is {self.depth}. VAN-3 checks Delta^m(P^m) = 0 for "
                f"m from one to the depth, so a depth below one checks nothing, "
                f"and above the {variables} variables of the lift it checks "
                "nothing that depth "
                f"{variables} does not (Zhao, Theorem 4.3)."
            )

    @property
    def form(self) -> sp.Expr:
        """Return ``P``, the form whose gradient the lift's target is."""
        return self.lift.form

    def verify(self) -> None:
        """Check VAN-1 to VAN-4, or raise. VAN-5 is stated and not checked."""
        if self._verified:
            return

        self._verify_lift()
        self._verify_collision()

        form = self.lift._form()  # noqa: SLF001
        square = check_hypothesis(form, self.depth)
        check_conclusion_at_one(form, square)

        object.__setattr__(self, "_verified", True)

    def _verify_lift(self) -> None:
        """VAN-1: the lift verifies, and its source is cubic."""
        try:
            self.lift.verify()
        except VerificationError as failure:
            raise VerificationError(
                "VAN-1",
                f"The lift does not verify: {failure.obligation} failed. "
                f"{failure.message}",
            ) from failure

        degree = _degree(self.lift.source)
        if degree != 3:
            raise VerificationError(
                "VAN-1",
                f"The source of the lift has degree {degree}, so the form has "
                f"degree {degree + 1}. Part 4 of Theorem 3 and Zhao's "
                "conjecture are about the quartic a cubic source gives.",
            )

    def _verify_collision(self) -> None:
        """VAN-2: the collision is one of ``id - grad(P)``."""
        try:
            self.collision.verify(self.lift.target)
        except VerificationError as failure:
            raise VerificationError(
                "VAN-2",
                f"The collision is not one of the gradient map: "
                f"{failure.obligation} failed. {failure.message}",
            ) from failure
