"""The certificate file, FMT-1 to FMT-12 of ``docs/contracts.md``.

Three kinds of test. Round trips write a certificate and read it back, and
require the maps, the collisions and the text to come back unchanged and every
step to come back ``SUPPLIED``. Controls change one thing in a text that reads,
and require the refusal to cite the obligation and the location the change
breaks. The chains of the reconstruction scripts are read back and verified,
which is the first control of the format that FMT-10 names.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
import sympy as sp

from kellermap import (
    Certificate,
    Collision,
    CompressionStep,
    Dilation,
    ElementaryAutomorphism,
    ElementaryFactor,
    InvariantError,
    LinearAutomorphism,
    LinearStep,
    PolynomialMap,
    Provenance,
    Reduction,
    SymmetricLiftStep,
    TranslationStep,
    Transposition,
    Transvection,
    VanishingWitness,
    VerificationError,
    examples,
    over_field,
)
from kellermap.bcw import BCWStep, HomogenizationStep, UnipotentStep
from kellermap.bcw.step import Carried, Fresh
from kellermap.descent import DescentStep

from . import chains

x, y, z, u, T = sp.symbols("x y z u T")

ROOT = Path(__file__).resolve().parent.parent

Edit = Callable[[Any], None]


# --------------------------------------------------------------------------
# Certificates to write
# --------------------------------------------------------------------------


def small_chain() -> Certificate:
    """A translation, a BCW step with both kinds of slot, and a linear step.

    Over ``QQ``, so that the linear step can carry a dilation by two. The
    linear factors are given by hand and are not a normalization, so that all
    three kinds occur.
    """
    source = over_field(PolynomialMap((x, y), (x + y**2 + 1, y + 2)))
    translation = TranslationStep.normalize(source)
    bcw = BCWStep.build(
        translation.target,
        0,
        Fresh(y**2, u),
        Carried(1),
        filtration_level=1,
        coefficient=3,
    )
    ring = bcw.target.ring
    linear = LinearStep.build(
        bcw.target,
        LinearAutomorphism(
            (
                Transvection(ring, 0, 1, sp.Rational(1, 3)),
                Transposition(ring, 0, 2),
                Dilation(ring, 1, 2),
            )
        ),
    )

    return Certificate(Reduction((translation, bcw, linear)))


def pipeline() -> Certificate:
    """The unipotent step, the homogenization and the lift, from ``QQ`` to ``QQ_I``."""
    source = over_field(PolynomialMap((x, y), (x + y**3, y)))
    unipotent = UnipotentStep.build(source)
    homogenized = HomogenizationStep.build(unipotent.target)
    lift = SymmetricLiftStep.build(homogenized.target)

    return Certificate(Reduction((unipotent, homogenized, lift)))


def descent() -> Certificate:
    """A descent whose triangularity is hidden behind a completion."""
    plain = PolynomialMap((x, y, z), (x + y**2, y, z + x * y))
    change = ElementaryAutomorphism((ElementaryFactor(plain.ring, 0, -(z**2)),))
    source = change.inverse().apply_to(plain)

    return Certificate(Reduction((DescentStep(source, 2, left=change),)))


def parametric() -> Certificate:
    """A BCW step over ``ZZ[T]``, whose factor and coefficient involve ``T``."""
    source = PolynomialMap((x, y), (x + T * y**2, y))
    step = BCWStep.build(source, 0, Fresh(T * y**2, u), Carried(1), coefficient=T)

    return Certificate(Reduction((step,)))


FOLD = PolynomialMap((x, y), (x**2 + T * y, y))
"""A map over ``ZZ[T]`` that identifies a point with its mirror image."""


def folded(*points: tuple[sp.Expr, ...]) -> Certificate:
    """A certificate of ``FOLD`` alone with one collision at the given points."""
    return Certificate(FOLD, ((0, Collision.at(FOLD, points)),))


SQUARE = PolynomialMap((x, y), (x**2, y))
"""A map over ``ZZ`` that identifies ``(a, b)`` with ``(-a, b)``."""


def squared(*points: tuple[sp.Expr, ...]) -> Certificate:
    return Certificate(SQUARE, ((0, Collision.at(SQUARE, points)),))


def gao() -> Certificate:
    """Gao's map, whose collision lies over ``QQ(sqrt(-23))``."""
    quartic = examples.gao_quartic()

    return Certificate(quartic, ((0, examples.gao_quartic_collision()),))


QUOTIENT = PolynomialMap((x, y), (x**2 + y / T, y))
"""A map over the field of fractions ``ZZ(T)``."""


SMALL: dict[str, Callable[[], Certificate]] = {
    "small chain": small_chain,
    "pipeline": pipeline,
    "descent": descent,
    "parametric": parametric,
    "gao": gao,
    "fold over ZZ[T]": lambda: folded((T, 0), (-T, 0)),
    "gaussian points": lambda: squared((sp.I, 0), (-sp.I, 0)),
    "a map over ZZ(T)": lambda: Certificate(
        QUOTIENT, ((0, Collision.at(QUOTIENT, ((T, 0), (-T, 0)))),)
    ),
}


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------


def edited(text: str, edit: Edit) -> str:
    """Return ``text`` with ``edit`` applied to its parsed form."""
    document = json.loads(text)
    edit(document)

    return json.dumps(document, sort_keys=True, separators=(",", ":")) + "\n"


