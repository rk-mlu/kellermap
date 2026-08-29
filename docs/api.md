# API

Every example below is executed by the test suite. If the library changes and
this page does not, `make check` fails.

`architecture.md` explains *why* things are the way they are; this page says
what they do.

---

## Contents

- [Public surface](#public-surface)
- [PolynomialMap](#polynomialmap)
  - [Construction](#construction)
  - [The expression boundary](#the-expression-boundary)
  - [Degree, order and the filtration](#degree-order-and-the-filtration)
  - [Composition](#composition)
  - [Jacobian and determinant](#jacobian-and-determinant)
  - [The identity](#the-identity)
  - [Stable extension](#stable-extension)
  - [Reordering](#reordering)
- [Example maps](#example-maps)
- [Variable factories](#variable-factories)
- [Elementary automorphisms](#elementary-automorphisms)
- [Linear automorphisms](#linear-automorphisms)
- [Collisions](#collisions)
- [Steps and reductions](#steps-and-reductions)
  - [The translation](#the-translation)
- [The BCW step](#the-bcw-step)
- [The unipotent step](#the-unipotent-step)
- [The homogenization](#the-homogenization)
- [Finding candidates](#finding-candidates)
- [Assembling a chain](#assembling-a-chain)
- [Peeling a chain off a target](#peeling-a-chain-off-a-target)
- [Naming across a reduction](#naming-across-a-reduction)
- [Guarantees](#guarantees)
- [Errors](#errors)

---

## Public surface

```python
>>> import kellermap
>>> kellermap.__all__
['DEFAULT_VARIABLE_FACTORY', 'Candidate', 'Collision', 'Dilation', 'ElementaryAutomorphism', 'ElementaryFactor', 'FixedVariableFactory', 'IndexedVariableFactory', 'LinearAutomorphism', 'LinearFactor', 'LinearStep', 'PeelOutcome', 'PolynomialMap', 'Provenance', 'Reduction', 'ReductionOutcome', 'ReductionContext', 'SearchOutcome', 'Step', 'TranslationStep', 'Transposition', 'Transvection', 'Undo', 'VariableFactory', 'VerificationError', 'anchors', 'conjugate', 'diagonal_matching', 'enumerate_candidates', 'lowers_the_weight', 'field_ring', 'over_field', 'peel', 'reduce_to_degree3', 'remaining_weight', 'reserved_names', 'search', 'untargeted_candidates']

```

Anything not listed there is internal and may change without notice.

---

## PolynomialMap

A polynomial endomorphism `F : k^n -> k^n`.

### Construction

From SymPy expressions:

```python
>>> import sympy as sp
>>> from kellermap import PolynomialMap
>>> x, y = sp.symbols("x y")
>>> F = PolynomialMap((x, y), (x + y**3, y))
>>> F.dimension
2

```

Or directly from elements of a sparse polynomial ring, which is the fast path
used internally:

```python
>>> from sympy.polys.domains import QQ
>>> from sympy.polys.rings import ring
>>> R, a, b = ring("a,b", QQ)
>>> PolynomialMap.from_ring(R, (a + b**3, b)).components
(a + b**3, b)

```

Symbols that are not among the variables become part of the coefficient
domain. They are coefficients, not coordinates, and do not count towards
degree or order:

```python
>>> T = sp.Symbol("T")
>>> G = PolynomialMap((x, y), (T**5 * x + y, x))
>>> G.ring.domain
ZZ[T]
>>> G.degree()
1

```

### The expression boundary

`components`, `matrix` and `jacobian()` return SymPy objects for inspection,
printing and LaTeX output. The matrices are immutable.

```python
>>> F.components
(x + y**3, y)
>>> F.matrix.T
Matrix([[x + y**3, y]])
>>> F(sp.Integer(2), sp.Integer(3)).T
Matrix([[29, 3]])

```

`to_polynomials()` returns the sparse representation, as defensive copies:

```python
>>> [str(p) for p in F.to_polynomials()]
['x + y**3', 'y']

```

### Degree, order and the filtration

`degree()` is the largest total degree over all components, `order()` the
smallest. The zero map has degree `0` and order `math.inf`.

```python
>>> F.degree(), F.order()
(3, 1)

```

BCW filter by the order of the displacement `F - X`:

    F in MA^d  <=>  ord(F - X) > d

```python
>>> F.displacement().components
(y**3, 0)
>>> F.filtration_degree()
2
>>> F.is_in_MA(2), F.is_in_MA(3)
(True, False)

```

The identity lies in every `MA^d`:

```python
>>> PolynomialMap((x, y), (x, y)).filtration_degree()
inf

```

### Composition

`F.compose(G)` is `F o G`, substituting simultaneously:

```python
>>> H = PolynomialMap((x, y), (y, x))
>>> F.compose(H).components
(x**3 + y, x)
>>> H.compose(F).components
(y, x + y**3)

```

Both maps must carry the same variables in the same order. Differing but
compatible coefficient domains are unified.

### Jacobian and determinant

```python
>>> F.jacobian()
Matrix([
[1, 3*y**2],
[0,      1]])
>>> F.determinant()
1

```

The determinant is computed over the sparse ring. Where a subset of the
coordinates spans a unipotent block of the Jacobian — which stable extensions,
elementary automorphisms and BCW-reduced maps always produce — it is obtained
from the Schur complement of that block instead of from an `n x n` expansion.
`carrier_indices` reports the block:

```python
>>> F.carrier_indices
(0, 1)

```

An empty tuple means no such block was found and the general path was used:

```python
>>> PolynomialMap((x, y), (x*y + 1, x - y**2)).carrier_indices
()

```

This is a performance property only; both paths return the same polynomial.

### The identity

`PolynomialMap.identity(variables)` builds the identity on those variables.
Written out, the identity repeats its variable list, and a typo in the second
copy gives a map that is not the identity and still constructs:

```python
>>> PolynomialMap.identity((x, y)).components
(x, y)
>>> PolynomialMap.identity((x, y)).determinant()
1

```

The other spelling, `from_ring(ring, ring.gens)`, repeats nothing and keeps its
ring explicit. It stays as it is.

### Stable extension

`F.extend(m)` appends `m` identity coordinates:

```python
>>> F.extend(2).components
(x + y**3, y, X3, X4)

```

Degree and order are *not* preserved. The new coordinates are monomials of
degree exactly one, so for `m > 0`

    deg(F^[m]) = max(deg F, 1),      ord(F^[m]) = min(ord F, 1).

What survives is the displacement, and therefore the filtration degree:

```python
>>> F.extend(2).filtration_degree() == F.filtration_degree()
True

```

### Reordering

`F.reordered(variables)` lists the same map's coordinates in a different
order. Coordinate `i` of the result carries `variables[i]` and the component
that belonged to that generator, so both lists move together:

```python
>>> F.components
(x + y**3, y)
>>> F.reordered((y, x)).components
(y, x + y**3)

```

Nothing about the map changes, and nothing is certified — there is nothing to
certify. Degree, order, filtration degree and the Jacobian determinant all
survive, and the round trip returns the original:

```python
>>> shuffled = F.reordered((y, x))
>>> (shuffled.degree(), shuffled.determinant()) == (F.degree(), F.determinant())
True
>>> shuffled.reordered((x, y)) == F
True

```

Equality compares the variables as an ordered tuple, so the two presentations
are *not* equal until one of them is rewritten. That is what the method is
for: a chain built step by step lists its generators in the order the steps
introduced them, which need not be the order in which a published map lists
the same generators.

```python
>>> shuffled == F
False

```

Anything that is not a permutation of the map's own variables is refused,
since dropping, adding or substituting a generator would be a different map:

```python
>>> F.reordered((x, x))
Traceback (most recent call last):
    ...
ValueError: The order (x, x) is not a permutation of (x, y).

```

---

## Example maps

`kellermap.examples` holds the Keller maps this repository writes out in more
than one place. Two criteria decide what is there: a map is included if it is
repeated, and if its Jacobian determinant is a non-zero constant. Repeated maps
that are *not* Keller maps stay where they are used, because they are written
the way they are precisely for that reason.

```python
>>> from kellermap import examples, over_field
>>> examples.factorable_shear().components
(x1 + x2**2*x3**2, x2, x3)
>>> examples.alpoege().degree(), examples.alpoege().determinant()
(7, -2)

```

They are functions, so importing `kellermap` builds nothing, and each returns
its map over the domain its coefficients imply. Use `over_field` where a field
is needed:

```python
>>> examples.parametric_shear().ring.domain
ZZ[T]
>>> over_field(examples.quadratic_shear()).ring.domain
QQ

```

Everything there was written for this project except two source maps, which are
somebody else's mathematics: `alpoege` and `gao_quartic`. `docs/references.md`
records both sources, what each paper claims, and what agreement with it does
and does not establish.

`gao_quartic` is the second, from arXiv:2608.00222, licensed CC BY 4.0. Its
collision is the only one here whose points are not rational:

```python
>>> quartic = examples.gao_quartic()
>>> quartic.degree(), quartic.determinant()
(12, 2)
>>> examples.gao_quartic_collision().image
(0, 1, 1)

```

The name says geometric degree and not dimension. `bcw17` and `alpoege15` are
reductions and their dimension is what tells them apart; the paper carries two
maps in three variables, and the geometric degree is what distinguishes those.

---

## Variable factories

`extend()` names its new generators through a `VariableFactory`: any callable
taking a ring and a count and returning that many symbols.

```python
>>> from kellermap import IndexedVariableFactory
>>> F.extend(2, IndexedVariableFactory(prefix="u")).variables
(x, y, u1, u2)

```

Without an explicit prefix the convention is read off the existing
generators, so a numbered map stays numbered:

```python
>>> numbered = PolynomialMap(sp.symbols("x1:4"), sp.symbols("x1:4"))
>>> numbered.extend(2).variables
(x1, x2, x3, x4, x5)

```

`reserved_names()` reports what a factory must avoid — ring generators and
coefficient-domain symbols alike:

```python
>>> from kellermap import reserved_names
>>> sorted(reserved_names(G.ring))
['T', 'x', 'y']

```

A custom factory must satisfy two conditions. Both are checked in the test
suite for the shipped implementations, and neither is verified for yours at
runtime, because a violation produces valid maps that are merely the wrong
ones.

**Purity.** The same ring and count must always give the same names.
Otherwise the monoid identity `(F o G)^[m] = F^[m] o G^[m]`, whose sides reach
`extend()` through three separate calls, silently fails.

**Composition.** Extending by `m` and then by `l` must allocate the names a
single extension by `m + l` would:

```python
>>> F.extend(2).extend(2) == F.extend(4)
True

```

This does not follow from purity. A factory naming its output after the size
of the ring it was handed is pure and never collides, yet gives `g2_1, g2_2,
g4_1, g4_2` where a single call gives `g2_1, ..., g2_4`.

What `extend()` *does* check is the result: count, type, pairwise
distinctness, and collisions.

---

## Elementary automorphisms

`EA_n(k)` is a group; its generators are not closed under composition, so
there are two types.

**`ElementaryFactor`** is a generator in the sense of BCW p. 304: the map
fixing every coordinate but one,

    X_j |-> X_j + P,       P free of X_j.

```python
>>> from kellermap import ElementaryFactor
>>> R, X1, X2, X3, X4 = ring("X1,X2,X3,X4", QQ)
>>> G = ElementaryFactor(R, index=0, polynomial=-X3 * X4)
>>> G.to_polynomial_map().components
(X1 - X3*X4, X2, X3, X4)

```

The inverse is read off the definition rather than solved for:

```python
>>> G.inverse().to_polynomial_map().components
(X1 + X3*X4, X2, X3, X4)

```

**`ElementaryAutomorphism`** is an element of the group, stored as the ordered
product of its factors. Proposition (3.1) needs this: its `G` is one factor,
its `H` is two.

```python
>>> from kellermap import ElementaryAutomorphism
>>> H = ElementaryAutomorphism(
...     [ElementaryFactor(R, 2, X2**2), ElementaryFactor(R, 3, X2**2)]
... )
>>> H.to_polynomial_map().components
(X1, X2, X2**2 + X3, X2**2 + X4)

```

Composition concatenates the factorizations, inversion reverses and inverts:

```python
>>> H.compose(H.inverse()).to_polynomial_map() == PolynomialMap.from_ring(R, R.gens)
True

```

`apply_to()` composes with a map on the left. A factor moves one coordinate,
so this performs one polynomial composition where a full map composition would
perform `n`:

```python
>>> target = PolynomialMap.from_ring(R, (X1 + X2**2, X2, X3, X4))
>>> G.apply_to(target) == G.to_polynomial_map().compose(target)
True

```

The determinant is one, structurally, for every factor and every product:

```python
>>> G.determinant(), H.determinant()
(1, 1)

```

The filtration level is not structural. Two factors in `EA^0` can multiply to
something deeper, so `filtration_degree()` forms the map:

```python
>>> up = ElementaryFactor(R, 0, X2)
>>> down = ElementaryFactor(R, 0, -X2)
>>> up.filtration_degree(), down.filtration_degree()
(0, 0)
>>> ElementaryAutomorphism([up, down]).filtration_degree()
inf

```

Two different factorizations of the same automorphism are different objects.
The factorization is the certificate:

```python
>>> cancelling = ElementaryAutomorphism([G, G.inverse()])
>>> empty = ElementaryAutomorphism.identity()
>>> cancelling.to_polynomial_map() == empty.to_polynomial_map(R)
True
>>> cancelling == empty
False

```

---

## Linear automorphisms

The transformation of BCW Chapter II, Proposition (1.1), as an ordered product
of Gauss
operations. Three generators, and which of them are elementary in the sense of
the paper is the reason the module exists.

A transvection is elementary and can be handed to `EA_n(k)` unchanged:

```python
>>> from kellermap import Transvection, Transposition, Dilation
>>> shear = Transvection(R, 0, 1, 3)
>>> shear.is_elementary
True
>>> shear.as_elementary_factor().polynomial
3*X2
>>> shear.as_elementary_factor().filtration_degree()
0

```

A transposition and a dilation are not. A dilation displaces `X_i` by
`(a - 1) X_i`, which involves `X_i`; a transposition moves two coordinates and
has determinant `-1`:

```python
>>> Transposition(R, 0, 1).is_elementary, Transposition(R, 0, 1).determinant()
(False, -1)
>>> Dilation(R, 0, 2).is_elementary, Dilation(R, 0, 2).determinant()
(False, 2)

```

`factorize()` runs Gauss-Jordan elimination and keeps the row operations. The
product of the factors is the matrix again:

```python
>>> from kellermap import LinearAutomorphism
>>> matrix = sp.diag(sp.Matrix([[0, 2], [1, 0]]), 1, 1)
>>> L = LinearAutomorphism.factorize(R, matrix)
>>> L.factors
(Transposition(first=0, second=1), Dilation(index=1, coefficient=2))
>>> sp.Matrix(L.matrix()) == matrix
True
>>> L.determinant()
-2

```

The determinant is the product of the factor determinants, so no matrix is
formed to obtain it. `apply_to()` composes on the left, which recombines the
components without substituting anything:

```python
>>> square = PolynomialMap.from_ring(R, (X1 + X2**2, X2, X3, X4))
>>> L.apply_to(square).components
(2*X2, X1 + X2**2, X3, X4)

```

Dilations need their coefficient to be a unit, so a map read off a paper over
`ZZ` has to be widened first. That is a deliberate step, not something the
arithmetic does quietly:

```python
>>> from kellermap import over_field
>>> integral = PolynomialMap((x, y), (x + y**2, y))
>>> integral.ring.domain, over_field(integral).ring.domain
(ZZ, QQ)

```

Two factorizations of one matrix are different objects, exactly as for
`ElementaryAutomorphism`: the factorization is the certificate.

---

## Collisions

Several distinct points sharing one image. For a Keller map this is the whole
point: it is what makes the map a counterexample rather than merely a
candidate.

```python
>>> from kellermap import Collision
>>> square = PolynomialMap((x, y), (x**2, y))
>>> collision = Collision.at(square, ((1, 0), (-1, 0)))
>>> collision.image
(1, 0)
>>> len(collision), collision.dimension
(2, 2)

```

`Collision.at()` evaluates the map at the first point and verifies the result
before returning it, so it cannot manufacture a collision out of points that
do not collide. Where the image is a claim rather than a consequence, state it
and check it:

```python
>>> Collision(((1, 0), (-1, 0)), (1, 0)).verify(square) is None
True

```

`verify()` returns nothing and raises `VerificationError` on failure, carrying
the identifier of the obligation from `docs/contracts.md` that failed:

```python
>>> from kellermap import VerificationError
>>> try:
...     Collision(((1, 0), (-1, 0)), (0, 0)).verify(square)
... except VerificationError as failure:
...     failure.obligation
'COL-3'

```

Distinct points are a constructor invariant rather than an obligation, and
distinctness is decided by value:

```python
>>> Collision(((sp.Rational(1, 2), 0), (sp.Rational(2, 4), 0)), (0, 0))
Traceback (most recent call last):
    ...
ValueError: Points 0 and 1 are equal; a collision needs distinct points.

```

A collision holds no map, because a reduction carries it from one map to the
next. Two operations move it. Appending coordinates is what a stabilizing step
needs:

```python
>>> collision.extended(((2, 3), (-2, 3)), (0, 0)).points[0]
(1, 0, 2, 3)

```

Replacing the image is what composing a map on the left does, since left
composition leaves every preimage where it was:

```python
>>> collision.with_image((4, 0)).verify(PolynomialMap((x, y), (4 * x**2, y)))

```

Equality treats the points as a set. Listing them in another order is the same
certificate:

```python
>>> Collision(((-1, 0), (1, 0)), (1, 0)) == collision
True

```

---

## Steps and reductions

A step certifies one identity between two maps. `Reduction` chains steps and
verifies the joins between them. `LinearStep` is the kind that composes an
element of `GL_n(k)` on the left, which is what BCW Chapter II, Proposition
(1.1) does.

```python
>>> from kellermap import LinearStep, Reduction, over_field
>>> keller = over_field(PolynomialMap((x, y), (x + y**2, y)))
>>> step = LinearStep.normalize(keller)
>>> step.transformation.factors
()
>>> step.verify() is None
True

```

`normalize()` builds the transformation from `J(F)(0)` and marks the step as
claiming to be the normalization, which turns on LIN-6: the transformation has
to be the inverse of the linear part, and the target has to reach `MA^1`.

A step records where its target came from. When the step computed it, the
identity check compares the implementation against itself and cannot fail,
which is weaker evidence and is recorded as such:

```python
>>> from kellermap import Provenance
>>> step.provenance is Provenance.CONSTRUCTED
True
>>> supplied = LinearStep(keller, step.target, step.transformation)
>>> supplied.provenance is Provenance.SUPPLIED
True

```

The public constructor takes no `provenance` argument: a target reaching it
came from outside, and `build()` is the only route to a constructed step. The
label is therefore part of the value, and two steps that disagree about it are
not equal even with the same target:

```python
>>> supplied == step
False

```

`Reduction` verifies each step and each join, and a failure names the step it
came from:

```python
>>> chain = Reduction([step])
>>> chain.verify() is None
True
>>> chain.dimensions(), chain.degrees()
((2, 2), (2, 2))

```

A chain carries a collision from its source to its target, verifying it at
every intermediate map rather than only at the ends:

```python
>>> from kellermap import Collision
>>> square = over_field(PolynomialMap((x, y), (x**2, y)))
>>> flip = LinearStep.build(
...     square, LinearAutomorphism([Transposition(square.ring, 0, 1)])
... )
>>> Reduction([flip]).transport(Collision.at(square, ((1, 0), (-1, 0)))).image
(0, 1)

```

Left composition leaves every preimage where it was and moves only the image.

### The translation

Proposition (1.1) splits `F` as `(X + F(0)) ∘ F_(1) ∘ F'`, so the linear
normalization is the *second* factor. A map that does not fix the origin has
to lose the first one before `LinearStep.normalize` will look at it:

```python
>>> from kellermap import TranslationStep
>>> moved = over_field(PolynomialMap((x, y), (x + y**2 + 1, y + 2)))
>>> LinearStep.normalize(moved)
Traceback (most recent call last):
    ...
ValueError: The map does not fix the origin, so the linear normalization is not the first step: Proposition (1.1) splits F as (X + F(0)) o F_(1) o F', and the translation (X - F(0)) has to come off first. Use TranslationStep.normalize on this map and normalize its target.

```

`TranslationStep.normalize` takes `F(0)` off, and the two steps chain:

```python
>>> shifted = TranslationStep.normalize(moved)
>>> shifted.shift
(1, 2)
>>> shifted.target == keller
True
>>> Reduction([shifted, LinearStep.normalize(shifted.target)]).verify() is None
True

```

A translation is elementary in the sense of the paper, and the step exhibits
the factorization rather than asserting invertibility:

```python
>>> [(factor.index, factor.polynomial) for factor in shifted.translation.factors]
[(0, -1), (1, -2)]

```

It lies in no `EA^d` for `d ≥ 0` all the same, because it leaves `MA^0`. The
degree `-1` belongs to the transformation; what the *step* reports is the `EA`
bound it establishes for its target, and a translation establishes none:

```python
>>> shifted.translation.filtration_degree()
-1
>>> shifted.filtration_level
inf

```

That is the difference that keeps `Reduction.filtration_level()` meaningful:
the level describes the target of the chain, and the translation is a
statement about its source.

---

## The BCW step

Proposition (3.1): two new dimensions, one factorization removed. It lives in
the subpackage, because it is the one object here that is specific to the
paper.

```python
>>> from kellermap.bcw import BCWStep, Fresh
>>> x1, x2, x3, x4, x5 = sp.symbols("x1 x2 x3 x4 x5")
>>> quartic = over_field(
...     PolynomialMap((x1, x2, x3), (x1 + x2**2 * x3**2, x2, x3))
... )
>>> step = BCWStep.build(quartic, 0, Fresh(x2**2, x4), Fresh(x3**2, x5))
>>> step.target.components
(x1 - x2**2*x5 - x3**2*x4 - x4*x5, x2, x3, x2**2 + x4, x3**2 + x5)
>>> step.verify() is None
True

```

`G` and `H` are derived from the index and the two factor slots. They are never
supplied separately, because storing both descriptions would allow them to
disagree:

```python
>>> step.H.factors[0].polynomial, step.H.factors[1].polynomial
(x2**2, x3**2)
>>> step.G.factors[0].polynomial
-x4*x5

```

The declared filtration level is checked rather than inferred. Proposition
(3.1) admits `EA^0` where the factorization has to be linear, and whether a
step leaves `MA^1` is a fact the certificate records:

```python
>>> linear = over_field(PolynomialMap((x1, x2, x3), (x1 + x2 * x3, x2, x3)))
>>> BCWStep.build(
...     linear, 0, Fresh(x2, x4), Fresh(x3, x5), filtration_level=1
... ).verify()
Traceback (most recent call last):
    ...
kellermap.errors.VerificationError: [BCW-6] H does not lie in EA^1; it reaches EA^0.

```

`P` and `Q` are converted into the source's ring and stored there, so a factor
that is not a polynomial over it is refused at construction rather than failing
later. Parameters of the coefficient domain are not coordinates and are
admitted:

```python
>>> T = sp.Symbol("T")
>>> parametric = PolynomialMap((x1, x2, x3), (x1 + T * x2**2 * x3**2, x2, x3))
>>> parametric.ring.domain
ZZ[T]
>>> BCWStep.build(parametric, 0, Fresh(T * x2**2, x4), Fresh(x3**2, x5)).P
T*x2**2
>>> BCWStep.build(parametric, 0, Fresh(1 / x2, x4), Fresh(x3**2, x5))
Traceback (most recent call last):
    ...
ValueError: P must be a polynomial over the coefficient domain ZZ[T] in the variables ('x1', 'x2', 'x3'); got 1/x2.

```

A slot may also reuse a coordinate that already carries the factor. The step
then introduces fewer generators, and `m` reports how many:

```python
>>> from kellermap.bcw import Carried
>>> carrying = over_field(
...     PolynomialMap((x1, x2, x3, x4), (x1 + x2**2 * x3**2, x2, x3, x2**2 + x4))
... )
>>> reused = BCWStep.build(carrying, 0, Carried(3), Fresh(x3**2, x5))
>>> reused.m, reused.P, reused.Q
(1, x2**2, x3**2)
>>> reused.target.dimension
5
>>> reused.verify() is None
True

```

With both slots reused the step introduces nothing at all, `H` is the identity,
and the step is `F' = G ∘ F`. The coordinate a slot reuses must actually carry
its factor, which is BCW-10:

```python
>>> twisted = over_field(
...     PolynomialMap((x1, x2, x3, x4), (x1, x2, x3, x4 * x2 + x4))
... )
>>> BCWStep.build(twisted, 0, Carried(3), Fresh(x3, x5)).verify()
Traceback (most recent call last):
    ...
kellermap.errors.VerificationError: [BCW-10] Slot 0 reuses coordinate 3, but component 3 of the source is not x4 plus something free of it.

```

A step carries a collision by filling the fresh coordinates with `-P(a)` and
`-Q(a)`, leaving the image padded with zeros:

```python
>>> square = over_field(PolynomialMap((x1, x2, x3), (x1**2, x2, x3)))
>>> carried = BCWStep.build(
...     square, 0, Fresh(x2**2, x4), Fresh(x3**2, x5)
... ).transport(
...     Collision.at(square, ((1, 2, 3), (-1, 2, 3)))
... )
>>> carried.points[0], carried.image
((1, 2, 3, -4, -9), (1, 2, 3, 0, 0))

```

A reused slot appends no coordinate, since the step adds no generator for it.
It does affect the image: `G` reduces the target component by the product of
the two slot values there, and a fresh slot contributes zero. So the image
moves only when both slots are reused:

```python
>>> both = over_field(PolynomialMap(
...     (x1, x2, x3, x4, x5), (x1**2, x2, x3, x2**2 + x4, x3**2 + x5)
... ))
>>> pair = Collision(((1, 2, 3, 0, 0), (-1, 2, 3, 0, 0)), (1, 2, 3, 4, 9))
>>> moved = BCWStep.build(both, 0, Carried(3), Carried(4)).transport(pair)
>>> moved.points == pair.points
True
>>> moved.image
(-35, 2, 3, 4, 9)

```

The first coordinate moved from `1` to `1 - 4 * 9`.

---

## The unipotent step

The second step of the Reduction Theorem, Section 4. It doubles the dimension
and makes the Jacobian of the displacement nilpotent. Given `F = X + F_(2) +
F_(3)`, the target is `(X + F_(2) + Y, Y - F_(3))`:

```python
>>> from kellermap.bcw import UnipotentStep
>>> cubic = over_field(
...     PolynomialMap((x1, x2, x3), (x1 + x2**2 * x3, x2, x3))
... )
>>> lift = UnipotentStep.build(cubic)
>>> lift.variables
(x4, x5, x6)
>>> lift.target.components
(x1 + x4, x2 + x5, x3 + x6, -x2**2*x3 + x4, x5, x6)
>>> lift.verify() is None
True

```

There is nothing to choose here. Every other step type takes a component, a
matrix or a factorization; given a source, this one is determined up to the
names of the fresh generators, and `build` is the ordinary route rather than
the convenient one.

`G` and `H` are derived from the source, one factor per component each:

```python
>>> [factor.polynomial for factor in lift.G.factors]
[x4, x5, x6]
>>> [factor.polynomial for factor in lift.H.factors]
[-x2**2*x3, 0, 0]

```

Three obligations constrain the *source*, so `build` cannot make them true and
a constructed step still fails to verify. The map has to lie in `MA^1`, which
is where `LinearStep.normalize` comes in:

```python
>>> linear = over_field(PolynomialMap((x1, x2), (x1 + x2, x2)))
>>> linear.is_in_MA(1)
False
>>> UnipotentStep.build(linear).verify()
Traceback (most recent call last):
    ...
kellermap.errors.VerificationError: [UNI-2] The source is not in MA^1: its displacement has order 1. Section 4 starts from a map whose displacement has order at least two; LinearStep.normalize produces one.

```

The target leaves `MA^1` itself: its displacement has the linear part `(Y, 0)`.
A step that follows may not assume otherwise, and the step declines to be
applied twice:

```python
>>> lift.target.is_in_MA(1)
False
>>> lift.filtration_level
0

```

A collision is carried by lifting each point with the cubic part of the
displacement. `H` displaces `Y` by `-F_(3)`, so its inverse displaces it by
`+F_(3)`, and the sign is opposite to the BCW step's:

```python
>>> square = over_field(
...     PolynomialMap((x1, x2, x3), (x1**2 + x2**3, x2, x3))
... )
>>> pair = Collision(((1, 2, 3), (-1, 2, 3)), (9, 2, 3))
>>> moved = UnipotentStep.build(square).transport(pair)
>>> moved.points
((1, 2, 3, 8, 0, 0), (-1, 2, 3, 8, 0, 0))
>>> moved.image
(9, 2, 3, 0, 0, 0)

```

That source is not a Keller map and `verify` would refuse it. `transport` does
not: it checks the incoming collision against the source and the outgoing one
against the target, and neither needs the step to apply.

---

## The homogenization

The third step of the Reduction Theorem. It adds one variable and lifts each
part of the displacement by the power of `T` its own degree is short of, so the
result is cubic homogeneous:

```python
>>> from kellermap.bcw import HomogenizationStep
>>> shear = over_field(
...     PolynomialMap((x1, x2), (x1 + x2 + x2**2, x2))
... )
>>> homogenized = HomogenizationStep.build(shear)
>>> homogenized.variable
x3
>>> homogenized.target.components
(x1 + x2**2*x3 + x2*x3**2, x2, x3)
>>> homogenized.verify() is None
True

```

The linear part is lifted by `T**2` and the quadratic one by `T`. `parts`
reports what the formula read, in the order `N_(1)`, `N_(2)`, `N_(3)`:

```python
>>> homogenized.parts
((x2, 0), (x2**2, 0), (0, 0))

```

This step is not a composition, so there is no `EA` level to declare and
`filtration_level` is `math.inf`. What relates the two maps is a slice: setting
`T = 1` returns the source. The target is in `MA^2`, where the unipotent step
before it leaves `MA^1` altogether:

```python
>>> homogenized.filtration_level
inf
>>> homogenized.target.filtration_degree()
2

```

The source has to have nilpotent Jacobian, and being a Keller map is not
enough. `(2*x1, x2/2)` has determinant one and a displacement whose Jacobian is
`diag(1, -1/2)`:

```python
>>> HomogenizationStep.build(
...     over_field(PolynomialMap((x1, x2), (2 * x1, x2 / 2)))
... ).verify()
Traceback (most recent call last):
    ...
kellermap.errors.VerificationError: [HOM-3] det(I + T J(N)) is -x3**2/2 + x3/2 + 1 and not one, so the displacement of the source does not have nilpotent Jacobian. The second step of Section 4 is what produces one; a Keller source is not enough, because the target's Jacobian is a scaled substitution of this one.

```

A collision moves to the slice `T = 1`. The appended coordinate is one and not
zero, unlike every other step here: at `T = 0` only `N_(3)` survives, and that
slice is a different map.

```python
>>> square = over_field(PolynomialMap((x1, x2), (x1**2 + x2**3, x2)))
>>> pair = Collision(((1, 2), (-1, 2)), (9, 2))
>>> moved = HomogenizationStep.build(square).transport(pair)
>>> moved.points
((1, 2, 1), (-1, 2, 1))
>>> moved.image
(9, 2, 1)

```

---

## Finding candidates

`enumerate_candidates(source, pool)` lists the steps Proposition (3.1) could
take at a map. It verifies nothing: a `Candidate` is a proposal, and it becomes
evidence only by being built and verified.

The `pool` bounds the search. It holds the polynomials a fresh coordinate may
carry, and one factor of every candidate comes from it; the other is obtained
by dividing the component and is free.

```python
>>> from kellermap import enumerate_candidates
>>> from kellermap.bcw import Carried
>>> flat = PolynomialMap((x, y), (x + x**2 * y**3, y))
>>> found = enumerate_candidates(flat, [x * y])
>>> [(c.index, c.values(flat)) for c in found]
[(0, (x*y, x*y**2))]

```

The candidate says: remove `x**2 * y**3` from component 0, splitting it as
`(x y) * (x y^2)`. Its slots are still nameless, because by SEA-3 the names
come from outside:

```python
>>> candidate = found[0]
>>> candidate.m
2
>>> candidate.factors(sp.symbols("u v"))
(Fresh(polynomial=x*y, variable=u), Fresh(polynomial=x*y**2, variable=v))

```

The `EA` level is derived rather than chosen. `H` displaces the fresh
coordinates by the factors, so its filtration degree is one below the smallest
order among them:

```python
>>> candidate.filtration_level(flat)
1

```

A factor a coordinate already carries costs no dimension, so carriers are
offered as anchors whether or not the pool is empty, and a `Carried` slot is
preferred to a fresh one supplying the same factor:

```python
>>> carried = PolynomialMap((x, y), (x + x**2 * y**3, y + x**2))
>>> carried.carrier_indices
(1,)
>>> [(c.index, c.left, c.right, c.m) for c in enumerate_candidates(carried, [])]
[(0, Carried(index=1), y**3, 1)]

```

## Searching without a target

`enumerate_candidates` divides a displacement, so it needs a target. Without
one, Proposition (3.1) supplies the rule instead: take a monomial of top degree
and write it as a product of two proper parts. `untargeted_candidates` offers
those, and `docs/contracts.md` states what the family may claim under UNT-1 to
UNT-11.

```python
>>> from kellermap import untargeted_candidates, remaining_weight
>>> quintic = PolynomialMap((x, y), (x + 7 * x**3 * y**2, y))
>>> candidates = untargeted_candidates(quintic)
>>> [(candidate.index, candidate.coefficient, candidate.m) for candidate in candidates]
[(0, 7, 2), (0, 7, 2), (0, 7, 2)]

```

The coefficient is in the candidate because the two parts are monic and it has
to go somewhere. `enumerate_candidates` leaves it at one, which SEA-14 states.

`remaining_weight` is the measure that bounds such a search: the sum of
`3 ** (deg M - 3)` over the monomials of degree at least four. It is zero
exactly at degree three, which is the reduction target, and the enumerator
offers nothing there.

```python
>>> remaining_weight(quintic)
9
>>> from kellermap import examples
>>> remaining_weight(examples.bcw17())
0
>>> untargeted_candidates(examples.bcw17())
()

```

Every step has to lower it. For a step that introduces a generator that follows
from Proposition (3.1); for a step that introduces none it is a rule this
project states, and UNT-3 says which is which.

`reduce_to_degree3` walks that space. It takes a source and no target, stops where
the enumerator runs out, and reports what it saw:

```python
>>> from kellermap import LinearStep, over_field, reduce_to_degree3
>>> normalized = LinearStep.normalize(over_field(examples.alpoege())).target
>>> outcome = reduce_to_degree3(normalized, budget=2000)
>>> outcome.reduction.target.degree(), len(outcome.reduction.steps)
(3, 7)
>>> outcome.reduction.target.dimension
13
>>> outcome.exhausted
False

```

`exhausted` is `False` on a chain that was found, as it is for `search` and
`peel`: a walk that stops at the first chain did not see the space to the end.

Depth first, and the candidates are ordered by what a step removes, UNT-10.
Seven steps into dimension 13, where the chains computed by hand take eight
into 15 and eight into 17. What that shows and what it does not is on the
contract page; `scripts/reconstruct_alpoege13.py` recomputes the chain without
this library.

`untargeted_candidates` offers 22 candidates at that map, in the order its own
enumeration fixes. The order of UNT-10 is on the steps, because how much a step
removes is not known before the step exists:

```python
>>> from kellermap import remaining_weight, untargeted_candidates
>>> from kellermap.context import ReductionContext
>>> from kellermap.untargeted import ordered_steps
>>> len(untargeted_candidates(normalized))
22
>>> first = ordered_steps(normalized, ReductionContext())[0]
>>> remaining_weight(normalized) - remaining_weight(first.target)
102

```

An order discards nothing, UNT-11. Every candidate that lowers the measure is
still offered, and a different order would find a longer chain rather than
none. That is what separates ordering from pruning, and it is why the two are
separate packages.

A source that already has degree three is a non-answer, like equal endpoints
under REV-11:

```python
>>> outcome = reduce_to_degree3(examples.bcw17(), budget=5)
>>> outcome.reduction is None, outcome.examined, outcome.exhausted
(True, 0, True)

```

That is UNT-5, the base case of Proposition (3.1)'s induction: nothing to
reduce, so nothing to build. A caller who wants to tell it from a search that
found nothing asks the source for its degree, which is cheaper than the search.

---

## Assembling a chain

`search(source, target, pool)` looks for a chain of `BCWStep` from one map to
another. `pool` maps the name of a fresh generator to the value it carries in
the target; the search decides which step introduces which name.

```python
>>> from kellermap import search, conjugate
>>> u, v = sp.symbols("u v")
>>> start = over_field(PolynomialMap((x, y), (x + x**2 * y**3, y)))
>>> finish = BCWStep.build(start, 0, Fresh(x*y, u), Fresh(x*y**2, v), 1).target
>>> outcome = search(start, finish, {u: x * y, v: x * y**2})
>>> outcome.reduction.verify() is None
True
>>> outcome.reduction.target == finish
True

```

The search verifies nothing by itself. Its chain is `CONSTRUCTED` throughout,
so what carries weight is that the endpoint matches a map the library did not
compute, and that comparison is plain equality after reordering.

The pool bounds what it can reach. A target in other coordinates *is* reachable
in principle — the family of steps is closed under conjugation by a diagonal —
but the chain that reaches it carries other coefficients and other factor
values, and both come from the pool here:

```python
>>> flipped = conjugate(finish, (1, 1, 1, -1))
>>> search(start, flipped, {u: x * y, v: x * y**2}).reduction is None
True

```

Peeling solves for them instead, and reaches such a target exactly.

Finding nothing is not a proof that nothing exists, and `exhausted` says
whether even the space the search covers was seen to the end:

```python
>>> search(start, finish, {u: x * y, v: x * y**2}, budget=1).exhausted
False

```

### The coefficient ring

An exhausted space is worth what the space is worth. `over` names the
coefficient ring to search, and the outcome carries it either way:

```python
>>> from kellermap import peel
>>> search(start, finish, {u: x * y, v: x * y**2}, over=sp.QQ).domain
QQ
>>> peel(finish, finish.extend(1)).domain
QQ

```

Omitted, `over` is the ring of the source, which is what both functions used
before it existed. Given, an argument over another ring is a contradiction
rather than a narrower search, and it is reported where the call is made:

```python
>>> from kellermap import VerificationError
>>> try:
...     search(start, finish, {u: x * y, v: x * y**2}, over=sp.ZZ)
... except VerificationError as failure:
...     print(failure.obligation, "|", failure.message)
DOM-2 | the source lies over QQ, and the search was asked for ZZ

```

A pool value whose coefficients lie outside the ring is refused whether or not
`over` was named, because such a value describes nothing at all. Until 0.5 it
simply yielded no candidate:

```python
>>> integral = PolynomialMap((x, y), (x + x**2 * y**3, y))
>>> try:
...     enumerate_candidates(integral, [x * y / 2])
... except VerificationError as failure:
...     print(failure.obligation, "|", failure.message)
DOM-2 | the pool value has coefficients outside ZZ; got x*y/2

```

A value naming a coordinate the source does not have yet is a different case
and stays admissible. It is how the dependency between carriers falls out by
itself: such a value yields no candidate until a later step introduces the
coordinate.

```python
>>> z = sp.Symbol("z")
>>> enumerate_candidates(integral, [y * z])
()

```

## Peeling a chain off a target

`peel(source, target)` walks the other way. It is given the two maps and
nothing else -- no value pool, no names, no sign convention -- because a step
leaves its fresh coordinate in exactly two components, which says which
coordinates could have been introduced last.

```python
>>> from kellermap import peel
>>> outcome = peel(start, finish)
>>> outcome.reduction.verify() is None
True
>>> outcome.reduction.target == finish
True

```

What a peel produces is a structure. The chain is rebuilt forwards with
`BCWStep.build` and verified before it is a `Reduction`, and the endpoint is
compared against the target — as plain equality, because each step carries the
constant it was undone with:

```python
>>> [step.coefficient for step in outcome.reduction.steps]
[1]

```

A target in other coordinates is reached exactly too. The family of steps is
closed under conjugation by a diagonal, so a chain that reaches `D F D^-1` is
itself a chain:

```python
>>> other = peel(start, conjugate(finish, (1, 1, 1, -1))).reduction
>>> other.target == conjugate(finish, (1, 1, 1, -1))
True
>>> [step.coefficient for step in other.steps]
[-1]

```

Finding nothing means the same as it does forwards, and no more:

```python
>>> peel(start, finish, budget=1).exhausted
False

```

---

## Naming across a reduction

A reduction extends its ring many times, and the answers have to fit together.
`ReductionContext` holds a `VariableFactory` to that, and is otherwise thin: it
names generators, extends rings and maps, and knows nothing about steps.

```python
>>> from kellermap import ReductionContext
>>> context = ReductionContext()
>>> identity = PolynomialMap((x1, x2, x3), (x1, x2, x3))
>>> context.variables(identity.ring, 2)
(x4, x5)
>>> context.extend(identity, 2).variables
(x1, x2, x3, x4, x5)

```

Extending twice lands where extending once lands, with the same names:

```python
>>> context.extend(context.extend(identity, 2), 2) == context.extend(identity, 4)
True

```

Both properties a factory promises are rechecked on every call, because
neither failure raises anywhere downstream — each produces a perfectly valid
map that is simply not the one the identity needs. A factory that counts:

```python
>>> class Counting:
...     def __init__(self):
...         self.calls = 0
...     def __call__(self, ring, count):
...         self.calls += 1
...         return tuple(sp.Symbol(f"g{self.calls}_{i}") for i in range(count))
>>> ReductionContext(factory=Counting()).variables(identity.ring, 2)
Traceback (most recent call last):
    ...
ValueError: The variable factory is not a pure function of its arguments: it returned (g1_0, g1_1) and then (g2_0, g2_1).

```

And one that names its output after the size of the ring it was handed, which
is pure and never collides and still breaks `(F^[2])^[2] = F^[4]`:

```python
>>> class Sized:
...     def __call__(self, ring, count):
...         return tuple(sp.Symbol(f"g{ring.ngens}_{i}") for i in range(count))
>>> ReductionContext(factory=Sized()).variables(identity.ring, 2)
Traceback (most recent call last):
    ...
ValueError: The variable factory does not compose: allocating 2 names at once gave (g3_0, g3_1), one at a time (g3_0, g4_0).

```

`FixedVariableFactory` pins an extension to names decided elsewhere — what a
supplied certificate needs, since it records the generators it used. It answers
only one count and therefore does not compose, so it belongs in
`PolynomialMap.extend` rather than in a context.

---

## Guarantees

**Value semantics.** `PolynomialMap`, `ElementaryFactor` and
`ElementaryAutomorphism` are immutable. Nothing they hand out shares mutable
state with them.

```python
>>> before = F.displacement().components
>>> F.ring.gens[0].clear()
>>> F.to_polynomials()[0].ring.gens[0].clear()
>>> F.displacement().components == before
True

```

This costs something worth knowing: `F.ring` is a *clone* of the ring the map
computes in, not that ring. It is value-equal, so it composes, compares and
coerces interchangeably, and remains a valid argument to `from_ring()`,
`ElementaryFactor` and a factory — but it is not the same object.

```python
>>> F.ring == F.ring
True
>>> PolynomialMap.from_ring(F.ring, F.to_polynomials()) == F
True

```

`matrix` and `jacobian()` are `ImmutableMatrix`. Use `sp.Matrix(...)` for a
mutable copy.

**Equality** compares variables, coefficient domain and components, not object
identity or construction history:

```python
>>> PolynomialMap((x, y), (x + y**3, y)) == F
True

```

---

## Errors

| Situation | Raised |
| --- | --- |
| no variables, or count mismatch | `ValueError` |
| variables sharing a name | `ValueError` |
| non-polynomial component | `ValueError` |
| component from another ring | `ValueError` |
| composing maps with different variables | `ValueError` |
| a factory returning a colliding, duplicate or miscounted name | `ValueError` |
| an elementary polynomial involving its own variable | `ValueError` |
| a transvection or transposition on one coordinate | `ValueError` |
| a dilation by zero or by a non-unit | `ValueError` |
| factorizing a singular matrix, or one of the wrong shape | `ValueError` |
| a reduction with no steps, or with a non-step in it | `ValueError`, `TypeError` |
| a factory that is impure, miscounts, collides or does not compose | `ValueError` |
| a linear step changing the dimension | `ValueError` |
| a BCW step whose fresh variables share a name, or take a reserved one | `ValueError` |
| `P` or `Q` that is not a polynomial over the source's ring | `ValueError` |
| fewer than two collision points, or two equal ones | `ValueError` |
| a collision whose points and image differ in length | `ValueError` |
| an obligation of `contracts.md` failing | `VerificationError` |
| variables or components of the wrong type | `TypeError` |
| a source or target of a search that is not a `PolynomialMap` | `TypeError` |
| a value pool that is not a mapping, or a pool name that is not a symbol | `TypeError` |
| pool names sharing a name, or taking one reserved by the source's ring | `ValueError` |
| a source, target or pool value over a ring other than `over` | `VerificationError` |

The last four are checked before anything else a search does, so that they do
not depend on whether REV-11 answers the pair from its endpoints.

```python
>>> PolynomialMap((x, y), (sp.sin(x), y))
Traceback (most recent call last):
    ...
ValueError: Components must be polynomials in the specified variables.

>>> ElementaryFactor(R, 0, X1 * X2)
Traceback (most recent call last):
    ...
ValueError: The polynomial must not involve X1; otherwise the factor is not invertible by the elementary formula.

```
