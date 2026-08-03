"""Jede als ``Iterable`` deklarierte Schnittstelle vertraegt einen Generator.

Anlass ist ein Befund aus dem Audit von 0.2.0rc2: ``BCWStep.build`` reichte
sein ``variables``-Argument an zwei Konstruktoraufrufe weiter, und ein
Generator war nach dem ersten verbraucht. Der regulaere Konstruktor nahm
denselben Generator an. Zwei Eingaenge mit derselben Typangabe verhielten sich
also verschieden, und das faellt niemandem auf, der Tupel uebergibt.

Diese Datei prueft deshalb nicht nur die eine Stelle. Wer ``Iterable``
schreibt, sagt zu, mit einem einmal durchlaufbaren Objekt auszukommen; die
Zusage gilt fuer die ganze Oberflaeche oder fuer keine.
"""

from collections.abc import Callable

import pytest
import sympy as sp

from kellermap import (
    Collision,
    ElementaryAutomorphism,
    ElementaryFactor,
    LinearAutomorphism,
    PolynomialMap,
    Reduction,
    Transposition,
    over_field,
)
from kellermap.bcw import BCWStep
from kellermap.reduction import LinearStep

x1, x2, x3, x4, x5 = sp.symbols("x1 x2 x3 x4 x5")

SHEAR = over_field(PolynomialMap((x1, x2, x3), (x1 + x2**3, x2, x3)))
QUARTIC = over_field(PolynomialMap((x1, x2, x3), (x1 + x2**2 * x3**2, x2, x3)))
SQUARE = over_field(PolynomialMap((x1, x2, x3), (x1**2, x2, x3)))
RING = SHEAR.ring

COLLISION = Collision(((1, 2, 3), (-1, 2, 3)), (1, 2, 3))
SWAP = LinearAutomorphism([Transposition(RING, 0, 1)])


def once(*items: object) -> object:
    """Ein Iterable, das sich genau einmal durchlaufen laesst."""
    return iter(items)


CASES: dict[str, Callable[[], object]] = {
    "PolynomialMap": lambda: PolynomialMap(once(x1, x2, x3), once(x1 + x2**3, x2, x3)),
    "PolynomialMap.from_ring": lambda: PolynomialMap.from_ring(RING, once(*RING.gens)),
    "Collision": lambda: Collision(once(once(1, 2, 3), once(-1, 2, 3)), once(1, 2, 3)),
    "Collision.at": lambda: Collision.at(SQUARE, once((1, 2, 3), (-1, 2, 3))),
    "Collision.extended": lambda: COLLISION.extended(once(once(7), once(8)), once(0)),
    "Collision.with_image": lambda: COLLISION.with_image(once(4, 2, 3)),
    "ElementaryAutomorphism": lambda: ElementaryAutomorphism(
        once(ElementaryFactor(RING, 0, RING.gens[1]))
    ),
    "LinearAutomorphism": lambda: LinearAutomorphism(once(Transposition(RING, 0, 1))),
    "Reduction": lambda: Reduction(once(LinearStep.build(SHEAR, SWAP))),
    "BCWStep": lambda: BCWStep(
        QUARTIC,
        BCWStep.build(QUARTIC, 0, x2**2, x3**2, (x4, x5)).target,
        0,
        x2**2,
        x3**2,
        once(x4, x5),
    ),
    "BCWStep.build": lambda: BCWStep.build(QUARTIC, 0, x2**2, x3**2, once(x4, x5)),
}


@pytest.mark.parametrize("case", sorted(CASES))
def test_a_one_shot_iterable_is_enough(case: str) -> None:
    assert CASES[case]() is not None


def test_build_and_the_constructor_agree_on_a_generator() -> None:
    """Der Befund in seiner urspruenglichen Form.

    ``build`` konstruiert zweimal -- einmal fuer den Entwurf, der die Formel
    traegt, und einmal fuer das Ergebnis. Der Generator war nach dem ersten
    Aufruf leer, und die Meldung sprach dann von null Variablen.
    """
    built = BCWStep.build(QUARTIC, 0, x2**2, x3**2, (variable for variable in (x4, x5)))
    supplied = BCWStep(
        QUARTIC,
        built.target,
        0,
        x2**2,
        x3**2,
        (variable for variable in (x4, x5)),
    )

    assert built.variables == (x4, x5)
    assert supplied.variables == built.variables
    assert built.verify() is None
    assert supplied.verify() is None
