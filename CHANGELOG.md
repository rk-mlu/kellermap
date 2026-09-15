# Changelog

Notable changes per release. The milestone plan and its reasoning live in
`docs/roadmap.md`, the binding obligations of the verification surface in
`docs/contracts.md`.

## 0.7.0rc10

An audit of `0.7.0rc9` found two release blockers and five smaller defects.
Both blockers are in the ring-general factorization `0.7.0rc9` introduced, and
the first of them is a domain predicate that was trusted instead of checked.

**The Euclidean fold ran over rings with zero divisors.** It was gated on
`domain.is_PID`, and SymPy reports that for `Z/6Z`, which is not an integral
domain at all. The fold then divided by a zero divisor and SymPy's
`NotInvertible` escaped as a raw exception: 48 invertible matrices over `Z/6Z`
were refused that way, 320 over `Z/10Z` and 768 over `Z/12Z`. All 13296
invertible `2x2` matrices over `Z/4`, `Z/6`, `Z/8`, `Z/9`, `Z/10` and `Z/12`
factor now, each reconstructing to the matrix it was given.

The gate is a measured predicate rather than a reported one: SymPy calls
`Z/nZ` a finite field for every `n` and sets `is_Field` only when `n` is
prime, so a finite-field domain that is not a field is a residue ring with a
composite modulus. Both attempts at a unit pivot also work on a copy and
commit only on success, and the fold reports failure rather than raising, so a
domain predicate that is wrong again costs a refusal and not a crash.

**A unit determinant was not enough over `ZZ[T]`.** The same gate excluded
every domain that is not a principal ideal domain, so `[[T, T+1], [T-1, T]]`,
of determinant one, was refused although `R1 <- R1 - R2` gives a unit pivot
immediately. A bounded search over row combinations now runs on every domain,
after the fold and before the refusal. It is incomplete at any bound and FAC-2
says so; the refusal reports that no unit pivot was reached and names the two
readings, rather than asserting that the determinant is not a unit, which is
what `0.7.0rc9` asserted of every refusal including of matrices in `GL_2(ZZ)`.

**`LinearStep.normalize` inverts a factorization, not a matrix.** It went
through `domain.get_field()` and `DomainMatrix.inv()`, and for `Z/4Z` the
field of fractions is that ring again, so a shear of unit determinant raised
`DMNotAField` -- with `over_field()` unable to help, since the widening is not
one. Every `LinearFactor` exhibits its own inverse, so the inverse of the
linear part is the reversed product of the inverses of its factors. Nothing
inverts a matrix, no adjugate is needed and no dimension bound with it, and
the supported boundary is exactly `factorize`'s, stated once.

**Two new obligation families.** Four mutation probes carried clauses that do
not cover them: three about `PolynomialMap` arithmetic under `DOM-4`, which
says a `SearchOutcome` carries the ring it searched, and one about what
`factorize` can build under `LIN-2`, which says an exhibited inverse undoes
its transformation. A full sweep still caught every mutation, but a targeted
run of either selector meant less than its name. `MAP-1` to `MAP-3` cover
evaluation in the coefficient domain, the substitution fallback outside it,
and that neither is linear in the exponent; `FAC-1` and `FAC-2` cover the unit
pivot and the bounded search. All 61 probe identifiers were then read against
the clauses they name; the other 55 hold.

**CNJ-2 had the coordinate change backwards.** `conjugate` computes
`G(X) = D F(D^-1 X)`, so the determinant composes with `D^-1`; the clause and
the docstring said `D`. Over the entries `(2, 3)` the two read
`1 + x y^3 / 27` and `1 + 108 x y^3`. The implementation was right throughout.
The test covering it used a diagonal of signs, where `D` and `D^-1` coincide,
so it could not have found the error.

**A second test asserted a value where the claim was a complexity.** The
scaling loop in `conjugate` was covered by its result, which the loop it
replaced produces just as well, and the docstring said a mutation probe
covered the loop where none existed. The loop is now a module-level
`_scaled_terms` exercised with a value that counts how it is combined, and it
has a probe.

**Documentation.** `docs/contracts.md`, `docs/architecture.md` and
`docs/api.md` all still required `over_field()` for every map over `ZZ`, which
`0.7.0rc9` had made false and tested false. `diagonal_matching` and two tests
still spoke of SEA-5 in the present tense. The `CNJ` section was missing from
the contract page's table of contents. And CNJ-1 promised that every refusal
names the entry, where only the non-unit path did; the conversion and zero
paths named the whole tuple.

## 0.7.0rc9

An audit of `0.7.0rc8` found two release blockers and four smaller defects, all
of them in public behaviour at an edge nothing had tested.

**`LinearAutomorphism.factorize` refused matrices it should factor.** Over a
domain that is not a field a pivot has to be a *unit* and not merely non-zero.
The elimination took the first non-zero entry and divided by it, which is right
over a field and wrong over a ring: `[[2, 1], [1, 1]]` lies in `GL_2(ZZ)` with
determinant one and a swap with the second row gives a unit pivot straight
away, while `[[2, 1], [3, 2]]` needs a real Euclidean combination. Both were
refused with advice to call `over_field()`, and of the 104 unimodular matrices
with entries from `-2` to `2`, 16 were refused. All 104 factor now, each
reconstructing to the matrix it was given.

Where no entry of a column is a unit, one is made: the determinant lies in the
ideal the column generates, so a unit determinant forces the column's greatest
common divisor to be a unit, and the rows are folded pairwise by the Euclidean
algorithm run with row operations — a division is a `Transvection` and the
exchange after it a `Transposition`, so the record stays a product of Gauss
generators. The folding runs exactly where the domain says it has a Euclidean
structure, on a principal ideal domain. Over `ZZ[T]` nothing is attempted and
the refusal stands, now for a reason that is true of the domain rather than an
accident of which entry came first.

`LinearStep.normalize` documented a field and checked nothing, so which `ZZ`
maps normalized depended on the same accident. The condition was never that the
domain is a field: it is that the linear part's determinant is a unit, which is
`factorize`'s question and is asked of the matrix. A unimodular linear part over
`ZZ` now normalizes without widening; a determinant of `2` still needs
`over_field`, and says so.

**`conjugate` let a raw SymPy exception escape.** `sp.GF(4)` is `Z/4Z` and not a
field, so `2` is a non-zero non-unit, and the unit check caught
`ExactQuotientFailed` but not `NotInvertible`. Every non-zero zero divisor
modulo 4, 6, 8, 9, 10 and 12 is now refused as a `ValueError` naming the entry,
and every unit of those rings is still accepted.

**CNJ is a new obligation family**, for `conjugate`. The diagonal was part of
SEA-5 until work package 10 and unnamed from then on, while the docstring went
on attributing it there. That cost something rather than merely reading oddly: a
mutation probe for the unit rule had been filed under `SEA-5`, so one selector
stood for two unrelated promises and a green run said less than it looked like.
CNJ-1 is the admissible diagonal — every entry lies in the domain, is non-zero
there and is a unit there, each decided in the domain — and CNJ-2 is what
conjugation preserves. SEA-5 is untouched.

**A test claimed a complexity and tested a value.** `0.7.0rc8` replaced a
multiplication per unit of exponent with exponentiation and covered it by
evaluating `x**64` and checking the answer, which the linear version also
returns; the audit put the old body back and the test stayed green. It now
evaluates against a value that counts how it is combined, and asserts one
exponentiation and at most four multiplications. Re-running the audit's own
experiment fails it.

The same shape was still in `conjugate`, which divided once per unit of
exponent, because only the evaluator had been looked at when that was fixed.

**Gate documentation.** The rule that runtimes are not written into prose was
itself ambiguous — its framing forbade every runtime and its prohibition named
only seconds — and `AGENTS.md` broke it under the wider reading. The rule now
says exactly what it permits: an order of magnitude carrying an argument about
who runs something, and a figure that is the subject of its own sentence, which
says when it was taken. Everything mentioned in passing goes. A sweep found
seven places beyond the three the audit named; four were corrected and three
were already magnitudes.

