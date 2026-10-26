# Testing rare events

Many management-mode scenes come up once in years of play (photo books, film offers, factions,
retirements, bankruptcy, the Final Series). To check their English without waiting, use the test
cheats and the recipes below. They are for testing the translation only.

## Setup (PCSX2 2.x)
1. Build, then write the cheat file for that build:
   `python3 tools/cheats.py "build/WAS test16.iso"` → `build/cheats/SLPM-66239_<CRC>.pnach`.
   The CRC changes with every build, so write a new file each time.
2. Copy the .pnach into PCSX2's `cheats` folder (Settings > Folders shows where).
3. Start the game, open the game's **Properties > Cheats**, tick the cheats you want. They can be
   turned on and off while playing; most act at the next month change.
4. **Turn on "Money\AP 99,999" first** and check the office screen shows 99,999 AP. If it does not,
   the cheats are pointed at the wrong promotion; tell the translator.

Always keep a save from before a test (cheats change the save's data, e.g. ages and trust).

## The cheats
| Cheat | Use |
|---|---|
| Money\AP 99,999 | Buy anything: facilities, belts, partnerships, TV, ads |
| Money\AP -100 | Bankruptcy: warnings in months 1 and 2, bankruptcy in month 3 (game over alone) |
| Wrestlers\Popularity 99 + morale 99 | Unlocks the media events for every wrestler |
| Wrestlers\Morale 20 | Alignment drift toward EVIL; Rebel Army material |
| Wrestlers\Trust 3 / Trust 0 | Skipping practice, missing, thinking of leaving / leaving |
| Wrestlers\Age 27 | Everyone retires at the next month change |
| Events\Always: ... | That event's monthly roll always succeeds (its conditions still apply) |
| Events\Never: random events | Quiet months while you test something else |
| Calendar\Month = November | Jump toward December/January; turn it off after one month |
| Gallery\Unlock everything / Show everything | Complete gallery (save once to keep) / view only |
| Roster\Sophie and Holly Sierra in management | The two wrestlers management never uses (before New Game) |
| Roster\All 2P alternates from year 1 | The 52 alternates as year-1 candidates (before New Game) |
| Hidden\Gym Talk plays: ... | Gym > Talk plays the Expression check, the unused scenes 164/186 or the staff roll |
| Hidden\Title menu: show the cut Team Event slot | The skipped 団体戦 slot (does nothing) |

Hidden content itself is described in HIDDEN_CONTENT.md.

## Recipes
Use **Events\Always** cheats one or two at a time: the game plays at most one event per check,
and many at once crowd each other out.

| Scene (script entry) | How to get it |
|---|---|
| Fan club (49), film offer (50), police chief (51), photo book (52-155) | Popularity 99 + morale 99, then Always: fan club / film / police chief / photo book. End a month. Each happens once per wrestler; sign different wrestlers to see their photo books (list in MANAGEMENT.md). |
| Vacation scenes (188-261) | Business > Vacation with Always: vacation scene. The scene's wrestler is picked from those with one (MANAGEMENT.md). |
| Heartbreak (48) | Always: heartbreak (it also needs an internal state, often after special training). |
| Skipping practice, thinking of leaving, missing, leaving (157, 14, 158-159, 13) | Trust 3 with Always: skipping practice / goes missing; Trust 0 for leaving. |
| Retirement and ceremony (11, 172) | Age 27, end the month, book a show (the ceremony is at the month's last show). |
| Injuries, hospital, discharge (4-10) | Book many matches for one wrestler; or keep an injured wrestler wrestling. Not cheat-driven. |
| Rebel Army (16, 18, 24, 25) | 6+ wrestlers, 2+ of them EVIL (Talk > Instruct, or Morale 20 for a few months), Morale 20 + Always: faction forms (all three). |
| Revolution Army and showdown (15, 17, 19-23, 166, 167, 329) | 8+ wrestlers; top wrestler 21+ and a 19-or-younger rising star of a different alignment; Always: faction forms + Always: joins the Revolution Army. The showdown demand comes after 6+ months. |
| New Japan / partner guests (45-47) | AP 99,999, buy the HQ (rating +3000), Always: New Japan guests / partner guests. |
| Invasion and counter-invasion | Invade a CPU promotion; it invades back. Beware the freeze bug (MANAGEMENT.md §15): keep a save. |
| EX Tag League invitation (44) | Rating 1500+ (HQ), 2+ wrestlers, December (Calendar cheat, then off). |
| Wrestling Awards (313-317) | January after a year with shows (if the awards option is on). |
| Wrestler moves abroad (327-328) | 6+ wrestlers, Always: wrestler moves abroad. |
| Title warnings and stripping (26-33) | Create a belt (AP 99,999 + HQ for the rating), hold a title match, then skip title matches for 5 and 6 months. Junior belt: a champion turning 19. |
| Overseas defence (40, 41, 325) | Win a partner promotion's belt; the request comes in that belt's set month. |
| Bankruptcy (1-3, 169, 170) | AP -100 for three month changes. In a two-player game the bankrupt player restarts (169). |
| Burglary (156) | Fixed 1 % roll (not in the table); just keep 2,000+ AP. |
| Show cancelled (304) | 5 % per show day; run full months. |
| Final Series (301), ending (307, 319, 320) | System menu > years until the Final Series: set the current year, play to April. With AP 99,999 and strong wrestlers you can see the ranking; the Special ending needs all three events and every prefecture. **Save before it - it happens once.** |

## Without cheats
- PCSX2 save states let you retry a month, but the game's random numbers may replay the same
  result after loading unless you do something different first (book another show, open a menu).
- The System menu's "years until the Final Series" brings the Final Series forward without
  cheats.
