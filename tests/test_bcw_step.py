"""Proposition (3.1) als Zertifikat.

Der Schwerpunkt liegt auf BCW-1: an einem *vorgelegten* Ziel muss die Pruefung
scheitern koennen, sonst prueft sie nichts. Die Einheitstests arbeiten dafuer
mit einer kleinen Abbildung, deren Schritt sich von Hand hinschreiben laesst.

Am Ende steht der erste Schritt der Referenzreduktion mit ausgeschriebenem
Ziel. Seine erste Komponente ist bereits die erste Komponente von BCW17, weil
kein spaeterer Schritt sie mehr anfasst.
"""

import pytest
import sympy as sp

from kellermap import (
    Collision,
    PolynomialMap,
    Provenance,
    Reduction,
    Step,
    VerificationError,
    over_field,
)
from kellermap.bcw import BCWStep
from kellermap.reduction import LinearStep

x1, x2, x3, x4, x5 = sp.symbols("x1 x2 x3 x4 x5")

# F = (x1 + x2^2 x3^2, x2, x3). Der Spitzenterm x2^2 x3^2 der ersten
# Komponente faktorisiert als P * Q mit P = x2^2 und Q = x3^2.
SIMPLE = over_field(PolynomialMap((x1, x2, x3), (x1 + x2**2 * x3**2, x2, x3)))

P = x2**2
Q = x3**2
FRESH = (x4, x5)

# G o F^[2] o H, von Hand: (F_1 - P Q) - x4 Q - P x5 - x4 x5.
SIMPLE_TARGET = PolynomialMap(
    (x1, x2, x3, x4, x5),
    (
        x1 - x4 * x3**2 - x2**2 * x5 - x4 * x5,
        x2,
        x3,
        x4 + x2**2,
        x5 + x3**2,
    ),
)


@pytest.fixture
def step() -> BCWStep:
    return BCWStep(SIMPLE, over_field(SIMPLE_TARGET), 0, P, Q, FRESH)


# --------------------------------------------------------------------------
# Konstruktion
# --------------------------------------------------------------------------


def test_a_step_satisfies_the_protocol(step: BCWStep) -> None:
    assert isinstance(step, Step)


def test_the_index_must_address_a_component() -> None:
    with pytest.raises(ValueError, match="out of range"):
        BCWStep(SIMPLE, over_field(SIMPLE_TARGET), 3, P, Q, FRESH)


def test_the_index_must_be_an_integer() -> None:
    with pytest.raises(TypeError, match="must be an integer"):
        BCWStep(SIMPLE, over_field(SIMPLE_TARGET), True, P, Q, FRESH)


def test_exactly_two_fresh_variables() -> None:
    with pytest.raises(ValueError, match="exactly two variables"):
        BCWStep(SIMPLE, over_field(SIMPLE_TARGET), 0, P, Q, (x4,))


def test_the_filtration_level_is_zero_or_one() -> None:
    with pytest.raises(ValueError, match="must be 0 or 1"):
        BCWStep(SIMPLE, over_field(SIMPLE_TARGET), 0, P, Q, FRESH, 2)


def test_BCW3_P_and_Q_live_over_the_source() -> None:  # noqa: N802
    """Ein Faktor, der die frischen Variablen traegt, ist gar nicht erst baubar."""
    with pytest.raises(ValueError, match="polynomials in the variables"):
        BCWStep(SIMPLE, over_field(SIMPLE_TARGET), 0, x4 * x2, Q, FRESH)


# --------------------------------------------------------------------------
# G und H
# --------------------------------------------------------------------------


def test_the_factors_are_derived_not_stored(step: BCWStep) -> None:
    """G und H folgen aus (index, P, Q, variables), Formel (1)."""
    assert len(step.G) == 1
    assert len(step.H) == 2
    assert step.G.factors[0].variable == x1
    assert step.G.factors[0].polynomial == -x4 * x5
    assert step.H.factors[0].polynomial == P
    assert step.H.factors[1].polynomial == Q


