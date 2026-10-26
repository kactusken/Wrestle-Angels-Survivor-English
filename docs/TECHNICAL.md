# Technical notes - Wrestle Angels Survivor

**Conventions:** numbers in hex with `0x`; addresses are RAM addresses unless marked as file
offsets; `u16`/`u32` little-endian unless marked BE. Findings are marked *verified in game* or
*from the code*.

## Contents
- [Image](#image) · [Disc layout](#disc-layout) · [Executable and memory](#executable-and-memory)
- [Archives and compression](#archives-and-compression) · [Text](#text) · [Images](#images)
- [Open questions](#open-questions)

## Image
`Wrestle Angels Survivor (Japan).iso`, 2396487680 bytes, SHA-1 `8f7f823bdae30bfa0431714c4c0bced83b9e51bb`.

## Disc layout
| LBA | Size | File | Contents |
|---|---|---|---|
| 600000 | 54 | `/SYSTEM.CNF` |  |
| 600001 | 4745904 | `/SLPM_662.39` |  |
| 602319 | 33521 | `/MODULES/CDVDSTM.IRX` |  |
| 602336 | 68893 | `/MODULES/CRI_ADXI.IRX` |  |
| 602370 | 43856 | `/MODULES/EZMIDI.IRX` |  |
| 602392 | 278353 | `/MODULES/IOPRP310.IMG` |  |
| 602528 | 30085 | `/MODULES/LIBSD.IRX` |  |
| 602543 | 15280 | `/MODULES/LOAD.IRX` |  |
| 602551 | 103677 | `/MODULES/MCMAN.IRX` |  |
| 602602 | 7713 | `/MODULES/MCSERV.IRX` |  |
| 602606 | 63005 | `/MODULES/MODHSYN.IRX` |  |
| 602637 | 21941 | `/MODULES/MODMIDI.IRX` |  |
| 602648 | 13717 | `/MODULES/MODSESQ.IRX` |  |
| 602655 | 45925 | `/MODULES/PADMAN.IRX` |  |
| 602678 | 9161 | `/MODULES/SDRDRV.IRX` |  |
| 602683 | 5217 | `/MODULES/SIO2MAN.IRX` |  |
| 602686 | 256 | `/A000/A000.` |  |
| 602687 | 1931 | `/A000/A001.` |  |
| 602688 | 240910 | `/A000/A002.` |  |
| 602806 | 56972 | `/A000/A003.` |  |
| 602834 | 7098 | `/A000/A004.` |  |
| 602838 | 157176 | `/A000/A005.` |  |
| 602915 | 243821 | `/A000/A006.` |  |
| 603035 | 8718 | `/A000/A007.` |  |
| 603040 | 25780 | `/A000/A008.` |  |
| 603053 | 6926649 | `/A000/A009.` |  |
| 606436 | 184105 | `/A000/A00A.` |  |
| 606526 | 1635508 | `/A000/A00B.` |  |
| 607325 | 658564 | `/A000/A00C.` |  |
| 607647 | 236111 | `/A000/A00D.` |  |
| 607763 | 1426399 | `/A000/A00E.` |  |
| 608460 | 96954 | `/A000/A00F.` |  |
| 608508 | 101050 | `/A000/A010.` |  |
| 608558 | 20978132 | `/A000/A011.` |  |
| 618802 | 114593 | `/A000/A012.` |  |
| 618858 | 28890 | `/A000/A013.` |  |
| 618873 | 69801 | `/A000/A014.` |  |
| 618908 | 12005094 | `/A000/A015.` |  |
| 624770 | 6165529 | `/A000/A016.` |  |
| 627781 | 29607941 | `/A000/A017.` |  |
| 642239 | 12567678 | `/A000/A018.` |  |
| 648376 | 165409 | `/A000/A019.` |  |
| 648457 | 10986 | `/A000/A01A.` |  |
| 648463 | 25858061 | `/A000/A01B.` |  |
| 661090 | 1162583 | `/A000/A01C.` |  |
| 661658 | 66164 | `/A000/A01D.` |  |
| 661691 | 450532 | `/A000/A01E.` |  |
| 661911 | 152642 | `/A000/A01F.` |  |
| 661986 | 12859089 | `/A020/A020.` |  |
| 668265 | 12892585 | `/A020/A021.` |  |
| 674561 | 51233 | `/A020/A022.` |  |
| 674587 | 219110 | `/A020/A023.` |  |
| 674694 | 548779 | `/A020/A024.` |  |
| 674962 | 107333 | `/A020/A025.` |  |
| 675015 | 673183 | `/A020/A026.` |  |
| 675344 | 98995 | `/A020/A027.` |  |
| 675393 | 93419 | `/A020/A028.` |  |
| 675439 | 98077 | `/A020/A029.` |  |
| 675487 | 97216 | `/A020/A02A.` |  |
| 675535 | 93753 | `/A020/A02B.` |  |
| 675581 | 96033 | `/A020/A02C.` |  |
| 675628 | 97138 | `/A020/A02D.` |  |
| 675676 | 96412 | `/A020/A02E.` |  |
| 675724 | 96379 | `/A020/A02F.` |  |
| 675772 | 95504 | `/A020/A030.` |  |
| 675819 | 99408 | `/A020/A031.` |  |
| 675868 | 99377 | `/A020/A032.` |  |
| 675917 | 104527 | `/A020/A033.` |  |
| 675969 | 99545 | `/A020/A034.` |  |
| 676018 | 103854 | `/A020/A035.` |  |
| 676069 | 106562 | `/A020/A036.` |  |
| 676122 | 101594 | `/A020/A037.` |  |
| 676172 | 100983 | `/A020/A038.` |  |
| 676222 | 45532 | `/A020/A039.` |  |
| 676245 | 14650 | `/A020/A03A.` |  |
| 676253 | 84709 | `/A020/A03B.` |  |
| 676295 | 526301 | `/A020/A03C.` |  |
| 676552 | 1091138 | `/A020/A03D.` |  |
| 677085 | 476298 | `/A040/A040.` |  |
| 677318 | 420810 | `/A040/A041.` |  |
| 677524 | 213291 | `/A040/A042.` |  |
| 677629 | 365687 | `/A040/A043.` |  |
| 677808 | 3506504 | `/A040/A044.` |  |
| 679521 | 781458 | `/A040/A045.` |  |
| 679903 | 4063820 | `/A040/A046.` |  |
| 681888 | 131444 | `/A040/A047.` |  |
| 681953 | 5372 | `/A040/A048.` |  |
| 681956 | 33208 | `/A040/A049.` |  |
| 681973 | 179122 | `/A040/A04A.` |  |
| 682061 | 3904 | `/A060/A060.` |  |
| 682063 | 2320 | `/A060/A061.` |  |
| 682065 | 411248 | `/A060/A062.` |  |
| 682266 | 9664 | `/A060/A063.` |  |
| 682271 | 19712 | `/A060/A064.` |  |
| 682281 | 739344 | `/A060/A065.` |  |
| 682643 | 2912 | `/A060/A066.` |  |
| 682645 | 14160 | `/A060/A067.` |  |
| 682652 | 305360 | `/A060/A068.` |  |
| 682802 | 8928 | `/A060/A069.` |  |
| 682807 | 15568 | `/A060/A06A.` |  |
| 682815 | 792912 | `/A060/A06B.` |  |
| 683203 | 8912 | `/A060/A06C.` |  |
| 683208 | 14240 | `/A060/A06D.` |  |
| 683215 | 838272 | `/A060/A06E.` |  |
| 683625 | 9552 | `/A060/A06F.` |  |
| 683630 | 21984 | `/A060/A070.` |  |
| 683641 | 762672 | `/A060/A071.` |  |
| 684014 | 9040 | `/A060/A072.` |  |
| 684019 | 12304 | `/A060/A073.` |  |
| 684026 | 763552 | `/A060/A074.` |  |
| 684399 | 9760 | `/A060/A075.` |  |
| 684404 | 17888 | `/A060/A076.` |  |
| 684413 | 861200 | `/A060/A077.` |  |
| 684834 | 13328 | `/A060/A078.` |  |
| 684841 | 17792 | `/A060/A079.` |  |
| 684850 | 748768 | `/A060/A07A.` |  |
| 685216 | 7376 | `/A060/A07B.` |  |
| 685220 | 10512 | `/A060/A07C.` |  |
| 685226 | 674592 | `/A060/A07D.` |  |
| 685556 | 8256 | `/A060/A07E.` |  |
| 685561 | 21504 | `/A060/A07F.` |  |
| 685572 | 741072 | `/A080/A080.` |  |
| 685934 | 8000 | `/A080/A081.` |  |
| 685938 | 16416 | `/A080/A082.` |  |
| 685947 | 619424 | `/A080/A083.` |  |
| 686250 | 7456 | `/A080/A084.` |  |
| 686254 | 8704 | `/A080/A085.` |  |
| 686259 | 549472 | `/A080/A086.` |  |
| 686528 | 9456 | `/A080/A087.` |  |
| 686533 | 15744 | `/A080/A088.` |  |
| 686541 | 788720 | `/A080/A089.` |  |
| 686927 | 7456 | `/A080/A08A.` |  |
| 686931 | 14560 | `/A080/A08B.` |  |
| 686939 | 668176 | `/A080/A08C.` |  |
| 687266 | 7568 | `/A080/A08D.` |  |
| 687270 | 19168 | `/A080/A08E.` |  |
| 687280 | 781952 | `/A080/A08F.` |  |
| 687662 | 10512 | `/A080/A090.` |  |
| 687668 | 21264 | `/A080/A091.` |  |
| 687679 | 822816 | `/A080/A092.` |  |
| 688081 | 7920 | `/A080/A093.` |  |
| 688085 | 20224 | `/A080/A094.` |  |
| 688095 | 737152 | `/A080/A095.` |  |
| 688455 | 9776 | `/A080/A096.` |  |
| 688460 | 10880 | `/A080/A097.` |  |
| 688466 | 786832 | `/A080/A098.` |  |
| 688851 | 9360 | `/A080/A099.` |  |
| 688856 | 28784 | `/A080/A09A.` |  |
| 688871 | 942304 | `/A080/A09B.` |  |
| 689332 | 4144 | `/A080/A09C.` |  |
| 689335 | 7904 | `/A080/A09D.` |  |
| 689339 | 750400 | `/A080/A09E.` |  |
| 689706 | 4288 | `/A080/A09F.` |  |
| 689709 | 11072 | `/A0A0/A0A0.` |  |
| 689715 | 789104 | `/A0A0/A0A1.` |  |
| 690101 | 4336 | `/A0A0/A0A2.` |  |
| 690104 | 15744 | `/A0A0/A0A3.` |  |
| 690112 | 934688 | `/A0A0/A0A4.` |  |
| 690569 | 4208 | `/A0A0/A0A5.` |  |
| 690572 | 8688 | `/A0A0/A0A6.` |  |
| 690577 | 967632 | `/A0A0/A0A7.` |  |
| 691050 | 3360 | `/A0A0/A0A8.` |  |
| 691052 | 6608 | `/A0A0/A0A9.` |  |
| 691056 | 725440 | `/A0A0/A0AA.` |  |
| 691411 | 3904 | `/A0A0/A0AB.` |  |
| 691413 | 12048 | `/A0A0/A0AC.` |  |
| 691419 | 527824 | `/A0A0/A0AD.` |  |
| 691677 | 5088 | `/A0A0/A0AE.` |  |
| 691680 | 10768 | `/A0A0/A0AF.` |  |
| 691686 | 1121840 | `/A0A0/A0B0.` |  |
| 692234 | 4288 | `/A0A0/A0B1.` |  |
| 692237 | 10464 | `/A0A0/A0B2.` |  |
| 692243 | 970976 | `/A0A0/A0B3.` |  |
| 692718 | 5744 | `/A0A0/A0B4.` |  |
| 692721 | 10160 | `/A0A0/A0B5.` |  |
| 692726 | 1302864 | `/A0A0/A0B6.` |  |
| 693363 | 5776 | `/A0A0/A0B7.` |  |
| 693366 | 6928 | `/A0A0/A0B8.` |  |
| 693370 | 1098448 | `/A0A0/A0B9.` |  |
| 693907 | 3840 | `/A0A0/A0BA.` |  |
| 693909 | 13360 | `/A0A0/A0BB.` |  |
| 693916 | 763248 | `/A0A0/A0BC.` |  |
| 694289 | 3024 | `/A0A0/A0BD.` |  |
| 694291 | 11200 | `/A0A0/A0BE.` |  |
| 694297 | 662752 | `/A0A0/A0BF.` |  |
| 694621 | 3968 | `/A0C0/A0C0.` |  |
| 694623 | 9536 | `/A0C0/A0C1.` |  |
| 694628 | 552544 | `/A0C0/A0C2.` |  |
| 694898 | 4512 | `/A0C0/A0C3.` |  |
| 694901 | 8288 | `/A0C0/A0C4.` |  |
| 694906 | 1274800 | `/A0C0/A0C5.` |  |
| 695529 | 2448 | `/A0C0/A0C6.` |  |
| 695531 | 8912 | `/A0C0/A0C7.` |  |
| 695536 | 933520 | `/A0C0/A0C8.` |  |
| 695992 | 8128 | `/A0C0/A0C9.` |  |
| 695996 | 6832 | `/A0C0/A0CA.` |  |
| 696000 | 595008 | `/A0C0/A0CB.` |  |
| 696291 | 98697220 | `/A0E0/A0E0.` |  |
| 744484 | 863805440 | `/A980/A980.` |  |
| 1166264 | 7966720 | `/A980/A981.` |  |

The files have no names, only hex numbers; the executable lists them (`\A000\A000.;1` ...,
15 bytes each, at RAM 0x45b5d0, 2761 names) and opens them by index (*from the code*: 0x145fe4,
loader 0x147ae0). What they hold (*from the data*):
- `A060`-`A0A6`...: pairs of Sony sound banks (an `IECSsreV` .HD header, then the .BD samples).
- `A0E0`: an MPEG program stream (video). `A980`/`A981`: CRI AFS archives, 11642 and 49 entries
  (voices and music, probably; `MODULES/` loads CRI ADX).
- `A000`-`A04A`: graphics and data. Most are enciphered (below; tools/datafile.py) and hold LZ
  pieces (tools/lz.py): either a run of pieces at 2048-byte boundaries, each enciphered on its own,
  usually one TIM2 picture each, or one enciphered stream with a u32 offset table. A001, A01A,
  A03A are plain LZ. 2625 TIM2 pictures in all (build/work/allpics.py exports them; A006, A00B,
  and the rest of A01B are still unknown).
- `/A040/A040.`: the match screen, 9 pieces with **no gaps** between them (the 2nd starts at
  0xf7f8, not on a boundary), listed by the (offset, size) table at 0x482550. Piece 1 (328x108)
  holds the red and blue name plates and their block meters. Until test12 the piece walker
  stopped at the first boundary, so repacking piece 0 zeroed piece 1's first 8 bytes: both plates
  came out blue and the meter as one long box.
- `/A040/A048.`: the pre-match quotes (tools/quotes.py).

### The cipher (*from the code*: 0x16cf50, key at 0x47c4b0)
Each byte is XORed with key[k] (30 bytes), then k = ((k + plain byte) & 0x1e) + 1, and k = 0 once
it reaches 0x1e; k starts at 0. The same function enciphers (mode 0) and deciphers (mode 1).
Some loads pass the file's size as a constant (A048: 0x14fc at 0x222b50/0x222e1c; A049: 0x81b8).

This game's engine is not WAS2's, but the font is the same kind (22x22, 4 bpp, JIS order).

## Executable and memory
`SLPM_662.39`: PT_LOAD file 0x80 -> 0x100000, 0x486880 bytes, .bss up to 0x8ef300, and an empty
second PT_LOAD at 0x8ef300 (*from the ELF header*). RAM = file offset - 0x80 + 0x100000. Code
ends at about 0x240000; `$gp` = 0x58e670. Entry 0x100008 (crt0).

Memory end (*from the code*): crt0 clears .bss up to 0x8ef300 (0x100120 - must not move) and
calls SetupHeap(0x8ef300, -1) (0x1001d0/0x1001d8); sbrk() (0x10dee0) keeps its break in the word
at 0x23e374, initialised to 0x8ef300; 0x13f3b0 sizes the game's memory pool as
0x2000000 - (end + 0x102000) - 0x10. Data that grows goes into the second PT_LOAD and all three
end markers move past it (tools/exefile.py) - the WAS2 lesson (moved strings were overwritten
when only SetupHeap moved).
Every byte of the extra segment comes out of that pool: with the whole script archive moved
there (0xe0000 bytes, test1-test9) tag matches ran out and stopped drawing the wrestlers. The
archive now stays in place and only the entries that don't fit spill over (below).

## Archives and compression
*Verified by round trip* (A001, A01A, A03A unpack to the stated size, using every input byte).
LZ format: a 3-byte big-endian unpacked size, then tokens:
- `t` < 0x80: copy the next `t` + 1 bytes;
- `t` >= 0x80, then byte `b`: copy `((t >> 2) & 0x1f) + 3` bytes from `(((t & 3) << 8) | b) + 1`
  bytes back in the output.

Research decoder: build/work/lz.py.

## Text

### Event scripts (*from the code*; round trip verified on all 329 scripts)
The LZ archive at file 0x3a82c0 (RAM 0x4a8240; 7 lui/addiu references) has 330 entries (the readers 0x13d950/0x13d9d0 add an
entry's offset to the archive's address, so an entry can live in the extra segment); the VM
(0x1b2e10) runs one at a time: `-0x79f4(gp)` the unpacked entry, `-0x79fc(gp)` the offset.
Opcode table at 0x57e680: 8 bytes per opcode (s8 operand bytes, -1 = none, ..., u32 handler);
the dispatcher adds size + 2 unless the handler returns bit 31 (it set the offset itself).
Variable-size opcodes: 0x14 header (u16 n, n x u32 label offsets, u16 m, m x s16), 0x37 text
(u16 length, Shift-JIS, NUL, padded to even), 0x3e (6 bytes: jump through the labels), 0x3f
(var, n, n x u32 offsets: branch), 0x40 (u32 offset: goto), 0x51 (4 bytes: another entry).
Offsets are from the entry's start. 0x35 sets the speaker kind (2 President, 1 secretary,
0 others); 0x42 plays a voice clip. Entry 321 is a list (u16 length + message): match
commentary. tools/script.py.

Text codes: \r (0x0d) line break; FF 01 + u16 n inserts string n (0x1af350: wrestler names
from 0x8e4100 + n x 0xcc; in the commentary also move names; 60/70/80/100 are pauses).

### Drawing (*from the code*)
Glyphs: 0x141f90 maps a code to a glyph in the font at RAM 0x251390 (22x22, 4 bpp, 242 bytes;
JIS row/cell order, ASCII 0x20-0x7f at index code + 0x208d); 0x13a0a0 unpacks one to 8 bpp.
Three renderers draw into 8-bpp bitmaps 552 px wide (rows of 0x2f70 bytes = 22 lines):
- the message window (around 0x13a7c0): x counted in 11-px half cells (`0xa8(sp)`): a 2-byte
  character takes 2, a 1-byte one 1; wraps by itself at 47 cells; punctuation in the lists at
  -0x7c00(gp)/-0x7bfc(gp) may hang over; 0x13d1c0 keeps a record per glyph;
- 0x13afd0 (menus and most text) with the same cells (10 px, or 11 with flag 0x10);
- 0x13b570 (a third, not yet read).
ASCII therefore shows as the font's narrow serif half-width set, one 11-px cell per letter.
Messages are copied (0x1af350) into a 0x360-byte buffer at 0x7ea530.

### The executable's other text
- Strings reached by pointers or lui/addiu pairs: translation/text/exe.csv (tools/exetext.py,
  ported from WAS2): 1061 strings. 0x251360 (line-break punctuation list) is data. The region
  list's 中国 (Chugoku) is also the country list's China: its pointer at 0x47e830 gets its own
  string. Two winner messages use `\k` (new page).
- Records (tools/roster.py): table at 0x47d930 of (offset, size) pairs into the blob at
  0x499350 (one reference, 0x1947ec); 279 records: 206 wrestlers (u16 id, name, numbers,
  finisher as the last field), coaches/staff, 棄権 placeholders. Strings are u16 length + text +
  NUL, padded to even. The game copies a name only if its length / 2 < 11.
- The name-entry kana/kanji grid (0x57ef20-0x580c40) stays as it is.

## Images
TIM2 inside the LZ files (above).

## Open questions
- Proportional English: the three renderers count in half cells; changing them needs in-game
  testing (the per-glyph records of 0x13d1c0 too).
- A006, A00B and the tail of A01B; which pictures hold text (build/work/sheets).
- Whether anything else limits a message's length (the window wraps at 47 cells).

### More picture files (2026-10-24, after the first in-game test)
- `A006`: a plain header of 33 u32 offsets then 33 u32 sizes; each entry one enciphered LZ piece
  (month banners 1月-12月, screen titles). tools/gfx.py kind `dir`; the header is rewritten.
- `A00B`: an LZ archive (u32 offsets, 24 entries at 2048-byte boundaries: list panels, the info
  screen's label sheets, move lists, the card icon sheet) under a second cipher (*from the code*:
  0x16d010(buffer, size, key, mode), called only for A00B at 0x17cf04): the first
  min(size - 2, 200000) bytes as u16 h, deciphered = swap_bytes(h) ^ key, key + 1 each; the key
  is the file's LAST u16 (the game zeroes it after deciphering). The game loads the file whole
  (size constant 0x17cef4/0x17cef8) and reads entries by number (0x13d950). gfx.py kind
  `archive16`. test4 zeroed the key (it sat in the padding after the last entry) and the info
  screen crashed - keep it.
- `A015`: per-wrestler portraits (roster order) with the name written down the right edge;
  `A041`: per-wrestler name strips for the match screen. Both drawn from roster.csv by
  tools/namegfx.py + tools/letter_ext/names.py.

### The info screen and list rows (*from the code*, 0x178440)
Values are sprintf'd into 54-byte rows (sp+0x660 + 0x36*n), drawn into a text texture at 11 px
per byte, and cut out by layout tables of 24-byte sprites (u32, u32, u16 w, h, screen x, y,
texture u, v): page 1 0x4930d0 (13), coaches 0x4934b0 (10), page 2 0x493210 (16). Page 2's two
rows are converted to full-width (0x13ce30) and a loop turns 'F' into 'S' (stat 15 = rank S);
the same loop runs over the roster lists (0x179cc8). tools/infopage.py (build step) changes the
formats, the sprites and both loops - see its docstring.
Page 2's 寸評 value is a title from 0x19c150: a championship ("%s World Champ", the
organisation full-width from 0x47e4c0) or one of the pointers at 0x47e2f0 (0x4a58e8-0x4a5ff8).
Page 1's alignment is GOOD / NORMAL / EVIL (ASCII in the original, 0x47c8a0).

### Menu highlights (*from the data*, not yet confirmed in game)
The office and training menus (/A000/A00A. pieces 0 and 1) are drawn as whole blue panels; the
selected item gets a white copy of its label drawn over it, one sprite per item in the same
24-byte layout: tables at 0x491e70 (main), 0x491f00 (Staff), 0x491fc0 (Business), 0x492070
(Info), 0x4920d0 (system), 0x492190 / 0x492220 / 0x4922e0 / 0x492340 / 0x4923c0 (training).
The sprites were cut to the Japanese labels; tools/menu_sprites.py widens them to the English.

Piece tables: files of pieces are read through (offset, size) tables in the executable (A040
0x482550, A041 0x4825a0, A04A 0x484a70, A015 0x482c30, A018 0x47fe10, A01C 0x481b10, A03C
0x4818d0). The game reads exactly `size` bytes: a piece packed bigger than before must have its
size updated even when it still fits its slot, or the end of its TIM2 (the CLUT) is lost.

### Management-mode lists and titles (*from the code*)
- 0x13afd0 (text, column, row, page, flags) writes into a text page 24 full-width cells wide;
  24-byte sprite tables cut pieces out at fixed byte columns (11 px per byte), as on the info
  screen. tools/screens.py widens the pieces English needs: the home-base map title (0x4a7f28,
  0x4a7f40; regions for scouting come from table 0x47e2b0, repointed to padded copies; the name used to be padded to 8 bytes only when 4 or 6 long, so "Fukui" showed
  "FukuiLas" from the "Last show" text after it) and the rankings rows (format 0x496990, hometown
  sprites 0x4947d0 + 0x78 n; alignment marks Ｇ/Ｎ/Ｅ at 0x4966d8 -> "G "/"N "/"E ").
- Formats whose Japanese columns English must keep (byte for byte): partner rows 0x493010/30,
  HQ row 0x492e80 (its last 10 bytes are the merch-shop note), coach rows 0x4971d0, venue rows
  0x4a80c0 / 0x5849c0.
- Venues: a one-entry LZ archive at 0x4a2da0 (384 records: u16 length + name, u16 capacity,
  u16 0, prefecture, rank, indoor/outdoor), read with 0x13d950 at 0x19b68c; names padded to 26
  bytes for the list columns (0x1aa1e8, 0x21e950). tools/venues.py, translation/text/venues.csv.
- exetext.py now also finds strings that follow other data without a NUL (0x4964d0
  通常の練習です。, pointed to from 0x47c7d0) and one-kanji list formats ("%s　%4d　%2d　%2d名").
- Save/load slots (0x1eefc0): rows are sprintf'd, turned full-width (0x13ce30) and cut into
  boxes (the layout guide is the unused picture A023_t1): so English formats keep the Japanese
  cell counts ("%2d年目" 4 cells -> "Yr%2d", "選手%2d名　" 6 -> "%2d ppl", "%2d月" 3 -> "M%2d"). The
  slot label データ１ (0x4843d0) is copied as 9 bytes and byte 7 incremented for slots 2 and 3:
  English "Ｎｏ．１" (full-width, digit in place; tools/screens.py).
- Ring announcer: LZ block 0x5852d8 (19 length-prefixed lines, 0x0d break, ff 01 NN 00 values),
  unpacked by 0x1c6830 into a buffer of its stated size; tools/announcer.py moves it to the extra
  segment (one lui/addiu at 0x222f48).
