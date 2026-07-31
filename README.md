# BCW Reduction

Implementation of the Bass–Connell–Wright reduction of polynomial Keller maps.

This project aims to provide the first open-source implementation of the degree
reduction algorithm introduced by

> H. Bass, E. H. Connell, D. Wright,
> *The Jacobian Conjecture: Reduction of Degree and Formal Expansion of the Inverse*, Bull. Amer. Math. Soc., 1982.

The implementation is intended as both

- a research tool for experiments related to the Jacobian Conjecture,
- and a faithful software implementation of the original mathematical proof.

Unlike a simple symbolic manipulation package, every reduction step is
represented explicitly as a mathematical object and can be verified, documented
and exported.

---

## Project Status

Current version: **0.1.0rc1**

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
roadmap.md        milestones
```

---

## License

MIT License