def refused(text: str, obligation: str, location: str) -> VerificationError:
    """Read ``text`` and require a refusal with this identifier and place."""
    with pytest.raises(VerificationError) as refusal:
        Certificate.loads(text)

    assert (refusal.value.obligation, refusal.value.location) == (
        obligation,
        location,
    ), str(refusal.value)

    return refusal.value


def round_trip(certificate: Certificate) -> Certificate:
    """Write and read back, and check what FMT-12 promises of the two."""
    text = certificate.dumps()
    back = Certificate.loads(text)

    assert back.maps == certificate.maps
    assert back.collisions == certificate.collisions
    assert all(step.provenance is Provenance.SUPPLIED for step in back.steps)
    assert back.dumps() == text

    return back


# --------------------------------------------------------------------------
# Round trips
# --------------------------------------------------------------------------


@pytest.mark.parametrize("name", list(SMALL))
def test_a_certificate_reads_back_as_it_was_written(name: str) -> None:
    back = round_trip(SMALL[name]())

    assert back.verify() is None


@pytest.mark.parametrize("name", chains.NAMES)
def test_the_chain_of_a_reconstruction_script_reads_back_and_verifies(
    name: str,
) -> None:
    """FMT-10: the first control of the format, on the chains of the scripts.

    The chain is built by the library from the script's data, so it is
    ``CONSTRUCTED``. Read back it is ``SUPPLIED``, and every identity now
    compares a target from the file with the formula. The end of the chain is
    also compared with what the script computes, which is the agreement CHK-8
    will ask of the checker.
    """
    certificate = chains.certificate(name)
    assert all(step.provenance is Provenance.CONSTRUCTED for step in certificate.steps)

    back = round_trip(certificate)

    assert back.verify() is None
    end = back.maps[-1].components
    expected = chains.script_target(name)
    assert len(end) == len(expected)
    assert all(sp.expand(a - b) == 0 for a, b in zip(end, expected, strict=True))


def test_the_compression_lift_and_witness_of_thompson_read_back(
    thompson_compressed: CompressionStep, thompson_lift: SymmetricLiftStep
) -> None:
    """The eighth chain, ``reconstruct_prellberg40.py``, with its witness."""
    collision = examples.thompson24_homogeneous_collision()
    pair = thompson_compressed.transport(collision)
    lifted = thompson_lift.transport(pair)
    certificate = Certificate(
        Reduction((thompson_compressed, thompson_lift)),
        ((0, collision), (1, pair), (2, lifted)),
        VanishingWitness(thompson_lift, lifted),
    )

    back = round_trip(certificate)

    assert back.witness is not None
    assert back.witness.lift is back.steps[1]
    assert back.witness.collision == lifted
    assert back.verify() is None


def test_a_step_read_back_is_the_supplied_step_of_the_same_arguments() -> None:
    """FMT-12: equal to the step the public constructor gives, not to the original."""
    original = small_chain()
    back = Certificate.loads(original.dumps())
    bcw = original.steps[1]
    assert isinstance(bcw, BCWStep)

    supplied = BCWStep(
        bcw.source,
        bcw.target,
        bcw.index,
        bcw.left,
        bcw.right,
        bcw.filtration_level,
        bcw.coefficient,
    )

    assert back.steps[1] == supplied
    assert back.steps[1] != bcw


def test_the_provenance_of_a_step_does_not_reach_the_file() -> None:
    """A constructed chain and the supplied chain read from it give one text."""
    constructed = chains.certificate("bcw17")
    supplied = Certificate.loads(constructed.dumps())

    assert supplied.dumps() == constructed.dumps()


def test_a_single_map_is_read_back_as_a_map() -> None:
    """FMT-2: no step, one map, and no empty ``Reduction``."""
    back = round_trip(Certificate(SQUARE))

    assert back.chain == SQUARE
    assert back.steps == ()
    assert back.maps == (SQUARE,)


# --------------------------------------------------------------------------
# The text, FMT-12
# --------------------------------------------------------------------------


def test_the_text_has_sorted_keys_no_whitespace_and_one_final_newline() -> None:
    text = small_chain().dumps()
    document = json.loads(text)

    assert text == json.dumps(document, sort_keys=True, separators=(",", ":")) + "\n"
    assert text.isascii()
    assert text.count("\n") == 1
    assert not text.startswith('{"format"')


def test_terms_are_written_in_descending_lexicographic_order() -> None:
    """Whatever the monomial order of the ring, which is ``grlex`` here."""
    ring, gx, gy = sp.ring("x y", sp.QQ, "grlex")
    graded = PolynomialMap.from_ring(ring, [gx + gy**3, gy])
    document = json.loads(Certificate(graded).dumps())
    exponents = [term[0] for term in document["maps"][0]["components"][0]]

    assert document["maps"][0]["ring"]["order"] == "grlex"
    assert exponents == sorted(exponents, reverse=True) == [[1, 0], [0, 3]]


def test_the_points_of_a_collision_are_written_in_one_order() -> None:
    """COL-6 makes a collision a set, so its text does not depend on the order."""
    first = squared((1, 0), (-1, 0)).dumps()
    second = squared((-1, 0), (1, 0)).dumps()

    assert first == second


