"""The chains of the reconstruction scripts, built with the library.

Each ``scripts/reconstruct_*.py`` repeats one chain in plain SymPy. This module
builds the same chains with the library, from the step data the scripts carry,
and returns each as a ``Certificate``: the chain, Alpoege's collision at its
source and the transported collision at its target.

Two work packages of milestone 0.9 need them. FMT-10 asks that each is read
back from its file and verified, and CHK-8 that the checker verifies the same
files. The data is read from the scripts and not copied, so the chain built
here and the chain a script computes rest on one transcription. What the
library adds is its own arithmetic: every step is built with ``build`` and the
script's ``apply`` is never called.

The seven scripts that start from Alpoege's map are covered here. The eighth,
``reconstruct_prellberg40.py``, compresses and lifts Thompson's map, and the
library builds that chain from ``kellermap.examples`` without the script's data.
``tests/conftest.py`` builds its two steps once per session, so the test that
uses it takes them from there.

The script data is read without ``tests/data.py``. The two maps that file holds
are the ends of two of these chains, and the chains reach them from their
steps. Nothing here compares an end with that file.
"""

from __future__ import annotations

import importlib.util
import sys
from functools import cache
from pathlib import Path
from types import ModuleType
from typing import Any

import sympy as sp

from kellermap import (
    Certificate,
    Collision,
    LinearStep,
    PolynomialMap,
    Reduction,
    over_field,
)
from kellermap.bcw import BCWStep
from kellermap.bcw.step import Carried, Fresh
from kellermap.reduction import Step

ROOT = Path(__file__).resolve().parent.parent

NORMALIZED = ("bcw17", "alpoege15", "alpoege13", "alpoege12", "macfarlane13")
"""The chains whose script normalizes Alpoege's map before the first step."""

UNNORMALIZED = ("spacerat11", "alpoege19")
"""The chains whose script starts from Alpoege's map as it is."""

NAMES = NORMALIZED + UNNORMALIZED


@cache
def script(name: str) -> ModuleType:
    """Return the module of ``scripts/reconstruct_<name>.py``, loaded once."""
    path = ROOT / "scripts" / f"reconstruct_{name}.py"
    spec = importlib.util.spec_from_file_location(f"reconstruct_{name}", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    return module


def _level(source: PolynomialMap, slots: tuple[Fresh | Carried, ...]) -> int:
    """Return the filtration level the step can declare, BCW-6.

    ``H`` lies in ``EA^1`` when every factor it introduces has order two or
    more. A carried slot introduces nothing.
    """
    for slot in slots:
        if isinstance(slot, Fresh):
            terms = sp.Poly(slot.polynomial, *source.variables).monoms()
            if min(sum(monomial) for monomial in terms) < 2:
                return 0

    return 1


def _plan(step: Any) -> tuple[int, Fresh | Carried, Fresh | Carried, sp.Expr]:
    """Return index, slots and coefficient of one step of a script.

    The scripts write their steps in four shapes, and each is read by the
    attributes it has.
    """
    coefficient = getattr(step, "coefficient", sp.Integer(1))

    if hasattr(step, "u"):
        return step.target, Fresh(step.P, step.u), Fresh(step.Q, step.v), coefficient
    if hasattr(step, "carrier"):
        return (
            step.target,
            Carried(step.carrier),
            Fresh(step.other, step.fresh),
            coefficient,
        )

    def slot(entry: Any) -> Fresh | Carried:
        if hasattr(entry, "fresh"):
            return Fresh(entry.value, entry.fresh)
        return Carried(entry.index)

    return step.target, slot(step.left), slot(step.right), coefficient


def _plans_of_alpoege19() -> list[tuple[int, Fresh | Carried, Fresh | Carried, Any]]:
    """Return the steps of the nineteen-dimensional chain.

    That script names components by their variable, so the index of each is
    read off the order in which the chain introduces its variables.
    """
    module = script("alpoege19")
    order = [module.x, module.y, module.z]
    plans = []
    for target, left, right, coefficient in module.STEPS:
        slots: list[Fresh | Carried] = []
        for entry in (left, right):
            if len(entry) == 3:
                slots.append(Fresh(entry[2], entry[1]))
            else:
                slots.append(Carried(order.index(entry[1])))
        plans.append((order.index(target), slots[0], slots[1], coefficient))
        for entry in (left, right):
            if len(entry) == 3 and entry[1] not in order:
                order.append(entry[1])

    return plans


def _source(name: str) -> tuple[PolynomialMap, tuple[tuple[sp.Expr, ...], ...]]:
    """Return Alpoege's map in the script's coordinates, and its three points."""
    module = script(name)
    if name == "alpoege19":
        variables = (module.x, module.y, module.z)
        points = module.ALPOEGE_POINTS
    else:
        variables = tuple(module.X[:3])
        points = module.ALPOEGE_COLLISION

    return PolynomialMap(variables, module.ALPOEGE), tuple(points)


@cache
def certificate(name: str) -> Certificate:
    """Return the chain of one script as a certificate the library built."""
    source, points = _source(name)
    if name in NORMALIZED:
        source = over_field(source)

    steps: list[Step] = []
    current = source
    if name in NORMALIZED:
        normalization = LinearStep.normalize(source)
        steps.append(normalization)
        current = normalization.target

    if name == "alpoege19":
        plans = _plans_of_alpoege19()
    else:
        plans = [_plan(step) for step in script(name).STEPS]

    for index, left, right, coefficient in plans:
        step = BCWStep.build(
            current,
            index,
            left,
            right,
            filtration_level=_level(current, (left, right)),
            coefficient=coefficient,
        )
        steps.append(step)
        current = step.target

    reduction = Reduction(steps)
    collision = Collision.at(source, points)

    return Certificate(
        reduction,
        ((0, collision), (len(steps), reduction.transport(collision))),
    )


def script_target(name: str) -> tuple[sp.Expr, ...]:
    """Return the components the script computes at the end of its chain."""
    module = script(name)
    if name == "alpoege19":
        components, order, _, _, _ = module.apply_steps()
        return tuple(components[variable] for variable in order)

    return tuple(module.reduce_alpoege())
