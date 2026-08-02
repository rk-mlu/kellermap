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
- [Collisions](#collisions)
- [Guarantees](#guarantees)
- [Errors](#errors)

---

## Public surface

```python
>>> import kellermap
>>> kellermap.__all__
['DEFAULT_VARIABLE_FACTORY', 'Collision', 'ElementaryAutomorphism', 'ElementaryFactor', 'IndexedVariableFactory', 'PolynomialMap', 'VariableFactory', 'VerificationError', 'reserved_names']

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