Three mutation probes, which makes fifty-seven: the unit rule's refusal, the
unit pivot, and the evaluator's exponentiation. Two of the three sit on claims
that a test was asserting without checking.

## 0.7.0rc8

An audit of `0.7.0rc7` found one release blocker and five smaller defects. Four
of the six are in `0.7.0rc7`'s own repairs rather than in anything older, which
is the pattern this release takes its lesson from: a repair is a change and
earns the same scrutiny as the thing it repaired.

**The blocker.** `PolynomialMap.__call__` falls back to substitution when a
point does not lie in the coefficient domain, and the fallback caught only
`CoercionFailed`. That is what the atomic domains raise. Measured across the
domains this package supports, `from_sympy` raises three different things:
`CoercionFailed` over `ZZ`, `QQ`, `GF(p)`, `QQ_I` and an algebraic field, a
bare `ValueError` over every polynomial and fraction domain, and
`NotImplementedError` over a fraction field for an argument that is not an
expression. So over `QQ[T]`, `QQ(T)`, `ZZ[T]`, `GF(p)[T]` and `GF(p)(T)` the
fallback crashed instead of falling back: `F(s)` for a free symbol returned
`s**2` in `0.7.0rc6` and raised in `0.7.0rc7`, and so did a legitimate
characteristic-zero collision at `±sqrt(2)`. `Collision.at`, `Collision.verify`
and every transport path with a point outside the domain went with it.

The test that covered the fallback used `QQ`, which raises the one exception
that was caught, so a suite at 100 per cent statement coverage reached the
branch and never exercised what reaches it. The regression is parametrized over
five composite domains and has a control that a point *inside* the domain still
evaluates there.

**COL-7's justification was wrong, and the obligation is unchanged.** It read
that the Jacobian conjecture is open in characteristic zero. The first page of
`README.md` says it fell in July 2026 and that the counterexamples are this
library's subject. The claim stood in `collision.py`, in `docs/contracts.md`,
in this changelog and in the `VerificationError` a caller sees.

The boundary itself is sound and rests on this type's own semantics: COL-5
keeps the map out of a `Collision`, so COL-4 decides distinctness in the normal
form of `kellermap.canonical`, which carries no characteristic, and deciding
COL-3 in the coefficient domain while COL-4 stays outside it would let `0` and
`2` over `GF(2)` pass as two distinct points with one image. It is the boundary
`lift.py` draws at SYM-4 and `compression.py` at CHC-8. The justification now
says that and does not mention the conjecture's status at all. COL-7 also
reached `docs/api.md`, which `AGENTS.md` requires for new public behaviour and
which `0.7.0rc7` skipped.

**`conjugate` refused units.** Over a domain that is not a field it admitted
`1` and `-1`, which are the units of `ZZ` and of nothing else here. `2` is a
unit of `QQ[T]` and `i` of `ZZ[i]`, and both were refused with advice to call
`over_field` — which for `QQ[T]` widens to `QQ(T)` to obtain a reciprocal the
domain already had. `Dilation` had this right and the check disagreed with it.
The question is now asked of the domain with `exquo`.

**`LinearAutomorphism.matrix` came back congruent rather than normalized.** The
product of the factor matrices was formed in ordinary SymPy arithmetic, so over
`GF(2)` the factorization of `[[1, 1], [1, 0]]` returned `[[1, 1], [1, 2]]`. No
certificate was wrong, because LIN-6 converts into the ring before it compares,
but a public method answered with a matrix that is not the one it was given.
Of the 2550 invertible `2x2` matrices over `GF(2)`, `GF(3)`, `GF(5)` and
`GF(7)`, 1297 came back differing syntactically from their own normalized
input; none do now. The product is formed as a `DomainMatrix`.

**Evaluation is no longer linear in the exponent.** `_evaluate_at` multiplied
once per unit of exponent, where the public API sets no bound on the degree. It
exponentiates, and skips a zero exponent rather than raising to it — which is
also what keeps it correct, since `domain.zero ** 0` raises `ValueError` over
every polynomial and fraction domain here.

**Gate documentation.** The `Makefile` described one slow test where the marker
carries seventeen, `.github/workflows/ci.yml` described three reconstructions
where `make reconstruct` runs eight, and a docstring in
`tests/test_positive_characteristic.py` said the `GF(7)` enumeration belongs to
the slow suite, where nothing had put it there.

Two mutation probes, which makes fifty-four: the fallback the evaluation takes
for a point outside the domain, and the unit test in `conjugate`. Both sit on
repairs that had themselves gone wrong, which is the argument for probing a
repair and not only the thing it repaired.

## 0.7.0rc7

An audit of `0.7.0rc6` found four release blockers with one cause between them:
several paths decided equality, nullity and inversion in ordinary SymPy
expressions rather than in the ring the map lives over. Every one is closed
here, and each was reproduced against `0.7.0rc6` before anything was changed.

The targeted search compares a pool value against a slot factor in the ring of
the map the walk has reached, as `PolyElement` and with the sign, where it
compared expanded expressions. A spelling says nothing: over `GF(2)` the pool
value `3z^2` and the factor `z^2` are one element, and over `QQ(T)` so are
`(T+1)z^2` and `((T^2-1)/(T-1))z^2`. An exact match written differently was
charged a rewrite, and with the default of one rewrite left the chain was
dropped and the space reported as exhausted -- a claim SEA-13 makes and it was
false. The `GF(2)` case went from eleven maps and `exhausted=True` to a chain
found in ninety-two.

BCW-12 compares two `PolyElement` of the source's ring and runs after the slots
are converted into it. It ran before, on the expressions as they arrived, and
decided with `kellermap.canonical`, which has no characteristic: over `GF(2)`
it read `y` and `-y` as two values and refused a step whose two slots are one
element.

`Candidate.shared` is the whole of the intent. `shares_one_generator` kept a
structural equality test beside it, so the switch `0.7.0rc6` introduced could
not express what it promised -- `x^2 - y^2` beside `(x-y)(x+y)` gave
`shared=True` with `m == 2`. A `Candidate` carries expressions and no ring, so
whether the two values agree is decided where a ring exists to decide it.
`untargeted_candidates` sets the flag only where both slots are fresh and equal
in the source's ring, where it set it on every candidate it emitted.

The linear step does its arithmetic in the coefficient domain. The Gauss-Jordan
elimination formed `1/entry` as a rational and decided nullity with
`sp.simplify`, the determinant bookkeeping multiplied in characteristic zero,
and the normalization inverted the linear part with `sp.Matrix.inv()`. Over
`GF(5)` the pivot `2` produced `1/2` and the matrix was refused as needing
`over_field()`, which cannot help there. Of the invertible `2x2` matrices,
`LinearStep.normalize` failed on 5 of 6 over `GF(2)`, 8 of 48 over `GF(3)`, 392
of 480 over `GF(5)` and 1864 of 2016 over `GF(7)`; it now succeeds on all of
them. The inverse is formed over the domain's field of fractions and handed to
`factorize`, which still decides domain membership and still names
`over_field` for a caller over `ZZ`.

`PolynomialMap.__call__` evaluates in the coefficient domain wherever the
arguments lie in it, and substitutes otherwise. It was a bare `xreplace`, so
over `GF(2)` it answered `F(1) = 2` for `F = X + X^2` and COL-3 discarded a
true collision on the strength of it. The fallback is what a point outside the
domain needs: Gao's collision over `Q(sqrt(-23))` carries a radical `QQ` does
not hold, and a field into which `QQ` embeds has characteristic zero.

