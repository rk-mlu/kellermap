# KellerMap

A Python library for polynomial Keller maps — polynomial endomorphisms with a
nonzero constant Jacobian determinant — and for certified transformations of
them.

Whether every Keller map is an automorphism was the Jacobian conjecture, posed
by Ott-Heinrich Keller in 1939 — or, on a recent reading of the sources, by
Ludwig Kraus in 1884; see `docs/references.md`. It stood until July 2026 and is
now known to be false in every dimension `n >= 3`. The maps this library is
built to handle are therefore precisely those that need not be invertible,
which is why it is named after them rather than after automorphisms.

There is a local coincidence in that name. Keller held the second chair of
mathematics at the Martin-Luther-Universität Halle-Wittenberg from 1952 until
his retirement in 1971, succeeding Heinrich W. E. Jung, and he lectured there
into the 1980s — the present-day academic home of this project.

The first goal is the degree reduction introduced by

> H. Bass, E. H. Connell, D. Wright,
> *The Jacobian Conjecture: Reduction of Degree and Formal Expansion of the Inverse*,
> Bull. Amer. Math. Soc., 1982.

The implementation is intended as both

- a research tool for experiments related to the Jacobian Conjecture,
- and a faithful software implementation of the original mathematical proof.

Unlike a simple symbolic manipulation package, every reduction step is
represented explicitly as a mathematical object and carries its own
machine-checkable certificate. Since 0.2 that is no longer a promise: the
seventeen-dimensional cubic counterexample in the test suite is *derived* from
Alpöge's map by a chain of eight verified steps, which carries the collision
along with it.

---

## Project Status

Current version: **0.2.0rc1**

The first milestone covered the algebraic foundations:

- Polynomial maps over a sparse `PolyRing`, with value semantics
- Simultaneous composition
- Jacobian matrices and determinants
- Stable extensions, with an injectable variable factory
- Elementary automorphisms and the group `EA_n(k)`

The second adds the verification framework:

- `Collision`, the evidence that a map is not injective, carried across steps
- The group `GL_n(k)` as an ordered product of Gauss operations, and why only
  its transvections are elementary in the sense of the paper
- `BCWStep`, one certified application of Proposition (3.1)
- `Reduction`, a chain of steps with its adjacency checked
- `ReductionContext`, which holds a naming policy to its word across a chain
- Every obligation stated normatively in `docs/contracts.md`, one numbered
  identifier at a time, and cited by the exception when it fails

Searching for a reduction rather than verifying a presented one is 0.3.

---

## Installation

```
pip install kellermap
```

Requires Python 3.10 or newer and SymPy 1.14 or newer.

## Quick start

```python
import sympy as sp
from kellermap import PolynomialMap

x, y = sp.symbols("x y")
F = PolynomialMap((x, y), (x + y**3, y))

F.determinant()  # 1 — a Keller map
F.degree()  # 3
F.filtration_degree()  # 2, from ord(F - X) = 3
F.extend(2).variables  # (x, y, X3, X4)
```

The first two steps of the reduction that this library exists for — Alpöge's
counterexample to the Jacobian conjecture, on its way down to degree three:

```python
import sympy as sp
from kellermap import Collision, PolynomialMap, Reduction, ReductionContext
from kellermap import over_field
from kellermap.bcw import BCWStep
from kellermap.reduction import LinearStep

x1, x2, x3 = sp.symbols("x1 x2 x3")
R = sp.Rational

alpoege = over_field(
    PolynomialMap(
        (x1, x2, x3),
        (
            (1 + x1 * x2) ** 3 * x3 + x2**2 * (1 + x1 * x2) * (4 + 3 * x1 * x2),
            x2 + 3 * x1 * (1 + x1 * x2) ** 2 * x3 + 3 * x1 * x2**2 * (4 + 3 * x1 * x2),
            2 * x1 - 3 * x1**2 * x2 - x1**3 * x3,
        ),
    )
)
collision = Collision.at(
    alpoege,
    (
        (0, 0, R(-1, 4)),
        (1, R(-3, 2), R(13, 2)),
        (-1, R(3, 2), R(13, 2)),
    ),
)

normalization = LinearStep.normalize(alpoege)  # F'' = F'_(1)^-1 o F', BCW §4
first = BCWStep.build(  # Proposition (3.1): two dimensions bought
    normalization.target,
    0,
    -x1 * x3 / 2,
    x1**2,
    ReductionContext().variables(normalization.target.ring, 2),
)
reduction = Reduction([normalization, first])

reduction.verify()  # None, or VerificationError naming the obligation that failed
reduction.dimensions()  # (3, 3, 5)
reduction.transport(collision).points[1]  # (1, -3/2, 13/2, 13/4, -1)
```

The counterexample is still a counterexample at the other end, and the chain
says so by carrying it rather than by asserting it.

`docs/api.md` covers the rest; every example in it is executed by the test
suite, as are both blocks above.

---

## Documentation

The documentation is located in

```
docs/
```

Most important documents:

```
api.md            public API, with examples the test suite executes
architecture.md   design decisions and the reasons for them
contracts.md      binding obligations of the verification surface
references.md     sources, and the provenance of the fixed test data
roadmap.md        milestones
```

---

## License

MIT License
