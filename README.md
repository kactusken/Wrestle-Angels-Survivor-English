# Wrestle Angels Survivor — English Translation

An English translation patch for **Wrestle Angels Survivor** (Success, 2006, PlayStation 2,
released only in Japan), the women's wrestling promotion-management game.

It translates the whole game: all 8,348 event messages, the menus and help text, the 206
wrestlers' names, finishers, nicknames and voiced lines, 384 venues, the ring announcer and
pre-match quotes, and 911 pictures with Japanese lettering - menus, buttons, banners, match
screens, name strips and portraits. Screens the English didn't fit were rearranged in the game's
code (info pages, rankings, save slots, map titles, menu highlights).

> **Status: v0.1, first public release.** Tested in PCSX2 across exhibition (Special Match,
> Tournament, League) and management mode. Please report anything that looks wrong
> ([how to report](#reporting-problems)). [CHANGELOG.md](CHANGELOG.md) lists what's in each
> release.

## Downloads

Get the latest zip from the [Releases](../../releases) page. It contains three patches - pick
one - and a folder of cheats:

| Patch | What you get |
|---|---|
| **Wrestle Angels Survivor (English)** | The translation, with the game otherwise unchanged. |
| **Wrestle Angels Survivor (English) (Unlocked)** | The translation, and the gallery shows every picture from the start, and the 52 alternate ("2P") wrestlers can be found in tryouts and scouting from the first year of management mode instead of years 3-11. |
| **Wrestle Angels Survivor (Japan) (Unlocked)** | The original Japanese game with the same unlocks. |
| **cheats/** | PCSX2 cheat files for each patch and for the original game: money, wrestler stats, every random event on or off, the full gallery, and hidden scenes. Copy them into PCSX2's `cheats` folder and tick cheats in the game's Properties > Cheats. |

## How to patch

You need your own copy of the original Japanese disc. Disc images are not provided here.

- Game: *Wrestle Angels Survivor* (Japan), serial SLPM-66239. The budget "Good Price" reissue
  (SLPM-66927) is a different image and has not been tested; the patches won't apply to it.
- The image must match: `Wrestle Angels Survivor (Japan).iso`, 2396487680 bytes, CRC32 `484c321b`,
  SHA-1 `8f7f823bdae30bfa0431714c4c0bced83b9e51bb`.

Then:

1. Apply the `.xdelta` patch with an xdelta tool:
   - Delta Patcher, a desktop app for Windows, macOS and Linux (the easiest for a DVD image this
     size).
   - On the command line: `xdelta3 -d -s "Wrestle Angels Survivor (Japan).iso" "patch.xdelta" "patched.iso"`
   - [Rom Patcher JS](https://www.marcrobledo.com/RomPatcher.js/) in a web browser may not cope
     with a 2.4 GB image.
2. Open the patched image in your emulator. Tested in PCSX2.

> **PCSX2: the opening movie can crash the game.** This is a known PCSX2 issue with this game, the original Japanese version included (https://github.com/PCSX2/pcsx2/issues/12179). Press START as soon as the movie begins to skip it, or set the EE Cycle Rate to 50% (underclock) before the movie plays and put it back afterwards.

## Notes for players

- **Names.** Western order (given name first). Ring names stay as ring names; the rival
  promotions use the spellings on their own logos. Names that also appear in Wrestle Angels
  Survivor 2 match its English translation.
- **What's still in Japanese.** Logos and the opening movie, the voices, the staff credits, the
  kana side of the name-entry keyboard, and the Japanese name at the top of each wrestler's face
  picture (the English name is added along the bottom, so the art isn't cut).
- **Saves.** Saves made with the original Japanese game have not been tested with the patch;
  starting a new save is safest.
- **Hidden content.** Hold R1 during events to hide the message window. More - a cut game mode,
  unused scenes and pictures, two wrestlers management mode never uses - in
  [docs/HIDDEN_CONTENT.md](docs/HIDDEN_CONTENT.md).
- **How management mode works.** [docs/MANAGEMENT.md](docs/MANAGEMENT.md) explains the systems,
  events, endings and strategy.

## Reporting problems

Open an [issue](../../issues) with:

- a screenshot,
- which patch you used,
- where you were: the mode and menu, or roughly what had just happened.

Text that is cut off, overlaps, or still shows Japanese is especially helpful.

## For ROM hackers and contributors

Everything needed to rebuild the patches from the original disc is in this repository: the
translated text, the patching code (Python 3, no dependencies for the build) and documentation of
the game's formats.

| Document | What's in it |
|---|---|
| [docs/BUILDING.md](docs/BUILDING.md) | Setting up, building, making patches, and the checking tools |
| [docs/TRANSLATION.md](docs/TRANSLATION.md) | Text file formats, scope, style guide, glossary, and naming decisions |
| [docs/EDITING.md](docs/EDITING.md) | Editing the in-game text graphics |
| [docs/PATCHES.md](docs/PATCHES.md) | How each code patch works |
| [docs/TECHNICAL.md](docs/TECHNICAL.md) | The game's disc layout, archives, compression, data formats, and memory map |
| [docs/PLATFORM.md](docs/PLATFORM.md) | PS2 pitfalls for this kind of work |
| [docs/MANAGEMENT.md](docs/MANAGEMENT.md) | How management mode works, from the code |
| [docs/HIDDEN_CONTENT.md](docs/HIDDEN_CONTENT.md) | Unlockables, debug features, and unused and cut content |
| [docs/EVENT_TESTING.md](docs/EVENT_TESTING.md) | Making rare events happen with the test cheats |
| [tools/README.md](tools/README.md) | Every tool, what it's for and how to run it |

Quick start:

```sh
python3 tools/extract.py                 # unpack the disc in rom/ into extracted/
python3 build.py                         # -> build/Wrestle Angels Survivor (English).iso
python3 make_patches.py --version v0.1   # -> release/*.xdelta and a zip (needs xdelta3)
```

## AI disclosure

AI assisted with the translation.

## Legal

This is a non-commercial fan translation, not affiliated with or endorsed by the game's developers
or publishers. It contains no copyrighted game data that would let
anyone play without owning the game. The patches only work on your own copy of the disc.
Wrestle Angels Survivor and its contents belong to their respective owners. The Japanese text in this
repository is included for translation and reference.

The code in this repository is released under the [MIT License](LICENSE).
