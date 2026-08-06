"""Candidate enumeration: what Proposition (3.1) could do at a given map.

A candidate is a proposal, not a certificate. It names a target component and
two factor slots, which is what ``BCWStep.build`` needs apart from the source.
It becomes evidence by being built and verified, and by nothing else. Nothing
here verifies anything, and SEA-1 keeps it outside every certificate.

The enumeration is bounded by a *value pool*: the polynomials a fresh slot may
supply. SEA-8 makes the pool an argument rather than a search space, because
the unrestricted version is infinite before SEA-9 normalizes it and exponential
in the number of terms afterwards.

One factor of a candidate is an *anchor* -- a pool value, or the value a
coordinate of the source already carries. The other is the *co-factor*, and is
obtained by dividing the target component by the anchor and then selecting a
part of the quotient. SEA-10 says why a proper part has to be offered, and why
each selection is re-checked rather than inherited from the largest one.

See ``docs/contracts.md``, SEA-8 to SEA-10.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from itertools import combinations
from typing import TypeAlias, cast

import sympy as sp
from sympy.polys.rings import PolyElement

from .bcw import Carried, Fresh
from .bcw.step import Factor
from .polynomial_map import PolynomialMap

# Ein Platz vor der Namensvergabe: entweder der Wert, den eine frische
# Koordinate tragen wuerde, oder eine Koordinate, die ihn schon traegt.
# Kein eigener Typ fuer den frischen Fall, weil ``Fresh`` sich davon nur
# durch den Namen unterscheidet und den vergibt nach SEA-3 die Suche.
Slot: TypeAlias = sp.Expr | Carried


@dataclass(frozen=True)
class Candidate:
    """One way to apply Proposition (3.1) at a map, before names are given.

    Carries no ``verify()`` and therefore no numbered obligations, in the shape
    of ``LinearAutomorphism``. What it carries is the argument list of
    ``BCWStep.build`` minus the source and minus the fresh variable names.

    Parameters
    ----------
    index
        The component the step would act on, zero-based.
    left, right
        The two slots. A ``Carried`` slot names a coordinate of the source; any
        other slot is an expression, the value a fresh coordinate would carry.
    """

    index: int
    left: Slot
    right: Slot

    @property
    def slots(self) -> tuple[Slot, Slot]:
        """Return both slots in order."""
        return (self.left, self.right)

    @property
    def m(self) -> int:
        """Return how many generators the step would introduce."""
        return sum(not isinstance(slot, Carried) for slot in self.slots)

    def factors(self, names: Iterable[sp.Symbol]) -> tuple[Factor, Factor]:
        """Return the slots as ``BCWStep`` factors, taking names in slot order.

        The names come from outside, by SEA-3. Exactly ``m`` of them are
        consumed, and a shorter supply raises rather than inventing one.
        """
        supply = iter(names)
        built: list[Factor] = []

        for slot in self.slots:
            if isinstance(slot, Carried):
                built.append(slot)
                continue
            try:
                built.append(Fresh(slot, next(supply)))
            except StopIteration:
                raise ValueError(
                    f"The candidate introduces {self.m} generators, "
                    "and fewer names were supplied."
                ) from None

        return (built[0], built[1])

    def values(self, source: PolynomialMap) -> tuple[sp.Expr, sp.Expr]:
        """Return the two factors as expressions, against a given source.

        A ``Carried`` slot has no value of its own; it names the coordinate
        that supplies one, and which coordinate that is only means something
        relative to a map.
        """
        return cast(
            tuple[sp.Expr, sp.Expr],
            tuple(_value(source, slot).as_expr() for slot in self.slots),
        )

    def product(self, source: PolynomialMap) -> sp.Expr:
        """Return ``P * Q``, the subsum the step would remove."""
        left, right = self.values(source)

        return cast(sp.Expr, sp.expand(left * right))

    def filtration_level(self, source: PolynomialMap) -> int:
        """Return the ``EA`` level ``H`` would reach, as BCW-6 admits it.

        ``H`` displaces only the fresh coordinates, by the factors of the
        fresh slots, so its filtration degree is one less than the smallest
        order among them. BCW-6 confines the declared level to ``{0, 1}``, so
        anything above one is reported as one; a step may declare a weaker
        bound than it reaches, and this reports the strongest admissible one.
        """
        orders = [
            _order(_value(source, slot))
            for slot in self.slots
            if not isinstance(slot, Carried)
        ]
        if not orders:
            return 1

        return 1 if min(orders) >= 2 else 0


def _order(polynomial: PolyElement) -> int:
    """Return the smallest total degree among the terms of a polynomial."""
    return min(int(sum(monomial)) for monomial in polynomial.monoms())


def _value(source: PolynomialMap, slot: Slot) -> PolyElement:
    """Return the factor a slot supplies, as an element of the source's ring."""
    if isinstance(slot, Carried):
        return cast(
            PolyElement,
            source.to_polynomials()[slot.index] - source.ring.gens[slot.index],
        )

    return cast(PolyElement, source.ring.from_expr(slot))


