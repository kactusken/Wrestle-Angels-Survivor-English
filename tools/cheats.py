#!/usr/bin/env python3
"""Test cheats for management mode: a PCSX2 .pnach file to make rare events happen on demand.

  cheats.py [ISO] [--out DIR]    write <DIR>/SLPM-66239_<CRC>.pnach for the build ISO
                                 (default: the newest build/*.iso, into build/cheats/)

Made for testing the translation and shipped with the release (make_patches.py writes one per
patch and one for the original game). PCSX2 finds a cheat file by the executable's CRC (the XOR of
its 32-bit words), which changes with every build, so write a new file for each build. Copy it into PCSX2's `cheats` folder, then turn single cheats on and off in the game's
Properties > Cheats while playing (each [section] below is one cheat).

Addresses (*from the code*; docs/MANAGEMENT.md):
- event chances: words at 0x486030, each used as `rand() % 100 < value`, so 100 = always
  (the event's own conditions still apply);
- promotion slot s: 0x82aef0 + 0x15434 s + 0x44 (0x1951e0); player 1 is taken to be slot 0 -
  "Money" shows at once on the office screen whether that is right;
- AP (money): +0x24, signed;
- wrestler n (0-15): +0x19d0 + 0xec4 n; trust +0xd72 (byte), morale +0xd76 (u16), age +0xd78
  (u16), popularity +0xd7c (float);
- year 0x82aef2, month 0x82aef3 (bytes).
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import paths  # noqa: E402

EXE = '/SLPM_662.39'
CHANCES = 0x486030
PROMO = 0x82aef0 + 0x44                 # slot 0
AP = PROMO + 0x24
WRESTLER = PROMO + 0x19d0
WSIZE = 0xec4
MONTH = 0x82aef3
GALLERY, GALLERY_CRC = 0x8b5e48, 0x8b5fd8   # 400 seen flags (bit 0 each), CRC-32 of them
MASTER = 0x8baf70                            # wrestler master records, 0x1d0 each

# chance table index -> what it rolls
CHANCE = {0: 'vacation scene', 1: 'photo book', 2: 'heartbreak', 3: 'fan club', 4: 'film offer',
          5: 'one-day police chief', 6: 'skipping practice', 7: 'goes missing',
          8: 'joins the Revolution Army', 9: 'New Japan guests', 10: 'partner guests',
          11: 'faction forms (1)', 12: 'faction forms (2)', 13: 'faction forms (3)'}
OVERSEAS = [15, 17, 19]                 # % a month by promotion rating (<2000, <4000, <10000)


def chance(i, value=100):
    return ('word', CHANCES + 4 * i, value)


def every_wrestler(offset, kind, value):
    return [(kind, WRESTLER + WSIZE * n + offset, value) for n in range(16)]


POP_99 = 0x42c60000                     # 99.0 as a float

# (section, description, [(type, address, value)])
CHEATS = [
    ('Money\\AP 99,999 (player 1)', 'Keeps your AP at 99,999 (player 1 in a one-player game).', [('word', AP, 99999)]),
    ('Money\\AP -100 (bankruptcy test)', 'Keeps your AP below zero: warnings in months 1 and 2, '
     'bankruptcy (game over in one-player games) in month 3. Save first.', [('word', AP, -100 & 0xffffffff)]),
    ('Wrestlers\\Popularity 99 + morale 99 (all)', 'Meets the conditions of the media events '
     '(fan club, film, photo book, police chief) for every wrestler.',
     every_wrestler(0xd7c, 'word', POP_99) + every_wrestler(0xd76, 'short', 99)),
    ('Wrestlers\\Morale 20 (all)', 'Low morale: alignment drifts toward EVIL; with 2+ EVIL '
     'wrestlers the Rebel Army can form.', every_wrestler(0xd76, 'short', 20)),
    ('Wrestlers\\Trust 3 (all)', 'Low trust: skipping practice, thinking of leaving, going missing.',
     every_wrestler(0xd72, 'byte', 3)),
    ('Wrestlers\\Trust 0 (all)', 'Trust 0: wrestlers ask to leave (10 % a month each, more with '
     'Events\\Always). Save first.', every_wrestler(0xd72, 'byte', 0)),
    ('Wrestlers\\Age 27 (all)', 'Retirement at the next month change, with the ceremony at the '
     "month's last show. Save first.", every_wrestler(0xd78, 'short', 27)),
    *[(f'Events\\Always: {name}', f'The {name} roll always succeeds (its other conditions '
       'still apply).', [chance(i)]) for i, name in CHANCE.items()],
    ('Events\\Always: faction forms (all three)', 'Every faction-forming roll succeeds (needs 6+ '
     'or 8+ wrestlers and the age/alignment/morale conditions).', [chance(i) for i in (11, 12, 13)]),
    ('Events\\Always: wrestler moves abroad', 'A wrestler (no title, trust 80 or less) leaves for an '
     'overseas promotion. Needs 6+ wrestlers.', [chance(i) for i in OVERSEAS]),
    ('Events\\Never: random events', 'Turns off every roll above, for quiet testing of other things.',
     [chance(i, 0) for i in CHANCE] + [chance(i, 0) for i in OVERSEAS]),
    # --- hidden content (docs/HIDDEN_CONTENT.md) ---
    ('Gallery\\Unlock everything (save once to keep)', 'Sets all 400 gallery flags and their '
     'CRC-32 (the game wipes the flags if the CRC is wrong). Save once with it on and the gallery '
     'stays complete in that save.', [('word', GALLERY + 4 * i, 0x01010101) for i in range(100)]
     + [('word', GALLERY_CRC, 0x86D31D37)]),
    ('Gallery\\Show everything (nothing saved)', 'Code patch: the gallery treats every picture as '
     'seen while this is on; the save is not changed.',
     [('word', 0x22B84C, 0x1000000A), ('word', 0x22B8A0, 0x24020001)]),
    ('Roster\\Sophie and Holly Sierra in management', 'The only two wrestlers management never '
     'uses: puts them in a foreign roster in place of Yun / Shu Meifa. On before New Game.',
     [('short', 0x4A6320, 236), ('short', 0x4A632C, 336)]),
    ('Roster\\All 2P alternates from year 1', 'The 52 alternates normally debut in years 3-11 '
     '(four only after the Final Series); this makes them tryout/scouting candidates from year 1. '
     'On before New Game.', [('byte', MASTER + 0x1D0 * (rid - 33) + 0x115, 1) for rid in range(101, 153)]),
    *[(f'Hidden\\Gym Talk plays: {name} (one at a time)', f'Gym > Talk plays script entry {e} for '
       f'the chosen wrestler instead of the talk scene. {note}', [('word', 0x181FFC, 0x24040000 | e)])
      for e, name, note in [
          (305, 'Expression check', "A developer test: the wrestler's five face crops (Normal, "
           'Happy, Angry, Sad, Bashful).'),
          (164, 'left the Revolution (unused)', '120 voiced lines nothing plays.'),
          (186, 'back from tour (unused)', '120 voiced lines nothing plays.'),
          (319, 'staff roll', 'The ending credits.')]],
    ('Hidden\\Title menu: show the cut Team Event slot', "The title carousel's skipped slot 4 "
     '(団体戦 / TEAM EVENT banners); choosing it does nothing.',
     [('word', 0x16C338, 0x2402000F), ('word', 0x16C40C, 0x2402000F)]),
    ('Calendar\\Month = November (turn off again!)', 'Jumps to November so December (EX Tag '
     'League) and January (awards) come soon. Turn it on, end the month once, turn it off.',
     [('byte', MONTH, 11)]),
]


def crc(elf):
    """PCSX2's game CRC: the XOR of the executable's 32-bit words."""
    c = 0
    for i in range(0, len(elf) - len(elf) % 4, 4):
        c ^= int.from_bytes(elf[i:i + 4], 'little')
    return c


def pnach(game_crc):
    out = ['gametitle=Wrestle Angels Survivor (SLPM-66239)',
           f'comment=Cheats for the executable with CRC {game_crc:08X} (the Wrestle Angels Survivor English '
           'Patch project); turn single cheats on in the game properties', '']
    for name, desc, lines in CHEATS:
        out += [f'[{name}]', f'description={desc}']
        out += [f'patch=1,EE,{a:08X},{kind},{v & 0xffffffff:08X}' for kind, a, v in lines]
        out.append('')
    return '\n'.join(out)


def write(out, game_crc):
    """Write the cheat file for an executable CRC into folder out; returns its path."""
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    f = out / f'SLPM-66239_{game_crc:08X}.pnach'
    f.write_text(pnach(game_crc), encoding='utf-8')
    return f


def main(argv=None):
    argv = paths.configure(sys.argv[1:] if argv is None else argv)
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('iso', nargs='?')
    ap.add_argument('--out')
    args = ap.parse_args(argv)
    import disc
    iso = Path(args.iso) if args.iso else max(paths.BUILD.glob('*.iso'), key=lambda p: p.stat().st_mtime)
    d = disc.Disc(str(iso))
    game_crc = crc(d.read_file(d.find(EXE)))
    f = write(args.out or paths.BUILD / 'cheats', game_crc)
    print(f'cheats: {iso.name} -> {f} ({len(CHEATS)} cheats)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