def test_G_lies_in_EA1(step: BCWStep) -> None:  # noqa: N802
    """Die Verschiebung -x4 x5 hat Ordnung 2."""
    assert step.G.is_in_EA(1)


def test_the_two_factors_of_H_commute(step: BCWStep) -> None:  # noqa: N802
    """BCW-3 macht die Reihenfolge in H gleichgueltig."""
    forward, backward = step.H.factors
    swapped = type(step.H)([backward, forward])

    assert swapped.to_polynomial_map() == step.H.to_polynomial_map()


def test_the_stabilized_map_carries_the_fresh_variables(step: BCWStep) -> None:
    assert step.stabilized.variables == (x1, x2, x3, x4, x5)
    assert step.stabilized.components[3:] == (x4, x5)


# --------------------------------------------------------------------------
# BCW-1 bis BCW-7
# --------------------------------------------------------------------------


def test_a_correct_step_verifies(step: BCWStep) -> None:
    assert step.verify() is None
    assert step.verify() is None


def test_BCW1_a_target_that_is_not_the_composite() -> None:  # noqa: N802
    """Ein Vorzeichen daneben, und die Identitaet faellt."""
    wrong = PolynomialMap(
        (x1, x2, x3, x4, x5),
        (
            x1 - x4 * x3**2 - x2**2 * x5 + x4 * x5,
            x2,
            x3,
            x4 + x2**2,
            x5 + x3**2,
        ),
    )

    with pytest.raises(VerificationError) as failure:
        BCWStep(SIMPLE, over_field(wrong), 0, P, Q, FRESH).verify()

    assert failure.value.obligation == "BCW-1"


def test_BCW1_the_wrong_factorization() -> None:  # noqa: N802
    """P * Q muss der entfernte Teil sein, nicht irgendein Produkt."""
    with pytest.raises(VerificationError) as failure:
        BCWStep(SIMPLE, over_field(SIMPLE_TARGET), 0, x2, x3, FRESH).verify()

    assert failure.value.obligation == "BCW-1"


def test_BCW2_a_target_of_the_wrong_dimension() -> None:  # noqa: N802
    with pytest.raises(VerificationError) as failure:
        BCWStep(SIMPLE, SIMPLE, 0, P, Q, FRESH).verify()

    assert failure.value.obligation == "BCW-2"


def test_BCW2_a_target_with_other_variables() -> None:  # noqa: N802
    renamed = PolynomialMap(
        sp.symbols("x1 x2 x3 u v"),
        SIMPLE_TARGET.components,
    )

    with pytest.raises(VerificationError) as failure:
        BCWStep(SIMPLE, over_field(renamed), 0, P, Q, FRESH).verify()

    assert failure.value.obligation == "BCW-2"


def test_a_fresh_variable_that_is_not_fresh() -> None:
    """Frueh abgelehnt: sonst bezeichneten zwei Koordinaten einen Generator."""
    with pytest.raises(ValueError, match="already in use"):
        BCWStep(SIMPLE, over_field(SIMPLE_TARGET), 0, P, Q, (x2, x5))


def test_the_two_fresh_variables_must_differ() -> None:
    with pytest.raises(ValueError, match="must be distinct"):
        BCWStep(SIMPLE, over_field(SIMPLE_TARGET), 0, P, Q, (x4, x4))


def test_BCW4_the_component_need_not_be_the_first() -> None:  # noqa: N802
    """Eine Reduktion erreicht Komponenten, die ein frueherer Schritt anlegte."""
    source = over_field(PolynomialMap((x1, x2, x3), (x1, x2 + x1**2 * x3**2, x3)))
    built = BCWStep.build(source, 1, x1**2, x3**2, FRESH)

    assert built.verify() is None
    assert built.index == 1


