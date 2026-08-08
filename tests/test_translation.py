"""Der Translationsschritt: der erste Faktor von Proposition (1.1).

Was an vorgelegten Daten scheitern kann, ist TRA-1 und die erste Klausel von
TRA-6. TRA-3 und TRA-4 folgen aus TRA-1, TRA-2 ist eine Konstruktorinvariante,
und die ``MA^0``-Klausel von TRA-6 folgt aus der ersten -- diese vier sind hier
nur auf ihrem Erfolgspfad geprueft, weil ein Test dafuer das Objekt in einen
Zustand zwingen muesste, den es nicht erreichen kann.

Der Plan fuer dieses Arbeitspaket verlangte Fehlschlagfaelle auch fuer TRA-3,
TRA-4 und beide Klauseln von TRA-6. Beim Schreiben stellte sich heraus, dass
drei davon nicht erreichbar sind; die Roadmap ist entsprechend korrigiert.
"""

import math

import pytest
import sympy as sp

from kellermap import (
    Collision,
    LinearStep,
    PolynomialMap,
    Provenance,
    Reduction,
    Step,
    TranslationStep,
    VerificationError,
    examples,
    over_field,
)

x, y = sp.symbols("x y")
T = sp.Symbol("T")


@pytest.fixture
def keller() -> PolynomialMap:
    """Eine Keller-Abbildung in ``MA^1``, die den Ursprung festhaelt."""
    return over_field(examples.quadratic_shear())


@pytest.fixture
def moved(keller: PolynomialMap) -> PolynomialMap:
    """Dieselbe Abbildung, um ``(1, 2)`` verschoben."""
    return over_field(PolynomialMap((x, y), (x + y**2 + 1, y + 2)))


@pytest.fixture
def square() -> PolynomialMap:
    """Nicht injektiv, und um ``(1, 1)`` verschoben: traegt eine Kollision."""
    return over_field(PolynomialMap((x, y), (x**2 + 1, y + 1)))


# --------------------------------------------------------------------------
# Konstruktion
# --------------------------------------------------------------------------


def test_it_satisfies_the_step_protocol(moved: PolynomialMap) -> None:
    assert isinstance(TranslationStep.normalize(moved), Step)


def test_normalize_takes_off_F0(moved: PolynomialMap, keller: PolynomialMap) -> None:  # noqa: N802
    step = TranslationStep.normalize(moved)

    assert step.shift == (1, 2)
    assert step.target == keller
    assert step.is_normalizing


def test_a_map_in_MA0_gets_the_identity_step(keller: PolynomialMap) -> None:  # noqa: N802
    """Nicht abgelehnt, sondern verschoben um null.

    Das erspart jedem Aufrufer eine Fallunterscheidung, der nicht vorher weiss,
    ob seine Abbildung den Ursprung festhaelt.
    """
    step = TranslationStep.normalize(keller)

    assert step.shift == (0, 0)
    assert step.target == keller
    assert len(step.translation) == 0
    assert step.verify() is None


def test_build_accepts_any_constant_shift(keller: PolynomialMap) -> None:
    step = TranslationStep.build(keller, (3, -1))

    assert step.target == over_field(
        PolynomialMap((x, y), (x + y**2 - 3, y + 1)),
    )
    assert not step.is_normalizing
    assert step.verify() is None


def test_the_supplied_route_records_supplied(
    moved: PolynomialMap, keller: PolynomialMap
) -> None:
    """TRA-8: der oeffentliche Konstruktor kann nichts anderes sagen."""
    supplied = TranslationStep(moved, keller, (1, 2), normalizing=True)

    assert supplied.provenance is Provenance.SUPPLIED
    assert TranslationStep.normalize(moved).provenance is Provenance.CONSTRUCTED
    assert supplied.verify() is None


# --------------------------------------------------------------------------
# TRA-2: die Verschiebung ist konstant
# --------------------------------------------------------------------------


def test_a_shift_involving_a_generator_is_refused(keller: PolynomialMap) -> None:
    """Sonst waere die Jacobi-Matrix nicht die Einheitsmatrix."""
    with pytest.raises(ValueError, match="coefficient domain"):
        TranslationStep.build(keller, (y, 0))


