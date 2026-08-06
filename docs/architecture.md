# Architecture

## Overview

The goal of **kellermap** is to construct and verify Bass–Connell–Wright (BCW)
reductions of polynomial maps with constant Jacobian determinant.

The central design principle is that every reduction step produces a
**machine-verifiable certificate**.

Rather than proving correctness globally, the reduction is decomposed into
independent local transformations. Each transformation is verified by checking
explicit polynomial identities. The correctness of a complete reduction follows
immediately by induction over the sequence of verified steps.

This page explains why the design is what it is. What the verification surface
is *required* to guarantee is stated normatively in `contracts.md`, one
numbered obligation at a time; where the two disagree, `contracts.md` governs.

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

## Package layout

```
kellermap/
├── polynomial_map.py     PolynomialMap
├── elementary.py         ElementaryFactor, ElementaryAutomorphism
├── linear.py             Transvection, Transposition, Dilation,
│                         LinearAutomorphism, over_field
├── collision.py          Collision
├── reduction.py          Step, LinearStep, Reduction, Provenance
├── context.py            ReductionContext
├── variables.py          VariableFactory, IndexedVariableFactory,
│                         FixedVariableFactory
├── errors.py             VerificationError
└── bcw/                  BCWStep
```

The top level holds what any work on Keller maps needs: the maps themselves,
the group `EA_n(k)` acting on them, the group `GL_n(k)` beside it, collisions,
chains of certified identities, and the naming of fresh generators. None of it
is specific to one reduction method.

Only `BCWStep` is. A chain of certified identities is not a notion of the 1982
paper, and a second reduction method would reuse `Reduction`, `Collision` and
`ReductionContext` unchanged — which is exactly the misnomer the subpackage
exists to avoid. `LinearStep` composes an element of `GL_n(k)` on the left;
that Chapter II, Proposition (1.1) of the paper does so does not make the
operation theirs.

Keeping the subpackage one level down also removes an ambiguity the code
carried while the package itself was called `bcw`: `BCW` now always means the
1982 paper.

## Main Objects

```
PolynomialMap  ←──uses──  VariableFactory  ←──holds──  ReductionContext
        │
        ├── ElementaryFactor ──► ElementaryAutomorphism ──┐
        │                                                 │
        └── LinearFactor ──► LinearAutomorphism ──┐       │
                                                  │       │
                                            LinearStep  BCWStep
                                                  │       │
                                                  └───┬───┘
                                                      │
                                                   Step (protocol)
                                                      │
                                                  Reduction  ←──carries──  Collision
```

`VariableFactory` stands beside this hierarchy rather than in it. It is a
naming policy, not a mathematical object, and every level that extends a map
passes one down. `ReductionContext` checks that a factory keeps the promises
its protocol makes, across a whole chain.

`Collision` also stands beside the hierarchy. It holds no map, because the same
points are a collision of every map that identifies them, and a reduction
verifies them against each map of a chain in turn.

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

The public properties `variables`, `components`, `matrix`, `jacobian()` and
`determinant()` expose immutable SymPy objects suitable for inspection,
printing, testing and LaTeX output.

Two members cross into the sparse representation rather than staying at the
expression boundary, and are public because internal algorithms and callers
building on them need the fast path: `ring` and `to_polynomials()`. Both are
covered by the cloning rule below.

`docs/api.md` is the reference for the whole surface; its examples are
executed by the test suite.

The package ships a `py.typed` marker. Without it the annotations stop at
the project boundary: a consumer running mypy sees every member of `kellermap`
as `Any`, however strictly the project checks itself. Members typed in
terms of SymPy stay `Any` downstream regardless, since SymPy ships no
type information.

### The ring is cloned, not shared

`PolyRing` is not a value object. Its `gens` are `PolyElement` instances and
therefore mutable dicts, and SymPy reads them in `from_expr` and `ring_new`.
A map that handed out its internal ring would let a caller change what it
computes: `F.ring.gens[0].clear()` altered `F.displacement()` while
`F.components` still reported the original map.

Every value object therefore clones the ring it is given and never hands out
the one it computes with. Four paths carry it:

- `from_ring()` clones the caller's ring and rebinds the components onto the
  clone,
- `ring` returns a further clone,
- `to_polynomials()` binds its copies to that clone, since a `PolyElement`
  carries a reference to its ring,
- `extend()` passes the clone to the variable factory.

The clone is built fresh on every access to `ring`, and once per call to
`to_polynomials()`. Caching it would defeat the purpose: all callers would
share one clone, and the first to mutate it would corrupt what every later
caller sees. Cloning costs microseconds even in dimension 17.

