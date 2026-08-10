"""Jede Operation gegen jede zulaessige Gestalt eines Schritts.

Der Grund fuer dieses Modul steht in zwei Befunden, die beide nicht von einem
Test kamen.

``peeling.moves`` zaehlte die Plaetze mit ``combinations`` auf und bot damit nie
zwei ``Carried``-Plaetze auf derselben Koordinate an, obwohl BCW-6 das seit 0.3
zulaesst und der Konstruktor es baut. Gefunden hat es ein externes Audit. Und
``BCWStep.transport`` haengte je ``Fresh``-Platz eine Koordinate an statt je
frischem Generator, was bei einem Schritt mit einer Variablen in beiden
Plaetzen fehlschlaegt. Gefunden hat es der Zusammenbau der Kette zur
neunzehndimensionalen Abbildung.

Beide Male war jede einzelne Verpflichtung des Schritt-Typs geprueft, und
niemand hat gefragt, ob die *uebrigen* Teile dasselbe zulassen. Genau das
fragen die Tests hier: fuer jede Gestalt, die ``BCWStep`` baut, muessen
``verify``, ``transport`` und die Aufzaehler sie ebenfalls verarbeiten.

Eine neue zulaessige Gestalt gehoert in ``SHAPES``. Faellt dann ein Test um, so
ist das der Punkt.
"""

from collections.abc import Callable

import pytest
import sympy as sp

from kellermap import Collision, PolynomialMap, over_field
from kellermap.bcw import BCWStep, Carried, Fresh
from kellermap.peeling import moves, peel, undo
from kellermap.search import enumerate_candidates

x1, x2, x3 = sp.symbols("x1 x2 x3")
u, v = sp.symbols("u v")

Shape = tuple[str, Callable[[PolynomialMap], BCWStep]]

# Eine Quelle, in der alles gebaut werden kann: Koordinate 1 und 2 sind Traeger,
# und Koordinate 0 traegt genug, um jede Gestalt etwas entfernen zu lassen.
SOURCE = over_field(
    PolynomialMap(
        (x1, x2, x3),
        (
            x1**2 + x2**2 * x3**2 + x2**2 * x3**4 + x2**4 + x3**6,
            x2 + x3**2,
            x3 + x2**2,
        ),
    )
)

# ``x1`` occurs only squared, so these two points share an image. A real
# collision and not a pair of points with a hopeful name.
POINTS = ((1, 0, 0), (-1, 0, 0))

# Dieselbe Quelle, aber mit Traegerkomponenten, die am Kollisionspunkt nicht
# null werden. Genau daran ist ein Fehler haengen geblieben, den kein Test
# fand: ``_moved_image`` liess den Koeffizienten weg, und solange die
# getragenen Bildkoordinaten null sind, faellt das nicht auf, weil das Produkt
# ohnehin verschwindet. Ein externes Audit hat ihn gemeldet.
LOUD = over_field(
    PolynomialMap(
        (x1, x2, x3),
        (x1**2 + 3 * (x2 + 1) * (x3 + 2) + x2**4 + x3**6, x2 + 1, x3 + 2),
    )
)


def two_fresh(source: PolynomialMap, coefficient: sp.Expr) -> BCWStep:
    return BCWStep.build(source, 0, Fresh(x2**2, u), Fresh(x3**2, v), 1, coefficient)


def one_fresh(source: PolynomialMap, coefficient: sp.Expr) -> BCWStep:
    return BCWStep.build(source, 0, Carried(1), Fresh(x3**4, u), 1, coefficient)


def self_fresh(source: PolynomialMap, coefficient: sp.Expr) -> BCWStep:
    return BCWStep.build(source, 0, Fresh(x2**2, u), Fresh(x2**2, u), 1, coefficient)


def two_carried(source: PolynomialMap, coefficient: sp.Expr) -> BCWStep:
    return BCWStep.build(source, 0, Carried(1), Carried(2), 1, coefficient)


def one_carried_twice(source: PolynomialMap, coefficient: sp.Expr) -> BCWStep:
    return BCWStep.build(source, 0, Carried(2), Carried(2), 1, coefficient)