**COL-7 is new: a collision is stated over characteristic zero only.** Making
COL-3 domain-aware alone would have opened a worse hole than it closed, since
with distinctness still decided as expressions `0` and `2` over `GF(2)` would
have passed as a collision of distinct points. The reason to decline rather
than to extend the equality is this type's own semantics: COL-5 keeps the map
out of a `Collision`, so COL-4 decides distinctness with `kellermap.canonical`,
which has no characteristic. It is the boundary `lift.py` draws at SYM-4 and
`compression.py` at CHC-8. Nothing is lost with it that the library is for:
non-injective Keller maps in characteristic `p` are cheap and long known, the
`GF(2)` map the audit used being the Artin-Schreier map `X + X^p`. Checked in
`verify()` and not in the constructor, because COL-5 keeps the map out of the
object; what is refused is stating the points against that map. Two
consequences: a chain over positive characteristic carries no collision at any
step type, and `collision_hull` answers COL-7 where it answered the `d!` half
of CHC-8, which is still reached through the `CompressionStep` constructor.

`conjugate` decides in the domain whether a diagonal entry is zero.
`conjugate(F, (1, 2))` over `GF(2)` reached SymPy's raw `NotInvertible` instead
of the refusal the function owes its caller. A `# pragma: no cover` beside the
coercion branch there claimed the field check answers first; over `QQ` it does
not, and the branch has a test rather than the pragma.

Seven mutation probes, which makes fifty-two: COL-7, BCW-12, LIN-6, SEA-13,
SEA-14, UNT-1 and the evaluation under DOM-4. `search.py`, `untargeted.py` and
`polynomial_map.py` had no selector at all, which is why the audit could not
run the selection this project's rules ask for after a change of that kind.

**Timings are no longer written into prose.** `AGENTS.md` had summed a column of
gate timings and kept the sum after one entry of the column had grown, so the
stated total was off by most of a run, and `CONTRIBUTING.md` had copied the
number. A runtime is the one figure here that the reader who finds it cannot
check: it is a property of one machine on one day, where every other figure is
a property of the mathematics or the code. Both pages now state the division of
labour by which gate dominates and who runs it. `docs/roadmap.md` keeps the one
exact profile, under "What the fast suite costs", where the numbers are the
subject rather than an aside, and says on its face that they are a record of
one run on one machine. `AGENTS.md` carries the rule under "Timings are not
figures".

Documentation defects from the same audit. `CONTRIBUTING.md` said six
reconstructions where the `Makefile` runs eight, left out two reconstruction
scripts and `measure_pipeline.py`, and listed `make release` without
`sdist-test` and `dist-complete`. `linear.py` and the diagram in
`docs/architecture.md` named seven step types and the diagram omitted
`DescentStep`; there are eight. `docs/contracts.md` claimed the concrete
`GF(2)` example shows that neither carrier set contains the other, where they
are `(0,1,2)` and `()`. `docs/api.md` gained
`carrier_indices_for_factors` and `Candidate.shared`.
`docs/references.md` said the library has no form for the fourth move of the
eleven-variable derivation, which `DescentStep` has been since 0.7; what
remains true is that DSC-7 gives it no `build` and neither search constructs
one, so the move can be certified and not found.

`tests/test_positive_characteristic.py` holds the four blockers as regressions
over `GF(2)`, `GF(5)` and `QQ(T)`, and gained the adversarial map
`(x + y^2, y + x^2)` over `GF(2)`, which worked in `0.7.0rc6` with nothing
holding it there.

## 0.7.0rc6

`Candidate` has a `shared` field, and two fresh slots carrying one value are
two coordinates unless a candidate asks for one. Sharing was inferred from the
two polynomials being equal, so the two could not be told apart, and an audit
of `0.7.0rc5` found both directions. The targeted search could not express a
verified step with two distinct coordinates of one value -- it reported its
space exhausted after thirty maps -- and it did build a shared one, which
SEA-14 excludes, naming two coordinates and consuming one. Neither was a false
certificate; both were the search disagreeing with its own statement of where
it looks. `untargeted_candidates` asks for the sharing where UNT-1 wants
BCW-12's saving.

`Candidate.factors` refuses a surplus of names as well as a shortage, which is
the invariant that failed silently. One caller relied on that silence --
`scripts/untargeted_space.py` handed two names over whatever the candidate
needed -- and `make measure` failed the moment the guard went in, which is the
evidence the silence was worth ending.

The four-variable case with a carrier on a dependency cycle has a test for the
targeted search too. The untargeted walk and `peel` got theirs when they were
corrected; this one reached the changelog of `0.7.0rc4` without one, and an
audit noted the gap rather than finding a fault. It holds `anchors`,
`enumerate_candidates` and `search` against the step that verifies and drops
the degree to three without buying a coordinate.

The fast suite was profiled and one test marked slow. It had grown to 139
seconds, of which the unweighted control of SEA-14 was 44: it examines 3189
maps since `0.7.0rc5` widened the forward space, and it is now a test of its
own rather than one case of a parametrization, so the two weighted cases keep
their small budget and stay fast. The suite is 84 seconds and the coverage run
over it 208. `docs/roadmap.md` carries the rest of the profile and why nothing
else moves.

A Keller map over `GF(2)` broke four public operations at once, and all four
had one cause. `PolyElement.diff` leaves a term with a zero coefficient in the
sparse dictionary in positive characteristic, and such a polynomial compares
unequal to the same polynomial without it, so the Jacobian entries this library
stores were not in the ring's normal form. `carrier_indices` was empty on a map
whose Jacobian is the identity, and `determinant`, `search` and
`BCWStep.verify` let a raw `ExactQuotientFailed` out. The entries are
normalized where they are computed.

`carrier_indices_for_factors` asks BCW-10's condition on the monomial support
of `F_j - X_j` and not on `dF_j/dX_j`. The two are the same question in
characteristic zero only, and the property claimed they were the same: over
`GF(2)` the map `(x + x^2, y + y^2, z + z^2)` has the identity for its Jacobian
and no displacement free of its own variable, so the block is the whole map and
no coordinate is a carried factor. Neither set contains the other there, where
one contained the other before. The old test came out right by accident,
because the unnormalized derivative compared unequal to one, so correcting the
storage would have made the wrong condition bite.

`tests/test_positive_characteristic.py` holds the audit's map against the
Jacobian, both carrier notions, the determinant, a search from the map to
itself and a step that builds and verifies, with a control that characteristic
zero is unchanged.

## 0.7.0rc5

The targeted enumerator asks BCW-10's condition for a carried factor, like the
untargeted one since `0.7.0rc4`, and offers a co-factor a coordinate holds both
as that carrier and bought. The second half is what makes the first safe. Until
now the carried form displaced the bought one in the deduplication, and the
bought form is what a pool name fills, so widening the carrier condition alone
removed a chain the search used to find rather than adding any.

On the four-variable map an audit of `0.7.0rc3` reported against, `anchors`
offered two of four coordinates and `search` called its space exhausted after
one map although the target was one verified step away. It offers all four now
and finds the step after two.

The cost is branching and it is measured: the unweighted control of SEA-14
examines 3189 maps where 200 sufficed, about sixteen times as many, and finds
the same chain. Its budget in the tests moves for that case and not for the
weighted ones, where the chain is absent and a larger budget buys only the time
to exhaust the space.

## 0.7.0rc4

`PolynomialMap.carrier_indices_for_factors` is what a carried factor is asked
for now: BCW-10's own condition, `dF_j/dX_j == 1`, and not the unipotent block
of `carrier_indices`, which drops every coordinate on a dependency cycle and
says of itself that it is not maximal. The untargeted enumerator and the
pruning rule of `peel` ask it.

The pruning rule is why this is a release blocker rather than a lost dimension.
It prunes a branch standing one coordinate above the source when the source has
no carrier, and `carrier_indices` is empty on a linear map whose coordinates
depend on each other in a cycle although every one of them satisfies BCW-10. A
peel on such a source reported an exhausted space with a verified two-step
chain inside its bounds. An exhausted space is a claim.

