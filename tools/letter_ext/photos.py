"""Lettering on painted pictures (spec "draw": "photos.draw"): event photo banners (A00E) and the
awards backdrop (A009_p12_0), where the Japanese sits on a shaded ground (a stamp, a sheet of paper,
a slip, a sign, a halftone stripe) at an angle.

  1. erase: each entry {'poly': [[x, y], ...], 'ink': 'expr of r, g, b'} marks the pixels inside
     the polygon whose colour makes `ink` true; 'close' fills holes up to that size (dots inside a
     letter), 'grow' widens the mask by n px (the soft edge). The marked pixels are rebuilt:
       'fill': 'diffuse'   from the pixels around them (smooth grounds)
       'fill': 'lattice'   a halftone screen: diffused, plus the dots of the nearest unmarked
                           pixel one step of 'lattice' (two vectors) away, preferring vertical
                           steps; 'screen_x': columns left of it are only diffused
  2. text: each label is drawn in its box [x, y, w, h] (the unrotated frame: the text is fitted to
     w x h and centred), then turned by 'angle' degrees (counter-clockwise, as PIL) about the box
     centre. Keys: font, cap (capital height, px), shear (lean, x per y), tracking (px), 'lines'
     (labels split at '/' into lines, line gap 'leading' x cap), 'axes' [u, v] (instead of an
     angle: the picture directions of the text's x and of its y downwards, for lettering on a
     surface seen at a slant), 'colour' [r, g, b] or 'screen'
     (each letter pixel copies an original letter pixel one lattice step away: the original's
     halftone dots), 'blur' (px, softens the edge like the painted original), 'rough' (brush:
     the edge is eaten and grown by a fixed noise), 'shadow' {'offset': [dx, dy], 'colour', 'alpha'}.
     Edges are blended with the rebuilt ground and snapped to the palette, so the picture keeps it.

'paint': [{'rect': [x, y, w, h], 'from': [x, y]}] fills areas with one original pixel's index (a
flat sign), after erasing and before the text.

Per-label settings: spec 'labels': [{...}, ...] overrides the spec's keys for that label.
"""
import math
import random

from PIL import Image, ImageDraw, ImageFilter, ImageFont

import letter
from banners import Snap

SUPER = 4


def draw(name, im, out, pal, texts, boxes, spec):
    W, H = im.size
    src = im.load()
    rgb = {}
    for y in range(H):
        for x in range(W):
            rgb[x, y] = list(pal[src[x, y]][:3])
    erased, smooth = set(), set()
    for e in spec.get('erase', []):
        mask = _mask(im, pal, e)
        if e.get('fill', 'diffuse') == 'lattice':
            _lattice(rgb, mask, e['lattice'], W, H, e.get('reach', 12), e.get('screen_x', 0))
        else:
            smooth |= mask          # diffused together: one area's edge mustn't feed another
        erased |= mask
    _diffuse(rgb, smooth, W, H)
    snap = Snap(pal)
    opx = out.load()
    for p in erased:
        opx[p] = snap(tuple(rgb[p]) + (255,))
    for r in spec.get('paint', []):       # flat areas: {'rect': [x, y, w, h], 'from': [x, y]}
        x0, y0, w, h = r['rect']
        c = list(pal[src[tuple(r['from'])]][:3])
        for y in range(y0, y0 + h):
            for x in range(x0, x0 + w):
                rgb[x, y] = list(c)
                opx[x, y] = src[tuple(r['from'])]
    notes = []
    for k, (text, box) in enumerate(zip(texts, boxes)):
        if text == '=':
            continue
        g = spec | (spec.get('labels') or [{}] * len(texts))[k]
        cov, cap = _coverage(text, box, g, W, H)
        notes.append(f'{text!r}: capitals {cap} px')
        if g.get('shadow'):
            sh = g['shadow']
            dx, dy = sh['offset']
            for (x, y), a in list(cov.items()):
                q = (x + dx, y + dy)
                if q in rgb and q not in cov:
                    a2 = a * sh.get('alpha', 0.5)
                    c = rgb[q]
                    rgb[q] = [c[i] * (1 - a2) + sh['colour'][i] * a2 for i in range(3)]
                    opx[q] = snap(tuple(rgb[q]) + (255,))
        screen = _screen(im, pal, g) if g.get('colour') == 'screen' else None
        for (x, y), a in cov.items():
            if screen is not None:
                ink = screen(x, y)
            else:
                ink = g['colour']
            c = rgb[x, y]
            c = [c[i] * (1 - a) + ink[i] * a for i in range(3)]
            opx[x, y] = snap(tuple(c) + (255,))
    return notes, 0


# ---------------------------------------------------------------- erase

def _inside(poly, x, y):
    n, c = len(poly), False
    for i in range(n):
        (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % n]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            c = not c
    return c


