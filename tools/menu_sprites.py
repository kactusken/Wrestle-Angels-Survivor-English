#!/usr/bin/env python3
"""Office and training menus: highlight sprites wide enough for the English (a build step).

*From the executable's data* (not yet confirmed in game): the menus of /A000/A00A. are drawn as
whole panels (blue labels, A00A_p0_0 / A00A_p1_0), and the selected item is highlighted by a white
copy of its label drawn over it - one 24-byte sprite per item (u32, u32, u16 w, h, screen x, y,
texture u, v) in tables at 0x491e70 (main menu), 0x491f00 (Staff), 0x491fc0 (Business), 0x492070
(Info), 0x4920d0 (system menu), 0x492190 (training), 0x492220 (training plans), 0x4922e0 (move
changes), 0x492340 (move types), 0x4923c0 (coach menu). Each sprite was cut to the Japanese
label, so a longer English label was only partly white (test: "Expand Facili" white, "ties"
blue). Each sprite below grows to the white English ink of translation/images-handmade/A00A_p*_0
(right, left and down for descenders): where u moves left, screen x moves with it so the white
copy still lies on the blue one. No other label's ink falls inside any new rectangle (checked
against the lettered sheets; "Change Difficulty" starts at u 386 because "Remove Wrestler" ends at
384 beside it). Labels that already fit are left alone.

If the lettering of A00A_p0_0 / A00A_p1_0 changes, re-measure these rectangles.

  menu_sprites.py           apply to extracted/SLPM_662.39 in memory and report (writes nothing)
  menu_sprites.py --out F   also write the patched executable to F
"""
import argparse
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import exefile  # noqa: E402
import paths  # noqa: E402