Cloning covers the coefficient domain, recursively. A composite domain owns
mutable generators just as a ring does, and domains nest — `QQ[X3][S]` carries
such state at two levels. Sharing the domain left the ring consulting a
caller's object: after `caller_domain.gens[0].clear()` the supposedly isolated
ring converted `T*u` to `0`. Coefficients are rebound onto the cloned domain,
since a `PolyElement` or `FracElement` carries a reference to its own ring or
field.

The same nesting matters for naming. `reserved_names()` walks the whole domain
chain, not just its top level: over `QQ[X3][S]`, reading `domain.symbols` alone
finds `S` and misses `X3` — enough for a stable extension to hand out a
coordinate named `X3` and collapse it with the parameter. `validate_ring()`
rejects that collision up front, which SymPy itself only does for the top
level.

Both constructors run that check. The expression constructor did not, and
`sring` will place a symbol that is already a generator into the coefficient
domain as well when it appears with different assumptions — same name,
different objects. The result was a map that looked valid, printed one glyph
for two things in `components`, and failed only later in `extend()`.

Cloning must not go through `PolyRing.clone()`. That method is memoised by
SymPy's `cacheit`, and cloning a ring that is *itself* a clone returns the
same object. Isolation built on it does nothing for any map produced by
`from_ring()` — which is every result of `compose()` and `extend()` — while
still passing a test that only exercises the expression constructor.
`clone_ring()` constructs a `PolyRing` directly instead.

Rebinding likewise cannot go through `PolyElement.set_ring()`, which
short-circuits on value-equal rings and returns the original. `copy_polynomial()`
takes the target ring and rebuilds through `from_terms()`.

The clones are value-equal, so they compose, compare and coerce
interchangeably with the internal ring, and remain usable as arguments to
`from_ring()`, `ElementaryFactor` and a `VariableFactory`.

### Matrices

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

`ElementaryFactor` is a generator, in the sense of BCW p. 304: `F` in
`MA_n(k)` is elementary if for some `j` the difference `F_i - X_i` vanishes
for `i != j` and is independent of `X_j` for `i = j`. So

    X_j  |-->  X_j + P,      P free of X_j,

with no coefficient on `X_j`. The paper draws the inverse straight from the
definition, `(F^-1)_i - X_i = -(F_i - X_i)`:

    X_j  |-->  X_j - P,

where `P` survives the substitution unchanged precisely because it does not
involve `X_j`. The condition on `P` is enforced at construction.

A scaling `X_j |-> a X_j + P` with `a != 1` is a polynomial automorphism but
not an elementary one: its displacement `(a - 1) X_j` depends on `X_j`.
Admitting it would put elements of determinant other than one into
`EA_n(k)` — and the argument that a reduction step preserves the Jacobian
determinant rests on every element of `EA_n(k)` having determinant one.
Scalings belong to the linear part, which Proposition (1.1) separates; if
they are needed they get their own type rather than a parameter here.

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

The Jacobian determinant of a factor is one, and hence so is that of any
product: the Jacobian is the identity except for row `j`, whose off-diagonal
entries are the partials of `P` and whose diagonal entry is one. This is a
theorem, not a computation, and it is what allows `BCWStep.verify()` to check
determinants at every step.

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

## The linear part

The normalization of Chapter II, Proposition (1.1) needs an element of
`GL_n(k)`,
and only some Gauss operations are elementary in the sense of the paper. A
transvection `X_i ↦ X_i + a X_j` is: `a X_j` is free of `X_i`, and
`Transvection.as_elementary_factor()` hands it to `elementary.py` unchanged, in
`EA^0` rather than `EA^1`. A transposition and a dilation are not — a dilation
displaces `X_i` by `(a - 1) X_i`, which involves `X_i`, and a transposition
moves two coordinates and has determinant `-1`.

The shortest argument needs no factorization at all: every element of
`EA_n(k)` has determinant one, and the transformation normalizing Alpöge's map
has determinant `-1/2`. That is why the linear part gets its own type rather
than a scaling parameter on `ElementaryFactor`, and why `LinearStep` is the
only kind of step permitted to change the Jacobian determinant.

`LinearAutomorphism` mirrors `ElementaryAutomorphism` throughout: ordered
product, factorization kept rather than multiplied out, composition by
concatenation, inversion by reversal, determinant as a product of factor
determinants without forming a matrix.

`is_elementary` on a product is sufficient, not characteristic. Two equal
transpositions multiply to the identity, which lies in `EA_n(k)` although
neither factor does. The property reports on the factorization that was
supplied. A certificate can check that without forming any matrix.

Dilations need their coefficient to be a unit, so a map read off a paper over
`ZZ` passes through `over_field()` first. That stays a visible step: two maps
over different coefficient domains are different objects here, and the
arithmetic must not widen one quietly.