The figures do not move, and the exhaustiveness claims of work packages 6 and 7
were made again rather than assumed to hold: a negative claim over a space that
has since grown is the error the pruning rule was making. `reduce_to_degree3`
reaches the same thirteen from Alpoege's map in the same seven steps and the
same map, the multi-affine walk reaches the same 19, 23 and 24, the candidate
counts at all six maps of the published chain are unchanged, and the exhaustive
searches under the bound of eleven give the same 2, 33, 299 and 2720 states.

The reason they do not move is worth recording. The two sets differ only on a
dependency cycle, and a chain of `BCWStep`s does not make one: a bought
coordinate is `X_u + P` with `P` over the coordinates already there, so the
carriers a reduction produces never depend on each other. The widening bites on
a map somebody hands in, not on one this library builds.

Four statements that an audit found disagreeing with their own page or with
their source. `docs/references.md` credited Prellberg with the symmetric lift,
where his version 2 credits de Bondt and van den Essen and claims the
collision-generated subspace instead, and where the same page says so a hundred
lines down. Its density paragraph set his forty-variable quartic against this
project's thirty-eight, which is not a comparison, and left out his
thirty-eight with 340 monomials. `docs/contracts.md` named Corollary 7's
route-specific minimality and not Proposition 8's. And `docs/api.md` and one
test docstring still gave the justification for a base of at least three that
`0.7.0rc3` removed from the code and the contract page.

The entry for version 2 of arXiv:2608.12543 moves to `0.7.0rc3`, where the work
was done; it was written while `0.7.0rc2` was the open heading. One test
docstring called itself marked slow and carries no marker: the sentence goes
rather than the marker being added, because deselecting it would leave the
figures on three pages with nothing checking them.

The targeted search still asks the narrower question, and that is measured
rather than left. Swapping the condition in there does not widen the space:
a carrier takes a slot a pool name would otherwise fill, and the first
candidate to reach the deduplication wins, so a chain the search used to find
drops out -- the unweighted control of SEA-14 then exhausts at 2667 states with
nothing. Offering both forms is the correction, and it is the same one the
multi-affine walk needed; it is its own package.

## 0.7.0rc3

Version 2 of arXiv:2608.12543, of 31 August 2026, is recorded. It renames the
paper, keeps Theorem 3 with its number and its statement, and adds a second
application at nineteen variables whose collision hull is the whole space, so
its thirty-eight-variable lift cannot be lowered by any invariant linear
restriction retaining that collision. Van Rijn's nineteen and thirty-eight were
already on `docs/references.md` and are not what the new version adds. Its
ancillary file was read and has the digest that version states, and nothing
from it is vendored: what this repository needs from it is already held in its
own idiom, and the maps it carries are third party twice over.

`docs/references.md` also withdraws a claim two of its own sections disagreed
about. One said the nineteen this pipeline reaches is one below anything
published; another said on the same page that nineteen and thirty-eight are van
Rijn's figures too, a month earlier. The second was right and the first was
wrong when it was written. `docs/errata.md` records it.

The citations that name a theorem move to version 2; those that record where
fixed data was transcribed from stay at version 1, because a transcription is
from the bytes it was made from.

UNT-12 says one candidate per factorization *and* slot assignment. It said per
factorization, which was the count before the walk stopped choosing an
assignment greedily; on `(x + y^2, y, z + y)` one factorization yields two. The
obligation is widened rather than the walk deduplicated, because the
alternatives are what let the pair that buys least win.

The justification for a base of at least three loses its second half. Being
zero exactly on a multi-affine map fails at base zero alone and holds at one
and at two, so it is a reason for refusing zero and not for asking three. The
falling measure is the whole reason and was always the first half.

The README no longer names the candidate its DOI sentence was written for. It
said the number is the DOI of `0.7.0rc1` and went stale at the next candidate;
it says the number is not the DOI of the version above, which stays true.

The multi-affine walk asks BCW-10's own condition for what holds a factor, not
`carrier_indices`. That set is deliberately not maximal -- it drops every
coordinate on a dependency cycle, which is what makes the block it picks out
unipotent -- and that is the right question for the block and the wrong one for
a factor. On `(x + y, y + x + z, z + 2x + y, w + y^2)` the walk reached six
where five is enough. The three maps of this milestone are unchanged at 19, 23
and 24, so no figure on any page moves.

DSC-4 is checked at every public route into a `DescentStep`. `0.7.0rc2`
checked it in `verify` and in `target`, and an audit found `conjugate` and
`tail` still letting a bare `ValueError` out of
`ElementaryAutomorphism.apply_to`. The test that was meant to cover those two
called `target`, which is why it went unnoticed; it is three tests now, one per
method, and each calls the method it names.

## 0.7.0rc2

The corrections an external audit of `0.7.0rc1` asked for.

`DescentStep` rebuilt its target with the expression constructor, which
re-infers a ring: a source over `QQ` gave a target over `ZZ`, and over a finite
field that changes the characteristic. It is carried over with `clone_ring` and
`reindex` now. The step's `ring` property went through SymPy's cache and handed
the same mutable object back on every access, which is what `clone_ring` exists
to prevent. DSC-4 asked for automorphisms over the source's ring and nothing
checked; a mismatch surfaced as a bare `ValueError` from inside
`ElementaryAutomorphism`.

`squared_terms` rebuilt its exempt set inside a comprehension, so a one-shot
iterable was empty from the second generator onward and every variable counted.
`remaining_excess` validated nothing: a base of zero reported zero on a map
that squares a variable. `reduce_to_multi_affine` now carries the note about
the interpreter's recursion limit that its sibling has.

Documentation the audit found stale. `docs/references.md` still said the
library does not implement the multi-affine half of Theorem 2.1(b), which
stopped being true in this milestone, and a second paragraph still said it
carries out neither of the two stages that lead to the cubic homogeneous form,
which stopped being true in 0.6: the 27 and the 22 for `alpoege13` are
certified now and `scripts/measure_pipeline.py` recomputes both. The abstract of
`CITATION.cff` described milestone 0.6 and the description in `pyproject.toml`
still said the project was working towards the reduction.

`scripts/mutation_probe.py` gains three probes, for both halves of DSC-3 and
for the half of DSC-4 that is about arithmetic. Those are the clauses the
contract page names as able to fail on data a caller supplies; HOM-11 and
HOM-12 cannot fail after HOM-1 and UNT-12 is an enumerator, so neither takes
one.

The carrier map kept one coordinate per value where two can hold it, so the
walk bought a coordinate it already had. `(x + y^3, y)` reaches the multi-affine
form at dimension six again, which is the chain `docs/roadmap.md` writes out,
and the three maps of the milestone reach 19, 23 and 24 against 20, 24 and 26.
Their chains to the normal form of Theorem 2.1(b) were rerun and reach 39, 47
and 49.

## 0.7.0rc1

What the Reduction Theorem still owed, the obligation of the symmetric lift
that was argued rather than checked, and the first questions about the search
that were worth asking.

### Theorem 2.1(b)

`reduce_to_multi_affine` reaches the half of the theorem the homogenization
cannot supply: a cubic map in which no variable occurs squared. HOM-11 and
HOM-12 say at the end of the chain that the property arrived, over every
variable except the homogenizing parameter and not only over the ones the
source began with. `squared_terms` in `kellermap.bcw.grading` is what all three
read.

The walk is a second enumerator and not the degree reduction with another
stopping rule, UNT-12. It measures itself by `remaining_excess`, and the count
of squared monomials would not serve: the first step on `y^3` replaces one by
two while the measure falls from nine to six.

Measured, every step verified: `alpoege13` reaches the normal form at 39
variables, `alpoege12` at 47, `spacerat11` at 49. The order inverts, and the
cost of verifying a chain follows neither the dimension nor the density -- of
six chains on one machine the cheapest determinant is the largest map and the
dearest is the smallest.

The refinement is a branch and not a stage. `docs/architecture.md` says why
under "Where the pipeline forks": the symmetric lift does not carry the
property, nothing between the gradient form and the Vanishing Conjecture asks
for it, and carrying it there would cost about 130 variables against 38.