@pytest.mark.parametrize(
    ("certificate", "domain"),
    [
        (lambda: squared((1, 0), (-1, 0)), "ZZ"),
        (lambda: squared((sp.Rational(1, 2), 0), (-sp.Rational(1, 2), 0)), "QQ"),
        (lambda: squared((sp.I, 0), (-sp.I, 0)), "ZZ_I"),
        (lambda: squared((sp.I / 2, 0), (-sp.I / 2, 0)), "QQ_I"),
        (lambda: squared((sp.sqrt(2), 0), (-sp.sqrt(2), 0)), {"quadratic": "2"}),
        (gao, {"quadratic": "-23"}),
        (
            lambda: folded((T, 0), (-T, 0)),
            {"polynomial": "ZZ", "parameters": ["T"], "order": "lex"},
        ),
        (
            lambda: folded((T / 2, 0), (-T / 2, 0)),
            {"polynomial": "QQ", "parameters": ["T"], "order": "lex"},
        ),
        (
            lambda: folded((sp.I * T, 0), (-sp.I * T, 0)),
            {"polynomial": "ZZ_I", "parameters": ["T"], "order": "lex"},
        ),
        (
            lambda: folded((1 / T, 0), (-1 / T, 0)),
            {"fraction": "ZZ", "parameters": ["T"], "order": "lex"},
        ),
    ],
    ids=[
        "ZZ",
        "QQ",
        "ZZ_I",
        "QQ_I",
        "sqrt 2",
        "sqrt -23",
        "ZZ[T]",
        "QQ[T] before ZZ(T)",
        "ZZ_I[T]",
        "ZZ(T)",
    ],
)
def test_the_domain_of_a_collision_is_the_first_that_holds_it(
    certificate: Callable[[], Certificate], domain: Any
) -> None:
    """FMT-8: the order in which ``dumps`` tries the domains."""
    made = certificate()
    document = json.loads(made.dumps())

    assert document["collisions"][0]["domain"] == domain
    assert round_trip(made).verify() is None


def test_a_collision_over_a_field_of_fractions_is_written_over_it() -> None:
    """No polynomial ring contains ``ZZ(T)``, so the first candidates are passed."""
    certificate = SMALL["a map over ZZ(T)"]()
    domain = json.loads(certificate.dumps())["collisions"][0]["domain"]

    assert domain == {"fraction": "ZZ", "parameters": ["T"], "order": "lex"}


def test_a_reader_accepts_a_domain_that_dumps_would_not_choose() -> None:
    """FMT-8: a base lies in a polynomial ring over it, and a reader allows that."""

    def widen(document: Any) -> None:
        entry = collision(document)
        entry["domain"] = {"polynomial": "ZZ", "parameters": ["T"], "order": "lex"}
        for coordinates in [*entry["points"], entry["image"]]:
            for position, value in enumerate(coordinates):
                coordinates[position] = [] if value == "0" else [[[0], value]]

    text = squared((1, 0), (-1, 0)).dumps()
    widened = Certificate.loads(edited(text, widen))

    assert widened.collisions == Certificate.loads(text).collisions
    assert widened.dumps() == text


def test_a_polynomial_ring_does_not_contain_a_field_of_fractions() -> None:
    def narrow(document: Any) -> None:
        collision(document)["domain"]["polynomial"] = collision(document)["domain"].pop(
            "fraction"
        )

    text = SMALL["a map over ZZ(T)"]().dumps()

    refused(edited(text, narrow), "FMT-8", "collision 0")


def test_a_collision_over_a_map_over_qq_i_stays_there() -> None:
    lifted = over_field(PolynomialMap((x, y), (x**2, y + sp.I * x**2)))
    certificate = Certificate(lifted, ((0, Collision.at(lifted, ((1, 0), (-1, 0)))),))

    assert json.loads(certificate.dumps())["collisions"][0]["domain"] == "QQ_I"


# --------------------------------------------------------------------------
# What dumps refuses
# --------------------------------------------------------------------------


def unwritable(certificate: Certificate, obligation: str, location: str) -> None:
    with pytest.raises(VerificationError) as refusal:
        certificate.dumps()

    assert (refusal.value.obligation, refusal.value.location) == (
        obligation,
        location,
    ), str(refusal.value)


def test_a_finite_field_is_not_written() -> None:
    ring, gx = sp.ring("x", sp.GF(5))

    unwritable(Certificate(PolynomialMap.from_ring(ring, [gx])), "FMT-5", "map 0")


def test_an_algebraic_field_is_not_written_for_a_map() -> None:
    field = sp.QQ.algebraic_field(sp.sqrt(2))
    ring, gx = sp.ring("x", field)

    unwritable(Certificate(PolynomialMap.from_ring(ring, [gx])), "FMT-5", "map 0")


def test_a_polynomial_ring_over_a_polynomial_ring_is_not_written() -> None:
    domain = sp.QQ.poly_ring(T).poly_ring(sp.Symbol("S"))
    ring, gx = sp.ring("x", domain)

    unwritable(Certificate(PolynomialMap.from_ring(ring, [gx])), "FMT-5", "map 0")


