# Contracts

Normative specification of the verification surface: `Collision`,
`LinearAutomorphism`, the `Step` protocol, `ReductionContext`, `BCWStep`,
`LinearStep`, `TranslationStep`, `Reduction`, and the search that assembles a
reduction.

This document is written *before* the implementation and is binding on it.
Where the implementation and this page disagree, the implementation is wrong
until this page is changed deliberately.

Each obligation carries a stable identifier (`RC-1`, `BCW-4`, `RED-2`, ...).
Error messages cite the identifier that failed, so that an independent review
can address findings to a numbered obligation rather than to a line of code.
Identifiers are never reused; a withdrawn obligation stays listed as withdrawn.

An obligation marked with a milestone number is stated but not yet
implemented, and the marker is removed when the milestone closes. It is a
statement of intent that the implementation is measured against, not a
description of the current code, and a review of an unfinished milestone should
read it as such. Obligations without a marker are implemented.

**Status as of `0.4.0`:** every obligation on this page is
implemented, and the test suite covers every statement of the package. Where
the implementation forced a change, this page was amended deliberately and the
amendment is visible in the wording — the clearest cases are COL-4 and BCW-3,
which moved from obligations of `verify()` to constructor invariants, and
LIN-2, which was narrowed to what is actually checkable.

**Milestone `0.4`, closed.** The milestone added `TranslationStep`, which
completes Chapter II, Proposition (1.1); two searches for a step sequence, one
from the source and one from the target; and the certified factorization of the
published 19-dimensional map. Its obligations carried the `[0.4]` marker while
it ran and carry none now.

Four statements on this page were corrected while it ran, and the corrections
are visible in the wording: the milestone number in RC-7 and under
"No progress measure", the scope of the `filtration_level` row in the error
table, and the withdrawal of the non-obligation "No search".

**Amended in work package 10, after an external audit.** `BCWStep` gains a
coefficient (BCW-11) and admits two `Fresh` slots naming one variable
(BCW-12); BCW-1 and BCW-2 are amended for both. The diagonal is withdrawn from
SEA-5, which returns to plain equality, and REV-4 hands its solved constant to
the step. Both extensions go beyond Chapter II, Proposition (3.1) and are
marked as extensions, as carrier reuse is.

The page has also grown during the milestone, which an audit should read as
intended rather than as drift. SEA-8 to SEA-10 were added in work package 5,
before the enumerator was written and after a measurement showed that the
enumerator the plan implied was unaffordable. The measurement and its numbers
are on this page beside the obligations they justify.

