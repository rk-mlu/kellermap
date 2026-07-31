"""Namensgebung fuer Stabilisierungsvariablen.

Die Tests halten zwei Zusagen fest, an denen spaetere Reduktionen haengen:
dass eine Factory eine reine Funktion ist, und dass ``extend`` ihr Ergebnis
prueft statt es zu glauben.
"""

import pytest
import sympy as sp

from bcw import (
    DEFAULT_VARIABLE_FACTORY,
    IndexedVariableFactory,
    PolynomialMap,
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
    F = PolynomialMap((x, y), (x + y, x - y))
    G = PolynomialMap((x, y), (x + y, x - y))

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
    F = PolynomialMap((x, y), (x + y, x - y))

    assert F.extend(2).variables == (x, y, sp.Symbol("X3"), sp.Symbol("X4"))


def test_fallback_prefix_on_mixed_conventions() -> None:
    """Uneinheitliche Praefixe geben keine Konvention her."""
    a1, b2 = sp.symbols("a1 b2")
    F = PolynomialMap((a1, b2), (a1, b2))

    assert F.extend(1).variables[-1] == sp.Symbol("X3")


def test_explicit_prefix_overrides_the_convention() -> None:
    """Der Sinn der Injektion: eine Reduktion kann Traegervariablen benennen."""
    F = PolynomialMap((x, y), (x + y, x - y))

    extended = F.extend(3, IndexedVariableFactory(prefix="u"))

    assert extended.variables[-3:] == sp.symbols("u1 u2 u3")


# --------------------------------------------------------------------------
# Kollisionen
# --------------------------------------------------------------------------


def test_reserved_names_cover_the_coefficient_domain() -> None:
    """T in k[T] ist kein Generator, sein Name ist trotzdem belegt."""
    F = PolynomialMap((x, y), (T * x + y, x))

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
    F = PolynomialMap((x, y), (x + y, x - y))

    def colliding(ring: object, count: int) -> tuple[sp.Symbol, ...]:
        return (x,)

    with pytest.raises(ValueError, match="already in use"):
        F.extend(1, colliding)


def test_extend_rejects_a_wrong_count() -> None:
    F = PolynomialMap((x, y), (x + y, x - y))

    def too_few(ring: object, count: int) -> tuple[sp.Symbol, ...]:
        return (sp.Symbol("u1"),)

    with pytest.raises(ValueError, match="returned 1 names, expected 2"):
        F.extend(2, too_few)


def test_extend_rejects_duplicates() -> None:
    F = PolynomialMap((x, y), (x + y, x - y))

    def duplicated(ring: object, count: int) -> tuple[sp.Symbol, ...]:
        return (sp.Symbol("u1"), sp.Symbol("u1"))

    with pytest.raises(ValueError, match="duplicate names"):
        F.extend(2, duplicated)


def test_extend_rejects_non_symbols() -> None:
    F = PolynomialMap((x, y), (x + y, x - y))

    def not_symbols(ring: object, count: int) -> tuple[sp.Expr, ...]:
        return (x * y,)

    with pytest.raises(TypeError, match="SymPy symbols"):
        F.extend(1, not_symbols)  # type: ignore[arg-type]