### The descent

`DescentStep` deletes a coordinate that two elementary changes have made
triangular, DSC-1 to DSC-7. It is the fourth move of the two published
derivations at degree three and the one this library had no step type for. It
verifies a claim a caller supplies; there is no `build`, so every instance is
`SUPPLIED`, and searching for the two changes is a separate question.

### SYM-7

The determinant of the gradient form was stopped after nineteen hours rather
than eight, and the obligation now rests on what the run showed: the cost
follows the carrier and not the dimension. Every stage before the lift leaves a
four-by-four block; the lift leaves twenty-nine.

### What the search does and does not reach

`reduce_to_degree3` reaches dimension 13 from Alpoege's map in seven steps and
never spends its budget, so what bounds it is the greedy rule and the offer.
Started on the published eleven-variable chain's own maps it leaves for 13 or
14 every time, including one step from the end.

Searched exhaustively under a hard bound of eleven, the offer runs out with
nothing of degree three to find from five of the six maps of that chain, and
the external beam driver reached the same answer from the sixth. Both searches
enumerate one offer, so the two negatives are one negative.

Widening that offer was measured and does not pay. The three ways to widen it
cost a branching factor of nine at Alpoege's map; the cheapest of them
multiplies the searched space by a factor that compounds to twenty or fifty per
coordinate and reaches nothing new from any map where the answer is known. No
single one of them makes the published chain reachable.

### Documentation

`docs/errata.md` gains four entries. Theorem 2.1(b) had been stated for the
original variables only; a work package planned a step a previous milestone had
already built; a widening was assigned to a milestone that does not contain it;
and a bought coordinate was said not to be able to carry a sum. All four were
found by reading a page against the source it rests on rather than by a gate.

## 0.6.0

The second and third stages of the Reduction Theorem, and the two constructions
that carry the result to the form the literature compares. Everything before
this milestone stopped at degree three, which is BCW's first stage, while the
published figures are cubic homogeneous, which is the third.

Two stages and not the whole theorem. Theorem 2.1(b) asks for a normal form
that is also linear in each original variable and quadratic only in `T`; this
milestone does not produce that refinement, and `(x + y^3, y)` homogenizes to a
verified five-dimensional target that still carries a `y^3`. The reduction the
usual corollary needs -- cubic homogeneous with nilpotent Jacobian -- is
unaffected, and `docs/references.md` says which is which.

The pipeline, from the smallest degree-three map this project holds, with every
step verified and the collision carried to the far end:
`examples.spacerat11` at 11 variables, 22 after the unipotent reduction, 23
cubic homogeneous, 19 after collision-hull compression, and 38 for the gradient
form of a quartic over `Q(i)`. `scripts/measure_pipeline.py` recomputes that
and the same for the two larger maps.

What that is worth and what it is not is in `docs/references.md`. Nineteen and
thirty-eight are the smallest figures published at either stage and they were
published elsewhere first, on 30 July 2026, by a different route. No priority
is claimed and no minimality. The forms this project produces are denser than
the published ones: 386 monomials against 350 at the quartic stage.

Three pages were split out of `docs/references.md`, which had grown to four
subjects at once. `docs/provenance.md` holds what an audit reads and
`docs/errata.md` what this project reported wrongly and corrected — eighteen
entries, five of them findings of the audits of this milestone's release
candidates.

### Added

- `kellermap.bcw.UnipotentStep` — Section 4's second step, which doubles the
  dimension and makes the Jacobian of the displacement nilpotent. Obligations
  UNI-1 to UNI-12.
- `kellermap.bcw.HomogenizationStep` — the third step, which adds one variable
  and makes the displacement cubic homogeneous. The first step type that is not
  a composition, and whose transport runs forward only. Obligations HOM-1 to
  HOM-10.
- `kellermap.CompressionStep` and `collision_hull` — Theorem 3 of
  arXiv:2608.12543v1. The one step that lowers the dimension, restricting to
  the subspace a collision generates. Obligations CHC-1 to CHC-10.
- `kellermap.SymmetricLiftStep` — part 3 of the same theorem: the gradient of a
  quartic over `k(i)`, which is the object Zhao's Vanishing Conjecture is
  about. The first step that changes the coefficient domain. Obligations SYM-1
  to SYM-12.
- `examples.thompson24_homogeneous` and `examples.spacerat11`, with their
  collisions — two published maps this project did not write, transcribed from
  the licensed presentations. `docs/provenance.md` records the terms.
- `scripts/reconstruct_spacerat11.py` and `scripts/measure_pipeline.py`, joined
  to `make reconstruct` and `make measure`.
- `docs/provenance.md` and `docs/errata.md`.
- `CITATION.cff`, shipped in the source archive, and `docs/deposit.md`, which
  holds the description text and the procedure of the Zenodo deposit rather
  than leaving the wording of a permanent record to a browser session. The
  version stands in four places now and `tests/test_documentation.py` holds
  the four together.
- The DOI of this version, `10.5281/zenodo.22299353`, in `CITATION.cff` and in
  `README.md`. Zenodo reserves a DOI on a draft, so it was written in before
  the archive was built and the archive carries the DOI of the record it goes
  into. `docs/deposit.md` had the two steps the other way round and now says
  to reserve first; a test holds the two places together, with a control for a
  Markdown link whose label and target disagree.
- The concept DOI, `10.5281/zenodo.22299351`, in `README.md`. It resolves to
  the newest version and is the one to cite for the software rather than for a
  state. Zenodo assigns it at publication and not before, so this entry and
  the two files it names were written after the tag `v0.6.0`, which does not
  carry them. `CITATION.cff` states a version and keeps the version DOI.

### Changed

- `examples.thompson24` is `examples.thompson24_homogeneous`. A map that is not
  at degree three carries its stage in its name, since `alpoege19` is nineteen
  variables at degree three and the compression reaches a cubic homogeneous map
  in nineteen by another route.
- `kellermap.bcw.grading` holds what the second and third steps share, which is
  reading a displacement by degree and asking whether a Jacobian is nilpotent
  through one determinant.
- `docs/references.md` states the position and no longer tells the story of how
  it was corrected; `docs/errata.md` does that.
- `docs/provenance.md` gains "How this repository was written", which is the
  one place stating which generative models were used, in which roles, what
  the arrangement found, and who answers for the result. `CITATION.cff` and
  the Zenodo description point at it rather than repeating it.
- `AGENTS.md` gains the rule that a new way of distributing the repository is
  checked against the licence rule before it is used. It has now failed twice
  at a channel nobody checked, and `docs/deposit.md` records the check for the
  third.
- The `Documentation` list in `README.md` still described `references.md` as
  the page holding the provenance of the fixed data, which stopped being true
  when this milestone split it. It names all seven pages now.

### Fixed

- `scripts/reconstruct_macfarlane13.py` carried a transcription of Macfarlane's
  map, and the source archive ships `scripts/`. His repository carries no
  licence, so the archive was distributing mathematics whose terms could not be
  established. The script reads it from `tests/data.py` now, which is the
  pattern `reconstruct_alpoege19.py` has had since 0.5.
- A sentence in `docs/references.md` wrapped so that a number began a line, and
  Markdown read it as an ordered list. A test now covers the class.
- The source archive shipped a suite that failed: one test imported
  `tests/data.py`, which the archive excludes on purpose. It skips now, and
  `make sdist-test` unpacks the archive, installs it and runs the suite the
  archive ships. `build-test` never saw this, because it runs the tests of the
  working tree. The fault had stood since 0.5.

### Found in review

None of these reached a release. Every one was introduced inside this
milestone and found before it closed, by six external audits of the release
candidates and by the maintainer. They are listed because a defect that was
caught is evidence about the review and not an embarrassment, and because the
first of them is five defects that are one defect.

