# Hidden content

Unlockables, debug features, button codes and unused content in Wrestle Angels Survivor
(SLPM-66239). Each finding is marked *verified in game*, *from the code* (address given; RAM
address = file offset + 0xfff80 in `SLPM_662.39`) or *fans* (Japanese sources from 2006-2009).
**Unless marked otherwise, nothing here has been checked in the game yet.** No Cutting Room Floor
page or English write-up exists for this game.

Most of it can be tried with the test cheats: `python3 tools/cheats.py <build iso>` writes a PCSX2
cheat file with a section for each item below (docs/EVENT_TESTING.md explains how to use it).

## Short answers
- **Button codes, passwords, debug menus:** none. Every pad check is a plain single button, the
  name entry compares no strings, and the executable has no debug menu or debug print of its
  own (*from the code*). Fans agree: "no hidden events, no 裏技".
- **One undocumented control:** **hold R1 to hide the message window** during events and Yes/No
  questions, to see the picture behind it (*from the code* 0x1b3100, 0x190434; not during the
  staff roll).
- **A cut mode:** the title menu has a slot for **団体戦 "TEAM EVENT"** that the cursor skips.
- **Gallery:** always open (title menu); 166 pictures unlock by seeing them in management mode.
  The cheat **Gallery\Unlock everything** completes it; nothing is rewarded for a full gallery.
- **Hidden wrestlers:** every wrestler can be picked in exhibition. In management mode, **Sophie
  Sierra and Holly Sierra never appear**, and the 52 2P alternates only arrive in years 3-11.
- **Unused content:** a developer "Expression check" scene, two fully voiced but unused event
  scenes (240 lines), 66 unused beach pictures, a second photo-book shot the gallery never shows,
  a few unused banners and backgrounds.

## 1. Controls and codes
- Pad state words: 0x7e5fa0 held, 0x7e5fa2 pressed, 0x7e5fa8 repeat. Every use is a single
  button (○, ×, △, □, d-pad, L1/R1 pages, START to skip logos) (*from the code*).
- **R1 held hides the message window** in event scripts (0x1b3100) and Yes/No boxes (0x190434),
  restoring it on release; off for the staff roll (entries 319/320) (*from the code*).
- No sequence checks, no held-button-at-boot checks, no name-entry passwords (*from the code*).

## 2. Cut and test modes
- **団体戦 / TEAM EVENT.** The title menu is an 8-slot carousel (cursor bits 3-6 of 0x8b6fec):
  0-3 the match modes, **4 Team Event**, 5 Gallery, 6 Options, 7 Save/Load. The cursor code skips
  slot 4 (0x16c338 right, 0x16c40c left) and the ○ handler has no case for it; only its banners
  remain (A006 p21 and the yellow "TEAM EVENT" p29). Cheat **Hidden\Title menu: show the cut Team
  Event slot** makes the slot visible; choosing it does nothing (*from the code*).
- **Expression check** (script entry 305): a developer viewer of a wrestler's five face crops
  (Normal, Happy, Angry, Sad, Bashful). No code plays it. Cheat **Hidden\Gym Talk plays:
  Expression check** makes Gym > Talk play it for the chosen wrestler (*from the code* 0x181ffc).
- **Game flow** (*from the code*): task 0x16b2a0, state word 0x594d34 (0 boot, 1 logos / movie /
  title, 2 new-game setup, 3 management office, 4 script player). Test builds can start at the
  title (`build.py --boot title`) or skip only the opening movie (`--boot nomovie`).
- Exhibition modes 0-7 exist; 2-4 also serve the Final Series. No other unreachable modes,
  office states, sound test or model viewer were found.
- Leftovers: a development file path `host:D:/affect/ResEnjye/rom/cdwork/...` (the developer was
  probably Affect), and one flag (0x586a6c) nothing sets.

## 3. Unused scripts
No code plays these event-script entries (all 146 script calls checked):

| Entry | Content |
|---|---|
| 305 | Expression check (§2) |
| **164** | "{name} has left the Revolution Army" - **120 voiced wrestler lines** |
| **186** | back from an overseas tour - **120 voiced wrestler lines** |
| 38 | both tag champions retire |
| 39 | partnership ended, belt vacated |
| 160, 286 | "We terminated {name}'s contract" |
| 168 | partner group led by its champion (a copy of 47) |
| 171 | "We'll enter our {belt} champion in {event}" |
| 177 | no promising rookies at the tryout |
| 284 | released |
| 289, 295, 298, 299 | partnership ended, merch shop opened, broadcast contract ended, "We invaded {name}" |

Cheats **Hidden\Gym Talk plays: ...** play 164, 186 or the staff roll (319) from Gym > Talk.
Whether the voice clips of 164 and 186 are on the disc was not checked.

## 4. Gallery
*From the code* unless marked.
- Title-menu item 5, always open. **19 pages of 3x3 cells** (cell table 0x484f90): 96 photo-book
  pictures, 70 vacation scenes, 5 empty cells. L1/R1 change the page; ○ on an open picture shows
  the next unlocked variant of that cell. Thumbnails are A027-A039 (one file per page).
