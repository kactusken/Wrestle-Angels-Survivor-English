# Patches

What the build changes besides text and images, one section per patch: what the original code
does, what changed, why it works, the tool that makes it, limits to respect, and whether it was
*verified in game*.

Unlock groups (`build.py --unlocks`): the plain English patch has none; the "Unlocked" patches
(English and Japanese) have all. Translated builds include all by default. Not yet *verified in
game*.

## gallery: every picture shown
- **Original** (*from the code* 0x22b810): the gallery keeps 400 seen-flags at 0x8b5e48 (photo
  books, vacation scenes) with a CRC-32 at 0x8b5fd8. On opening it recomputes the CRC and wipes
  every flag if it doesn't match (branch at 0x22b84c), then shows a cell only if its flag is set
  (`lbu v0, 8(v0)` at 0x22b8a0).
- **Change:** 0x22b84c `beq` -> `b` (the check never wipes) and 0x22b8a0 `lbu v0, 8(v0)` ->
  `li v0, 1` (every cell counts as seen). build.py CODE_PATCHES, group `gallery`.
- **Limits:** the save's flags are untouched, so removing the patch brings back the earned
  gallery.

## alternates: the 2P alternates from year 1
- **Original** (*from the code* 0x19a7c4): each roster record holds a debut year after its
  moveset (post byte 12, master +0x115); the tryout/scouting pool takes a rookie once the years
  elapsed reach debut year - 1. The 52 domestic 2P alternates (ids 101-152) have years 3-11.
- **Change:** their debut year is set to 1 in the records (tools/unlocks.py, group
  `alternates`), found through the record table and the blob address at 0x1947ec, so it works on
  the original records and the English ones. They are then candidates from year 1; finding them
  still depends on the tryout/scouting roll and region.
- **Limits:** a new game is needed (the records are read at New Game).
