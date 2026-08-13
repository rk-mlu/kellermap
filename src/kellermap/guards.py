"""The checks a walk makes before it begins.

Two of them, and both were written twice before they were written here. The
forward search and the peel search in opposite directions and share almost
nothing, but they take the same kind of arguments and they answer the same two
questions before they spend anything:

* are the bounds numbers a walk can count with (SEA-12);
* do the two endpoints leave a chain to look for at all (REV-11).

Keeping one copy is not tidiness. The bound check existed in both modules with
different messages and different coverage -- one refused a negative
``selection_limit`` where the other did not -- and an audit of ``0.4.0rc8``
found the gap by calling the enumerator directly.
"""

from .polynomial_map import PolynomialMap


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

    Four invariants, each of them a property a ``BCWStep`` cannot change, so
    each of them decides the pair from its endpoints alone:

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
    * the endpoints are the same map, up to the order of its coordinates. The
      chain that reaches it has no steps, and RED-1 makes that unrepresentable.

    Where none of the four applies this returns false, even when no chain
    exists. That is then a question for the walk and not for the endpoints.
    """
    if target.dimension < source.dimension:
        return True

    if target.ring.domain != source.ring.domain:
        return True

    if not set(source.variables) <= set(target.variables):
        return True

    if target.dimension > source.dimension:
        return False

    return bool(target.reordered(source.variables) == source)
