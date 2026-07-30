# Architecture

## Overview

The goal of **bcw** is to construct and verify Bass–Connell–Wright (BCW)
reductions of polynomial maps with constant Jacobian determinant.

The central design principle is that every reduction step produces a
**machine-verifiable certificate**.

Rather than proving correctness globally, the reduction is decomposed into
independent local transformations. Each transformation is verified by checking
explicit polynomial identities. The correctness of a complete reduction follows
immediately by induction over the sequence of verified steps.

---

## Design Principles

The implementation follows five guiding principles.

1. **Mathematical correctness**

   Every transformation must preserve the mathematical meaning of the map.
   Verification has higher priority than execution speed.

2. **Immutable objects**

   Mathematical objects are immutable whenever possible.

3. **Local verification**

   Every reduction step carries its own proof certificate.

4. **Backend independence**

   The public API must not depend on the internal polynomial representation.

5. **Extensibility**

   New reduction strategies and polynomial backends should be easy to add.

---

## Main Objects

```
PolynomialMap
        │
        │
ElementaryAutomorphism
        │
        │
      BCWStep
        │
        │
     Reduction
```

---

## PolynomialMap

Represents a polynomial map

    F : Kⁿ → Kⁿ

Version 0.1 intentionally models polynomial endomorphisms.

Future versions may generalize this to arbitrary polynomial maps

    Kⁿ → Kᵐ.

Responsibilities:

- evaluation
- composition
- Jacobian matrix
- Jacobian determinant
- degree and order
- displacement `F - X` and filtration degree
- stable extension

Degree and order are always taken with respect to the map's own variables.
A symbol that is not one of them — an indeterminate `T` as in `MA_n(k[T])`, or
a symbolic coefficient — belongs to the coefficient domain and must not
contribute. Section 4 of BCW depends on this distinction.

The public interface is independent of the internal polynomial
representation.

---

## ElementaryAutomorphism

Represents an elementary polynomial automorphism.

Responsibilities:

- evaluation
- inverse
- composition

Every elementary automorphism must be explicitly invertible.

---

## Filtration

Bass–Connell–Wright filter the monoid by the order of the displacement:

    F ∈ MA^d_n(k)   ⟺   ord(F - X) > d

and put

    EA^d_n(k) = EA_n(k) ∩ MA^d_n(k).

The distinction is not cosmetic. Proposition (3.1) places `G` and `H` in
`EA^1` during degree reduction, but only in `EA^0` once `H` is allowed to make
`F'` linear in each variable, because the factorization `aM = PQ` may then
produce a linear `P`. Section 4 correspondingly uses `G(T), H(T)` in
`EA^0_2n(k[T])`.

A reduction step must therefore record which filtration level it establishes,
not merely that its elementary factors are invertible.

`PolynomialMap` exposes this as

```
order()
displacement()
filtration_degree()
is_in_MA(d)
```

where `filtration_degree()` is `ord(F - X) - 1`, so that the identity lies in
every `MA^d`.

---

## BCWStep

The fundamental building block of the project.

A BCW step stores

- the original map
- the transformed map
- the left elementary automorphism
- the right elementary automorphism

such that

    F' = G ∘ F[m] ∘ H

holds.

The class provides

```
verify()
```

which checks

- the polynomial identity
- equality of Jacobian determinants
- invertibility of G and H
- the filtration level of G and H, as the step requires

The determinant check is a cheap consistency check rather than an independent
condition: elementary automorphisms have Jacobian determinant 1, so equality
follows from the other checks. It is kept because it is nearly free and
catches implementation errors early.

A verified BCWStep is considered a complete proof certificate for one
reduction step.

---

## Reduction

Represents a complete BCW reduction.

Internally

```
steps : list[BCWStep]
```

Verification consists simply of

```
all(step.verify() for step in steps)
```

The mathematical correctness of the whole reduction follows immediately from
the correctness of every individual step.

---

## Variable Management

Stable extensions introduce fresh variables.

Variable creation is delegated to a dedicated

```
VariableFactory
```

(or a future ReductionContext)

to guarantee globally unique variable names during long reduction sequences.

---

## Polynomial Backend

The public API deliberately hides the concrete polynomial representation.

Version 0.1 uses SymPy expressions.

Future implementations may use

- sympy.polys.rings
- python-flint
- Singular

without changing the public interface.

---

## Testing Strategy

Testing is divided into three levels.

### Unit tests

Verify individual mathematical objects.

Examples:

- PolynomialMap
- ElementaryAutomorphism
- BCWStep

### Integration tests

Verify complete reduction sequences.

### Regression tests

Known benchmark examples from the literature are preserved to guarantee that
future optimizations never change mathematical correctness.

The current benchmark is Alpöge's counterexample to the Jacobian Conjecture
(dimension 3, degree 7, announced July 2026). The regression test asserts the
two properties that carry mathematical content:

- the Jacobian determinant is constant and invertible, so the map is Keller,
- three pairwise distinct rational points share an image, so the map is not
  injective and therefore not an automorphism.

Dimension and degree are checked separately as characteristic numbers. They
are not evidence: a test asserting only degree 7 and determinant -2 would pass
for a tame automorphism as well and would prove nothing about the example.

---

## Performance

Performance optimizations must never affect correctness.

Optimizations should be confined to the polynomial backend so that the public
API remains stable.
