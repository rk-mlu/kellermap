"""Fixed input that this project does not distribute.

The nineteen-dimensional map is mathematics from another source, and a licence
for it could not be established. ``AGENTS.md`` requires that such data is not
taken into the package, so it stands here and not in ``kellermap.examples``.

It is also the map the result of milestone 0.4 rests on. It is the only datum a
found chain is checked against that this project did not compute itself. Its
place outside the distributed package makes that externality visible, rather
than leaving it to a reader as a question about directories.

Provenance, and what the agreement establishes: ``docs/references.md``.

Plain SymPy constants, without ``kellermap``. The reason stands in
``scripts/reconstruct_alpoege19.py``. That script recomputes the reduction
independently of the library and reads the target map from here. If this module
built the ``PolynomialMap``, the conversion of the data would run through
exactly the code that is to be checked. The ``PolynomialMap`` is built in the
test module. An external audit pointed this out.
"""

import sympy as sp

x, y, z = sp.symbols("x y z")

w = sp.symbols("w1:17")

w1, w2, w3, w4, w5, w6, w7, w8, w9, w10, w11, w12, w13, w14, w15, w16 = w

VARIABLES = (x, y, z) + w

COMPONENTS = (
    x * w1 * w5
    + 3 * x * w4 * w9
    - x * w6 * w9
    + 6 * x * y * w11
    - x * y * w12
    - 7 * x * y * w7
    + 3 * x * y * w8
    + 3 * x * y * z
    + 6 * y * w3 * w9
    - 3 * y * z * w5
    + y**2 * w10
    - 7 * y**2 * w9
    + z * w2 * w7
    - w1 * w2
    - 3 * w3**2
    - 3 * w4 * w5
    + w5 * w6
    + w7 * w10
    - 7 * w7 * w9
    + 3 * w8 * w9
    + 6 * w9 * w11
    - w9 * w12
    + 4 * y**2
    + z,
    3 * x * w4 * w5
    + 12 * x * y**2
    + 9 * x**2 * w14
    - 3 * x**2 * w15
    - 6 * x**2 * w4
    + 9 * y * w7 * w13
    - 3 * y * w8 * w13
    - 6 * y * z * w13
    - 3 * y * z * w2
    - 9 * y**2 * w5
    + 9 * w13 * w14
    - 3 * w13 * w15
    - 3 * w2 * w4
    - 6 * w4 * w13
    - 9 * w5 * w7
    + 3 * w5 * w8
    + 3 * x * z
    + y,
    x * z * w13 + x**2 * w16 - 3 * x**2 * y + w13 * w16 + 2 * x,
    y**2 * z + w1,
    -x * y * w13 - x**2 * w9 - w9 * w13 + w2,
    x * y**2 + w3,
    y * z + w4,
    x**2 * y + w5,
    x * w1 + w6,
    y**2 + w7,
    x * w4 + w8,
    x * y + w9,
    z * w2 + w10,
    y * w3 + w11,
    x * w6 + w12,
    x**2 + w13,
    y * w7 + w14,
    y * w8 + w15,
    x * z + w16,
)


R = sp.Rational

PUBLISHED_POINTS = (
    (0, 0, R(-1, 4)) + (0,) * 16,
    (
        1,
        R(-3, 2),
        R(13, 2),
        R(-117, 8),
        R(3, 2),
        R(-9, 4),
        R(39, 4),
        R(3, 2),
        R(117, 8),
        R(-9, 4),
        R(-39, 4),
        R(3, 2),
        R(-39, 4),
        R(-27, 8),
        R(-117, 8),
        -1,
        R(-27, 8),
        R(-117, 8),
        R(-13, 2),
    ),
    (
        -1,
        R(3, 2),
        R(13, 2),
        R(-117, 8),
        R(3, 2),
        R(9, 4),
        R(-39, 4),
        R(-3, 2),
        R(-117, 8),
        R(-9, 4),
        R(-39, 4),
        R(3, 2),
        R(-39, 4),
        R(-27, 8),
        R(-117, 8),
        -1,
        R(27, 8),
        R(117, 8),
        R(13, 2),
    ),
)

ALPOEGE_POINTS = (
    (0, 0, R(-1, 4)),
    (1, R(-3, 2), R(13, 2)),
    (-1, R(3, 2), R(13, 2)),
)

ALPOEGE_IMAGE = (R(-1, 4), 0, 0)

CARRIERS = {w[j]: sp.expand(COMPONENTS[3 + j] - w[j]) for j in range(16)}

W2_INTRODUCED = x**3 * y


