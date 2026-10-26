"""Move-list panels and the card/tag icon sheet (A00B, A01D): status.py's ground patches, then
system.py's layered lettering.

draw() is a letter.py drawer ("draw": "movelist.draw"). Before calling system.draw (use
"ground": "keep") it rebuilds the ground under the old lettering, in this order:
  tag_model  {"tags", "expr", "grow", "all"}: green tags with a cyan border (see tag_model())
  ovals      one-colour badges flattened (see flatten_ovals())
  patches    status.py's format and modes ("inpaint" with an "expr": a Laplace fill; "fill")
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import status  # noqa: E402
import system  # noqa: E402
letter = status.letter


def flatten_ovals(out, pal, ovals):
    """Flat round badges (a kanji on a one-colour oval): `ovals` [[x, y, w, h], ...] are the
    badges' cells, with optional "margin" (px kept at each end of a row, default 2), "top" and
    "bottom" (rows left alone) and "index" (the oval's index; default the cell's commonest
    opaque one). Inside the oval (each row's run of opaque pixels, less the margin) every pixel
    becomes the oval's index."""
    from collections import Counter
    px = out.load()
    for o in ovals:
        o = o if isinstance(o, dict) else {'rect': o}
        x, y, w, h = o['rect']
        m = o.get('margin', 2)
        idx = o.get('index')
        if idx is None:
            idx = Counter(px[i, j] for j in range(y, y + h) for i in range(x, x + w)
                          if pal[px[i, j]][3] >= 250).most_common(1)[0][0]
        for j in range(y + o.get('top', 2), y + h - o.get('bottom', 2)):
            run = [i for i in range(x, x + w) if pal[px[i, j]][3] > 128]
            if run:
                for i in range(run[0] + m, run[-1] - m + 1):
                    px[i, j] = idx


def tag_model(out, pal, opts):
    """Vignetted tags of one piece of art (dark in the middle, glowing towards the border): every
    tag's ground is the same function of (distance to the nearer side, row). opts: "tags"
    [[x, y, w, h], ...] the tags' insides (the same height), "expr" the ground test (status.py's
    panel_test), "grow" px of ground next to the lettering also treated as lettering, "all" repaint
    every pixel (not only the lettering's). The model is the median colour of the clean ground
    pixels of all the tags at each (distance, row); a key without one takes the nearest distance
    in its row."""
    px = out.load()
    test = status.panel_test(pal, opts)
    grow = opts.get('grow', 1)
    samples, bad_of = {}, []
    for x, y, w, h in opts['tags']:
        bad = {(i, j) for j in range(y, y + h) for i in range(x, x + w) if not test(px[i, j])}
        for _ in range(grow):
            bad |= {(i + a, j + b) for i, j in bad for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1))}
        bad_of.append(bad)
        for j in range(y, y + h):
            for i in range(x, x + w):
                if (i, j) not in bad:
                    samples.setdefault((min(i - x, x + w - 1 - i), j - y), []).append(pal[px[i, j]][:3])
    model = {k: tuple(sorted(c[n] for c in v)[len(v) // 2] for n in range(3)) for k, v in samples.items()}
    cache = {}

    def colour(d, r):
        if (d, r) in model:
            return model[d, r]
        row = [k for k in model if k[1] == r] or list(model)
        k = min(row, key=lambda k: (abs(k[0] - d) + 3 * abs(k[1] - r), -k[0]))
        return model[k]
    for (x, y, w, h), bad in zip(opts['tags'], bad_of):
        for j in range(y, y + h):
            for i in range(x, x + w):
                if opts.get('all') or (i, j) in bad:
                    rgb = colour(min(i - x, x + w - 1 - i), j - y)
                    if rgb not in cache:
                        cache[rgb] = letter.nearest(pal, rgb + (255,), len(pal))
                    px[i, j] = cache[rgb]


def draw(name, im, out, pal, texts, boxes, spec):
    if 'tag_model' in spec:
        tag_model(out, pal, spec['tag_model'])
    flatten_ovals(out, pal, spec.get('ovals', []))
    status.patch(out, pal, spec.get('patches', []))
    return system.draw(name, im, out, pal, texts, boxes, spec)
