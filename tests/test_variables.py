"""Naming of stabilisation variables.

The tests record two promises that later reductions depend on: that a factory
is a pure function, and that ``extend`` checks its result rather than believing
it.
"""

import pytest
import sympy as sp
from sympy.polys.domains import QQ
from sympy.polys.rings import PolyRing, ring

from kellermap import (
    DEFAULT_VARIABLE_FACTORY,
    IndexedVariableFactory,
    PolynomialMap,
    examples,
    reserved_names,
)

x, y, T = sp.symbols("x y T")


@pytest.fixture
def numbered() -> PolynomialMap:
    """A map with numbered variables, as in BCW17."""
    variables = sp.symbols("x1:6")
    return PolynomialMap(variables, variables)


# --------------------------------------------------------------------------
# Purity
# --------------------------------------------------------------------------


def test_factory_is_a_pure_function(numbered: PolynomialMap) -> None:
    """The load-bearing promise of the protocol.

    A generator that counts upwards would return different names on the second
    call and break the monoid identity in test_invariants, without anything
    raising an exception.
    """
    ring = numbered.ring

    assert DEFAULT_VARIABLE_FACTORY(ring, 2) == DEFAULT_VARIABLE_FACTORY(ring, 2)


def test_repeated_extension_of_equal_maps_agrees() -> None:
    """The same promise, one level up."""
    F = examples.sum_and_difference()
    G = examples.sum_and_difference()

    assert F.extend(2).variables == G.extend(2).variables


# --------------------------------------------------------------------------
# Naming convention
# --------------------------------------------------------------------------


def test_convention_is_read_off_numbered_generators(numbered: PolynomialMap) -> None:
    """x1..x5 becomes x6, x7 and not X6, X7.

    A reduction composes many extensions. Two competing naming schemes in one
    map are hard to read against the paper.
    """
    assert numbered.extend(2).variables[-2:] == sp.symbols("x6 x7")


def test_fallback_prefix_without_a_convention() -> None:
    """x, y carries no numbering: the behaviour from before the factory."""
    F = examples.sum_and_difference()

    assert F.extend(2).variables == (x, y, sp.Symbol("X3"), sp.Symbol("X4"))


def test_fallback_prefix_on_mixed_conventions() -> None:
    """Inconsistent prefixes yield no convention."""
    a1, b2 = sp.symbols("a1 b2")
    F = PolynomialMap((a1, b2), (a1, b2))

    assert F.extend(1).variables[-1] == sp.Symbol("X3")


def test_explicit_prefix_overrides_the_convention() -> None:
    """The point of the injection: a reduction can name carrier variables."""
    F = examples.sum_and_difference()

    extended = F.extend(3, IndexedVariableFactory(prefix="u"))

    assert extended.variables[-3:] == sp.symbols("u1 u2 u3")


# --------------------------------------------------------------------------
# Collisions
# --------------------------------------------------------------------------


def test_reserved_names_cover_the_coefficient_domain() -> None:
    """T in k[T] is not a generator, and its name is taken all the same."""
    F = examples.parametric_swap()

    assert reserved_names(F.ring) == {"x", "y", "T"}


def test_generated_names_skip_the_coefficient_domain() -> None:
    X3 = sp.Symbol("X3")
    F = PolynomialMap((x, y), (X3 * x, y))

    assert F.extend(2).variables[-2:] == (sp.Symbol("X4"), sp.Symbol("X5"))


def test_explicit_prefix_skips_taken_names() -> None:
    u1 = sp.Symbol("u1")
    F = PolynomialMap((u1, y), (u1, y))

    extended = F.extend(2, IndexedVariableFactory(prefix="u"))

    assert extended.variables[-2:] == sp.symbols("u2 u3")


def test_factory_rejects_a_negative_count(numbered: PolynomialMap) -> None:
    with pytest.raises(ValueError, match="non-negative"):
        DEFAULT_VARIABLE_FACTORY(numbered.ring, -1)


def test_factory_returns_nothing_for_zero(numbered: PolynomialMap) -> None:
    assert DEFAULT_VARIABLE_FACTORY(numbered.ring, 0) == ()


# --------------------------------------------------------------------------
# extend checks what the factory promises
# --------------------------------------------------------------------------


def test_extend_rejects_a_colliding_name() -> None:
    """The most expensive failure: ``clone`` would accept it without a word
    and build a ring in which two coordinates mean one generator."""
    F = examples.sum_and_difference()

    def colliding(ring: object, count: int) -> tuple[sp.Symbol, ...]:
        return (x,)

    with pytest.raises(ValueError, match="already in use"):
        F.extend(1, colliding)


def test_extend_rejects_a_wrong_count() -> None:
    F = examples.sum_and_difference()

    def too_few(ring: object, count: int) -> tuple[sp.Symbol, ...]:
        return (sp.Symbol("u1"),)

    with pytest.raises(ValueError, match="returned 1 names, expected 2"):
        F.extend(2, too_few)


def test_extend_rejects_duplicates() -> None:
    F = examples.sum_and_difference()

    def duplicated(ring: object, count: int) -> tuple[sp.Symbol, ...]:
        return (sp.Symbol("u1"), sp.Symbol("u1"))

    with pytest.raises(ValueError, match="duplicate names"):
        F.extend(2, duplicated)


