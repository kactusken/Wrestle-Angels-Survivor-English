#!/usr/bin/env python3
"""Build the translated image from the original. Standard library only.

  python3 build.py [--name NAME] [--unlocks all|none|GROUP,...] [--clean]
      -> build/NAME.<ext> (default NAME: "<game> (English)")

Steps (default folders shown; move any of them with the folder options - see --help):
  1. verify the original in rom/ (size + SHA-1; --skip-verify skips the hash)
  2. prepare build/NAME: a fresh copy of the original, or - much faster for big images - the last
     build with every range it wrote restored from the original (tools/image.py; --clean copies)
  3. text: translation/script/ and translation/text/ into the game's files (TEXT_STEPS)
  4. code patches picked by --unlocks (CODE_PATCHES, tools/codepatch.py)
  5. images: for every catalogued image the English file the catalogue picks (hand-made >
     approved > rendered), imported by tools/gfx.py; the final set is copied to review/images-english/
  6. write every changed file back into the image (files that fit in place first)

Test builds: --boot PART starts the game straight in PART (BOOT_PATCHES, once known);
--no-translation skips text and images, and gameplay patches unless --unlocks is given - on its
own the result is byte-identical to the original (tools/check.py --control proves it).
Developer flags (never for releases): --no-text FILE skips one text file.
"""
import argparse
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / 'tools'))
import catalog  # noqa: E402
import codepatch  # noqa: E402
import disc  # noqa: E402
import exefile  # noqa: E402
import gfx  # noqa: E402
import image  # noqa: E402
import paths  # noqa: E402
import unlocks  # noqa: E402

# Gameplay patches: (group, file, address, original, new, description) - see tools/codepatch.py.
# Unlocks that change data instead are in tools/unlocks.py (DATA_UNLOCKS); docs/PATCHES.md.
CODE_PATCHES = [
    # The gallery (0x22b810) wipes its seen-flags when their CRC is wrong and shows a cell only if
    # its flag is set: skip the CRC check's branch and read every flag as set.
    ('gallery', '/SLPM_662.39', 0x22b84c, 0x1202000a, 0x1000000a, 'Gallery: every picture shown'),
    ('gallery', '/SLPM_662.39', 0x22b8a0, 0x90420008, 0x24020001, None),     # lbu v0,8(v0) -> li v0,1
]
UNLOCK_GROUPS = sorted({p[0] for p in CODE_PATCHES} | set(unlocks.DATA_UNLOCKS))

# --boot: (part, file, address, original, new) - patches that start the game in a given part.
# Game flow: task 0x16b2a0, state word 0x594d34 (0 boot, 1 logos/movie/title, 2 new game, 3 office,
# 4 script player); the title part's substate is set at 0x16ca60 (2 = logos) and 0x16cd58 (7 = movie).
BOOT_PATCHES = {
    'title': [('/SLPM_662.39', 0x16ca60, 0x24020002, 0x24020008)],     # skip the logos and the movie
    'nomovie': [('/SLPM_662.39', 0x16cd58, 0x24020007, 0x24020008)],   # logos, but no opening movie
}


def to_offset(name, addr):
    """File offset of a RAM address in file `name`: only the executable has code patches."""
    if name == '/SLPM_662.39':
        return exefile.off(addr)
    raise SystemExit(f'build.py to_offset(): no address mapping for {name}')


# Text steps: (text file or folder under translation/, function(path, files)). Each inserts the
# English into the game's files through `files` and stops with a clear message if anything doesn't fit.
# Zero-padding files a grown file may take room from when the disc is full (PS2 disc.py
# take_from_padding: their end is cut off) - e.g. ['/DUMMY.DAT']; check they are all zeros.
PADDING_DONORS = []

def script_step(path, files):
    import script
    script.step(path, files)


def roster_step(path, files):
    import roster
    roster.step(path, files)


def exetext_step(path, files):
    import exetext
    exetext.apply(path, files)


def quotes_step(path, files):
    import quotes
    quotes.step(path, files)


def infopage_step(path, files):
    import infopage
    infopage.step(path, files)


def announce_step(path, files):
    import announcer
    announcer.step(path, files)


def menu_sprites_step(path, files):
    import menu_sprites
    menu_sprites.step(path, files)


def venues_step(path, files):
    import venues
    venues.step(path, files)


def screens_step(path, files):
    import screens
    screens.step(path, files)


TEXT_STEPS = [
    ('script', script_step),        # event scripts: the LZ archive in the executable
    ('text/roster.csv', roster_step),   # wrestler/coach names and finishers (records)
    ('text/exe.csv', exetext_step),     # the executable's own strings
    ('script/quotes.txt', quotes_step),  # pre-match quotes (/A040/A048.)
    ('text/infopage', infopage_step),   # info screen / roster list layout for English values
    ('text/screens', screens_step),     # map title and rankings rows: room for English values
    ('text/venues.csv', venues_step),   # venue names (an LZ archive in the executable)
    ('text/menu_sprites', menu_sprites_step),  # office menu highlights as wide as the English
    ('text/announcer.csv', announce_step),  # ring announcer's lines before a match
]


