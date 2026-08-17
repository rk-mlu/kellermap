"""The checks a walk makes before it begins.

Two of them, and both were written twice before they were written here. The
forward search and the peel search in opposite directions and share almost
nothing, but they take the same kind of arguments and they answer the same two
questions before they spend anything:

* are the arguments the kinds of thing a walk can work with (SEA-3, SEA-12);
* do the two endpoints leave a chain to look for at all (REV-11).

Keeping one copy is not tidiness. The bound check existed in both modules with
different messages and different coverage -- one refused a negative
``selection_limit`` where the other did not -- and an audit of ``0.4.0rc8``
found the gap by calling the enumerator directly.

The order matters as much as the content. Every check here runs before
``settled``, because ``settled`` can answer and return, and an argument that is
only rejected after it would be rejected or accepted depending on the
endpoints. An audit of ``0.4.0rc11`` found exactly that: ``search(F, F, None)``
returned an outcome while the same pool against endpoints that had to be walked
raised. Whether a call is valid is not allowed to depend on how far the walk
gets.
"""

from collections.abc import Iterable, Mapping, Sequence
from typing import Any

import sympy as sp
from sympy.polys.domains import Domain
from sympy.polys.polyerrors import CoercionFailed
from sympy.polys.rings import PolyRing

from .canonical import agree
from .errors import VerificationError
from .polynomial_map import PolynomialMap
from .variables import reserved_names


def maps(**named: Any) -> None:
    """Raise unless every named argument is a ``PolynomialMap``.

    First, because everything after it reads ``dimension``, ``ring`` and
    ``variables``. Passing ``None`` raised ``AttributeError`` from inside
    ``settled``, which names an implementation detail rather than the argument
    that was wrong, and which the error table of ``api.md`` does not promise.
    """
    wrong = {
        name: type(value).__name__
        for name, value in named.items()
        if not isinstance(value, PolynomialMap)
    }
    if wrong:
        raise TypeError(f"These arguments must be polynomial maps: {wrong}.")


def fresh_names(pool: Mapping[sp.Symbol, sp.Expr], source: PolynomialMap) -> None:
    """Raise unless the names of a value pool satisfy RC-4 for the source.

    SEA-3 hands the fresh generators to the search rather than letting it
    allocate them, and says each of them satisfies RC-4 against the source's
    ring, as it would if a context had produced it. That obligation was written
    down and not checked: a pool naming a generator of the source was accepted,
    and the search then looked for steps introducing a coordinate that already
    existed.

    Distinctness is by *name* and not by symbol. Two keys of one dictionary are
    distinct as objects, but ``Symbol("w")`` and ``Symbol("w", positive=True)``
    are two keys with one name, and a ring cannot tell them apart.
    """
    if not isinstance(pool, Mapping):
        raise TypeError(f"The value pool must be a mapping; got {type(pool).__name__}.")

    not_symbols = [name for name in pool if not isinstance(name, sp.Symbol)]
    if not_symbols:
        raise TypeError(f"The pool names must be symbols; got {not_symbols}.")

    names = [str(symbol.name) for symbol in pool]
    repeated = sorted({name for name in names if names.count(name) > 1})
    if repeated:
        raise ValueError(f"The pool names must be distinct by name: {repeated}.")

    taken = sorted(set(names) & reserved_names(source.ring))
    if taken:
        raise ValueError(
            f"The pool names must be fresh for the source's ring: {taken}."
        )


def counts(**bounds: int) -> None:
    """Raise unless every bound is a whole number a walk can count down from.

    A negative budget produced ``examined = -1``, which is not a count of
    anything. A fractional one produced ``examined = 1.5``, which contradicts
    the ``int`` that ``PeelOutcome`` and ``SearchOutcome`` declare. Both are
    refused rather than clamped: a caller who passes one has made a mistake and
    should hear about it.

    ``bool`` is a subclass of ``int``, so ``budget=True`` is a budget of one
    map. That is almost certainly a typing slip and not a request, and it is
    refused for the same reason ``extend(True)`` is.
    """
    wrong_type = {
        name: value
        for name, value in bounds.items()
        if isinstance(value, bool) or not isinstance(value, int)
    }
    if wrong_type:
        raise TypeError(f"These bounds must be integers: {wrong_type}.")

    negative = {name: value for name, value in bounds.items() if value < 0}
    if negative:
        raise ValueError(f"These bounds must not be negative: {negative}.")


def same_generators(reached: PolynomialMap, source: PolynomialMap) -> bool:
    """Return whether the two maps are built on the same generators.

    ``reordered`` raises on anything but a permutation, so it cannot be the
    test for whether a walk has arrived: two maps of one dimension over
    different generators are a legitimate pair of arguments and a legitimate
    non-answer.

    The symbols themselves and not their printed names. ``Symbol("x",
    positive=True)`` and ``Symbol("x", real=True)`` print alike and are two
    generators, so comparing names let a pair through that ``reordered`` then
    refused. An external audit built it.
    """
    return set(reached.variables) == set(source.variables)


