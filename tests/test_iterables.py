"""Every interface declared as ``Iterable`` accepts a generator.

The occasion is a finding of the audit of 0.2.0rc2. ``BCWStep.build`` passed
its ``variables`` argument on to two constructor calls, and a generator was
spent after the first. The regular constructor accepted the same generator. Two
entry points with the same type annotation therefore behaved differently, and
nobody who passes tuples notices that.

This file does not check the one place alone. Writing ``Iterable`` is a promise
to make do with an object that can be walked once. The promise holds for the
whole surface or for none of it.
"""

import inspect
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
    examples,
    over_field,
)
from kellermap.bcw import BCWStep
from kellermap.reduction import LinearStep

x1, x2, x3, x4, x5 = sp.symbols("x1 x2 x3 x4 x5")

SHEAR = over_field(PolynomialMap((x1, x2, x3), (x1 + x2**3, x2, x3)))
QUARTIC = over_field(examples.factorable_shear())
SQUARE = over_field(PolynomialMap((x1, x2, x3), (x1**2, x2, x3)))
RING = SHEAR.ring

COLLISION = Collision(((1, 2, 3), (-1, 2, 3)), (1, 2, 3))
SWAP = LinearAutomorphism([Transposition(RING, 0, 1)])


def once(*items: object) -> object:
    """An iterable that can be walked exactly once."""
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
}


@pytest.mark.parametrize("case", sorted(CASES))
def test_a_one_shot_iterable_is_enough(case: str) -> None:
    assert CASES[case]() is not None


def test_bcw_step_no_longer_takes_an_iterable() -> None:
    """The place of the original finding no longer exists.

    ``BCWStep`` took the fresh variables as an ``Iterable`` and passed them on
    to two constructor calls. A generator was empty after the first. Since the
    factor slots were introduced, each slot carries its own variable and the
    parameter is gone. This test records that the signature does not return to
    that shape.
    """
    names = list(inspect.signature(BCWStep.__init__).parameters)

    assert "variables" not in names
    assert names[4:6] == ["left", "right"]
