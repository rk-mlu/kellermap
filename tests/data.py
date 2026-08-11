"""Feste Eingabe, die dieses Projekt nicht ausliefert.

Die neunzehndimensionale Abbildung ist fremde Mathematik, und eine Lizenz dazu
liess sich nicht ermitteln. ``AGENTS.md`` verlangt, solche Daten nicht ins Paket
zu uebernehmen, also stehen sie hier und nicht in ``kellermap.examples``.

Das ist zugleich die Abbildung, an der das Ergebnis von Meilenstein 0.4 haengt:
sie ist das einzige Datum, gegen das eine gefundene Kette geprueft wird und das
dieses Projekt nicht selbst gerechnet hat. Dass sie ausserhalb des
ausgelieferten Pakets liegt, macht diese Aeusserlichkeit sichtbar, statt sie
einem Leser als Verzeichnisfrage zu ueberlassen.

Herkunft und was die Uebereinstimmung belegt: ``docs/references.md``.

Reine SymPy-Konstanten, ohne ``kellermap``. Der Grund steht in
``scripts/reconstruct_alpoege19.py``: dieses Skript rechnet die Reduktion
unabhaengig von der Bibliothek nach und liest die Zielabbildung von hier. Baute
dieses Modul die ``PolynomialMap``, so ginge die Konversion der Daten durch
genau den Code, gegen den geprueft werden soll. Die ``PolynomialMap`` entsteht
im Testmodul. Ein externes Audit hat darauf hingewiesen.
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
