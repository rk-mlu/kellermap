# Roadmap

The project follows an incremental development strategy.
Every milestone should leave the repository in a fully functional and tested
state.

---

# Version 0.1

## Core mathematical objects

- PolynomialMap
- ElementaryAutomorphism

### Features

- evaluation
- composition
- Jacobian
- determinant
- degree
- stable extension

### Quality

- complete unit tests
- mypy
- ruff
- black
- documentation

---

# Version 0.2

## Verification framework

Introduce

- BCWStep
- Reduction
- VariableFactory

Implement

```
BCWStep.verify()
```

Verification checks

- polynomial identity

      F' = G ∘ F[m] ∘ H

- equality of Jacobian determinants

- invertibility of elementary automorphisms

At this point the project can already produce machine-verifiable proof
certificates.

---

# Version 0.3

## BCW reduction

Implement

- degree reduction
- elementary transformations
- stable extension
- complete reduction pipeline

Goal:

Produce verified reductions for examples from the literature.

---

# Version 0.4

## Reduction heuristics

Develop heuristics for selecting reduction steps.

Tasks

- candidate generation
- ranking heuristics
- search strategies
- pruning

Benchmark against the current reference instance
(currently dimension 39).

This milestone targets scientific improvements rather than software features.

---

# Version 0.5

## Polynomial backend

Introduce an abstraction layer for polynomial arithmetic.

Initially support

- SymPy expressions

Evaluate alternative implementations

- sympy.polys.rings
- python-flint
- Singular

The public API must remain unchanged.

---

# Version 0.6

## Complete verification framework

Large-scale regression tests.

Benchmark suite.

Performance evaluation.

Verified reduction certificates for large examples.

---

# Version 0.7

## User experience

History management.

LaTeX export.

Visualization.

Command-line improvements.

Documentation.

---

# Long-term Goals

- dimensions well beyond the current benchmark
- interchangeable polynomial backends
- reproducible reduction certificates
- publishable benchmark results
- automated verification of complete BCW reductions
