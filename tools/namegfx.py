#!/usr/bin/env python3
"""Wrestler names in pictures: writes a tools/letter.py spec per picture from the English names in
translation/text/roster.csv (run it again after changing a name, then letter.py on the pictures).

  namegfx.py            write the specs (translation/letters/A041_p<n>_0.json, A015_p<n>_0.json)
  namegfx.py --draw     and draw them (letter.py)

*From the data*: /A040/A041. holds one 256x32 name strip per wrestler, /A000/A015. one portrait
per wrestler with her name written down its right edge, /A000/A018. the match-up screen's
close-ups (piece n + 1; piece 0 is something else), /A000/A01C. face pictures with the name on
top (the first 120 wrestlers) - all in roster order (the first 206 records are the wrestlers).
See tools/letter_ext/names.py.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import paths  # noqa: E402
import roster  # noqa: E402

WRESTLERS = 206
FONT = 'BarlowCondensed-Bold.ttf'
KINDS = {
    'A041': {'source': '/A040/A041. part {p}', 'width': 256, 'height': 32, 'bpp': 4,
             'box': [0, 0, 176, 22], 'mode': 'strip', 'cap': 15,
             'notes': 'name strip under the wrestler in a match (tools/namegfx.py)'},
    'A015': {'source': '/A000/A015. part {p}', 'width': 512, 'height': 512, 'bpp': 8,
             'box': [456, 0, 56, 304], 'mode': 'portrait', 'cap': 28, 'top': 4,
             'notes': 'vertical name on the full portrait, turned 90 degrees clockwise, '
                      'reads top to bottom (tools/namegfx.py)'},
    'A018': {'source': '/A000/A018. part {p}', 'width': 512, 'height': 512, 'bpp': 8, 'offset': 1,
             'boxes': [[432, 200, 32, 265], [464, 200, 32, 265]], 'mode': 'vsband', 'cap': 17,
             'notes': 'match-up (VS) screen close-ups: the name in the red and the blue band, '
                      'turned 90 degrees clockwise, ending where the Japanese did (tools/namegfx.py)'},
    # The Japanese name across the top is kept (erasing it cut into the hair); the English goes
    # small in a band ending at row 116, the bottom of the art (rows 117-127 are transparent and
    # not shown) - as WAS2 does its portrait tags
    'A01C': {'source': '/A000/A01C. part {p}', 'width': 128, 'height': 128, 'bpp': 8, 'count': 120,
             'box': [0, 103, 128, 14], 'mode': 'icon', 'cap': 8,
             'extra': {'draw': 'portraits.draw', 'band': [0, 103, 128, 14], 'clear_tag': False,
                       'font': 'BarlowSemiCondensed-Bold.ttf', 'outline_width': 1},
             'notes': 'face picture: Japanese name kept at the top, English at the bottom of the art '
                      '(tools/namegfx.py)'},
}


def names():
    rows = {r['key']: r for r in roster.read_rows()}
    out = []
    for n in range(WRESTLERS):
        r = rows[f'{n}.name']
        if not r['english'].strip():
            raise SystemExit(f'namegfx: roster record {n} ({r["japanese"]}) has no English name')
        out.append((r['japanese'], r['english'].strip()))
    return out


def write_specs():
    d = paths.TRANSLATION / 'letters'
    ids = []
    for n, (jp, en) in enumerate(names()):
        for stem, k in KINDS.items():
            if n >= k.get('count', WRESTLERS):
                continue
            p = n + k.get('offset', 0)                  # the picture's piece number
            boxes = k.get('boxes', [k.get('box')])
            spec = {'english': ' | '.join([en] * len(boxes)), 'boxes': boxes, 'ground': 'transparent',
                    'font': FONT, 'cap': k['cap'], 'draw': 'names.draw', 'mode': k['mode'],
                    'notes': k['notes'],
                    'catalogue': {'source': k['source'].format(n=n, p=p), 'width': k['width'],
                                  'height': k['height'], 'bpp': k['bpp'], 'category': 'name',
                                  'japanese': jp}}
            if 'top' in k:
                spec['top'] = k['top']
            spec.update(k.get('extra', {}))
            ident = f'{stem}_p{p}_0'
            (d / f'{ident}.json').write_text(json.dumps(spec, ensure_ascii=False, indent=1) + '\n',
                                             encoding='utf-8')
            ids.append(ident)
    print(f'namegfx: {len(ids)} specs')
    return ids


def main(argv=None):
    argv = paths.configure(sys.argv[1:] if argv is None else argv)
    ids = write_specs()
    if '--draw' in argv:
        import letter
        letter.main(ids)
    return 0


if __name__ == '__main__':
    sys.exit(main())
