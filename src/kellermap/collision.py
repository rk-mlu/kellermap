"""Collisions: the evidence that a polynomial map is not injective.

A collision is several distinct points sharing one image. For a Keller map it
is the whole point of the exercise, and it is the cheapest object in the
project to check: evaluation, no polynomial arithmetic, no ring.

The type exists so that a reduction can *carry* one. A degree reduction that
loses the counterexample it started from has reduced the wrong thing, and
``Step.transport`` in version 0.2 moves a collision from a map to its
successor. That the collision then still holds is verified, never assumed.

See ``docs/contracts.md`` for the obligations ``verify`` checks.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

import sympy as sp

from .canonical import agree, canonical
from .errors import VerificationError
from .polynomial_map import PolynomialMap

# A point of affine space, coordinate by coordinate as a SymPy expression.
# Expressions and not numbers, because over k(T) a parameter may appear as
# well. What a point must not contain are the variables of the map itself.
Point = tuple[sp.Expr, ...]


@dataclass(frozen=True, eq=False)
class Collision:
    """Distinct points of ``k^n`` together with their common image.

    Parameters
    ----------
    points
        At least two points, pairwise distinct, all of the same length.
    image
        The point they are all claimed to map to.

    Distinctness is a constructor invariant rather than an obligation of
    ``verify``: a ``Collision`` whose points coincide is not a weaker
    certificate but a meaningless one, and refusing to build it is stronger
    than reporting it later. What ``verify`` checks is everything that
    involves a map, since a collision is stated against one map and carried to
    another.

    The class holds no map. The same points are a collision of every map that
    identifies them, and a reduction verifies them against several in turn.
    """

    _points: tuple[Point, ...]
    _image: Point

    def __init__(
        self,
        points: Iterable[Iterable[sp.Expr]],
        image: Iterable[sp.Expr],
    ) -> None:
        collected = tuple(_coerce_point(point) for point in points)
        target = _coerce_point(image)

        if len(collected) < 2:
            raise ValueError(
                f"A collision needs at least two points; got {len(collected)}."
            )

        dimensions = {len(point) for point in collected} | {len(target)}
        if len(dimensions) != 1:
            raise ValueError(
                "All points and the image must have the same number of "
                f"coordinates; got {sorted(dimensions)}."
            )

        if not target:
            raise ValueError("A collision needs at least one coordinate.")

        _reject_repeated_points(collected)

        object.__setattr__(self, "_points", collected)
        object.__setattr__(self, "_image", target)

    @classmethod
    def at(
        cls,
        F: PolynomialMap,
        points: Iterable[Iterable[sp.Expr]],  # noqa: N803
    ) -> Collision:
        """Build a collision of ``F`` by evaluating it at the first point.

        Convenient where the image is a consequence rather than a claim. The
        result is verified against ``F`` before it is returned, so this cannot
        manufacture a collision out of points that do not collide.
        """
        collected = tuple(_coerce_point(point) for point in points)
        if not collected:
            raise ValueError("A collision needs at least two points; got none.")

        image = tuple(F(*collected[0]))
        collision = cls(collected, image)
        collision.verify(F)

        return collision

    @property
    def points(self) -> tuple[Point, ...]:
        """Return the colliding points, in the order they were given."""
        return self._points

    @property
    def image(self) -> Point:
        """Return the common image."""
        return self._image

    @property
    def dimension(self) -> int:
        """Return the number of coordinates of each point."""
        return len(self._image)

    def verify(self, F: PolynomialMap) -> None:  # noqa: N803
        """Check that this is a collision of ``F``, or raise.

        Obligations, in the numbering of ``docs/contracts.md``:

        - ``COL-1`` the dimensions agree,
        - ``COL-2`` no coordinate involves a variable of ``F``,
        - ``COL-3`` ``F`` sends every point to the recorded image.

        ``COL-2`` is not pedantry. A coordinate carrying one of the map's own
        variables would be substituted into itself by the evaluation, and the
        resulting identity would say nothing about any point at all.
        """
        if self.dimension != F.dimension:
            raise VerificationError(
                "COL-1",
                f"The collision has dimension {self.dimension}, "
                f"the map has dimension {F.dimension}.",
            )

        variables = set(F.variables)
        for position, point in enumerate(self._points):
            clashes = {
                symbol.name
                for coordinate in point
                for symbol in coordinate.free_symbols
            } & {symbol.name for symbol in variables}
            if clashes:
                raise VerificationError(
                    "COL-2",
                    f"Point {position} involves the variables "
                    f"{sorted(clashes)} of the map.",
                )

        for position, point in enumerate(self._points):
            value = F(*point)
            deviating = [
                index
                for index, (left, right) in enumerate(
                    zip(value, self._image, strict=True)
                )
                if not agree(left, right)
            ]
            if deviating:
                raise VerificationError(
                    "COL-3",
                    f"The map sends point {position} to {tuple(value)}, "
                    f"not to {self._image}; coordinates {deviating} differ.",
                )

    def extended(
        self,
        coordinates: Iterable[Iterable[sp.Expr]],
        image: Iterable[sp.Expr],
    ) -> Collision:
        """Return the collision with coordinates appended to every point.

        This is what a stabilizing step needs: the points gain the fresh
        coordinates the step introduces, and the image gains its own. One
        entry of ``coordinates`` per point, in the order of ``points``.
        """
        appended = tuple(_coerce_point(entry) for entry in coordinates)
        target = _coerce_point(image)

        if len(appended) != len(self._points):
            raise ValueError(
                f"Expected coordinates for {len(self._points)} points, "
                f"got {len(appended)}."
            )

        widths = {len(entry) for entry in appended} | {len(target)}
        if len(widths) != 1:
            raise ValueError(
                "Every point and the image must gain the same number of "
                f"coordinates; got {sorted(widths)}."
            )

        return Collision(
            tuple(
                point + entry
                for point, entry in zip(self._points, appended, strict=True)
            ),
            self._image + target,
        )

    def with_image(self, image: Iterable[sp.Expr]) -> Collision:
        """Return the collision with a different image and the same points.

        A map composed on the left moves the image and leaves every preimage
        where it was. That is the whole effect of the linear normalization of
        BCW Chapter II, Proposition (1.1) on a collision.
        """
        return Collision(self._points, image)

    def __len__(self) -> int:
        """Return the number of colliding points."""
        return len(self._points)

    def __eq__(self, other: object) -> bool:
        """Compare as a set of points plus an image.

        A collision is a set: listing the same points in another order is the
        same certificate.

        Coordinates were put into normal form on the way in, so ``==`` decides
        this soundly and agrees with ``__hash__``. Canonicalizing at
        construction rather than comparing canonically here is what makes the
        two consistent: equal objects must hash equal, and
        ``(T**2 - 1)/(T - 1)`` and ``T + 1`` do not.

        Normal form is not conversion. ``Rational(1, 4)`` and ``Float(0.25)``
        remain different objects here, as they are everywhere else in SymPy.
        """
        if not isinstance(other, Collision):
            return NotImplemented

        return (
            frozenset(self._points) == frozenset(other._points)
            and self._image == other._image
        )

    def __hash__(self) -> int:
        return hash((frozenset(self._points), self._image))

    def __repr__(self) -> str:
        return f"Collision(points={self._points}, image={self._image})"


def _coerce_point(point: Iterable[sp.Expr]) -> Point:
    """Sympify a point and put every coordinate into normal form.

    Normalizing here rather than at each comparison is deliberate. It gives
    the class one representation to store, which is what lets ``__eq__`` and
    ``__hash__`` agree; comparing canonically while storing whatever arrived
    would leave equal collisions hashing differently.
    """
    if isinstance(point, sp.Basic) or isinstance(point, str):
        raise TypeError(
            f"A point must be an iterable of coordinates, not {type(point).__name__}."
        )

    coordinates: list[sp.Expr] = []
    for coordinate in point:
        try:
            value = sp.sympify(coordinate)
        except (sp.SympifyError, TypeError) as error:
            raise TypeError(
                f"Coordinate {coordinate!r} is not a SymPy expression."
            ) from error

        if not isinstance(value, sp.Expr):
            raise TypeError(f"Coordinate {coordinate!r} is not a SymPy expression.")

        coordinates.append(canonical(value))

    return tuple(coordinates)


def _reject_repeated_points(points: tuple[Point, ...]) -> None:
    """Raise if two points are equal as values.

    Compared coordinate by coordinate and by value rather than by tuple
    equality: two points may be written differently and still be the same
    point, and a collision of a map with itself proves nothing. Over ``k(T)``
    the difference bites -- ``(T**2 - 1)/(T - 1)`` and ``T + 1`` are one point.
    """
    for left in range(len(points)):
        for right in range(left + 1, len(points)):
            if all(
                agree(a, b) for a, b in zip(points[left], points[right], strict=True)
            ):
                raise ValueError(
                    f"Points {left} and {right} are equal; a collision needs "
                    "distinct points."
                )
