# Contracts

Normative specification of the public surface introduced in version 0.2:
`ReductionContext`, `BCWStep` and `Reduction`.

This document is written *before* the implementation and is binding on it.
Where the implementation and this page disagree, the implementation is wrong
until this page is changed deliberately.

Each obligation carries a stable identifier (`RC-1`, `BCW-4`, `RED-2`, ...).
Error messages cite the identifier that failed, so that an independent review
can address findings to a numbered obligation rather than to a line of code.
Identifiers are never reused; a withdrawn obligation stays listed as withdrawn.

**Status as of `0.2.0`:** every obligation on this page is implemented, and
the test suite covers every statement of the package. Where the implementation
forced a change, this page was amended deliberately and the amendment is
visible in the wording — the clearest cases are COL-4 and BCW-3, which moved
from obligations of `verify()` to constructor invariants, and LIN-2, which was
narrowed to what is actually checkable.

Obligations marked **[0.3]** are specified but not yet implemented. They are
written before the implementation, as the rest of this page was: it is easier
to decide what a certificate must guarantee while no code depends on the
answer. A review of the released library should not look for them.

Full statement coverage is not full obligation coverage, and the difference is
worth naming. Several of the raises here cannot be reached at all, because an
obligation checked earlier in the same `verify()` rules them out — BCW-5,
BCW-7, LIN-2, LIN-3 and the `MA^1` clause of LIN-6. They carry
`# pragma: no cover` with the reason written beside them. Writing a test for
them would mean forcing the object into a state it cannot reach. Each type states which of
its obligations can fail on supplied data and which are self-checks of the
library's own arithmetic; a review should weigh them differently.

`architecture.md` explains why the design is what it is. `api.md` shows what
the implemented surface does, with executed examples. This page states what
the implementation is required to guarantee.

---

## Contents