def test_BCW6_a_level_that_is_not_reached() -> None:  # noqa: N802
    """Ein linearer Term in Q druckt H nach EA^0."""
    source = over_field(PolynomialMap((x1, x2, x3), (x1 + x2 * x3, x2, x3)))

    with pytest.raises(VerificationError) as failure:
        BCWStep.build(source, 0, x2, x3, FRESH, filtration_level=1).verify()

    assert failure.value.obligation == "BCW-6"


def test_BCW6_the_weaker_claim_is_accepted() -> None:  # noqa: N802
    """EA^0 zu behaupten, wo EA^1 gilt, ist wahr und wird angenommen."""
    modest = BCWStep(
        SIMPLE, over_field(SIMPLE_TARGET), 0, P, Q, FRESH, filtration_level=0
    )

    assert modest.verify() is None
    assert modest.filtration_level == 0
    assert modest.attained_filtration_level == 1


def test_BCW7_the_determinant_is_unchanged(step: BCWStep) -> None:  # noqa: N802
    assert SIMPLE.determinant() == 1
    assert step.target.determinant() == 1


# --------------------------------------------------------------------------
# BCW-8: Transport
# --------------------------------------------------------------------------


def test_BCW8_the_fresh_coordinates_become_minus_P_and_minus_Q() -> None:  # noqa: N802
    source = over_field(PolynomialMap((x1, x2, x3), (x1**2, x2, x3)))
    built = BCWStep.build(source, 0, x2**2, x3**2, FRESH)
    collision = Collision.at(source, ((1, 2, 3), (-1, 2, 3)))

    carried = built.transport(collision)

    assert carried.points[0] == (1, 2, 3, -4, -9)
    assert carried.points[1] == (-1, 2, 3, -4, -9)
    assert carried.image == (1, 2, 3, 0, 0)


def test_BCW8_the_number_of_points_is_preserved() -> None:  # noqa: N802
    source = over_field(PolynomialMap((x1, x2, x3), (x1**2, x2, x3)))
    built = BCWStep.build(source, 0, x2**2, x3**2, FRESH)
    collision = Collision.at(source, ((1, 2, 3), (-1, 2, 3)))

    assert len(built.transport(collision)) == len(collision)


def test_transport_rejects_a_collision_of_another_map(step: BCWStep) -> None:
    with pytest.raises(VerificationError) as failure:
        step.transport(Collision(((1, 2, 3), (-1, 2, 3)), (0, 0, 0)))

    assert failure.value.obligation == "COL-3"


# --------------------------------------------------------------------------
# BCW-9: Provenienz
# --------------------------------------------------------------------------


def test_a_supplied_target_is_recorded_as_such(step: BCWStep) -> None:
    assert step.provenance is Provenance.SUPPLIED


def test_build_records_the_target_as_constructed() -> None:
    built = BCWStep.build(SIMPLE, 0, P, Q, FRESH)

    assert built.provenance is Provenance.CONSTRUCTED
    assert built.target == over_field(SIMPLE_TARGET)
    assert built.verify() is None


def test_a_reduction_takes_the_weaker_provenance(step: BCWStep) -> None:
    assert Reduction([step]).provenance is Provenance.SUPPLIED
    assert (
        Reduction([BCWStep.build(SIMPLE, 0, P, Q, FRESH)]).provenance
        is Provenance.CONSTRUCTED
    )


# --------------------------------------------------------------------------
# Wertsemantik
# --------------------------------------------------------------------------


def test_equality_and_hash(step: BCWStep) -> None:
    twin = BCWStep(SIMPLE, over_field(SIMPLE_TARGET), 0, P, Q, FRESH)

    assert step == twin
    assert hash(step) == hash(twin)
    assert step != object()


def test_repr_names_the_essentials(step: BCWStep) -> None:
    assert "index=0" in repr(step)
    assert "3->5" in repr(step)


# --------------------------------------------------------------------------
# Regression: der erste Schritt der Referenzreduktion, mit vorgelegtem Ziel
# --------------------------------------------------------------------------

