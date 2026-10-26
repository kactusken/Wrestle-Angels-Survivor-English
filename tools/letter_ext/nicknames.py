"""Wrestler nicknames for tools/letter.py (spec "draw": "nicknames.draw"): A04A_p1_0 ... p85_0 and
the champion words of A04A_p0_0.

These pictures are white lettering with no outline: the 16 palette entries are all white, and
entry i is i/15 opaque (0 = clear, 15 = solid). So a letter is just an antialiased mask, and each
pixel's coverage picks the entry of the same opacity.

Spec keys used here besides letter.py's:
  mode     vertical (default): the English turned 90 degrees clockwise so it reads top to bottom,
           as the vertical Japanese does, starting at the box's top;
           upright: set normally, centred in the box (the 1-cell "Ex" for 前).
  font     file in tools/fonts;  cap: capital height in px (vertical: across the box)
  top      vertical: px from the box's top where the text starts (default 2, as the Japanese)
  axis     vertical: x (inside the box) of the first capital column - capitals stand to its
           right, descenders hang to its left (default: caps + descenders centred in the box, the
           same for every strip)
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import letter  # noqa: E402

FONT_DIR = letter.FONT_DIR
SUPER = 4
MIN_SQUEEZE = 0.78      # narrowest horizontal squeeze (along the text) before the size drops


def _font(file, cap):
    """Font at the size whose capital H is `cap` px tall (at SUPER)."""
    size = cap * SUPER
    for _ in range(3):
        f = ImageFont.truetype(str(FONT_DIR / file), size)
        b = f.getbbox('H', anchor='ls')
        size = round(size * cap * SUPER / (b[3] - b[1]))
    return ImageFont.truetype(str(FONT_DIR / file), size)


def _line(text, file, cap):
    """Coverage of `text` set horizontally at SUPER: (L image, baseline y, cap top y)."""
    f = _font(file, cap)
    l, t, r, b = f.getbbox(text, anchor='ls')
    pad = 2 * SUPER
    im = Image.new('L', (r - l + 2 * pad, b - t + 2 * pad), 0)
    ImageDraw.Draw(im).text((pad - l, pad - t), text, font=f, fill=255, anchor='ls')
    base = pad - t
    return im, base, base - cap * SUPER


def _fit(text, file, cap, length, depth):
    """(image at 1x, baseline, cap top, cap, squeeze): the line shrunk to `length` px along and
    no more than `depth` px across."""
    while cap > 6:
        im, base, top = _line(text, file, cap)
        w = im.width / SUPER
        squeeze = min(1.0, length / w)
        if squeeze >= MIN_SQUEEZE and im.height / SUPER <= depth + 4:
            nw = max(1, round(im.width * squeeze / SUPER))
            nh = max(1, round(im.height / SUPER))
            small = im.resize((nw, nh), Image.LANCZOS)
            return small, base / SUPER, top / SUPER, cap, squeeze
        cap -= 1
    raise SystemExit(f'nicknames: {text!r} does not fit {length} px')


def _paint(out, cov, ox, oy, box):
    """Write coverage (L image) at (ox, oy) into `out` as palette entry = opacity, inside box."""
    x0, y0, w, h = box
    px, cp = out.load(), cov.load()
    for j in range(cov.height):
        for i in range(cov.width):
            x, y = ox + i, oy + j
            if x0 <= x < x0 + w and y0 <= y < y0 + h:
                v = round(cp[i, j] * 15 / 255)
                if v:
                    px[x, y] = max(px[x, y], v)


def _bounds(cov):
    b = cov.point(lambda v: 255 if v >= 24 else 0).getbbox()
    return b or (0, 0, 0, 0)


def draw(name, im, out, pal, texts, boxes, spec):
    notes, caps = [], []
    mode = spec.get('mode', 'vertical')
    for text, box in zip(texts, boxes):
        if text == '=':
            continue
        x, y, w, h = box
        px = out.load()
        for j in range(h):
            for i in range(w):
                px[x + i, y + j] = 0
        cap = spec.get('cap', 14)
        if mode == 'upright':
            cov, base, top, c, sq = _fit(text, spec['font'], cap, w - 2, h)
            l, t, r, b = _bounds(cov)
            ox = x + (w - (r - l)) // 2 - l
            oy = y + round((h - c) / 2 - top)
            _paint(out, cov, ox, oy, box)
        else:
            start = spec.get('top', 2)
            cov, base, top, c, sq = _fit(text, spec['font'], cap, h - start - 1, w)
            l, t, r, b = _bounds(cov)
            rot = cov.transpose(Image.ROTATE_270)       # clockwise: line top -> right side
            # after rotating, row y of the line becomes column (height - 1 - y)
            H = cov.height
            desc = round(c * 0.3)
            axis = spec.get('axis', (w - c - desc) // 2 + desc)
            ox = x + axis - (H - round(base))
            oy = y + start - l
            _paint(out, rot, ox, oy, box)
        caps.append(c)
        if sq < 1:
            notes.append(f'{text!r}: squeezed to {sq:.0%}')
        if c < cap:
            notes.append(f'{text!r}: capitals {c} px')
    notes.insert(0, f'capitals {min(caps) if caps else 0} px')
    return notes, min(caps) if caps else 0
