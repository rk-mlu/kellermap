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
PolynomialMap  ←──uses──  VariableFactory
        │
        │
ElementaryFactor ──► ElementaryAutomorphism
        │
        │
      BCWStep
        │
        │
     Reduction
```

`VariableFactory` sits beside the tower rather than in it: it is a naming
policy, not a mathematical object, and every level that extends a map passes
one down.

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

`matrix` and `jacobian()` return `sp.ImmutableMatrix`. For `matrix` this is
load-bearing rather than decorative: the property is cached, so a mutable
matrix would let a caller alter the value of every subsequent evaluation
while `components` still reported the original map. `sp.Matrix(F.matrix)`
gives a mutable copy where one is wanted.

Generators must have pairwise distinct *names*, not merely be distinct
symbols. Two `Symbol` objects with different assumptions compare unequal but
print identically, and `PolyRing` accepts both, yielding two generators that
no expression can tell apart. Both constructors reject this.

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

`PolyElement` inherits from `dict` and is mutable, and so is a coefficient
that is itself a `PolyElement` — over `k[T]` the copy must therefore descend
recursively, not stop at the top level. Therefore:

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

The determinant must not be computed by first expanding a general
expression-valued matrix. Two strategies operate on the sparse representation.

`carrier_indices()` reports the coordinates spanning a unipotent block of the
Jacobian: those with `dF_i/dX_i = 1` whose mutual dependencies are acyclic.
Stable extensions, elementary automorphisms and BCW-reduced maps produce this
shape by construction. Writing the Jacobian as

    | A  B |
    | C  D |,      D = I + L,  L nilpotent

gives `det J = det(D) det(A - B D^-1 C) = det(A - B D^-1 C)`, so an `n x n`
determinant becomes one of size `n - len(carrier)`. Only `D^-1 C` is formed,
through the Neumann series `sum_k (-L)^k C`, never `D^-1` itself. In dimension
17 this takes the determinant computation from roughly a minute to under ten
milliseconds; an elementary automorphism is unipotent throughout, so its
determinant is one by structure rather than by expansion.

Unipotence is decided on the dependency graph rather than by taking powers,
and it is verified rather than inherited. Termination of the Neumann series is
not evidence for it: with an empty head block the series terminates whatever
`L` is, and the empty Schur complement would then report determinant one for
an arbitrary map.

Otherwise a `DomainMatrix` over the polynomial-ring domain computes the
determinant. That path remains the reference against which the optimized one
is cross-checked.

### Degree and order

Degree and order are obtained directly from exponent tuples in the sparse
monomial support:

- `degree()` is the largest total degree,
- `order()` is the smallest occurring total degree,
- the zero map has degree `0` and order `math.inf`.

Neither is preserved by stable extension. The added coordinates `X_{n+i}` are
monomials of degree exactly one, so for `m > 0`

    deg(F^[m]) = max(deg F, 1),      ord(F^[m]) = min(ord F, 1).

What survives is the displacement: `F^[m] - X` differs from `F - X` by zero
components only, so its degree and order — and therefore the filtration
degree — are unchanged. That is the invariant BCW actually relies on, and the
one a reduction step must record.

---

## ElementaryAutomorphism

Two objects, because `EA_n(k)` is a group and its generators are not closed
under composition.

`ElementaryFactor` is a generator: the map fixing every coordinate but one,

    X_i  |-->  a X_i + P,

with `a` a unit of the coefficient domain and `P` free of `X_i`. Both
conditions carry the inverse, which is then a formula rather than a solved
equation,

    X_i  |-->  a^-1 (X_i - P),

with `P` unchanged under the substitution precisely because it does not
involve `X_i`. Both are enforced at construction.

`ElementaryAutomorphism` is an element of `EA_n(k)`, stored as the ordered
product `f_1 o ... o f_k` of the factors that build it, with the empty product
as the identity. Composition concatenates, inversion reverses and inverts.
Proposition (3.1) needs this: its `G` is a single factor, its `H` is a product
of two.

Responsibilities:

- evaluation
- inverse
- composition
- conversion to `PolynomialMap`
- filtration level, since the proposition places its factors in `EA^1` or
  `EA^0` and a step must record which

Every factor uses the `PolyRing` context of the maps it acts on; mismatches
are rejected rather than coerced.

### The factorization is kept

The product is not multiplied out. Two different factorizations of the same
automorphism are different objects and compare unequal, even though their
`PolynomialMap`s agree. This is deliberate. "Invertible" is a claim; "here are
the generators and their inverses" is a proof, and a certificate has to
exhibit the factorization it used.

### What is structural and what is not

The Jacobian determinant of a factor is `a`, and of a product the product of
the coefficients — no polynomial arithmetic at all. This is what allows
`BCWStep.verify()` to check determinants at every step.

The filtration level is *not* structural. Factors in `EA^0` can multiply to
something in `EA^1`: `X_1 |-> X_1 + X_2` composed with `X_1 |-> X_1 - X_2` is
the identity, which lies in every `EA^d`. `MA^d` being a submonoid gives a
lower bound only, so `ElementaryAutomorphism.filtration_degree()` forms the
map.

### Applying a factor

`apply_to()` composes a factor with a map on the left. Only one coordinate
changes, so one polynomial composition suffices where a full map composition
would perform `n`. This is the reason the class exists rather than everything
being a `PolynomialMap`, and it is checked against `PolynomialMap.compose()`
in the tests.

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
implementation errors early when it is computationally cheap -- which the
unipotent-block strategy makes it, precisely for the maps a reduction
produces.

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

Naming those generators is isolated in `bcw.variables` as a

```
VariableFactory
```

a callable taking a ring and a count and returning that many symbols.
`PolynomialMap.extend()` accepts one; omitting it uses
`DEFAULT_VARIABLE_FACTORY`.

### Purity is a correctness requirement

**A factory must be a pure function of its arguments.** Two calls with the
same ring and count must return the same names, and no call may influence a
later one.

This follows from stable extension being a monoid homomorphism,

    (F o G)^[m] = F^[m] o G^[m],

whose two sides reach `extend()` through three separate calls. A factory that
counted upwards would name the sides differently and break the identity
*silently*: both sides remain perfectly valid polynomial maps, so nothing
raises, and only a structural comparison notices.

The requirement is why `IndexedVariableFactory` is a frozen dataclass without
state. It is also the constraint a `ReductionContext` inherits: anything that
must remember something across calls belongs there, and the context is then
responsible for handing the *same* factory to every side of such an identity.

### Extending twice must equal extending once

Stable extension composes,

    (F^[m])^[l] = F^[m+l],

so an extension of size `m` followed by one of size `l` must allocate exactly
the names a single extension of size `m + l` would, in that order. A reduction
stabilizes step by step and must land where one stabilization lands.

This does *not* follow from purity, and the two requirements are stated
separately for that reason. A factory naming its output after the size of the
ring it was handed — `g2_1, g2_2` for a two-generator ring — is pure and never
collides, so `extend()` finds nothing to object to, yet

    (F^[2])^[2] -> g2_1, g2_2, g4_1, g4_2
    F^[4]       -> g2_1, g2_2, g2_3, g2_4.

Names must be drawn from a sequence determined by the ring alone, with the
count deciding only how far along it to walk, never entering the name.

### Naming convention

`IndexedVariableFactory` produces `prefix1, prefix2, ...`, skipping names
already taken. Given no explicit prefix, it reads the convention off the
existing generators: a ring generated by `x1, ..., x17` extends by `x18, x19`,
not by `X18, X19`. A reduction composes many extensions, and a map whose
coordinates follow two competing schemes is needlessly hard to read against
the paper. Generators carrying no such convention — `x, y` — fall back to the
prefix `X`, which is the behaviour that predates the factory.

### Collision avoidance

`reserved_names()` reports the names a fresh generator must not take:
generators of the ring, and symbols of the coefficient domain. An
indeterminate `T` in `MA_n(k[T])` is not a generator, but reusing its name
would still collapse two distinct objects.

Avoiding collisions is the factory's responsibility, and `extend()` rechecks
the result rather than trusting it — count, type, pairwise distinctness, and
disjointness from the reserved names. This is the one validation in the class
that guards against silence rather than against an error: `PolyRing.clone()`
accepts a duplicated generator name and yields a ring in which two coordinates
denote the same generator.

### Scope

`VariableFactory` covers naming and nothing else. `ReductionContext`, which
keeps names reproducible across a complete reduction sequence, belongs to 0.2,
where the objects that determine its requirements are built.

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
| Jacobian determinant, unipotent block | Schur complement, Neumann series on `PolyElement` |
| Jacobian determinant, general case | `DomainMatrix` over `PolyRing.to_domain()` |
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
- `VariableFactory`
- `ElementaryAutomorphism`
- `BCWStep`
- simultaneous composition
- coefficient-domain handling
- defensive copying of mutable `PolyElement` objects
- purity and composition of variable factories, and the validation `extend()`
  performs on them
- rejection of empty input and of malformed rings passed to `from_ring()`
- recursive defensive copying where a coefficient is itself a polynomial

### Cross-representation tests

For small examples, compare PolyRing results with independently computed SymPy
expressions. These tests guard the conversion boundary and the custom
integration with `DomainMatrix`.

### Integration tests

Verify complete reduction sequences and their certificates.

### Regression and benchmark tests

Known examples from the literature are preserved to guarantee that future
optimizations never change mathematical correctness.

Two regression examples are kept. The small one checks a degree-seven map in
dimension three by asserting both its constant Jacobian determinant and an
explicit collision. The larger one is a BCW reduction of that map to a cubic
Keller map in dimension 17, with the collision carried along; its components
are fixed input, not output of this library, until `BCWStep` can reproduce
them.

A separate cubic Keller map in 19 variables is described at
`https://rhicksrad.github.io/jacobian-degree3/`. It arises from a different
reduction of the same degree-seven map -- dimension 19, determinant -2 -- and
serves as a performance reference, not as a regression against the dimension-17
example.

Checks whose runtime is measured in minutes carry the `slow` pytest marker and
are deselected by default. The marker records duration, not a timing threshold,
so the suite stays machine-independent.

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
