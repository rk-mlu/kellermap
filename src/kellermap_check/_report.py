"""The verdicts of the checker, its report and its refusal, CHK-6 and CHK-7."""

from __future__ import annotations

from dataclasses import dataclass, field

VERIFIED = "VERIFIED"
"""Every check that applies to the file was made, and every one passed."""

INCOMPLETE = "INCOMPLETE"
"""Every check that was made passed, and a caller left at least one out."""

REFUSED = "REFUSED"
"""A check failed. ``check`` raises ``Refusal`` and returns no report."""

NOT_COMPUTED = {
    "SYM-7": "the determinant of a lift is one, by Theorem 3 of arXiv:2608.12543v3",
    "VAN-5": "the conclusion of the Vanishing Conjecture fails, by part 4 of "
    "that theorem",
}
"""Consequences that neither this checker nor the library computes, CHK-5."""


class Refusal(Exception):
    """A file the checker refuses, with the obligation and where it failed.

    Attributes
    ----------
    obligation
        The identifier of ``docs/contracts.md`` that failed, such as
        ``"BCW-1"`` or ``"FMT-6"``.
    location
        ``"file"``, ``"map i"``, ``"step i"``, ``"collision k"`` or
        ``"witness"``.
    message
        What failed, naming the object.
    """

    def __init__(self, obligation: str, location: str, message: str) -> None:
        self.obligation = obligation
        self.location = location
        self.message = message

        super().__init__(f"[{obligation}] in {location} {message}")


@dataclass(frozen=True)
class Report:
    """What an accepted file rests on, CHK-7.

    Attributes
    ----------
    verdict
        ``VERIFIED`` or ``INCOMPLETE``.
    checked
        For every object that was checked, its location and the identifiers
        checked there, in the order they were checked.
    skipped
        For every object with a check left out at the caller's request, its
        location and those identifiers.
    not_computed
        The consequences the file rests on and that were not computed.
    claims
        The statements the file makes and the checker confirmed.
    not_claimed
        What a reader might take from the file and the checker did not
        confirm.
    """

    verdict: str
    checked: tuple[tuple[str, tuple[str, ...]], ...]
    skipped: tuple[tuple[str, tuple[str, ...]], ...]
    not_computed: tuple[str, ...]
    claims: tuple[str, ...]
    not_claimed: tuple[str, ...] = ()

    def lines(self) -> list[str]:
        """Return the report as the command line prints it."""
        lines = [self.verdict]
        for heading, entries in (("checked", self.checked), ("skipped", self.skipped)):
            for location, identifiers in entries:
                lines.append(f"  {heading:8} {location}: {' '.join(identifiers)}")
        for claim in self.claims:
            lines.append(f"  claim    {claim}")
        for item in self.not_claimed:
            lines.append(f"  not claimed  {item}")
        for identifier in self.not_computed:
            lines.append(f"  not computed {identifier}: {NOT_COMPUTED[identifier]}")

        return lines


@dataclass
class Ledger:
    """What was checked and left out, per object, while a file is read."""

    skip: frozenset[str]
    checked: dict[str, list[str]] = field(default_factory=dict)
    skipped: dict[str, list[str]] = field(default_factory=dict)

    def wants(self, location: str, obligation: str) -> bool:
        """Return whether a check is to be made, and record either answer."""
        if obligation in self.skip:
            entries = self.skipped.setdefault(location, [])
            if obligation not in entries:
                entries.append(obligation)
            return False

        entries = self.checked.setdefault(location, [])
        if obligation not in entries:
            entries.append(obligation)
        return True