BUILDERS = {
    "two fresh": (two_fresh, 2),
    "one fresh and one carried": (one_fresh, 1),
    "one fresh in both slots": (self_fresh, 1),
    "two carried": (two_carried, 0),
    "one carried in both slots": (one_carried_twice, 0),
}

COEFFICIENTS = [sp.Integer(1), sp.Integer(-3), sp.Rational(1, 2)]

SHAPES = [
    (f"{name}, coefficient {coefficient}", builder, expected, coefficient)
    for name, (builder, expected) in BUILDERS.items()
    for coefficient in COEFFICIENTS
]

IDS = [shape[0] for shape in SHAPES]


@pytest.mark.parametrize(
    ("name", "builder", "expected", "coefficient"), SHAPES, ids=IDS
)
def test_the_constructor_builds_it(
    name: str, builder: Callable, expected: int, coefficient: sp.Expr
) -> None:
    """Die Liste selbst: was hier nicht baut, gehoert nicht in ``SHAPES``."""
    step = builder(SOURCE, coefficient)

    assert step.m == expected
    assert step.coefficient == coefficient
    assert step.target.dimension == SOURCE.dimension + expected


@pytest.mark.parametrize(
    ("name", "builder", "expected", "coefficient"), SHAPES, ids=IDS
)
def test_verify_accepts_it(
    name: str, builder: Callable, expected: int, coefficient: sp.Expr
) -> None:
    """BCW-1 bis BCW-12, an einem Schritt dieser Gestalt."""
    assert builder(SOURCE, coefficient).verify() is None


@pytest.mark.parametrize(
    ("name", "builder", "expected", "coefficient"), SHAPES, ids=IDS
)
def test_transport_carries_a_collision_through_it(
    name: str, builder: Callable, expected: int, coefficient: sp.Expr
) -> None:
    """Der Befund, der diesem Modul seinen Namen gab.

    Eine Koordinate je frischem Generator, nicht je ``Fresh``-Platz.
    """
    step = builder(SOURCE, coefficient)

    carried = step.transport(Collision.at(SOURCE, POINTS))

    assert all(len(point) == SOURCE.dimension + expected for point in carried.points)
    assert len(carried.image) == SOURCE.dimension + expected
    assert carried.verify(step.target) is None


@pytest.mark.parametrize(
    ("name", "builder", "expected", "coefficient"), SHAPES, ids=IDS
)
def test_the_factors_are_exhibited_for_it(
    name: str, builder: Callable, expected: int, coefficient: sp.Expr
) -> None:
    """Ausstellen statt behaupten: ``G`` und ``H`` sind invertierbar.

    Beide sind Produkte elementarer Faktoren, also unimodular, und ``H``
    verschiebt je frischem Generator eine Koordinate.
    """
    step = builder(SOURCE, coefficient)
    ring = step.G.ring
    # ``from_ring`` und nicht ``identity``: die Gleichheit von
    # ``PolynomialMap`` vergleicht den Koeffizientenbereich mit, und die
    # Automorphismen leben ueber ``QQ``.
    identity = PolynomialMap.from_ring(ring, ring.gens)

    assert step.G.compose(step.G.inverse()).to_polynomial_map() == identity
    assert step.G.determinant() == 1
    assert step.H.determinant() == 1
    assert len(step.variables) == expected


@pytest.mark.parametrize(
    ("name", "builder", "expected", "coefficient"), SHAPES, ids=IDS
)
def test_the_peel_offers_it_back(
    name: str, builder: Callable, expected: int, coefficient: sp.Expr
) -> None:
    """Der andere Befund. Der Aufzaehler muss anbieten, was der Typ baut.

    ``moves`` bot zwei ``Carried``-Plaetze auf einer Koordinate nie an, weil es
    ``combinations`` benutzte statt ``combinations_with_replacement``. Eine
    Kette mit einem solchen Schritt war damit unerreichbar und nicht ungefunden.
    """
    step = builder(SOURCE, coefficient)
    offered = list(moves(step.target, spare=1))

    assert any(
        undo(step.target, candidate) == SOURCE
        for candidate in offered
        if len(candidate.dropped) == expected
    )