def test_a_symbol_with_assumptions_is_not_written() -> None:
    positive = sp.Symbol("x", positive=True)

    unwritable(Certificate(PolynomialMap((positive,), (positive,))), "FMT-7", "map 0")


def test_a_name_outside_the_pattern_is_not_written() -> None:
    odd = sp.Symbol("x'")

    unwritable(Certificate(PolynomialMap((odd,), (odd,))), "FMT-7", "map 0")


def test_a_monomial_order_outside_the_list_is_not_written() -> None:
    ring, gx = sp.ring("x", sp.QQ, "ilex")

    unwritable(Certificate(PolynomialMap.from_ring(ring, [gx])), "FMT-1", "map 0")


def test_a_collision_that_needs_two_roots_is_not_written() -> None:
    points = ((sp.sqrt(2) + sp.I, 0), (-sp.sqrt(2) - sp.I, 0))

    unwritable(squared(*points), "FMT-5", "collision 0")


def test_a_step_type_the_format_does_not_know_is_not_written() -> None:
    """FMT-3. A ``Step`` written outside this library has no form in a file."""

    class Identity:
        provenance = Provenance.SUPPLIED
        filtration_level = float("inf")

        def __init__(self, source: PolynomialMap) -> None:
            self.source = source
            self.target = source

        def verify(self) -> None:
            return None

        def transport(self, collision: Collision) -> Collision:
            return collision

    unwritable(Certificate(Reduction((Identity(SQUARE),))), "FMT-3", "step 0")


# --------------------------------------------------------------------------
# What loads refuses: the file as a whole, FMT-1 and FMT-2
# --------------------------------------------------------------------------


SMALL_TEXT = small_chain().dumps()
FOLD_TEXT = folded((1 / T, 0), (-1 / T, 0)).dumps()
PARAMETRIC_TEXT = parametric().dumps()
QUOTIENT_TEXT = SMALL["a map over ZZ(T)"]().dumps()
SQUARE_TEXT = squared((sp.I / 2, 0), (-sp.I / 2, 0)).dumps()


TEXTS = [
    pytest.param("not json", "FMT-1", id="not JSON"),
    pytest.param("[]", "FMT-1", id="not an object"),
    pytest.param('{"a": 1, "a": 2}', "FMT-1", id="a key twice"),
    pytest.param('{"a": NaN}', "FMT-1", id="NaN"),
    pytest.param('{"a": 1.5}', "FMT-6", id="a float"),
]


@pytest.mark.parametrize(("text", "obligation"), TEXTS)
def test_text_that_is_no_file_is_refused(text: str, obligation: str) -> None:
    refused(text, obligation, "file")


FRAME_EDITS = [
    pytest.param(lambda d: d.update(format="other"), "FMT-1", id="format"),
    pytest.param(lambda d: d.update(version=2), "FMT-1", id="version"),
    pytest.param(lambda d: d.update(version=True), "FMT-1", id="a boolean version"),
    pytest.param(lambda d: d.update(extra=1), "FMT-1", id="an unknown key"),
    pytest.param(lambda d: d.pop("steps"), "FMT-1", id="a missing key"),
    pytest.param(lambda d: d.update(maps={}), "FMT-1", id="maps not a list"),
    pytest.param(lambda d: d["maps"].pop(), "FMT-2", id="a map short"),
]


@pytest.mark.parametrize(("edit", "obligation"), FRAME_EDITS)
def test_the_frame_of_a_file_is_checked(edit: Edit, obligation: str) -> None:
    refused(edited(SMALL_TEXT, edit), obligation, "file")


# --------------------------------------------------------------------------
# Maps, names and numbers: FMT-5, FMT-6 and FMT-7
# --------------------------------------------------------------------------


def ring_of(document: Any) -> Any:
    return document["maps"][0]["ring"]


def first_term(document: Any) -> Any:
    return document["maps"][0]["components"][0][0]


