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

2. **Immutable mathematical objects**

   Public mathematical objects are immutable whenever possible. Internally,
   mutable low-level objects are never shared with callers.

3. **Local verification**

   Every reduction step carries its own proof certificate.

4. **Sparse polynomial arithmetic**

   Polynomial arithmetic is performed in
   `sympy.polys.rings.PolyRing`. General SymPy expressions are restricted to
   the input and output boundary.

5. **Measured optimization**

   Additional arithmetic kernels or external dependencies are considered only
   after reproducible benchmarks show that the PolyRing implementation is
   insufficient.

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
- simultaneous composition
- Jacobian matrix
- Jacobian determinant
- degree and order
- displacement `F - X` and filtration degree
- stable extension

### Public boundary

The constructor accepts

- a tuple or iterable of SymPy `Symbol` objects,
- a tuple or iterable of polynomial SymPy `Expr` objects.

The public properties `variables`, `components`, `matrix`, `jacobian()`, and
`determinant()` expose immutable SymPy objects suitable for inspection,
printing, testing, and LaTeX output.

### Internal representation

Internally a map stores

```
PolyRing
private tuple[PolyElement, ...]
```

The ring is constructed with the map variables as generators. Every other
symbol occurring in a component belongs to the coefficient domain. Thus an
indeterminate `T` in `MA_n(k[T])`, or a symbolic coefficient, does not
contribute to degree or order.

`PolyElement` inherits from `dict` and is mutable. Therefore:

- coordinate polynomials remain private,
- the expression-level constructor copies its internal polynomials,
- `from_ring()` copies all supplied polynomials,
- `to_polynomials()` returns defensive copies.

This preserves the value semantics of the frozen `PolynomialMap` class.

### Composition

For maps over the same ring, composition uses the simultaneous multivariate
substitution implemented by `PolyElement.compose()`.

If two maps have the same generators but compatible, different coefficient
domains, they are first coerced into a common `PolyRing`. The usual reduction
pipeline should keep all related maps in one ring so that this fallback remains
exceptional.

### Jacobian and determinant

Partial derivatives are computed directly on sparse `PolyElement` objects.
The public Jacobian is converted to an expression-valued SymPy matrix only at
the output boundary.

The determinant is computed by a `DomainMatrix` over the polynomial-ring
domain. It must not be computed by first expanding a general expression-valued
matrix.

### Degree and order

Degree and order are obtained directly from exponent tuples in the sparse
monomial support:

- `degree()` is the largest total degree,
- `order()` is the smallest occurring total degree,
- the zero map has degree `0` and order `math.inf`.

---

## ElementaryAutomorphism

Represents an elementary polynomial automorphism.

Responsibilities:

- evaluation
- inverse
- composition
- conversion to `PolynomialMap`

Every elementary automorphism must be explicitly invertible and must use the
same `PolyRing` context as the map on which it acts.

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

The fundamental certificate object of the project.

A BCW step stores

- the original map,
- the transformed map,
- the left elementary automorphism,
- the right elementary automorphism,
- the number of stabilization variables,
- the required filtration levels.

It certifies the identity

    F' = G ∘ F[m] ∘ H.

The method

```
verify()
```

checks

- the polynomial identity in the common `PolyRing`,
- invertibility of `G` and `H`,
- the required filtration levels,
- equality of Jacobian determinants as a consistency check.

The determinant equality is not an independent proof obligation: elementary
automorphisms have determinant one. It is retained because it catches
implementation errors early when it is computationally cheap.

A verified `BCWStep` is a complete proof certificate for one local
transformation.

---

## Reduction

Represents a complete BCW reduction.

Internally

```
steps: list[BCWStep]
```

Verification consists of checking every step and the adjacency of consecutive
maps. The mathematical correctness of the whole reduction follows by induction
from the local certificates.

---

## Variable Management

Stable extensions introduce fresh generators and therefore create a new
`PolyRing` containing the old generators and the new identity coordinates.
Existing coordinate polynomials are transferred into the enlarged ring without
passing through general expressions.

Version 0.1 creates deterministic names while avoiding collisions with

- existing ring generators,
- symbols in the coefficient domain.

Version 0.2 delegates this responsibility to a dedicated

```
VariableFactory
```

or `ReductionContext`, ensuring reproducible names over complete reduction
sequences.

---

## Polynomial Arithmetic Strategy

`PolyRing` is the canonical polynomial representation of the project.
`Expr` is not an alternative computational backend; it is an interchange and
presentation format.

The core operations are implemented as follows:

| Operation | PolyRing primitive |
| --- | --- |
| addition and multiplication | `PolyElement` arithmetic |
| simultaneous composition | `PolyElement.compose()` |
| partial derivative | `PolyElement.diff()` |
| degree and order | iteration over exponent tuples |
| homogeneous parts | monomial support filtering |
| Jacobian determinant | `DomainMatrix` over `PolyRing.to_domain()` |
| conversion to output | `PolyElement.as_expr()` |

Potential future accelerators include python-flint or Singular. They are not
planned as parallel public backends. They may be introduced behind the same
polynomial-ring semantics only if benchmarks demonstrate a compelling need.

---

## Testing Strategy

Testing is divided into four levels.

### Unit tests

Verify individual mathematical objects and backend invariants.

Examples:

- `PolynomialMap`
- `ElementaryAutomorphism`
- `BCWStep`
- simultaneous composition
- coefficient-domain handling
- defensive copying of mutable `PolyElement` objects

### Cross-representation tests

For small examples, compare PolyRing results with independently computed SymPy
expressions. These tests guard the conversion boundary and the custom
integration with `DomainMatrix`.

### Integration tests

Verify complete reduction sequences and their certificates.

### Regression and benchmark tests

Known examples from the literature are preserved to guarantee that future
optimizations never change mathematical correctness.

The current small regression example checks a degree-seven map in dimension
three by asserting both its constant Jacobian determinant and an explicit
collision. The cubic Keller map in 19 variables described at
`https://rhicksrad.github.io/jacobian-degree3/` is the first performance
reference for sparse Jacobian and determinant computations.

Correctness tests and performance benchmarks remain separate: timing thresholds
must not make the unit test suite machine-dependent.

---

## Performance

Performance work follows three rules.

1. Benchmark complete BCW-relevant operations, not isolated micro-operations
   alone.
2. Keep conversion between `Expr` and `PolyElement` outside timed inner loops.
3. Avoid recomputing invariants that follow from verified elementary
   transformations.

The initial benchmark suite measures

- construction from expressions,
- composition,
- Jacobian construction,
- determinant computation,
- degree and order,
- stable extension,
- verification of a complete BCW step.

Results from the former expression implementation are retained as a baseline.