---

## Certificates

A step certifies one identity between two maps. `Step` is a protocol rather
than a base class — a step is anything that can say what it starts from, what
it reaches, how it got there, and how to carry a collision across, and nothing
has to inherit to qualify.

Two kinds exist. `LinearStep` composes an element of `GL_n(k)` on the left.
`BCWStep` is one application of Proposition (3.1): with `H = (…, X_u + P,
X_v + Q)` and `G = (…, X_i - X_u X_v, …)`,

    F' = G ∘ F^[m] ∘ H.

`G` and `H` are *derived* from the index and the two factor slots by that
formula, and are never stored beside them. Storing both a factorization and
the automorphisms built from it would allow the two to disagree, and the
identity check would then compare one of them against the other.

### Factor slots

A step is given two slots, and each supplies one factor. `Fresh(P, u)`
introduces a new generator `u`, whose component in the target is `u + P`.
`Carried(j)` reuses coordinate `j` of the source, which already has the form
`X_j + P`. `m` is the number of `Fresh` slots, so a step introduces two, one
or no generators.

Reusing a coordinate is not in the paper. It is admitted because the identity
holds for every `m`, and because a reduction that reuses carriers reaches a
lower dimension. The seventeen-dimensional reduction of Alpöge's map
introduces `x1²` twice and `x1x2` twice; avoiding both duplications takes it
to dimension 15.

At `m = 0` the step performs no stabilization and `H` is the identity, so it
is not an application of Proposition (3.1). It is the identity that
proposition rests on, which holds for every `m`. An earlier plan gave that
case its own simpler type. The slot form was chosen instead, because
`F' = G ∘ F` alone does not record which product was removed, from which
component, or through which two carriers.

Transport differs in one respect. For `m ≥ 1` at least one slot contributes a
zero at the padded image, so the image is unchanged apart from padding. At
`m = 0` both contributions are real values and the image moves.

Two things are wider than the paper states them, because the reduction of
Alpöge's map to dimension 17 needs both and the identity holds for both. `P·Q`
is any subsum of the target component rather than the factorization of a single
leading monomial — one step removes four monomials of degrees 7, 6, 5 and 4 at
once. And the target component is any component: step seven acts on component
11, which step four introduced.

### Verification raises, and says which obligation failed

`verify()` returns nothing and raises `VerificationError`, carrying the stable
identifier of the obligation from `contracts.md` and, inside a chain, the index
of the step. A boolean would collapse six distinct obligations into one bit,
and the first question anyone asks of a failed certificate is which one failed.

### Provenance

A step records whether its target was supplied or computed by `build()`. For a
supplied target the identity check compares an externally computed map against
the formula and can fail; for a constructed one it compares the implementation
against itself and cannot. That is a self-check, not evidence, and the
distinction has to survive into any review — so `Reduction` propagates the
weaker provenance of its steps rather than averaging it away.

The label is recorded, not given: the public constructor takes no such
argument and always writes `SUPPLIED`, because a target reaching it came from
outside. `build()` is the only route to `CONSTRUCTED`. That guards against
mislabelling by accident and not against deliberate forgery — Python has no
privacy — and it is worth reading it as the former rather than the latter.

Because the label is observable, it is part of the value. Leaving it out of
equality would give equal objects a disagreeing attribute, and a set or cache
could quietly replace a supplied step by a constructed one with the same
target.

The same honesty applies within a step. Some obligations cannot fail on
supplied data at all: the determinant equality follows from the identity
together with every element of `EA_n(k)` having determinant one, and the
exhibited inverses come from the definition. They are retained because they are
cheap on the maps a reduction produces and localize an error to the step that
made it. `contracts.md` says per type which obligations are load-bearing.

---

## Reduction

A chain of steps, and the induction over them.

```
steps: tuple[Step, ...]
```

Verification consists of checking every step and the adjacency of consecutive
maps, and stops there. That the target is a Keller map, or has degree three,
follows from the local certificates; recomputing it would be a second and
independent argument, which is not what a certificate is for. What the chain
reports — degrees, dimensions, filtration level — it reports rather than
constrains.

Nothing requires a step to make progress. Two steps of the reference reduction
leave the degree at seven, because they remove top-degree terms from a
component that is not the deepest one. A certificate certifies correctness;
whether a step makes progress is a question for the search in 0.4 and the
heuristics of 0.5.

Transport is what the structure exists for. Each step carries a collision from
its source to its target and verifies it on both sides. A chain that completes
has therefore checked the counterexample at every intermediate map, not only at
the two ends. A degree reduction that loses the collision it started from has
reduced the wrong thing.

---

## Variable Management