- [Collision](#collision)
- [LinearAutomorphism](#linearautomorphism)
- [The Step protocol](#the-step-protocol)
- [ReductionContext](#reductioncontext)
- [BCWStep](#bcwstep)
- [LinearStep](#linearstep)
- [Reduction](#reduction)
- [Errors](#errors)
- [Deliberate non-obligations](#deliberate-non-obligations)

---

## Collision

Distinct points of `k^n` sharing one image. Implemented in work package 1.

```python
@dataclass(frozen=True)
class Collision:
    points: tuple[tuple[sp.Expr, ...], ...]
    image: tuple[sp.Expr, ...]

    @classmethod
    def at(cls, F: PolynomialMap, points) -> Collision: ...

    def verify(self, F: PolynomialMap) -> None: ...

    def extended(self, coordinates, image) -> Collision: ...

    def with_image(self, image) -> Collision: ...
```

**COL-1 — Dimensions agree.** `self.dimension == F.dimension`.

**COL-2 — Coordinates are constant relative to the map.** No coordinate of a
point involves a variable of `F`. A coordinate carrying one of the map's own
variables would be substituted into itself by the evaluation, and the resulting
identity would say nothing about any point. Symbols of the coefficient domain
are permitted: a collision over `k(T)` is a collision.

**COL-3 — The image is the image.** `F` sends every point to `image`, checked
by evaluation and compared as values rather than as syntax. "As values" means
in the normal form of `kellermap.canonical`: over `k(T)` a correct image
coordinate may arrive written as `(T^2 - 1)/(T - 1)`, and rejecting it would be
a false negative.

**COL-4 — Distinctness is a constructor invariant, not an obligation.** A
`Collision` whose points coincide cannot be built; the constructor raises
`ValueError`. This is deliberately stronger than reporting it in `verify()`: a
certificate whose points coincide is not weaker evidence but no evidence at
all, and it should not be possible to hold one. Equality of points is decided
by value, so two spellings of one point are one point — over `k(T)`,
`(T^2 - 1)/(T - 1)` and `T + 1` are the same coordinate and the pair is
refused.

**COL-5 — The collision holds no map.** The same points are a collision of
every map that identifies them, and a reduction verifies them against each map
of the chain in turn. `Collision` therefore stores points and image only, and
takes the map as an argument.

**COL-6 — Value semantics.** Immutable; `extended()` and `with_image()` return
new objects. Equality treats the points as a set, since listing them in another
order is the same certificate.

Coordinates are put into normal form as they enter, so `__eq__` decides
soundly by `==` and agrees with `__hash__`. That order matters: canonicalizing
at construction is what makes the two consistent, whereas comparing
canonically while storing whatever arrived would leave equal collisions hashing
differently. Normal form is not conversion — `Rational(1, 4)` and `Float(0.25)`
remain different, as everywhere else in SymPy.

Everything else in the package is compared inside a `PolyRing`, where the
domain canonicalizes on the way in and the question does not arise. `Collision`
is the exception because its coordinates belong to the coefficient field rather
than to the ring; forcing them through a domain would tie a collision to one
map, which COL-5 exists to prevent.
---

## LinearAutomorphism

An element of `GL_n(k)`, as an ordered product of Gauss generators. Implemented
in work package 2.

```python
class LinearFactor(ABC):
    ring: PolyRing
    dimension: int
    is_elementary: bool

    def matrix(self) -> sp.ImmutableMatrix: ...
    def determinant(self) -> sp.Expr: ...
    def inverse(self) -> LinearFactor: ...
    def apply_to(self, F: PolynomialMap) -> PolynomialMap: ...


@dataclass(frozen=True)
class LinearAutomorphism:
    factors: tuple[LinearFactor, ...]

    @classmethod
    def factorize(cls, ring, matrix) -> LinearAutomorphism: ...

    def matrix(self, ring: PolyRing | None = None) -> sp.ImmutableMatrix: ...
    def determinant(self) -> sp.Expr: ...
    def inverse(self) -> LinearAutomorphism: ...
    def apply_to(self, F: PolynomialMap) -> PolynomialMap: ...
```

The type carries no `verify()` and therefore no numbered obligations. It is an
algebraic object like `ElementaryFactor`, not a certificate; what is verified
about it is verified by `LinearStep`, in LIN-1 to LIN-4. What the type
guarantees structurally:

**Three generators, and only one of them elementary.** `Transvection`
(`X_i |-> X_i + a X_j`, `i != j`) reports `is_elementary` as true and converts
to an `ElementaryFactor` unchanged; it lies in `EA^0` and not in `EA^1`.
`Transposition` and `Dilation` report false. A dilation displaces `X_i` by
`(a - 1) X_i`, which involves `X_i`; a transposition moves two coordinates and
has determinant `-1`.

**`is_elementary` on a product is sufficient, not characteristic.** Two equal
transpositions multiply to the identity, which lies in `EA_n(k)` although
neither factor does. The property reports on the factorization that was
supplied. A certificate can check that without forming any matrix.

**The determinant is structural.** It is the product of the factor
determinants — `1`, `-1` and `a` respectively — and no matrix is formed to
obtain it. Unlike in `EA_n(k)` it is not one in general, which is precisely
why the linear part needs its own type and its own kind of step.

**The factorization is kept.** `factorize()` runs Gauss-Jordan elimination and
records the row operations; two factorizations of one matrix are different
objects and compare unequal, as for `ElementaryAutomorphism`.

**Widening the domain is explicit.** A dilation needs its coefficient to be a
unit, so a map over `ZZ` has to pass through `over_field()` before it can be
normalized. Two maps over different domains are different objects here, and
the arithmetic does not widen one quietly.

---

## The Step protocol

`Reduction` is a sequence of steps. A step is anything satisfying:

```python
@runtime_checkable
class Step(Protocol):
    @property
    def source(self) -> PolynomialMap: ...

    @property
    def target(self) -> PolynomialMap: ...

    @property
    def provenance(self) -> Provenance: ...

    @property
    def filtration_level(self) -> int | float: ...

    def verify(self) -> None: ...

    def transport(self, collision: Collision) -> Collision: ...
```

`Step`, `LinearStep` and `Reduction` live at the top level of the package, in
`kellermap.reduction`; only `BCWStep` lives in `kellermap.bcw`. A chain of
certified identities is not a notion of the 1982 paper, and a second reduction
method would reuse it -- which is exactly the misnomer the subpackage exists to
avoid. `LinearStep` composes an element of `GL_n(k)` on the left; that BCW
Chapter II, Proposition (1.1) does so does not make the operation theirs.

`filtration_level` reports `math.inf` where a step establishes no `EA` level,
following `ElementaryAutomorphism.filtration_degree()` on the identity.

**STEP-1 — Verification raises, it does not return a verdict.** `verify()`
returns `None` on success and raises `VerificationError` otherwise. A boolean
would collapse six distinct obligations into one bit; an audit needs to know
*which* one failed.

**STEP-2 — Verification is pure.** `verify()` has no observable effect other
than caching its own result. Calling it twice is equivalent to calling it once,
and never calling it changes nothing about the object.

**STEP-3 — Transport presupposes nothing.** `transport()` verifies the incoming
collision against `source` before transporting, and the returned collision
against `target` afterwards. A collision that does not hold for `source` raises
`VerificationError`; the method never returns an unverified result.

**STEP-4 — Transport preserves cardinality.** If the argument holds for
`source` and has `k` distinct points, the result holds for `target` and has `k`
distinct points. This is the property the whole project delivers: a
counterexample stays a counterexample.

**STEP-5 — Value semantics.** Steps are immutable, hashable, and compare by
mathematical content, not by object identity.

`provenance` is part of that content. It is publicly observable, so excluding
it would leave equal objects disagreeing about an attribute, and a set or a
cache could then replace a supplied step by a constructed one with the same
target without anything noticing. What equality ignores is construction
history proper — which factory instance was involved, in what order the
factors were listed — not what the certificate records about its own
standing.

---

## ReductionContext

Reproducible naming of fresh generators across a whole reduction.

```python
@dataclass(frozen=True)
class ReductionContext:
    factory: VariableFactory = DEFAULT_VARIABLE_FACTORY

    def variables(self, ring: PolyRing, count: int) -> tuple[sp.Symbol, ...]: ...

    def extended_ring(self, ring: PolyRing, count: int) -> PolyRing: ...

    def extend(self, F: PolynomialMap, count: int) -> PolynomialMap: ...
```

It lives in `kellermap.context`, at the top level. Naming the generators of a
chain of stabilizations is not a notion of the 1982 paper — the same argument
that puts `Reduction` there, and the one this page already makes above.

**RC-1 — Determinism.** `variables(ring, count)` is a pure function of its two
arguments. Two calls with value-equal arguments return equal names, whether
they occur in the same reduction, in a different one, in a later process, or in
a different interpreter run. Dependence on a step counter, on call order, on
`id()`, on set or dict iteration order, or on anything outside the arguments is
forbidden.

**RC-2 — No hidden state.** The context carries nothing that changes between
calls. Anything a reduction must remember is passed explicitly. This is what
distinguishes the context from a factory that counts upwards: a counting
factory names the two sides of `(F ∘ G)^[m] = F^[m] ∘ G^[m]` differently, and
does so *silently*, since both sides remain valid maps.

**RC-3 — Composition.** Extending twice allocates what extending once
allocates, in the same order:

```
variables(R, m) + variables(extended_ring(R, m), l) == variables(R, m + l)
```

A reduction stabilizes step by step and must land where a single stabilization
lands.

**RC-4 — Freshness.** The result has exactly `count` entries, all `sp.Symbol`,
pairwise distinct by *name*, and disjoint from `reserved_names(ring)` —
generators of the ring and indeterminates of the coefficient domain at every
level of nesting.

**RC-5 — The context rechecks the factory.** RC-1, RC-3 and RC-4 are verified
on the factory's output rather than assumed, on every call. None of the three
failures raises anywhere downstream: `PolyRing` accepts a duplicated generator
name without complaint and yields a ring in which two coordinates denote one
generator, and an impure or non-composing factory produces perfectly valid maps
that are simply not the ones the identity needs.

RC-1 is checked by asking twice and comparing, which catches a factory holding
a counter. RC-3 is checked by allocating `count` names at once and then one at
a time, which catches a factory naming its output after the size of the ring it
was handed — pure, collision-free and still wrong.

The cost is a constant number of extra factory calls and ring clones per
allocation, on an operation a reduction performs a handful of times.

**RC-6 — Arithmetic context is preserved.** Every map produced by `extend()`
has the coefficient domain and the monomial order of its argument. A reduction
runs in one arithmetic context from beginning to end.

**RC-7 — Scope.** The context names generators and extends rings and maps. It
does not choose steps, does not verify anything, does not hold the reduction,
and does not know which step is being taken. Selection is milestone 0.5.

A step therefore takes its two variables as data rather than taking a context.
That is not only separation of concerns: a supplied certificate has to record
the generators it used, or it could not be checked at all, so the variables are
part of the certificate whether a context produced them or not.

---

## BCWStep

One application of Bass–Connell–Wright, Proposition (3.1), and **[0.3]** its
extension to steps that reuse a factor an earlier step already introduced.

```python
@dataclass(frozen=True)
class Fresh:
    polynomial: sp.Expr
    variable: sp.Symbol


@dataclass(frozen=True)
class Carried:
    index: int


Factor = Fresh | Carried


@dataclass(frozen=True)
class BCWStep:
    source: PolynomialMap
    target: PolynomialMap
    index: int
    left: Factor
    right: Factor
    filtration_level: int
    provenance: Provenance

    @classmethod
    def build(cls, source, index, left, right, filtration_level=1): ...

    @property
    def P(self) -> sp.Expr: ...

    @property
    def Q(self) -> sp.Expr: ...

    @property
    def variables(self) -> tuple[sp.Symbol, ...]: ...

    @property
    def m(self) -> int: ...

    @property
    def G(self) -> ElementaryAutomorphism: ...

    @property
    def H(self) -> ElementaryAutomorphism: ...

    @property
    def stabilized(self) -> PolynomialMap: ...

    @property
    def attained_filtration_level(self) -> int | float: ...
```

`index` is zero-based. A step is given two *factor slots*. Each slot supplies
one of the two factors, in one of two ways:

- `Fresh(P, u)` introduces a new generator `u`. Its component in the target is
  `u + P`, so the new coordinate carries `P`.
- `Carried(j)` reuses coordinate `j` of the source. That component already has
  the form `X_j + P`, so the factor `P` is available without a new generator.

An earlier draft of this page also listed a `classic()` constructor that kept
the call form of 0.2, taking `P`, `Q` and a pair of variables. It was dropped
during implementation. `Fresh(P, u), Fresh(Q, v)` is no longer than the old
form and shows which factor goes with which variable, so the second entry point
earned nothing. Dropping it also removed the last parameter typed `Iterable`
on `BCWStep`, and with it the one place where a one-shot iterable could be
consumed twice.

`m` is the number of `Fresh` slots, so `m ∈ {0, 1, 2}`. `variables` is the
fresh generators in slot order. These are the new generators only, not the
variables of either map; those are `source.variables` and `target.variables`.

`P` and `Q` are the values of the two slots. They are derived, not stored: a
`Fresh` slot supplies its own polynomial, and a `Carried(j)` slot supplies
`source.components[j] - X_j`.

`G` and `H` are also derived from the slots, and are never supplied separately.
If both a factorization and the automorphisms built from it were stored, the
two could disagree. Write `A` and `B` for the *coordinates* of the two slots:
the fresh generator for a `Fresh` slot, and `X_j` for a `Carried(j)` slot.
Then

    G:  X_index  |-->  X_index - A*B
    H:  one factor per Fresh slot,  u |--> u + P

and `H` is the identity when `m = 0`.

### Why one type and not two

The roadmap for 0.3 planned a separate and simpler step type for the case
`m = 0`, because that case performs no stabilization and is therefore not
Proposition (3.1). Writing this contract led to a different conclusion.

A step `F' = G ∘ F` with `G` elementary is more general, but it is too general
to serve as this certificate. It records that some elementary automorphism was
composed on the left. It does not record which product was removed, from which
component, or through which two carriers. The slot form records all three, and
it reduces to `F' = G ∘ F` by itself when both slots are `Carried`.

The consequence is that `BCWStep` at `m = 0` is no longer an application of
Proposition (3.1). It is the identity on which that proposition rests, which
holds for every `m`. `m` is reported so that a reader can tell the cases
apart.

**BCW-1 — The identity.** `target == G ∘ source^[m] ∘ H`, checked as a
polynomial identity in one shared `PolyRing`, not by comparing printed
expressions. **[0.3]** amends this only in replacing the fixed `2` by `m`; at
`m = 0` the stabilization and `H` are both trivial and it reads
`target == G ∘ source`.

**BCW-2 — Dimension and generators.** `target.dimension == source.dimension + m`;
the generators of `target` are those of `source` followed by `variables`, in
slot order; each fresh variable satisfies RC-4 against `source.ring`.

**[0.3]** amends this. Until 0.3 the step always introduced two new
generators, and `m` was fixed at 2. This is the only place in the milestone
where a binding obligation is weakened rather than extended, and it is the
reason 0.3 is a minor release and not a patch. Nothing that verified before
stops verifying: a step with two `Fresh` slots is exactly the earlier step.

**BCW-3 — The factors are free of the fresh variables.** No polynomial of a
`Fresh` slot involves any of the fresh variables. Two consequences depend on
this: the factors of `H` commute, so their order is immaterial, and `H^-1` is
the componentwise negation, which is what `transport()` uses. A `Carried` slot satisfies this automatically, because its value comes from a
component of the source.

Enforced at construction, and by conversion rather than by inspection: `P` and
`Q` are converted into `source.ring` and stored as elements of it. Since the
fresh variables are not generators of that ring, a factor mentioning one cannot
be built at all, and BCW-3 has no verify-time code — the same shape as COL-4.

The conversion settles three questions at once that a check on symbol names
answered badly or not at all. A factor must be a polynomial, so `1/x` is
refused at construction rather than failing somewhere downstream. Its
coefficients must lie in the domain, so `x/2` is refused over `ZZ[T]` and
admitted over `ZZ(T)`. And every symbol in it must be a generator *or a
parameter of the coefficient domain*, so `T x` over `k[T]` is admitted — which
a name-based check refused. That put `BCWStep` in conflict with COL-2, which
allows the same `T` explicitly.

Freshness of `variables` is likewise a constructor invariant, checked against
`reserved_names(source.ring)` rather than against the coordinates alone: a
parameter of the coefficient domain is taken too. Distinctness of the two is
decided by `symbol.name`, because `Symbol("v")` and `Symbol("v", positive=True)`
are two symbols for SymPy and one generator for a `PolyRing`.

**BCW-4 — The target component may be any component.** `0 <= index <
source.dimension`. BCW state the proposition for the first component; a
reduction reaches components that an earlier step introduced. In the reference
reduction of Alpöge's map, step seven acts on component 11, which step four
created.

**BCW-5 — Invertibility is exhibited, not asserted.** `G` and `H` are checked
to be products of elementary factors whose polynomials do not involve their own
variable, and `G.inverse() ∘ G` and `H.inverse() ∘ H` are checked to be the
identity map. The factorization is kept rather than multiplied out, because
the factorization is what a reader checks.

**[0.3]** `G` is elementary in every case. Its displacement `-A*B` is free of
`X_index` exactly when neither slot names `index`, which BCW-10 requires. At
`m = 0`, `H` is the identity, so the check on `H` establishes nothing.

**BCW-6 — The declared filtration level is attained.** `filtration_level ∈
{0, 1}`, `H.is_in_EA(filtration_level)` holds, and `G.is_in_EA(1)` holds.

**[0.3]** At `m = 0`, `H` is the identity. The identity lies in every `EA^d`,
so the declared level constrains nothing and `attained_filtration_level` is
infinite; the obligation then rests on `G` alone. A step that reuses both
factors cannot leave `MA^1`. That is useful to know when choosing between two
ways of removing the same product. The
level is declared and checked, not inferred: Proposition (3.1) admits `EA^0`
when the factorization must be linear, and whether a step leaves `MA^1` is a
fact the certificate has to record. In the reference reduction exactly two of
seven steps declare `EA^0`, and those two are why the resulting map lies in
`MA^0` and not in `MA^1`.

Declaring `EA^0` where `EA^1` holds is a true statement and is accepted. The
step reports what it actually reaches as `attained_filtration_level`, and a
reduction that understates its level merely reports a weaker bound than it
could.

**BCW-7 — The determinant is unchanged.** `target.determinant() ==
source.determinant()`. Redundant in principle, since every element of `EA_n(k)`
has determinant one, and retained because it is cheap for the maps a reduction
produces and catches implementation errors early.

**BCW-8 — Transport.** With `F(a) = F(b) = c` and the fresh coordinates filled
with zero, a point gains one coordinate per `Fresh` slot, in slot order, and
the image gains a zero per `Fresh` slot:

```
a  |-->  (a, -P(a), -Q(a)),        c  |-->  (c, 0, 0)
```

which is `H^-1` applied to the padded point and `G` applied to the padded
image. Any constant fill would do — the points must merely share it — and the
contract fixes zero, because a non-zero fill `(s, t)` moves the image component
`index` to `c_index - s*t` and buys nothing.

**[0.3]** A `Carried` slot appends nothing to a point, because it adds no
coordinate. It does affect the image. `G` reduces component `index` of the
padded image by the product of the two slot values at that image: `0` for a
`Fresh` slot, and `c_j` for `Carried(j)`. So for `m ≥ 1` at least one of the
two factors is zero and the image is unchanged apart from padding, as before.
Only at `m = 0` can the image move, and it then moves to
`c_index - c_u * c_w`. This is the only respect in which reusing a coordinate
differs from introducing one, beyond the saved dimension.

### Supplied versus constructed

**BCW-9 — Provenance is recorded, and not settable.** `provenance` is
`SUPPLIED` when `target` was given to the constructor and `CONSTRUCTED` when it
came from `BCWStep.build(source, index, left, right)`. The public
constructor takes no such argument: a target that reaches it came from outside,
and there is no way to say otherwise. `build()` is the only route to a
`CONSTRUCTED` step.

The guarantee is an integrity marker against mislabelling by accident, not a
security boundary. Python has no privacy, and a caller determined to overwrite
the attribute can. A review should read it as "this label was not set by hand
somewhere in the call chain", which is what it is for, and not as a claim that
the object could not be tampered with.

This distinction is the central result of milestone 0.2 and has to remain
visible to any audit.
For a `SUPPLIED` step, BCW-1 compares an externally computed map against the
formula and can fail. For a `CONSTRUCTED` step it compares the implementation
against itself and cannot: it is a self-check, not evidence. `Reduction`
propagates the weaker provenance of its steps.

**BCW-10 — [0.3] A reused slot names a carrier.** For `Carried(j)`:
`0 <= j < source.dimension`, `j != index`, and `source.components[j] - X_j` is
free of `X_j`.

The first two clauses are constructor invariants and raise `ValueError`; they
keep `G` elementary. The third clause is checked by `verify()` and gives the
step its meaning. Without it, `P` would be an arbitrary component minus a
variable, rather than a value that some coordinate carries, and the statement
"this step removes `P·Q`" would describe nothing. The identity of BCW-1 holds
in either case. That is why this clause has to be stated separately: it
constrains what the step means, not what it computes.

Both slots may name the same coordinate. `G` is then `X_index - X_j^2`, and the
step removes a square. This is a valid case and needs no exception.

### Which of these can fail on supplied data

BCW-1, BCW-2, BCW-6 and **[0.3]** the third clause of BCW-10. BCW-3, the
freshness half of BCW-2 and the first two clauses of BCW-10 are constructor
invariants and are not reachable by `verify()` at all. BCW-5 and BCW-7 follow
from BCW-1 — every element of `EA_n(k)` has determinant one, and the exhibited
inverses come from the definition — and are retained as cheap self-checks that
localize an error to the step that made it. A review should weigh them as such.

---

## LinearStep

The linear normalization of BCW Chapter II, Proposition (1.1). A `Step`, so
that a
`Reduction` can span the whole derivation rather than only its BCW part.

```python
@dataclass(frozen=True)
class LinearStep:
    source: PolynomialMap
    target: PolynomialMap
    transformation: LinearAutomorphism
    normalizing: bool
    provenance: Provenance
```

As for `BCWStep`, `provenance` is recorded rather than given: the public
constructor always sets `SUPPLIED`, and `build()` and `normalize()` are the
only routes to `CONSTRUCTED`.

**LIN-1 — The identity.** `target == transformation ∘ source`, as a polynomial
identity.

**LIN-2 — The exhibited inverse undoes the transformation.**
`transformation.inverse()` composes with `transformation` to the identity map.

That the factors multiply to the declared matrix is *not* checked, because it
is not checkable: `LinearAutomorphism.matrix()` is that product, and no second,
independently declared matrix is stored to compare it against. That is
deliberate, for the reason `BCWStep` derives `G` and `H` rather than storing
them — storing both a factorization and the automorphisms built from it would allow
the two to disagree.

**LIN-3 — Determinant bookkeeping.** `target.determinant() ==
transformation.determinant() * source.determinant()`. A linear step is the only
kind that may change the determinant, and it must say by what factor. Implied
by LIN-1 and retained anyway: two multiplications on maps a reduction produces,
which catch an error in a factor's determinant before it propagates through a
chain.

**LIN-4 — Not elementary.** `transformation` is not required to lie in
`EA_n(k)`, and generally does not: every element of `EA_n(k)` has determinant
one. The normalization of Alpöge's map has determinant `-1/2`.

**LIN-5 — Transport.** Points are unchanged; the image becomes
`transformation(c)`. Left composition does not move preimages.

**LIN-6 — Normalization is a claim, not a definition.** If the step declares
itself the normalization, `source` lies in `MA^0`, `transformation` equals the
inverse of `J(source)(0)`, and `target` lies in `MA^1`. A `LinearStep` that is
not so declared carries no such obligation.

The `MA^0` clause is not decoration. Proposition (1.1) splits `F` as
`(X + F(0)) ∘ F_(1) ∘ F'`, so the linear normalization is the *second* factor
and presupposes the first. Without it the target simply fails to reach `MA^1`,
which is true but points one stage past the cause; `normalize()` refuses such a
source outright rather than building a step that fails its own verification.

### Which of these can fail on supplied data

LIN-1 and the first clause of LIN-6. LIN-2 and LIN-3 follow from LIN-1 and can
only fail if the library is wrong about its own arithmetic; the second clause
of LIN-6 follows from the first. They are retained as cheap self-checks, and a
review should weigh them as such rather than as evidence about a supplied
target.

---

## Reduction

A chain of steps, and the induction over them.

```python
@dataclass(frozen=True)
class Reduction:
    steps: tuple[Step, ...]

    @property
    def source(self) -> PolynomialMap: ...

    @property
    def target(self) -> PolynomialMap: ...

    @property
    def provenance(self) -> Provenance: ...

    def verify(self) -> None: ...

    def transport(self, collision: Collision) -> Collision: ...

    def filtration_level(self) -> int: ...
```

**RED-1 — Non-empty.** A reduction has at least one step, so that `source` and
`target` are defined without a separate carrier for the identity case.

**[0.3]** A chain's dimensions no longer grow by two at every BCW step: with
`m ∈ {0, 1, 2}` they may grow by nothing at all. `dimensions()` reports what
happened rather than constraining it, and RED-2 is unaffected — adjacency is
equality of maps, not of shapes.

**RED-2 — Adjacency.** `steps[i].target == steps[i + 1].source` for every `i`,
by value equality of `PolynomialMap` — variables, coefficient domain and
components. Adjacency is what turns the individual certificates into a proof
about the whole chain, so it is checked separately and not inferred from the
steps.

**RED-3 — Verification is local plus adjacency, and nothing else.**
`verify()` calls `verify()` on every step and checks RED-2. It does not
recompute any global invariant of `target`. That the target is a Keller map,
or has a given degree, follows from the local certificates; recomputing it
would be a second, independent argument and is not what a certificate is for.

**RED-4 — Failures are located.** A `VerificationError` raised by `verify()`
names the index of the failing step and the obligation that failed.

**RED-5 — Transport folds.** `transport()` verifies the collision against
`source`, applies `transport()` of each step in order, and verifies the result
against `target`. By STEP-4 the number of distinct points is preserved, so a
verified transport of a genuine collision is a machine-checked proof that
`target` is not injective.

**RED-6 — Filtration.** `filtration_level()` is the minimum of the levels the
steps establish. It answers, from the certificate alone, why the target lies in
the filtration stage it does.

**RED-7 — Provenance propagates.** `Reduction.provenance` is `SUPPLIED` only if
every step is `SUPPLIED`.

**RED-8 — Value semantics.** `steps` is a tuple; concatenation and slicing
return new `Reduction` objects; nothing mutates.

---

## Errors

```python
class VerificationError(Exception):
    obligation: str  # "COL-3", "BCW-1", "RED-2", ...
    message: str  # what went wrong, naming the offending object
    step: int | None  # index within the reduction, if applicable

    def located_at(self, step: int) -> VerificationError: ...
```

A step verifies itself without knowing where in a chain it sits, so the index
is attached afterwards by the reduction that catches the failure.
`located_at()` returns a new exception and leaves the original untouched. The
identifier also appears in `str(...)`, but a caller is expected to branch on
`obligation` rather than to parse the message.

| Situation | Raised |
| --- | --- |
| an obligation on this page fails | `VerificationError` |
| `filtration_level` outside `{0, 1}` | `ValueError` |
| `index` outside `range(source.dimension)` | `ValueError` |
| **[0.3]** a borrowed slot naming `index`, or an index out of range | `ValueError` |
| **[0.3]** a borrowed slot naming a component that is not a carrier | `VerificationError` |
| `P` or `Q` that is not a polynomial over the source's ring | `ValueError` |
| two fresh variables of one name, or a name already reserved | `ValueError` |
| `variables` colliding with reserved names | `ValueError` |
| an empty `steps` tuple | `ValueError` |
| a dilation by zero or by a non-unit of the domain | `ValueError` |
| factorizing a singular matrix | `ValueError` |
| fewer than two collision points, or two equal ones | `ValueError` |
| a collision whose points and image differ in length | `ValueError` |
| a factory returning a miscounted or colliding name | `ValueError` |
| arguments of the wrong type | `TypeError` |

Constructor-time conditions raise at construction. Conditions that require
polynomial arithmetic are checked by `verify()` and raise `VerificationError`;
construction never performs them silently.

---

## Deliberate non-obligations

Listed so that their absence is not read as an oversight.

**No progress measure.** Nothing requires a `BCWStep` to lower the degree or
the number of top-degree monomials. Steps two and three of the reference
reduction leave the degree at seven. A certificate certifies correctness;
whether a step makes progress is a question for the heuristics of 0.5, and
`Reduction` reports degrees rather than constraining them.

**No minimality.** Nothing claims a reduction is the shortest, or the
lowest-dimensional, or that dimension 17 cannot be improved.

**No search.** Neither `BCWStep` nor `Reduction` finds a factorization. They
verify one that is presented to them. Searching is 0.4.

**No reduction method other than this one.** *Withdrawn in 0.3.* Until then,
BCW-2 fixed exactly two fresh variables per step, so a chain of `BCWStep`s
could not express a reduction that reuses carrier variables across steps. The
amendment above admits `m ∈ {0, 1, 2}`, and that limitation is gone. A narrower
one remains.

A reused factor must be carried by a coordinate of the *source* of that step.
BCW-10 is stated against the immediate source, not against the chain. In
practice a carrier does survive, because no step changes a component it does
not target, but `Reduction` still cannot express a step that refers to a map
earlier in the chain. Nothing in 0.3 requires that.

**No injectivity claim about `source`.** `transport()` moves a collision that
is supplied. That a map *has* no collision is not something this framework
establishes.

**No global recomputation.** See RED-3. Where a test recomputes a global
invariant anyway — the determinant of the 17-dimensional map, say — it does so
as an independent cross-check, and that is a property of the test suite, not of
the certificate.
