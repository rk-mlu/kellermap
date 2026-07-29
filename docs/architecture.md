# Software Architecture

## Design Philosophy

The implementation follows the mathematical structure of the proof by
Bass–Connell–Wright rather than viewing the reduction as a purely symbolic
algorithm.

Every mathematical object appearing in the proof is represented by a dedicated
Python class.

The implementation therefore mirrors the mathematical notation as closely as
possible.

---

# High-Level Overview

```
PolynomialMap
        │
        │
        ├──────────────┐
        │              │
        ▼              ▼
Elementary      StableExtension
Automorphism
        │
        ▼
BCWStep
        │
        ▼
BCWHistory
        │
        ▼
BCWReducer
```

---

# Package Structure

```
src/bcw/

    algebra/

        polynomial_map.py
        automorphism.py

    reduction/

        term.py
        factorization.py
        step.py
        reducer.py
        history.py

    verification/

        verify.py

    output/

        latex.py
        pretty.py
```

---

# Core Classes

## PolynomialMap

Represents a polynomial mapping

\[
F : K^n \rightarrow K^m.
\]

Responsibilities

- composition
- Jacobian
- determinant
- degree
- substitution
- stable extension

---

## ElementaryAutomorphism

Represents elementary polynomial automorphisms

\[
x_i
\mapsto
x_i+p(x).
\]

Responsibilities

- construction
- inversion
- verification

---

## Term

Represents one monomial term

\[
aM.
\]

---

## Factorization

Stores

\[
aM=P\,Q.
\]

Responsibilities

- factors
- degree
- verification

---

## BCWStep

Represents exactly one application of Proposition 3.1.

Contains

- original map
- transformed map
- chosen coordinate
- chosen monomial
- factorization
- automorphisms

---

## BCWHistory

Stores an entire reduction.

Responsibilities

- ordered list of BCWStep objects
- verification
- LaTeX export
- pretty printing

---

## BCWReducer

Implements the complete reduction algorithm.

Responsibilities

- selecting terms
- selecting factorizations
- performing BCW steps
- termination

---

# Mathematical Invariants

Every BCWStep preserves

- stable equivalence
- Jacobian determinant
- Keller property

The implementation will provide verification methods for these invariants.

---

# Development Strategy

The implementation proceeds in the following order.

1. Algebra
2. Elementary automorphisms
3. BCW step
4. Complete reduction
5. Verification
6. LaTeX export
7. Optimisation