Stable extensions introduce fresh generators and therefore create a new
`PolyRing` containing the old generators and the new identity coordinates.
Existing coordinate polynomials are transferred into the enlarged ring without
passing through general expressions.

Naming those generators is isolated in `kellermap.variables` as a

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

`VariableFactory` covers naming and nothing else. `ReductionContext` keeps
names reproducible across a complete reduction sequence, and is deliberately
thin: it names generators, extends rings and maps, and knows nothing about
steps. Which step to take is 0.4, and a context that knew would be the wrong
object to ask.

The context does not trust the factory. Both properties a factory promises are
cheap to check, and both are checked on every call — purity by asking twice and comparing,
composition by allocating `count` names at once and then one at a time. The
reason is the one this section already gives twice: neither failure raises
anywhere downstream. A counting factory and one naming its output after the
size of the ring it was handed both produce perfectly valid polynomial maps,
just not the ones the identity needs.

A step takes its two variables as data rather than taking a context. That is
not only separation of concerns: a supplied certificate has to record the
generators it used, or it could not be checked at all, so the variables belong
to the certificate whether a context produced them or not.

---

## Polynomial Arithmetic Strategy

### One answer to what zero means

Comparisons inside a `PolyRing` need no zero test: the domain canonicalizes on
the way in, so `(T^2 - 1)/(T - 1)` is already `T + 1` before anything looks at
it, and two equal elements are the same object in the same normal form.

`Collision` is the one surface where that does not hold, and it does not hold
on purpose. Its coordinates are points of the coefficient field rather than
polynomials, and pushing them through a domain would tie a collision to one
map — which is precisely what `Collision` avoids by holding no map at all. They
therefore arrive as `Expr` and are compared as `Expr`, and `expand` is the
wrong tool there because it does not clear a denominator.

`kellermap.canonical` holds the one answer: `cancel(together(...))`, a decision
procedure for rational functions, which is exactly the class the coefficient
domains of this project fall into. Coordinates are put into that form as they
enter, so equality and hashing stay consistent with each other. The remaining
`Expr`-level comparisons in the package — the two determinant checks and the
pivot tests in `factorize` — use the same function, defensively rather than out
of need: their values come out of a ring and are normalized already. Having a
second, cheaper answer to the same question is how the original defect arose.


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

### The SymPy lower bound is semantic, not just API

`sympy>=1.14` is not a matter of a missing method. Up to 1.13, `PolyRing.__new__`
interned its rings in a process-wide `_ring_cache`: two constructions with equal
arguments returned *the same object*, so `clone_ring()` could not produce an
isolated ring at all. The value semantics this project promises — no mutable
object shared with a caller — is unreachable on 1.13, and a compatibility shim
for the also-missing `PolyRing.is_element()` would only move the failure later.

`make test-minimum` resolves to the lowest permitted versions and runs the suite
against them. Without it a declared lower bound is a guess: development happens
against current packages, and `sympy>=1.13` sat in `pyproject.toml` unnoticed
even though test collection failed on it.

### Executable documentation

`docs/api.md` is collected by pytest with `--doctest-glob=*.md`. Every example
in it runs on every `make check`, so the reference cannot describe an API the
library no longer has. It is not a substitute for the unit tests: it covers the
surface a reader meets first, not the edge cases.

### Regression and benchmark tests

Known examples from the literature are preserved to guarantee that future
optimizations never change mathematical correctness.

Four regression examples are kept. The small one checks Alpöge's degree-seven
map in dimension three by asserting both its constant Jacobian determinant and
an explicit collision.

The second is a cubic Keller map in dimension 17 carrying the same collision.
Since 0.2 it is *derived*: the suite verifies a chain of eight steps from the
small one to it and transports the collision along. Only the last step is
supplied, because the intermediate maps in dimensions 5 to 15 are published
nowhere and writing them out ourselves would put this library's own output
behind a `SUPPLIED` label. The external fact is the endpoint, and a negative
control changes one component, so that the test fails if the check does not
work.

The third is `alpoege15`, this project's own reduction of the same source. It
reuses the two carrier values that the seventeen-dimensional chain introduces
twice, and is derived since 0.3. Its target is supplied by an implementation
that does not use this library, so the check can fail; what the agreement
shows is that two implementations of the same formulas compute the same thing,
not that the result matches a published map.

The fourth is a published cubic map in dimension 19, kept as fixed input. Its
reduction reuses carrier variables across steps, which `BCWStep` has been able
to express since 0.3. What is missing is the ordered sequence of steps: the
source publishes the map but not its factorization, and this project has not
reconstructed one. It is in the suite as an independent second instance and as
a target for the search in 0.4.

Searching for a factorization rather than verifying a presented one is 0.4
throughout.

See `references.md` for sources and for what the fixed data rests on.

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
