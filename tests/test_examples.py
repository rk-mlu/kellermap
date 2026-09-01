"""The example maps: what they are and what they may not be.

The criterion this module defines is a checked property here and not an
intention. Every map in it is a Keller map, so its Jacobian determinant is a
non-zero constant. Without this test the name of the module would be a claim
that nobody follows up.
"""

import importlib.util
import inspect
import sys
from pathlib import Path

import pytest
import sympy as sp

from kellermap import (
    LinearStep,
    PolynomialMap,
    Reduction,
    enumerate_candidates,
    examples,
    over_field,
    peel,
)
from kellermap.bcw import BCWStep


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
    """Thirteen small maps that recur, four reductions, and the four sources.

    And eight collisions, which are not maps and are therefore not covered by
    the criteria below.
    """
    assert len(NAMES) == 20
    assert len(COLLISIONS) == 8


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
    ("map_name", "collision_name", "points"),
    [
        ("alpoege", "alpoege_collision", 3),
        ("bcw17", "bcw17_collision", 3),
        ("alpoege15", "alpoege15_collision", 3),
        ("gao_quartic", "gao_quartic_collision", 3),
        ("alpoege13", "alpoege13_collision", 3),
        ("alpoege12", "alpoege12_collision", 3),
        ("thompson24_homogeneous", "thompson24_homogeneous_collision", 2),
        ("spacerat11", "spacerat11_collision", 3),
    ],
)
def test_each_collision_belongs_to_its_map(
    map_name: str, collision_name: str, points: int
) -> None:
    """Otherwise the pairing would be a similarity of names only.

    The count is stated per row rather than once for all. It was three
    everywhere while every collision descended from Alpoege's, and Thompson's
    map has two.
    """
    collision = getattr(examples, collision_name)()

    assert collision.verify(getattr(examples, map_name)()) is None
    assert len(collision.points) == points


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


# --------------------------------------------------------------------------
# The second source map
#
# Everything below recomputes a claim of Theorem 3.5 or of the paper's text.
# Agreement is evidence about mathematics external to this project, which is
# what a second source is worth and what a second example would not be.
# --------------------------------------------------------------------------


def test_the_quartic_map_matches_theorem_three_five() -> None:
    """Component degrees 4, 11, 12 and Jacobian determinant identically 2."""
    quartic = examples.gao_quartic()
    degrees = [
        sp.Poly(component, *quartic.variables).total_degree()
        for component in quartic.components
    ]

    assert degrees == [4, 11, 12]
    assert quartic.determinant() == 2


def test_the_divisions_of_the_paper_come_out_exact() -> None:
    """The paper states the divisibility; the example transcribes the quotient.

    ``PolynomialMap`` refuses a component that is not a polynomial, so a
    division that did not come out exact would fail at construction rather than
    leave a rational function standing. This test says that the refusal is what
    is relied on, so that removing the ``cancel`` is not mistaken for a
    simplification.
    """
    quartic = examples.gao_quartic()

    for component in quartic.components:
        assert sp.together(component).is_polynomial(*quartic.variables)


def test_the_quartic_map_is_not_normalized() -> None:
    """Determinant 2, like Alpoege's -2, and for the same reason.

    Neither source map has had the linear normalisation of Chapter II,
    Proposition (1.1), applied to it. A reduction of either begins with it.
    """
    quartic = examples.gao_quartic()

    assert quartic.determinant() == 2
    assert quartic.ring.domain.is_QQ


def test_the_quartic_collision_lives_over_a_quadratic_extension() -> None:
    """What makes this collision different from every other one here.

    Two of the three points carry ``sqrt(-23)``. That is inside what
    ``kellermap.canonical`` claims to decide, and the module says where the
    claim stops.
    """
    collision = examples.gao_quartic_collision()
    root = sp.sqrt(23) * sp.I
    carried = [
        point
        for point in collision.points
        if any(
            root in coordinate.free_symbols or coordinate.has(root)
            for coordinate in point
        )
    ]

    assert len(carried) == 2
    assert collision.image == (0, 1, 1)


def test_the_paper_sample_point_is_the_first_of_the_three() -> None:
    """The paper gives ``(0, 1/2, -1/4)`` over ``(0, 1, 1)``, and so does this."""
    collision = examples.gao_quartic_collision()

    assert (0, sp.Rational(1, 2), sp.Rational(-1, 4)) in collision.points


def test_the_three_points_are_distinct() -> None:
    """COL-4, on the collision that made the normal form insufficient.

    Distinctness of algebraic points is what ``cancel`` alone could not decide,
    and it is the clause a wrong answer would break: a counterexample with two
    "distinct" preimages that are one point is no counterexample.
    """
    collision = examples.gao_quartic_collision()

    assert len({tuple(point) for point in collision.points}) == 3