def _mask(im, pal, e):
    px = im.load()
    poly = e['poly']
    xs, ys = [p[0] for p in poly], [p[1] for p in poly]
    test = eval('lambda r, g, b: ' + e['ink'])
    inside = {(x, y) for y in range(max(0, min(ys)), min(im.height, max(ys) + 1))
              for x in range(max(0, min(xs)), min(im.width, max(xs) + 1)) if _inside(poly, x + .5, y + .5)}
    m = {p for p in inside if test(*pal[px[p]][:3])}
    n = e.get('close', 0)
    if n:
        m = _erode(_dilate(m, n), n) & inside | m
    m = _dilate(m, e.get('grow', 1))
    return {p for p in m if 0 <= p[0] < im.width and 0 <= p[1] < im.height}


def _dilate(m, n):
    out = set(m)
    for _ in range(n):
        out |= {(x + dx, y + dy) for x, y in out for dx in (-1, 0, 1) for dy in (-1, 0, 1)}
    return out


def _erode(m, n):
    out = set(m)
    for _ in range(n):
        out = {(x, y) for x, y in out if all((x + dx, y + dy) in out for dx in (-1, 0, 1) for dy in (-1, 0, 1))}
    return out


def _diffuse(rgb, mask, W, H, rounds=400):
    """Harmonic fill of the masked pixels from their unmasked neighbours (Gauss-Seidel)."""
    if not mask:
        return
    pts = sorted(mask, key=lambda p: (p[1], p[0]))
    # start: mean of the ring around the mask
    ring = [q for q in _dilate(mask, 1) - mask if q in rgb]
    mean = [sum(rgb[q][i] for q in ring) / max(1, len(ring)) for i in range(3)]
    for p in pts:
        rgb[p] = list(mean)
    nb = {p: [q for q in ((p[0] + 1, p[1]), (p[0] - 1, p[1]), (p[0], p[1] + 1), (p[0], p[1] - 1)) if q in rgb]
          for p in pts}
    for k in range(rounds):
        for p in (pts if k % 2 == 0 else reversed(pts)):
            q = nb[p]
            c = rgb[p]
            for i in range(3):
                c[i] = sum(rgb[n][i] for n in q) / len(q)


