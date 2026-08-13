"""The checks a walk makes before it begins.

Two of them, and both were written twice before they were written here. The
forward search and the peel search in opposite directions and share almost
nothing, but they take the same kind of arguments and they answer the same two
questions before they spend anything:

* are the bounds numbers a walk can count with (SEA-13, REV-11);
* do the two endpoints leave a chain to look for at all.

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

    Two cases, and both are decided by the endpoints alone:

    * the endpoints are the same map, up to the order of its coordinates. The
      chain that reaches it has no steps, and RED-1 makes that unrepresentable.
    * the dimensions agree and the generators do not. A step never removes a
      coordinate, so equal dimensions mean every step introduces none, and such
      a step leaves the generators alone. No chain can cross from one set to
      the other.

    Where the dimensions differ this returns false even when no chain exists,
    because that is a question for the walk and not for the endpoints.
    """
    if target.dimension != source.dimension:
        return False

    if not same_generators(target, source):
        return True

    return bool(target.reordered(source.variables) == source)
