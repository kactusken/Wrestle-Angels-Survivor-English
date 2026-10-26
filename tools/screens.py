#!/usr/bin/env python3
"""Room for English on management-mode screens whose text is cut out of a text page by sprites
at fixed byte columns (a build step; see tools/infopage.py for the info screen itself).

*From the code*: 0x13afd0 (text, column, row, page, flags) writes into a text page 24 full-width
cells wide; layout tables of 24-byte sprites (u32, u32, u16 w, h, screen x, y, texture u, v) cut
the pieces out, 11 px per byte. The Japanese values had fixed byte lengths, the English don't:

  map title   home-base map (0x1a9710): the prefecture, padded with spaces only when it is 4 or
              6 bytes long, then the venue's "Last show..." text; the sprite at 0x4a7f28 shows
              the first 8 bytes (88 px). "Fukui" showed as "FukuiLas". Now every name is padded to
              10 bytes ("%-10s"; 東%s / 西%s are "E.%-8s" / "W.%-8s" in exe.csv), the title sprite
              is 110 px wide and the "Last show" sprite after it starts at u = 110.
  rankings    rows "%s　%2d　%s　%s　%s" (name, age, hometown, alignment, status) at byte columns
              0, 22, 26 (8 bytes), 36, 40 (layout 0x4947a0; the hometown sprites 0x4947d0, 8
              rows 0x78 apart). The hometown was centred in 8 bytes by 0x17941c (switched off by
              infopage.py for the info screen's %-9.9s) and English names run to 9 letters, so
              everything after it moved.
              Now "%-9.9s" with the hometown sprite 99 px wide, and the alignment marks Ｇ/Ｎ/Ｅ
              (full-width, which the font draws oddly) are "G "/"N "/"E ".
"""
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import exefile  # noqa: E402

EXE = '/SLPM_662.39'

# (address, original, new, room): strings in place; the room (bytes up to the next string) must be
# zeros after the original
STRINGS = [
    (0x4a8008, '%s', '%-10s', 8),
    (0x496990, '%s　%2d　%s　%s　%s', '%s  %2d  %-9.9s %s  %s', 24),
    (0x4966d8, 'Ｇ', 'G ', 8),
    (0x4966e0, 'Ｎ', 'N ', 8),
    (0x4966e8, 'Ｅ', 'E ', 8),
    # save/load slot label: 0x1eefe4 copies 9 bytes and adds 1 to byte 7 (the low byte of １) for
    # the next slots; the row is turned full-width and cut 4 cells wide, so the English is
    # full-width too with its digit in the same place
    (0x4843d0, 'データ１', 'Ｎｏ．１', 9),
    # a created belt's name: the promotion's abbreviation + Heavy/Tag/Junior (0x193f04-0x193fa4,
    # into 204-byte records at 0x8e4100), which ran together as "ABCHeavy"
    (0x498b48, '%s%s', '%s %s', 8),
    # the nine CPU promotions (table 0x4a4b20, records of 0x30 bytes, the name in the first 22):
    # 0x19a104 copies the name into the promotion. The code reaches only the table base, so the
    # names are written here in place, spelt as on the promotions' own logos (A01F), shortened to
    # fit 21 bytes
    *[(0x4a4b20 + 0x30 * k, ja, en, 22) for k, (ja, en) in enumerate([
        ('新日本女子プロレス', "New Japan Women's Pro"),
        ('太平洋女子プロレス', 'Pacific Women Pro'),
        ('激闘龍', 'Gekitouryu'),
        ('日本海女子プロレス', 'Japan Ocean Women Pro'),
        ('パラシオン', 'Palacion'),
        ('ＪＷＩ', 'JWI'),
        ('ワールド女子プロレス', 'World Women Pro'),
        ('ＷＡＲＳ', 'WARS'),
        ('プロレスリング　ネオ', 'Pro Wrestling NEO'),
    ])],
]
# sprites: (entry address, (w, h, x, y, u, v) original, new w, new u)
SPRITES = [
    (0x4a7f28, (88, 22, 0, 0, 0, 66), 110, 0),          # map title: the prefecture
    (0x4a7f40, (242, 22, 0, 0, 88, 66), 242, 110),      # map title: "Last show ..."
    *[(0x4947d0 + 0x78 * k, (88, 22, 384, 88 + 30 * k, 286, 22 * k), 99, 286) for k in range(8)],
]
# The same map title shows a region (scouting) by strcpy from its own pointer table 0x47e2b0
# (read only by 0x195890, called only from the title code at 0x1a9764), so "Kanto" ran into
# "Last show" as the prefectures did. The table gets copies padded to the title's 10 bytes.
REGION_TABLE = 0x47e2b0
REGION_TITLES = ['Hokkaido', 'Tohoku', 'Kanto', 'Koshinetsu', 'Tokai', 'Kinki', 'Chugoku',
                 'Shikoku', 'Kyushu']
TITLE_BYTES = 10


def step(path, files):
    exe = files.get(EXE)
    for a, old, new, room in STRINGS:
        o = exefile.off(a)
        ob, nb = old.encode('cp932'), new.encode('cp932')
        if exe[o:o + len(ob) + 1] != ob + b'\0':
            raise SystemExit(f'screens: the string at {a:#x} is not {old!r}')
        if len(nb) + 1 > room or any(exe[o + len(ob):o + room]):
            raise SystemExit(f'screens: {new!r} does not fit at {a:#x}')
        exe[o:o + room] = nb + bytes(room - len(nb))
    for a, orig, w, u in SPRITES:
        o = exefile.off(a) + 8
        got = struct.unpack_from('<6H', exe, o)
        if got != orig:
            raise SystemExit(f'screens: the sprite at {a:#x} is {got}, not {orig}')
        struct.pack_into('<H', exe, o, w)
        struct.pack_into('<H', exe, o + 8, u)
    if exefile.refs(exe, REGION_TABLE) != [(0x195894, 0x195898)]:
        raise SystemExit('screens: the region title table is used somewhere else too')
    blob = b''.join(t.ljust(TITLE_BYTES).encode('ascii') + bytes(2) for t in REGION_TITLES)
    exe, at = exefile.alloc(exe, blob)
    exe = bytearray(exe)
    for k in range(len(REGION_TITLES)):
        struct.pack_into('<I', exe, exefile.off(REGION_TABLE) + 4 * k, at + (TITLE_BYTES + 2) * k)
    files.put(EXE, exe)
    print(f'screens: {len(STRINGS)} strings, {len(SPRITES)} sprites, region titles at {at:#x}')
