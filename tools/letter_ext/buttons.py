"""Green column-head buttons (the list panels of A00B, A00C, A00D, A010, A025): a clean button
ground rebuilt from a model of the art, then system.py's layered lettering.

draw() is a letter.py drawer ("draw": "buttons.draw"). The buttons are one piece of art: a 1 px
cyan frame round a vignetted inside - teal at the sides, yellow-green in the middle, lighter in the
top and bottom rows - with the lettering's dark-green glow over it. Spec keys, besides system.py's
(use "ground": "keep"):

  buttons   [[x, y, w, h], ...] the frames (54 x 24 with the cyan border, which is kept): their insides are repainted
  model     original pictures (names in review/images-original) whose 54 x 24 buttons are sampled,
            besides this one (more buttons: more clean ground between the glyphs)
  grow      px next to the lettering not sampled (default 2: the glow)
  dither    levels of 4x4 ordered dither when the model is snapped to the palette (default 12)

Every inside pixel becomes the model's colour at (distance to the nearer side, row): the median of
the clean pixels sampled there; keys with too few samples (the middle, under the lettering) are
filled by Laplace interpolation from the rest, so the middle blends smoothly into the sides.
"""
import sys
from collections import defaultdict, deque
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import system  # noqa: E402
letter = system.letter

FRAME = (54, 24)
MIN_SAMPLES = 3


def _ground(c):
    r, g, b = c[:3]
    return g - r > 40 and g >= b - 15


def _frames(rgb):
    """The 54 x 24 cyan button frames in the top rows of an RGB picture."""
    px = rgb.load()
    w, h = rgb.width, min(rgb.height, 80)
    cyan = lambda c: c[1] > 150 and c[2] > 150 and c[0] < 140
    seen, out = set(), []
    for y in range(h):
        for x in range(w):
            if (x, y) in seen or not cyan(px[x, y]):
                continue
            q, xs, ys = deque([(x, y)]), [], []
            seen.add((x, y))
            while q:
                a, b = q.popleft()
                xs.append(a)
                ys.append(b)
                for c, d in ((a + 1, b), (a - 1, b), (a, b + 1), (a, b - 1)):
                    if 0 <= c < w and 0 <= d < h and (c, d) not in seen and cyan(px[c, d]):
                        seen.add((c, d))
                        q.append((c, d))
            box = (min(xs), min(ys), max(xs) - min(xs) + 1, max(ys) - min(ys) + 1)
            if box[2:] == FRAME:
                out.append(box)
    return out


def _sample(rgb, frames, grow, samples):
    px = rgb.load()
    for fx, fy, fw, fh in frames:
        x, y, w, h = fx + 1, fy + 1, fw - 2, fh - 2
        bad = {(i, j) for j in range(y, y + h) for i in range(x, x + w) if not _ground(px[i, j])}
        for _ in range(grow):
            bad |= {(i + a, j + b) for i, j in bad for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1))}
        for j in range(y, y + h):
            for i in range(x, x + w):
                if (i, j) not in bad:
                    samples[min(i - x, x + w - 1 - i), j - y].append(px[i, j][:3])


def model(names, grow):
    """{(distance, row): (r, g, b)} for the inside of a 54 x 24 button."""
    samples = defaultdict(list)
    for name in names:
        rgb = Image.open(letter.paths.ORIGINAL_IMAGES / f'{name}.png').convert('RGB')
        _sample(rgb, _frames(rgb), grow, samples)
    iw, ih = FRAME[0] - 2, FRAME[1] - 2
    keys = [(d, r) for d in range((iw + 1) // 2) for r in range(ih)]
    val = {}
    for k in keys:
        v = samples.get(k, [])
        if len(v) >= MIN_SAMPLES:
            val[k] = [sorted(c[n] for c in v)[len(v) // 2] for n in range(3)]
    fixed = set(val)
    if not fixed:
        raise SystemExit('buttons: no clean button ground sampled')
    mean = [sum(v[n] for v in val.values()) / len(val) for n in range(3)]
    for k in keys:
        val.setdefault(k, mean[:])
    dmax = (iw + 1) // 2 - 1
    for _ in range(600):        # Laplace: each free key the mean of its neighbours
        for d, r in keys:
            if (d, r) in fixed:
                continue
            nb = [(d + a, r + b) for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1))]
            nb = [(min(dd, dmax), rr) for dd, rr in nb]     # past the middle: its mirror image
            nb = [k for k in nb if k in val]
            val[d, r] = [sum(val[k][n] for k in nb) / len(nb) for n in range(3)]
    return val


def repaint(out, pal, frames, val, amp):
    px = out.load()
    dmax = max(d for d, _ in val)
    rmax = max(r for _, r in val)
    cache = {}
    for fx, fy, fw, fh in frames:
        x, y, w, h = fx + 1, fy + 1, fw - 2, fh - 2
        for j in range(y, y + h):
            for i in range(x, x + w):
                d = min(i - x, x + w - 1 - i, dmax)
                r = max(0, min(rmax, j - y))
                t = (system.BAYER[j % 4][i % 4] + 0.5) / 16 - 0.5
                rgb = tuple(max(0, min(255, round(c + t * amp))) for c in val[d, r])
                if rgb not in cache:
                    cache[rgb] = letter.nearest(pal, rgb + (255,), len(pal))
                px[i, j] = cache[rgb]


def draw(name, im, out, pal, texts, boxes, spec):
    val = model([name] + [n for n in spec.get('model', []) if n != name], spec.get('grow', 2))
    repaint(out, pal, spec['buttons'], val, spec.get('dither', 12))
    return system.draw(name, im, out, pal, texts, boxes, spec)