- **The orientation of the two lifted points went through five orderings.** A
  collision is a set, so `SymmetricLiftStep.transport` has to decide which of
  the two points is which. The first version took the order the tuple happened
  to carry, and two equal collisions transported to two unequal results that
  both verified. `str`, `srepr` and `Basic.compare` each replaced the one
  before and each failed on a pair the next audit produced: two symbols of one
  name with different assumptions, one symbol written two ways, two `Function`
  classes of one name. What they had in common is not the choice of key. Each
  was used instead of an equality test rather than after one, which asks a
  single key to agree on everything equal and separate everything unequal. The
  released version asks `==` first, then `Basic.compare`, then metadata of the
  class, and refuses under SYM-8 where all of that ties. `docs/errata.md`
  carries the five in full, and the fifth is the only one that did not replace
  the version before it.
- `collision_hull` and `CompressionStep` did field arithmetic over any
  coefficient domain, and the symmetric lift had no domain boundary at all.
  All three require a field of characteristic zero now, which is what Theorem 3
  assumes. A value the domain cannot represent raises the `ValueError` CHC-2
  promises rather than the domain's own error, and a source over `GF(5)` no
  longer reaches SymPy's `UnificationFailed`.
- `CompressionStep` stored basis entries as they arrived, so two spellings of
  one element gave two steps that verify alike and compare unequal. They go
  through the domain now.
- `SymmetricLiftStep.build` failed over an algebraic number field, because
  adjoining `i` there gives a field whose elements `convert` cannot unify with
  the source's. Coefficients go through SymPy now.
- SYM-8's residual was compared with `expand`, which does not decide equality
  for a rational function, so a collision that holds was refused.
  `canonical.agree` decides it now, and so do the two comparisons beside it.
- The two halves of SYM-4's domain check were one branch, so a finite field
  reached the characteristic alone and the field half had no control of its
  own. Two branches, two messages, two probes.
- `make release` deleted the wheel it had just checked, because `sdist-test`
  began by emptying `dist/`. The archive is built into its own directory now,
  and `make dist-complete` requires exactly one wheel and one archive before
  `dist-check` runs.
- A test asserted `hash(one) == hash(b and other)`, which is `hash(other)`
  because `b` is truthy. It checked the intended claim by accident.
- The contract page and the code disagreed four times about which obligation
  covers what. CHC-8 cited DOM-1 for characteristic zero, which DOM-1 does not
  say; CHC-2's error type was one thing on the page and another in the
  constructor; SYM-4 and a docstring cited CHC-4 for a boundary that is CHC-2
  and CHC-8; and SYM-8 claimed an order total on expressions, named an
  implementation two versions stale, and did not list its own refusal among
  what supplied data can fail.
- Documentation claimed six step types where there are seven, or claimed of
  "every other step" something two of them no longer satisfy, in three rounds,
  and twice an entry of this file reported that cleanup as finished when it was
  not. `README.md` and this file called the milestone "the rest of the
  Reduction Theorem", where Theorem 2.1(b) asks in addition for a form linear
  in each original variable. `docs/provenance.md` did not list
  `examples.spacerat11` among the third-party maps, and the advice to use
  `over_field()` was wrong for a finite field, whose field of fractions is
  itself.

### Known limits

- SYM-7 is stated and not checked. The determinant of the gradient form follows
  from the identity and the source; computing it on the forty-variable lift did
  not finish in eight hours, where the same determinant at a random point takes
  22 seconds. `docs/roadmap.md` carries the measurement and milestone 0.7 the
  bottleneck.
- The chains `peel` finds are mostly not chains the untargeted search offers:
  none of six for `spacerat11`, two of seven for `macfarlane13`. Why is a
  measurement for 0.7.
- Nothing here computes `Delta^m(P^m)`, so the last link of the chain this
  project follows is not in the repository. It is milestone 0.8.
- `SymmetricLiftStep.transport` can refuse a collision that holds. It orients
  the pair itself, because a collision is a set, and two points that are
  unequal, compare equal and carry the same class metadata -- module, qualified
  name, declared assumptions and construction keywords -- cannot be ordered by
  anything it reads. No total order on SymPy expressions is claimed and the
  refusal is what stands in place of one. It is deterministic, and every
  collision this milestone produces is far from it.

## 0.5.0

Searching without a target. The question changes from "does this chain reach
that map" to "reduce this map to degree three", and the answer is a chain the
library found rather than one it was given.

`reduce_to_degree3` takes a source and nothing else. It reaches degree three
from Alpoege's normalized map in seven steps into dimension 13 and from Gao's
in twenty-nine into thirty-nine, and both chains verify. The chains computed by
hand take eight steps into fifteen and eight into seventeen.

What that is worth and what it is not is in `docs/references.md`. Thirteen
variables at degree three were reached a month earlier by A. Macfarlane, by a
route this library has no construction for, and no priority is claimed. A
seven-step BCW chain reaches his map from the same source, found by `peel`;
that chain is not one the untargeted enumerator can currently produce, and an
earlier draft of this entry said otherwise.
No minimality is claimed either, and the measurement behind that refusal is in
`docs/roadmap.md`.

The repository is English throughout since this milestone, tests included, and
a gate holds it there.

### Added

- `kellermap.untargeted` — an enumerator and a search that need no target.
  `untargeted_candidates` offers the steps Proposition (3.1) allows at a map,
  `ordered_steps` sorts them by what they remove, `remaining_weight` is the
  measure that bounds the walk, and `reduce_to_degree3` walks it. Obligations
  UNT-1 to UNT-11.
- `over=` on `search` and `peel`, so the coefficient ring is something a caller
  states rather than something inferred. `SearchOutcome` and `PeelOutcome`
  carry the ring they searched. Obligations DOM-1 to DOM-4.
- `examples.gao_quartic` and `gao_quartic_collision` — the second source map
  this project has, from arXiv:2608.00222 Section 3.5, licensed CC BY 4.0. Its
  collision is the only one here whose points are not rational.
- `examples.alpoege13` and `alpoege13_collision` — the thirteen-dimensional
  cubic reduction the search finds, with Alpoege's three points carried
  through.
- `scripts/reconstruct_alpoege13.py` and `scripts/reconstruct_macfarlane13.py`
  — two more independent renderings in plain SymPy, and
  `scripts/untargeted_space.py` and `scripts/search_cost.py`, which recompute
  the figures the UNT obligations rest on.
- `tests/test_language.py` — a gate that keeps the repository in English, with
  `scripts/foreign_words.py` as its audit instrument.

### Changed

- `kellermap.canonical` denests square roots, so two spellings of one algebraic
  number are one point. Without it a `Collision` could be built whose points
  coincide, which COL-4 forbids, and a correct image written as a nested
  radical was rejected. The module states what it does not claim: a radical of
  higher index.
- `undo` in `peeling` computes in the polynomial ring rather than in SymPy
  expressions. Measured by alternating runs: about a fifth off the peel.
- `Candidate` carries a coefficient and reports the filtration level a step
  reaches, in both directions.

### Found in review

None of these reached a release. Every one was introduced inside this
milestone and found before it closed, by five external audits of the
release candidates and by the maintainer. They are listed because a defect
that was caught is evidence about the review and not an embarrassment, and
because several of them were introduced by the fix for the one before.

- A grouped candidate could take the monomial equal to its divisor, leaving a
  constant cofactor, so `H` reached `EA^-1` and the chain that came back did
  not verify. Found by an external audit. The filtration level reported `0`
  there, which is why it stayed silent.
- `polynomials_over` treated an indeterminate of the coefficient domain as a
  later coordinate, so a pool value over `ZZ[T]` raised `GeneratorsError`
  where 0.4 had answered. Found by an external audit.
- `over` of the wrong type raised `VerificationError` where the error table
  promises `TypeError`, and `SearchOutcome.domain` shared a mutable domain
  with the caller. Both found by an external audit.
