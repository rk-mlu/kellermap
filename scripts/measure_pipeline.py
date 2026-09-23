"""The four stages of milestone 0.6, on every map this project can start from.

`docs/references.md` compares this project's figures with the published ones
under "What the pipeline reaches". This script is where those figures come
from. It runs the whole chain on each of the three degree-three maps in
`kellermap.examples`, checks every step through the library's own verification
surface, and compares what comes out with what the page says.

It also recomputes what the Schur reduction leaves at each stage, which is
what SYM-7 rests its explanation on, and compares it with ``CARRIERS``, the
table ``docs/roadmap.md`` carries under work package 1.

The two tables here and the two on the pages are held against each other by
``tests/test_documentation.py``, row by row. Until ``0.7.0rc13`` the test asked
only whether each number occurred somewhere in the section, and an audit of
``0.7.0rc12`` changed a carrier from 16 to 17 and watched it stay green,
because 17 occurs elsewhere in that table. The same held for the pipeline
table, which that test had been written for. A row is a label and its values,
so the values are checked against the label.

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

The exit status is 0 if every figure agrees with the tables here and 1
otherwise. That the tables agree with the pages is the tests' to say.
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
class Carrier:
    """What ``docs/roadmap.md`` states about one stage of one chain.

    The complement is what ``determinant()`` is left with after the Schur
    reduction, and it is the quantity SYM-7 rests its explanation on. It was
    the one column of that table nothing recomputed, and an audit of
    ``0.7.0rc11`` was not needed to find it wrong: smoke-testing another
    script was enough, because the figures had stopped matching the code at
    some point nobody can name. Now it is recomputed.
    """

    stage: str
    dimension: int
    diagonal_ones: int
    carrier: int


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

LIFT_COMPLEMENT_MONOMIALS = 13589
"""The monomials in the complement of the lift of ``spacerat11``.

The one carrier figure stated in prose rather than in the table, so the row
check does not reach it and it is held on its own.
"""

CARRIERS: dict[str, tuple[Carrier, ...]] = {
    "spacerat11": (
        Carrier("UnipotentStep", 22, 20, 16),
        Carrier("HomogenizationStep", 23, 21, 17),
        Carrier("CompressionStep", 19, 17, 13),
        Carrier("SymmetricLiftStep", 38, 28, 10),
    ),
    "alpoege12": (
        Carrier("UnipotentStep", 24, 24, 20),
        Carrier("HomogenizationStep", 25, 25, 21),
        Carrier("CompressionStep", 20, 20, 16),
        Carrier("SymmetricLiftStep", 40, 30, 10),
    ),
    "alpoege13": (
        Carrier("UnipotentStep", 26, 26, 20),
        Carrier("HomogenizationStep", 27, 27, 21),
        Carrier("CompressionStep", 22, 22, 16),
        Carrier("SymmetricLiftStep", 44, 38, 12),
    ),
}


def monomials(polynomial_map: PolynomialMap) -> int:
    """Return the number of terms in the displacement."""
    return sum(
        len(component.terms())
        for component in polynomial_map.displacement().to_polynomials()
    )


def check(
    label: str, measured: object, claimed: object, page: str = "references"
) -> None:
    """Compare one recomputed figure with the value the page states."""
    mark = "ok " if measured == claimed else "BAD"
    print(f"  [{mark}] {label}: {measured} (page says {claimed})")
    if measured != claimed:
        raise SystemExit(
            f"{label}: measured {measured}, and docs/{page}.md says {claimed}."
        )


def check_carrier(name: str, stage: str, target: PolynomialMap) -> None:
    """Check the carrier of one stage against ``docs/roadmap.md``."""
    stated = next(row for row in CARRIERS[name] if row.stage == stage)
    rows = target._jacobian_polynomials  # noqa: SLF001
    ones = sum(
        1 for index in range(target.dimension) if rows[index][index] == target.ring.one
    )
    carried = len(target.carrier_indices)

    check(f"{stage}: dimension", target.dimension, stated.dimension, "roadmap")
    check(f"{stage}: diagonal ones", ones, stated.diagonal_ones, "roadmap")
    check(f"{stage}: carried", carried, stated.carrier, "roadmap")
    check(
        f"{stage}: complement",
        target.dimension - carried,
        stated.dimension - stated.carrier,
        "roadmap",
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
    check_carrier(row.name, "UnipotentStep", unipotent.target)

    homogenized = HomogenizationStep.build(unipotent.target)
    homogenized.verify()
    collision = homogenized.transport(collision)
    check("cubic homogeneous", homogenized.target.dimension, row.homogeneous)
    check(
        "monomials there",
        monomials(homogenized.target),
        row.homogeneous_monomials,
    )
    check_carrier(row.name, "HomogenizationStep", homogenized.target)

    compression = CompressionStep.build(homogenized.target, collision)
    compression.verify()
    collision = compression.transport(collision)
    check("after compression", compression.target.dimension, row.compressed)
    check(
        "monomials there",
        monomials(compression.target),
        row.compressed_monomials,
    )
    check_carrier(row.name, "CompressionStep", compression.target)

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
    check_carrier(row.name, "SymmetricLiftStep", symmetric.target)

    if row.name == "spacerat11":
        complement = symmetric.target._schur_complement(  # noqa: SLF001
            symmetric.target.carrier_indices
        )
        assert complement is not None
        check(
            "monomials in the complement of the lift",
            sum(len(entry.to_dict()) for line in complement for entry in line),
            LIFT_COMPLEMENT_MONOMIALS,
            "roadmap",
        )

    print(f"  {time.perf_counter() - started:.1f} s")


def main() -> int:
    print(
        "The pipeline of milestone 0.6, against docs/references.md, and what "
        "the\nSchur reduction leaves at each stage, against docs/roadmap.md."
    )
    for row in TABLE:
        run(row)

    print(
        "\nEvery figure agrees with the tables in this script. The tests hold "
        "those\nagainst docs/references.md and docs/roadmap.md row by row."
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
