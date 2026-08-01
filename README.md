# KellerMap

A Python library for polynomial Keller maps — polynomial endomorphisms with a
nonzero constant Jacobian determinant — and for certified transformations of
them.

KellerMap is named after Ott-Heinrich Keller, whose work gave rise to the notion
of Keller maps and who served as a professor at the Martin-Luther-Universität 
Halle-Wittenberg—the present-day academic home of this project.

Whether every Keller map is an automorphism was the Jacobian conjecture, open
from 1939 (or 1884, see `docs/references.md`) until July 2026. It is now known
to be false for every dimension `n >= 3`. The maps this library is built to
handle are therefore exactly the ones that need not be invertible, which is why
it is named after them rather than after automorphisms.

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

Current version: **0.1.0rc2**

The first milestone covers the algebraic foundations:

- Polynomial maps over a sparse `PolyRing`, with value semantics
- Simultaneous composition
- Jacobian matrices and determinants
- Stable extensions, with an injectable variable factory
- Elementary automorphisms and the group `EA_n(k)`

The BCW reduction itself follows in later milestones: `BCWStep` and
`Reduction` in 0.2, the reduction algorithm in 0.3.

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
