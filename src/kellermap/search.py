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

from collections.abc import Iterable, Iterator, Mapping, Sequence
from dataclasses import dataclass
from itertools import combinations
from typing import Any, TypeAlias, cast

import sympy as sp
from sympy.polys.domains import Domain
from sympy.polys.polyerrors import CoercionFailed
from sympy.polys.rings import PolyElement

from .bcw import BCWStep, Carried, Fresh
from .bcw.step import Factor
from .guards import (
    counts,
    fresh_names,
    maps,
    polynomials_over,
    searched_domain,
    settled,
)
from .polynomial_map import PolynomialMap, clone_domain
from .reduction import Reduction

# A slot before a name is assigned: either the value a fresh coordinate
# would carry, or a coordinate that already carries it. There is no separate
# type for the fresh case, because ``Fresh`` differs from it only by the name,
# and under SEA-3 the search assigns that name.
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
    coefficient
        What ``G`` scales the removed product by, BCW-11. One for a candidate
        from ``enumerate_candidates``, which divides a displacement and so has
        no weight to place; SEA-14 states that boundary. The untargeted
        enumerator sets it, because it takes ``P`` and ``Q`` monic and the
        coefficient of the leading monomial has to go somewhere.
    """

    index: int
    left: Slot
    right: Slot
    coefficient: sp.Expr = sp.Integer(1)

    @property
    def slots(self) -> tuple[Slot, Slot]:
        """Return both slots in order."""
        return (self.left, self.right)

    @property
    def shares_one_generator(self) -> bool:
        """Return whether both slots are fresh and carry the same value, BCW-12.

        Then one coordinate serves both. Two would carry the same value and
        cost a dimension for nothing, which is the same saving that puts
        ``alpoege15`` two dimensions below ``bcw17``.

        It arises when the leading monomial is a square. The untargeted
        enumerator produces it; ``enumerate_candidates`` never has, measured
        over 2690 candidates along both long chains, because its two slots come
        from a pool value and from dividing by it.
        """
        left, right = self.slots

        return (
            not isinstance(left, Carried)
            and not isinstance(right, Carried)
            and bool(left == right)
        )

    @property
    def m(self) -> int:
        """Return how many generators the step would introduce."""
        if self.shares_one_generator:
            return 1

        return sum(not isinstance(slot, Carried) for slot in self.slots)

    def factors(self, names: Iterable[sp.Symbol]) -> tuple[Factor, Factor]:
        """Return the slots as ``BCWStep`` factors, taking names in slot order.

        The names come from outside, by SEA-3. Exactly ``m`` of them are
        consumed, and a shorter supply raises rather than inventing one.

        Two fresh slots carrying one value take one name between them, BCW-12.
        """
        supply = iter(names)
        built: list[Factor] = []
        shared: sp.Symbol | None = None

        for slot in self.slots:
            if isinstance(slot, Carried):
                built.append(slot)
                continue
            if shared is not None:
                built.append(Fresh(slot, shared))
                continue
            try:
                name = next(supply)
            except StopIteration:
                raise ValueError(
                    f"The candidate introduces {self.m} generators, "
                    "and fewer names were supplied."
                ) from None
            if self.shares_one_generator:
                shared = name
            built.append(Fresh(slot, name))

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

        Above one only. A factor with a constant term has order zero and its
        ``H`` reaches ``EA^-1``, which BCW-6 admits at no level, so ``-1`` is
        returned and ``BCWStep.build`` refuses it by name. Reporting zero there
        was a second defect and the reason the first one was silent: the step
        was built with a level it does not reach and only ``verify`` said so,
        which nothing in the untargeted walk called. An external audit found
        the chain that came out of it.
        """
        orders = [
            _order(_value(source, slot))
            for slot in self.slots
            if not isinstance(slot, Carried)
        ]
        if not orders:
            return 1

        return min(min(orders) - 1, 1)


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

    ``selection_limit`` is checked here and not only in ``search``. This
    function is public, and until 0.4.0rc9 a negative limit passed through it
    and still produced candidates. The pool values are checked here for the
    same reason and by the same precedent: until 0.5 a value that is not a
    polynomial over the source's ring yielded nothing and said nothing.
    """
    values = tuple(pool)
    counts(selection_limit=selection_limit)
    polynomials_over(source.ring, values)

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
        # Not reachable: this would require the displacement of coordinate
        # ``index`` to be a multiple of itself, that is a constant anchor.
        # Constants are excluded as anchors.
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


# --------------------------------------------------------------------------
# Assembling a chain
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class SearchOutcome:
    """What a search returns. Not a certificate; see SEA-1.

    Parameters
    ----------
    reduction
        The chain, or ``None`` if none was found. There was a ``signs`` field
        between work packages 7 and 10, holding the diagonal SEA-5 then allowed
        in the comparison. BCW-11 removed the need for it: with the constant
        inside the step, the chain reaches the target exactly.
    examined
        How many maps the search looked at.
    deepest
        The greatest number of steps any chain reached. On a negative result it
        is the only thing that says what was searched rather than how much, and
        a run that never gets past a handful of steps is reporting something
        different from one that reaches the last name and fails at the
        endpoint.
    exhausted
        Whether the space the search covers was exhausted. ``False`` means the
        budget ran out first, and then a negative result says even less than
        SEA-6 already allows.
    domain
        The coefficient ring the search covered, DOM-4. An exhausted space is
        worth what the space is worth, and a chain found over ``QQ`` answers a
        different question from one found over ``ZZ``.
    """

    reduction: Reduction | None
    examined: int
    deepest: int
    exhausted: bool
    _domain: Domain

    @property
    def domain(self) -> Domain:
        """Return the coefficient ring, DOM-4, as a copy.

        A copy on every read. A SymPy domain is not a value object: its
        generators are ``PolyElement``, so mutable dicts, and a caller holding
        the one this outcome carries could change what a finished result
        reports. Cloning at construction closed the aliasing with the argument;
        an external audit of 0.5.0rc1 pointed out that the accessor still hands
        the same object out every time.

        Measured: 0.1 microseconds for ``QQ``, 23 for ``ZZ[T]``, 55 for
        ``QQ[X3][S]``, against a search that spends milliseconds per map. The
        frozen dataclass promises value semantics and this is what they cost.
        """
        return cast(Domain, clone_domain(self._domain))


def conjugate(source: PolynomialMap, signs: Sequence[sp.Expr]) -> PolynomialMap:
    """Return ``D F D^-1`` for a diagonal ``D`` of non-zero constants.

    A change of coordinates and not a presentation change: it rewrites the
    polynomials. Degree, order and filtration degree survive, and a collision
    carries over with its points and image sign-flipped, so two conjugate maps
    are the same map in different coordinates. A diagonal of ones and minus
    ones is its own inverse; a general one is not, which is why the
    inverse is taken and not reused.

    The Jacobian determinant survives as a *function*, in the new coordinates:
    it becomes ``det J(F)`` composed with ``D``. For a Keller map that is the
    same constant, which is the case SEA-5 is about; for a map whose
    determinant is not constant the two are equal only up to the sign flips.

    A zero entry raises: ``D`` has to be invertible, and this is the group
    SEA-5 admits, not an arbitrary linear change.

    The entries were ones and minus ones until 0.4. That was too narrow, and
    the measurement that showed it is in ``roadmap.md``: the backward search
    exhausts its space against the published nineteen-dimensional map, and at
    the map where it stops, no coordinate can be undone with a factor of ``+1``
    or ``-1``. A diagonal with arbitrary non-zero entries is just as much a
    change of coordinates, and Alpoege's map has determinant ``-2`` while its
    reductions have ``1``, so a scalar other than a sign is the rule in this
    material rather than the exception.
    """
    entries = tuple(sp.sympify(entry) for entry in signs)
    if len(entries) != source.dimension or any(entry == 0 for entry in entries):
        raise ValueError(
            f"Expected {source.dimension} non-zero entries, got {entries}."
        )

    ring = source.ring
    domain = ring.domain
    if not domain.is_Field and any(entry not in (1, -1) for entry in entries):
        raise ValueError(
            f"Conjugating by {entries} over {domain} needs the inverse of an "
            "entry that is not a unit. Use over_field first."
        )

    try:
        scale = [domain.from_sympy(entry) for entry in entries]
    except CoercionFailed as error:  # pragma: no cover - the field check first
        raise ValueError(f"The entries {entries} do not lie in {domain}.") from error

    def scaled(monomial: tuple[int, ...], coefficient: Any, position: int) -> Any:
        value = coefficient * scale[position]
        for index, exponent in enumerate(monomial):
            for _ in range(exponent):
                value = value / scale[index]
        return value

    return PolynomialMap.from_ring(
        ring,
        tuple(
            ring.from_terms(
                [
                    (monomial, scaled(monomial, coefficient, position))
                    for monomial, coefficient in component.iterterms()
                ]
            )
            for position, component in enumerate(source.to_polynomials())
        ),
    )


def diagonal_matching(
    candidate: PolynomialMap,
    published: PolynomialMap,
) -> tuple[int, ...] | None:
    """Return the signs of the ``D`` carrying ``candidate`` to ``published``.

    ``None`` if there is none. The system is linear over GF(2): a monomial
    with exponent vector ``e`` in component ``i`` acquires the sign
    ``d_i * prod(d_k ^ e_k)``, so each monomial of each component is one
    equation. It is heavily overdetermined -- nineteen components against
    nineteen unknowns for the milestone target -- so ``D`` is read off rather
    than fitted, which is what makes the comparison of SEA-5 evidence.

    Both maps must already list their generators in the same order. Use
    ``PolynomialMap.reordered`` first, per SEA-4.
    """
    if candidate.variables != published.variables:
        raise ValueError(
            "The two maps list different generators, or in a different order."
        )

    size = candidate.dimension
    rows: list[tuple[list[int], int]] = []

    for index, (ours, theirs) in enumerate(
        zip(candidate.to_polynomials(), published.to_polynomials(), strict=True)
    ):
        if set(ours.monoms()) != set(theirs.monoms()):
            return None

        for monomial, coefficient in ours.iterterms():
            other = theirs[monomial]
            if abs(coefficient) != abs(other):
                return None

            row = [0] * size
            row[index] ^= 1
            for position, exponent in enumerate(monomial):
                if exponent % 2:
                    row[position] ^= 1

            rows.append((row, 0 if other == coefficient else 1))

    signs = _solve_gf2(rows, size)
    if signs is None:
        return None

    # Self-check: the solution of a consistent system satisfies it. This can
    # fail only if the elimination is wrong.
    if conjugate(candidate, signs) != published:  # pragma: no cover - elimination
        return None

    return signs


def _solve_gf2(rows: list[tuple[list[int], int]], size: int) -> tuple[int, ...] | None:
    """Return one solution of the system, or ``None`` if it is inconsistent.

    Free variables are set so that the solution has as few minus ones as the
    elimination leaves; the choice is fixed rather than arbitrary, because
    SEA-2 makes the whole search a pure function of its arguments.
    """
    pivots: dict[int, tuple[list[int], int]] = {}

    for row, value in rows:
        current, rhs = list(row), value
        for column in range(size):
            if not current[column]:
                continue
            if column in pivots:
                other, other_rhs = pivots[column]
                current = [a ^ b for a, b in zip(current, other, strict=True)]
                rhs ^= other_rhs
            else:
                pivots[column] = (current, rhs)
                break
        else:
            if rhs:
                return None

    solution = [0] * size
    for column in sorted(pivots, reverse=True):
        row, rhs = pivots[column]
        value = rhs
        for later in range(column + 1, size):
            if row[later]:
                value ^= solution[later]
        solution[column] = value

    return tuple(1 - 2 * bit for bit in solution)


def search(
    source: PolynomialMap,
    target: PolynomialMap,
    pool: Mapping[sp.Symbol, sp.Expr],
    *,
    budget: int = 20000,
    spare: int = 2,
    rewrites: int = 1,
    selection_limit: int = 8,
    over: Domain | None = None,
) -> SearchOutcome:
    """Look for a chain of ``BCWStep`` from ``source`` to ``target``.

    ``pool`` maps the name of a fresh generator to the value it carries in the
    published target. The search decides which step introduces which name, not
    what the names are (SEA-3) and not what the values are (SEA-8). A value is
    admitted with either sign, because the published listing and the value a
    step supplies can differ by one.

    What this search cannot reach, stated rather than left to be discovered
    (SEA-14). Its steps carry no coefficient: ``enumerate_candidates`` divides
    a displacement into two factors, and a division has nowhere to put a
    weight. Its steps also give each fresh slot its own name from the pool, so
    the step of BCW-12 whose two slots are one coordinate is outside it. A
    chain needing either is reported as no result, which is correct under
    SEA-6 -- the space was searched and the chain is not in it -- and is not a
    deferral under SEA-7. ``peel`` has neither restriction: it solves for the
    coefficient and reads the names off the target.

    Four rules bound the walk, and each is a decision rather than a fact about
    Keller maps:

    * the degree never rises along a chain, which holds for both reference
      reductions and is what makes a chain converge on a cubic target;
    * the dimension never passes the target's;
    * at most ``spare`` steps introduce no generator at all;
    * at most ``rewrites`` fresh coordinates carry a factor the pool does not
      hold, and such a coordinate has to be rewritten later to end up carrying
      what the target publishes;
    * at most ``budget`` maps are examined.

    ``spare`` is what bounds the length of a chain. Every other step consumes a
    name, so a chain has at most ``len(pool) + spare`` steps. A step that
    introduces nothing reuses two coordinates that already carry their factors;
    the published nineteen-dimensional map needs at least one, because its
    dimension grows by sixteen over seventeen steps, and its `w2` component is
    the residue of exactly such a step. Such a step may also come *after* the
    last generator has been introduced, so reaching the target is tried
    whenever every name is spent and the walk continues afterwards if any spare
    step is left.

    The moves out of a map are tried in a fixed order, lower degree and fewer
    terms first. Ordering discards nothing; it decides which chain is found
    first, which is what a budget makes visible.

    The result verifies nothing by itself. Its chain is ``CONSTRUCTED``
    throughout, so by BCW-9 its own obligations compare the implementation
    against itself, and the evidence is the endpoint (SEA-5). Finding nothing
    is not a proof that nothing exists (SEA-6), and with ``exhausted`` false it
    is not even a statement about the space this search covers.
    """
    # Before ``settled``, and all of it. ``settled`` can answer and return, so
    # an argument checked only afterwards is valid or invalid depending on the
    # endpoints. An external audit built this: ``search(F, F, None)`` returned
    # a result, while the same pool against endpoints that had to be walked
    # raised.
    maps(source=source, target=target)
    counts(
        budget=budget,
        spare=spare,
        rewrites=rewrites,
        selection_limit=selection_limit,
    )
    fresh_names(pool, source)

    # DOM-1 and DOM-2, before ``settled`` and for the same reason as the checks
    # above. Without ``over`` this is the source's ring and nothing is checked,
    # so a call written against 0.4 keeps its meaning under DOM-3.
    domain = searched_domain(over, source, target)
    polynomials_over(source.ring, pool.values(), list(pool))

    # REV-11 before the search and not inside it, as in the peel. Until
    # 0.4.0rc8 the test stood only in ``_finish``, that is in the descent. The
    # non-answer case was fixed before the search began, and the budget still
    # decided whether the space was reported as exhausted. This becomes visible
    # only on a source with ``m = 0`` branches, because without them the
    # descent has nothing to do. An external audit built such a source.
    if settled(source, target):
        return SearchOutcome(None, 0, 0, True, domain)

    names = tuple(pool)
    values = {name: sp.expand(pool[name]) for name in names}

    remaining = [budget]
    cut_off = [False]
    deepest = [0]
    order = target.variables

    def walk(
        current: PolynomialMap,
        used: frozenset[sp.Symbol],
        steps: tuple[BCWStep, ...],
        spare: int,
        rewrites: int,
    ) -> SearchOutcome | None:
        if remaining[0] <= 0:
            # A map fails on the budget here, and only here. Deriving
            # ``exhausted`` from ``remaining > 0`` confused a budget spent
            # exactly with a cut-off search. This is the same defect as in the
            # peel, found by the same audit.
            cut_off[0] = True
            return None
        remaining[0] -= 1
        deepest[0] = max(deepest[0], len(steps))

        if len(used) == len(names):
            reached = _finish(
                current, target, order, steps, budget - remaining[0], deepest[0], domain
            )
            if reached is not None:
                return reached
            if spare <= 0:
                return None

        available = [
            sign * values[name]
            for name in names
            if name not in used
            for sign in (1, -1)
        ]

        reachable = []
        for candidate in enumerate_candidates(
            current, available, selection_limit=selection_limit
        ):
            for assigned, spent in _assignments(
                candidate, current, values, used, rewrites
            ):
                if not assigned and spare <= 0:
                    continue

                step = _extend(current, candidate, assigned)
                if not _admissible(step.target, current, target):
                    continue

                reachable.append((_rank(step.target), step, assigned, spent))

        reachable.sort(key=lambda entry: entry[0])

        for _, step, assigned, spent in reachable:
            found = walk(
                step.target,
                used | set(assigned),
                (*steps, step),
                spare - (0 if assigned else 1),
                rewrites - spent,
            )
            if found is not None:
                return found

        return None

    outcome = walk(source, frozenset(), (), spare, rewrites)
    if outcome is not None:
        return outcome

    return SearchOutcome(
        None, budget - max(remaining[0], 0), deepest[0], not cut_off[0], domain
    )


def _assignments(
    candidate: Candidate,
    current: PolynomialMap,
    values: dict[sp.Symbol, sp.Expr],
    used: frozenset[sp.Symbol],
    rewrites: int,
) -> Iterator[tuple[list[sp.Symbol], int]]:
    """Yield each way of naming the fresh slots, with the rewrites it costs.

    A fresh slot whose factor is a pool value, up to sign, takes that name.
    That is a decision and not a fact: a coordinate carrying a value the target
    publishes need not be the coordinate that publishes it. Assuming it is
    keeps the branching finite, and SEA-13 says so.

    A fresh slot whose factor is *not* a pool value may take any unused name,
    at the cost of one rewrite. Such a coordinate cannot end the chain carrying
    what the target says it carries, so a later step has to rewrite its
    component. ``rewrites`` bounds how many chains may need that. With none
    left the slot has no name and the candidate is dropped.

    Two slots of one step never claim the same name.
    """
    fresh = [
        sp.expand(value)
        for slot, value in zip(candidate.slots, candidate.values(current), strict=True)
        if not isinstance(slot, Carried)
    ]

    def extend(
        position: int, chosen: list[sp.Symbol], left: int
    ) -> Iterator[tuple[list[sp.Symbol], int]]:
        if position == len(fresh):
            yield list(chosen), rewrites - left
            return

        wanted = fresh[position]
        exact = [
            name
            for name in values
            if name not in used
            and name not in chosen
            and wanted in (values[name], sp.expand(-values[name]))
        ]
        if exact:
            for name in exact:
                yield from extend(position + 1, [*chosen, name], left)
            return

        if left <= 0:
            return

        for name in values:
            if name not in used and name not in chosen:
                yield from extend(position + 1, [*chosen, name], left - 1)

    return extend(0, [], rewrites)


def _extend(
    current: PolynomialMap,
    candidate: Candidate,
    names: list[sp.Symbol],
) -> BCWStep:
    """Build the step and verify it before it enters a chain.

    The enumerator already declines what BCW-6 and the constructor of
    ``BCWStep`` would refuse, so nothing here is expected to raise. Verifying
    anyway costs one pass and means a chain cannot grow through a step that
    does not hold.
    """
    step = BCWStep.build(
        current,
        candidate.index,
        *candidate.factors(names),
        candidate.filtration_level(current),
    )
    step.verify()

    return step


def _rank(reached: PolynomialMap) -> tuple[int, int, int]:
    """Return the order in which the moves from one map are tried.

    Lower degree first, then fewer terms, then fewer coordinates. Ordering
    loses no chain -- every move is still walked -- and it decides which one is
    walked first, which is what a bounded budget makes visible. The key is a
    total order on values, so SEA-2 survives it.
    """
    return (
        reached.degree(),
        sum(len(component.terms()) for component in reached.to_polynomials()),
        reached.dimension,
    )


def _admissible(
    reached: PolynomialMap,
    previous: PolynomialMap,
    target: PolynomialMap,
) -> bool:
    """Return whether the walk may continue through this map."""
    return (
        reached.dimension <= target.dimension
        and reached.degree() <= previous.degree()
        and reached.degree() >= target.degree()
    )


def _finish(
    current: PolynomialMap,
    target: PolynomialMap,
    order: tuple[sp.Symbol, ...],
    steps: tuple[BCWStep, ...],
    examined: int,
    deepest: int,
    domain: Domain,
) -> SearchOutcome | None:
    """Check the endpoint, and report the chain if it matches.

    A chain of no steps is not representable under RED-1, and two maps of one
    dimension over different generators are a legitimate pair of arguments;
    both are non-answers rather than errors, as they are for a peel. See
    REV-11, which the forward search follows for the same reason: a search that
    finds nothing raises nothing.
    """
    if current.dimension != target.dimension or not steps:
        return None

    if set(current.variables) != set(order):
        return None

    if current.reordered(order) != target:
        return None

    return SearchOutcome(Reduction(steps), examined, deepest, False, domain)