def _expressible(source: PolynomialMap, value: sp.Expr) -> PolyElement | None:
    """Return the pool value in the source's ring, or ``None`` if it is not.

    A pool value naming a generator the source does not have is not yet
    available. That is how the dependency between carriers is enforced, and it
    costs nothing: ``w6 = w1 x`` simply does not convert until ``w1`` exists.
    """
    try:
        return cast(PolyElement, source.ring.from_expr(value))
    except (ValueError, TypeError, sp.SympifyError):
        return None


def _displacements(source: PolynomialMap) -> tuple[PolyElement, ...]:
    """Return ``F_i - X_i`` for every coordinate."""
    return tuple(
        component - generator
        for component, generator in zip(
            source.to_polynomials(), source.ring.gens, strict=True
        )
    )


def _is_subsum(product: PolyElement, component: PolyElement) -> bool:
    """Return whether every term of the product occurs in the component."""
    return all(
        component.get(monomial) == coefficient
        for monomial, coefficient in product.items()
    )


def _quotient(component: PolyElement, anchor: PolyElement) -> PolyElement:
    """Return the largest co-factor the division of the component admits.

    Ordinary multivariate division. The result is a starting point and not an
    answer: SEA-10 requires every selection from it to be checked as a subsum
    in its own right, and the quotient itself is checked like any other.
    """
    quotient, _ = divmod(component, anchor)

    return cast(PolyElement, quotient)


def _selections(quotient: PolyElement, limit: int) -> Iterator[PolyElement]:
    """Yield the quotient and every non-empty part of it, largest first.

    ``limit`` caps the number of terms a quotient may have before its parts are
    skipped. A quotient of ``t`` terms has ``2^t - 1`` parts; the cap keeps a
    pathological component from making the enumeration unaffordable, and is
    reported by ``enumerate_candidates`` rather than hidden.
    """
    terms = sorted(quotient.terms(), reverse=True)
    if len(terms) > limit:
        yield quotient.ring.from_terms(terms)
        return

    for size in range(len(terms), 0, -1):
        for chosen in combinations(terms, size):
            yield quotient.ring.from_terms(list(chosen))


def anchors(source: PolynomialMap, pool: Iterable[sp.Expr]) -> tuple[Slot, ...]:
    """Return the factors available at a map, pool values before carriers.

    A pool value that does not convert into the source's ring is dropped: it
    names a generator the map does not have yet. A coordinate is offered only
    if it is a carrier, which is what BCW-10 requires of a ``Carried`` slot.

    A constant is dropped too. ``H`` displaces a fresh coordinate by its factor,
    so a factor of order zero puts ``H`` outside ``EA^0`` and BCW-6 refuses the
    step at either admissible level. Offering it would move the refusal from
    the enumerator to the constructor without making it any less certain.

    The order is fixed rather than incidental, because SEA-2 makes the whole
    enumeration a pure function of its arguments.
    """
    available: list[Slot] = [
        value
        for value in pool
        if (converted := _expressible(source, value)) is not None
        and converted
        and _order(converted) >= 1
    ]
    available.extend(Carried(index) for index in source.carrier_indices)

    return tuple(available)


