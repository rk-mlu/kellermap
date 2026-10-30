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

An obligation marked with a milestone number belongs to a release that has not
been published. The marker stays through the release candidates, which are not
published on PyPI or Zenodo, and is removed in the release commit. A marked
obligation may already be implemented; the milestone paragraph below says which
are. Until it is, it is a statement of intent that the implementation is
measured against, and a review of an unfinished milestone should read it as
such. Obligations without a marker are implemented.

**Status:** every obligation on this page without a milestone marker is
implemented and the test suite covers every statement of the package, with two
exceptions that say so where they stand: SYM-7 and VAN-5 are consequences this
library states and does not compute. SYM-7 is checked in part, by VAN-3 to the
depth a witness names. Where
the implementation forced a change, this page was amended deliberately and the
amendment is visible in the wording — the clearest cases are COL-4 and BCW-3,
which moved from obligations of `verify()` to constructor invariants, LIN-2,
which was narrowed to what is actually checkable, and UNI-9, which changed the
route by which it takes a determinant.

An audit of `0.7.0rc10` found two release blockers, and for them this page was
changed before the code, which is the order this section states. LIN-6, FAC-1,
WID-1 and WID-2 were stated that way and are implemented since `0.7.0rc11`.
They carried no `[0.7]` marker in between: the test that holds the markers to
the version read `0.7.0rc10` as released. That is settled since milestone 0.9.
A candidate is now read as below its release, and an obligation added during
the candidates carries the marker. `docs/roadmap.md` records the decision under
"Version 0.9".

An audit of `0.7.0rc11` found two more, and three clauses are ahead of the
implementation for them, by the same order and without markers for the same
reason: MAP-4, the ground-domain amendment of WID-1, and the sentence in FAC-1
that asks its predicate the same way. The figures SYM-7 quotes from work
package 1 are a separate matter: the carrier they record is not the carrier the
code selects today, which `docs/errata.md` states and a measurement has to
settle.

This paragraph used to carry a version number. It said `0.4.0` through the
whole of milestone 0.5 and was noticed only when 0.6 opened, which is what a
number maintained in one place and checked in none does. What it says now holds
whenever it is read, and the milestone paragraphs below carry the history.
`docs/errata.md` records the stale one.

**Milestone `0.9`, open.** Thirty-three obligations are marked. Three of
them are implemented since work package 1.1: LIN-7, TRA-9 and UNI-13. With
HOM-12 they make the conditional chain of Theorem 2.1(b) explicit for every
step type that can lie between `reduce_to_multi_affine` and the
homogenization. All three are self-checks: none can fail after the identity of
its step. `docs/roadmap.md` gives the reason for stating them anyway.

The other twenty were stated in work package 2. FMT-1 to FMT-12 are the file a
certificate is written to, under "The certificate file", and are implemented
since work package 3. CHK-1 to CHK-8 are the checker that reads it without the
library, under "The independent checker", and are implemented since work
package 4. Two of them want a reviewer's attention. FMT-5 narrows the
domains a file can hold, and the paragraph under it gives the measurement that
forced the narrowing. CHK-8 is the only evidence that the checker checks
anything, and the other seven say what it checks.

An audit of work package 2 read the twenty before any of them was implemented.
Work package 2.1 amended twelve of them, and each amendment says so where it
stands. The two that changed most are CHK-6, which now has three verdicts, and
CHK-8, whose first wording promised more than a control can show.

Work package 2.2 changed no obligation. It gave the constructor invariants
their identifiers and `VerificationError` a location, as the section on errors
describes.

TEX-1 to TEX-6 were stated in work package 5, before the view they describe,
under "The LaTeX view", and are implemented since work package 5. TEX-1 is
the one to read first: the view is made only from a file the checker verifies.

CLI-1 to CLI-4 were stated in work package 6, before the command line they
describe, under "The command line", and are implemented since work package 6. They
add a way to call what work packages 3 to 5 built, and nothing else.

**Milestone `0.8`, closed.** The milestone added `VanishingWitness`, VAN-1 to
VAN-5, the witness to Zhao's Vanishing Conjecture that the symmetric lift
provides. Their `[0.8]` markers are gone with the close.

Two of the five want a reviewer's attention. VAN-3 and VAN-4 cannot fail on a
lift that verifies, because both follow from Theorem 3, so they are
cross-checks against Zhao's theorems rather than checks of data, and their
negative controls call the two check functions on forms that are not lifts.
And VAN-5 is the first obligation on this page that is out of reach by
construction and not by measurement. A non-zero value at any index above a
known bound would decide it, and at the smallest witness the first integer
above that bound has eighteen digits. SYM-7 is a computation that did not
finish in eight hours.

**Milestone `0.7`, closed.** The milestone finished Theorem 2.1(b), HOM-11 and
HOM-12 for the property and UNT-12 for the walk that reaches it, and added the
descent, DSC-1 to DSC-7. Their `[0.7]` markers are gone with the close.

Two of the ten want a reviewer's attention. DSC-3 is the only obligation on
this page whose failure says nothing about the map it was given: the source may
be sound and the two automorphisms simply wrong, so it is a check on a claim
rather than on data. And HOM-12 is the only one whose hypothesis is a property
of the source that the source is not required to have, so it passes silently on
every map this project carried before `0.7`; the paragraph under the HOM family
says what its negative control therefore has to be and why there is none
through `verify()`.

UNT-12 was amended twice while it was implemented, and both amendments are
visible in its wording. The first requirement it carried made the smallest case
of the theorem unreachable rather than expensive.

**Milestone `0.6`, closed.** The milestone added the second and third steps of
the Reduction Theorem, UNI-1 to UNI-12 and HOM-1 to HOM-10; collision-hull
compression, CHC-1 to CHC-10; and the symmetric lift, SYM-1 to SYM-12. Their
`[0.6]` markers are gone with the close.

Two of the forty-four are unlike anything this page carried before, and a
review should weigh them as such. SYM-7 is the only obligation this library
states and does not check: the determinant of the gradient form follows from
the identity and the source, and computing it did not finish in eight hours.
CHC-9, SYM-8 and SYM-9 are the first transports that may refuse a collision
which genuinely holds for their source, which is an answer and not a failure.
SYM-8 was added to that list after an audit of `0.6.0rc5`.

One obligation was amended while it was implemented. UNI-9 takes its
determinant in one more coordinate rather than over `k[T]`; the amendment is
visible in its wording, with the measurement that prompted it.