Full statement coverage is not full obligation coverage, and the difference is
worth naming. Several of the raises here cannot be reached at all, because an
obligation checked earlier in the same `verify()` rules them out — BCW-5,
BCW-7, LIN-2, LIN-3, the `MA^1` clause of LIN-6, and, since 0.4, TRA-3, TRA-4
and the `MA^0` clause of TRA-6. They carry
`# pragma: no cover` with the reason written beside them. Writing a test for
them would mean forcing the object into a state it cannot reach. Each type
states which of
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
- [TranslationStep](#translationstep)
- [Reduction](#reduction)
- [Search](#search)
- [Peeling](#peeling)
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

This is the `EA` bound the step establishes for its target. It is
not the filtration degree of the transformation the step applies, and the two
must not be conflated. `TranslationStep` is where they visibly differ: the
translation `X |-> X - c` has filtration degree `-1`, since its displacement
`-c` has order zero, and it lies in no `EA^d` for `d >= 0`. As a step it
establishes no `EA` bound at all, so its `filtration_level` is `math.inf`, like
`LinearStep`'s. Reporting `-1` here would make `Reduction.filtration_level()`
return `-1` for every chain that begins with a translation, which says nothing
about that chain's target; the degree of the transformation is available on the
transformation, where it belongs.

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
and does not know which step is being taken. Selection is milestone 0.4.

The milestone number is a correction. Until 0.4 this clause read 0.5, which
disagreed with the non-obligation "No search" on the same page. 0.4 searches for
one step sequence against a known target; 0.5 searches without one. The
obligations of the search are stated under [Search](#search) below.

The search of 0.4 does not use a `ReductionContext`, because by
SEA-3 it is given the names of the fresh generators rather than allocating
them. This changes nothing about RC-1 to RC-7. The context remains the route
for a reduction that allocates its own names, which is every chain the test
suite builds today.

A step therefore takes its two variables as data rather than taking a context.
That is not only separation of concerns: a supplied certificate has to record
the generators it used, or it could not be checked at all, so the variables are
part of the certificate whether a context produced them or not.

---

## BCWStep

One application of Bass–Connell–Wright, Proposition (3.1), and its extension
to steps that reuse a factor an earlier step already introduced.

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
    coefficient: sp.Expr
    provenance: Provenance

    @classmethod
    def build(cls, source, index, left, right, level=1, coefficient=1): ...

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

`m` is the number of *distinct* fresh variables, so `m ∈ {0, 1, 2}`; two
slots may name one, and it is then introduced once. `variables` is the
fresh generators in slot order. These are the new generators only, not the
variables of either map; those are `source.variables` and `target.variables`.

`P` and `Q` are the values of the two slots. They are derived, not stored: a
`Fresh` slot supplies its own polynomial, and a `Carried(j)` slot supplies
`source.components[j] - X_j`.

`G` and `H` are also derived from the slots, and are never supplied separately.
If both a factorization and the automorphisms built from it were stored, the
two could disagree. Write `A` and `B` for the *coordinates* of the two slots:
the fresh generator for a `Fresh` slot, and `X_j` for a `Carried(j)` slot.
Then, writing `level` for `filtration_level` so the sketch fits the page,

    G:  X_index  |-->  X_index - coefficient * A * B
    H:  one factor per fresh generator,  u |--> u + P

and `H` is the identity when `m = 0`. The coefficient is BCW-11 and defaults to
one; per *generator* and not per slot is BCW-12, where two `Fresh` slots naming
one variable displace it once.

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
expressions. Version 0.3 amended this only in replacing the fixed `2` by `m`.
At `m = 0` the stabilization and `H` are both trivial and it reads
`target == G ∘ source`.

Version 0.4 amends it again, in `G`. Until now `G` subtracted
`X_u X_v`; it now subtracts `coefficient * X_u X_v`, so the step removes
`coefficient * P Q` from the target component. BCW-11 says why. Nothing that
verified before stops verifying: the coefficient defaults to one, and a step
built without it is exactly the earlier step.

**BCW-2 — Dimension and generators.** `target.dimension == source.dimension +
m`;
the generators of `target` are those of `source` followed by `variables`, in
slot order; each fresh variable satisfies RC-4 against `source.ring`.

`m` counts the *distinct* fresh variables, and each is appended
once, in the order of its first slot. Until 0.4 the two readings agreed,
because two `Fresh` slots had to name different variables. BCW-12 lifts that,
and then a step whose two slots are one fresh variable introduces one generator
and not two.

Version 0.3 amended this. Until then the step always introduced two new
generators, and `m` was fixed at 2. This is the only place in that milestone
where a binding obligation was weakened rather than extended, and it is the
reason 0.3 is a minor release and not a patch. Nothing that verified before
stopped verifying: a step with two `Fresh` slots is exactly the earlier step.

**BCW-3 — The factors are free of the fresh variables.** No polynomial of a
`Fresh` slot involves any of the fresh variables. Two consequences depend on
this: the factors of `H` commute, so their order is immaterial, and `H^-1` is
the componentwise negation, which is what `transport()` uses. A `Carried` slot
satisfies this automatically, because its value comes from a
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

`G` is elementary in every case. Its displacement `-A*B` is free of
`X_index` exactly when neither slot names `index`, which BCW-10 requires. At
`m = 0`, `H` is the identity, so the check on `H` establishes nothing.

**BCW-6 — The declared filtration level is attained.** `filtration_level ∈
{0, 1}`, `H.is_in_EA(filtration_level)` holds, and `G.is_in_EA(1)` holds.

At `m = 0`, `H` is the identity. The identity lies in every `EA^d`,
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
with zero, a point gains one coordinate per fresh *generator*, in slot order,
and the image gains a zero per generator. Since BCW-12 the two readings differ:
a step whose slots name one coordinate has two `Fresh` slots and one generator,
and appending twice is what it did until an assembly of the
nineteen-dimensional chain caught it. The image is then reduced by `G`, which
scales the removed product by the coefficient of BCW-11:

```
a  |-->  (a, -P(a), -Q(a)),        c  |-->  (c, 0, 0)
```

which is `H^-1` applied to the padded point and `G` applied to the padded
image. Any constant fill would do — the points must merely share it — and the
contract fixes zero, because a non-zero fill `(s, t)` moves the image component
`index` to `c_index - coefficient * s * t` and buys nothing.

A `Carried` slot appends nothing to a point, because it adds no
coordinate. It does affect the image. `G` reduces component `index` of the
padded image by the weighted product of the two slot values at that image: `0`
for a `Fresh` slot, and `c_j` for `Carried(j)`. So for `m ≥ 1` at least one of
the two factors is zero and the image is unchanged apart from padding, as
before. Only at `m = 0` can the image move, and it then moves to

```
c_index - coefficient * c_u * c_w
```

with the `coefficient` of BCW-11. The weight was missing here and in the
implementation until `0.4.0rc2`, and no test caught it because every collision
image in the suite had zeros in its carried coordinates, where a product
remembers no factor. This is the only respect in which reusing a coordinate
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

`SUPPLIED` states that the target was not produced by this library in this
run. It says nothing about who computed it, and a review should not read more
into it. A target may come from a published source, from a second
implementation in this repository, or from a hand computation; the label is the
same in all three cases, and where it came from belongs in the test that holds
it.

This distinction is the central result of milestone 0.2 and has to remain
visible to any audit.
For a `SUPPLIED` step, BCW-1 compares an externally computed map against the
formula and can fail. For a `CONSTRUCTED` step it compares the implementation
against itself and cannot: it is a self-check, not evidence. `Reduction`
propagates the weaker provenance of its steps.

**BCW-11 — The coefficient is part of the step and is recorded.**
`G` subtracts `coefficient * X_u X_v`, for a non-zero constant of the
coefficient domain, and the step reports it. It defaults to one.

This is an extension beyond the paper, and is marked as one for the same reason
carrier reuse is: Chapter II, Proposition (3.1) removes a product and nothing
scales it. The extension is elementary all the same -- `X_i |-> X_i - c X_u X_v`
displaces `X_i` by a polynomial free of `X_i`, so `G` is still exhibited under
BCW-5 -- and it is needed. The published nineteen-dimensional map is reached by
a chain whose steps carry the coefficients `3, -3, 7, 9, 6, -1, -6` among
others, and no single change of coordinates removes them: solving the diagonal
that would absorb them gives two contradictions, at step 7, which needs `1/7`
where the earlier steps force `1/9`, and at step 9, which needs `1` where they
force `1/2`.

The coefficient is a constant by the same rule as TRA-2 and BCW-3: it is
converted into the coefficient domain, so a coefficient involving a generator
cannot be built. Zero is refused, because a step that removes nothing is the
identity written at length.

**BCW-12 — Both slots may be one fresh variable.** Two `Fresh` slots
may name the same variable, and then they must carry the same polynomial. `G`
subtracts `coefficient * X_u^2`, and `H` displaces `X_u` once.

Also an extension, and the one the published chain forced. Its fifteenth step
is `F_x -> F_x - 3 (w3 + x y^2)^2`, which removes `3 x^2 y^4` and leaves the
terms in `w3^2`. Until 0.4 the constructor refused it, and correctly under the
model it had: a chain needing it was unreachable rather than unfound.

The symmetry with BCW-10 is exact and worth stating. Two `Carried` slots have
been allowed to name one coordinate since 0.3, where `G` is `X_i - X_j^2`. Two
`Fresh` slots naming one variable is the same shape one step earlier, and there
was no reason for the two to differ beyond the order they were written in.

**BCW-10 — A reused slot names a carrier.** For `Carried(j)`:
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

BCW-1, BCW-2, BCW-6 and the third clause of BCW-10. BCW-3, the
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
them — storing both a factorization and the automorphisms built from it would
allow
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

The first factor is `TranslationStep`, and the refusal names it.
Until 0.4 the message named a step that did not exist, which was honest about
the gap and useless for closing it. `normalize()` still refuses; it does not
insert a translation of its own. Proposition (1.1) has three factors and a
`Reduction` shows all three, rather than folding two of them into one step
whose name mentions only one.

### Which of these can fail on supplied data

LIN-1 and the first clause of LIN-6. LIN-2 and LIN-3 follow from LIN-1 and can
only fail if the library is wrong about its own arithmetic; the second clause
of LIN-6 follows from the first. They are retained as cheap self-checks, and a
review should weigh them as such rather than as evidence about a supplied
target.

---

## TranslationStep

The first factor of BCW Chapter II, Proposition (1.1). A `Step`, so
that a `Reduction` can begin at a map that does not fix the origin. Implemented
in work package 2 of this milestone.

```python
@dataclass(frozen=True)
class TranslationStep:
    source: PolynomialMap
    target: PolynomialMap
    shift: tuple[sp.Expr, ...]
    normalizing: bool
    provenance: Provenance

    @classmethod
    def build(cls, source, shift, normalizing=False) -> TranslationStep: ...

    @classmethod
    def normalize(cls, source) -> TranslationStep: ...

    @property
    def translation(self) -> ElementaryAutomorphism: ...
```

The step composes `X |-> X - shift` on the left. `normalize()` sets
`shift = source(0)`, which is the only case a reduction needs, and `build()`
admits any constant shift.

As for `LinearStep` and `BCWStep`, `provenance` is recorded rather than given:
the public constructor always sets `SUPPLIED`, and `build()` and `normalize()`
are the only routes to `CONSTRUCTED`.

### Why a separate type

A translation is affine and not linear, so it is not an element of `GL_n(k)`
and cannot be a `LinearAutomorphism`. Widening that type to affine maps would
break the two things it exists for: `matrix()` and the structural determinant.

Nor is it a `BCWStep`. It is elementary in the sense of the paper —
`X_i |-> X_i - c_i` displaces `X_i` by a constant, which is free of `X_i` — so
it needs no new non-elementary type, and `translation` exhibits it as an
`ElementaryAutomorphism` with one factor per non-zero entry of `shift`. What it
is not is an application of Proposition (3.1): it removes no product, names no
target component, and buys no carrier. Recording it as a `BCWStep` with both
slots `Carried` would state three things that are not the case.

**TRA-1 — The identity.** `target == translation ∘ source`, that is,
`target.components[i] == source.components[i] - shift[i]` for every `i`, as a
polynomial identity in one shared `PolyRing`.

**TRA-2 — The shift is constant.** Every entry of `shift` lies in the
coefficient domain of `source.ring` and involves no generator. Enforced at
construction and by conversion rather than by inspection, in the shape of
BCW-3: the entries are converted into the domain, so an entry involving a
generator cannot be built at all, and TRA-2 has no verify-time code.

Symbols of the coefficient domain are permitted, as in COL-2 and BCW-3: a
translation by `T` over `k[T]` is a translation. What the obligation excludes is
a shift that varies with the point, which would not be a translation and whose
Jacobian would not be the identity.

**TRA-3 — Invertibility is exhibited, not asserted.** `translation` is checked
to be a product of elementary factors whose polynomials do not involve their own
variable, and `translation.inverse() ∘ translation` is checked to be the
identity map. The inverse is `X_i |-> X_i + c_i`, read off the definition.

**TRA-4 — The determinant is unchanged.** `target.determinant() ==
source.determinant()`. The Jacobian of a translation is the identity matrix.
Redundant in principle and retained as a cheap self-check, in the shape of
BCW-7.

**TRA-5 — The step establishes no `EA` level.** `filtration_level` is
`math.inf`. The transformation has filtration degree `-1` and lies in no
`EA^d`; the step therefore constrains nothing about its target's filtration
stage, and `Reduction.filtration_level()` is not lowered by it. The reasoning
is under [The Step protocol](#the-step-protocol).

**TRA-6 — Normalization is a claim, not a definition.** If the step declares
itself the normalization, `shift == source(0)` and `target` lies in `MA^0`. A
`TranslationStep` that is not so declared carries no such obligation. This is
LIN-6 one stage earlier, and for the same reason: a step that says what it is
for can be held to it.

A source already in `MA^0` is not refused. Its shift is zero, the target equals
the source, and the step is the identity — a true statement, and simpler than a
special case in every caller that does not know in advance whether its map fixes
the origin.

**TRA-7 — Transport.** Points are unchanged; the image becomes
`c - shift`. Left composition does not move preimages, as in LIN-5.

**TRA-8 — Provenance is recorded, and not settable.** As BCW-9, with the same
reading: an integrity marker against mislabelling by accident, not a security
boundary.

### Which of these can fail on supplied data

TRA-1 and the first clause of TRA-6, which compares the shift against `F(0)`.

This is narrower than the wording this section carried when it was written,
which named both clauses of TRA-6. The implementation showed why. The `MA^0`
clause follows from TRA-1 together with the first clause: if the target is the
source translated by `F(0)`, it vanishes at the origin. It is retained as a
self-check and carries `# pragma: no cover`.

TRA-3 and TRA-4 follow from TRA-1 in the same way and can only fail if the
library is wrong about its own arithmetic. TRA-2 is a constructor invariant and
is not reachable by `verify()` at all. TRA-5 is a property of the type rather
than a check.

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

A chain's dimensions do not grow by two at every BCW step: with
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

A `TranslationStep` reports `math.inf` by TRA-5 and therefore does
not lower it, as a `LinearStep` does not. A chain that begins at a map outside
`MA^0` reports the same level as the same chain begun one step later, which is
the intended reading: the level describes the target, and the translation is
about the source.

**RED-7 — Provenance propagates.** `Reduction.provenance` is `SUPPLIED` only if
every step is `SUPPLIED`.

**RED-8 — Value semantics.** `steps` is a tuple; concatenation and slicing
return new `Reduction` objects; nothing mutates.

---

## Search

Assembling a `Reduction` rather than checking one that is presented.
The milestone target is the step sequence of the published 19-dimensional map,
which its source does not publish.

The search is the first part of this package that produces a chain instead of
checking one, and the obligations below exist mostly to keep that from being
read as more than it is. A found chain is not evidence because a search found
it. It is evidence because `Reduction.verify()` passes on it and because its
endpoint equals a map this library did not compute.

### What is searched, and what is given

The task is bounded on both ends. The source is Alpöge's three-dimensional map,
the target is the published nineteen-dimensional map, and both are fixed input.
What is unknown is the sequence between them: seventeen steps and sixteen fresh
generators, so `sum(m) == 16` over the seventeen steps and at least one step has
`m = 0`.

The names of the fresh generators are given too. This is a decision, and the
alternative is worth stating because a reader will otherwise assume it. A search
that allocated its own names through a `ReductionContext` would introduce them
in the order it discovers them, and BCW-2 puts the generators of a target in
that order, which need not be the order the published map lists them in. The two
maps would then be equal in no sense the package can check without a second
notion of equality. Giving the search the names and letting it search their
*assignment to steps* keeps one notion of equality, and leaves the remaining
difference a matter of presentation, which SEA-4 handles.

This clause was argued from a stronger premise than survives. It said the
published numbering *is not* the introduction order, on the evidence that the
fifth component uses `w13` and `w9`. That component is `w2`'s, and it is a
residue rather than an introduced value; with that corrected, every dependency
points to a smaller index and `w1` to `w16` is a valid introduction order. The
decision stands on the weaker premise, which is all it needed: the two orders
*need not* agree, and a search that assumed they did would be assuming its
answer. If they do agree, `reordered()` returns the map unchanged and nothing is
lost.

**SEA-1 — The search is not trusted.** It returns a `Reduction` or reports that
it found none. Nothing about the search is part of any certificate, and
`Reduction.verify()` is called on the result rather than assumed. A search that
returns a wrong chain is caught by verification, not by the search.

**SEA-2 — Determinism.** A search is a pure function of its arguments. Two runs
with value-equal arguments return equal results, in the same process, in a later
process, and in a different interpreter run. Dependence on `id()`, on set or
dict iteration order, on wall clock or on a random seed that is not an argument
is forbidden. This is RC-1 for a larger object and for the same reason: a chain
that cannot be replayed is not a certificate anyone else can check.

**SEA-3 — Fresh generators are data.** The names of the fresh generators are
supplied to the search. It decides which name belongs to which step, not what
the names are. Each satisfies RC-4 against the source's ring, as it would if a
context had produced it.

**SEA-4 — Reordering is presentation, and is not a step.** Implemented in work
package 3 of this milestone, ahead of the search, so that a failure there
cannot have its cause here. A chain built by the
search has its generators in introduction order. `PolynomialMap.reordered(vars)`
returns the same map with its generators listed in the given order, permuting
the component tuple by the same permutation. `vars` must be a permutation of the
map's own variables; anything else raises `ValueError`.

This changes no polynomial and no value. Coordinate `i` of the result is the
coordinate of the argument that carries the same generator, together with the
component that belongs to it, so the two objects describe one map on `k^n` and
differ only in the order the coordinates are listed. That is why it is not a
`Step` and certifies nothing: there is nothing to certify. Making it a step
would put an entry in a chain that verifies an identity between two spellings of
one object, which reads like evidence and is not.

**SEA-5 — The evidence is the endpoint.** A chain the search produces is
`CONSTRUCTED` throughout, so by BCW-9 its BCW-1 compares the implementation
against itself. The external fact is

```
found.target.reordered(published.variables) == published
```

checked separately from `verify()`, and the only place where the run can be
contradicted by data this library did not compute.

The diagonal is withdrawn from this clause. Between work packages 7
and 10 it read `conjugate(found.target.reordered(...), D) == published` for a
diagonal `D` the search reported. BCW-11 makes it unnecessary: with the
coefficient inside the step, the family of steps is closed under conjugation by
a diagonal, since conjugating `(t, a, b, lambda)` by `D` gives
`(t, a, b, lambda d_t / (d_a d_b))` with the factor values scaled by their own
entry. A chain that reached the target only up to `D` is therefore itself
expressible as a chain that reaches it exactly, and equality costs nothing: the
peel *solves* for the constant rather than searching it, and the forward search
takes its values from the pool verbatim. Keeping `D` would leave two ways to
say the same thing, one of them weaker.

`conjugate` and `diagonal_matching` remain and carry no obligation. They answer
a question still worth asking -- in what respect two chains that are the same
reduction differ -- and nothing that `verify()` or this clause asks.

The clause went through two widenings before it was withdrawn, and both stay on
the page because each was a measurement. `D` was restricted to ones and minus
ones, which was too narrow: at the map where the peel stopped, no coordinate
could be undone with `+1` or `-1`, and admitting any non-zero entry took it from
depth six to depth eleven. Then BCW-11 made the clause unnecessary altogether.
The first widening was right, and the second is why it stopped mattering -- a
scalar the step cannot carry has to live somewhere, and `D` was where it
lived. It is checked separately from `verify()` and is the only place where
the run can be contradicted by data this library did not compute.

`D` entered in work package 7, forced by the data. Component 2 of the published
map carries `+w13 w16`, and this library's `G` subtracted `X_u X_v` always, so
no choice of factors reproduced it. The published map is reached
under `G = X_i + X_u X_v`, and the two conventions are related by

    S+(-P, Q) = D_u o S-(P, Q) o D_u^-1,

verified componentwise, where `D_u` flips one slot coordinate. So the second
convention reaches no map the first does not, up to conjugation by a signed
diagonal, and implementing it would add a per-step degree of freedom inside
`BCWStep` — inside the verification surface — to reach maps already reachable.
`D` keeps that freedom in the search, which SEA-1 already declines to trust.

`D` cannot absorb an error. Every monomial of every component is one equation
over GF(2) for the signs, so the system is heavily overdetermined: nineteen
components against nineteen unknowns for the milestone target, and six of its
equations are readable from the published map before any chain exists. The
minimum weight consistent with those six is three, so `D` is not the identity
and is not free either. It is read off and then checked, not fitted.

Conjugation preserves what the comparison is about: degree, order, filtration
degree, and the constant Jacobian determinant of a Keller map. Two conjugate
maps are the same map in different coordinates. A review should read
the two as different in kind: verification says the chain is internally sound,
and this equality says it arrives where an outside source says it should.

The transported collision is a second such fact. `Reduction.transport()` carries
Alpöge's three points to `k^19` by RED-5, and the result, reordered, is compared
against the published table. The two facts are independent: one is about the
map, the other about three points of it.

**SEA-6 — A failure to find is not a proof of absence.** Reporting no chain
means this search did not find one with these arguments. It is not a statement
that no chain exists, and nothing in the package turns it into one. See
"No completeness" under
[Deliberate non-obligations](#deliberate-non-obligations).

**SEA-7 — Deferral is explicit.** A structural case the search does not handle
raises `NotImplementedError` naming the work package, rather than returning a
plausible chain or silently reporting no result. A case it handles and does not
solve reports no result, which is a different outcome and is spelled
differently.

**SEA-14 — The forward search builds unweighted steps with distinct fresh
coordinates, and says so.** It reaches a proper subset of the chains
`BCWStep` admits, and the two omissions are structural rather than incidental.
A step with a coefficient other than one is outside it, because
`enumerate_candidates` divides a displacement into two factors under SEA-9 and
SEA-10 and a division has no place to put a weight. A step whose two slots name
one fresh coordinate is outside it as well, because a candidate carries two
factors and SEA-8 gives each of them a name from the pool.

Naming the boundary is the obligation; moving it is not. `search()` reports no
result for a chain that needs either, and that is the correct outcome under
SEA-6 rather than a deferral under SEA-7: the case is handled, the space is
searched, and the chain is not in it. What would be wrong is leaving a reader to
discover the boundary from a failed run, so `search()` states it, this clause
states it, and `tests/test_admissible_shapes.py` exercises it against every
shape the step type admits.

Peeling has neither restriction. It solves for the coefficient instead of
dividing, and reads a fresh coordinate's name off the target instead of a pool,
so REV-1 to REV-12 cover what SEA-14 excludes. A chain outside the forward search
is not outside this library.

**SEA-11 — A budget is reported, not hidden.** The search examines at
most a stated number of maps and says how many it examined and whether the
space it covers was exhausted. A result with `exhausted` false says less than
SEA-6 already allows: not merely that nothing was found, but that the search
did not finish looking.

**SEA-13 — A factor outside the pool costs a rewrite, and rewrites are
counted.** A fresh slot whose factor is a pool value, up to sign, takes
that name. A fresh slot whose factor is *not* a pool value may take any unused
name, and at most `rewrites` slots in a chain may do so.

The rule exists because SEA-8 bounds the anchor and leaves the co-factor free,
while a fresh co-factor still needs a name, and the only names on offer are the
target's. A coordinate named this way cannot end the chain carrying what the
target publishes, so a later step has to rewrite its component — which is what
`alpoege15` does at component 10 and what the published nineteen-dimensional
map does at `w2`.

Two halves of the rule are decisions rather than facts. A factor that matches a
pool value takes that name, although a coordinate carrying a value the target
publishes need not be the coordinate that publishes it; and `rewrites` bounds
how often the other case may happen. Both are there to keep the branching
payable, and the measurement says how much they are worth: recovering the
fifteen-dimensional map costs 62 maps with `rewrites=0` and does not finish
within 400 with `rewrites=1`, on the same complete pool. Allowing a rewrite is
not a small loosening.

**SEA-12 — The walk is bounded by stated rules, and they are decisions.**
 The degree never rises along a chain, the dimension never passes the
target's, and at most `spare` steps introduce no generator. None is a fact
about Keller maps. Nothing obliges a step to lower the degree — see "No
progress measure" — and the first rule is adopted because degrees do not rise
along either reference chain and a chain that does not converge on a cubic
target cannot reach one. A chain outside these rules is unreachable here, in
the sense of "No completeness of the enumerator either".

`spare` is what bounds the length of a chain: every other step consumes a name,
so a chain has at most `len(pool) + spare` steps. It is also what lets a chain
*end* with a step that introduces nothing. Reaching the target is therefore
tried as soon as every name is spent, and the walk continues afterwards while
any spare step is left.

That last clause is a correction, and the run that forced it is worth
recording. A search whose walk stopped at the last introduction reported the
space exhausted without a chain after 68425 maps — a clean negative result
about a space that could not contain the answer, since the published
nineteen-dimensional map grows by sixteen dimensions over seventeen steps and
its `w2` component is the residue of exactly such a step. An exhausted space
says something only about the rules that defined it, which is why they are
written down here rather than left in the code.

Every one of these bounds is a whole non-negative number, and a caller who
passes anything else hears about it rather than receiving a result built on it.
A negative budget produced `examined = -1` and a fractional one produced
`examined = 1.5`, neither of which is the count `SearchOutcome` and
`PeelOutcome` declare. `True` is refused with them, since `bool` is a subclass
of `int` and a budget of one map is almost certainly a slip. `enumerate_candidates`
is public and makes the same check on `selection_limit`; until `0.4.0rc9` it did
not, so the same value was refused through `search` and accepted directly.

### Candidates

The search enumerates the arguments of `BCWStep.build` — a target component and
two factor slots — against a map it has reached. No new type is required for
that, and none is introduced unless the implementation shows one is needed; if
one is, it carries no `verify()` and therefore no numbered obligations, in the
shape of `LinearAutomorphism`. A candidate is a proposal. It becomes a
certificate by being built and verified, and by nothing else.

The three obligations below were added in work package 5, after a measurement
the plan for this milestone had left open. They narrow what the enumerator
claims, and each is there because the unrestricted version is either infinite or
unaffordable.

**SEA-8 — The value pool is data.** The polynomials the enumerator may use to
*anchor* a candidate are given to it. It does not invent them and does not
search for them.

This is narrower than the wording of work package 5, which said the pool bounds
every `Fresh` slot. Work package 6 measured that, and it is false. One factor of
a candidate is an anchor, from the pool or from a coordinate that already
carries it; the other is obtained by dividing the component and is *free*. The
stronger reading was tested and yields nothing: at the first map of the
`alpoege15` chain, no pair of pool values has a product that is a subsum of any
component. Zero candidates, against an average of 122 per map for the rule as it
now stands.

The reason is visible in the reference chain. Step four of `alpoege15`
introduces `x1^2 x2 x3 + 3 x1 x2^2 + 3 x1 x3 + 7 x2`, and the published
fifteen-dimensional map does not carry that value: step seven acts on component
10 and rewrites it. A pool read off a final map is therefore not the set of
factors its chain used, wherever a later step targets a carrier.

What survives is the bound that matters. A carrier value is available only once
the map has the generator it names, so `w6 = w1 x` does not convert into the
ring until `w1` exists, and the dependency order falls out of the arithmetic
rather than being imposed. The sixteen carrier values of the published
nineteen-dimensional map are readable from the map itself, as
`components[3 + j] - w_j`:

    w1  = y^2 z    w5  = x^2 y    w9  = x y     w13 = x^2
    w3  = x y^2    w6  = w1 x     w10 = w2 z    w14 = w7 y
    w4  = y z      w7  = y^2      w11 = w3 y    w15 = w8 y
    w16 = x z      w8  = w4 x     w12 = w6 x
    w2  = -w13 w9 - w13 x y - w9 x^2

A `Fresh` slot introduces `X_u + P`, so these sixteen polynomials are the
sixteen factors the seventeen steps supplied *if* no step rewrote a carrier
component afterwards. What the search has to find is their order, the co-factor
each was paired with, and the component each step acted on.

**The condition under which a pool read off a target carries.** Every step has
at least one factor that no later step overwrites. It is a statement about a
chain and not about Keller maps, and it is the assumption the whole pool
construction rests on, so it is named here rather than left implicit.

It does not hold for `w2`. The component of that carrier is not an introduced
value but the residue of a later step, with `w13` and `w9` in the two slots and
`x^3 y` removed; `tests/test_alpoege19.py` verifies the identity and a
perturbation of it. The value `w2` was introduced with is therefore absent from
the pool.

The consequence is sharper than it first looks, and `alpoege15` shows it.
Step seven of that chain acts on component 10 and rewrites it, so the value
that coordinate was introduced with is not in its published map either. A
search given only the published carrier values does not fail to find the chain:
it cannot express it, because a fresh coordinate needs a name and the only
names on offer are the published ones. Supplying the one missing value turns a
budget spent for nothing into a chain found after 62 maps. Both runs are in
`tests/test_alpoege15.py`, the second as the negative control.

What makes the assumption plausible here is a degree bound rather than anything
structural. Degrees do not rise along either reference chain, so every removed
product has degree at most 7 and `min(deg P, deg Q) <= 3`; a factor of degree at
most three needs no reduction towards a cubic map. Measured across all fourteen
known steps, exactly one factor per chain is missing from the pool, and in both
cases it is the single factor of degree 4, whose partner of degree 3 is present.

The bound is a property of this example. For a source of degree `d` it gives
only `min <= floor(d / 2)`, which says nothing from degree 8 upward, and nothing
obliges a chain to leave a small carrier alone in any case — see "No progress
measure". Searching without this assumption means giving up the pool and
enumerating factorizations of subsums, which is what SEA-8 exists to avoid. That
is 0.5's problem, where the target is not known either.

**SEA-9 — An anchor is used verbatim, and the scalar goes to the co-factor.**
`(P, Q)` and `(cP, c^-1 Q)` remove the same product for any unit `c` of the
coefficient domain, so without a rule the enumerator would emit one candidate
per unit, which over a field is infinitely many.

The rule is not a tie-break between equals. The two steps have *different*
targets, whose fresh coordinates differ by a scaling, and the anchor says which
of them is wanted. Step one of the `alpoege15` chain is recorded as
`Fresh(-x1 x3 / 2), Fresh(x1^2)` and appears in the enumeration as the same
product with the scalar on the other side, because the anchor is taken verbatim
and the division puts the scalar into the quotient.

Two further factors are excluded outright, each because the step would not
build. A constant may be neither anchor nor co-factor: `H` displaces a fresh
coordinate by its factor, so a factor of order zero puts `H` outside `EA^0` and
BCW-6 refuses the step at either admissible level. And a `Carried` slot on the
component the step acts on is never offered, which the constructor of `BCWStep`
refuses in any case. Moving a refusal from the enumerator to the constructor
would not make it less certain, only later.

**SEA-10 — A proper part of the co-factor is a candidate too.** The enumerator
does not offer only the largest `Q` for which `P Q` is a subsum of the
component.

Measured against a known chain. Step two of `alpoege15` uses
`Q = x1 x2 x3 + 3 x2^2`, while the largest admissible co-factor at that map is
`3 x1 x2 x3 + 9 x2^2 + 6 x3`. The step leaves a term behind, so an enumerator
restricted to the largest co-factor would miss a step that demonstrably exists.

Every selection is checked to be a subsum in its own right. Dropping terms from
`Q` is not a safe operation: cancellation inside `P Q` can hide a monomial that
reappears once a term is removed, so the smaller product can fail where the
larger one held. `(x - y)(x + y)` is a subsum of `x^2 - y^2`; the part `x` of
the co-factor gives `x^2 - x y`, and `-x y` is not there.

What is divided is the *displacement* `F_i - X_i`, not the component. A product
containing the term `X_i` itself would leave a target whose `i`-th component is
no longer `X_i` plus something. The arithmetic of BCW-1 would hold, and the map
would leave the shape every later step assumes.

### The control, and what it costs

The seven steps of the `alpoege15` chain and the seven of `bcw17` are known, and
the enumerator must contain each of them at the map that precedes it, with the
final map supplying the pool, and must derive the filtration level each step
declares. An enumerator that misses a step which demonstrably exists is
incomplete in a way that a search failure alone would not reveal.

The count is a correction. This page said eight for `bcw17`; there are seven,
which is what the dimension requires, since `bcw17` grows from 3 to 17 and every
one of its steps introduces two generators.

The control passes for all fourteen, and the derived level agrees with the
declared level in all fourteen. The level is derived rather than searched: `H`
displaces the fresh coordinates by the factors, so its filtration degree is one
below the smallest order among them, reported as 1 wherever BCW-6's ceiling
applies.

Affordability is measured rather than assumed. Over the two reference chains the
enumerator offers between 104 and 173 candidates per map, averaging 122 and 124.
The components stay small, which is why: no component of the `alpoege15` chain
exceeds 13 terms, and the published nineteen-dimensional map has 24, 18 and 5
terms in its three non-carrier components, 4 in the carrier component of `w2`,
and 2 in each of the remaining fifteen.

`selection_limit` caps the number of terms a quotient may have before its parts
are skipped and only the whole quotient is offered. It guards against a
pathological component rather than against the data: no quotient in either
reference chain comes near the default of 8.

For contrast, the enumerator SEA-8 rules out. Free choice of `P` means choosing
a subsum of a component and a way to split it, which at 13 terms is 8192 subsums
before any factorization, per component, at every node of a seventeen-level
search.

### Which of these can fail on supplied data

SEA-5, and only SEA-5. It compares a chain this library built against a map and
a collision it did not. SEA-1 to SEA-4 and SEA-6 to SEA-14 are obligations on
the library's own conduct: they say what the search and its enumerator may
claim, not what the data is. A review weighing this milestone should look first
at SEA-5 and at the provenance of the two published objects it compares against,
which `references.md` records.

---

## Peeling

Assembling a chain from the far end. The forward search of SEA-1 to
SEA-13 exhausts its space against the published nineteen-dimensional map
without a chain and cannot say which of its rules emptied the space. Peeling
runs the other way, and the reason it is a separate surface rather than a flag
is that undoing a step is a different operation from building one.

**REV-1 — Peeling needs the target and nothing else.** No value pool, no
supplied names, no sign convention. The factors fall out of the arithmetic
instead of being given, so SEA-8 and SEA-13 and the failure modes they carry do
not apply here. That is the point of the surface, not a convenience: those two
obligations are where a forward search silently loses a chain.

**REV-2 — A coordinate may be peeled only if it occurs in exactly two
components.** A step that introduces `X_u` leaves it in its own component, as
`X_u + P`, and in the residue of the component it targeted. A coordinate
occurring anywhere else was read by a later step and cannot be the last one
introduced.

This is the whole reason peeling is cheaper. Six of the sixteen carriers of the
published map satisfy it, against the hundred and forty candidates the forward
enumerator offers at a map of that size; `tests/test_alpoege19.py` records
which six and what their steps targeted.

**REV-3 — Undoing is exact, and needs no inverse.** A step subtracts the
product of its two slot *components*, so

    F_i = F'_i +- F'_a F'_b

recovers the map before it, and every peeled coordinate must then occur in no
remaining component. The second half is the check: a coordinate that survives
the undoing was not introduced by the step that was undone.

**REV-4 — The constant is solved, not guessed, and it belongs to the step.**
Undoing a step adds some non-zero constant times the product of its two slot
components. The constant is fixed by the requirement that the dropped
coordinates vanish, which is linear in it, so it is computed and each step
reports the value it used.

That constant is the `coefficient` of BCW-11 and nothing else. Until
work package 10 it was an entry of the diagonal of SEA-5, solved for and carried
alongside the chain, because the step had nowhere to put it. It now goes into
the step the peel rebuilds, and the multiplicative system that turned the
constants into a diagonal is gone rather than kept beside a second answer.

It was two signs until work package 10, and both measurements are worth keeping.
With `+` alone the published map peels to dimension 18, with `-` alone to 17,
with both to 15 -- so the constants are mixed, and restricting them to signs is
a restriction. Solving instead of trying two took the peel from depth six to
depth eleven, which is what showed the restriction was also wrong: at the map
where the sign version stopped, six coordinates satisfy REV-2 and not one of
them can be undone with `+1` or `-1`.

What the constants were used for, and no longer are: read in the order the
chain was built, each step introduced its fresh coordinates as new unknowns
while its target and any reused coordinate were fixed, so `f = d_i / (d_u d_v)`
solved by substitution and peeling produced `D` while it ran. That was worth
having when the step could not carry a scalar. Now the substitution has one
step: the constant is the coefficient.

**REV-5 — A peel is not a certificate.** The chain a peel finds is rebuilt
forwards with `BCWStep.build`, verified, and only then is it a `Reduction`.
Peeling and building are different operations, and that they agree is checked
rather than assumed. The endpoint comparison of SEA-5 is unchanged: what
carries weight is still that the chain arrives at a map this library did not
compute.

**REV-6 — Budget and depth are reported.** As SEA-11, and for the same reason:
a peel that stops says nothing unless it says how far it got and whether it
finished looking.

**REV-8 — What the source admits bounds the last step.** A last step
that introduces one coordinate has a `Carried` slot, and that slot is never the
component the step acts on, so its component is the same before and after --
which makes it a carrier of the source as well. A source without carriers
cannot be reached by such a step, and a peel standing at one coordinate more
than the source has nowhere left to go and is discarded.

This is a statement about the source that was handed in, not a rule about
Keller maps, and it is why the arithmetic of a chain is worth doing before a
run. With `a` steps introducing two generators, `b` introducing one and `c`
introducing none, `2a + b` is the number of generators and `S = a + b + c` the
number of steps. Alpoege's map has no carriers, so `a >= 1`, and a chain of the
seventeen steps its source describes then needs `c = a + 1 >= 2`. A peel
allowing one such step cannot find that chain whatever its budget.

**REV-9 — What is left to change bounds what is left to do.** An undo
changes exactly one component. Every coordinate that survives the whole peel is
a coordinate of the source, so each of those whose component still differs from
the source's needs at least one more step aimed at it. At most `d + spare`
steps remain, where `d` is how many coordinates still have to go, because a
step removes at least one unless it is a spare. A peel with more differing
components than remaining steps is discarded.

Sound rather than heuristic, and it bites late, which is where a peel spends
its time. Two steps from the end with all three of the source's components
still wrong, there is nowhere to go.

**REV-10 — At `m = 0` only constants that cancel a monomial are tried.** A step
introducing no coordinate is undone by adding `constant * F_a * F_b` back, and
nothing in the map fixes the constant: every value gives a map, and REV-3 has
no dropped coordinate to work with. What the peel does instead is enumerate the
constants that make one of the target component's monomials vanish, taking each
monomial the component shares with the product in turn.

That is a bound on the search and not a fact about Keller maps, which is why it
is written here rather than left in the code. Two ways a step falls outside it,
both found by external audits:

- The removed product cancelled the target component's terms exactly, so the
  two share no monomial at all and nothing is tried. Example:
  `(s + a*b + x**3, a, b, x)` and the step on `s` with both slots carried,
  whose target is `(s + x**3, a, b, x)`.
- The two do share a monomial, but the step's own constant is not one that
  cancels any of them. Example: the same source with `2*a*b`, whose target
  keeps `a*b`; the step has constant `1` and the peel tries only `-1`.

Both steps verify and neither is found. The bound applies only where the
coordinate count does not change: a step that introduces one has its constant
fixed by REV-3, in every monomial carrying the coordinate it dropped.

**REV-11 — Equal endpoints are a non-answer and not an error.** A peel that
finds the source already at the target has no step to build, and RED-1 requires
a `Reduction` to have at least one so that its source and target are defined.
The chain of no steps is therefore not representable, and `peel` reports an
exhausted space rather than raising. The same holds for a target of the source's
dimension over different generators: a legitimate pair of arguments and a
legitimate non-answer.

Both cases are decided from the endpoints alone, so both are answered before a
walk begins and neither costs an examined map. That is a clause about the
answer and not only about the timing: a case that is settled in advance must
not have its `exhausted` flag depend on the budget. It did. Until `0.4.0rc8`
the forward search made this test in its descent, so `search(F, F)` reported an
unexhausted space at a budget of one and an exhausted space at a budget of
four, for a pair whose answer was fixed before either. An external audit built
the map that shows it: a source without steps that introduce no generator has
nothing to descend into, and the omission stays invisible.

The clause binds `search` and `peel` alike. It is written here rather than in
the SEA family because it is one rule, and a second statement of it is a second
thing that can drift.

This is a clause about the shape of the answer and not about the mathematics.
`source == target` says the reduction is the identity, which is true and which
this library has no way to write down.

What can be settled in advance is fixed by what a `BCWStep` cannot change.
Six such invariants of the endpoints are checked, from the cheapest to the
dearest:

* the dimension never falls, since a step introduces two coordinates, one, or
  none, and removes none;
* the coefficient domain never changes, since a step takes its factors and its
  coefficient from the domain of its source, and `PolynomialMap` counts the
  domain as part of its identity;
* every generator of the source is a generator of every map reachable from it,
  since a step keeps the coordinates it was given and adds fresh ones. At equal
  dimensions this is the case of two maps over different generators;
* membership of `MA^0` is carried along a chain. A step builds `G o F^[m] o H`
  with `H` in `EA^0` and `G` in `EA^1` by BCW-6, and both fix the origin, while
  the extension by identity coordinates adds zeros. So `target(0) = 0` exactly
  when `source(0) = 0`, in both directions;
* the Jacobian determinant is unchanged, which is BCW-7;
* a chain of no steps is not representable, which decides the case of equal
  endpoints.

Each entry is a claim about steps, and a claim that is wrong would turn a
reachable target into a non-answer, so each names the obligation or the
property it rests on.

**The list is not claimed to be complete.** It holds the invariants a step is
required to preserve that are cheap enough to test on two maps, and it has
grown under audit twice: from two entries to four in `0.4.0rc10`, and to six in
`0.4.0rc11`. Earlier wordings of this paragraph called four entries "the whole
of what the endpoints decide", and an audit of `0.4.0rc10` produced two more
the same day. A false negative here costs a walk that was going to fail
anyway; a false positive would lose a reachable target. That asymmetry is why
the list is allowed to be short and is not allowed to be wrong.

What the audits measured, in each case: the pair was reported as an unexhausted
space at a budget of zero and as an exhausted one at a budget of one, for
endpoints whose answer was fixed before either. The coefficient domain has cost
more than a flag: a driver built its source with `over_field` while the target
lay over `ZZ`, and the forward search ran for hours in a space that could not
contain the answer.

**REV-12 — How far the degree may rise is a decision, not a theorem.** An
intermediate map of a peel may exceed the source's degree by at most `rising`,
which defaults to zero. It is a ceiling and not a direction: at `rising = 0` no
intermediate map exceeds `degree(source)`, which still admits a chain of
degrees `4, 3, 4` because none of those exceeds four. A larger value admits
chains that go above the source before coming back down.

The code carried this bound with a proof beside it, and the proof was wrong.
It read: the new terms of a step have degree at most `1 + deg Q <= deg(P Q)`
while no factor is constant, so the degree never rises. That holds when the
factors are new, and fails when a factor is a component the map already has. An
external audit built the chain, of degrees `3, 4, 3`: it steps up and comes back
down, and is refused at `rising = 0` and found at `rising = 1`.

The bound stays because it is what keeps a peel from wandering upwards
indefinitely, and because the reference reductions do not need it lifted. It is
now a stated decision like `spare` and `pairs`, and it contradicts nothing: "A
certificate certifies correctness, not progress" says a chain need not descend,
and this says which chains this search looks at.

**REV-7 — No completeness, again.** A peel that reaches no chain has shown that
this peel, under REV-2 and its budget, found none. REV-2 is a decision about
where to look and not a fact about Keller maps, so a chain outside it is
unreachable rather than absent -- the same reading "No completeness of the
enumerator either" already asks for.

### Which of these can fail on supplied data

REV-3, whose second half is a real check on the map being peeled, and REV-5,
which compares a rebuilt chain against the target. REV-1, REV-2, REV-4 and
REV-6, REV-7 and REV-9 to REV-12 are obligations on the library's own conduct.

REV-4 is worth a second look by a reviewer all the same. The constant it solves
for is now a coefficient inside a certificate rather than a presentation
detail beside one, so an error there is an error in what the chain claims.
BCW-1 catches it: a coefficient that does not fit makes the identity fail.

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
| a `BCWStep` `filtration_level` outside `{0, 1}` | `ValueError` |
| `index` outside `range(source.dimension)` | `ValueError` |
| a reused slot naming `index`, or an index out of range | `ValueError` |
| a reused slot naming a component that is not a carrier | `VerificationError` |
| `P` or `Q` that is not a polynomial over the source's ring | `ValueError` |
| two fresh variables of one name, or a name already reserved | `ValueError` |
| `variables` colliding with reserved names | `ValueError` |
| an empty `steps` tuple | `ValueError` |
| a dilation by zero or by a non-unit of the domain | `ValueError` |
| factorizing a singular matrix | `ValueError` |
| fewer than two collision points, or two equal ones | `ValueError` |
| a collision whose points and image differ in length | `ValueError` |
| a factory returning a miscounted or colliding name | `ValueError` |
| a shift entry outside the coefficient domain | `ValueError` |
| a shift whose length is not `source.dimension` | `ValueError` |
| `reordered()` given anything but a permutation of the variables | `ValueError` |
| a structural case the search does not handle | `NotImplementedError` |
| arguments of the wrong type | `TypeError` |

The scope of the `filtration_level` row is a correction. It was written for
`BCWStep`, where BCW-6 confines the declared level to `{0, 1}`, but it was
stated without naming a type. Read as a statement about `Step.filtration_level`
it was already wrong in 0.3, since `LinearStep` reports `math.inf`; with
`TranslationStep` doing the same it would be wrong twice. The obligation
`filtration_level ∈ {0, 1}` is BCW-6 and belongs to `BCWStep` alone.

Constructor-time conditions raise at construction. Conditions that require
polynomial arithmetic are checked by `verify()` and raise `VerificationError`;
construction never performs them silently.

A search that finds nothing raises nothing. It reports no result, and SEA-6 and
SEA-7 keep that outcome distinct from a case it refuses to attempt.

---

## Deliberate non-obligations

Listed so that their absence is not read as an oversight.

**No progress measure.** Nothing requires a `BCWStep` to lower the degree or
the number of top-degree monomials. Steps two and three of the reference
reduction leave the degree at seven. A certificate certifies correctness;
whether a step makes progress is a question for the search, and `Reduction`
reports degrees rather than constraining them.

The milestone number here is a correction. It read 0.5, which disagreed with
"No search" below. Progress is a question the search of 0.4 already has to
answer for one target; ranking steps in general is 0.5. Neither is a question
for a certificate, which is what this entry says and what has not changed.

**No minimality.** Nothing claims a reduction is the shortest, or the
lowest-dimensional, or that dimension 17 cannot be improved.

**No search.** *Withdrawn in 0.4.* Until then the package only verified a
factorization that was presented to it. It now assembles one as well, under the
obligations of [Search](#search). What has not changed is the division the entry
was there to protect: `BCWStep` and `Reduction` still verify and do not search,
and SEA-1 keeps the search outside every certificate. Three narrower
non-obligations take its place.

**No completeness.** A search that reports no chain has not shown that
none exists. It has shown that this search, with these arguments, did not find
one. Nothing in the package converts the one statement into the other, and a
negative result should not be quoted as if it did.

**No completeness of the enumerator either.** The enumerator is complete
relative to its value pool, and relative to nothing else. It does not offer
every `(P, Q)` whose product is a subsum of a component: that space is infinite
before SEA-9 normalizes it and exponential in the number of terms afterwards.
A step outside the pool is therefore not merely unfound but unreachable, and a
search that fails is silent about it. This is the narrower price of SEA-8, and
it is the reason SEA-6 is stated as bluntly as it is.

The price is bounded on the other side. An incomplete pool can only cause a
failure to find; it cannot produce a wrong result, because SEA-5 checks the
endpoint against a map this library did not compute. The worst outcome is a
milestone that ships the search without the sequence, which the roadmap provides
for.

**No optimality of the sequence.** A chain the search finds is one that
verifies and reaches the target. Nothing claims it is the shortest such chain,
the one the published source used, or the one with the fewest fresh generators.
Recovering *a* sequence that produces the published map is the milestone target;
recovering *the* sequence its author wrote down is not something the published
data makes checkable.

**No claim from reordering.** `reordered()` establishes nothing. It puts
two presentations of one map into one order so that they can be compared at all,
and SEA-4 says why that is not a step. The comparison afterwards is what carries
the weight.

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

The search of 0.4 relies on this and does not widen it. The
published nineteen-dimensional map shares sixteen carriers across seventeen
steps, and whether every one of them survives to the step that reuses it is a
property of that sequence, not something this page can assert in advance. If the
sequence turns out to need a factor carried by an earlier map, BCW-10 is
amended, deliberately and visibly, and the amendment gets its own work package
rather than being folded into the search.

**No injectivity claim about `source`.** `transport()` moves a collision that
is supplied. That a map *has* no collision is not something this framework
establishes.

**No global recomputation.** See RED-3. Where a test recomputes a global
invariant anyway — the determinant of the 17-dimensional map, say — it does so
as an independent cross-check, and that is a property of the test suite, not of
the certificate.
