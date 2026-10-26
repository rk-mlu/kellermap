"""An independent checker for the certificate files of ``kellermap``.

``docs/contracts.md`` states what it promises, CHK-1 to CHK-8. It reads a file
of the format FMT-1 to FMT-12 and checks the obligations of every map, step,
collision and witness in it that can fail on a file. It imports nothing from
``kellermap``: the reading, the formulas and the determinant are written here
again, with SymPy for the rings and the domains. A test holds it to that.

In Python, ``check(text)`` returns a ``Report`` whose ``verdict`` is
``"VERIFIED"`` for a file every check passes. From the command line::

    python -m kellermap_check FILE [--skip ID ...]

Three verdicts, CHK-6. ``VERIFIED``: every check that applies was made and
passed. ``INCOMPLETE``: a caller left out checks with ``skip``, and every
check made passed. ``REFUSED``: a check failed, and ``check`` raises
``Refusal``. The exit status is 0, 3 and 1, and 2 for a file that cannot be
opened or a wrong call.

The order of the checks is fixed, so that one file always gives one refusal:

1. The file by the format, in ``_reading``: the JSON, the keys and the
   version, each map, the shape of each step, each collision, and the
   witness, in the order of the file.
2. The steps, in the order of the file. Within a step, the order stands in
   the docstring of its function in ``_checks``.
3. The collisions, in the order of the file: COL-1, COL-4, COL-3.
4. The witness: VAN-1, VAN-2, and the range of the depth in VAN-3.

What is not checked, CHK-5: the self-checks of the library, which follow from
the obligations checked here, and SYM-7 and VAN-5, which neither computes.
The report names the last two where the file rests on them.
"""

from __future__ import annotations

from collections.abc import Iterable

from . import _checks
from ._reading import Document, read
from ._report import INCOMPLETE, REFUSED, VERIFIED, Ledger, Refusal, Report

__all__ = ["CHECKS", "INCOMPLETE", "REFUSED", "VERIFIED", "Refusal", "Report", "check"]

CHECKS = frozenset(
    {
        "COL-1",
        "COL-3",
        "COL-4",
        "BCW-1",
        "BCW-2",
        "BCW-4",
        "BCW-6",
        "BCW-10",
        "BCW-11",
        "BCW-12",
        "LIN-1",
        "LIN-2",
        "LIN-6",
        "TRA-1",
        "TRA-6",
        "UNI-1",
        "UNI-2",
        "UNI-3",
        "UNI-4",
        "UNI-5",
        "HOM-1",
        "HOM-2",
        "HOM-3",
        "HOM-4",
        "CHC-1",
        "CHC-2",
        "CHC-3",
        "CHC-4",
        "CHC-5",
        "SYM-1",
        "SYM-3",
        "SYM-4",
        "SYM-5",
        "DSC-1",
        "DSC-2",
        "DSC-3",
        "DSC-4",
        "VAN-1",
        "VAN-2",
        "VAN-3",
    }
)
"""The identifiers of the table of CHK-4, which ``skip`` may name."""

FORMAT = (
    "FMT-1",
    "FMT-2",
    "FMT-3",
    "FMT-4",
    "FMT-5",
    "FMT-6",
    "FMT-7",
    "FMT-8",
    "FMT-9",
)
"""The rules of the format the reading checks, reported for the file."""

KELLER = ("UnipotentStep", "CompressionStep", "SymmetricLiftStep")
"""The step types that check that their source is a Keller map."""


def check(text: str, skip: Iterable[str] = frozenset()) -> Report:
    """Check the text of a certificate file and return what it rests on.

    Raises ``Refusal`` for a file that breaks an obligation, and
    ``ValueError`` for a ``skip`` that names a check this checker does not
    make.
    """
    left_out = frozenset(skip)
    unknown = left_out - CHECKS
    if unknown:
        raise ValueError(
            f"{sorted(unknown)} are not checks of this checker; CHK-4 lists them."
        )

    document = read(text)
    ledger = Ledger(left_out)
    ledger.checked["file"] = list(FORMAT)

    for index, step in enumerate(document.steps):
        context = _checks.Context(ledger, f"step {index}")
        _checks.STEPS[step.kind](
            context, step, document.maps[index], document.maps[index + 1]
        )

    for number, entry in enumerate(document.collisions):
        context = _checks.Context(ledger, f"collision {number}")
        _checks.collision(context, entry, document.maps[entry.position])

    if document.witness is not None:
        witness = document.witness
        checked = ledger.checked.get(f"collision {witness.collision}", [])
        _checks.witness(
            _checks.Context(ledger, "witness"),
            document.maps[witness.step],
            document.maps[witness.step + 1],
            witness.depth,
            all(identifier in checked for identifier in ("COL-1", "COL-3", "COL-4")),
        )

    return _report(document, ledger)


def _report(document: Document, ledger: Ledger) -> Report:
    claims = [
        f"step {index} ({step.kind}) takes map {index} to map {index + 1}"
        for index, step in enumerate(document.steps)
    ]
    claims += [
        f"collision {number} is a collision of map {entry.position}, "
        f"{len(entry.points)} distinct points with one image"
        for number, entry in enumerate(document.collisions)
    ]
    not_computed = []
    if any(step.kind == "SymmetricLiftStep" for step in document.steps):
        not_computed.append("SYM-7")
    if document.witness is not None:
        witness = document.witness
        claims.append(
            f"the form of step {witness.step} with collision {witness.collision} is "
            "a witness: the lift of a cubic source and a collision of its gradient "
            f"map; the depth {witness.depth} is in range, and the hypothesis is not "
            "computed here (VAN-3)"
        )
        not_computed.append("VAN-5")

    not_claimed = []
    if not document.steps and not document.collisions:
        not_claimed.append("this file makes no mathematical claim")
    elif not document.steps or document.steps[0].kind not in KELLER:
        not_claimed.append(
            "that map 0 is a Keller map: no step of this file checks its source "
            "for it there (RED-3)"
        )

    return Report(
        INCOMPLETE if ledger.skipped else VERIFIED,
        tuple((location, tuple(found)) for location, found in ledger.checked.items()),
        tuple((location, tuple(found)) for location, found in ledger.skipped.items()),
        tuple(not_computed),
        tuple(claims),
        tuple(not_claimed),
    )