@pytest.mark.parametrize(
    ("name", "builder", "expected", "coefficient"), SHAPES, ids=IDS
)
def test_the_peel_recovers_a_chain_of_it(
    name: str, builder: Callable, expected: int, coefficient: sp.Expr
) -> None:
    """Und der Weg zurueck fuehrt zu einer geprueften ``Reduction``."""
    step = builder(SOURCE, coefficient)

    outcome = peel(SOURCE, step.target, spare=1)

    assert outcome.reduction is not None
    assert outcome.reduction.verify() is None
    assert outcome.reduction.target.reordered(step.target.variables) == step.target


@pytest.mark.parametrize(
    ("name", "builder", "expected", "coefficient"), SHAPES, ids=IDS
)
def test_the_forward_enumerator_offers_the_ones_it_claims(
    name: str, builder: Callable, expected: int, coefficient: sp.Expr
) -> None:
    """Was der Vorwaertsaufzaehler nicht kann, sagt er hier und nicht spaeter.

    ``enumerate_candidates`` teilt eine Verschiebung in zwei Faktoren und kennt
    keinen Koeffizienten: SEA-9 und SEA-10 beschreiben Faktoren, nicht
    Gewichte. Ein Schritt mit einem Koeffizienten ungleich eins ist deshalb
    vorwaerts nicht aufzaehlbar, und das ist eine bekannte Grenze und kein
    Fehler -- der Abtrag loest den Koeffizienten, und die Tests oben zeigen,
    dass er jede Gestalt zurueckbekommt.
    """
    step = builder(SOURCE, coefficient)
    values = [
        sp.expand(step.target.components[index] - step.target.variables[index])
        for index in step.target.carrier_indices
    ]

    candidates = list(enumerate_candidates(SOURCE, values))

    assert isinstance(candidates, list)
    if coefficient == 1 and expected == 2:
        assert candidates


@pytest.mark.parametrize("coefficient", COEFFICIENTS)
def test_the_transported_image_is_scaled_by_the_coefficient(
    coefficient: sp.Expr,
) -> None:
    """``G`` skaliert das entfernte Produkt, also auch im Bild.

    Der Test, den es haette geben muessen. Die Kollisionsbilder der bisherigen
    Tests hatten in den getragenen Koordinaten eine Null, und ein Produkt mit
    einer Null merkt sich keinen Faktor. Hier sind sie ``1`` und ``2``, also
    schlaegt jeder vergessene Koeffizient durch.
    """
    collision = Collision.at(LOUD, POINTS)
    step = BCWStep.build(LOUD, 0, Carried(1), Carried(2), 1, coefficient)

    moved = step.transport(collision)

    assert collision.image[1] != 0
    assert collision.image[2] != 0
    assert moved.image[0] == sp.expand(
        collision.image[0] - coefficient * collision.image[1] * collision.image[2]
    )
    assert moved.verify(step.target) is None


@pytest.mark.parametrize("coefficient", COEFFICIENTS)
def test_a_fresh_slot_contributes_nothing_to_the_image(
    coefficient: sp.Expr,
) -> None:
    """Und ohne getragenen Platz aendert der Koeffizient das Bild nicht.

    Die Gegenprobe: eine frische Koordinate wird im Bild mit null aufgefuellt,
    also ist das Produkt null, und kein Koeffizient rettet es. Ohne diese
    Haelfte waere der Test oben mit einer zu allgemeinen Regel vereinbar.
    """
    collision = Collision.at(LOUD, POINTS)
    step = BCWStep.build(LOUD, 0, Fresh(x2**2, u), Fresh(x3**2, v), 1, coefficient)

    moved = step.transport(collision)

    assert moved.image[: LOUD.dimension] == collision.image
    assert moved.image[LOUD.dimension :] == (0, 0)
    assert moved.verify(step.target) is None