def settled(source: PolynomialMap, target: PolynomialMap) -> bool:
    """Return whether REV-11 answers this pair without a walk.

    Six invariants, each of them a property a ``BCWStep`` cannot change, so
    each of them decides the pair from its endpoints alone. They are checked
    from the cheapest to the dearest, since any one of them is enough:

    * the target has fewer coordinates. A step introduces two, one or none and
      removes none, so the dimension never falls along a chain.
    * the coefficient domains differ. A step takes its factors and its
      coefficient from the domain of its source, and ``PolynomialMap`` counts
      the domain as part of its identity, so no chain crosses from ``ZZ`` to
      ``QQ``. This one has cost a release before: a driver built its source
      with ``over_field`` while the target lay over ``ZZ``, and the search ran
      for hours in a space that could not contain the answer.
    * a generator of the source is missing from the target. A step keeps every
      coordinate it was given and adds fresh ones, so the source's generators
      are a subset of any map reachable from it. At equal dimensions this is
      the case of two maps over different generators.
    * one endpoint fixes the origin and the other does not. A step builds
      ``G o F^[m] o H`` with ``H`` in ``EA^0`` and ``G`` in ``EA^1`` by BCW-6,
      and both fix the origin; the extension by identity coordinates adds
      zeros. So ``target(0) = 0`` exactly when ``source(0) = 0``, in both
      directions, and membership of ``MA^0`` is carried along a chain.
    * the Jacobian determinants differ. BCW-7 requires a step to preserve the
      determinant, because every element of ``EA_n(k)`` has determinant one.
      The comparison goes through ``canonical.agree``, which is the one answer
      this package gives to what equality of two expressions means. Both values
      come out of a ring and are normalized already, so this is defensive; a
      second, cheaper answer to the same question is how the original defect
      arose.

    The last two compute something; the four before them read structure. That
    is the order they are checked in. Until ``0.4.0rc12`` this paragraph said
    the determinant was the only one that computes anything, which passes over
    ``is_in_MA``.
    * the endpoints are the same map, up to the order of its coordinates. The
      chain that reaches it has no steps, and RED-1 makes that unrepresentable.

    The list is not claimed to be complete. It holds the invariants a step is
    required to preserve that are cheap enough to test on two maps, and it has
    grown under audit twice, from two entries to four and then to six. A
    missing entry costs a walk that was going to fail anyway; a wrong entry
    would lose a reachable target. That asymmetry is why the list may be short
    and may not be wrong.

    Where none of them applies this returns false, which says that the
    endpoints do not settle the pair and not that a chain exists. That question
    belongs to the walk.
    """
    if target.dimension < source.dimension:
        return True

    if target.ring.domain != source.ring.domain:
        return True

    if not set(source.variables) <= set(target.variables):
        return True

    if source.is_in_MA(0) != target.is_in_MA(0):
        return True

    if not agree(source.determinant(), target.determinant()):
        return True

    if target.dimension > source.dimension:
        return False

    return bool(target.reordered(source.variables) == source)


def searched_domain(
    over: Domain | None,
    source: PolynomialMap,
    target: PolynomialMap,
    pool: Mapping[sp.Symbol, sp.Expr] | None = None,
) -> Domain:
    """Return the coefficient ring the search covers, DOM-1 and DOM-2.

    Without ``over`` the ring is the source's, which is what ``search`` and
    ``peel`` used before it existed and is why a call written against 0.4 keeps
    its meaning. Two endpoints over different rings are then a non-answer under
    REV-11 and DOM-3, and not an error.

    With ``over`` the caller has stated the space, and an argument over another
    one contradicts them rather than narrowing the search. No search over
    either ring answers what they asked, so this raises where the call is made
    instead of reporting an exhausted space.

    The pool is not checked here. A value that is not a polynomial over the
    ring is malformed whether or not the caller named one, so
    ``polynomials_over`` checks it and is called without ``over`` as well.
    """
    if over is None:
        return source.ring.domain

    for name, argument in (("source", source), ("target", target)):
        if argument.ring.domain != over:
            raise VerificationError(
                "DOM-2",
                f"the {name} lies over {argument.ring.domain}, "
                f"and the search was asked for {over}",
            )

    return over


def polynomials_over(
    ring: PolyRing,
    values: Iterable[sp.Expr],
    names: Sequence[sp.Symbol] | None = None,
) -> None:
    """Raise unless every value is a polynomial over ``ring``, DOM-2.

    What is checked is the coefficients and not the generators. A value may
    name a coordinate the source does not have yet: ``w6 = w1 x`` becomes
    convertible only once ``w1`` exists, and the enumerator dropping such a
    value is how the dependency between carriers falls out by itself. So the
    value is converted into the ring widened by whatever symbols it mentions,
    and only a coefficient outside the domain is refused.

    That distinction is the whole of this check. ``1/2 * y**2`` over ``ZZ`` and
    ``y * z`` over ``ZZ[x, y]`` both fail ``ring.from_expr``, and only the
    first is malformed: the second describes a step that a later coordinate
    makes reachable. The first version of this guard refused both, and three
    tests written for the second said so.

    Unconditional, and that is the one asymmetry of this family. Two endpoints
    over different rings each describe a map, and REV-11 answers the pair
    without an error; DOM-3 keeps that. A value whose coefficients are outside
    the domain describes nothing at all, so there is no reading of the call
    under which it is a narrower search.

    Called from ``enumerate_candidates``, which is public and was the one place
    a bad value passed unremarked, and called again by ``search`` before its
    walk. Not a duplicate: a search whose endpoints are equal is answered by
    ``settled`` and never reaches the enumerator, and whether a call is valid
    must not depend on how far it gets. An audit made that finding against
    0.4.0rc11 for the pool itself.
    """
    labels = list(names) if names is not None else []
    known = set(ring.symbols)

    for position, value in enumerate(values):
        later = sorted(sp.sympify(value).free_symbols - known, key=str)
        widened, *_ = sp.polys.rings.ring(
            list(ring.symbols) + later, ring.domain, ring.order
        )
        try:
            widened.from_expr(value)
        except (CoercionFailed, ValueError, TypeError) as exc:
            named = f"for {labels[position]} " if position < len(labels) else ""
            raise VerificationError(
                "DOM-2",
                f"the pool value {named}has coefficients outside "
                f"{ring.domain}; got {value}",
            ) from exc
