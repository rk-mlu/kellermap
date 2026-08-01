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

Unlike a simple symbolic manipulation package, every reduction step *will* be
represented explicitly as a mathematical object and carry its own machine-checkable
certificate. That is the goal of the project; `BCWStep` and `Reduction` arrive in
0.2. Version 0.1 provides the algebraic objects they are built from.

---

## Project Status

Current version: **0.1.0rc4**

The first milestone covers the algebraic foundations:

- Polynomial maps over a sparse `PolyRing`, with value semantics
- Simultaneous composition
- Jacobian matrices and determinants
- Stable extensions, with an injectable variable factory
- Elementary automorphisms and the group `EA_n(k)`

The BCW reduction itself follows in later milestones: `BCWStep` and
`Reduction` in 0.2, the reduction algorithm in 0.3.

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

`docs/api.md` covers the rest; every example in it is executed by the test
suite.

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
references.md     sources, and the provenance of the fixed test data
roadmap.md        milestones
```

---

## License

MIT License