def test_a_shift_outside_the_domain_is_refused() -> None:
    """Ueber ``ZZ`` ist ``1/2`` keine Konstante des Rings."""
    integral = examples.quadratic_shear()

    with pytest.raises(ValueError, match="coefficient domain"):
        TranslationStep.build(integral, (sp.Rational(1, 2), 0))


def test_a_domain_parameter_is_admitted() -> None:
    """Eine Translation um ``T`` ueber ``k[T]`` ist eine Translation.

    Dieselbe Unterscheidung wie in COL-2 und BCW-3: Parameter des
    Koeffizientenbereichs sind keine Variablen der Abbildung.
    """
    parametric = examples.parametric_shear()
    step = TranslationStep.build(parametric, (T, 1))

    assert step.shift == (T, 1)
    assert step.verify() is None


def test_a_miscounted_shift_is_refused(keller: PolynomialMap) -> None:
    with pytest.raises(ValueError, match="entries"):
        TranslationStep.build(keller, (1,))


@pytest.mark.parametrize("wrong", [None, 0, "F", (x, y)])
def test_the_maps_must_be_polynomial_maps(keller: PolynomialMap, wrong: object) -> None:
    with pytest.raises(TypeError):
        TranslationStep(wrong, keller, (0, 0))  # type: ignore[arg-type]

    with pytest.raises(TypeError):
        TranslationStep(keller, wrong, (0, 0))  # type: ignore[arg-type]


def test_the_dimensions_must_agree(keller: PolynomialMap) -> None:
    other = over_field(PolynomialMap((x,), (x**2,)))

    with pytest.raises(ValueError, match="a translation keeps it"):
        TranslationStep(keller, other, (0, 0))


# --------------------------------------------------------------------------
# TRA-1 und TRA-6: was an vorgelegten Daten scheitern kann
# --------------------------------------------------------------------------


def test_a_wrong_target_fails_TRA1(moved: PolynomialMap, keller: PolynomialMap) -> None:  # noqa: N802
    """Negativkontrolle: ohne sie sagt der Erfolgsfall nichts."""
    step = TranslationStep(moved, keller, (1, 3))

    with pytest.raises(VerificationError) as failure:
        step.verify()

    assert failure.value.obligation == "TRA-1"


def test_a_wrong_shift_fails_TRA6(keller: PolynomialMap) -> None:  # noqa: N802
    """Die Identitaet stimmt, die Behauptung ueber ``F(0)`` nicht.

    Genau der Unterschied, den TRA-6 macht: ``build`` liefert ein gueltiges
    Zertifikat, und erst das Praedikat ``normalizing`` bindet es an ``F(0)``.
    """
    step = TranslationStep.build(keller, (5, 0), normalizing=True)

    with pytest.raises(VerificationError) as failure:
        step.verify()

    assert failure.value.obligation == "TRA-6"
    assert "F(0)" in failure.value.message


def test_a_step_that_makes_no_claim_carries_no_obligation(
    keller: PolynomialMap,
) -> None:
    assert TranslationStep.build(keller, (5, 0)).verify() is None


def test_verification_is_idempotent(moved: PolynomialMap) -> None:
    """STEP-2: zweimal pruefen ist wie einmal pruefen."""
    step = TranslationStep.normalize(moved)

    assert step.verify() is None
    assert step.verify() is None


# --------------------------------------------------------------------------
# TRA-3 und TRA-5: die Faktorisierung und der Filtrationsgrad
# --------------------------------------------------------------------------


def test_the_translation_is_exhibited(moved: PolynomialMap) -> None:
    """TRA-3: ein Faktor je Eintrag ungleich null, aufsteigend."""
    factors = TranslationStep.normalize(moved).translation.factors

    assert [factor.index for factor in factors] == [0, 1]
    assert [factor.polynomial for factor in factors] == [-1, -2]


def test_only_nonzero_entries_buy_a_factor(keller: PolynomialMap) -> None:
    step = TranslationStep.build(keller, (0, 7))
    factors = step.translation.factors

    assert [factor.index for factor in factors] == [1]


def test_the_inverse_is_read_off_the_definition(moved: PolynomialMap) -> None:
    exhibited = TranslationStep.normalize(moved).translation

    assert [factor.polynomial for factor in exhibited.inverse().factors] == [2, 1]


