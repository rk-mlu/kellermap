"""The two exceptions of ``kellermap.errors`` and what each carries.

Work package 2.2 of milestone 0.9 gave every constructor invariant of a step,
a collision, a reduction and a witness the identifier of the obligation it
enforces. Before it, the refusals were plain ``ValueError`` and only their
messages said what was wrong. A certificate read from a file has to cite an
obligation for every refusal, FMT-10 in ``docs/contracts.md``, and it can do
that only if the constructor says which.

The table below is the control. Each row builds one set of arguments that
breaks one invariant and names the identifier the refusal has to carry. A row
that raised the wrong identifier, or a plain ``ValueError``, fails here. The
rows follow the order in which each constructor checks, so that every row
breaks only the invariant it names.
"""

from __future__ import annotations

from collections.abc import Callable

import pytest
import sympy as sp

from kellermap import (
    Collision,
    CompressionStep,
    DescentStep,
    InvariantError,
    LinearAutomorphism,
    LinearStep,
    PolynomialMap,
    Reduction,
    SymmetricLiftStep,
    TranslationStep,
    VanishingWitness,
    VerificationError,
)
from kellermap.bcw import BCWStep, HomogenizationStep, UnipotentStep
from kellermap.bcw.step import Carried, Fresh

x, y, u, v, a, b, c, d = sp.symbols("x y u v a b c d")

SHEAR = PolynomialMap((x, y), (x + y**2, y))
"""A map over ``ZZ`` in two variables, for every constructor that takes one."""

RATIONAL = PolynomialMap((x, y), (x + sp.Rational(1, 2) * y**2, y))
"""The same shape over ``QQ``, for the compression, which needs a field."""

LINE = PolynomialMap((x,), (x,))
"""A map in one variable, which a descent cannot reduce."""

LIFTED = PolynomialMap((a, b, c, d), (a, b, c, d))
"""A target with four generators, twice the dimension of ``SHEAR``."""

STEPS = (
    BCWStep(
        SHEAR,
        PolynomialMap((x, y, u), (x + y**2, y, u)),
        0,
        Fresh(y, u),
        Carried(1),
    ),
)
"""One step that constructs, so that the reduction below has something."""


def _lift() -> SymmetricLiftStep:
    return SymmetricLiftStep(SHEAR, LIFTED, (a, b, c, d))


def _collision() -> Collision:
    return Collision(((1, 0, 0, 0), (0, 1, 0, 0)), (0, 0, 0, 0))


CASES: list[tuple[str, str, Callable[[], object]]] = [
    # BCWStep, in the order of its constructor.
    ("index", "BCW-4", lambda: BCWStep(SHEAR, SHEAR, 2, Carried(1), Carried(1))),
    (
        "level",
        "BCW-6",
        lambda: BCWStep(SHEAR, SHEAR, 0, Carried(1), Carried(1), filtration_level=2),
    ),
    (
        "carried range",
        "BCW-10",
        lambda: BCWStep(SHEAR, SHEAR, 0, Carried(2), Carried(1)),
    ),
    (
        "carried target",
        "BCW-10",
        lambda: BCWStep(SHEAR, SHEAR, 0, Carried(0), Carried(1)),
    ),
    ("carried negative", "BCW-10", lambda: Carried(-1)),
    (
        "coefficient zero",
        "BCW-11",
        lambda: BCWStep(SHEAR, SHEAR, 0, Carried(1), Carried(1), coefficient=0),
    ),
    (
        "coefficient outside",
        "BCW-11",
        lambda: BCWStep(SHEAR, SHEAR, 0, Carried(1), Carried(1), coefficient=x),
    ),
    (
        "fresh reserved",
        "BCW-2",
        lambda: BCWStep(SHEAR, SHEAR, 0, Fresh(y, x), Carried(1)),
    ),
    (
        "factor not polynomial",
        "BCW-3",
        lambda: BCWStep(SHEAR, SHEAR, 0, Fresh(1 / y, u), Carried(1)),
    ),
    (
        "one variable, two values",
        "BCW-12",
        lambda: BCWStep(SHEAR, SHEAR, 0, Fresh(y, u), Fresh(y**2, u)),
    ),
    # Collision.
    ("one point", "COL-4", lambda: Collision(((0, 0),), (0, 0))),
    ("lengths", "COL-1", lambda: Collision(((0, 0), (1,)), (0, 0))),
    ("no coordinate", "COL-1", lambda: Collision(((), ()), ())),
    ("equal points", "COL-4", lambda: Collision(((1, 0), (1, 0)), (0, 0))),
    # LinearStep and TranslationStep.
    (
        "linear dimension",
        "LIN-1",
        lambda: LinearStep(SHEAR, LINE, LinearAutomorphism()),
    ),
    ("translation dimension", "TRA-1", lambda: TranslationStep(SHEAR, LINE, (0, 0))),
    ("shift length", "TRA-1", lambda: TranslationStep(SHEAR, SHEAR, (0,))),
    ("shift outside", "TRA-2", lambda: TranslationStep(SHEAR, SHEAR, (x, 0))),
    # Reduction.
    ("no step", "RED-1", lambda: Reduction(())),
    # UnipotentStep and HomogenizationStep.
    ("unipotent count", "UNI-5", lambda: UnipotentStep(SHEAR, SHEAR, (u,))),
    ("unipotent repeated", "UNI-5", lambda: UnipotentStep(SHEAR, SHEAR, (u, u))),
    ("unipotent reserved", "UNI-5", lambda: UnipotentStep(SHEAR, SHEAR, (x, u))),
    ("homogenization reserved", "HOM-4", lambda: HomogenizationStep(SHEAR, SHEAR, x)),
    # CompressionStep, in the order of its constructor.
    (
        "basis against names",
        "CHC-5",
        lambda: CompressionStep(RATIONAL, RATIONAL, ((1, 0),), (u, v)),
    ),
    ("empty basis", "CHC-2", lambda: CompressionStep(RATIONAL, RATIONAL, (), ())),
    ("row length", "CHC-2", lambda: CompressionStep(RATIONAL, RATIONAL, ((1,),), (u,))),
    (
        "too many rows",
        "CHC-5",
        lambda: CompressionStep(
            RATIONAL, RATIONAL, ((1, 0), (0, 1), (1, 1)), (u, v, a)
        ),
    ),
    ("not a field", "CHC-2", lambda: CompressionStep(SHEAR, SHEAR, ((1, 0),), (u,))),
    (
        "entry outside",
        "CHC-2",
        lambda: CompressionStep(RATIONAL, RATIONAL, ((x, 0),), (u,)),
    ),
    (
        "dependent",
        "CHC-2",
        lambda: CompressionStep(RATIONAL, RATIONAL, ((1, 0), (2, 0)), (u, v)),
    ),
    (
        "compression reserved",
        "CHC-5",
        lambda: CompressionStep(RATIONAL, RATIONAL, ((1, 0),), (x,)),
    ),
    (
        "compression repeated",
        "CHC-5",
        lambda: CompressionStep(RATIONAL, RATIONAL, ((1, 0), (0, 1)), (u, u)),
    ),
    # SymmetricLiftStep.
    ("lift count", "SYM-5", lambda: SymmetricLiftStep(SHEAR, LIFTED, (a, b))),
    ("lift repeated", "SYM-5", lambda: SymmetricLiftStep(SHEAR, LIFTED, (a, a, c, d))),
    ("lift reserved", "SYM-5", lambda: SymmetricLiftStep(SHEAR, LIFTED, (x, b, c, d))),
    # DescentStep.
    ("descent index", "DSC-1", lambda: DescentStep(SHEAR, 2)),
    ("descent from one variable", "DSC-2", lambda: DescentStep(LINE, 0)),
    # VanishingWitness.
    ("depth", "VAN-3", lambda: VanishingWitness(_lift(), _collision(), depth=0)),
]


