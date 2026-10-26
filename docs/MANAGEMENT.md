# Management mode

How Wrestle Angels Survivor's management mode works: setup, the monthly turn, money, shows,
wrestlers and training, recruitment, titles, facilities, rival promotions, events, the Final
Series and the endings, with strategy and known bugs. It is the basis for a player guide.

**Nothing on this page has been checked in the game yet.** Each finding is marked:
- *code* - read in the executable (RAM address given; `extracted/SLPM_662.39`, file offset =
  address − 0xfff80);
- *text* - what an on-screen string says (exe.csv id) or an event script (`entry N` =
  `translation/script/NNN.txt`);
- *fans* - Japanese strategy sources from 2006-2009 (see [Sources](#sources)), used where the
  code was not traced;
- *inferred* - a reasonable reading that was not proven.

Integer division truncates throughout. Checks worth doing in an emulator are under
[Open questions](#open-questions). Do not mix this page's numbers with Survivor 2's
(`Wrestle-Angels-Survivor-2-English/docs/MANAGEMENT.md`): the engines differ.

## Contents
- [Short answers](#short-answers)
- [1. Starting a game](#1-starting-a-game) · [2. The month](#2-the-month) · [3. Money](#3-money)
- [4. Shows, venues and popularity](#4-shows-venues-and-popularity)
- [5. Wrestlers](#5-wrestlers) · [6. Growth and training](#6-growth-and-training)
- [7. Recruitment](#7-recruitment) · [8. Titles and overseas promotions](#8-titles-and-overseas-promotions)
- [9. Facilities](#9-facilities) · [10. Rival promotions](#10-rival-promotions)
- [11. Events](#11-events) · [12. Factions](#12-factions-revolution-and-rebel-armies)
- [13. The Final Series and the endings](#13-the-final-series-and-the-endings)
- [14. Strategy](#14-strategy) · [15. Known bugs](#15-known-bugs)
- [Wrestler-specific scenes](#wrestler-specific-scenes) · [Open questions](#open-questions) ·
  [Sources](#sources)

## Short answers

- **What is the goal?** Run a women's wrestling promotion for a number of years you choose at
  New Game (1-99, default 10). Then comes the **Final Series**: three tournaments between all
  promotions, after which every promotion is ranked by **total assets** in AP. First place is
  the Good ending; first place plus winning all three events plus being the most popular
  promotion in every prefecture is the **Special ending**. Play continues afterwards, up to
  year 99. There is no fixed story: everything between the opening and the Final Series is
  rolled from stats, flags and the calendar.
- **How do you lose?** **Bankruptcy**: three months in a row starting with negative AP. In a
  one-player game that is game over (*code* 0x1877b0). With other human players still in, a
  bankrupt player restarts from nothing with 3,000 AP.
- **What matters most?** Money (AP) and the **rating** of your wrestlers. Crowds come from your
  popularity in each prefecture and from a strong main event; popularity only grows from
  full houses, ads, autographs and TV. Wrestlers grow fast in their teens, peak around 20,
  decline from 21-23 and retire by 27-28, so the game is a cycle of finding, growing and
  replacing talent.
- **How do you win?** Recruit early (scouting finds the best rookies), fill small halls on a
  wide tour, grow young wrestlers against stronger opponents, buy the Venue facility before
  booking big halls, and hoard AP and highly rated wrestlers for the Final Series valuation.
  Fans also recommend weakening the fixed rival, New Japan Women's Pro (§14).

---

## 1. Starting a game

### 1.1 Setup screens
*Code* 0x1c5610; *text* 0x57ebc0-0x57eec0.

| Step | Choices |
|---|---|
| Players | 1-4 humans, each confirming with their own controller |
| Promotions | players + 1 up to **5** in total |
| Years until the Final Series | **1-99, default 10**; can be changed later in the System menu until the Series has been held (*text* 0x491130) |
| Per player | promotion name and abbreviation (name-entry grid), logo, home base (picked on the map) |
| CPU promotions | **New Japan Women's Pro is always in**; the rest are chosen from the other eight |

- You start with **3,000 AP and no wrestlers** (*code* 0x1c5d7c). A show needs at least 6.
- **There is no difficulty setting** in management mode (the "Set the level" screen belongs to
  the exhibition modes).
- **Starting popularity** in each of the 48 areas is 0.5-0.9 (big cities 0.9: Tokyo, Kanagawa,
  Aichi, Osaka), with **+0.3 in your home prefecture** and +0.2 in the rest of its region
  (*code* 0x19e380). Fans list the prefectures with a starting bonus as West Hokkaido, Miyagi,
  Chiba, Saitama, Tokyo, Kanagawa, Aichi, Osaka, Hyogo, Hiroshima and perhaps Fukuoka (*fans*).
- The first month opens with the secretary, Kiriko Inoue (entry 324): no wrestlers yet, six
  are needed for a show, recruit through tryouts and transfers, and a late debut strains the
  finances.

### 1.2 The CPU promotions
Table 0x4a4b20, nine records (*code* 0x19a0b0, 0x19a220).

| # | Promotion | Abbr. | Start AP | Home | Style | Starting wrestlers |
|---|---|---|---|---|---|---|
| 0 | New Japan Women's Pro (新日本女子プロレス, "Shinjo") | NJWP | 4000 | Tokyo | nationwide | Panther Risako, Mighty Yukiko, Bomber Kishima, Riyu Kikuchi, Shinobu Echigo, Hitomi Fujishima |
| 1 | Pacific Women Pro (太平洋女子プロレス) | PWPW | 4500 | Aichi | mid-size | Teddy Cat Hori, Blade Uehara |
| 2 | Gekitouryu (激闘龍) | BD | 6000 | Hyogo | big cities | none |
| 3 | Japan Ocean Women Pro (日本海女子プロレス) | JSW | 5000 | Ishikawa | regional (Hokuriku) | none |
| 4 | Palacion (パラシオン) | PLC | 4500 | Hiroshima | regional (Chugoku) | none |
| 5 | JWI | JWI | 9000 | Saitama | big cities | Beauty Ichigaya |
| 6 | World Women Pro (ワールド女子プロレス) | WWPA | 9000 | Osaka | nationwide | none |
| 7 | WARS | WARS | 6000 | Tokyo | mid-size | Thunder Ryuko, Suzumi Ishikawa (*inferred*) |
| 8 | Pro Wrestling NEO (プロレスリング ネオ) | NEO | 4000 | Kanagawa | mid-size | none |

The English names follow each promotion's own logo, shortened to the game's 21-letter limit.

- Without the CPU promotions that hold them, some stars start as **free agents**: fans list
  Reira Kirishima (910), Miki Shibata (920), Mimi Yoshihara (910) and Blade Uehara (1080) as
  ready to fight in year 1 (*fans*).
- Fans recommend choosing the CPU promotions with **no wrestlers and little AP** for an easier
  game, though more rivals also soak up weak rookies (*fans*).

---

## 2. The month

### 2.1 Calendar
- The game starts in **April of year 1**; **the year changes in April**; the counter stops at 99
  (*code* 0x19cb70, 0x1bd63c). Ages go up at the year change.
- **January:** the year-end Wrestling Awards (§11.1).
- **December:** New Japan's **EX Tag League** invitation (§11.1); no invasions and no faction
  showdown demands.
- **Final Series:** in the April after the set number of years (with 10 years, "as if year
  11"), once per game (§13).

### 2.2 Order of a month
1. **News and events**, read by the secretary (§11). At most one event per check, so a busy
   month queues several.
2. **Office work**: Staff, Business, Info, Gym, Invade, System. Most commands work **once a
   month** ("Done for this month.", *text* 0x490920): tryout, scouting, transfer talks,
   partnership, facility investment (merch shops included), tour abroad, coach hire, vacation,
   special training, advertising, TV, belt creation, invasion. Release, dismiss, vacate,
   autographs and Info have no limit (*code* 0x1bb1a0).
3. **Booking**: up to **8 show days**, never two in the same prefecture in one month
   (*code* 0x1aa530). Then the month's show roster (at least 6, an even number, at most 30)
   and the card for each day. A day can be normal matches, a **tournament** or a **league** (up
   to 8 teams; a league needs enough show days), with title matches.
4. **Shows**, day by day: attendance, a chance of cancellation, the matches (watch, play or
   simulate).
5. **Month end**: popularity update, the **financial report**, "This month's growth results"
   (training), then the next month.

A **vacation** month has no shows (§11.2).

### 2.3 The office menus
Help texts *text* 0x4913f0-0x491cb0.

**Staff**

| Command | Cost | Notes |
|---|---|---|
| Tryout | 1-99 AP (your choice) | Finds 1-2 rookie candidates; you decide whether to sign (§7.1). Needs a free dorm place. |
| Scouting | 50 AP per region, plus 10 AP × her age if you sign | Up to 3 finds born in the chosen region (§7.2) |
| Transfer Talks | a minimum fee (on success) + 1-99 AP you add (always charged) | From a rival or a free agent (§7.3) |
| Release Wrestler | free | |
| Hire Coach | 100 AP | Coach limit set by the Gym facility (§9) |
| Dismiss Coach | free | |
| Tour Abroad | the text says 50 AP a month; the code charges 5 | One wrestler per overseas partner (§8.3) |
| Vacate Title | free | Gives up a belt you hold |

**Business**

| Command | Cost | Notes |
|---|---|---|
| Partnership | 500-1000 AP (×1.5 to take it from another promotion) | Overseas partner (§8.3) |
| Expand Facilities | per level (§9); merch shop 500 AP | One investment a month |
| Create Belt | 1000 / 3000 / 5000 AP | Needs rating 2000 / 3000 / 4000 and 6 / 8 / 10 wrestlers (§8.1) |
| Vacation | 30 AP per eligible wrestler | No shows this month; trust +10 for everyone; may play a character scene (§11.2) |
| Autographs | 50 AP | 1-3 wrestlers in one prefecture: popularity there + (sum of their popularity)/1000 (§4.1) |
| Advertise | TV ad 200, radio 100, flyers 50 AP | +3 / +2 / +1 popularity in every prefecture (§4.1) |
| TV Broadcast | contract + monthly upkeep | One-year deal with one of 11 stations (§3.3) |

**Info** (free): promotion data (pages: promotion, facilities, belts, partners, history),
roster data, rankings (sorted by ability; national, regional and prefectural popularity), the
influence map (your popularity), the dominance map (the leading promotion per prefecture),
months since your last show in each prefecture, merch shop data.

**Gym**: individual and group training settings (free), **special training** (20 AP), **talk**
(10 AP), coach assignment (§6).

**Invade**: send 1-3 wrestlers into a rival's shows (§10.2).

**System**: save, load, options, years until the Final Series, and how CPU shows are shown
(watch all / watch the final / don't watch).

---

## 3. Money

### 3.1 AP
AP is the only currency: **1 AP = ¥100,000**; the books are kept in yen and AP changes by the
month's net / 100 (*code* 0x1bd074).

### 3.2 Income
| Source | Amount |
|---|---|
| **Tickets** | ¥4,000 per spectator: 25 spectators = 1 AP (*code* 0x1b55e0) |
| **Merch shops** | each month, 1 AP × your popularity (0-10) in each prefecture with a shop (*code* 0x1b4db0) |
| Media events | film +200 AP, photo book +100 AP, police chief +50 AP (§11.1) |
| Awards | MVP 300 AP; Rookie of the Year, Match of the Year 100 AP each (*text* entries 313-317) |
| Final Series | prize money (§13.2) |

TV is **not** income in this game: it costs AP and pays back in popularity.

### 3.3 Expenses
| Item | Amount |
|---|---|
| **Venue rent** per show day | capacity × ¥3,000 × the venue's rate (table below): **charged on the hall's capacity, not on the crowd** (*code* 0x19b7f0) |
| **Wrestler pay** | 1 AP per wrestler on the month's show roster, plus (rating − 300) × (popularity + 50) yen per match (rating capped at 1100); 1 AP each when there is no show roster (*code* 0x1b4e80) |
| Guests on your cards | ¥20,000 + (rating − 500) × ¥200 per match |
| Coaches | ¥20,000 × ability (0-15) a month: at most 3 AP each |
| **Running cost** | promotion rating / 100 AP a month (*code* 0x19e120) |
| Tours abroad | 5 AP a month per touring wrestler (as coded) |
| TV upkeep | the station's monthly fee |

There are no individual contracts or salary negotiations.

**Rent rate by venue rank** (*code* table 0x47ed40). The ticket is ¥4,000 against ¥3,000 a
seat, so **a show breaks even at 0.75 × the rate full**:

| Rank (capacity) | 0 (500-1,000) | 1 (1,500-2,000) | 2 (2,500-3,000) | 3 (3,500-5,000) | 4 (5,500-7,000) | 5 (7,500-10,000) | 6 (11,000-30,000) | 7 (40,000-55,000) |
|---|---|---|---|---|---|---|---|---|
| Rent, indoor | 30 % | 33 % | 41 % | 54 % | 62 % | 71 % | 76 % | 85 % |
| Rent, outdoor | 25 % | 26 % | 34 % | 43 % | 56 % | 62 % | 72 % | 85 % |
| Break-even, indoor | 22.5 % full | 25 % | 31 % | 40.5 % | 46.5 % | 53 % | 57 % | 64 % |

**TV stations** (*code* table 0x4992d0). Contracts run 12 months; each station serves one
promotion at a time; the benefit is +0.1 popularity in the station's area at intervals.

| Station | Area | Contract | Upkeep / month | Interval |
|---|---|---|---|---|
| DaiNippon TV | national | 1500 | 150 | 4 months |
| Odaiba TV | national | 1000 | 100 | 6 months |
| Kitaguni TV | Hokkaido | 200 | 20 | 3 |
| Ringo TV | Tohoku | 200 | 20 | 3 |
| TV Kanto | Kanto | 500 | 50 | 3 |
| Sado TV | Koshinetsu | 200 | 20 | 3 |
| Misokatsu TV | Tokai | 250 | 25 | 3 |
| Tsutenkaku | Kinki | 300 | 30 | 3 |
| Miyajima TV | Chugoku | 200 | 20 | 3 |
| Sanuki TV | Shikoku | 200 | 20 | 3 |
| Aso Volcano | Kyushu | 200 | 20 | 3 |

TV is a weak deal for its price (a national station costs 3,300 AP a year for a few tenths of
popularity). Fans say you can hold only one station at a time and recommend DaiNippon, or Aso
for all of Kyushu (*fans*). The code's timing of the gain may differ from the text (open
question 4).

### 3.4 Other money events
- **Burglary** (entry 156): 1 % a month once you have debuted and hold at least 2,000 AP; you
  lose 25 % or 50 % of your AP (*code* 0x236178). Fans spend spare AP on the HQ partly to avoid
  this.
- **Bankruptcy** (entries 1-3): a month that starts with negative AP brings a warning; a second
  in a row a stronger warning; **the third in a row is bankruptcy**. Any month starting at 0 AP
  or more resets the count. In one-player games bankruptcy is **game over**; with another human
  still playing, the promotion is wiped (wrestlers, coaches, belts, partners, popularity) and
  restarts with 3,000 AP (entry 169) (*code* 0x235f18, 0x1a45f0, 0x1877b0). CPU promotions
  restart the same way a few months later, without their starting stars (entry 170).

---

## 4. Shows, venues and popularity

### 4.1 Popularity
Each promotion has a **popularity of 0.0-10.0 in each of 48 areas** (the 47 prefectures, with
Hokkaido split East/West), plus a hidden **saturation** of 0-100 (*code* 0x1bb370).

| What | Effect on popularity |
|---|---|
| A show day | **+0.1 only if the crowd was at least 90 % of capacity** (or popularity is still ≤ 1.0) |
| No show there | −0.1 when the months since your last show reach 8, 14, 20, 26, then every 6 months |
| Advertising | +3 / +2 / +1 everywhere (TV ad / radio / flyers); the help text says for that month only (open question 1) |
| Autograph session | + (sum of the 1-3 wrestlers' popularity) / 1000 in that prefecture |
| TV | +0.1 in its area at intervals |
| Signing a wrestler | +0.2 in her home prefecture (*inferred*) |

**Saturation** rises after each show by the crowd relative to your popularity and rating, and
falls by 25 a month; it lowers the next crowd there. Together with the one-show-per-prefecture
rule, this rewards touring. Fans advise returning to a prefecture only after **3-5 months**.

Regions (for scouting, TV and rankings): Hokkaido, Tohoku, Kanto, Koshinetsu, Tokai, Kinki,
Chugoku, Shikoku, Kyushu (with Okinawa).

### 4.2 Venues
- **384 venues, 8 per area** (`translation/text/venues.csv`), each with a capacity, a rank 0-7
  and indoor or outdoor. The biggest: Fukuoka 55,000; Tokyo, Osaka and West Hokkaido 50,000;
  Aichi 45,000; Saitama 40,000.
- **The Venue facility caps the halls you can book**: up to 2,000 / 3,000 / 6,000 / 10,000 seats
  at levels 0-3, anything at level 4 (*code* 0x19c990). New promotions are limited to small
  halls.
- **Cancellations**: each show day has a 5 % chance (entry 304), by weighted cause: foreign
  wrestlers didn't arrive (only with an overseas partner), heavy snow (December-March), typhoon
  (June-September), traffic accident, earthquake (*code* 0x20d0f0).

### 4.3 Attendance
*Code* 0x19ed10. R = wrestler rating (capped 1100 here), p = her popularity (0-99), A = your
popularity in the area (0-10), B = saturation.

```
draw     = (R − 300) × (50 + p) / 100      your wrestler (×2/3 for other promotions' and free wrestlers)
base     = Σ draw × 0.8 + 500
base     = base × (100 − B) / 100 × A / 2
crowd    = min(base, 85 % of capacity)
main event: score from the total rating of the last match's wrestlers
            (singles 1200-2600, tag 2400-5000, 3-on-3 3600-7800 → 0-15) × the venue's rank factor
            (3.3 for the smallest halls down to 0.8 for domes), at most 20
crowd   += capacity × score / 100           (a weak main event subtracts)
title match: + capacity × (belt value − 700) / 10,000 if positive
crowd    = between 425 and 105 % of capacity
```

What this means:
- **Your popularity in the area multiplies everything.** Early on (0.5-0.9) crowds sit near the
  **425 floor**, so only the smallest halls fill.
- The base part stops at 85 %: a sell-out needs a **strong main event**, and it counts most in
  small and mid-size halls.
- How the match goes does not matter to the box office; only the card does.
- Fans' summary: base fans 0-85 %, main-event fans 0-20 %, title-match fans from the belt's
  value; six wrestlers rated 1000+ can sell out 6,000-7,000 seats without a title match
  (*fans*).

---

## 5. Wrestlers

### 5.1 What a wrestler has
| Field | Range | Notes |
|---|---|---|
| Style grades: Throws, Holds, Power, Strikes, Aerials (attack and defence each) | 1-15 (15 shows as S) | each pair at most 27; each at most its linked basic + 4 |
| Basics: Strength, Dexterity, Stamina, Recovery, Speed | 1-10 | total at most 40. Links: Throws-Str, Holds-Dex, Power-Stam, Strikes-Recov, Aerials-Speed |
| **Rating** | to about 2000 | 10 × (style grades, capped at 135 in total + basics + learned moves) (*code* 0x1953d0) |
| HP | | 50 + 10 × Str + 30 × Stam |
| Popularity | 0-99 | new wrestlers start at 10 + rating/30 |
| **Trust** | 0-99 | 50 when signed |
| Morale | 0-99 | drives alignment drift and media events |
| Alignment | GOOD / NORMAL / EVIL | |
| Faction | Reg. / Rev. / Reb. | regulars, Revolution Army, Rebel Army (§12) |
| Condition | Normal, Hurt, Injured, Hospital | §5.3 |
| Hidden: talent grade (S-E), growth type (early / normal / late), career-length type, grit | | fixed per wrestler; for 2P alternates rolled when they appear (*fans*) |

### 5.2 Popularity, trust and morale over time
- **After a match** (by the rating gap to the opponents): a win against stronger opponents
  gives up to +4, a win against weaker ones nothing; a loss to weaker opponents costs up to −2
  (*code* table 0x4846e0). **Upsets make stars.**
- **Each month**: with matches, popularity creeps up while it is 40 or less; **without matches,
  a star above 60 loses 2-5 a month**.
- **Trust** each month: −5 when hurt or injured, −15 in hospital; +20 on individual vacation
  training; title matches and main events raise it, openers for top wrestlers lower it (*fans*).
- **Low trust**: below 6, she may skip practice (50 % a month, entry 157) or go missing (20 %,
  entry 159), with a warning that she is thinking of leaving (entry 14); **at 0 she may quit**
  (10 % a month, entry 13).
- **Morale**: at 70+ alignment drifts toward GOOD (2 % a month per step); below 31 it drifts
  toward EVIL (GOOD→NORMAL 2 %, NORMAL→EVIL 10 %) and can feed the Rebel Army (§12).

### 5.3 Injuries, retirement, leaving
- **Injury levels** (entries 4-7): 1 Hurt (can still wrestle), 2 Injured, 3 Hospital (about a
  month), 4 severe (longer); **5 ends her career** (entry 10).
- **Healing**: Hurt or Injured heals a level a month with chance 10 × (6 − matches this
  month) %: 60 % when rested, none with 6+ matches. Individual vacation heals a level a month;
  a business vacation heals injuries up to serious ones (*fans*). After hospital she returns
  as Injured (entry 8).
- **Retirement** (entry 11, ceremony at the month's last show, entry 172): certain at **27**;
  earlier if she is in decline, holds no title and her rating has fallen under 81 % of her best
  (*code* 0x236a78). Fans: "retires in the April after turning 28 at the latest". Retired
  wrestlers can become coaches.
- **Leaving for abroad** (entry 328): 3-5 % a month (by promotion rating) for a promotion with
  6+ wrestlers; it picks a non-champion with trust 80 or less. Fans say she returns as a free
  agent a year later.
- **Rebirth**: three Aprils after a wrestler retires (a year later if she was a coach), she
  reappears as a 15-year-old rookie, usually as her **2P/B-type alternate** (*fans*; §7.4).

---

## 6. Growth and training

### 6.1 How growth works
At month end each wrestler earns a pool of points (*code* 0x1ba0e0):
1. **Matches**, by the rating gap:

   | Opponents stronger by | > 200 | 151-200 | 101-150 | 51-100 | −49..50 | weaker 50-99 | 100-149 | 150-199 | ≥ 200 |
   |---|---|---|---|---|---|---|---|---|---|
   | Win | 80 | 40 | 30 | 25 | 20 | 15 | 10 | 5 | 0 |
   | Loss | 25 | 20 | 15 | 10 | 5 | 0 | −3 | −6 | −10 |

   × talent × age phase × condition. **Losing to much stronger opponents still teaches**;
   beating much weaker ones teaches nothing, and losing to them costs.
2. **Training** = coach ability × **(10 − matches this month)** × talent × age × condition:
   **every match costs a tenth of the month's training.**
3. **Natural growth** by age phase: +10, +5, −5, −15, −30 (rising → late decline).

| Talent grade | S/0 | 1 | 2 | 3 | 4 | E/5 |
|---|---|---|---|---|---|---|
| Factor | 15 | 13 | 11 | 9 | 7 | 5 |

| Age phase | rising | growing | peak | decline | late decline |
|---|---|---|---|---|---|
| Match factor | 3 | 2 | 1 | 0 | −1 |
| Training factor | 15 | 15 | 10 | 10 | 10 |

- Phases are young by design: rising/growing end by **16-19**, decline begins at **21-23**
  and late decline at **22-25**, by type (*code* 0x19f4c0).
- Grades rise when their EXP passes thresholds 23, 36, 50, 65 ... 270, and can fall back.
- Fans add that about **80 % of experience follows the wrestler's existing stat profile** and
  only 20 % the training menu, so weaknesses barely grow; a coach redirects part of it along
  the coach's own profile (*fans*).

### 6.2 Training settings
Style (default), Weakness, Basics, Offense, Defense, Moves, Vacation (individual: no training,
trust +20, heals), and each style category (*text* 0x491a20-0x491cb0). Group training sets
everyone at once (no move practice).

- **Moves**: pick a move and a level 1-9; it is learned at 10 + 2 × (level − 1) EXP. **Each
  learned move adds 10 to the rating.** You can also change a learned move's difficulty, choose
  the finisher and rename moves. Fans: put the cursor on an **empty move slot** before teaching,
  or the new move overwrites an old one; teach moves around 18-19, fundamentals first.

### 6.3 Coaches, special training, talk
- **Coaches**: up to 5 (Gym facility); each handles up to 5 wrestlers; the coach's ability
  (0-15) replaces the wrestler's own in the training term. Hiring 100 AP plus a small monthly
  fee. Coaches retire after a while (entry 12). Fans say B-grade-or-better coaches appear only
  once your promotion rating reaches 3000.
- **Special training** (20 AP, once a month; needs an assigned coach): success 65 % + coach
  ability (65-80 %) doubles this month's training and gives trust +5 (entry 268); failure wastes
  the month's training, trust −5 (269), and one time in ten worsens an injury (270).
- **Talk** (10 AP; entries 271-279):

  | Option | Success | Effect |
  |---|---|---|
  | Praise | 70 % | morale +10 |
  | Scold | 70 % | trust +5 (failure: morale −10, trust −5) |
  | **Cheer** | 70 % | **trust +10** - the best trust repair |
  | Hear worries | 10 % | clears a grudge with another wrestler |
  | Instruct (GOOD / NORMAL / EVIL) | 5-10 % | changes her alignment |

---

## 7. Recruitment

### 7.1 Tryout (1-99 AP)
Score = AP spent − 30 + 5 × (6 − roster size) − random(1-100); a second candidate only on a
positive score and with two free places (*code* 0x19a5d8). **Spending under about 50 AP gives
the same result as 1 AP**, and the odds of a top-grade rookie are about 10 % at best. Fans:
"1 AP almost always turns up one rookie".

### 7.2 Scouting (50 AP a region)
Up to three finds born in the region; grades 0-1 (the best) about **35 %**, against about 10 %
from a tryout. Signing costs 10 AP × her age. Weak rookies tend to be found first and fans
save-scum the scout. **Best year-1 rookies (*fans*)**: Toshimi Minami (Shikoku, A) and Haruka
Date (Kyushu, A); Kanto and Chugoku are rich. Year 2: Kanna Kamui (Hokkaido, S). Year 3: Chigusa
Yuki and Megumi Muto (Tokai, S). Year 4: Reika Ichigaya (Kanto, S). Year 5: Ryuko Yoshida
(Kyushu, S). Year 6: Yukiko Shinzaki (Chugoku, A). S/A-quality rookies reportedly need a
promotion rating of 3000.

### 7.3 Transfer talks
```
minimum fee = max(100, rating − 400 + 5 × popularity)          charged only on success
target      = rating/20 + her trust in her promotion + popularity/2
              + 2 × your roster size + 30/20/10 if she is her promotion's #1/#2/#3
roll        = AP added (1-99) + random(1-100) + a quarter of what you added last time
success if target < roll; the added AP is always spent
```
A failure makes the next attempt easier. It always fails for a champion, a wrestler who joined
under 3 months ago, or one booked in an event. **The code suggests every transfer succeeds
before your debut show** (*code* 0x1a1158) - a strong opening if true (open question 2). Fans
note that rivals poach your wrestlers without a fee, and that champions can't be poached.

### 7.4 Free agents, 2P alternates and rebirth (*fans*)
- Rookies not signed by 17 join the free list; free agents stay until 26, then vanish and are
  reborn.
- The **2P / B-type alternates** (e.g. Yukiko Shinzaki for Mighty Yukiko, Risako Sakuma for
  Panther Risako, Ryuko Yoshida for Thunder Ryuko, Reika Ichigaya for Beauty Ichigaya) are not
  in the starting pool. They appear as 15-year-old rookies on a fixed schedule from **year 3**
  (year 3: Izumi Yoshihara, Risako Sakuma, Kyoko Uehara; year 4: Reika Ichigaya, Saki Hojo,
  Ogre/Yuka Asahina, Shoko Taki, Admiral Yajima; year 5: Ryuko Yoshida, Asuka Kagami ...; year 6:
  Yukiko Shinzaki, Hybrid Minami, Raijin Mifuyu, Eri Kishima ...; up to year 11), and through
  rebirth. Their talent and types are rolled when they appear; some are better than the
  originals. They share the originals' event lines.

---

## 8. Titles and overseas promotions

### 8.1 Your own belts
| Belt | Cost | Rating needed | Wrestlers needed |
|---|---|---|---|
| 1st | 1000 AP | 2000 | 6 |
| 2nd | 3000 AP | 3000 | 8 |
| 3rd | 5000 AP | 4000 | 10 |

At most 3 belts, one a month; types Heavy, Tag, Junior (a repeated type gets Ⅱ/Ⅲ). Belts change
hands in title matches on your cards. Fans: heavyweight belts first, junior belts draw poorly;
title matches raise both wrestlers' trust twice as fast.

### 8.2 Title rules
- **5 months without a title match** brings a warning (entries 26, 27); **at 6 the champion is
  stripped** (29, 30).
- **Junior belt**: vacated when the champion turns **19** or reaches **rating 1000** (28, 31).
- **Belt value** (*fans*): falls by value/40 a month; after a title match it becomes the
  loser's rating + 100. A champion gives the belt up when its value falls under 75 % of her
  rating (entries 32, 33).
- Retirement, a career-ending injury or a tag partner leaving vacate belts (37).

### 8.3 Overseas promotions
| Promotion | Style | Partnership cost (adds half to your rating) |
|---|---|---|
| IWWF | basics | 1000 |
| WWCA | throws | 800 |
| EWA | holds | 700 |
| AAC | aerial | 600 |
| TWWA | strikes | 500 |
| GWA | power | 500 |

- **Partnership**: exclusive to one Japanese promotion; taking one from another promotion costs
  1.5 × and is refused while that contract is young. A partner sends wrestlers to your shows
  (fans: about 4 a month), lets you tour abroad, brings visiting champions (entry 323) and its
  belts. Partnerships end or expire (entries 42, 161). **Fans' standard first move: a 500 AP
  partnership in April of year 1**, so you can run shows at once.
- **Tour abroad**: one wrestler per partner; she grows by a flat amount instead of match
  experience, gains a little trust, and fans say it changes her growth direction and cures a
  rebellion after 6+ months.
- **Foreign belts** must be defended abroad once a year in a set month (entry 40); declining
  strips her (41), going brings her home "in triumph" (325) with injuries healed.

---

## 9. Facilities
One investment a month (*code* table 0x499300).

| Facility | Cost per level | Effect by level |
|---|---|---|
| **Venue** | 1000 / 3000 / 5000 / 10000 | largest hall 2,000 / 3,000 / 6,000 / 10,000 / any |
| **Dorm** | 500 / 1000 / 3000 / 5000 / 10000 | roster limit 6 / 8 / 10 / 12 / 14 / 16 |
| **Gym** | 500 / 1000 / 1500 / 2000 | coach limit 1 / 2 / 3 / 4 / 5 |
| Tour bus | 500 / 1000 / 1500 / 2000 | "raises wrestler trust by 5" (mechanism not traced) |
| HQ | 5000 / 10000 / 30000 | promotion rating +3000 / +6000 / +10000 |
| Merch shop | 500 each, one per prefecture | 1 AP × your popularity there each month |

- **The Venue is the key facility**: without it nothing over 2,000 seats.
- **The HQ's rating costs upkeep** (rating / 100 AP a month) but opens belts and counts in the
  Final Series; fans say HQ level 2 brings overseas champions on tour.
- **A shop pays at most 10 AP a month**: build them where you are already popular, or late for
  the Final Series valuation (+50 AP each).

---

## 10. Rival promotions

### 10.1 How the CPU plays
CPU promotions invest in facilities, open merch shops by their style, hire coaches up to 3,
recruit over time and can go bankrupt like you (*code* 0x227250). Fans: they go bankrupt from
over-expansion around years 10-15 or when their roster is poached away, and return 3-4 months
later with everything reset.

### 10.2 Invasions
- **Your invasion**: 1-3 wrestlers into a rival's shows, once a month, not before your debut,
  not during a faction showdown; while it is set, no vacation and no tour abroad. **The target
  invades you back** (entries 46, 47; a champion may lead). Fans: it boosts attendance;
  invasion matches are never title matches; JWI counter-raids.
- **New Japan invades** (entry 45): 5 % a month once your rating reaches 1200, never in
  December.
- **Beware the invasion freeze bug** (§15).

---

## 11. Events
Events are rolled at the month change by one function (*code* 0x234f00) in a fixed order; the
scripts only show the text. Entry numbers are `translation/script/NNN.txt`.

### 11.1 Promotion events
| Event | Trigger | Entry |
|---|---|---|
| Opening, debut-show speech | first month; first show | 324, 308 |
| In the red / again / bankrupt | months starting with negative AP (§3.4) | 1, 2, 3 |
| Fresh start; rival bankrupt / restarts | | 169; 3, 170 |
| Burglary | 1 % a month, AP ≥ 2000 | 156 |
| TV contract ended; partner cancels / expires; guest contract broken / expired | | 163; 161, 42; 162, 43 |
| Coach retired | | 12 |
| New Japan / partner guests on your shows | rating ≥ 1200, not December, 5 % | 45-47 |
| **EX Tag League invitation** | **December**, rating ≥ 1500, 2+ wrestlers: Yes sends your top two to New Japan's year-end league | 44 |
| Show cancelled | 5 % per show day | 304 |
| Visiting champion | partnership | 323 |
| Training results, title results | month end | 302, 303 |
| **Wrestling Awards** | January: MVP (300 AP), Rookie of the Year, Best Foreign Wrestler, Match of the Year singles and tag (100 AP each); fans say the award adds a temporary rating bonus | 313-317 |

### 11.2 Wrestler events
| Event | Trigger | Entry |
|---|---|---|
| Injury, discharged, career-ending injury, healed | matches; hospital time | 4-10 |
| Retirement and ceremony | §5.3 | 11, 172 |
| **Fan club** | popularity ≥ 60, 30 % a month; rating +10 | 49 |
| **Film offer** (Yes/No) | popularity ≥ 60, morale ≥ 60, 10 %; +200 AP, popularity +10, rating +50, she misses the month | 50 |
| **One-day police chief** | popularity ≥ 80, morale ≥ 50, 10 %; +50 AP, rating +20 | 51 |
| **Photo book** (Yes/No) | popularity ≥ 70, morale ≥ 20, 10 %, once; +100 AP, rating +20, two event pictures, saved to the gallery | 52-155 |
| Heartbreak | 5 % (fans: after special training); this month's training suffers | 48 |
| Skipping practice, thinking of leaving, missing, leaves | low trust (§5.2) | 157, 14, 158-159, 13 |
| Title warnings, strippings, junior limit, defences abroad | §8.2-8.3 | 26-41, 325 |
| **Bad blood (grudge)** | after matches between different alignments (fans: a higher-rated wrestler losing by a 100+ gap, or bleeding in a close match) | 165 |
| Moves abroad | §5.3 | 328 |
| **Vacation** (Business command) | everyone's trust +10; 75 % of the time a wrestler's own beach scene plays (35 wrestlers have one) | 187-261 |

Media events (film, photo books) cost the wrestler that month's training and shows; fans warn
that too many slow her growth.

---

## 12. Factions: Revolution and Rebel Armies
Both exist in this game (Survivor 2 reportedly dropped the Rebel Army).

- **Revolution Army** (革命軍, entries 15, 17, 19-23, 166, 167, 329): forms (20 % a month) when you
  have **8+ wrestlers** and your top wrestler (21+) and a rising star (19 or younger) have
  different alignments; fans add a grudge between them from a match on your card. Younger
  wrestlers of her alignment join. After 6+ months it demands a **showdown** (normal matches
  only, no invasions meanwhile); afterwards it disbands (truce) or carries on whether it won or
  lost.
- **Rebel Army** (反乱軍, entries 16, 18, 24, 25): forms (20 %) with 6+ wrestlers and at least two
  **EVIL wrestlers with morale under 31**; more low-morale EVIL wrestlers join. No showdown; it
  ends when its members leave. Fans: rebels count at half value for your draw - "it only lowers
  your rating". Fix: raise morale (Praise), change alignment (Instruct), or tour them abroad
  6+ months.

---

## 13. The Final Series and the endings

### 13.1 When
In the April after the set number of years (default 10: "as if year 11", wrestlers one year
older than in March), **once per game** (*code* 0x1bcc48, flag 0x8b5e39). The date can be moved
in the System menu until then. Fans: a 1-year game can't reach the best ending, because New Japan
ranks first until the April of year 2 recalculation; play at least 2-3 years.

### 13.2 What it is
"At last, the strongest promotion will be decided" (entry 301). Each promotion enters one
wrestler in the **Junior** event, a pair in the **Tag** event and one wrestler in the **Singles**
event (fans differ on tournament or league formats); free and foreign wrestlers take part too.
- **Junior eligibility** (*fans*): up to 18 and rating up to 990 - mind the +1 age in April.
- You can't enter wrestlers who spent that March abroad or resting (*fans*).
- HP carries over between rounds, which favours submission specialists (*fans*).
- **Prizes**: 500 / 200 / 100 AP for the top places in each event, multiplied by (years / 10 + 1)
  (×2 at the default 10) (*code* 0x20894c).
- Fans' target to win everything: a singles wrestler around 1500, a tag pair around 1350-1450,
  a junior around 900-990.

### 13.3 The ranking
Every promotion's AP gets a valuation added (*code* 0x20b1f0), then promotions are ranked by
total AP ("With %d total AP, it's %s! Congratulations!!"):

| Item | Adds |
|---|---|
| **Each wrestler rated ≥ 500** | **2 × (rating − 500) AP** |
| Each merch shop | 50 AP |
| Facilities, overseas partners | a table by level (the code may read the wrong index: open question 5) |
| Leading a prefecture or region; national popularity | small amounts |
| Prize money | already in AP |

A bankrupt promotion ranks last. **Money plus many highly rated wrestlers wins**: one 1500-rated
wrestler is worth 2,000 AP.

### 13.4 Endings
| Ending | Condition | What you see |
|---|---|---|
| Normal | your promotion is not first | staff roll (entry 319) |
| Good | first in total AP | staff roll over wrestler pictures (entry 320) |
| **Special** | first in total AP **and** all three Final Series events won **and** first in popularity in **every prefecture** (*fans*; the exact test was not traced) | every wrestler on your roster congratulates you (entry 307), then the staff roll |

Play continues afterwards, up to year 99; the Final Series can't be repeated, so keep a save
from before it.

### 13.5 Gallery
Photo-book and vacation pictures are saved to a gallery (*fans*; the disc holds about 200 event
pictures plus 72 swimsuit photos). No hidden modes, codes or carry-over bonuses are known.

---

## 14. Strategy
From the mechanics above and the fan sources.

**Year 1**
1. Base in **Tokyo or Kanto** if you want the Special ending (best starting popularity, and you
   can overtake New Japan there).
2. **April: sign a cheap overseas partnership** (TWWA or GWA, 500 AP) so imported wrestlers fill
   your cards, and use the **pre-debut window** for transfers if every transfer really succeeds
   then (open question 2). One experienced free agent (around 900 rating) makes a starting ace.
3. Recruit by **tryout at 1 AP** and **scouting** (Shikoku for Minami, Kyushu for Date).
4. Debut quickly with 6 wrestlers; run up to **8 shows a month in the smallest halls you can
   fill** (90 %+ full raises popularity; rent is charged on capacity). Rotate prefectures and
   return after 3-5 months. Two months in the red are survivable; the third is the end.
5. Once you have 5-6 of your own, run an **8-wrestler league** padded with imports: it fixes most
   of the card, puts your ace in the main event, and gives youngsters strong opponents.
6. Autograph sessions on tour raise local popularity.

**Growing wrestlers**
- Growth is front-loaded: develop teenagers; peak around 18-22, decline from 21-23.
- Book trainees **against much stronger opponents** (a 200+ gap gives full experience even in a
  loss; fans' "tag method" pairs a trainee with high-rated imports for a big team gap).
- **Limit matches**: each one costs a tenth of the month's training. Special training is worth
  it with a strong coach.
- Fix stats stuck at 1 before debut with "Weakness" training and a matching coach.
- Keep trust above 6 with **Cheer** and vacations; rest the injured.

**Money and facilities**
- Buy the **Venue** before booking big halls, the **Dorm** when the roster is full, coaches early.
- Ads give the fastest popularity (+3 everywhere for 200 AP). TV is expensive for what it gives.
- Merch shops repay slowly; HQ costs upkeep but opens belts and counts at the end.

**Rivals**
- New Japan dominates early. Fans weaken or bankrupt it: take its overseas partners, book
  lopsided matches so its wrestlers' trust drops, then poach its best (strike right after it has
  spent on facilities). A bankruptcy wipes its regional popularity, which makes the Special
  ending far easier.
- Don't invade lightly: the target invades you back, and invasions can trigger the freeze bug.

**The last years**
- Hoard AP, keep a full roster of high-rated wrestlers, prepare a junior (≤ 990, ≤ 18 in April),
  a tag pair and a singles ace, and keep the champions home in March.
- Save before the Final Series.

---

## 15. Known bugs (*fans*)
- **Invasion freeze**: the game hangs on the start-of-month report when another promotion invades
  you (often a counter-invasion), reportedly with a full roster plus full overseas slots, or when
  an invasion arrives the same month as a coach's retirement notice. Avoid invading (especially
  JWI), handle the coach's retirement first, and **keep two alternating saves**.
- **Bankruptcy freeze**: when a CPU promotion goes bankrupt, some of its wrestlers may never be
  reset and vanish for good.
- Possible code slips found while reading (unconfirmed): the tryout odds table's top row is worse
  than its second; the Final Series facility valuation may read the wrong index; the TV gain
  timing looks inverted; tour costs disagree between text (50) and code (5).

---

## Wrestler-specific scenes

**Photo books** (entries 52-103; the alternates' copies 104-155 share the text). Wrestlers with
one: Suzumi Ishikawa, Chizuru Nagahara, Shinobu Echigo, Hikaru Ogawa, Reiko Kanamori, Sachiko
Kanda (refuses at first), Riyu Kikuchi, Cutie Kanai, Satomi Kojima, Akiko Saito, Thunder Ryuko,
Teddy Cat Hori, Rei Tomizawa, Panther Risako, Beauty Ichigaya, Hitomi Fujishima, Blade Uehara,
Bomber Kishima, Mighty Yukiko, Toshimi Minami, Mimi Yoshihara, Megumi Muto, Tomomi Watanabe,
Kazuki Aiba, Aya Enomoto, Freya Kagami, Kanna Kamui, Mikoto Kusanagi, Shiho Kobayakawa, Makoto
Kondo, Miyuki Sanada, Noel Shiraishi, Mitsuki Sugiura, Michelle Taki, Haruka Date, Kasumi Tsuji,
Foxy Maho, Azumi Nakamori, Yui Naruse, Tsubasa Nomura, Dolphin Hayase, Kazumi Fujiwara (a
tokusatsu-heroine shoot), Royal Hojo, Yuki Hoshina, Succubus Manabe, Shizuka Yajima, Mifuyu
Yagyu, RIKKA, and their alternates.

**Vacation scenes** (entries 188-224; alternates 225-261):

| Wrestler | Scene | Wrestler | Scene |
|---|---|---|---|
| Suzumi Ishikawa | made a bento to share | Mimi Yoshihara | asks for time alone with the Boss |
| Chizuru Nagahara | calls the Boss out to swim | Megumi Muto | not in the mood; the Boss takes her somewhere |
| Shinobu Echigo | stays behind "watching the bags" | Tomomi Watanabe | beach Dance Queen contest |
| Hikaru Ogawa | under the parasol, avoiding the sun | Kazuki Aiba | nervous in front of the sea |
| Reiko Kanamori | over-excited at the sea | Aya Enomoto | shows off her swimsuit |
| Sachiko Kanda | training even on the beach | Freya Kagami | two guys try to pick her up |
| Riyu Kikuchi | swimsuit string coming undone | Mikoto Kusanagi | drifting on the waves |
| Cutie Kanai | found crying | Shiho Kobayakawa | first to the beach |
| Satomi Kojima | missing; the Boss searches | Makoto Kondo | kicking a mat tied to a tree |
| Akiko Saito | special training under the sun | Miyuki Sanada | "It's BLAZING" |
| Thunder Ryuko | wants help catching seafood | Noel Shiraishi | playing in the sand |
| Teddy Cat Hori | lost; the Boss searches | Mitsuki Sugiura | asks the Boss to help her stretch |
| Rei Tomizawa | missing a book sale at "the con" | Michelle Taki | off to a "showdown" for her pride |
| Panther Risako | sunbathing beside the Boss | Haruka Date | "people... stare..." |
| Beauty Ichigaya | buried in the sand "like commoners do" | Kasumi Tsuji | waving far out at sea, goes under |
| Hitomi Fujishima | swimsuit washed away | Blade Uehara | prefers lazing on the beach |
| Bomber Kishima | hauling everyone's luggage | Mighty Yukiko | "I'm gonna be a mermaid" |
| Toshimi Minami | went into town and went missing | | |

Ogre Asahina and Kanna Kamui have no scene of their own.

---

## Open questions
1. Is the ad popularity boost removed after the month?
2. Does every transfer succeed before the debut show?
3. Tour abroad: 5 or 50 AP a month?
4. TV popularity timing: as coded or every N months as the text says?
5. Is the Final Series facility valuation really reading the wrong index?
6. With 10 years set, is the Final Series in "year 11" April as fans say?
7. The exact Special-ending test, and that play continues afterwards.
8. What invasions change; where matches roll injuries; what coach specialties and the tour bus
   do; how CPU promotions recruit.
9. When the vacation scene plays (75 % roll) and how its wrestler is chosen.
10. How the gallery is opened and what it records.
11. Event scripts with no caller found (possibly unused): 38, 39, 160, 164, 168, 171, 177, 186,
    284, 286, 289, 295, 298, 299, and 305 "Expression check" (a developer test of the face
    pictures, for HIDDEN_CONTENT.md).

## Sources
Fan sources (Japanese), collected 2026-10-25; facts marked *fans* come from these:
- sakuhindb strategy page by もろっち (archived:
  https://web.archive.org/web/20240813154121/https://sakuhindb.com/howtoj/7_Wrestll_20Angel_27s/6_A4E2A4EDA4C3A4C1/)
- FAIRY GARDEN, "レッスルエンジェルスサバイバーの攻略":
  http://fairygarden.air-nifty.com/color/survivor-kaisetsu.html
- 2ch strategy threads 01-03 (2006-2009), including a 2009 series quoting the official guide
  『レッスルエンジェルスサバイバー ザ・コンプリートガイド』
- y141.hatenablog.com (2006-09-20), psmk2.net reader reviews, Japanese Wikipedia
  (レッスルエンジェルス).
