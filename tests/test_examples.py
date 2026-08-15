"""The example maps: what they are and what they may not be.

The criterion this module defines is a checked property here and not an
intention. Every map in it is a Keller map, so its Jacobian determinant is a
non-zero constant. Without this test the name of the module would be a claim
that nobody follows up.
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
    """Thirteen small maps that recur, and the two reductions.

    And three collisions, which are not maps and are therefore not covered by
    the criteria below.
    """
    assert len(NAMES) == 15
    assert len(COLLISIONS) == 3


@pytest.mark.parametrize("name", NAMES)
def test_every_example_is_a_keller_map(name: str) -> None:
    """The criterion that decides inclusion.

    A determinant with a free variable is not a constant, and zero is not a
    unit. Either one excludes a map.
    """
    determinant = getattr(examples, name)().determinant()

    assert determinant.free_symbols == set()
    assert determinant != 0


@pytest.mark.parametrize("name", NAMES)
def test_every_example_is_a_polynomial_map(name: str) -> None:
    assert isinstance(getattr(examples, name)(), PolynomialMap)


@pytest.mark.parametrize("name", NAMES + COLLISIONS)
def test_every_example_is_a_pure_function(name: str) -> None:
    """Two calls give equal maps and no shared objects.

    As with ``VariableFactory``: an example map that differs between two calls
    could not be found again within one test run.
    """
    first, second = getattr(examples, name)(), getattr(examples, name)()

    assert first == second
    assert first is not second


@pytest.mark.parametrize("name", ALL)
def test_every_example_is_documented(name: str) -> None:
    """The docstring names the map. Without it the name is a guess."""
    assert (getattr(examples, name).__doc__ or "").strip()


# --------------------------------------------------------------------------
# What the individual maps are
# --------------------------------------------------------------------------


def test_the_parameter_is_not_a_coordinate() -> None:
    """``T`` belongs to the coefficient domain and not to the map.

    Exactly the distinction COL-2, BCW-3 and TRA-2 rest on.
    """
    parametric = examples.parametric_shear()

    assert str(parametric.ring.domain) == "ZZ[T]"
    assert sp.Symbol("T") not in parametric.variables


def test_the_unit_translation_lies_outside_MA0() -> None:  # noqa: N802
    """The source ``TranslationStep`` exists for."""
    outside = examples.unit_translation()

    assert outside.filtration_degree() == -1
    assert not outside.is_in_MA(0)


def test_alpoeges_map_has_degree_seven_and_determinant_minus_two() -> None:
    """Mathematics from another source; provenance in ``docs/references.md``."""
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
    """Why it is the usual source for a ``BCWStep``."""
    source = examples.factorable_shear()
    _, second, third = source.variables

    assert source.components[0] - source.variables[0] == second**2 * third**2


def test_not_every_example_has_determinant_one() -> None:
    """Otherwise no test checks Keller against unimodular."""
    determinants = {getattr(examples, name)().determinant() for name in NAMES}

    assert determinants != {1}
    assert examples.sum_and_difference().determinant() == -2
    assert examples.doubled_shear().determinant() == 2


# --------------------------------------------------------------------------
# The reference reductions and their collisions
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
    """Otherwise the pairing would be a similarity of names only."""
    collision = getattr(examples, collision_name)()

    assert collision.verify(getattr(examples, map_name)()) is None
    assert len(collision.points) == 3


def test_the_reference_reductions_are_cubic_and_normalized() -> None:
    """Both begin with the linear normalisation, so the determinant is one."""
    seventeen, fifteen = examples.bcw17(), examples.alpoege15()

    assert (seventeen.dimension, seventeen.degree()) == (17, 3)
    assert (fifteen.dimension, fifteen.degree()) == (15, 3)
    assert seventeen.determinant() == fifteen.determinant() == 1


def test_the_reductions_reduce_alpoeges_map() -> None:
    """The degree falls from seven to three and the dimension rises."""
    source = examples.alpoege()

    assert source.degree() == 7
    assert examples.bcw17().degree() == examples.alpoege15().degree() == 3
    assert source.dimension < examples.alpoege15().dimension


def test_the_reference_reductions_are_over_a_field_and_the_source_is_not() -> None:
    """The coefficient domain follows from the normalisation, not from style.

    The linear normalisation of Chapter II, Proposition (1.1), divides by the
    determinant, so ``bcw17`` and ``alpoege15`` carry proper fractions and live
    over ``QQ``. Alpoege's map itself is not normalised and lies over ``ZZ``.

    A ``BCWStep`` preserves the domain, so the domain of the source fixes that
    of every reachable map. This is a statement about the search space, and
    ``roadmap.md`` develops it for 0.5.
    """
    source = examples.alpoege()

    assert source.ring.domain.is_ZZ
    assert source.determinant() == -2

    for reduction in (examples.bcw17(), examples.alpoege15()):
        assert reduction.ring.domain.is_QQ
        assert reduction.determinant() == 1
        assert any(
            sp.Rational(coefficient).q != 1
            for component in reduction.to_polynomials()
            for coefficient in component.coeffs()
        )