MAP_EDITS = [
    pytest.param(
        lambda d: ring_of(d).update(generators=["x", "1y"]),
        "FMT-7",
        id="a name outside the pattern",
    ),
    pytest.param(
        lambda d: ring_of(d).update(generators=["x", "x"]),
        "FMT-7",
        id="two equal names",
    ),
    pytest.param(
        lambda d: ring_of(d).update(generators=[]), "FMT-7", id="no generator"
    ),
    pytest.param(
        lambda d: ring_of(d).update(generators=[1, "y"]),
        "FMT-1",
        id="a name that is not a string",
    ),
    pytest.param(
        lambda d: ring_of(d).update(order="ilex"),
        "FMT-1",
        id="an order outside the list",
    ),
    pytest.param(
        lambda d: ring_of(d).update(domain="RR"), "FMT-5", id="an unknown domain"
    ),
    pytest.param(
        lambda d: ring_of(d).update(domain={"quadratic": "2"}),
        "FMT-5",
        id="a quadratic field for a map",
    ),
    pytest.param(
        lambda d: ring_of(d).update(
            domain={"polynomial": "RR", "parameters": ["T"], "order": "lex"}
        ),
        "FMT-5",
        id="an unknown base",
    ),
    pytest.param(
        lambda d: ring_of(d).update(
            domain={"polynomial": "QQ", "parameters": [], "order": "lex"}
        ),
        "FMT-7",
        id="no parameter",
    ),
    pytest.param(
        lambda d: ring_of(d).update(
            domain={"polynomial": "QQ", "parameters": ["x"], "order": "lex"}
        ),
        "FMT-7",
        id="a parameter named like a generator",
    ),
    pytest.param(
        lambda d: d["maps"][0]["components"].pop(), "FMT-1", id="a component short"
    ),
    pytest.param(
        lambda d: first_term(d).append(1), "FMT-1", id="a term of three parts"
    ),
    pytest.param(
        lambda d: first_term(d).__setitem__(0, [1]),
        "FMT-6",
        id="an exponent vector too short",
    ),
    pytest.param(
        lambda d: first_term(d).__setitem__(0, [-1, 0]),
        "FMT-6",
        id="a negative exponent",
    ),
    pytest.param(
        lambda d: first_term(d).__setitem__(0, [True, 0]),
        "FMT-1",
        id="a boolean exponent",
    ),
    pytest.param(
        lambda d: d["maps"][0]["components"][0].append([first_term(d)[0], "5"]),
        "FMT-6",
        id="two terms with one exponent vector",
    ),
    pytest.param(
        lambda d: first_term(d).__setitem__(1, "0"), "FMT-6", id="a zero coefficient"
    ),
    pytest.param(
        lambda d: first_term(d).__setitem__(1, "01"), "FMT-6", id="a leading zero"
    ),
    pytest.param(
        lambda d: first_term(d).__setitem__(1, "-0"), "FMT-6", id="minus zero"
    ),
    pytest.param(
        lambda d: first_term(d).__setitem__(1, "+1"), "FMT-6", id="a plus sign"
    ),
    pytest.param(
        lambda d: first_term(d).__setitem__(1, "2/4"), "FMT-6", id="not in lowest terms"
    ),
    pytest.param(
        lambda d: first_term(d).__setitem__(1, "3/1"),
        "FMT-6",
        id="a denominator of one",
    ),
    pytest.param(
        lambda d: first_term(d).__setitem__(1, "1/-2"),
        "FMT-6",
        id="a negative denominator",
    ),
    pytest.param(
        lambda d: first_term(d).__setitem__(1, 1),
        "FMT-1",
        id="a number that is not a string",
    ),
]


@pytest.mark.parametrize(("edit", "obligation"), MAP_EDITS)
def test_a_map_breaking_a_rule_of_the_format_is_refused(
    edit: Edit, obligation: str
) -> None:
    refused(edited(SMALL_TEXT, edit), obligation, "map 0")


def test_an_integer_domain_refuses_a_fraction() -> None:
    text = descent().dumps()

    refused(
        edited(text, lambda d: first_term(d).__setitem__(1, "1/2")), "FMT-6", "map 0"
    )


GAUSSIAN_VALUES = [
    pytest.param(["1", "2", "3"], "FMT-1", id="a triple"),
    pytest.param(["1/2", "0"], "FMT-6", id="not a Gaussian integer"),
]


@pytest.mark.parametrize(("value", "obligation"), GAUSSIAN_VALUES)
def test_a_gaussian_element_is_a_pair_of_integers(value: Any, obligation: str) -> None:
    text = squared((sp.I, 0), (-sp.I, 0)).dumps()

    refused(
        edited(text, lambda d: d["collisions"][0]["points"][0].__setitem__(0, value)),
        obligation,
        "collision 0",
    )


def test_a_denominator_of_zero_is_refused() -> None:
    def zero(document: Any) -> None:
        document["collisions"][0]["points"][0][0]["denominator"] = []

    refused(edited(FOLD_TEXT, zero), "FMT-6", "collision 0")


def test_a_fraction_needs_both_parts() -> None:
    def half(document: Any) -> None:
        del document["collisions"][0]["points"][0][0]["denominator"]

    refused(edited(FOLD_TEXT, half), "FMT-1", "collision 0")


@pytest.mark.parametrize("value", ["4", "1", "0", "-1", "1/2", "8"])
def test_a_quadratic_field_names_a_square_free_integer(value: str) -> None:
    text = gao().dumps()

    def domain(document: Any) -> None:
        document["collisions"][0]["domain"] = {"quadratic": value}

    refused(edited(text, domain), "FMT-5", "collision 0")


# --------------------------------------------------------------------------
# Steps: FMT-1, FMT-3, FMT-4, and the invariants of the constructors
# --------------------------------------------------------------------------


def step(document: Any, index: int) -> Any:
    return document["steps"][index]


