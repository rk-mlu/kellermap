"""Namensgebung fuer Stabilisierungsvariablen.

Die Tests halten zwei Zusagen fest, an denen spaetere Reduktionen haengen:
dass eine Factory eine reine Funktion ist, und dass ``extend`` ihr Ergebnis
prueft statt es zu glauben.
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
    """Eine Abbildung mit durchnummerierten Variablen, wie BCW17."""
    variables = sp.symbols("x1:6")
    return PolynomialMap(variables, variables)


# --------------------------------------------------------------------------
# Reinheit
# --------------------------------------------------------------------------


def test_factory_is_a_pure_function(numbered: PolynomialMap) -> None:
    """Die tragende Zusage des Protokolls.

    Ein hochzaehlender Generator wuerde hier beim zweiten Aufruf andere Namen
    liefern und die Monoid-Identitaet in test_invariants brechen -- ohne dass
    irgendetwas eine Ausnahme wuerfe.
    """
    ring = numbered.ring

    assert DEFAULT_VARIABLE_FACTORY(ring, 2) == DEFAULT_VARIABLE_FACTORY(ring, 2)


def test_repeated_extension_of_equal_maps_agrees() -> None:
    """Dieselbe Zusage, eine Ebene hoeher."""
    F = examples.sum_and_difference()
    G = examples.sum_and_difference()

    assert F.extend(2).variables == G.extend(2).variables


# --------------------------------------------------------------------------
# Namenskonvention
# --------------------------------------------------------------------------


def test_convention_is_read_off_numbered_generators(numbered: PolynomialMap) -> None:
    """x1..x5 wird zu x6, x7 -- nicht zu X6, X7.

    Eine Reduktion komponiert viele Erweiterungen; zwei konkurrierende
    Namensschemata in einer Abbildung sind gegen das Paper schwer zu lesen.
    """
    assert numbered.extend(2).variables[-2:] == sp.symbols("x6 x7")


def test_fallback_prefix_without_a_convention() -> None:
    """x, y traegt keine Nummerierung: Verhalten wie vor der Factory."""
    F = examples.sum_and_difference()

    assert F.extend(2).variables == (x, y, sp.Symbol("X3"), sp.Symbol("X4"))


def test_fallback_prefix_on_mixed_conventions() -> None:
    """Uneinheitliche Praefixe geben keine Konvention her."""
    a1, b2 = sp.symbols("a1 b2")
    F = PolynomialMap((a1, b2), (a1, b2))

    assert F.extend(1).variables[-1] == sp.Symbol("X3")


def test_explicit_prefix_overrides_the_convention() -> None:
    """Der Sinn der Injektion: eine Reduktion kann Traegervariablen benennen."""
    F = examples.sum_and_difference()

    extended = F.extend(3, IndexedVariableFactory(prefix="u"))

    assert extended.variables[-3:] == sp.symbols("u1 u2 u3")


# --------------------------------------------------------------------------
# Kollisionen
# --------------------------------------------------------------------------


def test_reserved_names_cover_the_coefficient_domain() -> None:
    """T in k[T] ist kein Generator, sein Name ist trotzdem belegt."""
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
# extend prueft, was die Factory zusagt
# --------------------------------------------------------------------------


def test_extend_rejects_a_colliding_name() -> None:
    """Der teuerste Fehlerfall: ``clone`` wuerde ihn wortlos hinnehmen und
    einen Ring bauen, in dem zwei Koordinaten denselben Generator meinen."""
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
# Zweimal erweitern muss einmal erweitern gleichen
# --------------------------------------------------------------------------

SPLITS = [(1, 1), (2, 2), (1, 3), (3, 1)]

FACTORIES = [None, IndexedVariableFactory(), IndexedVariableFactory(prefix="u")]


@pytest.mark.parametrize(("m", "ell"), SPLITS)
@pytest.mark.parametrize("factory", FACTORIES)
def test_extending_twice_equals_extending_once(
    m: int, ell: int, factory: IndexedVariableFactory | None
) -> None:
    """(F^[m])^[l] = F^[m+l].

    Eine Reduktion stabilisiert schrittweise; sie muss dort landen, wo eine
    einzige Stabilisierung landet. Der Test prueft die Namensvergabe, nicht
    die Komponenten -- die sind ohnehin Identitaeten.
    """
    F = examples.sum_and_difference()

    assert F.extend(m, factory).extend(ell, factory) == F.extend(m + ell, factory)


@pytest.mark.parametrize(("m", "ell"), SPLITS)
def test_extending_twice_survives_a_reserved_name_in_between(m: int, ell: int) -> None:
    """Derselbe Test mit einer Luecke in der Namensfolge.

    X3 ist als Koeffizientensymbol belegt, die Vergabe muss es ueberspringen
    -- in beiden Zerlegungen an derselben Stelle.
    """
    F = PolynomialMap((x, y), (sp.Symbol("X3") * x, y))

    assert F.extend(m).extend(ell) == F.extend(m + ell)


def test_extending_twice_reads_the_numbered_convention(
    numbered: PolynomialMap,
) -> None:
    """x1..x5 -> x6..x9, gleich ob in einem oder in zwei Schritten."""
    stepwise = numbered.extend(2).extend(2)

    assert stepwise == numbered.extend(4)
    assert stepwise.variables[-4:] == sp.symbols("x6 x7 x8 x9")


def test_purity_alone_does_not_give_the_composition_invariant() -> None:
    """Warum die Anforderung eigenstaendig im Protokoll steht.

    Diese Factory ist eine reine Funktion von Ring und Anzahl und kollidiert
    nie -- ``extend`` findet also nichts zu beanstanden. Trotzdem liefern
    beide Zerlegungen verschiedene Abbildungen, weil die Ringgroesse in den
    Namen eingeht statt nur in die Laufweite.
    """

    def by_ring_size(ring: PolyRing, count: int) -> tuple[sp.Symbol, ...]:
        return tuple(sp.Symbol(f"g{ring.ngens}_{i}") for i in range(1, count + 1))

    F = examples.sum_and_difference()

    assert by_ring_size(F.ring, 2) == by_ring_size(F.ring, 2)

    assert F.extend(2, by_ring_size).extend(2, by_ring_size) != F.extend(
        4, by_ring_size
    )


# --------------------------------------------------------------------------
# Verschachtelte Koeffizientendomaenen
#
# Domains verschachteln sich: ueber QQ[X3][S] steht S oben und X3 eine Ebene
# tiefer. Wer nur domain.symbols liest, findet S und uebersieht X3 -- genug,
# damit extend() eine Koordinate X3 vergibt und sie mit dem Parameter
# zusammenfaellt.
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
    """Der Fehler, den die Luecke ermoeglichte."""
    R, u, v = ring("u,v", domain)
    F = PolynomialMap.from_ring(R, (u + v, v))

    fresh = {symbol.name for symbol in F.extend(3).variables[2:]}

    assert not fresh & expected


def test_a_generator_may_not_share_a_name_with_a_nested_parameter() -> None:
    """SymPy prueft nur die oberste Domain-Ebene; hier wird tiefer geschaut."""
    X3, S = sp.symbols("X3 S")
    R, generator, other = ring("X3,w", QQ[X3][S])

    with pytest.raises(ValueError, match="coefficient indeterminate"):
        PolynomialMap.from_ring(R, (generator, other))


def test_a_generator_may_not_share_a_name_with_a_fraction_field_parameter() -> None:
    T, S = sp.symbols("T S")
    R, generator, other = ring("T,w", QQ[T].frac_field(S))

    with pytest.raises(ValueError, match="coefficient indeterminate"):
        PolynomialMap.from_ring(R, (generator, other))
