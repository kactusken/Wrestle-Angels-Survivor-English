"""Wrestler names drawn into pictures, for tools/letter.py (spec "draw": "names.draw"). The specs
are written from translation/text/roster.csv by tools/namegfx.py, one per picture.

  mode "strip"     A041_p<n>_0 (256x32, 4bpp): the name under the wrestler's picture in a match.
                   White lettering with no outline: palette entry i is white at opacity i/15;
                   each pixel's coverage picks one of entries 4, 7, 11 and 15 (STRIP_LEVELS).
                   The whole picture is cleared; the English is centred on the Japanese's centre
                   line (x = 88, the middle of the 176-pixel field of 8 full-width characters).
  mode "portrait"  A015_p<n>_0 (512x512, 8bpp): the vertical name at the right edge of the
                   wrestler's full portrait. White letters with a red
                   outline that fades out in semi-transparent reds. Only the name's own pixels are
                   cleared: from the pure red outline pixels in the box, a flood fill through
                   name-coloured pixels (red to white: r >= 230, g and b within 12 of each other)
                   - the portrait art next to the column is left alone. The English is turned 90
                   degrees clockwise so it reads top to bottom (as the nickname strips), its
                   capitals facing right, starting `top` px down the box.

  mode "vsband"    A018_p<n+1>_0 (512x512, 8bpp): the match-up ("VS") screen's close-ups, with the
                   name in a red and a blue vertical band (two boxes). White letters, black outline,
                   on a band that fades in from the top (semi-transparent rows). The lettering's
                   pixels (anything not red or blue) become the band's colour of that row (the
                   most common other pixel of the row in the box); the English reads top to bottom
                   and ends where the Japanese did (`bottom`).
  mode "icon"      A01C_p<n>_0 (128x128, first 120 wrestlers): the name across the top of a face
                   picture, white with a navy outline, partly over the hair. The name's pixels
                   (white-to-navy blends, flooded from the white ones) take the colour of the
                   nearest pixel below them that isn't lettering (up to 4 px), else clear; the
                   English is centred on x = 64.

Spec keys besides letter.py's: mode, font, cap (capital height in px), top (portrait), bottom
(vsband), outline (outline width in px; portrait 3, vsband 2, icon 2), centre_y (icon).
"""
import sys
from collections import Counter
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import letter  # noqa: E402

SUPER = 4
MIN_SQUEEZE = 0.75
STRIP_CENTRE = 88


def _font(file, cap):
    """Font at the size whose capital H is `cap` px tall at SUPER."""
    size = cap * SUPER
    for _ in range(3):
        f = ImageFont.truetype(str(letter.FONT_DIR / file), size)
        b = f.getbbox('H', anchor='ls')
        size = round(size * cap * SUPER / (b[3] - b[1]))
    return ImageFont.truetype(str(letter.FONT_DIR / file), size)


def _line(text, file, cap, length, depth):
    """Coverage (L, 1x) of the text set horizontally, at most `length` px long and `depth` px from
    capital top to descender: (image, cap top y, cap, squeeze). Squeezed, then smaller."""
    while cap > 6:
        f = _font(file, cap)
        l, t, r, b = f.getbbox(text, anchor='ls')
        desc = max(0, b) // SUPER + 1
        pad = 2 * SUPER
        im = Image.new('L', (r - l + 2 * pad, cap * SUPER + desc * SUPER + 2 * pad), 0)
        ImageDraw.Draw(im).text((pad - l, pad + cap * SUPER), text, font=f, fill=255, anchor='ls')
        w = (r - l) / SUPER
        squeeze = min(1.0, length / w)
        if squeeze >= MIN_SQUEEZE and cap + desc <= depth:
            small = im.resize((max(1, round(im.width * squeeze / SUPER)), round(im.height / SUPER)),
                              Image.LANCZOS)
            return small, pad / SUPER, cap, squeeze
        cap -= 1
    raise SystemExit(f'names: {text!r} does not fit {length} px')


# coverage (0-15) -> palette entry. The player's strip flashes with a palette of its own that
# shows the faint entries as colours (test8: a dotted line under the name, coloured fringes):
# drop 1-3 and keep to the four entries the Japanese strips mostly use
STRIP_LEVELS = [0, 0, 0, 0, 4, 4, 7, 7, 7, 11, 11, 11, 11, 15, 15, 15]


def _strip(out, text, box, spec):
    x, y, w, h = box
    out.paste(0, (0, 0, out.width, out.height))
    cov, top, cap, sq = _line(text, spec['font'], spec.get('cap', 14), w - 2, h)
    bb = cov.point(lambda v: 255 if v >= 24 else 0).getbbox() or (0, 0, cov.width, cov.height)
    ox = x + STRIP_CENTRE - (bb[0] + bb[2]) // 2
    oy = y + round((h - cap) / 2 - top)
    px, cp = out.load(), cov.load()
    for j in range(cov.height):
        for i in range(cov.width):
            v = STRIP_LEVELS[round(cp[i, j] * 15 / 255)]
            if v and 0 <= ox + i < out.width and 0 <= oy + j < out.height:
                px[ox + i, oy + j] = max(px[ox + i, oy + j], v)
    return cap, sq


