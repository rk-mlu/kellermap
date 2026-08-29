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

**Status as of `0.5.0`:** every obligation on this page is
implemented, and the test suite covers every statement of the package. Where
the implementation forced a change, this page was amended deliberately and the
amendment is visible in the wording — the clearest cases are COL-4 and BCW-3,
which moved from obligations of `verify()` to constructor invariants, and
LIN-2, which was narrowed to what is actually checkable.

This line said `0.4.0` until milestone 0.6 opened, at which point the page had
carried the UNT and DOM obligations of 0.5 for a release without saying so. The
markers were removed when 0.5 closed and the status above was not moved with
them, which is the half of a two-part change that nothing checks.

**Milestone `0.6`, open.** The milestone adds the second and third steps of the
Reduction Theorem and the compression that follows them. Its obligations carry
the `[0.6]` marker and are not implemented; `UNI-1` to `UNI-12` are the first of
them. A review of the milestone should read them as intent that the
implementation is measured against, in the sense of the paragraph above.

**Milestone `0.5`, closed.** The milestone added the untargeted enumerator and
the search over it, UNT-1 to UNT-11, and the coefficient ring as something a
caller states, DOM-1 to DOM-4. Its obligations carried the `[0.5]` marker while
it ran and carry none now. The measurement the UNT obligations rest on stands
beside them, under "The untargeted search", because it is the reason they read
as they do.

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

One clause runs on every call, always passes, and still cannot fail: the
verification of the folded collision against `target` in RED-5. `target` is
`steps[-1].target`, and the last step has already verified its own output
against that same map under STEP-2, so the fold compares twice. It is kept as a
self-check and is marked as one in the code.

There is a third gap, narrower than either and harder to see. A check can be
reachable, executed on every run, and still be pinned by nothing: if removing
it leaves every test passing, then nothing in the repository distinguishes a
codebase that keeps the promise from one that does not. Coverage cannot report
this, because the line does run. `scripts/mutation_probe.py` asks the question
directly — it breaks one fragment, runs the suite, and puts the fragment back.
Its first run, for `0.4.0rc13`, found ten clauses in that state.

The accounting, corrected in `0.4.0rc14` after an audit did the arithmetic.
There are eight collision verifications: four `transport` methods, each
checking its input against its step's source and its output against its step's
target. One of the eight is the RED-5 clause above, which turned out to be
redundant rather than uncontrolled. That leaves **seven** uncontrolled
collision checks, which masked each other, together with the two peel bounds
REV-8 and REV-9, whose removal changes no result and only the count of maps
examined. Seven and two are the nine, and the redundant one makes ten. The page
said eight and two and called the sum nine, which is not a sum.

The ten are not re-derivable from the probes that were kept. The redundant
clause has no probe among them and cannot usefully have one, and the other nine
were fixed in `0.4.0rc13`, so the same probes against the current tree report
twelve caught. What the kept probes establish is that those controls are still
there; the ten is a record of a run, in `CHANGELOG.md`, and not a number this
repository recomputes.

