"""Die Beispielabbildungen: was sie sind und was sie nicht sein duerfen.

Das Kriterium, das dieses Modul definiert, ist hier gepruefte Eigenschaft und
nicht Absicht: jede Abbildung darin ist eine Keller-Abbildung, ihre
Jacobi-Determinante also eine Konstante ungleich null. Ohne diesen Test waere
der Name des Moduls eine Behauptung, die niemand nachhaelt.
"""

import inspect

import pytest
import sympy as sp

from kellermap import PolynomialMap, examples


def named() -> list[tuple[str, object]]:
    """Return every public example function of the module, in a fixed order."""
    return sorted(
        (name, member)
        for name, member in inspect.getmembers(examples, inspect.isfunction)
        if not name.startswith("_") and member.__module__ == examples.__name__
    )


ALL = [name for name, _ in named()]
NAMES = [name for name in ALL if isinstance(getattr(examples, name)(), PolynomialMap)]
COLLISIONS = [name for name in ALL if name not in NAMES]


def test_the_module_holds_what_it_says_it_holds() -> None:
    """Dreizehn wiederholte kleine Abbildungen, dazu die beiden Reduktionen.

    Und drei Kollisionen, die keine Abbildungen sind und deshalb von den
    Kriterien unten nicht erfasst werden.
    """
    assert len(NAMES) == 15
    assert len(COLLISIONS) == 3


@pytest.mark.parametrize("name", NAMES)
def test_every_example_is_a_keller_map(name: str) -> None:
    """Das Kriterium, das ueber die Aufnahme entscheidet.

    Eine Determinante mit einer freien Variablen ist keine Konstante, und null
    ist keine Einheit. Beides schliesst aus.
    """
    determinant = getattr(examples, name)().determinant()

    assert determinant.free_symbols == set()
    assert determinant != 0


@pytest.mark.parametrize("name", NAMES)
def test_every_example_is_a_polynomial_map(name: str) -> None:
    assert isinstance(getattr(examples, name)(), PolynomialMap)


@pytest.mark.parametrize("name", NAMES + COLLISIONS)
def test_every_example_is_a_pure_function(name: str) -> None:
    """Zwei Aufrufe geben gleiche Abbildungen und keine geteilten Objekte.

    Wie ``VariableFactory``: eine Beispielabbildung, die sich zwischen zwei
    Aufrufen unterscheidet, waere in einem Testlauf nicht wiederfindbar.
    """
    first, second = getattr(examples, name)(), getattr(examples, name)()

    assert first == second
    assert first is not second


@pytest.mark.parametrize("name", ALL)
def test_every_example_is_documented(name: str) -> None:
    """Der Docstring nennt die Abbildung; ohne ihn ist der Name eine Vermutung."""
    assert (getattr(examples, name).__doc__ or "").strip()


# --------------------------------------------------------------------------
# Was die einzelnen Abbildungen sind
# --------------------------------------------------------------------------


def test_the_parameter_is_not_a_coordinate() -> None:
    """``T`` gehoert dem Koeffizientenbereich, nicht der Abbildung.

    Genau die Unterscheidung, auf der COL-2, BCW-3 und TRA-2 beruhen.
    """
    parametric = examples.parametric_shear()

    assert str(parametric.ring.domain) == "ZZ[T]"
    assert sp.Symbol("T") not in parametric.variables


def test_the_unit_translation_lies_outside_MA0() -> None:  # noqa: N802
    """Die Quelle, fuer die es ``TranslationStep`` gibt."""
    outside = examples.unit_translation()

    assert outside.filtration_degree() == -1
    assert not outside.is_in_MA(0)


def test_alpoeges_map_has_degree_seven_and_determinant_minus_two() -> None:
    """Fremde Mathematik; Herkunft in ``docs/references.md``."""
    source = examples.alpoege()

    assert source.dimension == 3
    assert source.degree() == 7
    assert source.determinant() == -2


def test_two_coordinates_may_carry_the_same_value() -> None:
    paired = examples.paired_shear()

    assert paired.carrier_indices == (0, 1, 2, 3)
    assert paired.components[2] - paired.variables[2] == (
        paired.components[3] - paired.variables[3]
    )


def test_the_product_shear_is_short_a_product_of_two_coordinates() -> None:
    shape = examples.product_shear()

    assert (
        shape.components[0]
        == shape.variables[0] - shape.variables[2] * (shape.variables[3])
    )


def test_the_displacement_of_the_factorable_shear_factors() -> None:
    """Warum sie die uebliche Quelle fuer einen ``BCWStep`` ist."""
    source = examples.factorable_shear()
    _, second, third = source.variables

    assert source.components[0] - source.variables[0] == second**2 * third**2


def test_not_every_example_has_determinant_one() -> None:
    """Sonst pruefte kein Test die Unterscheidung Keller gegen unimodular."""
    determinants = {getattr(examples, name)().determinant() for name in NAMES}

    assert determinants != {1}
    assert examples.sum_and_difference().determinant() == -2
    assert examples.doubled_shear().determinant() == 2


# --------------------------------------------------------------------------
# Die Referenzreduktionen und ihre Kollisionen
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("map_name", "collision_name"),
    [
        ("alpoege", "alpoege_collision"),
        ("bcw17", "bcw17_collision"),
        ("alpoege15", "alpoege15_collision"),
    ],
)
def test_each_collision_belongs_to_its_map(map_name: str, collision_name: str) -> None:
    """Sonst waere die Zusammengehoerigkeit nur eine Namensaehnlichkeit."""
    collision = getattr(examples, collision_name)()

    assert collision.verify(getattr(examples, map_name)()) is None
    assert len(collision.points) == 3


def test_the_reference_reductions_are_cubic_and_normalized() -> None:
    """Beide beginnen mit der linearen Normalisierung, also Determinante eins."""
    seventeen, fifteen = examples.bcw17(), examples.alpoege15()

    assert (seventeen.dimension, seventeen.degree()) == (17, 3)
    assert (fifteen.dimension, fifteen.degree()) == (15, 3)
    assert seventeen.determinant() == fifteen.determinant() == 1


def test_the_reductions_reduce_alpoeges_map() -> None:
    """Der Grad faellt von sieben auf drei, die Dimension steigt."""
    source = examples.alpoege()

    assert source.degree() == 7
    assert examples.bcw17().degree() == examples.alpoege15().degree() == 3
    assert source.dimension < examples.alpoege15().dimension