def _lattice(rgb, mask, basis, W, H, reach, x0=0):
    """A screened ground: the smooth part diffused, the dots copied. Each pixel = the diffused
    ground + (the unmarked pixel one lattice step away - that pixel's local mean over one cell)."""
    (ax, ay), (bx, by) = basis
    steps = []
    for i in range(-reach, reach + 1):
        for j in range(-reach, reach + 1):
            dx, dy = i * ax + j * bx, i * ay + j * by
            if (dx, dy) != (0, 0):
                steps.append((abs(dx) * 4 + abs(dy), dx, dy))
    steps.sort()
    cell = max(abs(ax), abs(ay), abs(bx), abs(by), 2)
    found = {}
    for (x, y) in mask:
        if x < x0:              # left of the screen ('screen_x'): diffused only
            continue
        for _, dx, dy in steps:
            q = (x + dx, y + dy)
            if q in rgb and q not in mask:
                found[x, y] = q
                break
    means = {}
    for q in set(found.values()):
        x, y = q
        pts = [(x + i, y + j) for i in range(-cell // 2, cell - cell // 2) for j in range(-cell // 2, cell - cell // 2)]
        pts = [p for p in pts if p in rgb and p not in mask]
        means[q] = [sum(rgb[p][k] for p in pts) / len(pts) for k in range(3)]
    detail = {p: [rgb[q][k] - means[q][k] for k in range(3)] for p, q in found.items()}
    _diffuse(rgb, mask, W, H)
    for p, d in detail.items():
        rgb[p] = [rgb[p][k] + d[k] for k in range(3)]


# ---------------------------------------------------------------- text

def _font(file, cap):
    size = cap * SUPER
    f = ImageFont.truetype(str(letter.FONT_DIR / file), round(size / 0.7))
    h = f.getbbox('H')
    return ImageFont.truetype(str(letter.FONT_DIR / file), round(f.size * size / (h[3] - h[1])))


def _line_image(text, font, tracking):
    h = font.getbbox('H')
    width = sum(font.getlength(ch) for ch in text) + tracking * SUPER * (len(text) - 1)
    pad = 8 * SUPER
    img = Image.new('L', (int(width) + 2 * pad, (h[3] - h[1]) * 2 + 2 * pad), 0)
    d = ImageDraw.Draw(img)
    x = pad
    for ch in text:
        d.text((x, pad - h[1]), ch, font=font, fill=255)
        x += font.getlength(ch) + tracking * SUPER
    bb = img.getbbox()
    return img.crop(bb), pad - bb[1]          # the image, and the cap line's row in it


def _coverage(text, box, g, W, H):
    """{(x, y): coverage 0..1} of the label, and the capital height used."""
    x0, y0, w, h = box
    lines = [t.strip() for t in text.split('/')] if g.get('lines') else [text]
    cap = g.get('cap', h)
    while True:
        font = _font(g['font'], cap)
        imgs = [_line_image(t, font, g.get('tracking', 0)) for t in lines]
        lead = g.get('leading', 1.25) * cap * SUPER
        tw = max(i.width for i, _ in imgs) + abs(g.get('shear', 0)) * cap * SUPER
        th = cap * SUPER + lead * (len(lines) - 1)
        if (tw <= w * SUPER and th <= h * SUPER) or cap <= 5:
            break
        cap -= 1
    side = max(w, h) * SUPER * 2               # room to turn the text in
    sheet = Image.new('L', (side, side), 0)
    cx, cy = sheet.width / 2, sheet.height / 2
    top = cy - th / 2
    for k, (i, off) in enumerate(imgs):
        ax = {'left': cx - tw / 2, 'right': cx + tw / 2 - i.width}.get(g.get('align'), cx - i.width / 2)
        sheet.paste(255, (round(ax), round(top + k * lead - off)), i)
    if g.get('shear'):
        s = g['shear']
        sheet = sheet.transform(sheet.size, Image.AFFINE, (1, s, -s * cy, 0, 1, 0), Image.BICUBIC)
    if g.get('rough'):
        sheet = _rough(sheet, g['rough'])
    if g.get('angle'):
        sheet = sheet.rotate(g['angle'], Image.BICUBIC, center=(cx, cy))
    if g.get('axes'):
        # text x -> picture direction u, text y (down) -> picture direction v: a slip in perspective
        (ux, uy), (vx, vy) = g['axes']
        det = ux * vy - uy * vx
        a, b, d, e = vy / det, -vx / det, -uy / det, ux / det       # inverse of [[ux, vx], [uy, vy]]
        sheet = sheet.transform(sheet.size, Image.AFFINE, (a, b, cx - a * cx - b * cy, d, e, cy - d * cx - e * cy),
                                Image.BICUBIC)
    if g.get('blur'):
        sheet = sheet.filter(ImageFilter.GaussianBlur(g['blur'] * SUPER))
    small = sheet.resize((sheet.width // SUPER, sheet.height // SUPER), Image.BOX)
    sp = small.load()
    ox, oy = math.floor(x0 + w / 2 - small.width / 2), math.floor(y0 + h / 2 - small.height / 2)
    cov = {}
    for j in range(small.height):
        for i in range(small.width):
            a = sp[i, j] / 255
            if a > 0.03:
                p = (ox + i, oy + j)
                if 0 <= p[0] < W and 0 <= p[1] < H:
                    cov[p] = min(1.0, a * g.get('gain', 1.0))
    return cov, cap


def _rough(sheet, amount):
    """A brush edge: the letters' outline nibbled and swollen by smooth fixed noise."""
    rnd = random.Random(7)
    n = Image.new('L', (sheet.width // (SUPER * 2) + 2, sheet.height // (SUPER * 2) + 2))
    n.putdata([rnd.randrange(256) for _ in range(n.width * n.height)])
    n = n.resize(sheet.size, Image.BICUBIC)
    soft = sheet.filter(ImageFilter.GaussianBlur(amount * SUPER))
    sp, np_ = soft.load(), n.load()
    out = Image.new('L', sheet.size, 0)
    op = out.load()
    for y in range(sheet.height):
        for x in range(sheet.width):
            v = sp[x, y]
            if v:
                t = max(80, 128 + (np_[x, y] - 128) * 0.8)    # no stray specks away from the letters
                op[x, y] = 255 if v > t else 0
    return out


def _screen(im, pal, g):
    """Colour of a letter pixel at (x, y): an original letter pixel one lattice step away."""
    e = g['screen']
    px = im.load()
    test = eval('lambda r, g, b: ' + e['ink'])
    poly = e['poly']
    xs, ys = [p[0] for p in poly], [p[1] for p in poly]
    region = {(x, y) for y in range(min(ys), max(ys) + 1) for x in range(min(xs), max(xs) + 1)
              if _inside(poly, x + .5, y + .5)}
    lettr = {p for p in region if test(*pal[px[p]][:3])}     # letter pixels, dots included
    (ax, ay), (bx, by) = e['lattice']
    steps = sorted(((abs(i * ax + j * bx) * 4 + abs(i * ay + j * by), i * ax + j * bx, i * ay + j * by)
                    for i in range(-40, 41) for j in range(-40, 41)))
    cache = {}

    def colour(x, y):
        if (x, y) not in cache:
            c = None
            for _, dx, dy in steps:
                q = (x + dx, y + dy)
                if q in lettr:
                    c = pal[px[q]][:3]
                    break
            cache[x, y] = c or (255, 255, 255)
        return cache[x, y]
    return colour