STEP_EDITS = [
    pytest.param(
        lambda d: d["steps"].__setitem__(0, []),
        "FMT-1",
        "step 0",
        id="a step that is not an object",
    ),
    pytest.param(
        lambda d: step(d, 0).update(type="Unknown"),
        "FMT-1",
        "step 0",
        id="an unknown type",
    ),
    pytest.param(lambda d: step(d, 0).pop("type"), "FMT-1", "step 0", id="no type"),
    pytest.param(
        lambda d: step(d, 0).update(type=1),
        "FMT-1",
        "step 0",
        id="a type that is not a string",
    ),
    pytest.param(
        lambda d: step(d, 0).pop("normalizing"), "FMT-1", "step 0", id="a missing field"
    ),
    pytest.param(
        lambda d: step(d, 0).update(normalizing=1),
        "FMT-1",
        "step 0",
        id="an integer where a boolean belongs",
    ),
    pytest.param(
        lambda d: step(d, 0).update(shift=["0"]),
        "TRA-1",
        "step 0",
        id="a shift of the wrong length",
    ),
    pytest.param(
        lambda d: step(d, 1).update(left={"carried": 0}),
        "BCW-10",
        "step 1",
        id="a carried slot on the target component",
    ),
    pytest.param(
        lambda d: step(d, 1).update(left={"carried": -1}),
        "BCW-10",
        "step 1",
        id="a negative carried slot",
    ),
    pytest.param(
        lambda d: step(d, 1).update(left={"other": 0}),
        "FMT-1",
        "step 1",
        id="a slot of neither kind",
    ),
    pytest.param(
        lambda d: step(d, 1).update(filtration_level=2),
        "BCW-6",
        "step 1",
        id="a level outside zero and one",
    ),
    pytest.param(
        lambda d: step(d, 1).update(coefficient="0"),
        "BCW-11",
        "step 1",
        id="a coefficient of zero",
    ),
    pytest.param(
        lambda d: step(d, 1)["left"]["fresh"].update(variable="x"),
        "BCW-2",
        "step 1",
        id="a fresh variable already taken",
    ),
    pytest.param(
        lambda d: step(d, 2)["transformation"].append({}),
        "FMT-1",
        "step 2",
        id="a linear factor of no kind",
    ),
    pytest.param(
        lambda d: step(d, 2)["transformation"][0]["transvection"].update(source=0),
        "LIN-2",
        "step 2",
        id="a transvection on one coordinate",
    ),
    pytest.param(
        lambda d: step(d, 2)["transformation"][1]["transposition"].update(second=0),
        "LIN-2",
        "step 2",
        id="a transposition of one coordinate",
    ),
    pytest.param(
        lambda d: step(d, 2)["transformation"][2]["dilation"].update(coefficient="0"),
        "LIN-2",
        "step 2",
        id="a dilation by zero",
    ),
]


@pytest.mark.parametrize(("edit", "obligation", "location"), STEP_EDITS)
def test_a_step_breaking_its_constructor_is_refused_with_its_identifier(
    edit: Edit, obligation: str, location: str
) -> None:
    """FMT-10: a constructor invariant cites the identifier it carries.

    The cause is the constructor's own exception, a ``ValueError``.
    """
    failure = refused(edited(SMALL_TEXT, edit), obligation, location)

    if obligation not in ("FMT-1",):
        assert isinstance(failure.__cause__, ValueError)


def test_a_factor_of_a_descent_on_its_own_variable_cites_dsc_4() -> None:
    def own(document: Any) -> None:
        step(document, 0)["left"][0]["polynomial"] = [[[1, 0, 0], "1"]]

    refused(edited(descent().dumps(), own), "DSC-4", "step 0")


def test_a_written_target_that_the_descent_does_not_derive_cites_dsc_1() -> None:
    """FMT-4: the one comparison ``loads`` makes."""

    def moved(document: Any) -> None:
        document["maps"][1]["components"][0].append([[0, 0], "1"])

    refused(edited(descent().dumps(), moved), "DSC-1", "step 0")


def test_a_descent_that_is_not_triangular_is_refused_where_it_stands() -> None:
    """The derived target cannot be formed, and DSC-3 says so with the step."""

    def untouched(document: Any) -> None:
        step(document, 0)["left"] = []

    refused(edited(descent().dumps(), untouched), "DSC-3", "step 0")


def test_a_step_of_every_other_type_breaking_its_constructor_is_refused() -> None:
    """One invariant each for the unipotent step, the homogenization and the lift."""
    text = pipeline().dumps()

    refused(edited(text, lambda d: step(d, 0)["variables"].pop()), "UNI-5", "step 0")
    refused(edited(text, lambda d: step(d, 1).update(variable="x")), "HOM-4", "step 1")
    refused(edited(text, lambda d: step(d, 2)["variables"].pop()), "SYM-5", "step 2")


def test_a_basis_breaking_its_constructor_is_refused(
    thompson_compressed: CompressionStep,
) -> None:
    text = Certificate(Reduction((thompson_compressed,))).dumps()

    refused(edited(text, lambda d: step(d, 0)["basis"].pop()), "CHC-5", "step 0")


# --------------------------------------------------------------------------
# Collisions and the witness: FMT-7, FMT-8 and FMT-9
# --------------------------------------------------------------------------


def collision(document: Any) -> Any:
    return document["collisions"][0]


COLLISION_EDITS = [
    pytest.param(
        SQUARE_TEXT,
        lambda d: collision(d).update(map=1),
        "FMT-8",
        id="a position past the maps",
    ),
    pytest.param(
        SQUARE_TEXT,
        lambda d: collision(d).update(domain="ZZ_I"),
        "FMT-6",
        id="an element outside the stated domain",
    ),
    pytest.param(
        FOLD_TEXT,
        lambda d: collision(d).update(domain="QQ_I"),
        "FMT-8",
        id="a domain without the map's",
    ),
    pytest.param(
        FOLD_TEXT,
        lambda d: collision(d).update(
            domain={"fraction": "ZZ", "parameters": ["x"], "order": "lex"}
        ),
        "FMT-7",
        id="a parameter named like a generator",
    ),
    pytest.param(
        FOLD_TEXT,
        lambda d: collision(d).update(
            domain={"fraction": "ZZ", "parameters": ["S"], "order": "lex"}
        ),
        "FMT-8",
        id="fractions in another parameter",
    ),
    pytest.param(
        FOLD_TEXT,
        lambda d: collision(d)["points"].__setitem__(1, collision(d)["points"][0]),
        "COL-4",
        id="two equal points",
    ),
    pytest.param(
        FOLD_TEXT, lambda d: collision(d)["points"].pop(), "COL-4", id="one point"
    ),
]