ALPOEGE = over_field(
    PolynomialMap(
        (x1, x2, x3),
        (
            (1 + x1 * x2) ** 3 * x3 + x2**2 * (1 + x1 * x2) * (4 + 3 * x1 * x2),
            x2 + 3 * x1 * (1 + x1 * x2) ** 2 * x3 + 3 * x1 * x2**2 * (4 + 3 * x1 * x2),
            2 * x1 - 3 * x1**2 * x2 - x1**3 * x3,
        ),
    )
)

# Ausgeschrieben, nicht gerechnet: nur so kann BCW-1 ueberhaupt scheitern.
FIRST_TARGET = PolynomialMap(
    (x1, x2, x3, x4, x5),
    (
        -3 * x1**2 * x2 / 2 - x1**2 * x4 + x1 * x3 * x5 / 2 + x1 - x4 * x5,
        3 * x1**3 * x2**2 * x3
        + 9 * x1**2 * x2**3
        + 6 * x1**2 * x2 * x3
        + 12 * x1 * x2**2
        + 3 * x1 * x3
        + x2,
        x1**3 * x2**3 * x3
        + 3 * x1**2 * x2**4
        + 3 * x1**2 * x2**2 * x3
        + 7 * x1 * x2**3
        + 3 * x1 * x2 * x3
        + 4 * x2**2
        + x3,
        -x1 * x3 / 2 + x4,
        x1**2 + x5,
    ),
)


@pytest.fixture(scope="module")
def first_step() -> BCWStep:
    normalization = LinearStep.normalize(ALPOEGE)

    return BCWStep(
        normalization.target,
        over_field(FIRST_TARGET),
        0,
        -x1 * x3 / 2,
        x1**2,
        (x4, x5),
        filtration_level=1,
    )


def test_the_first_step_of_the_reference_reduction(first_step: BCWStep) -> None:
    assert first_step.provenance is Provenance.SUPPLIED
    assert first_step.verify() is None


def test_the_first_component_is_already_the_one_BCW17_carries(  # noqa: N802
    first_step: BCWStep,
) -> None:
    """Kein spaeterer Schritt fasst sie noch an."""
    expected = -3 * x1**2 * x2 / 2 - x1**2 * x4 + x1 * x3 * x5 / 2 + x1 - x4 * x5

    assert sp.expand(first_step.target.components[0] - expected) == 0


def test_the_normalization_and_the_first_step_chain(first_step: BCWStep) -> None:
    chain = Reduction([LinearStep.normalize(ALPOEGE), first_step])

    assert chain.verify() is None
    assert chain.dimensions() == (3, 3, 5)
    assert chain.degrees() == (7, 7, 7)
    assert chain.target.determinant() == 1


def test_the_collision_survives_the_first_step(first_step: BCWStep) -> None:
    """Die vierte und fuenfte Koordinate von BCW17, an drei Punkten."""
    chain = Reduction([LinearStep.normalize(ALPOEGE), first_step])
    collision = Collision.at(
        ALPOEGE,
        (
            (0, 0, sp.Rational(-1, 4)),
            (1, sp.Rational(-3, 2), sp.Rational(13, 2)),
            (-1, sp.Rational(3, 2), sp.Rational(13, 2)),
        ),
    )

    carried = chain.transport(collision)

    assert len(carried) == 3
    assert carried.points[0] == (0, 0, sp.Rational(-1, 4), 0, 0)
    assert carried.points[1] == (
        1,
        sp.Rational(-3, 2),
        sp.Rational(13, 2),
        sp.Rational(13, 4),
        -1,
    )
    assert carried.points[2] == (
        -1,
        sp.Rational(3, 2),
        sp.Rational(13, 2),
        sp.Rational(-13, 4),
        -1,
    )
    assert carried.image == (0, 0, sp.Rational(-1, 4), 0, 0)
