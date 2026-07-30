import sympy as sp

from bcw import PolynomialMap


def test_dimension() -> None:
    x, y = sp.symbols("x y")

    F = PolynomialMap(
        variables=(x, y),
        components=(x + y, x - y),
    )

    assert F.dimension == 2