# --------------------------------------------------------------------------
# macfarlane13
#
# A. Macfarlane, https://github.com/Amacfa/keller-counterexamples-13-20,
# timestamped 22 July 2026. Thirteen variables, degree three, determinant one,
# and a two-point collision. Obtained by restricting W. Thompson's
# twenty-four-variable cubic-homogeneous form to an invariant subspace, which
# is a construction this project does not have.
#
# Here for the same reason as the nineteen-dimensional map above: the
# repository carries no licence, so the values are not taken into the package.
# ``docs/references.md`` records what was recomputed from them and what the
# agreement establishes.
#
# It is not the same map as ``kellermap.examples.alpoege13``, which has 58
# terms and a three-point collision. It is reachable by the same kind of chain:
# ``scripts/reconstruct_macfarlane13.py`` carries seven BCW steps from
# Alpoege's normalized map that arrive at it exactly.
# --------------------------------------------------------------------------

m = sp.symbols("m1:14")

MACFARLANE_VARIABLES = m

_R = (
    -m[10] * m[11],
    3 * m[0] * m[2] - m[7] * m[8] - 3 * m[4] * m[5],
    -m[7] * m[9] + 4 * m[1] ** 2 - m[3] * m[4] - m[5] * m[6],
    2 * m[11] * m[12],
    3 * m[1] ** 2,
    sp.Integer(0),
    3 * m[1] * m[2] - m[1] * m[4],
    m[0] * m[1],
    6 * m[0] * m[2] - 3 * m[0] * m[4] - 3 * m[2] * m[5],
    -m[0] * m[6] + 7 * m[1] ** 2 - m[2] * m[3],
    m[0] * m[2],
    -R(1, 2) * m[0] ** 2,
    m[1] ** 2,
)

_GAMMA = (
    -2 * m[0] * m[2] * m[7]
    + m[0] * m[4] * m[7]
    - R(1, 3) * m[0] * m[1] * m[8]
    + 4 * m[0] * m[1] ** 2
    + m[2] * m[5] * m[7]
    - 3 * m[1] ** 2 * m[5],
    m[0] * m[6] * m[7]
    - m[0] * m[1] * m[9]
    - 7 * m[1] ** 2 * m[7]
    + m[2] * m[3] * m[7]
    - 3 * m[1] ** 2 * m[3]
    - 3 * m[1] * m[2] * m[5]
    + m[1] * m[4] * m[5],
    m[0] ** 2 * m[12] - 2 * m[11] * m[1] ** 2,
    -R(1, 2) * m[0] ** 2 * m[10] + m[0] * m[11] * m[2],
    m[0] * m[1] * m[2],
    m[0] ** 2 * m[1],
)

# B: Q^6 -> Q^13, linear, as the source prints it.
_B = (
    -_GAMMA[3] - R(3, 2) * _GAMMA[5],
    3 * _GAMMA[0],
    _GAMMA[1] + 3 * _GAMMA[4],
    -_GAMMA[2],
    _GAMMA[4],
    _GAMMA[5],
) + (sp.Integer(0),) * 7

MACFARLANE_COMPONENTS = tuple(sp.expand(m[i] + _R[i] + _B[i]) for i in range(13))

MACFARLANE_POINTS = (
    (0, 0, R(-1, 4), 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
    (
        1,
        R(-3, 2),
        R(13, 2),
        R(-9, 4),
        3,
        R(3, 2),
        R(99, 4),
        R(3, 2),
        R(-3, 4),
        R(-45, 8),
        R(-13, 2),
        R(1, 2),
        R(-9, 4),
    ),
)

MACFARLANE_IMAGE = (0, 0, R(-1, 4), 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)

# A third preimage, and it is this project's and not his.
#
# His two points come from the repository above. This one comes from carrying
# Alpoege's collision through the seven-step chain that reaches his map, so it
# is external to the library and internal to the project, which
# ``AGENTS.md`` asks to be kept apart.
#
# The transport also reproduces his two, coordinate for coordinate, which is
# the check ``scripts/reconstruct_macfarlane13.py`` makes. His derivation
# restricts Thompson's twenty-four-variable form, and what arrives there is
# what Thompson carried: two points. Alpoege's map has three, and the chain
# brings all three.
MACFARLANE_THIRD_POINT = (
    -1,
    R(3, 2),
    R(13, 2),
    R(-9, 4),
    3,
    R(-3, 2),
    R(-99, 4),
    R(3, 2),
    R(3, 4),
    R(-45, 8),
    R(13, 2),
    R(1, 2),
    R(-9, 4),
)