def test_the_quartic_collision_survives_a_chain() -> None:
    """The transport work package 6 was measured on, as a test rather than a note.

    The roadmap reports that the collision was carried through a linear step, a
    BCW step and a two-step chain. That was a measurement in a session and
    nothing in the suite repeated it, which an external audit pointed out: the
    generic transport tests all use rational points, and nested square roots
    are what made work package 6 necessary.

    The chain is short on purpose. What is under test is that the algebraic
    coordinates survive the arithmetic of a step and still verify, not the
    reduction of this map, which nothing here claims to have.
    """
    quartic = over_field(examples.gao_quartic())
    collision = examples.gao_quartic_collision()
    normalization = LinearStep.normalize(quartic)
    candidate = enumerate_candidates(
        normalization.target, [sp.Symbol("x") * sp.Symbol("y")]
    )[0]
    step = BCWStep.build(
        normalization.target,
        candidate.index,
        *candidate.factors(sp.symbols("s t")),
        1,
    )
    chain = Reduction((normalization, step))

    carried = chain.transport(collision)

    assert carried.verify(chain.target) is None
    assert carried.dimension == chain.target.dimension
    assert len(carried.points) == 3

    root = sp.sqrt(23) * sp.I
    algebraic = [point for point in carried.points if any(c.has(root) for c in point)]

    assert len(algebraic) == 2


# --------------------------------------------------------------------------
# The chain a search found
# --------------------------------------------------------------------------


# --------------------------------------------------------------------------
# The map the compression is checked against
# --------------------------------------------------------------------------


def test_thompsons_map_is_cubic_homogeneous_and_Keller() -> None:  # noqa: N802
    """Twenty-four variables at BCW's third stage, not the first.

    Every figure this project produced before milestone 0.6 is at degree three,
    which is the first stage. This one is homogeneous, so it lies in ``MA^2``
    and is comparable with the output of the homogenization and not with
    ``alpoege12``.
    """
    thompson = examples.thompson24_homogeneous()

    assert (thompson.dimension, thompson.degree()) == (24, 3)
    assert thompson.determinant() == 1
    assert thompson.filtration_degree() == 2

    degrees = {
        sum(monomial)
        for component in thompson.displacement().to_polynomials()
        if component
        for monomial in component.itermonoms()
    }

    assert degrees == {3}


def test_its_collision_is_a_fixed_point_and_another_point() -> None:
    """The image is the first of the two points, as for ``alpoege13``."""
    collision = examples.thompson24_homogeneous_collision()

    assert len(collision.points) == 2
    assert collision.image == collision.points[0]


