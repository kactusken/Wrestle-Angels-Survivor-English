#!/usr/bin/env python3
"""Roster group pictures for the player's guide: the wrestlers' portraits side by side, one picture
per group (New Japan, free agents, the tryout pool, the rookies, the 2P alternates, overseas).

  rostercards.py              write docs/guide/roster/<group>.webp
  rostercards.py --list       only print the groups and who is in them

Needs Pillow, and the English portraits in review/images-english (A015_p<n>_0.png, one per roster
record, from tools/gfx.py); the groups come from tools/guidedata.py, so they follow the same data
as the guide's roster table. The portraits are the patch's own pictures with the English name down
the right edge; this crops the figure, lays the group out on the guide's indigo grid with a gold
title stroke, and writes a WebP. The owner made an exception to the no-game-art rule for these
(2026-10-26): docs/guide/roster/ only.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import paths  # noqa: E402
import roster  # noqa: E402
import guidedata  # noqa: E402

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    sys.exit('needs Pillow: .venv/bin/pip install -r requirements.txt, then run with .venv/bin/python')

OUT = paths.DOCS / 'guide' / 'roster'
FONTS = Path(__file__).resolve().parent / 'fonts'

ART = (0, 0, 452, 432)       # the figure on an A015 portrait; the name is at x 456+, faces below 432
CELL_W, CELL_H = 168, 212    # one wrestler: figure 168x176 and a name band
PER_ROW = 12                 # at most; rows are balanced
PAD, TITLE_H = 28, 92
BG, GRID, INK, MUTED = (26, 35, 128), (90, 210, 255, 34), (243, 245, 255), (185, 195, 242)
GOLD, GOLD_DEEP, BAND = (249, 190, 13), (240, 138, 0), (11, 16, 64, 210)


def groups(data):
    """[(file stem, title, subtitle, [wrestlers])] in guide order."""
    W = data['wrestlers']
    P = {p['i']: p['n'] for p in data['promotions']}
    japanese = [w for w in W if w['id'] < 200 and w.get('alt') is None]
    alts = [w for w in W if w['id'] < 200 and w.get('alt') is not None]
    foreign = [w for w in W if w['id'] >= 200]
    out = [
        ('new-japan', "New Japan Women's Pro", 'The fixed rival: its roster at the start of every management game',
         [w for w in japanese if w.get('p') == 0]),
        ('rival-stars', 'Rival stars and free agents', 'On the other rival rosters (' +
         ', '.join(sorted({P[w['p']] for w in japanese if w.get('p') not in (None, 0)})) + ') or free to sign in year 1',
         [w for w in japanese if w.get('p') not in (None, 0)] + [w for w in japanese if w.get('p') is None and w.get('st') == 'veteran']),
        ('tryout-pool', 'The tryout pool', 'Rookies who can turn up in tryouts and scouting from year 1',
         [w for w in japanese if w.get('st') == 'prospect' and w.get('p') is None]),
        ('rookies', 'Later rookies', 'Debut as 15-year-olds in years 2-5',
         sorted([w for w in japanese if w.get('st') == 'rookie'], key=lambda w: (w.get('dy', 0), w['id']))),
        ('alternates-1', '2P alternates, years 3-6', 'The second versions of the originals, debuting as rookies',
         sorted([w for w in alts if w.get('dy', 99) <= 6], key=lambda w: (w.get('dy', 0), w['id']))),
        ('alternates-2', '2P alternates, years 7-11', 'The last four arrive after a default 10-year game',
         sorted([w for w in alts if w.get('dy', 0) > 6], key=lambda w: (w.get('dy', 0), w['id']))),
        ('overseas-1', 'Overseas wrestlers', 'They come with the overseas partners (part 1 of 2)',
         [w for w in foreign if w.get('fg') in (0, 1, 2, 3)]),
        ('overseas-2', 'Overseas wrestlers', 'Part 2 of 2, with Sophie and Holly Sierra, whom management mode never uses',
         [w for w in foreign if w.get('fg') not in (0, 1, 2, 3)]),
    ]
    placed = [w['id'] for g in out for w in g[3]]
    twice = {w['n'] for w in W if placed.count(w['id']) > 1}
    if twice:
        sys.exit(f'rostercards: in two groups: {", ".join(sorted(twice))}')
    missing = [w['n'] for w in W if w['id'] not in placed]
    if missing:
        sys.exit(f'rostercards: not in any group: {", ".join(missing)}')
    return out


def records():
    """English name -> roster record number (= the portrait's piece number)."""
    out = {}
    rows ={r['key']: r for r in roster.read_rows()}
    for n in range(206):
        out[rows[f'{n}.name']['english'].strip()] = n
    return out


def figure(n):
    src = paths.ENGLISH_IMAGES / f'A015_p{n}_0.png'
    if not src.is_file():
        sys.exit(f'rostercards: {paths.show(src)} is missing - extract the pictures first (tools/gfx.py)')
    im = Image.open(src).convert('RGBA').crop(ART)
    box = im.getchannel('A').getbbox() or (0, 0, *im.size)
    # the top of the figure, as wide as it is, square: head and shoulders down to the waist
    x0, y0, x1, _ = box
    side = max(x1 - x0, 300)
    cx = (x0 + x1) // 2
    crop = im.crop((cx - side // 2, y0, cx - side // 2 + side, y0 + side))
    return crop.resize((CELL_W, CELL_W), Image.LANCZOS)


def font(name, size):
    return ImageFont.truetype(str(FONTS / name), size)


def fit(draw, text, name, size, width):
    f = font(name, size)
    while draw.textlength(text, font=f) > width and size > 10:
        size -= 1
        f = font(name, size)
    return f


def poster(title, subtitle, members, rec):
    rows = -(-len(members) // PER_ROW)
    cols = -(-len(members) // rows)
    W = PAD * 2 + cols * CELL_W
    H = PAD + TITLE_H + rows * CELL_H + PAD
    im = Image.new('RGBA', (W, H), BG + (255,))
    grid = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    g = ImageDraw.Draw(grid)
    for x in range(0, W, 32):
        g.line([(x, 0), (x, H)], fill=GRID)
    for y in range(0, H, 32):
        g.line([(0, y), (W, y)], fill=GRID)
    im.alpha_composite(grid)
    d = ImageDraw.Draw(im)
    # title with the gold brush stroke under it
    tf = font('BarlowCondensed-ExtraBoldItalic.ttf', 46)
    tw = d.textlength(title, font=tf)
    sx, sy = PAD, PAD + 52
    stroke = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    s = ImageDraw.Draw(stroke)
    length = int(min(tw + 60, W * 0.6))
    for i in range(length):
        a = 255 if i < length * 0.55 else int(255 * (1 - (i - length * 0.55) / (length * 0.45)))
        t = min(1, i / (length * 0.35))
        c = tuple(int(GOLD_DEEP[k] + (GOLD[k] - GOLD_DEEP[k]) * t) for k in range(3))
        s.line([(sx + i + 5, sy), (sx + i, sy + 9)], fill=c + (a,))
    im.alpha_composite(stroke)
    d.text((PAD, PAD - 6), title, font=tf, fill=INK)
    d.text((PAD + 2, PAD + 66), subtitle, font=font('Barlow-Medium.ttf', 18), fill=MUTED)
    nf_name = 'BarlowCondensed-Bold.ttf'
    for i, w in enumerate(members):
        r, c = divmod(i, cols)
        x = PAD + c * CELL_W
        y = PAD + TITLE_H + r * CELL_H
        im.alpha_composite(figure(rec[w['n']]), (x, y))
        band = Image.new('RGBA', (CELL_W - 6, 30), BAND)
        im.alpha_composite(band, (x + 3, y + CELL_W + 2))
        label = w['n']
        f = fit(d, label, nf_name, 20, CELL_W - 16)
        d.text((x + CELL_W / 2, y + CELL_W + 17), label, font=f, fill=INK, anchor='mm')
    return im.convert('RGB')


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0], epilog=paths.FOLDER_HELP,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--list', action='store_true', help='only print the groups')
    args = ap.parse_args(paths.configure(sys.argv[1:] if argv is None else argv))
    data = guidedata.build()
    gs = groups(data)
    if args.list:
        for stem, title, sub, members in gs:
            print(f'{stem}: {title} ({len(members)}): {", ".join(w["n"] for w in members)}')
        return
    rec = records()
    OUT.mkdir(parents=True, exist_ok=True)
    for stem, title, sub, members in gs:
        out = OUT / f'{stem}.webp'
        poster(title, sub, members, rec).save(out, 'WEBP', quality=86, method=6)
        print(f'{paths.show(out)}: {len(members)} wrestlers, {out.stat().st_size // 1024} KB')


if __name__ == '__main__':
    main()
