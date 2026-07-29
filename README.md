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

Current version: **0.1 (under development)**

The first milestone focuses on the algebraic foundations:

- Polynomial maps
- Composition
- Jacobian matrices
- Stable extensions
- Elementary automorphisms

The BCW reduction algorithm itself will be implemented in later milestones.

---

## Documentation

The documentation is located in

```
docs/
```

Most important documents:

```
architecture.md
roadmap.md
```

---

## License

MIT License