class Files:
    """The game's files for this build: read from the image on first use, written back at the end."""

    def __init__(self, d):
        self.d, self.data, self.changed = d, {}, set()

    def get(self, name):
        if name not in self.data:
            self.data[name] = bytearray(self.d.read_file(self.d.find(name)))
        return self.data[name]

    def put(self, name, data):
        self.data[name] = bytearray(data)
        self.changed.add(name)


def unlock_groups(value):
    if value == 'all':
        return set(UNLOCK_GROUPS)
    if value == 'none':
        return set()
    groups = {g.strip() for g in value.split(',') if g.strip()}
    if groups - set(UNLOCK_GROUPS):
        raise argparse.ArgumentTypeError(f'expected all, none or some of {",".join(UNLOCK_GROUPS) or "(no groups yet)"}')
    return groups


def images_step(files):
    final = catalog.final_images()
    missing, changed, _ = catalog.stale()
    if missing or changed:
        print(f'note: {len(missing) + len(changed)} automatic renders are out of date - run tools/render.py '
              f'(building with the frozen files there are)')
    n = gfx.import_images({k: p for k, (tag, p) in final.items()}, files)
    if paths.ENGLISH_IMAGES.exists():
        shutil.rmtree(paths.ENGLISH_IMAGES)
    if final:
        paths.ENGLISH_IMAGES.mkdir(parents=True)
        for name, (tag, p) in final.items():
            shutil.copyfile(p, paths.ENGLISH_IMAGES / f'{name}.png')
        counts = {}
        for tag, _ in final.values():
            counts[tag] = counts.get(tag, 0) + 1
        print(f'images: {n} imported (' + ', '.join(f'{c} {t}' for t, c in sorted(counts.items())) + ')')


def verify_original(original):
    """SHA-1 of the original image, once: the result is remembered with the file's size and
    modification time (build/original.verified), so later builds only re-hash a changed file
    (a DVD image takes ~20 s to hash)."""
    st = original.stat()
    stamp = f'{original.resolve()} {st.st_size} {st.st_mtime_ns} {paths.ORIGINAL["sha1"]}'
    memo = paths.BUILD / 'original.verified'
    if memo.exists() and memo.read_text() == stamp:
        return
    print('verifying the original...')
    if image.sha1(original) != paths.ORIGINAL['sha1']:
        sys.exit(f'{original.name} does not match the expected SHA-1 {paths.ORIGINAL["sha1"]}')
    paths.BUILD.mkdir(parents=True, exist_ok=True)
    memo.write_text(stamp)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0], epilog=paths.FOLDER_HELP,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--name', default=f'{paths.GAME_FILE} (English)')
    ap.add_argument('--skip-verify', action='store_true', help="don't hash the original image")
    ap.add_argument('--clean', action='store_true', help='copy the original instead of restoring the last build')
    ap.add_argument('--no-translation', action='store_true', help='skip text and images (alone: identical to the original)')
    ap.add_argument('--unlocks', type=unlock_groups, metavar='all|none|GROUP,...',
                    help='gameplay patches: all (default), none or some groups; none with --no-translation')
    ap.add_argument('--boot', choices=sorted(BOOT_PATCHES), help='TEST BUILD: start the game in this part')
    ap.add_argument('--no-text', action='append', default=[], metavar='FILE',
                    help='developer: leave this text file untranslated (repeatable)')
    args = ap.parse_args(paths.configure(sys.argv[1:] if argv is None else argv))
    if args.unlocks is None:
        args.unlocks = set() if args.no_translation else set(UNLOCK_GROUPS)

    original = paths.ROM
    if not original.exists():
        sys.exit(f'put the original image in {paths.show(paths.ROM_DIR)} (or pass --rom): {paths.ORIGINAL_NAME}')
    if original.stat().st_size != paths.ORIGINAL['size']:
        sys.exit(f'{original.name}: {original.stat().st_size} bytes, expected {paths.ORIGINAL["size"]} - not the right image')
    if not args.skip_verify:
        verify_original(original)

    out = paths.BUILD / (args.name + original.suffix)
    with image.prepare(original, out, clean=args.clean) as f:
        d = disc.Disc(f, writable=True)
        files = Files(d)

        if not args.no_translation:
            for rel, step in TEXT_STEPS:
                if rel in args.no_text:
                    print(f'text: skipped {rel} (--no-text)')
                    continue
                step(paths.TRANSLATION / rel, files)

        codepatch.apply(files, CODE_PATCHES, args.unlocks, to_offset)
        unlocks.apply(files, args.unlocks)

        if not args.no_translation:
            images_step(files)

        if args.boot:
            codepatch.apply(files, [(args.boot, *p, f'TEST BUILD: boots into {args.boot}') for p in BOOT_PATCHES[args.boot]],
                            {args.boot}, to_offset)

        def fits(name):
            return (len(files.data[name]) + disc.SECTOR - 1) // disc.SECTOR <= d.allocated_sectors(d.find(name))
        for name in sorted(files.changed, key=lambda n: (not fits(n), n)):  # fixed order: same disc layout every build
            d.write_file(d.find(name), bytes(files.data[name]), relocate=True,
                         **({'donors': PADDING_DONORS} if PADDING_DONORS else {}))
            print(f'patched {name}')
    disc.companion_files(out)
    print(f'done: {paths.show(out)}  ({len(files.changed)} files patched)')
    return out


if __name__ == '__main__':
    main()
