"""Proposition (3.1) applied without a target, UNT-1 to UNT-5.

``search`` and ``peel`` both need a target. An untargeted search has only a
source and the instruction to reach degree three, so nothing tells it which
step to take. ``docs/contracts.md`` states what this module may offer and what
bounds it, and it carries the measurements those obligations rest on.

 UNT-6 to UNT-9 widen the offer to
factors that are sums and UNT-10 and UNT-11 order it. All eleven are built.

Two things here are worth reading before the code.

The candidates come from the leading monomials, because that is the only rule
left once there is no displacement to divide. The space is small: between 2
and 22 candidates at every map of the two long chains that is still above
degree three, from dimension 3 up to 19. This carried 4 and 25, which were
factorization counts from before the offer was widened and before swapped
pairs were merged; ``scripts/untargeted_space.py`` checks the two that hold.

The measure is exponential in the degree, and that is not a preference.
A step replaces one monomial of degree ``d`` by at most three of degree
``d - 1``, so anything linear in the degree can be defeated by a single step.
Two linear measures were tried and both were: see the contract page.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import InitVar, dataclass, field
from typing import cast

import sympy as sp
from sympy.polys.domains import Domain

from .bcw import BCWStep
from .bcw.step import Carried
from .context import ReductionContext
from .guards import counts, maps, searched_domain
from .polynomial_map import PolynomialMap, clone_domain
from .reduction import Reduction
from .search import Candidate, Slot

WEIGHT_BASE = 3
"""The base of the measure in UNT-3.

