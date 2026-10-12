"""Fixtures shared by more than one test module.

Thompson's twenty-four-variable map is compressed to twenty variables and
lifted to forty in three modules: ``test_compression.py`` checks the
compression, ``test_lift.py`` the published form of the lift, and
``test_vanishing.py`` the witness built on it. The compression is the
expensive part, and each module built it again. The profile taken when
milestone 0.9 opened found it computed three times in the fast suite; it is
now computed once per session.

The objects are values. ``PolynomialMap`` and the steps are immutable and
compare by value, so a module that receives the shared step cannot change what
another module sees. ``test_compression.py`` checks that verification is
idempotent on this very object.
"""

from __future__ import annotations

import pytest

from kellermap import (
    CompressionStep,
    SymmetricLiftStep,
    examples,
    over_field,
)


@pytest.fixture(scope="session")
def thompson_compressed() -> CompressionStep:
    """Return Thompson's map compressed along its collision, 20 variables."""
    return CompressionStep.build(
        over_field(examples.thompson24_homogeneous()),
        examples.thompson24_homogeneous_collision(),
    )


@pytest.fixture(scope="session")
def thompson_lift(thompson_compressed: CompressionStep) -> SymmetricLiftStep:
    """Return the symmetric lift of that compression, 40 variables."""
    return SymmetricLiftStep.build(thompson_compressed.target)