- `reduce_to_degree3` overran its budget: the check sat on entry to a frame
  and not between siblings, so at `budget=1` the walk descended into all
  twenty-two children of the root and reported one. All twenty-two are still
  built there, because ordering builds every candidate before choosing; what
  was wrong was descending into them. `examined` now says which of the two it
  counts, and it is the maps the walk descended into.
- `context` of the wrong type raised `AttributeError` from inside, and only
  when the source had degree above three. It raises `TypeError` at either
  degree.
- `SearchOutcome.domain` and the other two handed the same object out on
  every read, so a caller could reach into a frozen outcome. The accessor
  copies.
- The Gao attribution carried a title assembled from the abstract rather than
  the paper's own, which is the part CC BY asks for first.
- `docs/references.md` claimed that Macfarlane's map lies in the space the
  untargeted enumerator describes. Two of the seven steps do; the rest are
  outside it. `peel` searches a wider space, and the page says so now.
- `scripts/reconstruct_macfarlane13.py` still claimed the map lies in the
  space the untargeted enumerator describes. rc2 corrected that in
  `references.md` and here and left the script, which is a correction made in
  two places out of three.
- `references.md` cited the positions of the two matching candidates. A
  second audit reached different positions for the same steps, because no
  convention for matching a step against a proposal is written down. The
  positions are gone and which steps match stays.
- Four documentation leftovers: the docstring of `alpoege13` said the
  literature check was outstanding, a test comment said "no ranking",
  `architecture.md` opened its search section with "two directions", and the
  rc2 entry above said twenty-two maps were built where the defect was
  descending into them.
- The outcomes stored the copied ring in `_domain`, which put that name into
  the generated signature, the repr and `__match_args__`. The parameter is
  `domain` again, by `InitVar`, and the repr reports the ring by hand.
- The hash-seed test compared the step count and the dimension, which two
  different chains can share. It compares a fingerprint of the steps.
- The three outcome types ignored the coefficient ring in equality and
  hashing. Two results that agree on everything else and not on the ring are
  not the same result, which is the reason DOM-4 exists. Introduced in rc3 by
  the fix for the field name.
- `domain` looked optional: declaring it as an `InitVar` beside a property of
  the same name made the property object the parameter's default, so omitting
  it raised `AttributeError` from inside instead of `TypeError` at the call.
  The three constructors are written out by hand now.
- `references.md` explained the wrong candidate positions by a missing
  convention for matching. There is one, it gives 15 and 6, and the figures
  were simply wrong; the evasion is replaced by the correction.
- Two audit references named the wrong release candidate.
- `MACFARLANE_THIRD_POINT` in `tests/data.py` was cited by `references.md`
  and checked by nothing; the reconstruction script checked its own copy. A
  test compares the cited value against the chain the library computes.
- `dataclasses.replace` failed on all three outcome types: a hand-written
  constructor took `domain` while the field was `_domain`, so `fields()` and
  the signature disagreed. `domain` is a descriptor-typed field now, which is
  a field under that name and still copies the ring on read.
- The equality test required different hashes for different results, which
  asks more than Python promises. It requires inequality, and equal hashes
  for equal results.
- One audit reference named the wrong release candidate, and one line in
  `references.md` was not wrapped.

### Known limits

- `reduce_to_degree3` recurses once per step, so a chain longer than about 970
  steps raises `RecursionError` rather than reporting that it was cut off. The
  longest chain produced here is twenty-nine.
- No figure at BCW's third stage. The homogenization is not implemented, so
  nothing here compares with a cubic-homogeneous count.

## 0.4.0

Searching for a reduction rather than verifying one that is presented, and the
certified factorization of the published nineteen-dimensional Keller map of
degree three. `TranslationStep` completes the linear normalization, `search()`
walks from the source and `peel()` from the target, and the published chain is
a verified `Reduction` in the test suite, an independent rendering in plain
SymPy, and a search result.

What that factorization is worth is stated precisely in `docs/references.md`.
A chain was reconstructed by an external audit of this project and verified
here twice and independently. The backward search then found a second one, of
seventeen steps like the first, in eighteen examined maps. It is a chain and
not the chain, and no minimality is claimed for it.

The milestone went through fifteen release candidates and a series of external
audits. What each candidate changed is in the history of this file; the
candidates carry no public tag.

### Added

- `TranslationStep` — the first factor of Chapter II, Proposition (1.1), which
  completes the linear normalization for maps outside `MA^0`. Obligations TRA-1
  to TRA-8.
- `search(source, target, pool)` — a forward search for a step sequence, under
  SEA-1 to SEA-14, with `enumerate_candidates`, `anchors` and `Candidate`. It
  is told what a fresh coordinate may carry.
- `peel(source, target)` — a backward search, taking a chain off the target,
  under REV-1 to REV-12. It needs neither a value pool nor supplied names, and
  recovers the fifteen-dimensional reduction in eight examined maps where the
  forward search needs sixty-two and a value the published map no longer
  carries. `PeelOutcome`, `SearchOutcome` and `Undo` come with it.
- `BCWStep` takes a `coefficient` (BCW-11) and admits two `Fresh` slots naming
  one variable (BCW-12). Both are extensions beyond Proposition (3.1), marked
  as such, and the published chain needs both.
- `PolynomialMap.reordered()` — the generator order of a chain is the order its
  steps introduced them, and a target may name them differently.
- `PolynomialMap.identity()` — the identity was written out forty-one times,
  twenty-one of them repeating their own variable list.
- `kellermap.examples` — the Keller maps this repository writes out more than
  once, chosen by two counted criteria.
- `tests/test_alpoege19.py` and `scripts/reconstruct_alpoege19.py` — the chain
  as a verified `Reduction` and as an independent rendering.
- Gates for the agreements that had none: `tests/test_admissible_shapes.py` for
  every admissible shape of a step through every operation,
  `tests/test_ascii.py` for pure-ASCII Python files,
  `tests/test_documentation.py` for what the prose claims about the code,
  `tests/test_packaging.py` for what the source archive ships, and
  `tests/test_scripts.py` for the drivers.
- `scripts/mutation_probe.py` — it breaks one fragment of the source in a copy
  of the project, runs the suite, and reports whether anything noticed. Full
  statement coverage says a line ran; it does not say that removing the line
  would be caught, and those are different questions.

### Changed

- `Collision.transport` appends one coordinate per fresh generator rather than
  one per `Fresh` slot, which matters once two slots may name one variable.
- `m` counts distinct fresh variables, for the same reason. BCW-1 and BCW-2 are
  amended for the coefficient and for the shared name.
- The fixed maps moved to where their provenance puts them: `kellermap.examples`
  for the ones this project may distribute, `tests/data.py` for the
  nineteen-dimensional map, whose licence could not be established. The source
  archive does not carry that file.
- The source archive is defined by a positive list of what it ships rather than
  by a list of what it does not. A list of exclusions cannot be completed
  against names nobody has chosen yet, and the promise above it was that the
  archive does not depend on the state of the working directory.
- `docs/contracts.md` names a third gap beside the two it already named. Full
  statement coverage is not full obligation coverage; and full obligation
  coverage is not the same as every obligation being pinned by something.
- The release chain runs the coverage gate, the three reconstructions and the
  distribution metadata check automatically rather than by hand, on both ends
  of the supported Python range.

### Fixed

- `docs/references.md` attributed the filtration `MA_n^d(k)` to p. 304 of the
  paper. It is on p. 303; p. 304 opens with the decomposition of `GA_n(k)`.
  Read off the scan page by page, and the pages are separate rows now, since
  one row covering three pages is how they came to be confused.
- One Python file in the tree was not pure ASCII, against the project's own
  agreement, with no gate to attribute it to.

### Withdrawn

- The reading that the numbering `w1` to `w16` of the published map is the
  order the coordinates were introduced in. It is a topological order of the
  final carrier values and not a chronology; the chain settled it, and the
  paragraph that argued otherwise stays in `docs/roadmap.md`, withdrawn rather
  than deleted.

### Known limitations