def test_the_example_and_the_reconstruction_denote_one_map() -> None:
    """The library idiom against the transcription the script holds.

    ``scripts/reconstruct_prellberg40.py`` transcribes Thompson's map from
    Prellberg's ancillary file as the displacement ``H``. This module writes it
    as a map. Two transcriptions of one source can drift apart in a
    coefficient, and nothing else compares them.

    The script also holds the twenty-dimensional restriction, which is
    deliberately *not* in this module: it is what the compression has to
    arrive at.
    """
    root = Path(__file__).resolve().parent.parent
    path = root / "scripts" / "reconstruct_prellberg40.py"
    spec = importlib.util.spec_from_file_location("reconstruct_prellberg40", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    thompson = examples.thompson24_homogeneous()
    rewritten = tuple(
        sp.expand(
            displacement.xreplace(dict(zip(module.u, thompson.variables, strict=True)))
        )
        + variable
        for displacement, variable in zip(module.H, thompson.variables, strict=True)
    )

    assert rewritten == thompson.components

    lifted = {tuple(module.embed(point)) for point in (module.P20, module.Q20)}

    assert lifted == set(examples.thompson24_homogeneous_collision().points)


# --------------------------------------------------------------------------
# The published eleven-variable map
# --------------------------------------------------------------------------


def test_the_eleven_dimensional_map_is_cubic_and_Keller() -> None:  # noqa: N802
    """Degree three, determinant -2, one below alpoege12."""
    eleven = examples.spacerat11()

    assert (eleven.dimension, eleven.degree()) == (11, 3)
    assert eleven.determinant() == -2


def test_it_is_not_normalized() -> None:
    """UNI-2 refuses it, and LinearStep.normalize is what repairs it.

    Like ``alpoege13`` and unlike ``alpoege12``. It stands in Alpoege's own
    coordinates, which is where a chain reaches it: a ``BCWStep`` preserves the
    determinant, so no chain runs from the normalized map, whose determinant is
    one, to this one.

    The normalization divides by two, which ``ZZ`` cannot do, so it goes
    through ``over_field`` as every other normalization in this project does.
    """
    eleven = examples.spacerat11()

    assert not eleven.is_in_MA(1)
    assert LinearStep.normalize(over_field(eleven)).target.determinant() == 1


def test_the_eleven_dimensional_collision_continues_alpoeges() -> None:
    """The first three coordinates are Alpoege's own three points."""
    carried = examples.spacerat11_collision()

    assert {point[:3] for point in carried.points} == set(
        examples.alpoege_collision().points
    )


def test_the_eleven_dimensional_script_and_example_agree() -> None:
    """The independent replay against the transcription in this module.

    ``scripts/reconstruct_spacerat11.py`` recomputes the six steps in plain
    SymPy and holds its own copy of the published components. Two
    transcriptions of one source can differ in a coefficient, and the script
    compares its chain against its copy rather than against this one.
    """
    root = Path(__file__).resolve().parent.parent
    path = root / "scripts" / "reconstruct_spacerat11.py"
    spec = importlib.util.spec_from_file_location("reconstruct_spacerat11", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    eleven = examples.spacerat11()
    published = tuple(sp.expand(c) for c in module.PUBLISHED)

    assert published == tuple(sp.expand(c) for c in eleven.components)

    printed = {tuple(sp.sympify(v) for v in p) for p in module.PUBLISHED_POINTS}

    assert printed == {
        tuple(sp.sympify(v) for v in p) for p in examples.spacerat11_collision().points
    }


@pytest.mark.slow
def test_a_chain_of_six_steps_reaches_it_from_alpoeges_map() -> None:
    """It is not a source this library cannot reach.

    ``peel`` is given the target, so this does not say the map was found here;
    it says the map lies in the space of ``BCWStep`` chains from
    ``examples.alpoege()``. The endpoint is the map after reordering the
    generators, because the chain names its fresh ones in its own order.
    """
    outcome = peel(over_field(examples.alpoege()), over_field(examples.spacerat11()))

    assert outcome.reduction is not None
    assert len(outcome.reduction.steps) == 6
    assert outcome.reduction.verify() is None

    reached = outcome.reduction.target.reordered(examples.spacerat11().variables)

    assert reached == over_field(examples.spacerat11())


# --------------------------------------------------------------------------
# The chain an external driver found
# --------------------------------------------------------------------------


def test_the_twelve_dimensional_map_is_cubic_and_Keller() -> None:  # noqa: N802
    """Degree three, determinant one, one dimension below alpoege13."""
    twelve = examples.alpoege12()

    assert (twelve.dimension, twelve.degree()) == (12, 3)
    assert twelve.determinant() == 1
    assert examples.alpoege13().dimension == 13


def test_the_twelve_dimensional_map_is_already_in_MA_one() -> None:  # noqa: N802
    """Unlike alpoege13, which needs LinearStep.normalize before UNI-2.

    The linear part of alpoege13's displacement has the two non-zero entries
    7 and 6. This one has none, so Section 4 applies to it directly.
    """
    assert examples.alpoege12().is_in_MA(1)
    assert not examples.alpoege13().is_in_MA(1)


def test_its_collision_continues_alpoeges_as_well() -> None:
    """The first three coordinates are Alpoege's own three points."""
    carried = examples.alpoege12_collision()

    assert {point[:3] for point in carried.points} == set(
        examples.alpoege_collision().points
    )


@pytest.mark.parametrize(
    ("script", "example"),
    [
        ("reconstruct_bcw17", "bcw17"),
        ("reconstruct_alpoege15", "alpoege15"),
        ("reconstruct_alpoege13", "alpoege13"),
        ("reconstruct_alpoege12", "alpoege12"),
    ],
    ids=lambda value: value,
)
def test_each_script_and_its_example_denote_one_map(script: str, example: str) -> None:
    """Two renderings of one chain, compared where nothing else compares them.

    Each ``reconstruct_*`` script replays its chain in plain SymPy without this
    library, and checks the dimension, the degree, the determinant and the
    carried points against values written into it. None of them compares the
    *components* with the example it denotes, so the two could drift apart in a
    coordinate that no figure sees.

    Work package 2 of milestone 0.6 closed this for ``alpoege12`` alone and
    named the rest as open. They cost 0.2 seconds together, measured before
    this test was written, so there was no reason to leave them behind a slow
    marker.

    Two scripts are not here and need not be. ``reconstruct_alpoege19.py`` and
    ``reconstruct_macfarlane13.py`` read their target from ``tests/data.py``
    rather than holding one, which is the same separation by another route, and
    ``reconstruct_spacerat11.py`` has its own test below because it compares a
    transcription rather than a chain.
    """
    root = Path(__file__).resolve().parent.parent
    path = root / "scripts" / f"{script}.py"
    spec = importlib.util.spec_from_file_location(script, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    rebuilt = tuple(sp.expand(component) for component in module.reduce_alpoege())
    stored = tuple(
        sp.expand(component) for component in getattr(examples, example)().components
    )

    assert rebuilt == stored


def test_no_coordinate_of_it_is_a_triangular_extension() -> None:
    """The move that takes the published construction from twelve to eleven.

    A coordinate whose component is ``x_j`` plus something free of ``x_j``, and
    which occurs in no other component, can be deleted without changing the
    determinant or the collision. ``docs/references.md`` records where that
    move comes from. No coordinate here admits it: the search buys a
    coordinate only to use it, so every one of them occurs somewhere else.

    A narrow check and a negative result. It says nothing about the pair form
    of the same move, which is checked in the same place and also finds
    nothing.
    """
    twelve = examples.alpoege12()
    components = twelve.components

    deletable = [
        variable
        for index, variable in enumerate(twelve.variables)
        if not sp.expand(components[index] - variable).has(variable)
        and not any(
            component.has(variable)
            for position, component in enumerate(components)
            if position != index
        )
    ]

    assert deletable == []


def test_the_thirteen_dimensional_map_is_what_the_search_finds() -> None:
    """The example, the search and the reconstruction denote one map.

    ``scripts/reconstruct_alpoege13.py`` was written before the enumerator
    could find the chain, from a prototype, and the shipped enumerator found a
    different one: the prototype wrote a scalar into a factor where the
    enumerator takes its factors monic and puts it in the step. Both chains are
    valid and reach dimension 13, and ``alpoege13`` has to name one map.

    This is what says the three agree.
    """
    from kellermap import LinearStep, over_field, reduce_to_degree3

    source = LinearStep.normalize(over_field(examples.alpoege())).target
    outcome = reduce_to_degree3(source, budget=2000)

    assert outcome.reduction is not None
    assert outcome.reduction.target == examples.alpoege13()
    assert len(outcome.reduction.steps) == 7


def test_it_is_two_dimensions_below_the_chain_computed_by_hand() -> None:
    """Thirteen against fifteen, in seven steps against eight.

    A record and not a claim of minimality. What it establishes is in
    ``docs/references.md``.
    """
    assert examples.alpoege13().dimension == 13
    assert examples.alpoege15().dimension == 15
    assert examples.bcw17().dimension == 17


def test_its_collision_continues_alpoeges() -> None:
    """The first three coordinates are Alpoege's own three points."""
    carried = examples.alpoege13_collision()
    start = examples.alpoege_collision()

    assert {point[:3] for point in carried.points} == set(start.points)


def test_the_third_point_in_the_fixed_data_is_the_one_the_chain_carries() -> None:
    """The value ``docs/references.md`` cites, against the library's own chain.

    ``tests/data.py`` holds ``MACFARLANE_THIRD_POINT`` and
    ``scripts/reconstruct_macfarlane13.py`` holds a second copy that it checks.
    Nothing checked the first, so the cited value could drift from the computed
    one unnoticed. An audit of ``0.5.0rc3`` pointed that out.
    """
    from kellermap import Collision, LinearStep, over_field, peel

    # Skipped and not failed when the file is absent, which is what an
    # installed source archive looks like: tests/data.py is excluded from it
    # because the map is somebody else's and its licence could not be
    # established. tests/test_alpoege19.py has said so at module level since
    # 0.5; this test imported unconditionally and an audit of 0.6.0rc1 found it
    # by running the suite the archive ships.
    pytest.importorskip(
        "tests.data",
        reason="tests/data.py is excluded from the source archive",
    )

    from tests.data import (
        MACFARLANE_COMPONENTS,
        MACFARLANE_THIRD_POINT,
        MACFARLANE_VARIABLES,
    )

    renaming = dict(zip(MACFARLANE_VARIABLES, sp.symbols("x1:14"), strict=True))
    target = PolynomialMap(
        sp.symbols("x1:14"),
        tuple(sp.expand(c.xreplace(renaming)) for c in MACFARLANE_COMPONENTS),
    )
    normalization = LinearStep.normalize(over_field(examples.alpoege()))
    chain = peel(normalization.target, target, budget=400, spare=3, pairs=6).reduction

    assert chain is not None

    start = Collision.at(
        over_field(examples.alpoege()), examples.alpoege_collision().points
    )
    carried = chain.transport(normalization.transport(start))
    order = tuple(int(str(v)[1:]) for v in chain.target.variables)

    def in_his_numbering(point: tuple[sp.Expr, ...]) -> tuple[sp.Expr, ...]:
        placed: list[sp.Expr] = [sp.Integer(0)] * 13
        for position, index in enumerate(order):
            placed[index - 1] = sp.sympify(point[position])

        return tuple(placed)

    third = in_his_numbering(carried.points[2])

    assert third == tuple(sp.sympify(c) for c in MACFARLANE_THIRD_POINT)
