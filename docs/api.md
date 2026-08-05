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
  - [Stable extension](#stable-extension)
- [Variable factories](#variable-factories)
- [Elementary automorphisms](#elementary-automorphisms)
- [Linear automorphisms](#linear-automorphisms)
- [Collisions](#collisions)
- [Steps and reductions](#steps-and-reductions)
- [The BCW step](#the-bcw-step)
- [Naming across a reduction](#naming-across-a-reduction)
- [Guarantees](#guarantees)
- [Errors](#errors)

---

## Public surface

```python
>>> import kellermap
>>> kellermap.__all__
['DEFAULT_VARIABLE_FACTORY', 'Collision', 'Dilation', 'ElementaryAutomorphism', 'ElementaryFactor', 'FixedVariableFactory', 'IndexedVariableFactory', 'LinearAutomorphism', 'LinearFactor', 'LinearStep', 'PolynomialMap', 'Provenance', 'Reduction', 'ReductionContext', 'Step', 'Transposition', 'Transvection', 'VariableFactory', 'VerificationError', 'field_ring', 'over_field', 'reserved_names']

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

`G` and `H` are derived from the index, the two factors and the two fresh
variables. They are never supplied alongside them, because two ways to say the
storing both would allow the two to disagree:

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
