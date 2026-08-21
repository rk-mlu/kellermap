"""Proposition (3.1) applied without a target, UNT-1 to UNT-5.

``search`` and ``peel`` both need a target. An untargeted search has only a
source and the instruction to reach degree three, so nothing tells it which
step to take. ``docs/contracts.md`` states what this module may offer and what
bounds it, and it carries the measurements those obligations rest on.

UNT-1 to UNT-5 are what this module implements. UNT-6 to UNT-9 widen the offer
to factors that are sums, and they are written and not yet built: the family
was measured before it was implemented, and the page says which figures come
from a prototype.

Two things here are worth reading before the code.

The candidates come from the leading monomials, because that is the only rule
left once there is no displacement to divide. The space is small: between 4
and 25 factorizations at every map of the two long chains that is still above
degree three, from dimension 3 up to 19.

The measure is exponential in the degree, and that is not a preference.
A step replaces one monomial of degree ``d`` by at most three of degree
``d - 1``, so anything linear in the degree can be defeated by a single step.
Two linear measures were tried and both were: see the contract page.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass

import sympy as sp
from sympy.polys.domains import Domain

from .bcw import BCWStep
from .bcw.step import Carried
from .context import ReductionContext
from .guards import counts, maps, searched_domain
from .polynomial_map import PolynomialMap
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

    return tuple(found)


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
    ``BCWStep`` rejects, and it cannot arise: the component would have to be a
    carrier whose whole displacement is the part, and a part has degree at most
    ``d - 2``, so that component has degree below ``d`` and carries no leading
    monomial to split. There is no branch for it rather than an unreachable
    one.
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
        How many maps were built and looked at.
    deepest
        The longest chain reached, whether or not it arrived.
    exhausted
        Whether the space was seen to the end. ``False`` means the budget ran
        out first, and then a negative result says even less.
    domain
        The coefficient ring the search covered, DOM-4.
    """

    reduction: Reduction | None
    examined: int
    deepest: int
    exhausted: bool
    domain: Domain


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

    Depth first, and without ranking or pruning. Which candidate is tried first
    is the order the enumerator fixes, and nothing here prefers one over
    another. That is the point: work packages 11 and 12 need a measured
    baseline to be compared against, and a baseline with a heuristic in it
    measures the heuristic.

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
    """
    maps(source=source)
    counts(budget=budget)
    domain = searched_domain(over, source)
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

        for candidate in untargeted_candidates(current):
            names = naming.variables(current.ring, candidate.m)
            step = BCWStep.build(
                current,
                candidate.index,
                *candidate.factors(names),
                1,
                candidate.coefficient,
            )
            if not lowers_the_weight(current, step.target):  # pragma: no cover
                # UNT-3 where a search applies it. It cannot fire for what this
                # enumerator offers, and that is a property of the enumerator
                # and not of the rule: its two parts multiply to the leading
                # monomial exactly, so the term is cancelled and never added.
                # What replaces it has degree at most ``d - 1`` and the two new
                # components at most ``d - 2``, which together weigh less than
                # ``3 ** (d - 3)``. Measured over 172 candidates along both long
                # chains and 32 constructed maps: none was refused here.
                #
                # The check stays because the rule belongs to the search. A
                # later enumerator that does not guarantee it would otherwise
                # walk a space UNT-4 does not describe.
                continue

            remaining[0] -= 1
            found = walk(step.target, (*steps, step))
            if found is not None:
                return found

        return None

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
        reduction is not None or not cut_off[0],
        domain,
    )