def test_extend_rejects_non_symbols() -> None:
    F = examples.sum_and_difference()

    def not_symbols(ring: object, count: int) -> tuple[sp.Expr, ...]:
        return (x * y,)

    with pytest.raises(TypeError, match="SymPy symbols"):
        F.extend(1, not_symbols)  # type: ignore[arg-type]


# --------------------------------------------------------------------------
# Extending twice has to equal extending once
# --------------------------------------------------------------------------

SPLITS = [(1, 1), (2, 2), (1, 3), (3, 1)]

FACTORIES = [None, IndexedVariableFactory(), IndexedVariableFactory(prefix="u")]


@pytest.mark.parametrize(("m", "ell"), SPLITS)
@pytest.mark.parametrize("factory", FACTORIES)
def test_extending_twice_equals_extending_once(
    m: int, ell: int, factory: IndexedVariableFactory | None
) -> None:
    """(F^[m])^[l] = F^[m+l].

    A reduction stabilises step by step and has to arrive where a single
    stabilisation arrives. The test checks the naming and not the components,
    which are identities anyway.
    """
    F = examples.sum_and_difference()

    assert F.extend(m, factory).extend(ell, factory) == F.extend(m + ell, factory)


@pytest.mark.parametrize(("m", "ell"), SPLITS)
def test_extending_twice_survives_a_reserved_name_in_between(m: int, ell: int) -> None:
    """The same test with a gap in the sequence of names.

    X3 is taken as a coefficient symbol, so naming has to skip it, at the same
    place in both decompositions.
    """
    F = PolynomialMap((x, y), (sp.Symbol("X3") * x, y))

    assert F.extend(m).extend(ell) == F.extend(m + ell)


def test_extending_twice_reads_the_numbered_convention(
    numbered: PolynomialMap,
) -> None:
    """x1..x5 -> x6..x9, whether in one step or in two."""
    stepwise = numbered.extend(2).extend(2)

    assert stepwise == numbered.extend(4)
    assert stepwise.variables[-4:] == sp.symbols("x6 x7 x8 x9")


def test_purity_alone_does_not_give_the_composition_invariant() -> None:
    """Why the requirement stands in the protocol in its own right.

    This factory is a pure function of ring and count and never collides, so
    ``extend`` finds nothing to object to. The two decompositions give
    different maps all the same, because the size of the ring enters the names
    instead of only the walking distance.
    """

    def by_ring_size(ring: PolyRing, count: int) -> tuple[sp.Symbol, ...]:
        return tuple(sp.Symbol(f"g{ring.ngens}_{i}") for i in range(1, count + 1))

    F = examples.sum_and_difference()

    assert by_ring_size(F.ring, 2) == by_ring_size(F.ring, 2)

    assert F.extend(2, by_ring_size).extend(2, by_ring_size) != F.extend(
        4, by_ring_size
    )


# --------------------------------------------------------------------------
# Nested coefficient domains
#
# Domains nest: over QQ[X3][S] the symbol S is on top and X3 one level below.
# Reading domain.symbols alone finds S and misses X3, which is enough for
# extend() to hand out a coordinate X3 that then coincides with the
# parameter.
# --------------------------------------------------------------------------

NESTED_DOMAINS = [
    (QQ[sp.Symbol("X3")][sp.Symbol("S")], {"S", "X3"}),
    (QQ[sp.Symbol("T")].frac_field(sp.Symbol("S")), {"S", "T"}),
    (QQ[sp.Symbol("A")][sp.Symbol("B")][sp.Symbol("C")], {"A", "B", "C"}),
    (QQ.frac_field(sp.Symbol("T")), {"T"}),
    (QQ, set()),
]


@pytest.mark.parametrize(("domain", "expected"), NESTED_DOMAINS)
def test_reserved_names_reaches_every_domain_level(
    domain: object, expected: set[str]
) -> None:
    R = ring("u,v", domain)[0]

    assert reserved_names(R) == expected | {"u", "v"}


@pytest.mark.parametrize(("domain", "expected"), NESTED_DOMAINS)
def test_extension_avoids_nested_domain_symbols(
    domain: object, expected: set[str]
) -> None:
    """The defect the gap made possible."""
    R, u, v = ring("u,v", domain)
    F = PolynomialMap.from_ring(R, (u + v, v))

    fresh = {symbol.name for symbol in F.extend(3).variables[2:]}

    assert not fresh & expected


def test_a_generator_may_not_share_a_name_with_a_nested_parameter() -> None:
    """SymPy checks the top domain level only. Here the search goes deeper."""
    X3, S = sp.symbols("X3 S")
    R, generator, other = ring("X3,w", QQ[X3][S])

    with pytest.raises(ValueError, match="coefficient indeterminate"):
        PolynomialMap.from_ring(R, (generator, other))


def test_a_generator_may_not_share_a_name_with_a_fraction_field_parameter() -> None:
    T, S = sp.symbols("T S")
    R, generator, other = ring("T,w", QQ[T].frac_field(S))

    with pytest.raises(ValueError, match="coefficient indeterminate"):
        PolynomialMap.from_ring(R, (generator, other))
