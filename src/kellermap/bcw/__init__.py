"""Bass-Connell-Wright-specific machinery.

``BCW`` always means the 1982 paper. What is not specific to it -- the maps,
the group ``EA_n(k)``, collisions, and chains of certified identities -- lives
at the top level of the package.
"""

from .homogenization import HomogenizationStep
from .step import BCWStep, Carried, Factor, Fresh
from .unipotent import UnipotentStep

__all__ = [
    "BCWStep",
    "Carried",
    "Factor",
    "Fresh",
    "HomogenizationStep",
    "UnipotentStep",
]
