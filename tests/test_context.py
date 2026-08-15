"""The context that takes a factory at its word.

Both properties ``VariableFactory`` requires are cheap to check and are
checked. Purity, by asking twice. Composition, by having the context fetch
``count`` names once and one name ``count`` times.

That is the core of this file. Neither defect shows up anywhere further down.
Both produce entirely valid polynomial maps, only not
die, welche die Identitaet braucht.
"""

import pytest
import sympy as sp
from sympy.polys.rings import PolyRing

from kellermap import (
    DEFAULT_VARIABLE_FACTORY,
    FixedVariableFactory,
    IndexedVariableFactory,
    PolynomialMap,
    ReductionContext,
    examples,
)

x1, x2, x3 = sp.symbols("x1 x2 x3")

IDENTITY = PolynomialMap.identity((x1, x2, x3))
RING = IDENTITY.ring


@pytest.fixture
def context() -> ReductionContext:
    return ReductionContext()


# --------------------------------------------------------------------------
# RC-1: Determinismus
# --------------------------------------------------------------------------


def test_equal_arguments_give_equal_names(context: ReductionContext) -> None:
    assert context.variables(RING, 2) == context.variables(RING, 2)


def test_a_second_context_agrees(context: ReductionContext) -> None:
    """No state in the object, and therefore none between objects."""
    assert context.variables(RING, 2) == ReductionContext().variables(RING, 2)


def test_a_counting_factory_is_caught() -> None:
    """The defect the docstring of VariableFactory warns about."""

    class Counting:
        def __init__(self) -> None:
            self.calls = 0

        def __call__(self, ring: PolyRing, count: int) -> tuple[sp.Symbol, ...]:
            self.calls += 1
            return tuple(sp.Symbol(f"g{self.calls}_{index}") for index in range(count))

    with pytest.raises(ValueError, match="not a pure function"):
        ReductionContext(factory=Counting()).variables(RING, 2)


# --------------------------------------------------------------------------
# RC-3: Komposition
# --------------------------------------------------------------------------


def test_extending_twice_equals_extending_once(context: ReductionContext) -> None:
    """(F^[2])^[2] = F^[4], and with the same names."""
    twice = context.extend(context.extend(IDENTITY, 2), 2)
    once = context.extend(IDENTITY, 4)

    assert twice.variables == once.variables
    assert twice == once


def test_the_names_compose(context: ReductionContext) -> None:
    first = context.variables(RING, 2)
    second = context.variables(context.extended_ring(RING, 2), 2)

    assert first + second == context.variables(RING, 4)


def test_a_factory_naming_after_the_ring_size_is_caught() -> None:
    """Pure, free of collisions, and wrong all the same.

    The example from the docstring of ``VariableFactory``: the names carry the
    size of the ring the factory was given.
    """

    class Sized:
        def __call__(self, ring: PolyRing, count: int) -> tuple[sp.Symbol, ...]:
            return tuple(sp.Symbol(f"g{ring.ngens}_{index}") for index in range(count))

    with pytest.raises(ValueError, match="does not compose"):
        ReductionContext(factory=Sized()).variables(RING, 2)


# --------------------------------------------------------------------------
# RC-4 and RC-5: freshness, and that the context verifies it
# --------------------------------------------------------------------------


def test_the_names_are_fresh(context: ReductionContext) -> None:
    fresh = context.variables(RING, 3)

    assert fresh == sp.symbols("x4 x5 x6")
    assert not {symbol.name for symbol in fresh} & {
        symbol.name for symbol in RING.symbols
    }


def test_a_miscounting_factory_is_caught() -> None:
    class TooFew:
        def __call__(self, ring: PolyRing, count: int) -> tuple[sp.Symbol, ...]:
            return (sp.Symbol("u"),)

    with pytest.raises(ValueError, match="returned 1 names, expected 2"):
        ReductionContext(factory=TooFew()).variables(RING, 2)


def test_a_colliding_factory_is_caught() -> None:
    """PolyRing accepts a duplicated name without complaint."""

    class Colliding:
        def __call__(self, ring: PolyRing, count: int) -> tuple[sp.Symbol, ...]:
            return tuple(sp.Symbol("x2") for _ in range(count))

    with pytest.raises(ValueError, match="duplicate names"):
        ReductionContext(factory=Colliding()).variables(RING, 2)


def test_a_factory_taking_an_existing_name_is_caught() -> None:
    class Reusing:
        def __call__(self, ring: PolyRing, count: int) -> tuple[sp.Symbol, ...]:
            return (sp.Symbol("x2"), sp.Symbol("x9"))

    with pytest.raises(ValueError, match="already in use"):
        ReductionContext(factory=Reusing()).variables(RING, 2)