EXE = '/SLPM_662.39'
HEADER = (0x65322304, 0x20000006)       # the first two words of every sprite in these tables
# (sprite address, original (w, h, x, y, u, v), new)
SPRITES = [
    (0x491e88, (59, 21, 165, 111, 306, 217), (67, 21, 160, 111, 301, 217)),  # Business
    (0x491eb8, (59, 21, 166, 159, 307, 265), (59, 23, 166, 159, 307, 265)),  # Gym
    (0x491ee8, (60, 21, 165, 207, 306, 313), (76, 21, 156, 207, 297, 313)),  # End Month
    (0x491f00, (105, 21, 264, 94, 328, 1), (105, 23, 264, 94, 328, 1)),      # Tryout
    (0x491f18, (125, 21, 264, 118, 328, 25), (125, 23, 264, 118, 328, 25)),  # Scouting
    (0x491f30, (88, 21, 264, 142, 328, 49), (109, 21, 264, 142, 328, 49)),   # Transfer Talks
    (0x491f48, (87, 21, 265, 166, 329, 73), (126, 21, 264, 166, 328, 73)),   # Release Wrestler
    (0x491f60, (104, 20, 265, 191, 329, 98), (105, 20, 264, 191, 328, 98)),  # Hire Coach
    (0x491f78, (105, 21, 265, 214, 329, 121), (109, 21, 264, 214, 328, 121)), # Dismiss Coach
    (0x491f90, (87, 21, 264, 238, 328, 145), (92, 21, 264, 238, 328, 145)),  # Tour Abroad
    (0x491fc0, (86, 21, 265, 94, 405, 289), (88, 23, 264, 94, 404, 289)),    # Partnership
    (0x491fd8, (87, 21, 265, 118, 405, 313), (106, 23, 265, 118, 405, 313)), # Expand Facilities
    (0x492020, (84, 21, 264, 190, 404, 385), (87, 23, 264, 190, 404, 385)),  # Autographs
    (0x492038, (43, 21, 264, 214, 404, 409), (72, 21, 264, 214, 404, 409)),  # Advertise
    (0x492050, (79, 21, 264, 238, 404, 433), (102, 21, 264, 238, 404, 433)), # TV Broadcast
    (0x492070, (105, 21, 265, 94, 369, 193), (116, 21, 265, 94, 369, 193)),  # Promotion Data
    (0x4920a0, (105, 21, 264, 142, 368, 241), (105, 23, 264, 142, 368, 241)), # Rankings
    (0x4920b8, (85, 21, 265, 166, 369, 265), (104, 22, 265, 166, 369, 265)), # Influence Map
    (0x4920e8, (60, 21, 276, 145, 299, 361), (62, 21, 274, 145, 297, 361)),  # Load
    (0x492100, (100, 21, 275, 169, 298, 385), (100, 23, 275, 169, 298, 385)), # Options
    (0x492118, (87, 21, 274, 193, 297, 409), (103, 23, 274, 193, 297, 409)), # Change Years
    (0x4921a8, (78, 21, 156, 111, 297, 25), (78, 23, 156, 111, 297, 25)),    # Group
    (0x4921c0, (59, 21, 165, 135, 306, 49), (59, 23, 165, 135, 306, 49)),    # Special
    (0x4921f0, (62, 20, 164, 184, 305, 98), (64, 20, 164, 184, 305, 98)),    # Coaches
    (0x492220, (118, 21, 155, 87, 376, 1), (118, 23, 155, 87, 376, 1)),      # Develop Style
    (0x492238, (129, 21, 156, 111, 377, 25), (130, 21, 155, 111, 376, 25)),  # Fix Weakness
    (0x492250, (118, 21, 155, 135, 376, 49), (118, 23, 155, 135, 376, 49)),  # Basics Training
    (0x492268, (118, 21, 155, 159, 376, 73), (125, 23, 155, 159, 376, 73)),  # Offense Training
    (0x492280, (117, 21, 156, 183, 377, 97), (127, 23, 155, 183, 376, 97)),  # Defense Training
    (0x492298, (65, 21, 155, 207, 376, 121), (105, 21, 155, 207, 376, 121)), # Move Practice
    (0x4922b0, (44, 21, 155, 231, 376, 145), (67, 21, 155, 231, 376, 145)),  # Vacation
    (0x4922c8, (114, 21, 155, 255, 376, 169), (130, 23, 155, 255, 376, 169)), # Category Practice
    (0x4922e0, (118, 21, 283, 94, 384, 361), (125, 23, 285, 94, 386, 361)),  # Change Difficulty
    (0x4922f8, (109, 21, 283, 118, 384, 385), (123, 23, 283, 118, 384, 385)), # Change Finisher
    (0x492310, (87, 21, 283, 142, 384, 409), (122, 21, 283, 142, 384, 409)), # Learn New Move
    (0x492328, (87, 21, 283, 166, 384, 433), (103, 21, 283, 166, 384, 433)), # Rename Move
    (0x4923c0, (118, 21, 283, 94, 264, 337), (121, 23, 283, 94, 264, 337)),  # Change Wrestlers
    (0x4923d8, (119, 21, 283, 118, 264, 361), (121, 21, 283, 118, 264, 361)), # Remove Wrestler
]


def patch(exe):
    """Patch the sprites in exe (a bytearray) in place; refuses an executable that differs."""
    for a, old, new in SPRITES:
        o = exefile.off(a)
        if struct.unpack_from('<2I', exe, o) != HEADER or struct.unpack_from('<6H', exe, o + 8) != old:
            raise SystemExit(f'menu_sprites: the sprite at {a:#x} is not {old} - '
                             'wrong executable, or patched twice')
        struct.pack_into('<6H', exe, o + 8, *new)
    return len(SPRITES)


def step(path, files):
    exe = bytearray(files.get(EXE))
    n = patch(exe)
    files.put(EXE, exe)
    print(f'menu_sprites: {n} highlight sprites widened')


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--out', help='write the patched executable here')
    args = ap.parse_args(paths.configure(sys.argv[1:] if argv is None else argv))
    src = paths.EXTRACTED / EXE.lstrip('/')
    exe = bytearray(src.read_bytes())
    n = patch(exe)
    print(f'menu_sprites: {n} sprites patch cleanly in {paths.show(src)}')
    if args.out:
        Path(args.out).write_bytes(exe)
        print(f'menu_sprites: wrote {args.out}')


if __name__ == '__main__':
    main()