**Milestone `0.5`, closed.** The milestone added the untargeted enumerator and
the search over it, UNT-1 to UNT-11. It also made the coefficient ring
something a caller states, DOM-1 to DOM-4. Its obligations carried the `[0.5]` marker while
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
- [HomogenizationStep](#homogenizationstep)
- [CompressionStep](#compressionstep)
- [SymmetricLiftStep](#symmetricliftstep)
- [VanishingWitness](#vanishingwitness)
- [DescentStep](#descentstep)
- [Reduction](#reduction)
- [The certificate file](#the-certificate-file)
- [The independent checker](#the-independent-checker)
- [The LaTeX view](#the-latex-view)
- [The command line](#the-command-line)
- [Search](#search)
- [Peeling](#peeling)
- [The untargeted search](#the-untargeted-search)
- [Evaluating and factorizing](#evaluating-and-factorizing)
- [Conjugation by a diagonal](#conjugation-by-a-diagonal)
- [Widening the coefficient domain](#widening-the-coefficient-domain)
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
a false negative. The evaluation itself happens in the coefficient domain
wherever the point lies in it, and by substitution otherwise; COL-7 confines
the two to the case where they agree.

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

**COL-7 — Characteristic zero.** `F.ring.domain.characteristic() == 0`. Checked
first in `verify()`, before COL-1, so that a map outside the scope of this type
is answered as such rather than by a dimension or an image that also differs.

The reason is this type's own semantics rather than the state of any
conjecture. COL-5 keeps the map out of a `Collision`, so the points are held as
expressions and COL-4 decides their distinctness with `kellermap.canonical`,
whose normal form is built for rational functions and radicals and carries no
characteristic. Deciding COL-3 in the coefficient domain while COL-4 stays in
that normal form would admit `0` and `2` over `GF(2)` as two distinct points
with one image — a false certificate rather than a missing one. COL-7 removes
the case instead of giving the type a second notion of equality, which is the
boundary `lift.py` draws at SYM-4 and `compression.py` at CHC-8.

What a collision in positive characteristic would be worth is worth naming, so
that the boundary is not read as a larger claim. Non-injective Keller maps are
cheap there and have been known since long before the characteristic-zero
question was settled: over a field of characteristic `p` the Artin–Schreier map
`X + X^p` has Jacobian one and identifies the `p` elements of the prime field.
The maps this library is built around are the characteristic-zero
counterexamples; `README.md` states what became of the conjecture there and
when.

This paragraph said the Jacobian conjecture is open in characteristic zero
until `0.7.0rc8`, and that was simply wrong — the first page of `README.md`
says it fell in July 2026 and that the counterexamples are the subject of this
library. An audit of `0.7.0rc7` found the claim here, in `collision.py` and in
the `VerificationError` a caller sees. The obligation is unchanged; only its
justification was wrong, and the justification above does not depend on the
conjecture at all.

Checked in `verify()` and not in the constructor, because COL-5 keeps the map
out of the object. The points remain a legitimate `Collision`; what is refused
is stating them *against this map*. Positive characteristic is therefore not a
property a collision can have, and asking whether one "is" in characteristic p
is not a question this type answers.

No advice to call `over_field()`, for the reason `lift.py` gives at SYM-4: the
field of fractions of a finite field is itself.

Two consequences, named here rather than left to be discovered. Every
`Step.transport` verifies, so a reduction chain over a domain of positive
characteristic carries no collision, at any step type. And `collision_hull`
verifies its argument before it reaches the field check, so over `GF(p)` it now
answers COL-7 where it answered the `d!` half of CHC-8 until `0.7.0rc6`; that
half is still reached through the `CompressionStep` constructor, which needs no
collision.

The boundary this draws is the same one `kellermap.canonical` already assumed
without saying so. Its normal form decides equality for rational functions and
square roots, both of which live in characteristic zero, and it has no notion
of a characteristic to carry. Deciding COL-3 in the coefficient domain while
leaving COL-4 to that normal form would have let two spellings of one point
over `GF(2)` — `0` and `2` — pass as a collision of distinct points. COL-7
removes the case rather than giving the type a second equality.

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
unit. Over `ZZ` that admits every unimodular matrix without widening anything,
and refuses one whose determinant is `2`; `over_field()` is for the second case
and not for the domain as such. Two maps over different domains are different
objects here, and the arithmetic does not widen one quietly.

This paragraph said every map over `ZZ` has to pass through `over_field()`
before it can be normalized. That was true of `0.7.0rc8` and false of
`0.7.0rc9`, which implemented and tested the unimodular case, and the page was
not revised with the code. An audit of `0.7.0rc9` found the contradiction and
noted that this page calls itself binding, so the disagreement was not merely
editorial. FAC-1 and FAC-2 state the boundary that actually holds, and WID-1
and WID-2 state what the widening itself promises.

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

"The same polynomial" means the same element of `source.ring`, and the check
runs after both slots have been converted into it. Until `0.7.0rc6` it ran
before, on the expressions as they arrived, and decided with
`kellermap.canonical`, which has no characteristic. Over `GF(2)` that read `y`
and `-y` as two values and refused a step whose two slots are one element of
the ring; over any domain it would have refused `x^2 - y^2` beside
`(x - y)·(x + y)`. Whether one coordinate can hold both values is a question
about the coefficient ring and not about how the caller spelled them.

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

The equality is decided in `source.ring` and the product of the factor
determinants is formed in its domain. Both sides come out of a `PolyRing`
already, so the conversion normalizes rather than computes; what the ring adds
is the characteristic. A transposition accounts for `-1`, and over `GF(2)` that
is `1`. Deciding it with `kellermap.canonical` reported the identity of `GF(2)`
as a step whose bookkeeping does not add up, and an exhaustive enumeration put
5 of the 6 invertible `2x2` matrices over that field on this path.

**LIN-4 — Not elementary.** `transformation` is not required to lie in
`EA_n(k)`, and generally does not: every element of `EA_n(k)` has determinant
one. The normalization of Alpöge's map has determinant `-1/2`.

**LIN-5 — Transport.** Points are unchanged; the image becomes
`transformation(c)`. Left composition does not move preimages.

**LIN-6 — Normalization is a claim, not a definition.** If the step declares
itself the normalization, `source` lies in `MA^0`, `transformation` equals the
inverse of `J(source)(0)`, and `target` lies in `MA^1`. A `LinearStep` that is
not so declared carries no such obligation.

Nothing is inverted and nothing is factorized to decide this. `det J(source)(0)`
has to be a unit of the coefficient domain, which over a field is
non-singularity and over a ring is stronger, and the determinant is taken in
the domain. `transformation.matrix()` is then multiplied by `J(source)(0)` in
the domain, and the product has to be the identity. One side is enough: over a
commutative ring `A B = I` makes `det A` a unit and `B` the inverse of `A`.

Verification therefore uses the certificate the step exhibits and builds
nothing of its own. This is an amendment, and an audit of `0.7.0rc10` found the
release blocker that forced it. Until then verification called `factorize` on
`J(source)(0)` and compared the result entry by entry against `transformation`.
`factorize` refuses a matrix whose column its bounded search cannot bring to a
unit pivot, FAC-2 permits that refusal, and the verifier read it as a singular
linear part. Over `ZZ[T]` the matrix `[[T, -1], [2T+1, -2]]` has determinant
one; a step taking `(T x - y, (2T+1) x - 2y)` to the identity map, carrying the
inverse as an exhibited factorization, was refused as singular. A certificate
may not rest on a search that FAC-2 declares incomplete. `normalize()` still
builds through `factorize` and keeps that boundary; verification does not.

The two clauses have two messages, and each is true where it fires. A
determinant that is not a unit says Proposition (1.1) does not apply to this
source. A product that is not the identity says the transformation is not the
inverse. `0.7.0rc10` had one message for both, and it named singularity, which
was false of every matrix of unit determinant the search did not reach.

The comparison is of entries and not of matrices. `DomainMatrix` compares its
representation, so a dense product and the sparse identity of
`DomainMatrix.eye` hold the same entries and are unequal, and a check written
that way would refuse every step.

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

**LIN-7 — A multi-affine source gives a multi-affine target. [0.9]** If no
variable occurs squared in any monomial of `source - X`, then no variable occurs
squared in any monomial of `target - X`.

By LIN-1 each component of the target is a linear combination of components of
the source, so `target - X` is the transformation applied to `source - X` plus
a linear map. Neither creates a square. The obligation is conditional, as
HOM-12 is, and says nothing about a source that is not multi-affine.

### Which of these can fail on supplied data

LIN-1, and of LIN-6 the `MA^0` clause, the unit determinant and the product: a
supplied step can declare a normalization of a source that does not fix the
origin, of one whose linear part is not invertible over the domain, or with a
transformation that is not the inverse. LIN-2 and LIN-3 follow from LIN-1 and
can only fail if the library is wrong about its own arithmetic, and so does the
`MA^1` clause of LIN-6: under LIN-1 the linear part of the target is the
product the clause before it checks. They are retained as cheap self-checks,
and a review should weigh them as such rather than as evidence about a supplied
target. LIN-7 follows from LIN-1 in the same way.

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

**TRA-9 — A multi-affine source gives a multi-affine target. [0.9]** As LIN-7.
By TRA-1 the displacement of the target is that of the source minus a constant,
and a constant is no square.

### Which of these can fail on supplied data

TRA-1 and the first clause of TRA-6, which compares the shift against `F(0)`.

This is narrower than the wording this section carried when it was written,
which named both clauses of TRA-6. The implementation showed why. The `MA^0`
clause follows from TRA-1 together with the first clause: if the target is the
source translated by `F(0)`, it vanishes at the origin. It is retained as a
self-check and carries `# pragma: no cover`.

TRA-3, TRA-4 and TRA-9 follow from TRA-1 in the same way and can only fail if
the library is wrong about its own arithmetic. TRA-2 is a constructor invariant and
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

**UNI-1 — The identity.** `target == G ∘ source^[n] ∘ H`, checked as
a polynomial identity in one shared `PolyRing`, not by comparing printed
expressions.

The composition is BCW's `G(T) ∘ E(T)^[n] ∘ H(T)` at `T = 1`. The parameter
does not appear in the certificate. It carries the grading that Lemma (4.1)
needs, and the lemma is what makes the target's displacement nilpotent; the
identity this obligation checks holds without it.

**UNI-2 — The source lies in `MA^1`.** `source.is_in_MA(1)`, that is
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

**UNI-3 — The source has degree at most three.**
`source.degree() <= 3`.

`E(T) = X + T F_(2) + T^2 F_(3)` has no slot for a homogeneous part of degree
four, and `H` removes `F_(3)` alone. The first stage of the Reduction Theorem
is what supplies a source of degree three, and this obligation is where the
stages meet.

**UNI-4 — The source is Keller.** `source.determinant() == 1`.

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

**UNI-5 — Dimension and generators.** `target.dimension == 2 * n`; the
generators of `target` are those of `source` followed by `variables`, in order;
`len(variables) == n`; and each fresh variable satisfies RC-4 against
`source.ring`.

Freshness and the count are constructor invariants and raise `ValueError`, as
the corresponding half of BCW-2 does. A certificate names the variables it
used, and a supplied target is checked against those rather than against names
invented while verifying.

**UNI-6 — Invertibility is exhibited, not asserted.** `G` and `H` are
checked to be products of elementary factors whose polynomials do not involve
their own variable, and `G.inverse() ∘ G` and `H.inverse() ∘ H` are checked to
be the identity map. As BCW-5.

Each factor of `G` displaces `X_i` by `Y_i`, which is free of `X_i`; each
factor of `H` displaces `Y_i` by `-F_(3),i`, which is a polynomial in the
source's variables alone and therefore free of every `Y`. Within each block the
factors commute, so the order they are listed in does not matter, and `H^-1` is
the componentwise negation, which is what `transport()` uses.

**UNI-7 — The step establishes `EA^0` and no more.**
`filtration_level == 0`, `G.is_in_EA(0)` holds and `G.is_in_EA(1)` does not.

The level is not an argument here. `G` displaces `X_i` by `Y_i`, of order one,
so it lies in `EA^0` and in no higher stage, and the construction admits no
other factorization to declare. `H` lies in `EA^2` and constrains nothing.

**UNI-8 — The target leaves `MA^1`.**
`target.filtration_degree() == 0`.

The displacement is `(F_(2) + Y, -F_(3))` and its second block has order one.
This is a consequence of UNI-1 and is stated as an obligation because a caller
has to know it: a `BCWStep` declaring `EA^1` after this step is making a claim
about a map that is not in `MA^1`, and a second `UnipotentStep` on this target
is refused by UNI-2. What comes next is the homogenization, which is what
milestone 0.6 builds next.

**UNI-9 — The displacement of the target is nilpotent.**
`J(target - X)` is nilpotent, checked as the determinant of

    (X + T * (target - X),  T)

in one coordinate more than the target, which has to be one.

The check is one determinant and not a matrix power. The Jacobian of that map
is block triangular, with `I + T J(N)` above and a one in the corner, so its
determinant is `det(I + T J(N))`. That being one says that every coefficient of
the characteristic polynomial of `J(N)` below the leading one vanishes, and
Cayley-Hamilton over a commutative ring then gives `J(N)^m = 0`. The matrix
power is not an option: `J**26` on the 26-variable target of `alpoege13`
normalized had not finished after about half an hour, where this determinant is
done in a fraction of a second, which is about what the plain determinant of
the target costs under UNI-10.

The wording is an amendment, made when the step was implemented. It read `over
k[T]`, with `T` a parameter of the coefficient domain. That check is correct
and it is the slower of the two. It also needs a
fresh *parameter*, and nothing in this repository allocates one: RC-1 to RC-7
name fresh *generators*, and the factory protocol is about generators
throughout. The second reason is the stronger of the two.

This is redundant in principle. It follows from UNI-1 by Lemma (4.1), so it
cannot fail where UNI-1 holds, and a review should weigh it as a self-check in
the shape of BCW-7. It is checked all the same, because it is the property the
step exists to establish, and a reader who finds the word "unipotent" in the
name of a type should find it checked somewhere.

It is not UNI-10 run twice. The map whose determinant is taken here is not the
target but a one-variable widening of it, and the two calls exercise the
determinant strategies on different shapes. That widening is also nearly the
map the homogenization builds, which regrades the displacement instead of
scaling it uniformly; the two steps are expected to share the helper that
builds it.

If a later measurement makes this the dominant cost of a chain, it moves behind
an argument and this page says so. It is not moved on a guess.

**UNI-10 — The determinant is unchanged.** `target.determinant() ==
source.determinant()`. Redundant in principle, since every element of `EA_n(k)`
has determinant one, and retained as a cheap self-check in the shape of BCW-7.

**UNI-11 — Transport.** With `source(a) = source(b) = c`, and the fresh
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

**UNI-12 — Provenance is recorded, and not settable.** As BCW-9, with
the same reading: an integrity marker against mislabelling by accident, not a
security boundary.

**UNI-13 — A multi-affine source gives a multi-affine target. [0.9]** If no
variable occurs squared in any monomial of `source - X`, then no variable occurs
squared in any monomial of `target - X`.

Under UNI-1 the target is `(F_(2) + Y, -F_(3))` composed with the elementary
factors, built from homogeneous parts of the source's displacement and one
linear block. The fresh variables `Y` occur only linearly. So the step creates
no square it was not given, and no variable is exempt, unlike the parameter of
HOM-12.

### Which of these can fail on supplied data

UNI-1 for a supplied target, and UNI-2, UNI-3 and UNI-4 always.

The last three are the unusual entry on this page. Everywhere else, a
`CONSTRUCTED` step compares the implementation against itself and its
obligations become self-checks. These three constrain the *source*, which is
supplied on both routes, so `build()` cannot make them true and does not try.
A `CONSTRUCTED` `UnipotentStep` is therefore evidence about its source in a way
that a `CONSTRUCTED` `BCWStep` is not evidence about anything.

UNI-5 in its freshness and counting half is a constructor invariant and is not
reachable by `verify()`. UNI-6, UNI-9, UNI-10 and UNI-13 follow from UNI-1 and are
retained as self-checks that localize an error to the step that made it.
UNI-7 and UNI-8 are properties of the type rather than checks on data.

---

## HomogenizationStep

The third step of the Reduction Theorem, BCW Chapter II, Section 4, p. 307. It
adds one variable and makes the displacement cubic homogeneous.

```python
@dataclass(frozen=True)
class HomogenizationStep:
    source: PolynomialMap
    target: PolynomialMap
    variable: sp.Symbol
    provenance: Provenance

    @classmethod
    def build(cls, source, factory=None) -> HomogenizationStep: ...
```

It lives in `kellermap.bcw`, beside `BCWStep` and `UnipotentStep`.

Write `n` for `source.dimension`, `T` for `variable`, and `N_(1)`, `N_(2)`,
`N_(3)` for the homogeneous parts of `source.displacement()`. The target is

    target = (X + N_(1) T^2 + N_(2) T + N_(3),  T)

Each part is lifted to degree three by the power of `T` its own degree is short
of, which is what makes the displacement homogeneous. Nothing is composed and
nothing is factored.

### This step is not a composition

Every step type before this one has the shape `A o F^[m] o B` with `A` and `B`
automorphisms, and the certificate is the factorization: "invertible" is a
claim, and a list of generators with their inverses is something a reader can
check. This step has no factorization, because there is nothing to factor. The
target is not conjugate to the source, no automorphism relates the two, and
they do not have the same dimension.

What relates them is a slice. Setting `T = 1` in the first `n` components
returns the source, since `N(1) = N_(1) + N_(2) + N_(3)`. That is the whole of
the relation, and three things follow from it.

What is exhibited is the formula and the homogeneous parts the formula reads.
A reader checks the target by recomputing it, not by undoing it.

Transport goes forward and only forward. A collision of the source gives one of
the target, at `T = 1`. The converse is not claimed and is not true in general:
a collision of the target at some other value of `T` need not come from
anywhere, because the slice at `T = t` is a map that scaling relates to the
source only at `t = 1`. Every step type before this one carries the collision
both ways, because an automorphism is invertible. This one does not, and
nothing on this page needs it to: RED-5 reads a verified transport as a proof
that the *target* is not injective, which is the forward direction, and that is
the direction the milestone wants. What a chain containing this step no longer
supports is the reverse reading, from a collision of the far end back to one of
the near end.

There is no `EA` level to declare. `filtration_level` is `math.inf`, as for
`LinearStep` and `TranslationStep`, and for a different reason than either: a
composition step whose factors are not elementary makes no `EA` claim, and this
step is not a composition at all.

**HOM-1 — The identity.** `target == (X + N_(1) T^2 + N_(2) T + N_(3),
T)`, checked as a polynomial identity in one shared `PolyRing`.

The homogeneous parts are taken by total degree in the generators of the ring,
so a parameter of the coefficient domain does not count towards them. That is
the reading DOM-2 fixes and the one `PolynomialMap.degree` uses. Reading a
parameter as a variable would put `T x y` in the wrong slot and lift it by the
wrong power.

**HOM-2 — The source has degree at most three.** `source.degree() <= 3`.

The regrading has three slots and a part of degree four has no power of `T` to
be lifted by. This is where the first stage of the Reduction Theorem and the
third meet, as UNI-3 is where the first and the second do.

**HOM-3 — The Jacobian of the source's displacement is nilpotent.**
Checked as under UNI-9: the determinant of `(X + S * (source - X), S)`, in one
coordinate more than the source, has to be one.

This is the obligation that says the second step comes before the third, and
unlike UNI-9 it is not redundant. It can fail on supplied data, and when it
fails the target is not a Keller map. The reason is worth stating, because
"the source is Keller" would be the natural guess and is not enough:

    J_X N(T) = T^2 * J(N)(X/T)

so the Jacobian of the target's displacement is a scaled substitution of the
source's. Nilpotence survives that and invertibility alone does not. A source
with `det J = 1` whose `J(N)` is not nilpotent homogenizes to a map whose
determinant is not constant.

Measured on the 24-variable target of `alpoege12` lifted by `UnipotentStep`,
where it costs a fraction of a second.

**HOM-4 — Dimension and generators.** `target.dimension == n + 1`; the
generators of `target` are those of `source` followed by `variable`; and
`variable` satisfies RC-4 against `source.ring`.

Freshness is a constructor invariant and raises `ValueError`, as in UNI-5.

**HOM-5 — The target is cubic homogeneous.** Every non-zero component of
`target.displacement()` is homogeneous of degree three, and the component of
`T` is exactly `T`.

This follows from HOM-1 and is checked because it is what the step exists to
establish, in the shape of UNI-9. It is cheap: the check reads the monomials
and computes nothing.

**HOM-6 — The target lies in `MA^2`.** `target.filtration_degree() == 2`.

Every part of the displacement has order three, so the target is in `MA^2` and
therefore in `MA^1`. Stated because the second step left `MA^1` — UNI-8 — and a
caller needs to know that the third comes back past it. A `BCWStep` declaring
`EA^1` after this step is making a claim about a map that supports it.

**HOM-7 — The determinant is one.** `target.determinant() == 1`.

Follows from HOM-1 and HOM-3, and retained as a cheap self-check in the shape
of BCW-7, and a fraction of a second on the 25-variable target. The source's own
determinant needs no obligation of its own: HOM-3 at `S = 1` is
`det(I + J(N)) = 1`, which is Kellerness.

**HOM-8 — The slice at `T = 1` returns the source.** Substituting
`T = 1` in the first `n` components of the target gives the components of the
source.

Follows from HOM-1, and checked because it is the reason HOM-9 works rather
than an arithmetic detail. It is weaker than HOM-1 and is not a substitute for
it: at `T = 1` all three slots contribute alike, so a target that lifted
`N_(1)` by `T` and `N_(2)` by `T^2` would pass this check and fail HOM-1. The
page says so rather than leaving a reader to assume the two are the same
statement.

**HOM-9 — Transport.** With `source(a) = source(b) = c`,

```
a  |-->  (a, 1),        c  |-->  (c, 1)
```

The appended coordinate is one, and not zero as in BCW-8, UNI-11 and every
other transport on this page. A zero would give `target(a, 0) = (a, 0)`, which
is a fixed point of the target and no collision at all.

Distinctness needs no argument: the points differ before the coordinate is
appended and the appended value is the same for all of them.

**HOM-10 — Provenance is recorded, and not settable.** As BCW-9.

**HOM-11 — The parameter occurs to degree at most two.** In every
monomial of `target - X` the exponent of the fresh generator is at most two.

This is the second half of Theorem 2.1(b), and HOM-1 already gives it: the
parts of the displacement are scaled by `T^2`, by `T` and by one, and by
nothing else, so no target of this step can breach it. It is retained for the
reason HOM-5 to HOM-8 are retained, and it turns the half of 2.1(b) this step
is responsible for from an argument into a check.

**HOM-12 — A multi-affine source gives a multi-affine target.** If no
variable occurs squared in any monomial of `source - X`, then no variable other
than the fresh generator occurs squared in any monomial of `target - X`.

This is the first half of Theorem 2.1(b), and the step neither produces it nor
could: by HOM-1 every monomial of the target's displacement is a monomial of
the source's times a power of the parameter, so the step creates no square it
was not given. What reaches the property is `reduce_to_multi_affine` under
UNT-12, at degree three. The obligation says that the last stage does not lose
it again.

It is conditional, and therefore says nothing about a source that is not
multi-affine, which is every source this project had before `0.7`. That is
deliberate. An obligation that refused such a source would break the chain
towards the gradient form, which runs through this step and does not want the
property; `docs/architecture.md` records why the two ends of the pipeline fork
here.

Two stages of the chain lie between the refinement and this step: the
normalization, which is a `TranslationStep` and a `LinearStep`, and the
`UnipotentStep`. Each preserves the property, and LIN-7, TRA-9 and UNI-13 say
so. *Amended when milestone 0.9 opened.* Until then this paragraph said that
both stages preserve the property by inspection and that neither is held to
it, and it left open whether UNI wants an obligation of its own. The decision
is in `docs/roadmap.md` under "Version 0.9".

### Which of these can fail on supplied data

HOM-1 for a supplied target, and HOM-2 and HOM-3 always.

HOM-3 is the one to weigh most heavily. It is the only obligation on this page
that can fail on a source a *previous step of this library produced*: a chain
that homogenizes without lifting first will reach it, and the failure is a
statement about the order of the chain rather than about either step. UNI-2
plays the same part one step earlier, and the two together are what keep the
three stages of Section 4 in their order.

HOM-4 in its freshness half is a constructor invariant and is not reachable by
`verify()`. HOM-5 to HOM-8 follow from HOM-1 and are retained as self-checks
that localize an error to the step that made it. There is no invertibility
obligation here, because there is nothing exhibited to be invertible.

HOM-11 and HOM-12 follow from HOM-1 in the same way and are self-checks for the
same reason. HOM-12 is the one to read twice: it is the only obligation in this
family whose hypothesis is a property of the source that the source is not
required to have, so it passes silently on every map this project carried
before `0.7`.

*Amended when the checks were implemented.* This paragraph asked for a negative
control that supplies a multi-affine source and a target breaking the
conclusion. There is no such control, and the reason is the order of `verify()`:
HOM-1 runs first, and by HOM-1 every monomial of the target's displacement is a
monomial of the source's times a power of the parameter, so a target that
breaks HOM-11 or HOM-12 breaks HOM-1 and is named as that. Both raises carry
`# pragma: no cover` with the argument beside them, as HOM-5 to HOM-7 do, and
neither takes a probe in `scripts/mutation_probe.py` for the reason that script
gives about clauses which cannot fail on supplied data.

What is controlled instead is `squared_terms`, which both read. Its control is
a map that is multi-affine in the variables a source began with and squares a
coordinate an earlier stage bought: that map satisfies the reading this project
carried until `0.7` and not the theorem, and the predicate reports it.

---

## CompressionStep

Collision-hull compression, Theorem 3 of arXiv:2608.12543v2. It restricts a
homogeneous Keller map to the smallest invariant subspace containing a
collision, and it is the first step in this library that *lowers* the
dimension.

```python
def collision_hull(source, collision) -> tuple[Basis, tuple[int, ...]]: ...


@dataclass(frozen=True)
class CompressionStep:
    source: PolynomialMap
    target: PolynomialMap
    basis: tuple[tuple[sp.Expr, ...], ...]
    variables: tuple[sp.Symbol, ...]
    provenance: Provenance

    @classmethod
    def build(cls, source, collision, factory=None) -> CompressionStep: ...
```

It lives at the top level, in `kellermap.compression`, and not in
`kellermap.bcw`. That subpackage holds one paper, Bass, Connell and Wright of
1982, and nothing else; this is somebody else's, of 2026, and putting it beside
`BCWStep` would say it is theirs.

Write `n` for `source.dimension`, `d` for the degree of the source's
displacement `h`, `B` for `basis` as an `m x n` matrix of rows, and `m` for
`len(basis)`.

### Three things that are new here

**The target shares no generator with the source.** Every step written before
this one extends: its target carries the source's variables followed by fresh
ones, and RC-4 is about the fresh half. The symmetric lift, written after it,
does not extend either. Here the target lives in `m` coordinates of a subspace,
its generators are all fresh, and none of the source's appears in it. RC-4
still applies, and it now covers every generator of the target rather than the
added ones.

**`build` takes a collision.** The transformation is not determined by the
source alone: a different collision generates a different hull. `UnipotentStep`
and `HomogenizationStep` need only their source, `BCWStep` needs a choice, and
this one needs the very thing the other steps merely carry. A step therefore
records which subspace it restricted to, and `transport` will refuse a
collision that does not lie in it.

**Transport can refuse a genuine collision.** Everywhere else, any collision of
the source transports. Here a collision whose points leave `W` has no image in
the target's coordinates at all, and CHC-9 says so rather than producing
something.

Transport does run both ways, unlike the homogenization's. Distinct
coordinates give distinct points of `W`, and the restriction commutes with the
inclusion, so a collision of the target is a collision of the source. The page
states this because HOM makes the opposite statement two sections above and the
difference is easy to miss.

**CHC-1 — The identity.** For the displacements `h` of the source and
`hbar` of the target,

    B^T hbar(c) == h(B^T c)

as a polynomial identity in the target's ring, in every component.

This is the whole of the correctness. It says that `W` is invariant under `h`,
because the left side lies in `W` for every `c`, and that the target is the
restriction written in the recorded basis. Invariance therefore needs no
obligation of its own.

**CHC-2 — The basis is a basis.** `basis` is a tuple of `m` vectors, each
of `n` coordinates over the source's coefficient domain, and they are linearly
independent. The domain has to be a field of characteristic zero, as under
CHC-8 and for the same reason: the elimination that decides independence
divides by a pivot. Being an invariant of the constructor, that raises
`ValueError` like the rest of this obligation, where `collision_hull` raises a
`VerificationError` citing CHC-8. The page and the code disagreed about which
until an audit of `0.6.0rc2`.

The entries are stored through the domain and not as they arrived. Over a
fraction field `(T^2 - 1)/(T - 1)` and `T + 1` are one element and two
expressions, and storing the expression gave two steps that verify alike,
describe one restriction and compare unequal, which STEP-5 forbids. A value the
domain cannot represent raises `ValueError` and not whatever the domain
raises.

A constructor invariant, raising `ValueError`. A dependent list describes no
subspace of dimension `m` and no step, and a wrong length describes nothing at
all. Independence is a rank computation over the domain and is not deferred to
`verify()`, in the shape of BCW-2.

**CHC-3 — The source's displacement is homogeneous of degree at least
two.** Every non-zero component of `source.displacement()` is homogeneous of
one degree `d`, and `d >= 2`.

Can fail on supplied data, and it is where the third stage of the Reduction
Theorem and this construction meet: `HomogenizationStep` is what produces a
source that satisfies it, as `UnipotentStep` is what produces one for HOM-3.

The polarization is what needs it. A form of one degree has a symmetric
`d`-linear polarization and a sum of forms of several degrees does not, so the
iteration of CHC-8 has nothing to iterate. The lower bound is not a further
restriction: a Keller map whose displacement is homogeneous of degree one is
`I + N` with `N` a constant nilpotent matrix, which is injective, so no
collision exists to compress.

**CHC-4 — The source is Keller.** `source.determinant() == 1`.

Nilpotence of `J(h)` is what Lemma 2 needs, and here it does not need an
obligation, which is the one place this section is shorter than the
homogenization's. Under CHC-3, `J(h)(lambda x) = lambda^(d-1) J(h)(x)`, so
`det(I + lambda^(d-1) J(h)(x)) = 1` for every `lambda`, and over an infinite
field that is `det(I + s J(h)(x)) = 1` as a polynomial in `s`. The
characteristic polynomial of `J(h)` is then `lambda^n` and Cayley-Hamilton
gives `J(h)^n = 0`.

HOM-3 has to check the same property because its source is *not* homogeneous
and the implication is unavailable there. Here one determinant does the work of
two, and the page records the argument rather than the coincidence.

**CHC-5 — Dimension and generators.** `target.dimension == m`;
`variables` are the generators of the target, in order; each of them satisfies
RC-4 against `source.ring`; and `m <= n`.

The freshness half is a constructor invariant. A target generator named like a
source generator would mean two different things by one name in one chain,
which is worse here than elsewhere precisely because the two rings have nothing
else in common.

**CHC-6 — The target inherits the shape.** The target's displacement is
homogeneous of the same degree `d`, and `target.determinant() == 1`.

Both follow from CHC-1, CHC-3 and CHC-4, and both are retained as cheap
self-checks in the shape of BCW-7. The determinant is the one that localizes an
error: a restriction to a subspace that is invariant but wrongly transcribed
will usually still be homogeneous.

**CHC-7 — No `EA` claim.** `filtration_level` is `math.inf`, as for
`HomogenizationStep` and for the same reason: there is no composition with
elementary automorphisms here, so there is no stage of the filtration to
declare.

**CHC-8 — The hull.** `collision_hull(source, collision)` returns a basis
and the sequence of dimensions that reached it. With `T` the symmetric
polarization of `h`,

    d! T(w_1, ..., w_d) = sum over non-empty S in {1..d} of
                          (-1)^(d - |S|) h( sum of w_j for j in S )

and

    W_0     = span of the points of the collision
    W_(v+1) = W_v + span{ T(w_1, ..., w_d) : w_j a basis vector of W_v }

The iteration stops when the dimension does not grow, which happens after at
most `n` rounds. Taking the `w_j` from a basis rather than from all of `W_v` is
the same span, because `T` is `d`-linear.

The division by `d!` needs the coefficient domain to have characteristic zero,
and the elimination needs it to be a field. This paragraph said DOM-1 fixes
that; DOM-1 says only that the domain is a stated argument, so nothing fixed
it and nothing checked it. Both are preconditions of this obligation now, and
`collision_hull` raises against it. Theorem 3 of that paper works over a field
of characteristic zero throughout.

The returned sequence is *descriptive*. It is not stored on the step and it is
not part of any certificate: a supplied basis has no sequence, and storing one
beside a basis would be storing the same fact twice with two ways to disagree.
What the sequence is for is the control, where `2, 4, 11, 20, 20` on
`examples.thompson24_homogeneous` is a number this project did not set itself.

**CHC-9 — Transport.** Each point and the image are expressed in the
basis: the coordinates of a point `v` are the unique `c` with `B^T c = v`.

If any point or the image is not in the span, `transport` raises and cites this
obligation. It is the only transport on this page that can refuse a collision
that genuinely holds for the source, and the refusal is the honest answer: the
target is a map on `W`, and a point outside `W` has no coordinates there.

Distinctness is preserved because `B` has rank `m`, so distinct points of `W`
have distinct coordinates. STEP-4 therefore holds, and it holds in the other
direction too.

**CHC-10 — Provenance is recorded, and not settable.** As BCW-9. The
public constructor takes a basis and records `SUPPLIED`; `build` computes the
hull and records `CONSTRUCTED`.

### Which of these can fail on supplied data

CHC-1 for a supplied target, CHC-3 and CHC-4 always, and CHC-9 for a collision
the step was not built from.

CHC-2 and the freshness half of CHC-5 are constructor invariants and are not
reachable by `verify()`. CHC-6 follows from CHC-1 with CHC-3 and CHC-4, and is
retained as a self-check.

The interesting entry is CHC-1 on a *supplied* basis, because it is doing two
jobs at once. A basis that spans a subspace which is not invariant makes the
identity unsatisfiable by any target, so the failure is reported against the
target while the fault is in the basis. The exception says both.

### Deliberate non-obligations of this type

**No minimality.** The certificate does not check that `W` is the smallest
invariant subspace containing the points, and does not need to: any invariant
subspace containing them gives a restriction that is Keller and keeps the
collision. Minimality is a property of `collision_hull`, which is a
construction rather than an obligation, and that paper claims only
route-specific minimality: Corollary 7 for the number forty and Proposition 8
of its version 2 for the number thirty-eight.

**No claim that compression helps.** Nothing requires `m < n`. A collision
whose hull is the whole space compresses to itself, which is a correct step and
a useless one. Whether a step is a good step is a question for the search, as
BCW-1 already says for the degree.

---

## SymmetricLiftStep

The symmetric lift, part 3 of Theorem 3 of arXiv:2608.12543v2. It turns a
homogeneous Keller map into the gradient form of a quartic, over `k(i)`.

```python
@dataclass(frozen=True)
class SymmetricLiftStep:
    source: PolynomialMap
    target: PolynomialMap
    variables: tuple[sp.Symbol, ...]
    provenance: Provenance

    @classmethod
    def build(cls, source, factory=None) -> SymmetricLiftStep: ...

    @property
    def form(self) -> sp.Expr: ...
```

It lives in `kellermap.lift`, beside `kellermap.compression` and not in it. The
two are the same paper and not the same construction, and a module named for
what it does is what this package has everywhere else.

Write `m` for `source.dimension`, `h` for its displacement, `d` for the degree
of `h`, and `X` and `Y` for the first and last `m` of `variables`. Then

    P = i * sum over j of  Y_j * h_j(X + i Y)
    target = (X, Y) - grad(P)

`P` is homogeneous of degree `d + 1` and the target is again homogeneous of
degree `d`, in twice as many variables.

### Why a gradient form is the point

Everything before this in milestone 0.6 produces a Keller map. This produces a
Keller map that is the gradient of an exhibited form, which is a strictly
stronger thing to have. It is what the de Bondt-van den Essen reduction asks
for, and at `d = 3` the quartic `P` is a counterexample to the quartic case of
Zhao's Vanishing Conjecture whenever the source is a counterexample to the
Jacobian conjecture.

That is a consequence and not a new result, and it is why SYM-2 is stated as an
obligation rather than left in prose. A claim that some potential exists is not
checkable; `P` on the page is.

### Three things that are new here

**The coefficient domain grows.** The lift adjoins `i`, so a source over `QQ`
gives a target over `QQ(i)`. Every other step in this library keeps the domain,
and `guards.settled` even uses equality of domains as an invariant no `BCWStep`
can cross. This one crosses it deliberately, and SYM-5 says so; a source whose
domain already contains `i` gains nothing.

**Transport takes a pair, and it is asymmetric in it.** The lift sends `p` to
`(p, 0)` and `q` to `(q + rho, i rho)`. Two questions follow and they have
different answers. *Which two points* are lifted the step does not decide:
SYM-9 refuses a collision that does not have exactly two, and the caller
narrows a wider one, which is a real step since everything this milestone
builds carries three. *Which of the two is `p`* the step does decide, under
SYM-8, because a collision compares its points as a set and a caller has no
order to express.

**The determinant is not checked.** It is the first obligation on this page
that is left out on cost rather than kept as a cheap self-check. SYM-7 says
what was measured and what the affordable substitute is worth.

**SYM-1 — The identity.** `target == (X, Y) - grad(P)` with `P` as
displayed, checked as a polynomial identity in one shared `PolyRing`.

**SYM-2 — The target is a gradient map.** `target == id - grad(P)` for
the `P` that SYM-1 exhibits, and `form` returns it.

The same equation as SYM-1, and the page states it twice on purpose: SYM-1 is
"the target is what the formula gives" and SYM-2 is "the target has a
potential, and here it is". A reader checking the first is checking arithmetic;
a reader checking the second is checking the property this milestone was for.

**SYM-3 — The source's displacement is homogeneous of degree at least
two.** As CHC-3, and needed for the same reason at one remove: `P` is
homogeneous of degree `d + 1` only if `h` is homogeneous of degree `d`. A
source that fails this lifts to a form with no degree at all.

Can fail on supplied data, and it is where the compression and this step meet:
`CompressionStep` is what produces a source that satisfies it, and so is
`HomogenizationStep`.

**SYM-4 — The source is Keller, over a field of characteristic zero.**
`source.determinant() == 1`, and the coefficient domain is a field of
characteristic zero.

The second half is the boundary Theorem 3 states for both of its constructions
and CHC-2 and CHC-8 already draw for the compression. It was missing here until
an audit of `0.6.0rc2`, and a source over `GF(5)` reached SymPy's own
`UnificationFailed` instead of an answer: adjoining `i` is a statement about a
field. This paragraph named CHC-4 for that boundary, which is the obligation
about the source being a Keller map, until the next audit corrected it.

The determinant is compared by `canonical.agree` and not by `!=`, so a source
over `RR` whose determinant is `1.0` is not refused for the spelling.

Nilpotence of `J(h)` needs no obligation here, by the argument CHC-4 gives:
under SYM-3 a constant determinant is `det(I + s J(h)) = 1` for every `s`, and
Cayley-Hamilton finishes it. The two obligations are the same statement about
the same shape of source, and the page says so rather than repeating the
derivation.

**SYM-5 — Dimension, generators and domain.**
`target.dimension == 2 * m`; the `2m` generators are those of `variables`, in
order, and each satisfies RC-4 against `source.ring`; and the coefficient
domain of the target is the source's with `i` adjoined.

The generators are all fresh, as in CHC-5 and for the same reason: the target
is a map on a different space and shares no coordinate with its source.

The domain clause is the new one. It is checked and not assumed, because a
target supplied over `QQ` for a source over `QQ` would satisfy every other
obligation here up to the point where a coefficient of `P` fails to be
representable, and the failure would then be reported as an arithmetic one.

**SYM-6 — The degrees.** `form` is homogeneous of degree `d + 1`, and
every non-zero component of `target.displacement()` is homogeneous of degree
`d`.

Implied by SYM-1 with SYM-3, and checked because both are cheap: the check
reads monomials and computes nothing.

**SYM-7 — The determinant is one, and it is not recomputed.**
`det J(target) = 1` follows from SYM-1, SYM-3 and SYM-4 by part 3 of Theorem 3,
which gives that the Hessian of `P` is nilpotent. `verify()` does not compute
it.

This is a departure from UNI-10, HOM-7 and CHC-6, which all keep the
determinant as a cheap self-check, and it is a departure on a measurement
rather than on a preference. On the thirty-eight-variable lift of
`spacerat11`, `determinant()` was stopped after nineteen hours and
forty-eight minutes without returning. `docs/milestones.md` under work package 1
of milestone 0.7 records the runs and the machines they were made on.

That run used the fraction-free elimination of `DomainMatrix.det()`, which
MAP-4 replaces with a division-free one. The paragraph below lists the
elimination among the properties of the complement that were never isolated,
and it is isolated now. `scripts/measure_lift_determinant.py` put three routes
on that complement, each under the same budget of time and of memory, and none
of them returned. The fraction-free elimination spent the whole budget without
reaching the memory limit; both division-free routes reached the limit, the one
through the characteristic polynomial first. So the elimination is not what the
cost rests on, and the departure stands on a measurement that now covers the
route this library takes as well as the one it took. `docs/milestones.md`
records that run, dated and with the machine it was made on, under what the
determinant costs on the lift.

The failure differs even though the outcome does not. A caller who asks this
method for the determinant of a complement of that size now meets a memory
limit in hours rather than a computation that runs for as long as it is given.
That is the same answer in the end, which is no answer, and it arrives
differently.

**The reason is the carrier and not the dimension.** `determinant()` takes the
Schur complement of the unipotent block a map carries, so a BCW-reduced map is
left with a determinant of a size that does not grow with it: the unipotent
step, the homogenization and the compression leave six, six and six for
`spacerat11` at 22, 23 and 19 variables, and four at each of the three for
`alpoege12`. The gradient form of a quartic carries no such block. Of the 38
coordinates of the lift, 28 have a diagonal entry of one and 10 survive the
acyclicity test, so the complement is 28 by 28 with 13589 monomials in it.
Forming it is a matter of a moment. Its determinant is the whole of the
cost.

Those figures are recomputed by `scripts/measure_pipeline.py`, which `make
measure` runs, since `0.7.0rc12`. This paragraph said four at every
BCW-reduced stage and 29 by 29 at the lift until then, which was right for
neither, and nothing recomputed the column it rested on. `docs/errata.md`
records it; `docs/milestones.md` carries the table for all three chains.

This paragraph named dimension six against dimension forty until `0.7`, and
read as a statement about size. Size is what it is not. The lift is the one
target in the chain that gives up the structure the other three stages are
cheap by.

What was not isolated is which property of that complement carries the cost --
its width, the density of its entries, the coefficient domain or the
elimination used. Each candidate probe changed the problem instead of scaling
it. Narrowing the complement by a different acyclicity rule reached 21 by 21
and 13627 monomials, denser rather than smaller, and bought nothing; that rule
is not in the code and those two figures were not re-measured with the rest. A leading
`k` by `k` submatrix is a smaller matrix with a far larger answer, because the
determinant of the whole is one and a corner of it cancels not at all. Any
probe that does not preserve that cancellation measures a different kind of
problem, and none that preserves it is cheap.

What is affordable is the determinant at a point: under a minute, and one, at each
of two random rational points of the space. That is the check the
`reconstruct_*` scripts make and it is worth exactly what they say it is worth
-- a value other than one falsifies the claim, and agreement at finitely many
points does not prove it.

So the obligation is not checked, a test computes the determinant at dimension
six as an independent cross-check in the sense `AGENTS.md` gives that phrase,
and a caller who wants more on a real lift has the sample-point route and the
knowledge that the polynomial one is out of reach.

**SYM-8 — Transport, and the vector it goes through.** With
`source(p) = source(q)` and `p != q`,

```
rho = (I + J h(q)^T)^-1 (p - q)
p  |-->  (p, 0)
q  |-->  (q + rho, i rho)
```

Which of the two points is `p` the step decides and the caller does not. COL-6
makes a collision a statement about a *set*, so a step that took the order its
tuple happened to carry would send two equal collisions to two unequal results,
and both would verify. `0.6.0rc1` did that until an audit found it.

The order is a function of the two points and not of their printed form. It
asks `==` first, so everything after that sees two values already known to
differ; then `Basic.compare`; then metadata of the class, which is its module,
its qualified name, its declared assumptions and the keywords it was built
with. Four orderings were tried before this one, and `docs/errata.md` says what
each of them missed.

**The order can refuse, and that is part of this obligation.** Where two
unequal values compare equal and their classes agree in all four components,
`transport` raises and cites SYM-8 rather than taking the order the tuple
happened to carry. The refusal is deterministic and is the same for either
order of arrival.

No totality is claimed. This paragraph said the order "has to be total on
expressions" and named `srepr` as the implementation until an audit of
`0.6.0rc5`; the first was a claim nothing established and the second had been
stale since `0.6.0rc3`. What is claimed is weaker and checkable: the order
decides or it refuses, and it never depends on the order of arrival.

The refusal is reachable from valid supplied data, and this page implied it was
not. `Function("g", nargs=1)` and `Function("g", nargs=(1, 2))` are two classes
with one name, one module and one set of declared assumptions; the metadata of
`0.6.0rc5` tied on them, and a collision that holds was refused. The
construction keywords decide that pair. That they decide every pair is not
something this page asserts.

`rho` is computed and not stored, since the source and the pair determine it,
and the equation `(I + J h(q)^T) rho = p - q` is checked rather than the
inverse trusted. That is the same shape as UNI-6: an exhibited object with its
defining equation checked beats an asserted one.

The residual is decided by `canonical.agree`. `expand` is not a decision
procedure for a rational function, and `0.6.0rc2` refused a collision that
holds because a residual that is zero did not expand to zero.

**SYM-9 — A collision of more than two points is refused.**
`transport` raises and cites this obligation.

The lift carries a pair. Which pair, and which of the two is `p`, changes both
lifted points, so a step that picked would be making a mathematical choice
silently. Every collision this milestone produces has three points, so this is
reached in practice and not in principle.

**SYM-10 — The two lifted points are distinct.** The argument is on the
second block and not the first: `p != q` gives `p - q != 0`, hence
`rho != 0`, hence `i rho != 0`, which is the second block of one point against
the zero of the other. STEP-4 therefore holds without an argument about the
first block, where `p` and `q + rho` might in principle agree.

**SYM-11 — No `EA` claim.** `filtration_level` is `math.inf`, as for
`HomogenizationStep` and `CompressionStep`.

**SYM-12 — Provenance is recorded, and not settable.** As BCW-9.

### Which of these can fail on supplied data

SYM-1 and SYM-2 for a supplied target, SYM-3 and SYM-4 always, SYM-5's domain
clause for a supplied target, and SYM-8's orientation and SYM-9 for a supplied
collision.

SYM-8 stands in both categories and is the only obligation on this page that
does. Its equation for `rho` cannot fail where the arithmetic is right and is a
self-check of it. Its orientation can fail on a collision that holds, when the
two points cannot be put in an order by anything the step reads. This paragraph
named only the self-check until an audit of `0.6.0rc5`, and a reader took from
it that a valid collision always transports.

SYM-6 follows from SYM-1 and is retained because it is free. SYM-7 is
not checked at all, which is a third category this page has not needed before,
and the section above says what was measured before it was put there.

### Deliberate non-obligations of this type

**No minimality.** That paper states two route-specific ones. Corollary 7: forty
is minimal among examples obtained by restricting Thompson's map to an
invariant subspace containing the collision and then applying this lift
unchanged. Proposition 8 of its version 2, for the other route: the collision
hull of van Rijn's nineteen-variable map is the whole space, so no proper
invariant linear restriction retaining that collision lowers the
thirty-eight-variable lift, in any codimension. Both are statements about one
route each, both are the paper's and not this project's, and nothing here
claims either for any other route.

**No claim about Zhao's Vanishing Conjecture beyond the construction.** The
quartic form is a counterexample to it when the source is one. That is a
consequence of published theorems, and this library produces the object rather
than the theorem. What can be checked about that object is under
VanishingWitness.

---

## VanishingWitness

A witness to Zhao's Vanishing Conjecture: the gradient form of a symmetric
lift, a collision of its gradient map, and the finite checks that can be made
on the two. Theorem 3, part 4, of arXiv:2608.12543v3 says what it witnesses.
W. Zhao, *Hessian nilpotent polynomials and the Jacobian conjecture*, Trans.
Amer. Math. Soc. 359 (2007), 249-274, gives the theorems it is checked
against. `docs/milestones.md` under "Version 0.8" states the conjecture and says
what each finite check is worth.

```python
@dataclass(frozen=True)
class VanishingWitness:
    lift: SymmetricLiftStep
    collision: Collision
    depth: int = 2

    @property
    def form(self) -> sp.Expr: ...

    def verify(self) -> None: ...
```

It lives in `kellermap.vanishing`. It is not a step. It changes no map and
takes nothing to a target, so it has no `transport`, no `filtration_level` and
no provenance of its own.

`form` is `lift.form` and is not stored a second time. The nilpotent Hessian of
the form is what makes it a witness, and for a lift that follows from a
verified source by Theorem 3. That is the reason the witness takes a lift and
not a quartic.

Write `P` for `form`, `n` for `lift.target.dimension` and `Delta` for the
Laplacian in the variables of the lift.

**VAN-1 — The lift verifies, and its source is cubic.**
`lift.verify()` passes, and the displacement of `lift.source` has degree three. `P` is then a
homogeneous quartic by SYM-6.

Part 4 of Theorem 3 is stated for degree three only, and Zhao's conjecture is
about quartics. A lift of a source of degree two gives a cubic form that
witnesses nothing here. A lift of degree four or more gives a form this page
has no theorem for.

A lift that does not verify is reported as VAN-1, with the obligation of the
lift that failed named in the message and attached as the cause. The
implementation made this choice: a caller of the witness branches on the
witness's obligations, and the lift's own is one step further down.

**VAN-2 — The collision is a collision of the gradient map.**
`collision.verify(lift.target)` passes: the points are distinct and
`id - grad(P)` sends them to one image.

The witness does not require that the collision came from `lift.transport`. A
collision found any other way witnesses the same thing, and the obligations of
`Collision` check it the same way. A failure is reported as VAN-2, with the
COL obligation that failed in the message and as the cause, for the reason
given under VAN-1.

**VAN-3 — The hypothesis holds to the stated depth.**
`Delta^m(P^m) = 0` for `1 <= m <= depth`, checked as polynomial identities.

Zhao's Theorem 4.3: the Hessian of `P` is nilpotent if and only if this holds
for every `m >= 1`, and if and only if it holds for `m <= n`. His proof gives
the finite form: for a fixed `k`, vanishing for `m <= k` is equivalent to
`Tr Hes^m(P) = 0` for `m <= k`. Through Newton's identities and the degrees of
the Hessian's entries, depth `k` is equivalent to the vanishing of the
homogeneous parts of degrees `2, 4, ..., 2k` of `det J(id - grad(P))`. That
last step is this page's derivation and not Zhao's. So VAN-3 at depth `n`
would be SYM-7, and at a smaller depth it is a truncation of it.

The default depth is two because depth three needs `P^3`, which has more than
three million monomials at forty variables. `docs/milestones.md` has the
measurement. A depth below one or above `n` is refused with a `ValueError`: the
first checks nothing, and the second checks nothing more than depth `n`. A
depth that is not an integer, a `bool` included, is refused with a
`TypeError`. Both happen when the witness is constructed, before anything is
computed.

**VAN-4 — `Delta(P^2)` is not zero.** Checked as a polynomial.

By Zhao's Corollary 3.9, a Hessian-nilpotent `P` with `Delta(P^2) = 0` has
`Q_t = P`. The formal inverse of `z - grad(P)` is then `z + grad(P)`, which is
a polynomial, and `id - grad(P)` is injective. VAN-2 exhibits a collision, so
VAN-4 follows from VAN-2 and Theorem 3. It is checked because it relates the
collision to the form through a published theorem, and both are cheap: one
square and one Laplacian.

The number of monomials of `Delta(P^2)` is not an obligation. It depends on the
coordinates. For the forty-variable lift of Thompson's map it is 8 630, the
figure Section 4 of arXiv:2608.12543v3 states, and the gates hold it there.

**VAN-5 — The conclusion fails, and it is not checked.**
`Delta^m(P^(m+1)) != 0` for infinitely many `m`. This follows from VAN-1 and
VAN-2 by Theorem 3, part 4, of arXiv:2608.12543v3, which rests on Zhao's
Theorems 3.4 and 4.3. `verify()` does not compute it.

It is left out for a different reason than SYM-7. SYM-7 is a computation that
was measured and did not finish. VAN-5 is one that is out of reach before any
measurement. Values at small `m` do not decide eventual vanishing. A non-zero
value at one `m` above `B_n = (3^(n-1) - 3) / 2` would refute it, because a
polynomial inverse of a cubic map has degree at most `3^(n-1)` (Bass, Connell
and Wright, Chapter I, Corollary (1.4), p. 292), and `Delta^m(P^(m+1))`
contributes a term of degree `2m + 3` to the inverse. That is the argument of
Zhao's proof of Proposition 7.4. The bound is sufficient. That no smaller
index could decide the question is not shown, and this page does not claim it.
At `n = 38`, `B_n` has eighteen digits. VAN-5 is therefore derived from the
verified lift and the collision.

Until `0.8.0rc2` this paragraph said that VAN-5 cannot be finished. An audit
of `0.8.0rc1` showed that this is too strong, and `docs/errata.md` records
it.

### Which of these can fail on supplied data

VAN-1 always, since it verifies the lift, and for a lift of the wrong degree.
VAN-2 for a supplied collision. The depth of VAN-3 is refused before anything
is computed.

The vanishing in VAN-3 and the value in VAN-4 cannot fail on a lift that
verifies. Both follow from Theorem 3 and a verified source, so they are
cross-checks of this library's arithmetic against Zhao's theorems. Their
negative controls therefore cannot go through `verify()` on a real lift, in
the same way as for HOM-12. The two checks are the functions
`check_hypothesis` and `check_conclusion_at_one` in `kellermap.vanishing`, and
`verify()` calls them. The controls call them directly: `X^4` fails VAN-3 at
depth one, `Re (X + i Y)^4` passes depth one and fails depth two, and
`(X + i Y)^4` passes VAN-3 at every depth and fails VAN-4.

VAN-5 is not checked at all.

### Deliberate non-obligations of this type

**No quartic without a lift.** A bare quartic with a collision would need its
Hessian to be nilpotent, and that is VAN-3 at depth `n`, which is not
affordable. With a lift it is a theorem about a verified source.

**No figure of the conclusion.** `Delta^m(P^(m+1))` for small `m` is a
measurement and belongs to the scripts that measure. It establishes nothing
about the conjecture either way.

**No minimality**, of the form or of its dimension, for the reasons under
SymmetricLiftStep.

---

## DescentStep

The fourth move of the two published derivations at degree three, and the one
this library has had no step type for. Work package 4 of milestone `0.7`
settled that it is missing rather than expected to be: six of the seven step
types cannot lower a dimension at all, and the seventh, `CompressionStep`,
restricts along a linear embedding under CHC-1 and wants a homogeneous
displacement under CHC-3, where this move restricts to the level set of a
quadric on a map whose displacement carries two degrees at once.

**What the move is.** Two changes of determinant one, one on each side, after
which one coordinate is triangular and can be deleted. In Macfarlane's
thirteen-variable map the two are a source graph on the pair `(x_13, x_2)` and
a target completion on the pair `(y_4, y_8)`, and the completion cancels a
quartic because `x_8 + x_1 x_2` is already a component. The eleven-variable
derivation reaches the same shape by a different route.

**Where it sits.** At degree three, among the moves of the reduction, and not
in the chain towards the gradient form. It stands last here because it is the
newest and because it joins no chain this library builds; the pipeline is the
seven types above.

It is the second of the eight step types that lower a dimension, after
`CompressionStep`, and the only one whose target may have a higher degree than
its source.

**Why the identifier is `DSC`.** The obvious three-letter abbreviation of
"descent" spells a German article, which is on the word list of
`tests/test_language.py`, so every line citing such an obligation would be
reported as German. The check is right to do that: it reads a lowered line and
cannot tell an identifier from a word. An exemption added to make a prefix fit
would weaken the list for every page, and a prefix is the cheaper thing to
change. A new family should be tried against that list before it is written
out.

**What this family does not do.** It does not look for the two changes. The
step verifies a claim a caller supplies, and searching for the pair is a
separate thing that comes after, on the division `BCWStep` and `peel` already
stand on. So there is no `build()` in `0.7`, and DSC-7 says what follows from
that.

The step keeps the source, the index of the coordinate to delete, and the two
automorphisms. Everything else is derived: the conjugate `left . source .
right`, the tail that the deleted component carries, and the target.

**DSC-1 — The conjugate and the deletion.** With
`C = left . source . right` and `k = index`, `target` has as its components the
`C_j` for `j != k`, in their order, read in the ring of DSC-2.

Derived and not supplied, for the reason `G` and `H` are derived in BCW-3:
storing the target beside the two automorphisms would let a reader be told two
things that can disagree. What cannot be derived is the tail, `C_k - X_k`,
because the deletion is what throws it away; the step keeps it, and DSC-6 is
what it is kept for.

**DSC-2 — Dimension and generators.** `target.dimension ==
source.dimension - 1`, the generators are the source's with the `k`-th removed,
in order, and the coefficient domain and the monomial order are the source's.

The last clause is not decoration. An audit of `0.7.0rc1` found the target
being rebuilt from expressions, which re-infers a ring: a source over `QQ` gave
a target over `ZZ`, and over a finite field that changes the characteristic and
with it the arithmetic of every step after this one.

The second step type that lowers a dimension, after `CompressionStep`. It
lowers it by one where CHC-5 lowers it to the rank of a hull, and the two are
otherwise unrelated: one deletes a coordinate that has become triangular, the
other restricts to a subspace a collision lies in.

**DSC-3 — The coordinate is triangular in the conjugate.** In
`C = left . source . right`,

    C_k - X_k   is free of X_k, and
    C_j         is free of X_k for every j != k.

This is the claim the caller supplies and the obligation the family exists for.
Everything else here either follows from it or is a property of the objects
handed in. A step whose two automorphisms do not make the coordinate triangular
fails here and nowhere else, and the exception names the coordinate and the
component that still mentions it.

The second half is what makes the deletion well defined rather than a
truncation. Without it the components that survive would still refer to a
generator that the target does not have.

**DSC-4 — The two changes are exhibited.** `left` and `right` are
`ElementaryAutomorphism`s over the source's ring, each stored as its ordered
factorization, and each is applied on the side it is named for: `right` on the
source's variables, `left` on the components.

Being over the source's ring is checked and names this obligation, at every
public route into the step: `verify`, `target`, `conjugate` and `tail`. Until
`0.7.0rc1` it was not checked at all, and the mismatch surfaced from inside
`ElementaryAutomorphism.apply_to` as a bare `ValueError` naming neither the
obligation nor the side it came from. `0.7.0rc2` checked it on the first two
and an audit found the other two still leaking, together with the test that was
meant to cover them and called `target`.

Determinant one is not checked, because it is not a claim here. An
`ElementaryFactor` is `X_j |-> X_j + P` with `P` free of `X_j`, so its Jacobian
is unitriangular and the determinant of a product of them is one by
construction. That is the shape of BCW-4 and BCW-5: the factorization is kept
so that "invertible with determinant one" is something a reader can see rather
than something the page asserts.

An automorphism with no factors is admitted on either side. The move needs one
change on each side in Macfarlane's derivation and the page does not know that
every instance does.

**DSC-5 — The determinant carries over.** `target.determinant() ==
source.determinant()`.

A self-check of this library's own arithmetic. Under DSC-3 the Jacobian of `C`
is block triangular with a one in the `k`-th place on the diagonal, and the two
automorphisms contribute one each by DSC-4, so the two determinants agree. It
is here because the descent is the only move in this library that could quietly
lose the Keller property while lowering a dimension, and a caller should not
have to recompute a determinant to find that it did not.

**DSC-6 — A collision transports, and the transport is exhibited.** For a
`Collision` of the source at points `p_1, ..., p_r`, the transported points are
the `right.inverse()(p_i)` with their `k`-th coordinate deleted, and they are a
`Collision` of the target.

They stay distinct, which is not automatic for a projection and is worth the
argument. If two of them agreed, the two points they come from agreed outside
`k` and had the same image under `C`; the `k`-th component of `C` is
`X_k + (C_k - X_k)` with the tail free of `X_k` by DSC-3, so their `k`-th
coordinates agreed too and the points were one point.

**DSC-7 — Provenance is recorded, and not settable.** As BCW-9, with one
difference: `0.7` gives this type no `build()`, so every instance is `SUPPLIED`
and nothing in this milestone can produce a `CONSTRUCTED` one.

That is the integrity marker doing its job rather than a gap. A descent whose
two changes came from a caller is a different thing from one this library
found, and until there is a search to find them, saying so is the whole of what
provenance has to say here.

### Which of these can fail on supplied data

DSC-3 always, and DSC-4 in the part that asks the two arguments to be
automorphisms over the source's ring.

DSC-1 and DSC-2 are constructor invariants and are not reachable by `verify()`.
DSC-5 and DSC-6 follow from DSC-3 and are retained as self-checks that localize
an error to the step that made it, in the shape HOM-5 to HOM-8 are retained.

DSC-3 is the one to weigh. It is the only obligation in this library whose
failure says nothing about the map it was given and everything about the claim
that came with it: the source may be perfectly good and the two automorphisms
simply wrong.

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

## The certificate file

A certificate outside the running process. A file holds a chain, the maps it
passes through, collisions of those maps and a witness. It holds nothing that
can be derived from them. The library writes such a file and reads it back.
The checker of the next section reads it without the library.

Every obligation of this section and the next carries the marker of milestone
0.9. Work package 2 stated them before anything was written. The obligations of
this section are implemented since work package 3, and those of the next
since work package 4. `docs/roadmap.md` under "Version 0.9" records the four
decisions they rest on: JSON with structured coefficients, every map of a chain
written once, the checker as a package of its own in the wheel, and the
coefficient domains that the chains of this project use.

```python
@dataclass(frozen=True)
class Certificate:
    chain: Reduction | PolynomialMap
    collisions: tuple[tuple[int, Collision], ...] = ()
    witness: VanishingWitness | None = None

    @property
    def steps(self) -> tuple[Step, ...]: ...

    @property
    def maps(self) -> tuple[PolynomialMap, ...]: ...

    def verify(self) -> None: ...

    def dumps(self) -> str: ...

    @classmethod
    def loads(cls, text: str) -> Certificate: ...
```

It lives in `kellermap.certificate`, at the top level. A file is not a notion
of the 1982 paper, by the argument this page makes for `Reduction`.

`chain` is a `Reduction`, or a single map when the certificate holds no step.
`steps` is the steps of the chain, and none for a single map. `maps` is
derived. It is the source of the chain followed by the target of
every step, or the single map. Position `0` is the source, and position `i + 1`
is the target of step `i`. A collision is attached to a map by its position.
The witness takes its lift from the steps of the chain and its collision from
the collisions.

### What a file holds

A file is one JSON object, written in UTF-8. The names in capitals stand for
the parts described below.

```
{
  "format": "kellermap-certificate",
  "version": 1,
  "maps": [MAP, ...],
  "steps": [STEP, ...],
  "collisions": [COLLISION, ...],
  "witness": WITNESS
}

MAP        = {"ring": RING, "components": [POLYNOMIAL, ...]}
RING       = {"generators": [NAME, ...], "order": ORDER, "domain": DOMAIN}
STEP       = {"type": TYPE, ...the parameters of its constructor...}
COLLISION  = {"map": POSITION, "domain": DOMAIN,
              "points": [[ELEMENT, ...], ...], "image": [ELEMENT, ...]}
WITNESS    = {"step": INDEX, "collision": INDEX, "depth": INTEGER}

POLYNOMIAL = [[[EXPONENT, ...], ELEMENT], ...]
DOMAIN     = "ZZ" | "QQ" | "ZZ_I" | "QQ_I"
           | {"polynomial": BASE, "parameters": [NAME, ...], "order": ORDER}
           | {"fraction": BASE, "parameters": [NAME, ...], "order": ORDER}
           | {"quadratic": NUMBER}
BASE       = "ZZ" | "QQ" | "ZZ_I" | "QQ_I"
ORDER      = "lex" | "grlex" | "grevlex"
```

`NAME` is a name as FMT-7 describes it, and `NUMBER` is a number as FMT-6
describes it. `INDEX`, `POSITION`, `EXPONENT` and `INTEGER` are JSON integers.
`TYPE` is the name of a step class, and `ELEMENT` is an element of the domain
in force, as the first table below shows.

`witness` may be left out. The other keys are always present, and a list may
be empty where FMT-2 allows it. An element of a domain is written as follows.

| domain | element |
| --- | --- |
| `ZZ` | a `NUMBER` that is an integer |
| `QQ` | a `NUMBER` |
| `ZZ_I` | `[a, b]` for `a + b i`, with `a` and `b` integers |
| `QQ_I` | `[a, b]` for `a + b i` |
| `{"quadratic": d}` | `[a, b]` for `a + b sqrt(d)` |
| a polynomial ring over `B` | a `POLYNOMIAL` in the parameters, over `B` |
| a field of fractions over `B` | `{"numerator": POLYNOMIAL, "denominator": POLYNOMIAL}` |

A step is written with the fields of its constructor, listed here besides
`type`, whose value is the name of the class.

| `type` | fields |
| --- | --- |
| `BCWStep` | `index`, `left`, `right`, `filtration_level`, `coefficient` |
| `LinearStep` | `transformation`, `normalizing` |
| `TranslationStep` | `shift`, `normalizing` |
| `UnipotentStep` | `variables` |
| `HomogenizationStep` | `variable` |
| `CompressionStep` | `basis`, `variables` |
| `SymmetricLiftStep` | `variables` |
| `DescentStep` | `index`, `left`, `right` |

A slot of a `BCWStep` is `{"fresh": {"polynomial": POLYNOMIAL, "variable":
NAME}}` or `{"carried": INDEX}`. A linear transformation is a list of factors,
each one of `{"transvection": {"index": ..., "source": ..., "coefficient":
...}}`, `{"transposition": {"first": ..., "second": ...}}` and
`{"dilation": {"index": ..., "coefficient": ...}}`. Each side of a descent is
a list of elementary factors `{"index": INDEX, "polynomial": POLYNOMIAL}`.
Every polynomial of a step lies in the ring of the step's source. Every
coefficient, every entry of a shift and every entry of a basis is an element
of that ring's domain.

**FMT-1 — One format, one version. [0.9]** A file is one JSON object with the
keys shown above and no others, and every object inside it has the keys shown
for it and no others. `format` is `"kellermap-certificate"` and `version` is
`1`. A reader refuses any other value and any key it does not know.

An unknown key may carry a meaning that a later version gives it. A reader that
skipped it would accept a file it does not understand.

A reader also refuses an object that has one key twice, a value of the wrong
JSON type, and the constants `NaN`, `Infinity` and `-Infinity`. `true` and
`false` stand only where a boolean is asked for, which is `normalizing`. A
boolean where an integer is asked for is refused.

*Amended in work package 2.1, after an audit of work package 2.* The paragraph
above was added. Python's `json` module keeps the last of two equal keys and
accepts `NaN`. It reads `true` as `True`, which Python treats as an integer
equal to `1`. The first wording excluded none of the three.

**FMT-2 — Every map once, every step between two maps. [0.9]** `maps` has one
entry more than `steps`. Step `i` takes the map at position `i` to the map at
position `i + 1`. A map that is the target of one step and the source of the
next is written once.

RED-2 therefore holds by the layout of the file and not by a comparison, with
the one exception that FMT-4 names. A file with no step holds exactly one map,
and it is read back as a certificate whose chain is that map. RED-1 is not
weakened: no empty `Reduction` is built.

**FMT-3 — A step is written as the parameters of its constructor. [0.9]** The
fields of a step are the parameters of its public constructor, under the same
names, without `source` and `target`. Those two are the positions of FMT-2. A
parameter that has a default is written all the same, so that a file says what
the step is without a reader knowing the defaults of this library.

Nothing a step derives is written. That excludes `G` and `H`, `P` and `Q`, the
form of a lift, the conjugate and the tail of a descent, `rho`, a transported
collision, the dimensions of a hull, a determinant and an attained filtration
level. This is the rule of BCW-3 and of the certificates in general: a value
stored beside the data it is derived from can disagree with that data. The
constructors already take exactly the data that cannot be derived. So the rule
needs no list of its own beyond the table above.

**FMT-4 — A target that its step derives is compared and not taken. [0.9]**
`DescentStep` takes no target, and DSC-1 derives it. Its target is still
written at its position, because every map is. `loads` derives the target and
compares it with the written map. A difference is refused and cites DSC-1.

This is the one place where the layout of FMT-2 does not give RED-2 by itself.
It is also the one comparison that `loads` makes. FMT-10 says why it cannot be
left to `verify()`: the object read back cannot hold both maps.

**FMT-5 — The coefficient domains. [0.9]** The domain of a map is `ZZ`, `QQ`,
`ZZ_I` or `QQ_I`, or a polynomial ring or a field of fractions over one of
these four, in named parameters and with a monomial order. The domain of a
collision may also be a quadratic field `QQ(sqrt(d))`, for a square-free
integer `d` other than `0`, `1` and `-1`. Writing a map or a collision over any
other domain is refused and cites this obligation.

The list holds the domains that the chains and witnesses of this project use:
`ZZ` and `QQ` along the reductions, `QQ_I` after the symmetric lift, `ZZ[T]` in
the parametric examples, and `QQ(sqrt(-23))` for the collision of Gao's map.
Every domain on it has characteristic zero, so COL-7 holds for every collision
a file can hold. The value `-1` is excluded because that field is `QQ_I`, and
one field has one name.

`sqrt(d)` is the number SymPy gives that name. For `d > 0` it is the positive
square root. For `d < 0` it is `i` times the positive square root of `-d`, the
root with positive imaginary part. An element `[a, b]` is `a + b sqrt(d)` with
that root. *Amended in work package 2.1, after an audit of work package 2.* The
first wording did not say which of the two roots is meant.

Finite fields are left out. A chain over `GF(p)` carries no collision by COL-7
and no witness, and no file of this project needs one.

General algebraic fields are left out, and the quadratic field is admitted for
collisions only. Two measurements made while this section was written are the
reason. SymPy compares algebraic fields by the expression that generated them.
`QQ<sqrt(-23)>` rebuilt from its minimal polynomial and the index of a root is
`QQ<CRootOf(t**2 + 23, 1)>`, and the two compare unequal, so a map over such a
field would not read back equal to itself. And `kellermap.canonical` does not
decide coordinates written through `CRootOf`. The collision of Gao's map was
written that way, over the field of degree four that SymPy constructs for it,
and read back under each of the four roots. Under two of them the values agree
with the original to thirty digits, and under none of them does
`kellermap.canonical` find them equal. A quadratic field has the coordinate
`sqrt(d)`, which SymPy writes as a radical, and neither problem arises. Maps
over an algebraic field are possible in this library and occur in its tests,
but in no chain. Widening the list is an amendment of this obligation.

**FMT-6 — Exact numbers, one spelling each. [0.9]** Every coefficient is a
JSON string, a `NUMBER`. An integer is written in decimal, with a minus sign
when it is negative and without leading zeros, and zero is `0`. A rational that
is not an integer is written `p/q`, with `q > 1` and `p` and `q` coprime.
Indices, positions, exponents, the depth and the version are JSON integers.

A polynomial is a list of terms. Each term is an exponent vector and a
coefficient, with one exponent per generator of the ring of a map, or per
parameter of a domain. A term with the coefficient zero is refused, and so are
two terms with one exponent vector. A denominator of zero is refused.

An exponent is a non-negative JSON integer. An exponent vector of another
length than the number of generators or parameters is refused. The zero
polynomial is the empty list, and the zero of a field of fractions has the
empty list as its numerator. *Amended in work package 2.1, after an audit of
work package 2.* The first wording left negative exponents, vectors of the
wrong length and the spelling of zero unstated.

A float is never read. JSON has no exact rationals, and a coefficient that went
through a float would be a different number. The rules exclude every second
spelling of a value, so that a file cannot say one thing in two ways. The one
exception is an element of a field of fractions. Its numerator and denominator
are compared by value and are written as SymPy holds them, which FMT-12 makes
deterministic.

**FMT-7 — Names. [0.9]** A generator or a parameter is written by its name,
and the name matches `[A-Za-z_][A-Za-z0-9_]*`. The generators of one ring and
the parameters of its domain are pairwise distinct by name. The domain of a
collision has no parameter that is named like a generator of its map, which is
COL-2 in the terms of the file.

A symbol that carries assumptions is refused when it is written. It would be
read back as a plain symbol. `PolynomialMap` compares its variables as symbols,
assumptions included, so the map read back would not be equal to the map
written.

**FMT-8 — A collision is attached to a map, over a domain that contains the
map's. [0.9]** `map` is a position of FMT-2. The domain of the collision
contains the domain of its map, and "contains" means one of these:

- the two are equal;
- `ZZ` lies in `QQ`, `ZZ_I`, `QQ_I` and every quadratic field, `QQ` lies in
  `QQ_I` and every quadratic field, and `ZZ_I` lies in `QQ_I`;
- a base lies in a polynomial ring and in a field of fractions over a base
  that contains it;
- a polynomial ring lies in the field of fractions in the same parameters and
  order, over a base that contains its base;
- a polynomial ring or a field of fractions lies in the one of the same kind,
  in the same parameters and order, over a base that contains its base.

The checker evaluates a map at points of the collision's domain, and this is
what makes the evaluation defined. A map may carry several collisions or none.

`Collision` holds no domain, by COL-5, so `dumps` chooses one. It writes the
first domain of the following order that contains the domain of the map and
every coordinate. For a map over a base, the order is `ZZ`, `QQ`, `ZZ_I`,
`QQ_I`, and then the quadratic field of the one square-free `d` that the
coordinates need. For a map over a polynomial ring or a field of fractions, the
polynomial rings come before the fields of fractions. Each is in the parameters
and the order of the map's domain, and over the bases in the order `ZZ`, `QQ`,
`ZZ_I`, `QQ_I`. A collision for which no domain of the list qualifies is
refused and cites FMT-5. The domain a file writes is then a function of the map
and the collision. A reader accepts every domain that this obligation allows
and does not ask for the one `dumps` would choose.

*Amended in work package 2.1, after an audit of work package 2.* The rule of
the last paragraph and the last item of the list were added. A collision of
rational points over a map over `ZZ` lies in `QQ`, in `QQ_I` and in every
quadratic field, and the first wording did not say which of them a file writes.

**FMT-9 — The witness names its parts. [0.9]** `witness.step` is the index of
a `SymmetricLiftStep`. `witness.collision` is the index of a collision attached
at position `step + 1`, which is the target of that step. `witness.depth` is
the depth of VAN-3. The form is not written: VAN-1 derives it from the lift.

`Certificate` requires the same of the objects it is given. `witness.lift` is a
step of `chain`, `witness.collision` is attached to the target of that step,
and every position of `collisions` lies in `maps`. The constructor raises
`ValueError` otherwise.

**FMT-10 — A file read back is supplied. [0.9]** Every step that `loads`
builds is built through its public constructor and is `SUPPLIED`, whatever
wrote the file and whatever the provenance of the step it was written from.
The file has no field for provenance and none for the program that wrote it. A
reader could check neither, and BCW-9 says what `SUPPLIED` means: the target
was not produced by this library in this run.

This is what makes reading back a control. For a supplied step, BCW-1 and the
other identities compare a target from outside the library with the formula,
and they can fail. Reading back a chain that the library built, and verifying
it, is the first control of the format. Work package 3 runs it on every chain
of the reconstruction scripts.

`loads` does not verify, with the comparison of FMT-4 as the one exception. It
builds the objects and leaves their obligations to `verify()`.

Everything `loads` refuses, it refuses with a `VerificationError` that cites an
obligation and says where in the file it failed, in the `location` of the
section on errors. There are three kinds of refusal.

- A rule of this section that the file breaks cites that rule. A witness that
  names a step that is not a lift, or a collision at another position, cites
  FMT-9, and its location is the witness.
- A derived target that differs from the written map cites DSC-1, and its
  location is the step.
- A constructor invariant that the file breaks cites the obligation that the
  invariant belongs to. The exception the constructor raised is attached as
  the cause. A factor of a linear transformation cites LIN-2 and a factor of a
  descent cites DSC-4, as in CHK-3, because the factor types have no
  obligations of their own.

The constructors keep their exceptions. A caller who passes the same arguments
by hand gets the `ValueError` that the table of errors lists, as before.

*Amended in work package 2.1, after an audit of work package 2.* The first
wording said that a file which breaks a constructor invariant raises what the
constructor raises. The audit pointed out that the checker then cites COL-4 for
two equal points where the library raises a `ValueError` without an identifier.
No exception of a constructor said which invariant it enforces, so `loads`
could not have cited one. Work package 2.2 gave each of them the identifier,
as `InvariantError` in the section on errors.

**FMT-11 — A certificate verifies its parts and computes nothing else. [0.9]**
`Certificate.verify()` verifies the chain by RED-3, each collision against the
map at its position, and the witness. It computes nothing of its own, which is
RED-3 again. A failure names the obligation of the part and where it failed:
the index of the step by RED-4, the index of the collision, or the witness.

**FMT-12 — Writing is deterministic, and reading inverts it. [0.9]** The text
`dumps` writes depends only on what the certificate holds. It is JSON in ASCII,
with no whitespace outside strings, with the keys of every object sorted by
code point, and with one newline at the end. In Python that is
`json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)`
followed by a newline.

The terms of a polynomial are sorted by their exponent vectors, read as tuples
of integers, in descending lexicographic order. The monomial order of the ring
does not change that. The points of a collision are sorted by the text of their
encoding, because COL-6 makes a collision a set of points. Every other list
keeps the order of the certificate, because there the order carries meaning.
The domain of a collision is the one FMT-8 chooses. A certificate and the
certificate read back from its file therefore give the same text.

`loads(dumps(c))` has the maps and the collisions of `c`, equal by value. Each
of its steps is the step that the public constructor gives for the same
arguments, that is the step of `c` with `SUPPLIED` provenance.
`dumps(loads(t))` is `t` for every text `t` that `dumps` wrote. The second half
lets a paper cite a file by a hash of its bytes.

*Amended in work package 2.1, after an audit of work package 2.* The first
wording asked for a fixed order of the terms and did not say which, so an
independent writer could not tell whether it agrees with this one. It also left
two equal collisions, whose points arrive in different orders, to be written as
two texts.

### Files and the licence rule

The values in a file are the values of the maps it holds, under the terms of
those maps. A chain to the published nineteen-dimensional map, or to
`macfarlane13`, carries a map whose source has no licence. Those two maps are
in `tests/data.py`, and no distribution of this project ships that file.

So the repository holds no certificate file. The tests write theirs into a
temporary directory, and a test of work package 3 fails on a file of this
format anywhere in the tree. `AGENTS.md` asks that a new way for values to
leave the repository is checked against the licence rule before it is used.
This paragraph is that check for certificate files. Somebody who writes a file
of such a chain holds its values under their terms, as somebody who reads
`tests/data.py` does.

### Which of these can fail on supplied data

FMT-1 to FMT-9 can fail on a file from outside. Each of them is a reason to
refuse a file, and FMT-9 is also a reason to refuse the arguments of the
constructor. FMT-10 and FMT-12 are obligations on the library's own conduct.
FMT-11 adds no check of its own; what can fail there is what can fail in the
parts.

### Deliberate non-obligations of the format

**No transport.** A file holds the collisions it is given. It does not hold
the result of transporting one, unless that result is given to it as a
collision of its own. A collision is checked against its own map, by COL-3,
and that check needs no transport.

**No intermediate results.** A search that has not finished has no
certificate, and the format has no place for one.

**No signature and no author.** A file says nothing about who wrote it, by
FMT-10. Whether a file arrived unchanged is a question for the hash of its
bytes, which FMT-12 makes stable.

**No compatibility promise beyond the version.** A reader of version `1`
reads version `1`. What a later version reads is for that version to state.

---

## The independent checker

A second implementation of the checks a file needs, without the library. It
reads a file of the format above and reaches one of the three verdicts of
CHK-6. It is the eight
reconstruction scripts made general: each of them repeats one chain in plain
SymPy, and the checker repeats any chain a file holds.

```python
class Refusal(Exception):
    obligation: str  # "FMT-6", "BCW-1", "COL-3", ...
    location: str  # "step 4", "map 0", "collision 1", "witness", "file"
    message: str


@dataclass(frozen=True)
class Report:
    verdict: str  # "VERIFIED" or "INCOMPLETE"
    checked: tuple[tuple[str, tuple[str, ...]], ...]  # location, identifiers
    skipped: tuple[tuple[str, tuple[str, ...]], ...]
    not_computed: tuple[str, ...]  # "SYM-7", "VAN-5"
    claims: tuple[str, ...]
    not_claimed: tuple[str, ...]


def check(text: str, skip: Iterable[str] = frozenset()) -> Report: ...
```

From the command line it is `python -m kellermap_check FILE`, with `--skip ID`
for each check to leave out. CHK-6 says what the verdicts mean and CHK-7 what
a `Report` holds.

*Amended in work package 4.* The sketch gained `not_claimed`, which CHK-7
asks for since work package 2.1 and the first sketch did not hold. `skip` takes
any iterable of identifiers, as the command line passes a list.

**CHK-1 — Independent of the library. [0.9]** The checker is the package
`kellermap_check`. It imports nothing from `kellermap`, directly or through
another module, and nothing outside the standard library and SymPy. A test
holds it to that, as `tests/test_scripts.py` holds the reconstruction scripts.

The test has two parts. It reads the source of the package and finds no import
of `kellermap`. And it imports `kellermap_check` in a fresh interpreter and
finds no module of `kellermap` loaded afterwards. The second part covers an
import through another module, which the first cannot see. *Amended in work
package 2.1, after an audit of work package 2.* The first wording named a test
and not what it does.

Independent means independent of the code of this library. SymPy is shared,
and an error in SymPy could reach both. The page does not claim more.

**CHK-2 — Shipped in the wheel. [0.9]** The package is in the wheel beside
`kellermap`, with the same lower bounds for Python and SymPy. `kellermap` may
import it, and the command line of work package 6 may do so for `kellermap
verify`. The checker never imports `kellermap`, so the dependency runs one way.

The wheel and the source archive both carry the package, and
`tests/test_packaging.py` checks both. The coverage run measures the package
beside `kellermap`, with the same threshold of 100 per cent, so
`[tool.coverage.run]` names both source directories. *Amended in work package
2.1, after an audit of work package 2.* The configuration measures
`src/kellermap` alone, and the first wording would have left the checker
outside the threshold.

**CHK-3 — It refuses what the format refuses. [0.9]** The checker reads a file
by the rules of FMT-1 to FMT-9 and refuses a file that breaks one of them,
citing it. It calls no constructor of the library, because it has none. So
every constructor invariant that a file can break is a check of the checker,
and it cites the obligation the invariant belongs to. An invariant that the
library enforces without an identifier of its own cites the obligation of the
step it serves: LIN-2 for the factors of a linear transformation, whose
inverse it makes exist, and DSC-4 for the factors of a descent.

**CHK-4 — What it checks. [0.9]** For every object, the obligations that can
fail on supplied data, and the constructor invariants a file can break.

| object | checked |
| --- | --- |
| a collision | COL-1, COL-3, COL-4 |
| `BCWStep` | BCW-1, BCW-2, BCW-4, BCW-6, BCW-10, BCW-11, BCW-12 |
| `LinearStep` | LIN-1, LIN-2 for the factors, LIN-6 except its `MA^1` clause |
| `TranslationStep` | TRA-1, the first clause of TRA-6 |
| `UnipotentStep` | UNI-1, UNI-2, UNI-3, UNI-4, UNI-5 |
| `HomogenizationStep` | HOM-1, HOM-2, HOM-3, HOM-4 |
| `CompressionStep` | CHC-1, CHC-2, CHC-3, CHC-4, CHC-5 |
| `SymmetricLiftStep` | SYM-1, SYM-3, SYM-4, SYM-5 |
| `DescentStep` | DSC-1, DSC-2, DSC-3, DSC-4 |
| the witness | VAN-1, VAN-2, the range of the depth in VAN-3 |

Four obligations hold by the format and are checked as part of it. COL-2 is
FMT-7, and COL-7 follows from FMT-5. BCW-3 and TRA-2 follow from FMT-6 and the
rule that every polynomial and every coefficient of a step lies in the ring of
its source: a polynomial with one exponent per generator of the source cannot
mention a fresh variable, and an element of the domain mentions no generator.
SYM-2 is SYM-1 read as a statement about a potential and needs no second
computation. The clauses of LIN-6 that are checked are the `MA^0` clause, the
unit determinant and the product with `J(source)(0)`. DSC-1 is a check here and
not an invariant, because a file writes the target that the library
derives.

Four of these take a determinant: UNI-4, HOM-3, CHC-4 and SYM-4. The library
takes them without dividing, after the Schur complement of MAP-4. The checker
uses the same mathematics, written on its own. Its block is the coordinates
whose diagonal entry of the Jacobian is one. While the dependencies among them
have a cycle, it drops from each cyclic component the coordinate with the most
edges inside it. What is left is `I` plus a nilpotent matrix, and the
determinant of the complement is taken over the polynomial ring. Work package 4
measured whether the checker can afford the four on the chains of this
project. It can, on all eight, and `docs/roadmap.md` gives the measurement. A
determinant of the whole Jacobian, without the complement, could not be taken
on Thompson's map in the time the measurement allowed.

*Amended in work package 2.1, after an audit of work package 2.* The first
wording said that a determinant the checker cannot afford would be amended away
and named as not checked. The audit pointed out that a checker which still
reported such a file as accepted would report a confirmation it did not make.
CHK-6 now has a verdict for a check that was not made, and CHK-8 requires the
full verdict on the eight chains. A determinant the checker cannot afford on
one of them is therefore a failure of work package 4. It goes to the
maintainer, and it is not resolved by an amendment that lets the gate pass.

**CHK-5 — What it leaves to the library. [0.9]** The self-checks: BCW-5,
BCW-7, LIN-3, the `MA^1` clause of LIN-6, LIN-7, TRA-3, TRA-4, the `MA^0`
clause of TRA-6, TRA-9, UNI-6, UNI-9, UNI-10, UNI-13, HOM-5, HOM-6, HOM-7,
HOM-8, HOM-11, HOM-12, CHC-6, SYM-6, DSC-5, VAN-3 apart from the range of its
depth, and VAN-4. Each follows from obligations the checker checks, and this
page says which at each type. A second computation of a consequence is a
cross-check of arithmetic and no further evidence about the file.

SYM-7 and VAN-5 are computed neither by the library nor by the checker. The
transports are not checked, because a file holds no transport: BCW-8, LIN-5,
TRA-7, UNI-11, HOM-9, CHC-9, SYM-8, SYM-9, SYM-10 and DSC-6 have nothing to act
on. Nor are the properties of the types that a file does not carry, such as a
filtration level or a provenance.

**CHK-6 — Three verdicts, and a refusal names one obligation. [0.9]** A run of
the checker ends in one of three verdicts.

- `VERIFIED`: every check of CHK-3 and CHK-4 that applies to the file was made,
  and every one passed.
- `INCOMPLETE`: every check that was made passed, and at least one that
  applies was not made. The only reason is a caller who asked to leave out
  named checks, and the report names them. `INCOMPLETE` is not an acceptance.
- `REFUSED`: a check failed.

A refusal stops at the first check that fails. The order is fixed: the file by
the format, then the maps, the steps, the collisions and the witness, each in
the order of the file. Within one object the order is fixed by the package and
written in its documentation. So one file always gives one refusal.

`check` returns a `Report` for the first two verdicts. For the third it raises
`Refusal`, with the identifier, the location and a message. `skip` names checks
to leave out, by identifier, wherever they apply. An identifier that is not in
the table of CHK-4 is a wrong call and not an empty skip, as for a selector of
`scripts/mutation_probe.py`.

The exit status is 0 for `VERIFIED`, 1 for `REFUSED`, 2 for a file that cannot
be opened or a wrong call, and 3 for `INCOMPLETE`. The value 3 is the one
`scripts/gate_outcome.py` uses for a script that checked nothing, and the two
mean the same: nothing failed, and something was not checked. A file that
opens and is not JSON is refused under FMT-1 and exits with 1.

*Amended in work package 2.1, after an audit of work package 2.* The first
wording had two outcomes, accepted and refused. A check that was left out could
then be read as one that was made.

**CHK-7 — A report says what its verdict rests on. [0.9]** The report lists,
for every object, the identifiers the checker checked and those it left out at
the caller's request. It states the claims of the file that the checker
confirmed: that each step takes its map to the next, that each collision is a
collision of its map, and that the witness is a witness. Where the file holds a
lift or a witness, the report names SYM-7 and VAN-5 as consequences that were
not computed. They do not make a verdict `INCOMPLETE`, because neither is a
check of CHK-4.

The report also says what is not claimed. By RED-3 the checker computes no
global invariant, so it does not check that the first map of a chain is a
Keller map. Only a step that asks for it checks its own source, as UNI-4, CHC-4
and SYM-4 do. A file with no step and no collision makes no
mathematical claim, and the report says so in those words. Such a file is not
refused. Its verdict says that the file is well formed, and nothing about the
map.

*Amended in work package 2.1, after an audit of work package 2.* The second
paragraph was added. The audit pointed out that a file with one map passes
every check and confirms nothing, and that a successful read must not be
mistaken for a proof that a map is Keller.

**CHK-8 — Its controls. [0.9]** Three kinds.

On each of the eight chains of the reconstruction scripts, the checker returns
`VERIFIED` for the file the library writes, and the maps and collisions that
the script computes are the ones in the file. No chain depends on
`tests/data.py`: the library reaches the end of every chain from its steps, and
the file is compared with what the script computes and not with that file.

*Amended in work package 4.* The first wording said that the two chains whose
maps are in `tests/data.py` are skipped where that file is absent. The
implementation needs no skip, so the controls run from the source archive as
well.

The negative controls. Each takes a file the checker verifies and changes one
coefficient, one slot or one point, chosen so that the change breaks an
obligation. The control states in advance which obligation the change breaks,
at which location, and why. The checker has to refuse the file with that
identifier and that location. The library has to refuse the same file when it
reads it back and verifies it. Where the library cites another obligation, the
control says why.

The positive controls. A change that keeps a file valid has to be accepted. Two
are required: the points of a collision in another order, and an element of a
field of fractions with its numerator and its denominator multiplied by one
non-zero constant. The first is a set under COL-6, and the second is the
exception of FMT-6. Both files are verified, and `loads` gives the same
certificate for each as for the original file.

*Amended in work package 2.1, after an audit of work package 2.* The first
wording said that a file changed in one coefficient, one slot or one point is
refused. As a statement about every such change that is false. A file with one
map and nothing else stays valid when a coefficient changes, and a changed
point can give another collision. `docs/errata.md` records it. The positive
controls were added at the same time.

### Which of these can fail on supplied data

None of them is a check on a file in the sense of the other families. CHK-3
and CHK-4 say which obligations of other families the checker checks, and
those carry their own answers. CHK-1, CHK-2, CHK-6 and CHK-7 are obligations
on the conduct of the checker. CHK-8 is the evidence that the checker checks
anything at all, and it is the obligation to weigh. CHK-6 is the one to read
next: it decides when an output may say `VERIFIED`.

---

## The LaTeX view

A view of a certificate file, for a reader who wants to see the chain rather
than run it. `to_latex(text)` returns LaTeX for the text of a file. Nothing in
the view is checked by the view. What makes it worth reading is that it is
made only from a file the checker verifies, and that it shows what that file
holds.

```python
def to_latex(text: str, *, standalone: bool = True) -> str: ...
```

**TEX-1 — Only from a file the checker verifies. [0.9]** `to_latex` checks the
text with `kellermap_check.check` first and goes on only for the verdict
`VERIFIED`. A file the checker refuses raises `VerificationError` with the
identifier and the location of the refusal, and the refusal as its cause. No
check is left out, so the verdict `INCOMPLETE` cannot arise.

The checker and not the library decides, because the view is a statement about
a file. `kellermap` imports `kellermap_check` for it, which CHK-2 allows; the
checker still imports nothing of the library.

**TEX-2 — It shows what the file holds. [0.9]** Every map, with its generators,
its coefficient domain, its monomial order and its components. Every step,
with its type, the two maps it joins and every parameter the file writes for
it. Every collision, with its map, its domain, its points and its image. The
witness, with its step, its collision and its depth. And what the checker's
report says: the claims it confirmed, what the file does not claim, and the
consequences it did not compute.

One thing is shown that the file does not hold: the form `P` of the lift a
witness names, which the roadmap of milestone 0.9 asks for. It is derived from
the lift by the library and labelled as derived. Nothing else is derived: not
`G` or `H` of a step, not a transport, not a determinant.

**TEX-3 — As the file writes it. [0.9]** The view is made from the text that
`Certificate.loads(text).dumps()` returns. Terms stand in the order FMT-6
writes them and points in the order FMT-12 writes them. Indices count from
zero, as in the file. So two files that hold one certificate have one view,
including a file whose points stand in another order or whose fractions are
written with a common factor.

**TEX-4 — Two forms, and no package. [0.9]** With `standalone=True` the view
is a document from `\documentclass{article}` to `\end{document}`, and `pdflatex`
compiles it without any package. With `standalone=False` it is the body of
that document, to be read into another one with `\input`; it needs no package
either. Both begin with one comment line that names them as a view of a
certificate file.

**TEX-5 — Two names are never shown alike. [0.9]** A name of one letter
followed by digits is shown as that letter with the digits as a subscript:
`x12` is `x_{12}`. Every other name is shown as itself in `\mathit`, with its
underscores escaped: `x_1` is `\mathit{x\_1}`. The imaginary unit is shown
upright, as `\mathrm{i}`, so a generator named `i` is not mistaken for it.

SymPy's own rendering of a name is not used, because it is not injective. It
shows `x1` and `x_1` both as `x_{1}`, and it gives no valid LaTeX for some
names a file admits, such as `x__`.

**TEX-6 — Plain ASCII, and text is escaped. [0.9]** The view is ASCII, so it
compiles under any input encoding. Text that comes from the report is escaped,
so a character that LaTeX reads as a command stands as itself.

### Files and the licence rule

A view holds the values of the maps in its file, as the file does. So the
repository holds no view either. The comment line of TEX-4 makes a view
findable by its content, and a test of work package 5 fails on a file that
begins with it anywhere in the tree.

### Which of these can fail on supplied data

TEX-1, on a file the checker refuses. TEX-2 to TEX-6 are obligations on the
library's own output.

### Deliberate non-obligations of the view

**No check of its own.** The view repeats nothing the checker did, and a
compiled document is not checked by anybody. The file is the certificate; the
view is a way to read it.

**No layout.** Long components are left to the line breaking of TeX. A
long vector may run past the margin, which `pdflatex` reports as an overfull
box and not as an error.

---

## The command line

A program `kellermap` with two commands, for a reader who has a file and no
wish to write Python. It adds no behaviour of its own: each command calls what
the checker and the view already do, and these obligations say how.

```
kellermap verify FILE [--skip ID ...]
kellermap latex FILE [--output OUT] [--body]
```

**CLI-1 — `verify` is the checker. [0.9]** `kellermap verify` runs the command
line of `kellermap_check`, with the same arguments, the same output and the
same exit status as `python -m kellermap_check`, CHK-6. Only the name of the
program in a usage message differs. The checker and not the library decides,
for the reason it decides for the view: the command answers a question about
a file.

**CLI-2 — `latex` is the view. [0.9]** `kellermap latex` writes what
`to_latex` returns for the text of the file: the document, or with `--body`
the body, TEX-4. It writes to the standard output, or with `--output` to the
file it names.

**CLI-3 — Exit status, and nothing written on failure. [0.9]** `latex` exits
with 0 when the view was written. For a file the checker refuses it exits with
1 and prints the identifier, the location and the message, as `verify` does.
For a file that cannot be read, an output that cannot be written, or a wrong
call it exits with 2. A refused file writes nothing: no view and no file of
that name. The status of `verify` is the checker's.

**CLI-4 — One program, two ways in. [0.9]** The wheel installs the program
`kellermap` through an entry point in `pyproject.toml`, and
`python -m kellermap` is the same program. A command that is not one of the
two, or no command, is a wrong call and exits with 2.

### Which of these can fail on supplied data

None of them checks data. A file is checked by the checker, through CLI-1 and
CLI-2, and the command line only passes on its verdict.

### Deliberate non-obligations of the command line

**No standard input.** A command reads a file it is given by name. A file is
small, and a name is what a refusal and a report can point to.

**No command of its own.** There is no `kellermap check` that would verify
with the library instead of the checker. A caller who wants that writes the
two lines of Python `docs/api.md` shows.

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

`conjugate` and `diagonal_matching` remain and carry no *SEA* obligation. They
answer a question still worth asking -- in what respect two chains that are the
same reduction differ -- and nothing that `verify()` or this clause asks. What
`conjugate` does owe its caller is its own family, `CNJ`, below: the withdrawal
of the diagonal from SEA-5 left the function in place and left its promises
unnamed, and until `0.7.0rc9` its docstring still attributed them here. An audit
of `0.7.0rc8` found that, and found it costing something rather than merely
reading oddly: a mutation probe for the unit rule had been filed under `SEA-5`,
so one selector stood for two unrelated promises.

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

**Two fresh slots of one value are two coordinates here.** Sharing one is
BCW-12's saving, a `Candidate` asks for it with `shared`, and
`enumerate_candidates` never does: SEA-14 gives the forward space distinct
fresh coordinates, so equal values cost two and the step is `m = 2`.

Asked for and not inferred from the two polynomials being equal, which is how
`Candidate` decided it until `0.7.0rc6`. `shared` is the whole of the intent
since `0.7.0rc7`: `shares_one_generator` is `shared` and both slots fresh, with
no equality test of its own. A `Candidate` carries expressions and no ring, so
the only equality available to it is SymPy's structural one, which is not the
equality the step is built under; `0.7.0rc6` kept that test and so reported
`shared=True` beside `m == 2`, describing nothing. Whether the two values
really do agree is decided where a ring exists to decide it, in `BCWStep` under
BCW-12. For the same reason `untargeted_candidates` sets `shared` only where
both slots are fresh and equal in `source.ring`, rather than on every candidate
it emits. An audit of `0.7.0rc5` found both
directions of that conflation. The forward search could not express a verified
step with two distinct coordinates of one value and called its space exhausted
after thirty maps instead; and it did build a shared one, naming two
coordinates and consuming one, which is a chain outside the space SEA-14
describes. Neither was a false certificate -- the step holds under BCW-12 --
and both were the search disagreeing with its own statement of where it looks.

`Candidate.factors` refuses a surplus of names as well as a shortage since
then. That is the invariant which failed silently while `m` was inferred.

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

"Is a pool value" is decided in the ring of the map the walk has reached, with
both sides as `PolyElement` and the sign included. A pool value is a spelling
of a polynomial and which spelling it is says nothing: over `GF(2)` the value
`3z^2` and the factor `z^2` are one element, and over `QQ(T)` so are
`(T+1)z^2` and `((T^2-1)/(T-1))z^2`. Until `0.7.0rc6` the comparison ran on
expanded expressions, so an exact match written differently missed, the slot
was named at the cost of a rewrite, and with no rewrites left the chain was
dropped and the space reported as exhausted — a claim this obligation makes
about the space, and it was false. A pool value that does not convert into the
ring of the reached map names a generator that map does not have yet; it is an
exact match for nothing and stays available for a rewrite, as before.

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

**A co-factor that a coordinate holds is offered both ways.** As that carrier,
which costs no dimension, and bought from the pool, which costs one. Both,
since `0.7.0rc5`, and only the carried form before it.

Which coordinates count as holding it is BCW-10's own condition,
`carrier_indices_for_factors`, and every coordinate that holds the value rather
than the first of them. That is the correction `0.7.0rc4` made in the
untargeted walk and in the pruning rule of `peel`, and it could not be made
here on its own. The carried form displaced the bought one in the
deduplication, and the bought form is what a pool name fills, so widening the
carrier condition alone removed a chain the search used to find: the unweighted
control of SEA-14 then exhausted at 2667 maps with nothing. Offering both is
what makes the widening a widening.

It costs branching, and the figure is worth having. That control examines 3189
maps where it needed 200, about sixteen times as many, and finds the same
chain.

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

That reading makes the pruning a place to be careful, because a wrong premise
there does not narrow a decision, it falsifies a report. The rule that prunes a
branch standing one coordinate above the source does so when the source has no
carrier, since a further step could then only buy. A carrier there is
`carrier_indices_for_factors` since `0.7.0rc4`. It was `carrier_indices`, which
is a unipotent block and is empty on a linear map whose coordinates depend on
each other in a cycle, although every one of them satisfies BCW-10. An audit of
`0.7.0rc3` found the peel reporting an exhausted space on such a source with a
verified two-step chain inside its bounds.

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

A carrier here is `carrier_indices_for_factors`, BCW-10's own condition. Until
`0.7.0rc4` this enumerator asked `carrier_indices`, which is a unipotent block
and drops every coordinate on a dependency cycle, so a coordinate a step can
use was passed over: on `(x + y^2, y + x + z, z + 2x + y^2, w + y^4)` it bought
a coordinate where one step drops the degree to three and buys nothing. The
figures above are unchanged by the correction, which was measured before it was
made.

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

**UNT-12 — The multi-affine walk anchors on the squared monomial, and it is a
second enumerator.** At a map of degree at most three,
`reduce_to_multi_affine` offers one candidate per pair of a factorization
`M = P Q` into two parts of positive degree and an admissible assignment of the
two slots, over every monomial `M` of the displacement in which some variable
occurs squared. A candidate whose target does not lower `remaining_excess` is
left out. A source above degree three is refused by name, since the normal
form of Theorem 2.1(b) is cubic as well.

*Amended at `0.7.0rc3`, in the words "and an admissible assignment of the two
slots".* It said one candidate per factorization, which is what the walk did
until it stopped choosing a slot assignment greedily; on
`(x + y^2, y, z + y)` one factorization now yields two candidates. An audit of
`0.7.0rc2` found the count. The obligation is widened rather than the walk
deduplicated: the alternatives are what let the pair that buys least win, and
"Which slot a factor gets" below says why choosing greedily costs a
coordinate.

*Amended when the walk was implemented, and the amendment is the first two
sentences.* This obligation required `P` and `Q` each to be free of a square,
and it said the walk refuses a factorization whose carrier occurs in the
opposite factor or whose two slots name one coordinate. Both were wrong, and
in opposite directions.

The first made the smallest case of the theorem unreachable rather than
expensive. `y^3` has no factorization into two square-free parts at all, so a
walk under the old wording offers nothing at `(x + y^3, y)` and never starts.
What keeps the walk finite is the measure below and not the shape of the
parts.

The second refused where it should pass over. A carrier that would square a
variable is not the only way to supply that factor: the factor can be bought
instead, which costs a dimension and keeps the step. Refusing leaves a map with
no candidate where one exists, and a walk that has to arrive cannot afford
that. The wording says *passed over* now.

**The measure.** `remaining_excess` is the sum of `3 ** excess(M)` over the
monomials of the displacement that square a variable, where `excess(M)` is the
total degree less the number of variables in it. Zero exactly when the map is
multi-affine.

The base is three because two would not do. A step removes `M` and puts
`X_u Q`, `P X_v` and `X_u X_v` in its place, and gives `Q` a component of its
own when its slot is fresh. Only two of those five can square a variable, and
each carries the excess of `Q`, which is at least one below the excess of `M`.
So the measure falls whenever `base ** e > 2 * base ** (e - 1)`.

A base below three is refused, and the falling measure is the whole reason.
Being zero exactly on a multi-affine map is not: that fails at zero alone,
where every term is zero, and holds at one and at two where every term is
positive. Until `0.7.0rc1` this function refused nothing at all, and
`base = 0` reported zero on a map that squares a variable; the amendment that
added the guard gave that as a second reason for the bound, and an audit of
`0.7.0rc2` found that it is a reason for refusing zero and not for asking
three.

**The walk arrives, and that is a consequence and not a hope.** For any
monomial of excess `e` the split into its radical and the rest is among the
candidates and lowers the measure, and a measure of positive integers cannot
fall forever. The count of squared monomials would not do instead: the first
step on `y^3` replaces one by two while the measure falls from nine to six.

**Why it is not UNT-1 with another stopping rule.** UNT-2 says the space is
empty at degree three, and says that this is the stopping rule of the
untargeted search rather than a condition placed on it. UNT-1 also caps each
part of a split at `deg(F) - 2`, which is one at degree three, so the split
this walk needs -- a part of degree two against a part of degree one -- lies
outside both obligations. Widening them would weaken a correct statement about
the degree reduction in order to house a different walk, so neither is amended
and this obligation stands beside them.

**Which slot a factor gets.** Component `i` of a `BCWStep` target is
`(F_i - c P Q) - X_u Q - P X_v - X_u X_v`. The product cancels, and the three
terms that replace it are free of a square exactly when `u` does not occur in
`Q`, `v` does not occur in `P`, and `u` and `v` are two coordinates rather than
one. A coordinate that already holds a factor supplies it and costs nothing,
UNT-9; a coordinate that would break one of the three conditions is passed
over and the factor is bought.

Holding a factor is BCW-10's third clause and nothing stronger, which is what
`PolynomialMap.carrier_indices_for_factors` returns: `F_j - X_j` free of `X_j`,
decided on the monomial support. It is not `carrier_indices`, which asks a
different question and not merely more of the same. The two agree in
characteristic zero up to the acyclicity; over `GF(2)` the map
`(x + x^2, y + y^2, z + z^2)` has the identity for its Jacobian and no
displacement free of its own variable, so the block is the whole map and no
coordinate is a carried factor. There the two are `(0, 1, 2)` and `()`, so one
does contain the other; in general neither contains the other, and the wording
here claimed the concrete example showed that until `0.7.0rc7`. What the
example shows is that they differ, which is the point being made.

`carrier_indices` is a set of coordinates whose
dependencies are acyclic, which is what makes the block it picks out unipotent,
and its docstring says it is deliberately not maximal. That is the right
question for the block and the wrong one for a factor. Until `0.7.0rc3` this
walk asked it, and on `(x + y, y + x + z, z + 2x + y, w + y^2)` the first
coordinate holds `y` and lies on a cycle, so the walk bought a coordinate the
map already had and reached six where five is enough.

Every coordinate that holds a value, and not the first of them. Two can hold
one, and which serves depends on the split.

A slot on the component the step acts on cannot arise, and there is no branch
against it, for the reason `_slot` gives for the two enumerators above. A
carrier's value is its whole displacement, the acting component's displacement
contains the squared monomial, and a factor is a proper divisor of that
monomial.

Two shapes this library admits are unreachable for this walk. The repeated
fresh slot of BCW-12 gives `X_u^2`, so two fresh slots carrying the same value
take two coordinates here and not one. Two `Carried` slots on one coordinate
give the same, and the ten-step chain of `alpoege12` takes that shape twice.
Neither obligation is withdrawn or narrowed. A multi-affine walk does not offer
them; every other walk in this library still does.

No completeness, in the shape UNT-4 gives it, and no minimality. The walk is
greedy and takes the first chain it finds, so every dimension in the table
below is an upper bound.

### What the multi-affine refinement costs

Two rules, and the second improves the first by a third.

The crude rule was measured before the walk existed: ordinary `BCWStep`s,
two coordinates bought for every squared monomial, no carrier reused. The walk
is `reduce_to_multi_affine` under this obligation. Both are upper bounds and
neither is a claim of minimality. Every step of all six chains is verified,
and the last column is the endpoint of Theorem 2.1(b), reached through
`LinearStep.normalize`, `UnipotentStep` and `HomogenizationStep`:

| | rule | steps | multi-affine | unipotent | 2.1(b) |
| --- | --- | ---: | ---: | ---: | ---: |
| `alpoege13`, 13 | crude | 10 | 33 | 66 | 67 |
| `alpoege13`, 13 | walk | 10 | 19 | 38 | 39 |
| `alpoege12`, 12 | crude | 12 | 36 | 72 | 73 |
| `alpoege12`, 12 | walk | 12 | 23 | 46 | 47 |
| `spacerat11`, 11 | crude | 14 | 39 | 78 | 79 |
| `spacerat11`, 11 | walk | 14 | 24 | 48 | 49 |

The walk's column moved by one, one and two at `0.7.0rc2`. Until then the
carrier map kept one coordinate per value where two can hold it, so the walk
bought a coordinate it already had; an audit of `0.7.0rc1` found it costing the
dimension six that the smallest case reaches. The figures before the correction
were 20, 24 and 26.

The walk's three chains were run again after the correction and are what the
table carries; they were blank in `0.7.0rc2` rather than filled in with
`2n + 1`, which is arithmetic and not a certificate.

All six endpoints have no squared variable other than the
parameter and no
power of the parameter above two, which is the pair HOM-11 and HOM-12 state.
The count exempts the parameter and nothing else, so the coordinates the
refinement and the unipotent reduction buy are counted with the rest.

Carrier reuse is the whole of the difference between the two rules. The step
count is identical under both; what changes is how many coordinates a step
buys, and that is the same saving UNT-9 records for the degree reduction.

Which carrier, as well as whether one. A value can be held by two coordinates
and only one of them serve a given split, so the walk offers every admissible
pair of slots rather than choosing greedily from the left, and lets the
ordering take the pair that buys least.

The order inverts under both rules. The smallest map at degree three gives the
largest endpoint, where the four stages of milestone `0.6` were monotone on the
same three maps.

### What verifying these six chains cost

The determinant of UNI-9, in seconds, beside the dimension it ran at. All six
on one machine, which the figures of `0.7.0rc1` were not:

| | crude | walk |
| --- | --- | --- |
| `alpoege13` | 168 at 66 | 279 at 38 |
| `alpoege12` | 225 at 72 | 58 at 46 |
| `spacerat11` | 28 at 78 | 60 at 48 |

The cheapest of the six is the largest and the dearest is the smallest: 28
seconds on 78 coordinates against 279 on 38. Nothing here is monotone in the
dimension, and the direction is not even constant between the two rules on one
map: the walk costs `alpoege13` two thirds more than the crude rule at 28
coordinates fewer, costs `alpoege12` a quarter of it, and costs `spacerat11`
about twice.

So a timing taken on one of these maps says nothing about the others, and this
page states none of them as a cost of the stage. It is consistent with what
work package 1 found -- that a determinant follows the carrier rather than the
size -- and six chains that agree with a hypothesis are not a test of it. What
would test it is a run that varies the carrier and holds the dimension, and
that has not been done.

One regularity is worth recording because it makes the figures readable. HOM-7
costs about what UNI-9 costs in every one of the six: 166 against 168, 249
against 279, 213 against 225, 64 against 58, 28 against 28, 69 against 60. The
two obligations compute the same kind of determinant at one extra coordinate,
so the agreement is expected, and its absence would have said that one of the
numbers was noise.

The cost of verifying the chain follows neither the dimension nor the density.
The unipotent target of `spacerat11` is the widest of the three at 78
coordinates and the densest at 310 monomials, and it verifies in about a fifth
of the time `alpoege13` needs at 66 coordinates and 272 monomials. The domain
is not the reason; the figures are over `QQ` throughout. What UNI-9 spends is a
determinant, and work package 1 of milestone `0.7` found that a determinant
follows the carrier and not the size. That is a hypothesis here and not a
measurement, and it is recorded in `docs/milestones.md` rather than claimed.

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

## Evaluating and factorizing

Two families for operations that carry no certificate and are relied on by
those that do. Neither is a step obligation; both name promises the code makes
to its own callers, and both exist because mutation probes were filed against
clauses that did not cover them. `DOM-4` says a `SearchOutcome` carries the
ring it searched and was carrying three probes about arithmetic; `LIN-2` says
an exhibited inverse undoes its transformation and was carrying one about what
`factorize` can build. An audit of `0.7.0rc9` found both, and named the cost:
the full sweep still catches every mutation, but a targeted run of `DOM-4` or
`LIN-2` no longer means what its name says. That sweep could not report a miss at all,
and `docs/errata.md` says why under "The probe runner reported every probe as
caught".

**MAP-1 — Evaluation happens in the coefficient domain.** `F(point)` converts
every coordinate into `ring.domain` and evaluates there, so the answer is the
value of the map at that point and not a substitution into its expressions.
Over `GF(2)` the map `X + X^2` sends `1` to `0`, where substituting gives `2`.

**MAP-2 — A point outside the domain is substituted into instead.** Where any
coordinate does not convert, every coordinate is substituted and no coordinate
is reduced. All or nothing: a mixed evaluation would reduce part of a sum
modulo the characteristic and leave the rest, which is neither answer.

The fallback is the case a point genuinely outside the domain needs. Gao's
collision over `Q(sqrt(-23))` carries a radical `QQ` does not hold, and a field
into which `QQ` embeds has characteristic zero, so substitution is right there.
Which exceptions "does not convert" covers is measured and not assumed: SymPy
raises `CoercionFailed` over the atomic domains, a bare `ValueError` over every
polynomial and fraction domain, and `NotImplementedError` over a fraction field
for an argument that is not an expression.

**MAP-3 — Evaluation is not linear in the exponent.** A monomial of degree `d`
costs one exponentiation per variable and not `d` multiplications. A zero
exponent is skipped rather than raised to, which is also what keeps it correct:
`domain.zero ** 0` raises over every polynomial and fraction domain here.

The same holds of the scaling in `conjugate`, which is CNJ-1's function and
this clause's arithmetic.

**MAP-4 — The determinant is taken without dividing.** `determinant()` uses
addition, subtraction and multiplication in the coefficient domain and nothing
else. No step of it asks the domain for a quotient, so a domain with zero
divisors is not a special case, is not detected, and is not refused.

The Schur complement comes first and is unchanged. It divides nowhere: `D^-1`
is never formed, only `D^-1 C` through the Neumann series, and the nilpotency
that makes the series terminate is decided on the dependency graph rather than
by taking powers. What follows it is an expansion of the remaining block, and
that is the only place a division ever was.

`0.7.0rc11` and everything before it took the remaining block with
`DomainMatrix.det()`, whose fraction-free elimination divides exactly. Over
`Z/nZ` with composite `n` that division meets a zero divisor, and it does so in
two ways. Sometimes SymPy's `NotInvertible` or `ExactQuotientFailed` leaves the
library as a raw exception. Sometimes the elimination finishes and the answer is
wrong.

The second is the one that matters. Over `Z/4Z`, of 3000 random constant
three-by-three blocks 702 raised and 2298 returned, and 282 of those returned
disagree with the Leibniz expansion; with polynomial entries, 57 of 247. The
smallest witness is checkable by hand:

    A = [[0, 0, 1], [0, 1, 0], [2, 0, 0]]

Expanding along the first row gives `-2`, which is `2` in `Z/4Z`.
`DomainMatrix.det()` answers `0`.

An audit of `0.7.0rc11` found the exception. The wrong answers were found while
checking whether the old route could be kept and its exception caught, which is
what rules that out: an elimination that is silently wrong signals nothing to
catch.
This reaches the verification surface. LIN-3 compares determinants, so a step
over such a ring can be accepted or refused on a number that is not the
determinant, rather than failing where a reader would see it.

Two-by-two is unaffected, because `ad - bc` divides nothing. That is why 13296
matrices passed and why the measurement did not reach this: its exhaustive part
is two-by-two, and its three-by-three part calls `factorize` and not
`determinant`. Over `Z/4Z`, 454 of 2000 random three-by-three blocks raise and
1182 of 2000 four-by-four, and the wrong answers above sit among the rest.

What the replacement costs is a failure mode and not a result. On a block that
fits it is faster. On one that does not it fills memory where the fraction-free
elimination runs long in little of it, which is what the run SYM-7 now rests on
shows for the complement of the lift. Nothing returns either way, so no
determinant is lost; what changes is that a caller who asks for one on a block
of that size meets a limit rather than a long wait. SYM-7 is where that matters
and says so.

No domain case distinction. A division-free expansion is correct over every
commutative ring, so there is nothing for a predicate to decide, and a
predicate here would be the defect WID-1 was amended for a second time. It is
also not slower on a block that fits: on dense polynomial blocks the
division-free expansion is faster than the fraction-free elimination, and the
gap grows with the size of the block. `docs/milestones.md` carries the dated
profile, which `scripts/measure_lift_determinant.py` prints before anything
else.

This paragraph gave the gap as three factors, undated and with no machine, and
the script could not reproduce the largest of them. An audit of `0.7.0rc12`
found it against the rule in `AGENTS.md` that a runtime is a property of one
machine on one day. The repeated run gave a different factor at every size and
the same shape at all of them, which is the case for stating the shape here and
the figures there.

Only the determinant is computed, and not a characteristic polynomial it is
one coefficient of. Both are division-free and the difference is in what else
they hold. On the six-by-six complement of the `spacerat11` chain the
determinant has one term and the largest coefficient in the middle of the
characteristic polynomial has 147, which is the shape of every complement this
library takes a determinant of: the determinant of a Keller map is a unit, so
it is the one coefficient that cancels to almost nothing. Bird's algorithm
holds `n**2` ring elements and produces one polynomial, and on the complement
of the lift the route through the characteristic polynomial reaches the memory
limit well before it does.

Not from a factorization. A determinant taken by factorizing the matrix would
be defined only where `factorize` succeeds, and FAC-2 permits it to refuse a
matrix of unit determinant: `[[7, 17], [2, 5]]` over `ZZ[T]` is the witness
this page already carries. A value a certificate rests on may not rest on a
bounded search, which is what LIN-6 was amended for. The route is narrower
still than that suggests, since `determinant()` is asked of maps whose Jacobian
is not constant and of maps that are not invertible at all: of 400 random
nonlinear maps over `Z/4Z` in three variables, 96 fail on this path today, and
none of them has a matrix to factorize. The factorization is an independent
cross-check in the tests, which is where two implementations of one quantity
belong.

**FAC-1 — A pivot is a unit of the coefficient domain.** The elimination in
`factorize` divides only by units, asked of the domain with `exquo`. Over a
field every non-zero entry answers, so this is the same question there and a
stronger one over a ring.

Where no entry of a column is a unit, one is sought: the determinant lies in
the ideal the column generates, so a unit determinant forces a unit greatest
common divisor. Two attempts, in order. A Euclidean fold, complete where it
applies, which is over an integral domain with a Euclidean division. Then a
bounded search over row combinations, which applies everywhere.

Both work on a copy and commit only on success, so a failed attempt leaves the
elimination as it was. Neither trusts a domain predicate: `0.7.0rc9` gated the
fold on `domain.is_PID`, which SymPy reports for `Z/6Z`, and the fold divided
by a zero divisor.

The zero-divisor question is asked of the ground domain, since `0.7.0rc12`, and
it is the same question WID-1 asks. `(Z/4Z)[T]` has zero divisors and reports
neither `is_FiniteField` nor `is_Field` for itself, so a predicate that stops
at the outermost level answers `False` there. The fold does not run over that
domain today, because `is_PID` is `False` for it and the gate is a conjunction,
so this is a hazard the other half of the gate happens to cover and not a
defect that was found. One answer to one question all the same: two predicates
that disagree about the same ring are how the audits of `0.7.0rc9` and
`0.7.0rc11` both began.

*Amended in work package 4.2 of milestone 0.9, after the first sweep that could
report a miss.* The zero-divisor half of the gate changes no result today. Two
domains with zero divisors report `is_PID`: `Z/nZ` with composite `n`, and a
field of fractions over it. The fold runs only on a column without a unit, and
its first division by a non-unit fails there, so the guard inside the fold
returns and the search runs as it would have. With that half removed, all 288
invertible `2x2` matrices over `Z/6Z` with entries from 0 to 5 gave the same
answer as before, over `Z/6Z` and over `(Z/6Z)(T)`. The half stays, for the
reason the guard does, and the probe set holds no probe for it.

The search tries three combinations for each ordered pair of rows, and it tests
them before it applies one: subtract the other row, add it, or subtract the
quotient the domain's division reports. The first whose entry is a unit is the
one applied. Testing before applying is the amendment. `0.7.0rc10` applied the
first combination and left the loop, so the other two were computed and thrown
away, and whether a matrix factorized depended on the order of its rows: over
`ZZ[T]` the matrix `[[T, -1], [2T+1, -2]]` was refused, and the same matrix
with its rows exchanged factorized. Where no combination of a pair reaches a
unit, one of them is applied to make progress and the pairs are traversed
again, up to the bound FAC-2 states.

**FAC-2 — The search for a unit pivot is bounded, and the refusal says so.**
Over a domain that is not a field, `factorize` may refuse a matrix that does
factor. A refusal therefore reports that no unit pivot was reached and names
the two readings — the matrix is not invertible there, or it is and the search
did not find the combination — rather than asserting either.

This is the supported boundary of `factorize`, and of `LinearStep.normalize`
with it, since the normalization inverts a factorization rather than a matrix.
It is one boundary and not two: `0.7.0rc9` inverted through
`domain.get_field()`, which for `Z/nZ` returns that ring again and raised
`DMNotAField` on a shear of unit determinant.

The bound is measured and recorded in `docs/milestones.md`, by
`scripts/measure_pivot_search.py`, which `make measure` runs. It reaches a unit
pivot for every invertible `2x2` over `Z/4`, `Z/6`, `Z/8`, `Z/9`, `Z/10` and
`Z/12` — 13296 matrices — for a sample of random invertible `3x3` over `Z/6Z`,
and for both `ZZ[T]` matrices of unit determinant that audits have given. It
does not reach `[[7, 17], [2, 5]]` over `ZZ[T]`, whose determinant is one and
whose entries are integers: over `ZZ` the same matrix is folded to a unit pivot
at once. None of this is a proof for any of them.

---

## Conjugation by a diagonal

`conjugate(source, entries)` rewrites a map in the coordinates `X_i -> d_i X_i`.
It is not a step, certifies nothing, and appears in no chain. It is public, it
is used by `diagonal_matching` and by the comparisons around a published map,
and what it refuses it should refuse for a stated reason. These are those
reasons. They were part of SEA-5 until work package 10 and unnamed from then
until `0.7.0rc9`.

**CNJ-1 — The diagonal is invertible over the coefficient domain.** Every entry
lies in `ring.domain`, is non-zero there, and is a unit there. All three are
decided in the domain and not against a list of values.

Non-zero in the domain and not as an expression: over `GF(2)` the entry `2` is
zero, and comparing it to `0` as a SymPy expression said otherwise, so the
division below reached SymPy's raw `NotInvertible` instead of this refusal.

A unit in the domain and not "`1` or `-1`": those are the units of `ZZ` and of
nothing else the package supports. `2` is a unit of `QQ[T]` and `i` is a unit of
`ZZ[i]`, and both were refused with advice to call `over_field()` -- which for
`QQ[T]` widens to `QQ(T)` to obtain a reciprocal the domain already had. The
question is asked with `exquo`, which is what `Dilation` had always asked and
what this check disagreed with.

The refusal is a `ValueError` and never a raw SymPy exception. Over `sp.GF(4)`,
which is `Z/4Z` and not a field, `2` is a non-zero non-unit and the zero-divisor
error escaped. Each of the three refusals says which entry it is about.

**CNJ-2 — Conjugation preserves what a comparison is about.** Degree, order,
filtration degree and the constant Jacobian determinant of a Keller map survive,
and a collision carries over with its points and image scaled. Two conjugate
maps are the same map in different coordinates, which is what makes the question
`diagonal_matching` asks a diagnostic one rather than a claim.

The Jacobian determinant survives as a *function*: `conjugate` computes
`G(X) = D F(D^-1 X)`, so `det J(G)` is `det J(F)` composed with `D^-1`. For a
Keller map that is the same constant; for a map whose determinant is not
constant the two agree only up to the entries.

`D^-1` and not `D`, which this clause said until `0.7.0rc10`. Over the entries
`(2, 3)` the two read `1 + x y^3 / 27` and `1 + 108 x y^3`. The implementation
was right and the clause was wrong, and the test covering it used a diagonal of
signs, where the two coincide, so nothing could have found it short of reading
the clause against the code — which is what an audit of `0.7.0rc9` did.

---

## Widening the coefficient domain

`field_ring` and `over_field` move a ring and a map to the field of fractions
of the coefficient domain. They carry no certificate. The obligations of
`LinearStep` and of `factorize` are stated against the domain a map actually
has, so a widening that does not widen breaks a promise in silence and leaves
every obligation around it intact.

**WID-1 — A widening produces a field or refuses.** `field_ring` returns the
ring over the field of fractions of its domain, and raises where the domain has
none. The result is checked rather than the domain trusted: what `get_field`
returns has to report itself a field.

The question is asked of the whole domain tower and not of its outermost
level, since `0.7.0rc12`. A polynomial or fraction domain reports `is_Field`
for itself and says nothing about the ring underneath it: `(Z/4Z)[T]` widens to
`GF(4)(T)`, which reports `True` while holding `2 != 0` and `2 * 2 == 0`. The
ground domain decides, and a ground with zero divisors is refused whatever the
level above it reports.

`Z/nZ` for composite `n` is the case that forced this twice. SymPy's
`get_field` returns that ring again, and `0.7.0rc10` passed it on under a name
and a docstring that promise a field, so `field_ring` over `Z/4Z` answered with
a ring that has zero divisors. `0.7.0rc11` checked the answer and stopped at
its outermost level, so the same ring with a parameter adjoined passed. An
audit of `0.7.0rc11` found the second. The probe covered `Z/4Z` directly and
did not reach `(Z/4Z)[T]`, which is what a probe per reading is for.

A domain that already is a field is returned as it is. That is a widening that
changes nothing and not a failure, and `GF(5)` reaches it.

*Amended in work package 4.2 of milestone 0.9, after the first sweep that could
report a miss.* The two checks are not independent today. `get_field` answers
a ring that is not a field only for `Z/nZ` with composite `n`, measured over
the domains `field_of_fractions` names in its docstring, and that ring has
zero divisors. So the zero-divisor test refuses every domain the field test
refuses, and no domain SymPy offers tells the two apart. The field test stays,
because it is the statement of this clause and costs nothing. The probe set
holds no probe for it, and `scripts/mutation_probe.py` says why.

**WID-2 — `over_field` is named as advice only where it exists.** A message
that tells a caller to widen names `over_field()` only where the widening
exists and changes the domain. Where the domain already is a field the advice
changes nothing, and where the domain has no field of fractions it cannot be
followed at all.

Both readings have cost a release candidate. Over `GF(5)` a pivot was refused
with advice to widen a domain that is already a field, and an audit of
`0.7.0rc6` enumerated 392 matrices refused that way. Over `Z/4Z` a shear of
unit determinant was refused with the same advice, and an audit of `0.7.0rc9`
pointed out that the widening is not one.

The practice existed and was incomplete. `lift.py`, `collision.py` and
`compression.py` withheld the advice where the domain is a finite field, which
covers the first reading. The second was uncovered until `0.7.0rc11`: SYM-4 and
the hull refused a domain that is not a field at all and named `over_field()`
doing it, and `Z/4Z` is such a domain. This clause covers both readings and
holds for every message, not only for the ones a past audit reached.

### Which of these can fail on supplied data

WID-1, on the ring a caller brings. WID-2 is an obligation on the library's own
messages, and its negative control is therefore a message and not a
computation.

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
    location: str | None  # "step 4", "map 0", "collision 1", "witness", "file"

    def located_at(self, step: int) -> VerificationError: ...


class InvariantError(ValueError):
    obligation: str  # "BCW-10", "COL-4", "CHC-2", ...
    message: str
```

`location` is new in milestone 0.9 and was added in work package 2.2. It holds
the strings the checker uses for the same places, and `Certificate.loads` and
`Certificate.dumps` set it under FMT-10. A failure given a step and no location has the location
`step i`, so a failure inside a reduction carries both.

`InvariantError` is new in the same package. A constructor that refuses its
arguments raises it, with the identifier of the obligation the invariant
belongs to. It is a `ValueError`, so every caller who caught a `ValueError`
from a constructor still catches it, and its message begins with the
identifier in brackets, as the message of a `VerificationError` does. Every
constructor invariant of a step, a collision, a reduction and a witness raises
it. The rows of the table below that say `ValueError` for those types mean
`InvariantError`. The factor types and `PolynomialMap` raise a plain
`ValueError`, because they have no obligations of their own.

Some of these invariants had no obligation named for them on this page before
work package 2.2, and the package assigned the one each serves. Fewer than two
points of a collision cite COL-4, because a collision needs two distinct
points. Points and an image of different lengths, or of no coordinate at all,
cite COL-1. A linear step that changes the dimension cites LIN-1, and so do a
translation that changes it and a shift of the wrong length for TRA-1. A
descent at an index that is not a coordinate cites DSC-1, and a descent from a
map in one variable cites DSC-2.

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
| a source whose displacement is not homogeneous, or of degree below two | `VerificationError` |
| a basis whose vectors are dependent, or not of the source's dimension | `ValueError` |
| a collision whose points leave the compressed subspace | `VerificationError` |
| a collision of more than two points, at the symmetric lift | `VerificationError` |
| a witness `depth` below one or above the number of variables | `ValueError` |
| `reordered()` given anything but a permutation of the variables | `ValueError` |
| a structural case the search does not handle | `NotImplementedError` |
| an argument over a ring other than `over` | `VerificationError` |
| a file that breaks a rule of the certificate format, or an invariant of a constructor | `VerificationError` |
| a certificate that has no form in a file, by FMT-3, FMT-5 or FMT-7 | `VerificationError` |
| a certificate whose witness or collision is not part of it | `ValueError` |
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

**No degree bound on a descent.** Nothing requires the target of a
`DescentStep` to have a degree at most the source's, and the omission is the
point of the move rather than an oversight. The completion on the target side
may raise a degree while the deletion lowers a dimension, which is why both
published derivations pass through a dimension they then leave, and why a
search that only ever goes down cannot follow either. A step type that bounded
the degree here would rule out the one thing this type exists to express.

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
