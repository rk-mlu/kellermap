"""The exception a failing certificate raises.

Verification returns nothing and raises on failure. A boolean would collapse
several distinct obligations into one bit, and the first question anyone asks
of a failed certificate is *which* obligation failed -- see ``contracts.md``,
STEP-1.

Every obligation in ``contracts.md`` carries a stable identifier, and the
exception carries it too. A review can then address a finding to a numbered
obligation rather than to a line of code.
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

    Attributes carry the same names. They are part of the public surface: a
    caller is expected to branch on ``obligation``, not to parse ``str(...)``.
    """

    def __init__(self, obligation: str, message: str, step: int | None = None) -> None:
        self.obligation = obligation
        self.message = message
        self.step = step

        super().__init__(self._format())

    def _format(self) -> str:
        location = "" if self.step is None else f" in step {self.step}"

        return f"[{self.obligation}]{location} {self.message}"

    def located_at(self, step: int) -> VerificationError:
        """Return the same failure, attributed to a step of a reduction.

        A step verifies itself without knowing where in a chain it sits, so
        the index is attached by the reduction that catches the failure. The
        original is left untouched, since it may be held elsewhere.
        """
        return VerificationError(self.obligation, self.message, step)