@pytest.mark.parametrize(
    ("obligation", "build"),
    [(obligation, build) for _, obligation, build in CASES],
    ids=[name for name, _, _ in CASES],
)
def test_a_refused_construction_names_its_obligation(
    obligation: str, build: Callable[[], object]
) -> None:
    """The refusal is an ``InvariantError`` with the identifier of the row."""
    with pytest.raises(InvariantError) as refusal:
        build()

    assert refusal.value.obligation == obligation
    assert f"[{obligation}]" in str(refusal.value)


def test_the_arguments_of_the_table_construct_when_nothing_is_broken() -> None:
    """The fixtures of the table are valid by themselves.

    Without this, a row could pass because a fixture broke an invariant that
    happens to carry the same identifier, and not because of the change the
    row makes.
    """
    assert Reduction(STEPS).source == SHEAR
    assert VanishingWitness(_lift(), _collision()).depth == 2
    assert CompressionStep(RATIONAL, RATIONAL, ((1, 0),), (u,)).variables == (u,)


def test_an_invariant_error_is_a_value_error() -> None:
    """Code that caught a ``ValueError`` from a constructor still catches it."""
    with pytest.raises(ValueError, match=r"\[COL-4\] Points 0 and 1 are equal"):
        Collision(((1, 0), (1, 0)), (0, 0))


def test_an_invariant_error_carries_its_parts() -> None:
    refusal = InvariantError("BCW-10", "a slot names the target component")

    assert refusal.obligation == "BCW-10"
    assert refusal.message == "a slot names the target component"
    assert str(refusal) == "[BCW-10] a slot names the target component"


# --------------------------------------------------------------------------
# The location of a VerificationError
# --------------------------------------------------------------------------


def test_a_failure_without_a_place_has_no_location() -> None:
    failure = VerificationError("COL-3", "something failed")

    assert failure.location is None
    assert str(failure) == "[COL-3] something failed"


def test_a_step_gives_its_location() -> None:
    failure = VerificationError("BCW-1", "something failed", step=4)

    assert failure.location == "step 4"
    assert str(failure) == "[BCW-1] in step 4 something failed"


def test_a_location_can_name_a_place_that_is_not_a_step() -> None:
    """The places a file has and a reduction does not."""
    failure = VerificationError("FMT-6", "a float was read", location="map 0")

    assert failure.step is None
    assert failure.location == "map 0"
    assert "in map 0" in str(failure)


def test_located_at_sets_both_the_step_and_the_location() -> None:
    located = VerificationError("COL-3", "something failed").located_at(2)

    assert (located.step, located.location) == (2, "step 2")
