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
- degree
- stable extension

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

---

## Performance

Performance optimizations must never affect correctness.

Optimizations should be confined to the polynomial backend so that the public
API remains stable.