def _name_coloured(c):
    r, g, b, a = c
    return a > 0 and r >= 230 and abs(g - b) <= 12


def _clear_name(out, pal, box):
    x0, y0, w, h = box
    px = out.load()
    clear = next(i for i, c in enumerate(pal) if c[3] == 0)
    seeds = [(x, y) for y in range(y0, y0 + h) for x in range(x0, x0 + w)
             if pal[px[x, y]][:3] in ((253, 0, 0), (255, 0, 0)) and pal[px[x, y]][3] == 255]
    seen, todo = set(seeds), list(seeds)
    while todo:
        x, y = todo.pop()
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if (nx, ny) not in seen and x0 <= nx < x0 + w and y0 <= ny < y0 + h \
                    and _name_coloured(pal[px[nx, ny]]):
                seen.add((nx, ny))
                todo.append((nx, ny))
    # stray dither pixels of other colours inside the white letters
    for _ in range(3):
        add = []
        for y in range(y0 + 1, y0 + h - 1):
            for x in range(x0 + 1, x0 + w - 1):
                if (x, y) not in seen and sum((x + dx, y + dy) in seen for dx in (-1, 0, 1)
                                              for dy in (-1, 0, 1)) >= 5:
                    add.append((x, y))
        seen.update(add)
    # the outline's faintest edge pixels touch it only diagonally or across a clear pixel
    for x, y in list(seen):
        for dx in range(-3, 4):
            for dy in range(-3, 4):
                n = (x + dx, y + dy)
                if n not in seen and x0 <= n[0] < x0 + w and y0 <= n[1] < y0 + h:
                    c = pal[px[n]]
                    if c[3] < 255 and _name_coloured(c):
                        seen.add(n)
    for x, y in seen:
        px[x, y] = clear
    return len(seen)


def _portrait(out, pal, text, box, spec):
    x, y, w, h = box
    if not _clear_name(out, pal, box):
        raise SystemExit(f'names: no red name in {box}')
    ow = spec.get('outline', 3)
    top = spec.get('top', 4)
    cov, ctop, cap, sq = _line(text, spec['font'], spec.get('cap', 24), h - top - 2 * ow - 2,
                               w - 2 * ow - 2)
    # outline: the fill dilated by ow px, soft at its edge
    pad = ow + 2
    fill = Image.new('L', (cov.width + 2 * pad, cov.height + 2 * pad), 0)
    fill.paste(cov, (pad, pad))
    edge = fill.filter(ImageFilter.MaxFilter(2 * ow + 1)).filter(ImageFilter.GaussianBlur(0.6))
    # turn clockwise: the line's top faces right, the text reads top to bottom
    fill, edge = fill.transpose(Image.ROTATE_270), edge.transpose(Image.ROTATE_270)
    bb = edge.point(lambda v: 255 if v >= 24 else 0).getbbox()
    # centre the capitals + descenders across the box; the line starts `top` px down
    ox = x + (w - (bb[2] - bb[0])) // 2 - bb[0]
    oy = y + top - bb[1]
    red, white = (253, 0, 0), (255, 255, 255)
    px, fp, ep = out.load(), fill.load(), edge.load()
    limit = len(pal)
    cache = {}
    for j in range(fill.height):
        for i in range(fill.width):
            e, f = ep[i, j] / 255, fp[i, j] / 255
            if e < 0.05 and f < 0.05:
                continue
            X, Y = ox + i, oy + j
            if not (x <= X < x + w and y <= Y < y + h):
                continue
            # white over red outline over what is there (transparent around the name)
            a = max(e, f)
            rgb = tuple(round(white[k] * f + red[k] * (1 - f)) if a else 0 for k in range(3))
            key = rgb + (round(a * 255),)
            if key not in cache:
                cache[key] = letter.nearest(pal, key, limit)
            px[X, Y] = cache[key]
    return cap, sq


def _over(top, a, under):
    """RGBA of colour `top` at coverage a over the RGBA `under` (straight alpha)."""
    ua = under[3] / 255
    oa = a + ua * (1 - a)
    if oa <= 0:
        return (0, 0, 0, 0)
    rgb = tuple(round((top[k] * a + under[k] * ua * (1 - a)) / oa) for k in range(3))
    return rgb + (round(oa * 255),)