- A reused factor must be carried by a coordinate of the source of that step,
  not by an earlier map in the chain.
- The forward search has a stated boundary, SEA-14: no coefficient other than
  one, and no step whose two slots are one fresh coordinate. Reporting no
  result for either is an exhausted space and not a deferral. Peeling has
  neither restriction.
- A `Collision` holds points over the coefficient domain of its map. The second
  family of counterexamples recorded in `docs/references.md`, arXiv:2608.00222
  §3.5, has a collision that is not rational, so reaching it needs a collision
  over a number field. It is named as a second source for 0.5.
- The coefficient ring is part of the search space and not a matter of
  presentation. A step preserves the domain, so the source fixes what is
  reachable, and a benchmark figure has to say which space it belongs to.
- No minimality and no priority is claimed for any dimension reached here.
  `docs/references.md` says what a comparison with the literature does and does
  not establish.
- A peel spends its time in SymPy expression work rather than in coefficient
  arithmetic, measured under `cProfile`. Working in the ring throughout, which
  `undo` still does not, is the lever, and it is 0.5 work.

## 0.3.0

Steps that reuse a carrier. A step no longer always introduces two new
generators, and a reduction that reuses them reaches a lower dimension:
`alpoege15`, this project's own reduction of Alpöge's map to dimension 15, is
derived and verified.

### Added

- `Fresh` and `Carried` — the two kinds of factor slot. `Fresh(P, u)`
  introduces a new generator whose component becomes `u + P`. `Carried(j)`
  reuses coordinate `j` of the source, which already has the form `X_j + P`.
- `BCWStep.m` — the number of generators the step introduces, which is 2, 1
  or 0.
- `BCW-10` — a reused slot must name a carrier. Its first two clauses are
  constructor invariants; the third is checked by `verify()` and gives the
  step its meaning, since the identity holds without it.
- `tests/test_alpoege15.py` and `scripts/reconstruct_alpoege15.py` — the
  fifteen-dimensional map, derived by the library and computed independently
  in plain SymPy.

### Changed

- `BCWStep` takes two factor slots instead of `P`, `Q` and a pair of
  variables. This is a breaking change to the constructor and to `build()`.
  Migration from 0.2:

  ```python
  # 0.2
  BCWStep.build(F, i, P, Q, (u, v), level)
  BCWStep(F, target, i, P, Q, (u, v), level)

  # 0.3
  BCWStep.build(F, i, Fresh(P, u), Fresh(Q, v), level)
  BCWStep(F, target, i, Fresh(P, u), Fresh(Q, v), level)
  ```

  Two `Fresh` slots are exactly the earlier step. `P`, `Q` and `variables`
  remain readable as properties.
- `BCW-2` allows `target.dimension == source.dimension + m`. This is the only
  binding obligation the milestone weakens rather than extends, and the reason
  0.3 is a minor release.
- `BCW-8` covers every `m`. A point gains one coordinate per `Fresh` slot. For
  `m ≥ 1` the image is unchanged apart from padding; at `m = 0` it moves to
  `c_index - c_u * c_w`.
- `BCW-9` states what `SUPPLIED` claims: the target was not produced by this
  library in this run, and nothing about who computed it.
- Documentation uses plainer language throughout. Metaphors for technical
  facts, rhetorical constructions and long sentences were removed, so that the
  text is easier for readers who do not have English as a first language.

### Known limitations

- The translation `(X − F(0))` is still not implemented, so a map must already
  fix the origin. Neither driving example needs it.
- A reused factor must be carried by a coordinate of the source of that step,
  not by an earlier map in the chain.
- Searching for a factorization rather than verifying one that is presented is
  the next milestone.

## 0.2.0

The verification framework. A reduction is now a chain of certified
identities rather than a computation one has to trust, and the
seventeen-dimensional cubic counterexample in the test suite is *derived* from
Alpöge's map instead of being asserted.

### Added

- `Collision` — distinct points sharing one image, verified by evaluation and
  carried across steps. It holds no map, since the same points are a collision
  of every map that identifies them.
- `VerificationError` — carries the identifier of the obligation that failed
  and, inside a chain, the index of the step.
- `kellermap.linear` — `GL_n(k)` as an ordered product of Gauss generators:
  `Transvection`, which is elementary in the sense of the paper, and
  `Transposition` and `Dilation`, which are not. `over_field()` widens a
  coefficient domain explicitly, since a dilation needs a unit.
- `kellermap.reduction` — the `Step` protocol, `LinearStep` for the linear
  normalization of BCW Chapter II, Proposition (1.1), and `Reduction`, which
  verifies every step and every join and nothing else.
- `Provenance` — whether a step's target was supplied or computed. For a
  supplied target the identity check compares an externally computed map
  against the formula and can fail; for a constructed one it compares the
  implementation against itself. The distinction is recorded rather than
  averaged away.
- `kellermap.bcw.BCWStep` — one certified application of Proposition (3.1),
  with `G` and `H` derived from `(index, P, Q, variables)` rather than stored
  beside them. Two things are wider than the paper states them: `P·Q` may be
  any subsum of the target component, and the target component may be any
  component.
- `ReductionContext` — checks that a `VariableFactory` keeps its promises
  across a chain, rechecking purity and composition on every call.
- `kellermap.canonical` — the single normal form the package compares in.
- `docs/contracts.md` — every obligation of the verification surface, stated
  normatively before the implementation, with a stable identifier that the
  exception cites when it fails.
- `scripts/reconstruct_bcw17.py` — the same reduction in plain SymPy, without
  this library, as an independent second implementation of formula (1).
- A published cubic Keller map in dimension 19 as a second regression example,
  recomputed rather than trusted.

### Changed

- `tests/test_bcw17.py` derives its map: a `Reduction` of eight steps from
  Alpöge's map, verified step by step, carrying the three-point collision from
  `k³` to `k¹⁷`. Only the last step is supplied, because the intermediate maps
  are published nowhere; a negative control shows the check there bites.
- The linear normalization is cited as Chapter II, Proposition (1.1), p. 303,
  not as §4. Section 4 carries the same formula but with the linear part
  already in `EA⁰`; the step this library performs is the other one.
- Full statement coverage is enforced (`fail_under = 100`), and `make release`
  gained the coverage and `twine check` gates.

### Fixed

Findings from two external audits of the release candidates, none of which
required new functionality.

- `Collision` compared coordinates with `expand`, which does not clear a
  denominator; over `k(T)` two spellings of one point were accepted as two
  points. Coordinates are now put into normal form on entry, which also keeps
  equality and hashing consistent.
- `BCWStep` checked its factors by symbol name, which refused a valid `T·x`
  over `k[T]`, accepted a fresh variable named `T`, accepted two symbols of one
  name, and accepted non-polynomials. `P` and `Q` now pass through the source's
  ring.
- `provenance` was a public, unchecked constructor argument, so a supplied step
  could claim to be constructed. It is no longer settable, and it is part of
  equality and hashing.
- `LinearStep.normalize()` accepted a map with `F(0) ≠ 0` and built a step that
  then failed its own verification. Proposition (1.1) puts a translation first;
  such a source is now refused with that reason.
- `BCWStep.build()` consumed its `variables` argument twice, so a generator was
  consumed by the first construction.

### Known limitations

- The translation `(X − F(0))` is not implemented, so a map must already fix
  the origin. It is elementary in the sense of the paper and needs no new
  non-elementary type.
- `BCWStep` fixes two fresh variables per step, so a reduction that shares
  carrier variables across steps cannot be expressed as a chain of them.
- Searching for a factorization rather than verifying a presented one is a
  later milestone; see `docs/roadmap.md`.

## 0.1.0

The algebraic foundations: polynomial maps over a sparse `PolyRing` with value
semantics, simultaneous composition, Jacobian matrices and determinants via the
unipotent carrier block, stable extension with an injectable variable factory,
and elementary automorphisms with the filtration of `EA_n(k)`.