The script is not a gate. A miss is a question and not a defect, and answering
it sometimes means writing on this page rather than writing a test.

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
- [UnipotentStep](#unipotentstep)
- [Reduction](#reduction)
- [Search](#search)
- [Peeling](#peeling)
- [The untargeted search](#the-untargeted-search)
- [The coefficient ring](#the-coefficient-ring)
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

## UnipotentStep

The second step of the Reduction Theorem, BCW Chapter II, Section 4, p. 306.
It doubles the dimension and makes the Jacobian of the displacement nilpotent.

```python
@dataclass(frozen=True)
class UnipotentStep:
    source: PolynomialMap
    target: PolynomialMap
    variables: tuple[sp.Symbol, ...]
    provenance: Provenance

    @classmethod
    def build(cls, source, factory=None) -> UnipotentStep: ...

    @property
    def G(self) -> ElementaryAutomorphism: ...

    @property
    def H(self) -> ElementaryAutomorphism: ...
```

It lives in `kellermap.bcw`, beside `BCWStep` and by the argument this page
already makes for that one. Proposition (3.1) is the paper's and so is this
construction; what lives at the top level is what the paper does not have, such
as a chain of certified identities.

Write `n` for `source.dimension`, `Y` for `variables`, and `F_(2)`, `F_(3)` for
the homogeneous parts of `source.displacement()` of degrees two and three. The
target is

    target = (X + F_(2) + Y,  Y - F_(3))

and what is exhibited is the factorization it comes from, at `T = 1`:

    G:  one factor per i,   X_i  |-->  X_i + Y_i
    H:  one factor per i,   Y_i  |-->  Y_i - F_(3),i

`G` and `H` are derived from `source` and `variables` and are never supplied
separately, as in `BCWStep`: storing both a factorization and the automorphisms
built from it would let the two disagree.

As for `BCWStep`, `LinearStep` and `TranslationStep`, `provenance` is recorded
rather than given: the public constructor always sets `SUPPLIED`, and `build()`
is the only route to `CONSTRUCTED`.

### There is nothing here to search for

Every step type before this one has a choice in it. `BCWStep` chooses a
component and two factors, `LinearStep` a matrix, `TranslationStep` a shift.
This step has no argument beyond the names of the fresh variables: given a
source, the transformation is determined.

That is why `build()` is the ordinary route rather than the convenient one, and
why no enumerator, no ranking and no measure belongs to this type. It also
means that what can fail on supplied data is unusual for this page, and the
section at the end says so.

**UNI-1 — The identity. [0.6]** `target == G ∘ source^[n] ∘ H`, checked as
a polynomial identity in one shared `PolyRing`, not by comparing printed
expressions.

The composition is BCW's `G(T) ∘ E(T)^[n] ∘ H(T)` at `T = 1`. The parameter
does not appear in the certificate. It carries the grading that Lemma (4.1)
needs, and the lemma is what makes the target's displacement nilpotent; the
identity this obligation checks holds without it.

**UNI-2 — The source lies in `MA^1`. [0.6]** `source.is_in_MA(1)`, that is
`ord(source - X) >= 2`.

This is the precondition of Section 4 and the one a caller is most likely to
miss, because a map can be Keller without it. `alpoege13` is: the linear part
of its displacement has the two non-zero entries `7` and `6`. They are
nilpotent, so the map is Keller, and Section 4 still does not apply to it. A
displacement term of order one carries no power of `T`, `E'(T)` is then not
`X + N T`, and Lemma (4.1) reaches nothing.

The step does not normalize its source. `LinearStep.normalize` does that, the
dimension does not move, and the collision points do not move either. A step
that quietly normalized would hide a step from the chain, and with it the
transformation a reader has to undo to get back to the map they started from.

**UNI-3 — The source has degree at most three. [0.6]**
`source.degree() <= 3`.

`E(T) = X + T F_(2) + T^2 F_(3)` has no slot for a homogeneous part of degree
four, and `H` removes `F_(3)` alone. The first stage of the Reduction Theorem
is what supplies a source of degree three, and this obligation is where the
stages meet.

**UNI-4 — The source is Keller. [0.6]** `source.determinant() == 1`.

Under UNI-2 this is Kellerness itself and not a second requirement. A map in
`MA^1` has Jacobian `I + J(N)` with every entry of `J(N)` free of a constant
term, so its determinant is a polynomial with constant term one; a determinant
that is a non-zero constant is therefore one. What the obligation excludes is a
source whose determinant is not constant at all, which UNI-2 does not exclude
and which has no Reduction Theorem to be part of.

Where the determinant becomes one is the linear normalization. Alpoege's map
has determinant `-2` and a linear part of determinant `-2`; it is not in
`MA^1`, UNI-2 refuses it, and `LinearStep.normalize` returns a map for which
both obligations hold.

**UNI-5 — Dimension and generators. [0.6]** `target.dimension == 2 * n`; the
generators of `target` are those of `source` followed by `variables`, in order;
`len(variables) == n`; and each fresh variable satisfies RC-4 against
`source.ring`.

Freshness and the count are constructor invariants and raise `ValueError`, as
the corresponding half of BCW-2 does. A certificate names the variables it
used, and a supplied target is checked against those rather than against names
invented while verifying.

**UNI-6 — Invertibility is exhibited, not asserted. [0.6]** `G` and `H` are
checked to be products of elementary factors whose polynomials do not involve
their own variable, and `G.inverse() ∘ G` and `H.inverse() ∘ H` are checked to
be the identity map. As BCW-5.

Each factor of `G` displaces `X_i` by `Y_i`, which is free of `X_i`; each
factor of `H` displaces `Y_i` by `-F_(3),i`, which is a polynomial in the
source's variables alone and therefore free of every `Y`. Within each block the
factors commute, so the order they are listed in does not matter, and `H^-1` is
the componentwise negation, which is what `transport()` uses.

**UNI-7 — The step establishes `EA^0` and no more. [0.6]**
`filtration_level == 0`, `G.is_in_EA(0)` holds and `G.is_in_EA(1)` does not.

The level is not an argument here. `G` displaces `X_i` by `Y_i`, of order one,
so it lies in `EA^0` and in no higher stage, and the construction admits no
other factorization to declare. `H` lies in `EA^2` and constrains nothing.

**UNI-8 — The target leaves `MA^1`. [0.6]**
`target.filtration_degree() == 0`.

The displacement is `(F_(2) + Y, -F_(3))` and its second block has order one.
This is a consequence of UNI-1 and is stated as an obligation because a caller
has to know it: a `BCWStep` declaring `EA^1` after this step is making a claim
about a map that is not in `MA^1`, and a second `UnipotentStep` on this target
is refused by UNI-2. What comes next is the homogenization, which is what
milestone 0.6 builds next.

**UNI-9 — The displacement of the target is nilpotent. [0.6]**
`J(target - X)` is nilpotent, checked as `det(X + T * (target - X)) == 1`
over `k[T]`.

The check is one determinant and not a matrix power. `det(I + T A) = 1` says
that every coefficient of the characteristic polynomial of `A` below the
leading one vanishes, and Cayley-Hamilton over a commutative ring then gives
`A^m = 0`. Measured on `alpoege13` normalized, which is `n = 13` and a target
in 26 variables: 2.06 seconds for the determinant over `QQ[T]`, against 0.65
seconds for the plain determinant of the target under UNI-10. The matrix power
`J**26` did not finish in twenty-five minutes, which is why the obligation is
worded around the determinant rather than around the definition.

This is redundant in principle. It follows from UNI-1 by Lemma (4.1), so it
cannot fail where UNI-1 holds, and a review should weigh it as a self-check in
the shape of BCW-7. It is checked all the same, for two reasons. It is the
property the step exists to establish, and a reader who finds the word
"unipotent" in the name of a type should find it checked somewhere. And it
reaches the determinant through the parameterized domain of DOM-1, which is a
different code path from the one UNI-10 uses, so the two together cross-check
the library's own arithmetic.

If a later measurement makes this the dominant cost of a chain, it moves behind
an argument and this page says so. It is not moved on a guess.

**UNI-10 — The determinant is unchanged. [0.6]** `target.determinant() ==
source.determinant()`. Redundant in principle, since every element of `EA_n(k)`
has determinant one, and retained as a cheap self-check in the shape of BCW-7.

**UNI-11 — Transport. [0.6]** With `source(a) = source(b) = c`, and the fresh
coordinates filled so that the two points share the fill,

```
a  |-->  (a, F_(3)(a)),        c  |-->  (c, 0)
```

which is `H^-1` applied to the padded point and `G` applied to the padded
image. The fill is fixed at zero, as in BCW-8, and here it is not free of
consequence for the image: a fill `y` shared by both points sends `c` to
`(c + y, y)`, which is a true statement and a longer one.

The second block of the point is `F_(3)(a)` and not `-F_(3)(a)`. `H` displaces
`Y` by `-F_(3)`, so `H^-1` displaces it by `+F_(3)`; the sign is opposite to
BCW-8's `(a, -P(a), -Q(a))` for exactly that reason, and the two are easy to
confuse.

Distinctness is preserved without an argument about the second block: two
distinct points of the source already differ in the first block, so their
images under `H^-1` differ there too. STEP-4 therefore holds for any number of
points, and the three points of Alpoege's collision stay three.

**UNI-12 — Provenance is recorded, and not settable. [0.6]** As BCW-9, with
the same reading: an integrity marker against mislabelling by accident, not a
security boundary.

### Which of these can fail on supplied data

UNI-1 for a supplied target, and UNI-2, UNI-3 and UNI-4 always.

The last three are the unusual entry on this page. Everywhere else, a
`CONSTRUCTED` step compares the implementation against itself and its
obligations become self-checks. These three constrain the *source*, which is
supplied on both routes, so `build()` cannot make them true and does not try.
A `CONSTRUCTED` `UnipotentStep` is therefore evidence about its source in a way
that a `CONSTRUCTED` `BCWStep` is not evidence about anything.

UNI-5 in its freshness and counting half is a constructor invariant and is not
reachable by `verify()`. UNI-6, UNI-9 and UNI-10 follow from UNI-1 and are
retained as self-checks that localize an error to the step that made it.
UNI-7 and UNI-8 are properties of the type rather than checks on data.

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

Of the three parts, the first can fail on supplied data and the third cannot.
A caller brings the collision, so the check against `source` is the one that
catches a collision of the wrong map — and it is the fold's own and not the
first step's, because a failure there would otherwise be located at step 0 and
blame a step at which nothing is wrong. The check against `target` compares
against `steps[-1].target`, which the last step has already verified its output
against under STEP-2; it is a self-check.

`transport()` does not call `verify()`. On a supplied step whose target is
wrong, the output check inside that step is therefore the only thing between a
false certificate and an apparently machine-checked non-injectivity of its
target. That is reachable, and since `0.4.0rc13` it has a control of its own
for each step type.

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
context had produced it: a symbol, distinct from the others by name, and not a
name the source's ring has already taken.

Checked since `0.4.0rc12`, and before that written down and assumed. A pool
naming a generator of the source was accepted, and the search then looked for
steps introducing a coordinate that already existed. The check runs before
REV-11 is consulted, so that whether a pool is valid does not depend on whether
the endpoints settle the pair. An audit of `0.4.0rc11` found both halves: the
missing check, and that the checks which did exist ran after `settled` and were
therefore skipped whenever it answered.

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

Exact means over the coefficient domain of the map and not over some larger
one. A constant that does not belong to that domain names no step over this
ring, so undoing with it is a non-answer and not an error, which is the answer
REV-10 gives when a move cannot be offered for the same reason. The clause is
added in work package 4 of 0.5, where the arithmetic moved from expressions
into the ring and made the case reachable: before, such a constant was carried
through an expression and raised out of the search when the map was rebuilt.

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

## The untargeted search

`search` and `peel` both need a target. An untargeted search has only a source
and the instruction to reach degree three, so nothing tells it which step to
take. This family says what such an enumerator may offer, what bounds it, and
which of the two halves of that bound is proved and which is decided.

Everything below was measured before it was written. The numbers are from the
three chains this repository carries and from the moves its own enumerator
offers along them.

`scripts/untargeted_space.py` recomputes every figure in this section and stops
with both numbers side by side when one disagrees. `make measure` runs it and
`make release` includes it, so a number here cannot go stale quietly. A reader
who does not trust a figure on a page runs one command instead of rebuilding
the measurement.

**UNT-1 — Without a target the candidates come from the leading
monomials.** There is no displacement to divide, so Proposition (3.1)
supplies the rule instead: take a monomial `M` of degree `d = deg(F)` occurring
in `F`, with coefficient `a`, and write `aM = PQ` with `deg P` and `deg Q` at
most `d - 2`.

The space that follows is small and does not grow with the dimension.
Measured: 22 candidates at the normalized Alpöge map in dimension 3, and
between 2 and 22 at every map of the two long chains that is still above degree
three, from dimension 3 up to 19. Twelve of the 22 are narrow and ten are the
wider ones of UNT-6. It is bounded by the number of monomials of
top degree, and that number stays small because a step removes one and adds
only monomials below `d`.

Swapping `P` and `Q` gives the same step up to which name goes where, so it is
one candidate and not two, which is SEA-2. Counting ordered pairs doubles every
number above.

When the leading monomial is a square, `P` and `Q` are equal and one coordinate
serves both, which is BCW-12. The enumerator offers only that shape there. Two
coordinates carrying one value would cost a dimension for nothing, and it is
the same saving that puts `alpoege15` two dimensions below `bcw17`. Measured:
14 of the 272 candidates along the two long chains share a generator, and every
one of them lands one dimension lower than it would have.

That answers the second question this work package was set. Of the two shapes
SEA-14 leaves out, the coefficient is necessary and BCW-12 is not: two fresh
coordinates reach degree three as well. It is worth a dimension at every map
whose leading monomial is a square, and the nineteen-dimensional chain has
fourteen of those in a row.

A coefficient in the step is not optional here. From the second map of the
nineteen-dimensional chain onwards, every factorization comes from a leading
monomial whose coefficient is not one: 25 of 25, then 9 of 9 for thirteen maps,
then 8 of 8 and 4 of 4. An enumerator that took `P` and `Q`
monic and carried no coefficient could not express those steps, so BCW-11 is
what makes this family possible.

**UNT-2 — At degree three the space is empty, and that is the stopping
rule.** `deg P + deg Q = d` with both at most `d - 2` forces `d >= 4`.
At degree three the enumerator offers nothing, so a search stops because it has
run out of candidates and not because a separate rule told it to.

Measured at the end of both long chains: no factorizations at all.

**UNT-3 — The measure that bounds the search.** Put

    Phi(F) = sum over all monomials M of degree >= 4 in F of 3^(deg M - 3),

and require every step to lower it.

For a step that introduces at least one generator this is a consequence of
Proposition (3.1) and not an assumption. The step removes a monomial of degree
`d` and the terms it puts in its place have degree at most
`max(deg P, deg Q) + 1`, which is at most `d - 1`. Measured over every such
move the enumerator offers along both long chains: 105 of 105 lower `Phi`, that
is 19 of 19 introducing two generators and 86 of 86 introducing one. Over the
widened offer, all 272 candidates lower it.

For a step that introduces no generator it is a rule this project states, not a
theorem. Such a step subtracts a multiple of `X_u X_v` for two coordinates the
map already carries. When the target component does not contain that product,
the subtraction puts it there instead of cancelling it, and the map comes out
with more to reduce than it had. Measured: 365 of 376 such moves lower `Phi`
and 11 raise it or leave it standing, 8 of those by raising the degree of the
target component.

Without the rule the search does not terminate, and the reason is concrete. One
step can create `X_u X_v` and the next remove it again, so a walk can cycle
between two maps forever without either being wrong. Nothing in BCW-1 to BCW-12
forbids either step. `Phi` is what forbids the pair.

The base is 3 and could be 2. A step replaces one monomial of degree `d` by at
most three of degree `d - 1`, and `3^(d-3)` is exactly what absorbs that, which
is why the base was chosen so. Measured, base 2 suffices on all three chains
and base 4 changes nothing, so the choice is a margin and not a necessity.

**UNT-4 — An exhausted space is the space under UNT-3.** SEA-6 and REV-7
already say that finding nothing is not a proof that nothing exists. Here the
statement is narrower still: the space an untargeted search exhausts is the one
that UNT-3 leaves, and UNT-3 rules out steps that BCW-1 to BCW-12 admit.

`reduce_to_degree3` walks that space and `ReductionOutcome` reports it, with
the same four fields the other two searches report and the ring of DOM-4
beside them.

One thing the outcome cannot report. `reduce_to_degree3` walks by recursion,
one frame per step, so a source needing a chain longer than the interpreter's
recursion limit allows raises `RecursionError` rather than reporting that it
was cut off. Measured at about 970 steps against a default budget of 20000. It
is stated rather than repaired: the longest chain produced here is 29 steps,
and the docstring says where the ceiling is.

An outcome that reports an exhausted space says the search covered every chain
whose every step lowers `Phi`. A chain that raises it at one step and reaches
degree three afterwards would not be found. No such chain is known, and all
three chains this repository carries lower `Phi` at every one of their 33
steps, but that is evidence and not a proof.

**UNT-5 — A source of degree three is the base case and not a
failure.** There is nothing to reduce, so there is nothing to build.
RED-1 wants at least one step, so no `Reduction` can describe the situation,
and the outcome reports no reduction with nothing examined and the space
exhausted.

This is the base case of the induction in Proposition (3.1), which stops at
`d <= 3` with nothing to prove, and it is the same shape of answer REV-11 gives
for two endpoints that are already equal. A caller who wants to tell it from a
search that found nothing asks the source for its degree; that is cheaper than
the search and it is not the search's question.

UNT-2 makes this consistent rather than special, and the implementation has no
branch for it. At degree three the enumerator offers nothing, so the walk
returns at once with no steps, nothing examined and the space exhausted. A
branch was written and removed: a mutation showed it changed no outcome. The
clause states the answer, and UNT-2 is why no code has to.

**UNT-6 — A factor may be a sum, and that is an extension.** The
enumerator also offers a candidate whose second factor has several terms: `P` a
monomial that strictly divides more than one of the monomials of degree at
least four in one component, and `Q` the sum of the cofactors, so that the step
removes all of them at once.

Strictly, in both senses. A monomial equal to the divisor is not grouped, and a
group of fewer than two is not offered, because a wide candidate with one
cofactor is a narrow split written twice.

This goes beyond Proposition (3.1) and the page says so. BCW write `aM = PQ`
for a single monomial `M`, which forces both factors to be monomials over an
integral domain. BCW-6 admits the wider shape already: `G` subtracts
`c * X_u * X_v` for any two slots, and what the slots carry is not required to
be a monomial. UNT-1 describes the narrow space and this describes the rest of
what BCW-6 admits.

The measurement is why it is here. Work package 10 found that the high-yield
steps of the chains computed by hand all use a factor with several terms: five
of seven in `bcw17`, and the step that removes 102 of the measure has a factor
with four. The narrow enumerator uses none, so no ranking over what it offers
can reach those steps. The gap was coverage and not order.

**Every factor has order at least one.** `Q` is a sum of cofactors, so a
monomial equal to the divisor would leave the cofactor `1` and give `Q` a
constant term. Then `H` reaches `EA^-1`, which BCW-6 admits at no level. The
enumerator therefore groups only the monomials strictly larger than the
divisor.

This clause is an amendment, and it was written after the code rather than
before it. The first implementation grouped every monomial the divisor divides
and produced candidates that `BCWStep.verify` rejects; an external audit of the
snapshot of 25 August 2026 found a chain that reached degree three, reported an
exhausted space and failed its own first step. The hazard was already guarded
twice, in `peeling` and in `search.anchors`, and both places say why; it was
not carried here. Where a page names a bound in one family and not in another,
the second is where to look.

**UNT-7 — The degree of the divisor is `d // 2`, and that is a stated
choice.** `P` has degree `d // 2` where `d` is the degree of the map.
Admissibility bounds it on both sides -- `deg P` and `deg Q` are at least two
and at most `d - 2` -- and `d // 2` lies inside that for every `d >= 4`, which
is also why it falls to two at degrees four and five, where two is the only
admissible value.

It is measured and not proved. On the normalized Alpöge map at degree seven,
the best step a divisor of that degree allows removes 102 of the measure,
against 69 at degree two and 72 at degree five. Driven greedily to degree three
it takes seven steps, where a fixed divisor degree of two takes twelve and
`d - 2` takes twelve.

What that establishes is narrow, and the wording is deliberate. The choice was
measured on one map. The same rule on Gao's map did not finish in
twenty-five minutes, because at degree twelve the divisors of degree six are
many and the sums are long. A rule measured on one example is an observation
about that example.

**UNT-8 — The filtration level follows from the step.** It is not
prescribed. A step whose `Q` carries a linear term reaches `EA^0` and not
`EA^1`, and Proposition (3.1) admits that: BCW take `H` from `EA^0` for the
part of the argument that makes `F'` linear in each variable.

Following the step means downwards as well. A factor with a constant term
reaches `EA^-1`, and the level reported is `-1`, which `BCWStep.build` refuses
by name. Reporting `0` there was the reason the defect above stayed silent: the
step was built at a level it does not reach, and only `verify` said so, which
nothing in the untargeted walk calls. Clamping a level upwards is a weaker
declaration and allowed; clamping it downwards is a false one.

An enumerator that fixed the level at one would lose exactly the best steps.
The 102 above is such a step: with `EA^1` demanded it fails BCW-6, and with the
level left to follow it stands.

**UNT-9 — A factor a carrier already holds is offered as that
carrier.** Then the step buys no coordinate for it. BCW-10 admits it, and
it is what the whole extension is worth in dimension.

Measured on the normalized Alpöge map, greedily under UNT-6 to UNT-8: seven
steps into dimension 17 without carrier reuse and seven into dimension 13 with
it, buying two coordinates for the first three steps and one for each of the
last four. The search finds that pattern without being told that carriers
exist.

**UNT-10 — The steps are ordered, by what one removes and then by what it
buys.** `ordered_steps` returns them sorted: first by how much of `Phi`
the step removes, largest first, and among equals by how many coordinates it
buys, fewest first.

The steps and not the candidates. How much a step removes is not known before
the step exists, so the order cannot be a property of a proposal;
`untargeted_candidates` keeps the order its own enumeration fixes, which UNT-1
describes. A first wording of this clause named the wrong function, and an
example in `docs/api.md` written from it disagreed with the code.

Measured over the widened offer, on the two source maps, with every chain
verified and nothing else changed:

| order | Alpöge | Gao |
| --- | --- | --- |
| the order the enumerator happened to fix | 21, 20 | 177, 86 |
| largest removal | 7, 14 | 30, 42 |
| removal per coordinate bought | 8, 13 | -- |
| fewest coordinates, then removal | 8, 13 | -- |
| largest removal, then fewest coordinates | 7, 13 | 29, 39 |

Each cell is the number of steps and the dimension reached. The last row is
what the library does.

The last is at least as good as every other in both quantities and best in
both examples. It is a measured choice and not a proved one, and it was
measured on two maps.

Two of the rules reach dimension 13 as well and take a step more, so ordering
by the dimension is enough here. Spending the dimension as a cost and
exhausting each one before buying the next would say something else: that no
chain exists in dimension `k`, rather than that one was found in `k + 1`. That
is a statement about what is not there, and it belongs where the other such
statements are.

**UNT-11 — An order discards nothing.** Every chain the search of UNT-3
can reach stays reachable under any order, and a bad order costs length and not
correctness. The obligation is the promise, and the promise is what separates
this from pruning.

Measured on both maps: the number of maps examined equals the number of steps
in every run, under every order. The walk still never backtracks, so what
changed is which chain it walks into and not how much of the space it saw.

WP 12 discards, and cannot give this promise: a bound that prunes too much
reports a reachable chain as an exhausted space, and that result is wrong
rather than slow. The two are separate packages so that a failure in the second
cannot have its cause in the first.

### What the dimension thirteen does and does not establish

The chain is checked to the standard this repository holds a chain to: degree
three, determinant one, and Alpöge's three points transported through it and
verified against the endpoint, three distinct preimages of one image in
dimension 13.

It establishes that this rule finds such a chain. It does not establish
minimality. The search is greedy: it takes the best single step at every map
and never looks sideways, which is the limitation a cost on the dimension would
lift. Nor does it establish priority. Before the number leaves this repository,
the literature is checked again and what a comparison does and does not show is
written beside it.

The figures above come from the shipped enumerator and are checked by
`scripts/untargeted_space.py`, which `make measure` runs. They came from a
prototype while the obligations were written ahead of the code, and this
sentence said so until the code arrived.

### Which of these can fail on supplied data

None of them, for the reason UNT-1 to UNT-5 give: an untargeted search takes a
source and no target.

UNT-7 is the one to read twice. It is the only obligation in this family whose
content is a number chosen by measurement rather than a shape forced by an
argument, and the measurement is from one map.

---

### Why BCW's own measure is not used

The proof of Proposition (3.1) on page 305 argues by induction on the pair
`(d, e)`, where `e` is the number of monomials of degree `d` occurring in `F`,
and shows that either `deg(F') < d` or `deg(F') = d` and `e(F') < e`.

That is a termination proof for BCW's own construction, and it is too coarse
for a search. Measured along the chains here, `(d, e)` falls at 4 of 8 steps of
the seventeen-dimensional chain and at 6 of 17 of the nineteen-dimensional one.
The steps where it does not fall are the ones that build a carrier for a later
step to reuse, which BCW never do, and which are why `alpoege15` reaches
fifteen dimensions where `bcw17` reaches seventeen.

Two refinements were measured and are recorded here because they are the
obvious things to try. Counting per component, as
`(sum of (d_i - 3), sum of e_i)`, decides the two chains without carrier reuse
completely and fails six times on the nineteen-dimensional one. Weighting a
monomial by how often it must still be halved fails five times. Both are linear
in the degree, and a step that replaces one monomial by three of the next lower
degree defeats anything linear. That is what the exponent in UNT-3 is for.

### Which of these can fail on supplied data

None of them. An untargeted search takes a source and no target, so there is no
supplied object for these obligations to be wrong about. UNT-1 and UNT-2 are
statements about what the enumerator offers, and UNT-3 and UNT-4 are decisions
about which part of the space is walked.

UNT-3 is the one to read twice. Its first half is proved and its second half is
not, the two are stated in one obligation because a search cannot apply them
separately, and a reviewer weighing the family should weigh those halves
differently.

---

## The coefficient ring

A search returns a chain or an exhausted space, and an exhausted space is a
statement about a space. The space has never been named. Until 0.5 the
coefficient ring came from whichever map the caller happened to pass as the
source, and everything else was measured against it in silence.

Three narrowings have the same shape, and all three end in an exhausted space.
Measured on the tree before this family existed.

The ring comes from the source alone. Neither `search` nor `peel` takes it, and
`alpoege` lies over `ZZ` while `over_field(alpoege)` lies over `QQ`. Which
space a call searches is decided by a map the caller built earlier, possibly
for another reason.

Endpoints over different rings report an exhausted space. That is one of the
six invariants of REV-11 and it is true: no chain crosses from `ZZ` to `QQ`,
because a step takes its factors from the domain of its source. It is also the
defect that cost a release, when a driver built its source with `over_field`
and the target lay over `ZZ`. `settled` now answers in nought examined maps
instead of hours, which makes it fast and leaves it silent.

A pool value outside the ring disappears. `1/2 * y**2` over `ZZ` yields no
candidate, exactly as a value that describes nothing would. The enumerator does
not distinguish "not in this ring" from "nothing here to take".

The obligations below make the space something a caller states and a result
carries. The markers they carried while 0.5 was open are gone; the milestone closed
them.

**DOM-1 — The coefficient ring is an argument, and its default is the
source.** `search` and `peel` take `over`, a keyword-only argument
holding the domain to search over. Omitted, it is the domain of the source's
ring, which is what both functions used before and is why a call written
against 0.4 keeps its meaning.

Naming it is the point. A figure that leaves this repository has to say which
space it belongs to, and a reader cannot recover that from a call that never
mentioned one.

**DOM-2 — An argument that disagrees with the ring is an error and not a
result.** When `over` is given and the source or the target does not lie
in it, the call raises. It does not report an exhausted space.

A pool value is refused whether or not `over` was given, and that asymmetry is
deliberate. Two endpoints over different rings each describe a map, and REV-11
answers the pair without an error. A pool value whose coefficients lie outside
the domain describes nothing at all, so there is no reading of the call under
which it is a narrower search.

What is checked of a value are its coefficients and not its generators. A value
may name a coordinate the source does not have yet — `w6 = w1 x` becomes
convertible only once `w1` exists — and such a value yielding no candidate is
how the dependency between carriers falls out by itself. This clause is an
amendment: the first implementation refused both, and three tests written for
SEA-13 said so.

`enumerate_candidates` makes the same check. It is public, and until 0.5 a bad
value passed through it unremarked, which is the gap an audit found for
`selection_limit` in `0.4.0rc9`. `search` checks again before its walk, because
a search whose endpoints are equal is answered from the endpoints and never
reaches the enumerator, and whether a call is valid must not depend on how far
it gets.

The distinction is the whole of this family. An exhausted space says the search
covered a space and the chain was not in it, which is a result under SEA-6 and
REV-7. A caller who states one ring and passes an argument over another has
described two spaces, and no search over either answers what they asked. That
is a wrong call, and a wrong call is reported where it is made.

The exception carries `DOM-2` and names the argument and both rings, so that
the two are visible side by side rather than left to be inferred.

**DOM-3 — Without `over`, the endpoints keep the answer of REV-11.** A
call that names no ring behaves as it did in 0.4: two endpoints over different
rings are a non-answer and an exhausted space, decided from the endpoints
before any walk.

This is a deliberate asymmetry and not an oversight. REV-11 is about what a
pair of endpoints can be, and it stands. DOM-2 is about a caller contradicting
themselves, which is a different thing and cannot arise without `over`. The
alternative, making the mismatch an error everywhere, would change the meaning
of a call written against 0.4 without the caller doing anything.

**DOM-4 — The outcome carries the ring it searched.** `SearchOutcome`
and `PeelOutcome` hold the domain, whether the caller named it or it came from
the source.

An exhausted space is only worth what the space is worth, and the same holds
for a chain: a reduction found over `QQ` and one found over `ZZ` are answers to
different questions. Carrying the ring in the outcome means a number can be
quoted with it rather than beside it.

### Which of these can fail on supplied data

DOM-2, which is a check on the arguments a caller brings. DOM-1, DOM-3 and
DOM-4 are obligations on the library's own conduct.

DOM-2 is worth a second look by a reviewer. It is the one clause in this
package that turns something previously reported as a result into an
exception, and a check that fires where it should not would refuse a call that
0.4 answered.

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
| a source outside `MA^1`, of degree above three, or not Keller | `VerificationError` |
| `variables` whose length is not `source.dimension` | `ValueError` |
| `reordered()` given anything but a permutation of the variables | `ValueError` |
| a structural case the search does not handle | `NotImplementedError` |
| an argument over a ring other than `over` | `VerificationError` |
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

**No smallest unipotent lift.** `UnipotentStep` doubles the dimension, which is
what Section 4 does. Nothing claims that a map in `MA^1` of degree three has no
lift to a nilpotent Jacobian in fewer than `2n` variables, and no obligation
assumes it. The compression of milestone 0.6 works the other way round, on the
homogeneous map at the end, and says nothing about this step either.

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