@pytest.mark.parametrize(("text", "edit", "obligation"), COLLISION_EDITS)
def test_a_collision_breaking_a_rule_is_refused(
    text: str, edit: Edit, obligation: str
) -> None:
    refused(edited(text, edit), obligation, "collision 0")


# --------------------------------------------------------------------------
# A value of the wrong type where a string is read: FMT-1
#
# The audit of 0.9.0rc1 found the checker's reader testing a value for
# membership in a table before testing that it is a string, so a list or an
# object raised TypeError there. Two places, the base of a domain and the type
# of a step. The library's reader refused both under FMT-1. The table runs
# through both readers: here, and in tests/test_checker.py.
# --------------------------------------------------------------------------


def _base(document: Any, value: Any) -> None:
    document["maps"][0]["ring"]["domain"]["polynomial"] = value


def _fraction_base(document: Any, value: Any) -> None:
    document["maps"][0]["ring"]["domain"]["fraction"] = value


def _collision_base(document: Any, value: Any) -> None:
    document["collisions"][0]["domain"] = {
        "polynomial": value,
        "parameters": ["T"],
        "order": "lex",
    }


def _step_type(document: Any, value: Any) -> None:
    document["steps"][0]["type"] = value


WRONG_TYPES = [
    pytest.param([], id="an array"),
    pytest.param({}, id="an object"),
    pytest.param(0, id="a number"),
    pytest.param(True, id="a boolean"),
    pytest.param(None, id="null"),
]

TYPE_EDITS = [
    pytest.param(
        text, lambda d, change=change, value=value: change(d, value), location, id=id_
    )
    for text, change, location, kind in (
        (PARAMETRIC_TEXT, _base, "map 0", "the base of a polynomial domain"),
        (QUOTIENT_TEXT, _fraction_base, "map 0", "the base of a fraction domain"),
        (FOLD_TEXT, _collision_base, "collision 0", "the base of a collision domain"),
        (SMALL_TEXT, _step_type, "step 0", "the type of a step"),
    )
    for value, id_ in (
        (param.values[0], f"{kind}, {param.id}") for param in WRONG_TYPES
    )
]


@pytest.mark.parametrize(("text", "edit", "location"), TYPE_EDITS)
def test_a_value_of_another_type_where_a_string_is_read_is_refused(
    text: str, edit: Edit, location: str
) -> None:
    refused(edited(text, edit), "FMT-1", location)


WITNESS_EDITS = [
    pytest.param(
        lambda d: d["witness"].update(step=0), "FMT-9", id="a step that is not a lift"
    ),
    pytest.param(
        lambda d: d["witness"].update(step=0, collision=0),
        "FMT-9",
        id="a step that is not a lift, with a collision at its target",
    ),
    pytest.param(
        lambda d: d["witness"].update(step=2), "FMT-9", id="a step past the steps"
    ),
    pytest.param(
        lambda d: d["witness"].update(collision=0),
        "FMT-9",
        id="a collision at another position",
    ),
    pytest.param(
        lambda d: d["witness"].update(collision=5),
        "FMT-9",
        id="a collision past the collisions",
    ),
    pytest.param(lambda d: d["witness"].update(depth=0), "VAN-3", id="a depth of zero"),
    pytest.param(
        lambda d: d["witness"].update(depth=True), "FMT-1", id="a boolean depth"
    ),
    pytest.param(lambda d: d["witness"].update(extra=1), "FMT-1", id="an unknown key"),
]


@pytest.mark.parametrize(("edit", "obligation"), WITNESS_EDITS)
def test_a_witness_breaking_a_rule_is_refused(
    witness_text: str, edit: Edit, obligation: str
) -> None:
    refused(edited(witness_text, edit), obligation, "witness")


# --------------------------------------------------------------------------
# The positive controls of CHK-8, read here by the library
# --------------------------------------------------------------------------


def test_the_points_of_a_collision_in_another_order_are_accepted() -> None:
    def reorder(document: Any) -> None:
        collision(document)["points"].reverse()

    original = Certificate.loads(FOLD_TEXT)
    reordered = Certificate.loads(edited(FOLD_TEXT, reorder))

    assert reordered.collisions == original.collisions
    assert reordered.dumps() == FOLD_TEXT
    assert reordered.verify() is None


def test_a_fraction_scaled_by_a_constant_is_the_same_element() -> None:
    """FMT-6: the one value with more than one spelling, compared by value."""

    def scale(document: Any) -> None:
        for entry in collision(document)["points"][0]:
            for part in ("numerator", "denominator"):
                for term in entry[part]:
                    term[1] = str(2 * int(term[1]))

    scaled = edited(FOLD_TEXT, scale)

    assert scaled != FOLD_TEXT
    assert (
        Certificate.loads(scaled).collisions == Certificate.loads(FOLD_TEXT).collisions
    )
    assert Certificate.loads(scaled).dumps() == FOLD_TEXT


