# BCW Reduction

Implementation of the Bass–Connell–Wright reduction of polynomial Keller maps.

This project implements the degree reduction algorithm introduced by

> H. Bass, E. H. Connell, D. Wright,
> *The Jacobian Conjecture: Reduction of Degree and Formal Expansion of the Inverse*, Bull. Amer. Math. Soc., 1982.

The goal is not priority. Reductions of the July 2026 counterexample have
already been carried out and published by hand. What does not exist is a
reduction that can be **rechecked mechanically, without trusting the pipeline
that produced it**.

Every reduction step is therefore represented explicitly as a mathematical
object carrying its own certificate, and can be verified, documented and
exported. Correctness of a complete reduction follows by induction over
verified steps, so the final result stands independently of how it was found.

The implementation is intended as both

- a research tool for experiments related to the Jacobian Conjecture,
- and a faithful software implementation of the original mathematical proof.

---

## Project Status

Current version: **0.1 (under development)**

The first milestone focuses on the algebraic foundations:

- Polynomial maps
- Composition
- Jacobian matrices
- Degree, order and the `MA^d` filtration
- Stable extensions
- Elementary automorphisms

The BCW reduction algorithm itself will be implemented in later milestones.

---

## Reference Example

The driving example is the counterexample to the Jacobian Conjecture in
dimension 3 announced by Levent Alpöge on 20 July 2026: a polynomial map

    F : C³ → C³

of degree 7 with constant Jacobian determinant -2 that is generically three
to one, and therefore not a polynomial automorphism. The three points

    (0, 0, -1/4),   (1, -3/2, 13/2),   (-1, 3/2, 13/2)

all map to `(-1/4, 0, 0)`. This is kept as a regression test.

Applying the BCW reduction to this map yields a cubic homogeneous
counterexample in higher dimension, which is the first concrete goal of the
project.

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

## Related Work

No open-source implementation of the BCW degree reduction itself is known to
this project. The closest existing code is

```
https://github.com/Adamus-Bogdan/Algorithm-Reduction
```

which implements an algorithm for **inverting** polynomial mappings, including
computations over finite fields. That is a related but different problem: it
inverts a map assumed to be an automorphism, rather than reducing its degree.

---

## License

MIT License