def test_the_transformation_has_filtration_degree_minus_one(
    moved: PolynomialMap,
) -> None:
    """Es liegt in keinem ``EA^d`` mit ``d >= 0``, weil es ``MA^0`` verlaesst."""
    exhibited = TranslationStep.normalize(moved).translation

    assert exhibited.filtration_degree() == -1
    assert not exhibited.is_in_EA(0)


def test_the_step_establishes_no_level(moved: PolynomialMap) -> None:
    """TRA-5: der Grad gehoert der Transformation, nicht dem Schritt."""
    assert TranslationStep.normalize(moved).filtration_level == math.inf


def test_the_determinant_survives(moved: PolynomialMap) -> None:
    """TRA-4 auf seinem Erfolgspfad."""
    step = TranslationStep.normalize(moved)

    assert step.target.determinant() == step.source.determinant() == 1


# --------------------------------------------------------------------------
# TRA-7: Transport
# --------------------------------------------------------------------------


def test_transport_moves_the_image_and_not_the_points(square: PolynomialMap) -> None:
    collision = Collision.at(square, ((1, 0), (-1, 0)))
    step = TranslationStep.normalize(square)

    carried = step.transport(collision)

    assert carried.points == collision.points
    assert collision.image == (2, 1)
    assert carried.image == (1, 0)


def test_transport_refuses_a_collision_of_another_map(
    square: PolynomialMap, keller: PolynomialMap
) -> None:
    """STEP-3: geprueft wird vorher, nicht nur nachher."""
    step = TranslationStep.normalize(keller)
    foreign = Collision.at(square, ((1, 0), (-1, 0)))

    with pytest.raises(VerificationError):
        step.transport(foreign)


# --------------------------------------------------------------------------
# STEP-5 und die Kette
# --------------------------------------------------------------------------


def test_equality_is_by_content_including_provenance(
    moved: PolynomialMap, keller: PolynomialMap
) -> None:
    constructed = TranslationStep.normalize(moved)
    supplied = TranslationStep(moved, keller, (1, 2), normalizing=True)

    assert constructed == TranslationStep.normalize(moved)
    assert hash(constructed) == hash(TranslationStep.normalize(moved))
    assert constructed != supplied
    assert constructed != TranslationStep.build(moved, (1, 2))
    assert constructed.__eq__(42) is NotImplemented


def test_the_repr_names_the_shift_and_the_provenance(moved: PolynomialMap) -> None:
    text = repr(TranslationStep.normalize(moved))

    assert "shift=(1, 2)" in text
    assert "provenance=constructed" in text


def test_the_two_factors_of_proposition_1_1_chain(
    moved: PolynomialMap, keller: PolynomialMap
) -> None:
    """Erst die Translation, dann der Linearteil -- in dieser Reihenfolge."""
    translation = TranslationStep.normalize(moved)
    linear = LinearStep.normalize(translation.target)
    chain = Reduction([translation, linear])

    assert chain.verify() is None
    assert chain.source == moved
    assert chain.target.is_in_MA(1)


def test_a_translation_does_not_lower_the_reported_level(
    moved: PolynomialMap,
) -> None:
    """RED-6: die Stufe beschreibt das Ziel, die Translation die Quelle.

    Der BCW-Schritt entfernt ``y^2`` aus der ersten Komponente und erreicht
    ``EA^0``; die Kette meldet ``0`` und nicht ``-1``.
    """
    from kellermap.bcw import BCWStep, Fresh

    u, v = sp.symbols("u v")
    translation = TranslationStep.normalize(moved)
    linear = LinearStep.normalize(translation.target)
    bcw = BCWStep.build(linear.target, 0, Fresh(y, u), Fresh(y, v), 0)
    chain = Reduction([translation, linear, bcw])

    assert chain.verify() is None
    assert chain.filtration_level() == 0
    assert chain.dimensions() == (2, 2, 2, 4)


def test_the_linear_step_names_the_translation(moved: PolynomialMap) -> None:
    """LIN-6: die Ablehnung nennt jetzt einen Schritt, den es gibt."""
    with pytest.raises(ValueError, match="TranslationStep.normalize"):
        LinearStep.normalize(moved)
