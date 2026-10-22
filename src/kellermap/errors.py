"""The exceptions a failing certificate and a refused construction raise.

Verification returns nothing and raises on failure. A boolean would collapse
several distinct obligations into one bit, and the first question anyone asks
of a failed certificate is *which* obligation failed -- see ``contracts.md``,
STEP-1.

Every obligation in ``contracts.md`` carries a stable identifier, and the
exception carries it too. A review can then address a finding to a numbered
obligation rather than to a line of code.

A constructor that refuses its arguments raises ``InvariantError``, a
``ValueError`` that carries the identifier as well. Since work package 2.2 of
milestone 0.9 every constructor invariant of a step, a collision, a reduction
and a witness does. The factor types and ``PolynomialMap`` have no obligations
of their own and raise a plain ``ValueError``.
"""

from __future__ import annotations


class VerificationError(Exception):
    """An obligation from ``docs/contracts.md`` was not met.

    Parameters
    ----------
    obligation
        The identifier of the obligation, such as ``"COL-3"``.
    message
        What went wrong, in a form that names the offending object.
    step
        The index of the failing step within a reduction, where there is one.
    location
        Where the failure stands, as ``"step 4"``, ``"map 0"``,
        ``"collision 1"``, ``"witness"`` or ``"file"``. These are the strings
        the checker of milestone 0.9 uses for the same places. Given a step and
        no location, the location is ``"step i"``, so that a failure located in
        a reduction carries both.

    Attributes carry the same names. They are part of the public surface: a
    caller is expected to branch on ``obligation``, not to parse ``str(...)``.
    """

    def __init__(
        self,
        obligation: str,
        message: str,
        step: int | None = None,
        location: str | None = None,
    ) -> None:
        self.obligation = obligation
        self.message = message
        self.step = step
        self.location = (
            location if location is not None or step is None else f"step {step}"
        )

        super().__init__(self._format())

    def _format(self) -> str:
        where = "" if self.location is None else f" in {self.location}"

        return f"[{self.obligation}]{where} {self.message}"

    def located_at(self, step: int) -> VerificationError:
        """Return the same failure, attributed to a step of a reduction.

        A step verifies itself without knowing where in a chain it sits, so
        the index is attached by the reduction that catches the failure. The
        original is left untouched, since it may be held elsewhere.
        """
        return VerificationError(self.obligation, self.message, step)


class InvariantError(ValueError):
    """A constructor refused its arguments, and says which obligation it enforces.

    A subclass of ``ValueError``, so that every caller who caught a
    ``ValueError`` from a constructor still catches this one. What it adds is
    ``obligation``. A certificate read from a file cites an obligation for
    every refusal, FMT-10 in ``docs/contracts.md``, and it can only cite the
    one a constructor enforced if the constructor says which. Until milestone
    0.9 none of them did, and the identifier could only have been guessed from
    the message.

    Parameters
    ----------
    obligation
        The identifier of the obligation the invariant belongs to, such as
        ``"BCW-10"``.
    message
        What was refused, in a form that names the offending argument.
    """

    def __init__(self, obligation: str, message: str) -> None:
        self.obligation = obligation
        self.message = message

        super().__init__(f"[{obligation}] {message}")
