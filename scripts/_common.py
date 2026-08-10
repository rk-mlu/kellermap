"""Shared helpers for the two search drivers.

Not part of the library and not a gate. It exists so that ``read`` and
``describe`` are written once rather than twice, since a second copy is a
second thing to keep in step.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

from kellermap import PolynomialMap, Reduction
from kellermap.bcw import BCWStep, Carried

ROOT = Path(__file__).resolve().parent.parent


def read(name: str) -> ModuleType:
    """Return a module under ``tests/``, for the data the package does not ship.

    Everything a script needs is importable from ``kellermap.examples`` except
    the nineteen-dimensional map, whose licence could not be established and
    which therefore stays out of the wheel. This detour exists for that one map
    only, which puts the distinction in the code and not only in a document.
    """
    path = ROOT / "tests" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"{name}_data", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot read fixed data from {path}.")

    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(ROOT))
    spec.loader.exec_module(module)

    return module


def describe(reduction: Reduction, published: PolynomialMap) -> str:
    """Return everything needed to replay the chain, by name and not by index.

    A chain lists its generators in the order its steps introduced them, so
    every position in it depends on the chain. Positions are therefore printed
    as generator names: the component a step acts on, the coordinate a
    ``Carried`` slot reuses, and -- the part that was missing and made an
    earlier version of this report useless -- the name each fresh slot was
    given. Without those names the introduction order cannot be recovered, and
    without the introduction order neither the reordering of SEA-4 nor the
    endpoint comparison of SEA-5 can be redone.

    What the caller still needs, and already has: the source map, the value
    pool, and this library.
    """
    lines = [
        "# Replay by name. Positions belong to the chain, names do not.",
        "STEPS = (",
    ]

    for step in reduction.steps:
        # ``Reduction`` holds ``Step``, and only a ``BCWStep`` has slots and a
        # coefficient. A chain that begins with a linear normalization has
        # both kinds in it, so the narrowing is real and not a formality.
        if not isinstance(step, BCWStep):
            lines.append(f"    ({type(step).__name__},),")
            continue

        slots = []
        for slot in (step.left, step.right):
            if isinstance(slot, Carried):
                slots.append(f'("carried", {step.source.variables[slot.index]})')
            else:
                slots.append(f'("fresh", {slot.polynomial}, {slot.variable})')
        target = step.source.variables[step.index]
        lines.append(
            f"    ({target}, {slots[0]}, {slots[1]}, "
            f"{step.filtration_level}, {step.coefficient}),"
        )

    lines.append(")")
    lines.append("")

    order = reduction.target.variables
    lines.append(f"# introduction order: {', '.join(str(v) for v in order)}")
    lines.append(f"# dimensions:         {reduction.dimensions()}")
    lines.append(f"# degrees:            {reduction.degrees()}")

    coefficients = ", ".join(
        str(step.coefficient) if isinstance(step, BCWStep) else "-"
        for step in reduction.steps
    )
    lines.append(f"# coefficients:       {coefficients}")

    return "\n".join(lines)


def sanity(reduction: Reduction, published: PolynomialMap) -> bool:
    """Return whether the chain verifies and reaches the published map.

    Printed beside the chain so that a report carries its own check. The
    endpoint is compared against the published map itself, not against
    anything the search produced.
    """
    reduction.verify()

    return bool(reduction.target.reordered(published.variables) == published)
