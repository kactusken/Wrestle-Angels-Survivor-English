"""Menu sheets with a glowing label on a translucent gradient panel and a white highlight copy
(A00A_p0_0, A00A_p1_0: the office and gym command menus).

panel() is letter.draw_group() with one change for 'interpolate' groups: instead of each row being
rebuilt from the pixels left and right of the box (which smears the panel's diagonal gloss into
blocks, and snaps to the wrong translucency), the areas in spec 'heal' ([[x, y, w, h], ...]) are
healed once before lettering:

  - the panel's ground is every pixel whose alpha is 'ground_alpha' (default 204: the panel is one
    translucency; letters, outlines, glows, the side bar and the rim all have other alphas);
  - inside each area, every non-ground pixel, grown by 'grow' px (default 2, for the faint glow
    fringe), is unknown; unknown pixels are filled smoothly from the ground around them (a Laplace
    fill started from row and column interpolation), so the gloss and gradient continue under the
    old labels;
  - the result snaps to the nearest ground-alpha palette entry.

letter.clear is then a no-op for that group (the healed areas are already clean), so 'clear' and
the boxes are not cleared again. Groups with another ground ('transparent' highlight copies) are
plain letter.draw_group().
"""
import letter

ITERATIONS = 250


def heal(out, pal, rect, ground_alpha=204, grow=2):
    x, y, w, h = rect
    px = out.load()
    ground = [i for i, p in enumerate(pal) if p[3] == ground_alpha]
    hole = {(i, j) for j in range(y, y + h) for i in range(x, x + w) if pal[px[i, j]][3] != ground_alpha}
    for _ in range(grow):
        hole |= {(i + di, j + dj) for i, j in hole for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1))
                 if x <= i + di < x + w and y <= j + dj < y + h}
    val = {}
    for j in range(y - 1, y + h + 1):
        for i in range(x - 1, x + w + 1):
            if 0 <= i < out.width and 0 <= j < out.height and (i, j) not in hole \
                    and pal[px[i, j]][3] == ground_alpha:
                val[i, j] = pal[px[i, j]][:3]

    def interp(points, at):
        """Linear interpolation along one line of known (position, colour) pairs."""
        if not points:
            return None
        lo = [p for p in points if p[0] < at]
        hi = [p for p in points if p[0] > at]
        if lo and hi:
            (a, ca), (b, cb) = lo[-1], hi[0]
            t = (at - a) / (b - a)
            return [ca[k] + (cb[k] - ca[k]) * t for k in range(3)]
        return list((lo[-1] if lo else hi[0])[1])

    rows = {j: [(i, val[i, j]) for i in range(x - 1, x + w + 1) if (i, j) in val] for j in range(y, y + h)}
    cols = {i: [(j, val[i, j]) for j in range(y - 1, y + h + 1) if (i, j) in val] for i in range(x, x + w)}
    cur = {}
    for i, j in hole:
        a, b = interp(rows[j], i), interp(cols[i], j)
        got = [v for v in (a, b) if v is not None] or [[0, 0, 0]]
        cur[i, j] = [sum(v[k] for v in got) / len(got) for k in range(3)]
    order = sorted(hole, key=lambda t: (t[1], t[0]))
    for _ in range(ITERATIONS):
        for i, j in order:
            nb = [cur.get(k) or val.get(k) for k in ((i - 1, j), (i + 1, j), (i, j - 1), (i, j + 1))]
            nb = [v for v in nb if v is not None]
            if nb:
                cur[i, j] = [sum(v[k] for v in nb) / len(nb) for k in range(3)]
    cache = {}
    for (i, j), c in cur.items():
        key = tuple(round(v) for v in c)
        if key not in cache:
            cache[key] = min(ground, key=lambda g: sum((pal[g][k] - key[k]) ** 2 for k in range(3)))
        px[i, j] = cache[key]


def panel(name, im, out, pal, texts, boxes, spec):
    if spec.get('ground') != 'interpolate' or 'heal' not in spec:
        return letter.draw_group(name, im, out, pal, texts, boxes, spec)
    for rect in spec['heal']:
        heal(out, pal, rect, spec.get('ground_alpha', 204), spec.get('grow', 2))
    saved = letter.clear
    letter.clear = lambda *a, **k: None
    try:
        return letter.draw_group(name, im, out, pal, texts, boxes, spec)
    finally:
        letter.clear = saved