def enumerate_candidates(
    source: PolynomialMap,
    pool: Iterable[sp.Expr],
    *,
    selection_limit: int = 8,
) -> tuple[Candidate, ...]:
    """Return every candidate the pool admits at ``source``, in a fixed order.

    For each component and each anchor, the *displacement* of the component is
    divided by the anchor, and each part of the quotient is offered whose
    product with the anchor is a subsum of that displacement. A part that
    equals the value of a carrier is offered as that carrier rather than as a
    fresh factor, since reusing a coordinate costs no dimension.

    The displacement and not the component: a step removes ``P Q`` from
    ``F_i``, and a product containing the term ``X_i`` itself would leave a
    target whose ``i``-th component is no longer ``X_i`` plus something. The
    arithmetic of BCW-1 would hold and the map would leave the shape every
    later step assumes.

    Complete relative to the pool and to nothing else. A step whose fresh
    factor is outside the pool is unreachable here, not merely unfound; see
    "No completeness of the enumerator either" in ``docs/contracts.md``.
    """
    values = tuple(pool)
    carriers = {
        _value(source, Carried(index)): index for index in source.carrier_indices
    }

    found: dict[tuple[int, str, str], Candidate] = {}

    for index, component in enumerate(_displacements(source)):
        for anchor in anchors(source, values):
            if isinstance(anchor, Carried) and anchor.index == index:
                continue

            divisor = _value(source, anchor)
            if not divisor:
                continue

            quotient = _quotient(component, divisor)
            if not quotient:
                continue

            for selection in _selections(quotient, selection_limit):
                if _order(selection) < 1:
                    continue

                if not _is_subsum(divisor * selection, component):
                    continue

                partner = _partner(selection, carriers, index)
                if partner is None:  # pragma: no cover - see _partner
                    continue

                candidate = _canonical(index, anchor, partner)
                found.setdefault(_key(candidate), candidate)

    return tuple(found.values())


def _partner(
    selection: PolyElement,
    carriers: dict[PolyElement, int],
    index: int,
) -> Slot | None:
    """Return the co-factor as a slot, or ``None`` if it cannot be one.

    A co-factor equal to the value of a carrier is offered as that carrier: it
    is the same factor and it costs no dimension. The target component is not
    available as a carrier, since the constructor of ``BCWStep`` refuses a slot
    on the component the step acts on.
    """
    carried = carriers.get(selection)
    if carried is not None:
        # Nicht erreichbar: das setzte voraus, dass die Verschiebung von
        # Koordinate ``index`` ein Vielfaches ihrer selbst ist, also einen
        # konstanten Anker -- und Konstanten sind als Anker ausgeschlossen.
        if carried == index:  # pragma: no cover - needs a constant anchor
            return None
        return Carried(carried)

    return cast("sp.Expr", selection.as_expr())


def _canonical(index: int, anchor: Slot, partner: Slot) -> Candidate:
    """Return the candidate with its slots in a fixed order.

    Swapping the two slots gives the same step up to renaming the fresh
    coordinates, so one order is emitted rather than two. Carried slots come
    first, which is the order the reference reductions are recorded in.
    """
    if isinstance(partner, Carried) and not isinstance(anchor, Carried):
        return Candidate(index, partner, anchor)

    return Candidate(index, anchor, partner)


def _key(candidate: Candidate) -> tuple[int, str, str]:
    """Return a hashable identity for deduplication, stable across runs."""
    left, right = (
        f"carried:{slot.index}" if isinstance(slot, Carried) else f"fresh:{slot}"
        for slot in candidate.slots
    )

    return (candidate.index, left, right)