def test_a_factory_returning_something_else_is_caught() -> None:
    class NotSymbols:
        def __call__(self, ring: PolyRing, count: int) -> tuple[sp.Symbol, ...]:
            return tuple(sp.Integer(index) for index in range(count))  # type: ignore[misc]

    with pytest.raises(TypeError, match="SymPy symbols"):
        ReductionContext(factory=NotSymbols()).variables(RING, 2)


def test_a_name_of_a_coefficient_parameter_is_caught() -> None:
    """A T from k[T] is not a generator and is taken all the same."""
    T = sp.Symbol("T")
    parametric = PolynomialMap((x1, x2), (x1 + T * x2, x2))

    class Reusing:
        def __call__(self, ring: PolyRing, count: int) -> tuple[sp.Symbol, ...]:
            return (T,)

    with pytest.raises(ValueError, match="already in use"):
        ReductionContext(factory=Reusing()).variables(parametric.ring, 1)


# --------------------------------------------------------------------------
# RC-6: the arithmetic context is preserved
# --------------------------------------------------------------------------


def test_the_domain_and_order_survive(context: ReductionContext) -> None:
    widened = context.extended_ring(RING, 2)

    assert widened.domain == RING.domain
    assert widened.order == RING.order


def test_extending_a_map_keeps_its_domain(context: ReductionContext) -> None:
    extended = context.extend(IDENTITY, 2)

    assert extended.ring.domain == IDENTITY.ring.domain
    assert extended.components[:3] == IDENTITY.components


# --------------------------------------------------------------------------
# Randfaelle
# --------------------------------------------------------------------------


def test_extending_by_nothing(context: ReductionContext) -> None:
    assert context.variables(RING, 0) == ()
    assert context.extend(IDENTITY, 0) == IDENTITY
    assert context.extended_ring(RING, 0).symbols == RING.symbols


def test_the_count_must_be_an_integer(context: ReductionContext) -> None:
    with pytest.raises(TypeError, match="must be an integer"):
        context.variables(RING, True)


def test_the_count_must_be_non_negative(context: ReductionContext) -> None:
    with pytest.raises(ValueError, match="non-negative"):
        context.variables(RING, -1)


def test_a_prefix_can_be_chosen() -> None:
    context = ReductionContext(factory=IndexedVariableFactory(prefix="u"))

    assert context.variables(RING, 2) == sp.symbols("u1 u2")


def test_the_default_factory_is_the_package_default(
    context: ReductionContext,
) -> None:
    assert context.factory is DEFAULT_VARIABLE_FACTORY


def test_the_context_is_a_value(context: ReductionContext) -> None:
    assert context == ReductionContext()
    assert hash(context) == hash(ReductionContext())


# --------------------------------------------------------------------------
# FixedVariableFactory
# --------------------------------------------------------------------------


def test_a_fixed_factory_returns_what_it_was_given() -> None:
    names = sp.symbols("x4 x5")

    assert FixedVariableFactory(names)(RING, 2) == names


def test_a_fixed_factory_refuses_another_count() -> None:
    with pytest.raises(ValueError, match="names 2 generators, asked for 1"):
        FixedVariableFactory(sp.symbols("x4 x5"))(RING, 1)


def test_a_fixed_factory_does_not_compose() -> None:
    """And the context says so rather than passing over it.

    A fixed factory is there for *one* extension of known size. A chain needs
    one that composes.
    """
    context = ReductionContext(factory=FixedVariableFactory(sp.symbols("x4 x5")))

    with pytest.raises(ValueError, match="names 2 generators, asked for 1"):
        context.variables(RING, 2)


# --------------------------------------------------------------------------
# Interaction with a step
# --------------------------------------------------------------------------


def test_a_context_names_the_variables_of_a_step(
    context: ReductionContext,
) -> None:
    """RC-7: the context names, it does not select a step."""
    from kellermap import over_field
    from kellermap.bcw import BCWStep, Fresh

    source = over_field(examples.factorable_shear())
    fresh = context.variables(source.ring, 2)
    step = BCWStep.build(source, 0, Fresh(x2**2, fresh[0]), Fresh(x3**2, fresh[1]))

    assert fresh == sp.symbols("x4 x5")
    assert step.variables == fresh
    assert step.verify() is None


def test_the_context_names_a_whole_chain(context: ReductionContext) -> None:
    """Three steps, six variables, and no gap between them."""
    from kellermap import over_field

    current = over_field(PolynomialMap.identity((x1, x2, x3)))
    allocated: tuple[sp.Symbol, ...] = ()
    for _ in range(3):
        fresh = context.variables(current.ring, 2)
        allocated += fresh
        current = context.extend(current, 2)

    assert allocated == sp.symbols("x4 x5 x6 x7 x8 x9")
    assert current.variables == (x1, x2, x3) + allocated