def _paint_outlined(out, pal, cov, ox, oy, box, fill_rgb, edge_rgb, ow, ground=None):
    """Draw coverage `cov` (L, final orientation) at (ox, oy) with an `ow` px outline, over what
    is in `out` (or ground(x, y) -> RGBA), snapped to the palette, clipped to box."""
    pad = ow + 2
    fill = Image.new('L', (cov.width + 2 * pad, cov.height + 2 * pad), 0)
    fill.paste(cov, (pad, pad))
    edge = fill.filter(ImageFilter.MaxFilter(2 * ow + 1)).filter(ImageFilter.GaussianBlur(0.5))
    x0, y0, w, h = box
    px, fp, ep = out.load(), fill.load(), edge.load()
    cache = {}
    for j in range(fill.height):
        for i in range(fill.width):
            e, f = ep[i, j] / 255, fp[i, j] / 255
            if e < 0.05 and f < 0.05:
                continue
            X, Y = ox - pad + i, oy - pad + j
            if not (x0 <= X < x0 + w and y0 <= Y < y0 + h):
                continue
            under = ground(X, Y) if ground else pal[px[X, Y]]
            c = _over(fill_rgb, f, _over(edge_rgb, e, under))
            if c not in cache:
                cache[c] = letter.nearest(pal, c, len(pal))
            px[X, Y] = cache[c]


def _vsband(out, pal, text, box, spec):
    x0, y0, w, h = box
    px = out.load()

    def lettering(c):
        r, g, b, a = c
        return a > 0 and not (max(r, g, b) - min(r, g, b) > 120 and min(r, g, b) < 60)

    rowcol = {}
    for y in range(y0, y0 + h):
        c = Counter(px[x, y] for x in range(x0, x0 + w) if not lettering(pal[px[x, y]]))
        rowcol[y] = c.most_common(1)[0][0] if c else next(i for i, q in enumerate(pal) if q[3] == 0)
        for x in range(x0, x0 + w):
            if lettering(pal[px[x, y]]):
                px[x, y] = rowcol[y]
    ow = spec.get('outline', 2)
    bottom = spec.get('bottom', 431)
    top = spec.get('top', 222)
    cov, ctop, cap, sq = _line(text, spec['font'], spec.get('cap', 17), bottom - top, w - 2 * ow - 4)
    rot = cov.transpose(Image.ROTATE_270)
    bb = rot.point(lambda v: 255 if v >= 24 else 0).getbbox()
    ox = x0 + (w - (bb[2] - bb[0])) // 2 - bb[0]
    oy = bottom + 1 - bb[3]
    _paint_outlined(out, pal, rot, ox, oy, box, (255, 255, 255), (0, 0, 0), ow)
    return cap, sq


def _icon(out, pal, text, box, spec):
    x0, y0, w, h = box
    px = out.load()
    navy = (13, 0, 73)

    def blend(c):
        r, g, b, a = c
        if a == 0:
            return False
        t = g / 255
        exp = (navy[0] + (255 - navy[0]) * t, g, navy[2] + (255 - navy[2]) * t)
        return abs(r - exp[0]) <= 18 and abs(b - exp[2]) <= 18

    seeds = [(x, y) for y in range(y0, y0 + h) for x in range(x0, x0 + w)
             if pal[px[x, y]] == (255, 255, 255, 255)]
    seen, todo = set(seeds), list(seeds)
    while todo:
        x, y = todo.pop()
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                n = (x + dx, y + dy)
                if n not in seen and x0 <= n[0] < x0 + w and y0 <= n[1] < y0 + h \
                        and blend(pal[px[n]]):
                    seen.add(n)
                    todo.append(n)
    clear = next(i for i, c in enumerate(pal) if c[3] == 0)
    for x, y in sorted(seen, key=lambda p: -p[1]):         # bottom rows first
        for k in range(1, 5):
            if y + k < out.height and (x, y + k) not in seen:
                px[x, y] = px[x, y + k] if pal[px[x, y + k]][3] else clear
                break
        else:
            px[x, y] = clear
    ow = spec.get('outline', 2)
    cov, ctop, cap, sq = _line(text, spec['font'], spec.get('cap', 9), w - 2 * ow - 4, h)
    bb = cov.point(lambda v: 255 if v >= 24 else 0).getbbox()
    ox = x0 + 64 - (bb[0] + bb[2]) // 2
    oy = round(spec.get('centre_y', 9.5) - cap / 2 - ctop)
    _paint_outlined(out, pal, cov, ox, oy, (0, 0, out.width, out.height), (255, 255, 255), navy, ow)
    return cap, sq


def draw(name, im, out, pal, texts, boxes, spec):
    notes, caps = [], []
    mode = spec.get('mode')
    for text, box in zip(texts, boxes):
        if text == '=':
            continue
        if mode == 'portrait':
            cap, sq = _portrait(out, pal, text, box, spec)
        elif mode == 'icon':
            cap, sq = _icon(out, pal, text, box, spec)
        elif mode == 'vsband':           # the same name in the red and the blue band
            cap, sq = _vsband(out, pal, text, box, spec)
        else:
            cap, sq = _strip(out, text, box, spec)
        caps.append(cap)
        if sq < 1:
            notes.append(f'{text!r}: squeezed to {sq:.0%}')
        if cap < spec.get('cap', 0):
            notes.append(f'{text!r}: capitals {cap} px')
    return notes, min(caps) if caps else 0
