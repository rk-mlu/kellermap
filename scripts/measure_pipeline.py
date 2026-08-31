"""The four stages of milestone 0.6, on every map this project can start from.

`docs/references.md` compares this project's figures with the published ones
under "What the pipeline reaches". This script is where those figures come
from. It runs the whole chain on each of the three degree-three maps in
`kellermap.examples`, checks every step through the library's own verification
surface, and compares what comes out with what the page says.

Every figure the page states about the pipeline is in ``FIGURES`` below, and
``tests/test_documentation.py`` requires each of them to occur in that section.
Editing a number in one place and not the other leaves one of the two red.

The stages, in order:

- ``LinearStep.normalize`` where the source is not in ``MA^1``,
- ``UnipotentStep``, Section 4's second step, which doubles,
- ``HomogenizationStep``, the third step, which adds one,
- ``CompressionStep``, collision-hull compression,
- ``SymmetricLiftStep``, the gradient form, which doubles again.

What is checked here is the arithmetic. What the numbers are worth against the
published ones is on the page, and the short form is that nothing here claims
minimality and the construction composes published theorems.

Run with::

    python scripts/measure_pipeline.py

The exit status is 0 if every figure agrees and 1 otherwise.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

import sympy as sp

from kellermap import (
    Collision,
    CompressionStep,
    LinearStep,
    PolynomialMap,
    SymmetricLiftStep,
    examples,
    over_field,
)
from kellermap.bcw import HomogenizationStep, UnipotentStep


@dataclass(frozen=True)
class Row:
    """What the page states for one starting map."""

    name: str
    degree_three: int
    unipotent: int
    homogeneous: int
    homogeneous_monomials: int
    compressed: int
    compressed_monomials: int
    quartic: int
    quartic_monomials: int


TABLE: tuple[Row, ...] = (
    Row("spacerat11", 11, 22, 23, 60, 19, 56, 38, 386),
    Row("alpoege12", 12, 24, 25, 60, 20, 55, 40, 398),
    Row("alpoege13", 13, 26, 27, 73, 22, 68, 44, 506),
)

FIGURES = (
    11,
    22,
    23,
    60,
    19,
    56,
    38,
    386,
    12,
    24,
    25,
    20,
    55,
    40,
    398,
    13,
    26,
    27,
    73,
    68,
    44,
    506,
)
"""Every number this script asserts, for the test that ties it to the page.

``60`` occurs twice in the table and once here. ``22`` is the unipotent
dimension of the first row and the compressed dimension of the third, which is
a coincidence of two different stages and not a figure stated twice.
"""


def monomials(polynomial_map: PolynomialMap) -> int:
    """Return the number of terms in the displacement."""
    return sum(
        len(component.terms())
        for component in polynomial_map.displacement().to_polynomials()
    )


def check(label: str, measured: object, claimed: object) -> None:
    """Compare one recomputed figure with the value the page states."""
    mark = "ok " if measured == claimed else "BAD"
    print(f"  [{mark}] {label}: {measured} (page says {claimed})")
    if measured != claimed:
        raise SystemExit(
            f"{label}: measured {measured}, and docs/references.md says {claimed}."
        )


def run(row: Row) -> None:
    """Run the pipeline on one map and check every figure of its row."""
    print(f"\n{row.name}")
    started = time.perf_counter()

    source = over_field(getattr(examples, row.name)())
    collision = getattr(examples, f"{row.name}_collision")()
    check("degree three", source.dimension, row.degree_three)

    # Section 4 starts from MA^1. alpoege12 is there already; the other two
    # are not, and the normalization moves neither the dimension nor the
    # points.
    if not source.is_in_MA(1):
        normalization = LinearStep.normalize(source)
        normalization.verify()
        source = normalization.target
        collision = normalization.transport(collision)

    unipotent = UnipotentStep.build(source)
    unipotent.verify()
    collision = unipotent.transport(collision)
    check("after the unipotent reduction", unipotent.target.dimension, row.unipotent)

    homogenized = HomogenizationStep.build(unipotent.target)
    homogenized.verify()
    collision = homogenized.transport(collision)
    check("cubic homogeneous", homogenized.target.dimension, row.homogeneous)
    check(
        "monomials there",
        monomials(homogenized.target),
        row.homogeneous_monomials,
    )

    compression = CompressionStep.build(homogenized.target, collision)
    compression.verify()
    collision = compression.transport(collision)
    check("after compression", compression.target.dimension, row.compressed)
    check(
        "monomials there",
        monomials(compression.target),
        row.compressed_monomials,
    )

    # The lift carries a pair, and every collision here has three points, so
    # the caller chooses which two. The first two, in the order the chain
    # produced them.
    pair = Collision(collision.points[:2], collision.image)
    symmetric = SymmetricLiftStep.build(compression.target)
    symmetric.verify()
    moved = symmetric.transport(pair)
    form = sp.Poly(symmetric.form, *symmetric.variables)

    check("the gradient form", symmetric.target.dimension, row.quartic)
    check("monomials in P", len(form.terms()), row.quartic_monomials)
    check("the degree of P", form.total_degree(), 4)
    check("points in the lifted collision", len(moved.points), 2)

    print(f"  {time.perf_counter() - started:.1f} s")


def main() -> int:
    print("The pipeline of milestone 0.6, checked against docs/references.md.")
    for row in TABLE:
        run(row)

    print("\nEvery figure agrees with docs/references.md.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