- **Unlocking:** 400 seen-flags at **0x8b5e48** (bit 0 of each byte: 0-199 photo books, ids 1654+n;
  200-399 vacation pictures, ids 3000+k) with a **CRC-32 at 0x8b5fd8**. If the CRC doesn't match,
  the gallery screen (0x22b810) wipes every flag - so the fans' "gallery all" code, which writes
  only the flags, leaves an empty gallery.
  - Vacation pictures unlock as soon as they are shown.
  - Photo-book pictures unlock only if you answer **Yes** to "Make a photo book?".
  - Saving copies flags + CRC into the save; loading adds the card's flags to memory (it never
    clears them).
- **Unlock everything:** cheat **Gallery\Unlock everything** (all flags = 1, CRC = 0x86D31D37,
  the standard CRC-32 of 400 bytes of 1); save once with it on to keep a complete gallery. Cheat
  **Gallery\Show everything** instead patches the check (0x22b84c, 0x22b8a0) so nothing is saved.
- Fans: 35 wrestlers have both a vacation and a photo-book picture, 13 only a photo book; the
  2P version of a picture is the same art recoloured.

## 5. Pictures the game never shows
*From the code* (every picture-id range of the script picture opcode traced).
- **66 vacation pictures in A017**: each wrestler standing on the beach in casual clothes, 2-5
  expressions, both personas. No text, no test content; probably replaced by the usual portrait
  layer (*inferred*).
- **The photo books' second shot**: A01B pieces p96-199 (ids 1750-1853), a tilted "printed photo"
  of each photo book. The photo-book event shows it, the gallery never does (it uses p0-95).
- **A00E p17, p19, p20** (event banners) and **A016 p124** (a beach backdrop), **p125** ("GYM 休暇中",
  gym closed for vacation).
- The staff credits (A026) only play in the endings (319/320); there is no credits viewer.

## 6. Wrestlers
*From the code* unless marked.
- **Exhibition:** the pool builder (0x20d7d0) takes every roster id below 400 with a record, so
  **all 206 wrestlers are selectable** - no flags, no unlocks (Holly Sierra *verified in game*).
  Coaches (401-467) and the 棄権 forfeit placeholders (701-724) are never in it.
- **Management, never:** **Sophie Sierra (236) and Holly Sierra (336)**. Every other foreign wrestler
  belongs to one of 7 foreign-promotion rosters (table 0x4a6290, 6 originals + 6 successors each);
  these two are in none, though they have full assets (portrait, name strip, VS close-up,
  moveset, finisher, 13 voiced lines). 43 foreign pairs for 42 slots - probably cut for space
  (*inferred*). Cheat **Roster\Sophie and Holly Sierra in management** puts them in group 6 in
  place of Yun / Shu Meifa.
- **Management, late:** the 52 domestic **2P alternates** (ids 101-152) carry a **debut year**
  (master record +0x115) and join the tryout/scouting pool as 15-year-olds in years 3-11. Four
  arrive in year 10 and four in year 11 (Scarlet Kojima, Julia Watanabe, Raspberry Enomoto, Tsukasa
  Manabe), so with the default 10-year game they are effectively post-game. Cheat **Roster\All 2P
  alternates from year 1** makes them all candidates from the start (switch on before New Game).
  Fans call these alternates the game's "secret wrestlers"; the 16 guest-artist characters have
  none.
- **Foreign 2P versions** (301-343) take over their original's roster slot when she reaches the
  group's age limit (0x1a2a10).
- **Not playable:** the 49 coaches (no moves or pictures) and the 24 forfeit placeholders, which
  fill empty bracket slots ("Withdrew" / "Absent") although each still holds a dummy wrestler body
  copied from Suzumi Ishikawa's record.

## 7. Moves
*From the code*: names at 0x47d760 (108 entries), data at 0x4a4cec (28 bytes each).
- **Learnable but no wrestler starts with them:** Fisherman Buster, Dragon Cavernaria, Splash
  Mountain, Shooting Star Press, Body Throw.
- **In the table but in no move list:** the five tag double-team moves, Pin and Break Up (used
  by the match engine itself).
- All 28 counters are used; there are no test, dummy or empty move names.
- All 91 nickname strings are reachable (0x19c150).

## 8. Known cheat codes (*fans*)
Pro Action Replay 2 codes for this disc (bubera.com, 2ch strategy thread 03) decrypt with the
standard PAR2 seed; the raw addresses agree with this page (AP at 0x82af58, wrestlers at
0x82d658 + 0xec4 n) and the code patches match this disc's instructions, so the disc is the build
they were made for. They include repeat-a-command-this-month, always-successful transfers,
breaking growth caps, maximum experience per match and auto-win in unwatched matches (not
reproduced here). Whether they work on the Good Price reissue
(SLPM-66927) is unknown.