# --------------------------------------------------------------------------
# The certificate itself: FMT-8, FMT-9 and FMT-11
# --------------------------------------------------------------------------


def test_a_position_outside_the_maps_is_refused_by_the_constructor() -> None:
    with pytest.raises(InvariantError) as refusal:
        Certificate(SQUARE, ((1, Collision.at(SQUARE, ((1, 0), (-1, 0)))),))

    assert refusal.value.obligation == "FMT-8"


def test_a_witness_outside_the_certificate_is_refused_by_the_constructor(
    thompson_lift: SymmetricLiftStep, thompson_compressed: CompressionStep
) -> None:
    pair = thompson_compressed.transport(examples.thompson24_homogeneous_collision())
    lifted = thompson_lift.transport(pair)
    witness = VanishingWitness(thompson_lift, lifted)

    with pytest.raises(InvariantError) as refusal:
        Certificate(Reduction((thompson_lift,)), (), witness)

    assert refusal.value.obligation == "FMT-9"


@pytest.mark.parametrize(
    "arguments",
    [
        ("not a chain",),
        (SQUARE, ((0, "not a collision"),)),
        (SQUARE, ((True, Collision.at(SQUARE, ((1, 0), (-1, 0)))),)),
        (SQUARE, (), "not a witness"),
    ],
    ids=["chain", "collision", "position", "witness"],
)
def test_arguments_of_the_wrong_type_are_refused(arguments: tuple[Any, ...]) -> None:
    with pytest.raises(TypeError):
        Certificate(*arguments)


def test_a_collision_that_fails_names_its_place() -> None:
    """FMT-11: the obligation of the part, and the collision it failed in."""
    wrong = Collision(((1, 0), (-1, 0)), (2, 0))

    with pytest.raises(VerificationError) as failure:
        Certificate(SQUARE, ((0, wrong),)).verify()

    assert (failure.value.obligation, failure.value.location) == (
        "COL-3",
        "collision 0",
    )


def test_a_step_that_fails_names_its_step() -> None:
    def changed(document: Any) -> None:
        document["maps"][2]["components"][1].append([[0, 0, 0], "7"])

    failure_text = edited(SMALL_TEXT, changed)

    with pytest.raises(VerificationError) as failure:
        Certificate.loads(failure_text).verify()

    assert failure.value.location == "step 1"


def test_a_witness_that_fails_names_the_witness(
    witness_text: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The witness of Thompson's map verifies, so its failure is simulated.

    What is checked is only that ``Certificate.verify`` attaches the place.
    """
    certificate = Certificate.loads(witness_text)

    def fail(self: VanishingWitness) -> None:
        raise VerificationError("VAN-4", "simulated")

    monkeypatch.setattr(VanishingWitness, "verify", fail)

    with pytest.raises(VerificationError) as failure:
        certificate.verify()

    assert (failure.value.obligation, failure.value.location) == ("VAN-4", "witness")


# --------------------------------------------------------------------------
# The licence rule
# --------------------------------------------------------------------------

SKIPPED = {
    ".git",
    ".venv",
    "dist",
    "build_env",
    "min_env",
    "sdist_env",
    "sdist_tree",
    "sdist_build",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
}
"""Directories a build or a tool creates, and none of them is distributed."""


def certificate_files(root: Path) -> list[str]:
    """Return every file under ``root`` that is a certificate of this format.

    By content and not by name, since a file can be called anything. A text
    that is a JSON object whose ``format`` is the one of FMT-1 is one.
    """
    found = []
    for path in root.rglob("*"):
        if not path.is_file() or SKIPPED & set(path.relative_to(root).parts):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if not text.lstrip().startswith("{"):
            continue
        try:
            document = json.loads(text)
        except ValueError:
            continue
        if (
            isinstance(document, dict)
            and document.get("format") == "kellermap-certificate"
        ):
            found.append(str(path.relative_to(root)))

    return found


def test_the_repository_holds_no_certificate_file() -> None:
    """``docs/contracts.md`` under "Files and the licence rule".

    A file of a chain carries the values of its maps, and two maps of these
    chains have no licence. So no file of this format is kept in the tree. The
    tests write theirs in memory or into a temporary directory.
    """
    found = certificate_files(ROOT)

    assert not found, f"certificate files in the tree: {found}"


def test_the_search_finds_a_certificate_file(tmp_path: Path) -> None:
    """The control: a file ``dumps`` wrote is found, under any name."""
    (tmp_path / "notes.txt").write_text("not a certificate", encoding="utf-8")
    (tmp_path / "other.json").write_text('{"format": "other"}', encoding="utf-8")
    (tmp_path / "broken.json").write_text("{not json", encoding="utf-8")
    (tmp_path / "chain.data").write_text(SMALL_TEXT, encoding="utf-8")
    (tmp_path / "binary").write_bytes(bytes([0xFF, 0xFE, 0x00]))

    assert certificate_files(tmp_path) == ["chain.data"]