Three, and it could be two. A step replaces one monomial of degree ``d`` by at
most three of degree ``d - 1``, and ``3 ** (d - 3)`` is exactly what absorbs
that, which is why the base was chosen so. Measured, base two suffices on all
three chains this repository carries and base four changes nothing, so the
choice is a margin and not a necessity.
"""


def remaining_weight(source: PolynomialMap, base: int = WEIGHT_BASE) -> int:
    """Return the measure of UNT-3: what is left to reduce, weighted by degree.

    The sum of ``base ** (deg M - 3)` over every monomial ``M`` of degree at
    least four in every component. Zero exactly when the map has degree at most
    three, which is the reduction target.

    A step has to lower this. For a step that introduces at least one generator
    that follows from Proposition (3.1): the terms replacing the removed
    monomial have degree at most ``max(deg P, deg Q) + 1``, which is at most
    ``d - 1``. For a step that introduces none it is a rule this project
    states, because such a step can put a product into a component instead of
    cancelling one, and two of them can cycle forever without either being
    wrong.
    """
    counts(base=base)
    if base < 2:
        # ``counts`` admits zero, because most counts here may be zero. A base
        # below two makes the measure constant and it would rule out nothing.
        raise ValueError(f"The weight base must be at least 2; got {base}.")

    return sum(
        base ** (sum(monomial) - 3)
        for component in source.to_polynomials()
        for monomial in component.itermonoms()
        if sum(monomial) >= 4
    )


def lowers_the_weight(source: PolynomialMap, target: PolynomialMap) -> bool:
    """Return whether a step from ``source`` to ``target`` makes progress.

    UNT-3, as the predicate a search applies. Named for what it decides rather
    than for the measure, because a caller wants the answer and not the two
    numbers behind it.
    """
    return remaining_weight(target) < remaining_weight(source)


@dataclass(frozen=True)
class Split:
    """One way to write a leading monomial as a product, before names are given.

    Parameters
    ----------
    index
        The component the step would act on, zero-based.
    monomial
        The exponent vector of the leading monomial the step removes.
    coefficient
        Its coefficient. ``P`` and ``Q`` are monic, so the step carries this.
    """

    index: int
    monomial: tuple[int, ...]
    coefficient: sp.Expr
    left: tuple[int, ...]
    right: tuple[int, ...]


def _monomial(exponents: tuple[int, ...], variables: tuple[sp.Symbol, ...]) -> sp.Expr:
    """Return the monomial an exponent vector denotes."""
    product = sp.Integer(1)
    for variable, exponent in zip(variables, exponents, strict=True):
        product *= variable**exponent

    return product


def _splits(
    monomial: tuple[int, ...], degree: int
) -> Iterator[tuple[tuple[int, ...], ...]]:
    """Yield the ways to write ``monomial`` as a product of two proper parts.

    ``deg P`` and ``deg Q`` are at least one and at most ``degree - 2``, which
    is Proposition (3.1)'s own condition. Both together force ``degree >= 4``,
    so at degree three there is nothing to yield, which is UNT-2.

    Each pair is yielded once. Swapping the two gives the same step up to which
    name goes where, and SEA-2 says that is one candidate and not two.
    """
    for left_exponents in _divisors(monomial):
        right = tuple(
            whole - part for whole, part in zip(monomial, left_exponents, strict=True)
        )
        if not 1 <= sum(left_exponents) <= degree - 2:
            continue
        if not 1 <= sum(right) <= degree - 2:
            continue
        if left_exponents > right:
            continue
        yield left_exponents, right


def _divisors(monomial: tuple[int, ...]) -> Iterator[tuple[int, ...]]:
    """Yield every exponent vector dividing ``monomial``."""
    if not monomial:
        yield ()

        return

    head, *rest = monomial
    for tail in _divisors(tuple(rest)):
        for exponent in range(head + 1):
            yield (exponent, *tail)


def leading_splits(source: PolynomialMap) -> tuple[Split, ...]:
    """Return every factorization of a leading monomial, UNT-1 and UNT-2.

    A monomial of degree ``deg(F)`` occurring anywhere in ``F``, with its
    coefficient, written as a product of two parts of degree at most
    ``deg(F) - 2``. That is the rule Proposition (3.1) supplies once there is
    no target and therefore no displacement to divide.

    Empty at degree three, and that is the stopping rule of an untargeted
    search rather than a separate condition placed on it.

    The order is fixed: by component, then by monomial in the ring's order,
    then by the left part. ``moves`` emits its constants out of a sorted list
    for the same reason, after a set made ``PYTHONHASHSEED`` decide which move
    came first.
    """
    degree = source.degree()
    if degree <= 3:
        return ()

    found: list[Split] = []
    for index, component in enumerate(source.to_polynomials()):
        for monomial, coefficient in sorted(component.terms()):
            if sum(monomial) != degree:
                continue
            for left, right in sorted(_splits(monomial, degree)):
                found.append(
                    Split(
                        index=index,
                        monomial=monomial,
                        coefficient=source.ring.domain.to_sympy(coefficient),
                        left=left,
                        right=right,
                    )
                )

    return tuple(found)


def grouped_splits(source: PolynomialMap) -> tuple[Split, ...]:
    """Return the wider candidates of UNT-6 and UNT-7.

    ``P`` is a monomial of degree ``d // 2`` dividing at least two of the
    monomials of degree four or more in one component, and ``Q`` is the sum of
    their cofactors. The step removes all of them at once, where
    ``leading_splits`` removes one.

    This goes beyond Proposition (3.1) and the contract page says so. BCW write
    ``aM = PQ`` for a single monomial, which forces both factors to be
    monomials. BCW-6 admits the wider shape already, and work package 10
    measured what it is worth: the high-yield steps of the chains computed by
    hand all use a factor with several terms, and the narrow enumerator offers
    none.

    ``d // 2`` is UNT-7, a stated choice and not a proved one. Admissibility
    bounds the degree of a factor between two and ``d - 2``, and ``d // 2`` lies
    inside that for every ``d >= 4``.

    The coefficient of a grouped candidate is one. The coefficients of the
    monomials go into ``Q``, which is a sum and can carry them, where a single
    monomial has to hand its own to the step.

    ``Split`` carries a monomial and this yields a sum, so ``monomial`` holds
    the divisor and ``left`` and ``right`` hold the two parts as before, with
    ``right`` left empty. The candidates are built from ``coefficient`` and the
    two sides directly.
    """
    degree = source.degree()
    if degree <= 3:
        return ()

    wanted = degree // 2
    found: list[Split] = []
    for index, component in enumerate(source.to_polynomials()):
        high = sorted(
            (monomial, coefficient)
            for monomial, coefficient in component.terms()
            if sum(monomial) >= 4
        )
        if len(high) < 2:
            continue
        for divisor in _divisors_of_degree([monomial for monomial, _ in high], wanted):
            # Strictly larger, twice over. ``_cofactor_sum`` carries the same
            # condition and is the one that keeps ``Q`` free of a constant
            # term; this one decides whether a candidate is offered at all. A
            # group that counts the divisor among its two members leaves one
            # cofactor, and a wide candidate with one cofactor is a narrow
            # split written twice. Measured: dropping this line changes no
            # count on either source map and adds one duplicate on the map the
            # audit of 25 August 2026 built.
            covered = [
                (monomial, coefficient)
                for monomial, coefficient in high
                if sum(monomial) > sum(divisor)
                and all(a >= b for a, b in zip(monomial, divisor, strict=True))
            ]
            if len(covered) < 2:
                continue
            # No check that a cofactor stays within ``degree - 2``. It cannot
            # leave it: a monomial has degree at most ``d``, the divisor has
            # degree ``d // 2``, so a cofactor has degree at most
            # ``d - d // 2``, and that is at most ``d - 2`` for every
            # ``d >= 4``. At four and five the two are equal and above that the
            # slack grows. A branch was written and removed after coverage
            # showed it unreached and the arithmetic showed it unreachable.
            found.append(
                Split(
                    index=index,
                    monomial=divisor,
                    coefficient=sp.Integer(1),
                    left=divisor,
                    right=(),
                )
            )

    return tuple(found)


def _divisors_of_degree(
    monomials: list[tuple[int, ...]],
    degree: int,
) -> list[tuple[int, ...]]:
    """Return every exponent vector of that degree dividing one of them."""
    found: set[tuple[int, ...]] = set()
    for monomial in monomials:
        found |= {divisor for divisor in _divisors(monomial) if sum(divisor) == degree}

    return sorted(found)


def untargeted_candidates(source: PolynomialMap) -> tuple[Candidate, ...]:
    """Return the steps Proposition (3.1) could take at ``source``, UNT-1.

    One candidate per factorization of a leading monomial. A part that a
    coordinate of the source already carries is offered as that coordinate
    rather than as a fresh value, which costs no dimension; BCW-10 admits it
    and the fifteen-dimensional chain is what it is for.

    The coefficient of the leading monomial goes into the candidate. ``P`` and
    ``Q`` are monic here, so without BCW-11 these steps could not be written
    down at all: from the second map of the nineteen-dimensional chain onwards,
    every factorization comes from a monomial whose coefficient is not one.

    A slot on the component the step acts on is not offered. ``BCWStep``
    rejects it, and an enumerator that proposes what cannot be built only
    postpones the rejection.
    """
    variables = source.variables
    carried = _carried_values(source)

    found: list[Candidate] = []
    for split in leading_splits(source):
        left, right = (
            _slot(_monomial(part, variables), carried)
            for part in (split.left, split.right)
        )
        found.append(
            Candidate(
                index=split.index,
                left=left,
                right=right,
                coefficient=split.coefficient,
            )
        )

    # UNT-6 after UNT-1, so that a call written before the offer was widened
    # still sees the same candidates in the same places. The order within each
    # group is the one its enumerator fixes.
    for split in grouped_splits(source):
        divisor = _monomial(split.left, variables)
        cofactors = _cofactor_sum(source, split.index, split.left)
        found.append(
            Candidate(
                index=split.index,
                left=_slot(divisor, carried),
                right=_slot(cofactors, carried),
                coefficient=sp.Integer(1),
            )
        )

    return tuple(found)


def _cofactor_sum(
    source: PolynomialMap,
    index: int,
    divisor: tuple[int, ...],
) -> sp.Expr:
    """Return the sum of the cofactors the divisor leaves, UNT-6.

    Every monomial of degree four or more in the component that the divisor
    divides, with its coefficient, divided by it and added up. The step removes
    all of them in one move.
    """
    component = source.to_polynomials()[index]
    domain = source.ring.domain
    total = sp.Integer(0)
    for monomial, coefficient in sorted(component.terms()):
        if sum(monomial) < 4:
            continue
        if sum(monomial) <= sum(divisor):
            # The repair of UNT-6. A monomial equal to the divisor leaves the
            # cofactor ``1``, so ``Q`` gets a constant term, order zero, and
            # ``H`` reaches ``EA^-1``, which BCW-6 admits at no level.
            # ``peeling`` and ``search.anchors`` both guard this and both say
            # so; it was not carried here until an external audit found a chain
            # that failed its own first step.
            continue
        if not all(a >= b for a, b in zip(monomial, divisor, strict=True)):
            continue
        rest = tuple(a - b for a, b in zip(monomial, divisor, strict=True))
        total += domain.to_sympy(coefficient) * _monomial(rest, source.variables)

    return sp.expand(total)


def _carried_values(source: PolynomialMap) -> dict[sp.Expr, int]:
    """Return the value each carrier coordinate holds, by value."""
    held: dict[sp.Expr, int] = {}
    for index in source.carrier_indices:
        value = sp.expand(source.components[index] - source.variables[index])
        held.setdefault(value, index)

    return held


def _slot(value: sp.Expr, carried: dict[sp.Expr, int]) -> Slot:
    """Return the slot for a factor, reusing a carrier where one holds it.

    No case here refuses. A slot on the component the step acts on is what
    ``BCWStep`` rejects, and it cannot arise.

    For a narrow candidate the component would have to be a carrier whose whole
    displacement is the part, and a part has degree at most ``d - 2``, so that
    component has degree below ``d`` and carries no leading monomial to split.

    For a grouped candidate the acting component holds at least two monomials
    of degree four or more, while a carrier's displacement is one polynomial:
    it is neither the divisor, which is a single monomial, nor the cofactor
    sum, whose degree is strictly smaller than the component's. An external
    audit pointed out that the argument above covered only the first case,
    which was where a reader would look for the second.

    There is no branch for either rather than an unreachable one.
    """
    holder = carried.get(value)
    if holder is not None:
        return Carried(holder)

    return value


@dataclass(frozen=True)
class ReductionOutcome:
    """What an untargeted search found, and what it saw on the way.

    Parameters
    ----------
    reduction
        The chain to a map of degree three, or ``None``. ``None`` is not a
        proof that none exists, by UNT-4: the space walked is the one UNT-3
        leaves, and UNT-3 rules out steps that BCW-1 to BCW-12 admit.
    examined
        How many maps the walk descended into, which is what ``budget`` bounds.

        Not how many were built. Ordering the steps at a map builds every
        candidate it offers, so the arithmetic done is larger than this number
        by that factor: at the normalized Alpoege map, 22 builds for each map
        entered. An external audit asked which of the two this counts, because
        the answer was written as though it were both.
    deepest
        The longest chain reached, whether or not it arrived.
    exhausted
        Whether the space was seen to the end. ``False`` means the budget ran
        out first, and then a negative result says even less. Also ``False``
        when a chain was found, because a walk that stops at the first one did
        not see the space to the end. ``search`` and ``peel`` report it the
        same way.
    domain
        The coefficient ring the search covered, DOM-4.
    """

    reduction: Reduction | None
    examined: int
    deepest: int
    exhausted: bool
    domain: InitVar[Domain]
    _domain: Domain = field(init=False, repr=False, compare=False)

    def __post_init__(self, domain: Domain) -> None:
        """Store a copy, so the caller keeps no handle on it."""
        object.__setattr__(self, "_domain", clone_domain(domain))

    def __repr__(self) -> str:
        """Show the ring as well, since the generated one cannot.

        ``_domain`` is kept out of the generated ``repr`` so that the field a
        caller sees is the property, and DOM-4 wants the ring reported, so it
        is put back by hand.
        """
        return (
            f"{type(self).__name__}(reduction={self.reduction!r}, "
            f"examined={self.examined}, deepest={self.deepest}, "
            f"exhausted={self.exhausted}, domain={self._domain})"
        )

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


def ordered_steps(
    source: PolynomialMap,
    naming: ReductionContext,
) -> tuple[BCWStep, ...]:
    """Return the steps this map offers, in the order of UNT-10.

    Built and not merely proposed, because the order is by what a step removes
    and that is not known before the step exists. A candidate whose step does
    not lower the measure is left out here, which is UNT-3 applied where the
    order is decided.

    Largest removal first, and among equals fewest coordinates bought. Measured
    over the widened offer on both source maps: 7 steps into dimension 13 for
    Alpoege and 29 into 39 for Gao, against 21 into 20 and 177 into 86 in the
    order the enumerator happens to fix.

    An order discards nothing, UNT-11. Every step that lowers the measure is
    still here, and a bad order costs the length of what is found and not
    whether anything is.
    """
    built: list[tuple[tuple[int, int], BCWStep]] = []
    before = remaining_weight(source)

    for candidate in untargeted_candidates(source):
        names = naming.variables(source.ring, candidate.m)
        step = BCWStep.build(
            source,
            candidate.index,
            *candidate.factors(names),
            # UNT-8. Only a wide candidate reaches ``EA^0``, and until UNT-10
            # the walk never built one, so this line was not observable. It is
            # now: the order builds every candidate before choosing.
            candidate.filtration_level(source),
            candidate.coefficient,
        )
        removed = before - remaining_weight(step.target)
        if removed <= 0:  # pragma: no cover
            # UNT-3 where the order is decided. It cannot fire for what this
            # enumerator offers, for the reason given at ``remaining_weight``:
            # the factors multiply into the monomials they remove, so the term
            # is cancelled and what replaces it weighs less. Measured over 272
            # candidates along both long chains, none was refused here.
            #
            # It stays because the rule belongs to the search. A later
            # enumerator that does not guarantee it would otherwise order a
            # step that walks a space UNT-4 does not describe.
            continue
        built.append(((-removed, step.target.dimension - source.dimension), step))

    return tuple(step for _, step in sorted(built, key=lambda pair: pair[0]))


def reduce_to_degree3(
    source: PolynomialMap,
    *,
    budget: int = 20000,
    context: ReductionContext | None = None,
    over: Domain | None = None,
) -> ReductionOutcome:
    """Look for a chain from ``source`` to a map of degree three, UNT-1 to UNT-5.

    Named for the degree it reduces to, because there is only one. BCW call
    their Section 3 "Reduction to degree 3", and a name saying only that the
    degree falls would leave a reader asking how far.

    No target and no pool. The candidates are the ones ``untargeted_candidates``
    offers, the search stops where the enumerator runs out, and that is at
    degree three by UNT-2.

    Depth first, and without pruning. The candidates are ordered by what a step
    removes, UNT-10, and the first that lowers the measure is taken. This said
    "without ranking" while it was the baseline of work package 9 and kept
    saying it after work package 11.1 gave it an order.

    ``UNT-3`` is applied, and it is not a heuristic. A step that does not lower
    the measure is not a slower route but a route that need not end: one step
    can create ``X_u X_v`` and the next remove it. The rule is what makes an
    exhausted space a statement, and UNT-4 says which space that is.

    A source that already has degree three is the base case and not a failure,
    UNT-5. There is nothing to build, RED-1 wants at least one step, and the
    outcome reports no reduction with nothing examined. That is the answer
    REV-11 gives for equal endpoints, for the same reason. It needs no branch:
    the enumerator offers nothing at degree three, so the walk returns that by
    itself.

    ``context`` names the fresh coordinates. A caller cannot supply names by
    SEA-3 here, because the number of steps is not known before the search, so
    the policy is passed instead of the names.

    The walk recurses once per step, so the longest chain it can report is
    bounded by the interpreter and not by ``budget``. Measured: one frame per
    step over a base of about twenty, so roughly 970 steps at the default
    recursion limit of 1000, against ``budget=20000``. A source needing a
    longer chain raises ``RecursionError`` instead of reporting a cut-off
    outcome, which is not the answer UNT-4 promises.

    Stated and not repaired, because nothing measured comes near it: the
    longest chain this project has produced is 29 steps, for Gao's map, and the
    default budget is the misleading part rather than the recursion. An
    external audit of 25 August 2026 found it.
    """
    maps(source=source)
    counts(budget=budget)
    domain = searched_domain(over, source)
    if context is not None and not isinstance(context, ReductionContext):
        # Before anything else, and before the base case in particular. A
        # source of degree three never names a coordinate, so a wrong context
        # passed unremarked there and raised an ``AttributeError`` from inside
        # only when the degree was higher. Whether an argument is well formed
        # must not depend on the data, which is the finding an audit made
        # against 0.4.0rc11 for the value pool.
        raise TypeError(
            "context must be a ReductionContext; "
            f"got {type(context).__name__}: {context!r}"
        )
    naming = context if context is not None else ReductionContext()

    remaining = [budget]
    deepest = [0]
    cut_off = [False]

    # No store of maps already seen. Independent steps commute, so different
    # orders reach the same map, and ``peel`` keeps a store for that reason.
    # Here it would be a decision about the search with no measurement behind
    # it, and this package is the baseline the later ones are compared against.
    # Work package 10 is where it belongs if it is worth anything.

    def walk(current: PolynomialMap, steps: tuple[BCWStep, ...]) -> Reduction | None:
        deepest[0] = max(deepest[0], len(steps))

        if current.degree() <= 3:
            return Reduction(steps) if steps else None
        if remaining[0] <= 0:
            cut_off[0] = True

            return None

        for step in ordered_steps(current, naming):
            if remaining[0] <= 0:
                # The sibling loop has to stop too. Checking only on entry let
                # a frame keep descending into its remaining siblings after the
                # budget was gone: at ``budget=1`` an external audit counted 22
                # child maps built and one reported. ``search`` and ``peel``
                # both check inside their loops.
                cut_off[0] = True

                return None

            remaining[0] -= 1
            found = walk(step.target, (*steps, step))
            if found is not None:
                return found

        return None  # pragma: no cover
        # Unreachable since the budget is checked between siblings. Every step
        # offered lowers ``Phi``, which is well founded, so a descent that is
        # not cut off reaches degree three; and one that is cut off returns
        # above, at the budget check, before the loop can run out. It was
        # reachable while the check sat only on entry, which is the defect an
        # audit of 0.5.0rc1 found.

    # No special case for a source of degree three. UNT-5 is what the walk
    # already does: the enumerator offers nothing there by UNT-2, so the first
    # frame returns at once with no steps, nothing examined and the space
    # exhausted. A branch here changed no outcome, and a mutation showed it,
    # so it is gone.
    reduction = walk(source, ())

    return ReductionOutcome(
        reduction,
        budget - max(remaining[0], 0),
        deepest[0],
        # ``False`` when a chain was found, as ``search`` and ``peel`` report
        # it. A walk that stops at the first chain did not see the space to the
        # end, so saying it did would be a claim it cannot support. This read
        # ``True`` there until an external audit put the three side by side and
        # UNT-4 promises the same four fields as the other two.
        False if reduction is not None else not cut_off[0],
        domain,
    )
