# Matches: cards, who wins an exchange, damage and finishes

How a match works in Wrestle Angels Survivor: the controls, the cards, how the game decides
whose move happens, damage, pins and submissions, tag matches, the CPU, and unwatched matches.

**Nothing on this page has been checked in the game yet** unless marked. Findings are marked
*code* (read from the executable; RAM address given, = file offset + 0xfff80 in `SLPM_662.39`),
*text* (on-screen text), *fans* (Japanese strategy sources from 2006-2009, some quoting the
official guide) or *inferred*. The fans' description of the system agrees with the code wherever
both cover the same point. The SNES ancestor's rules are in the Super Wrestle Angels project's
docs/MATCHES.md; this game is the same card battle at heart, with the differences in §13.

## Contents
- [In plain words](#in-plain-words)
- [1. Before the match](#1-before-the-match) · [2. Controls and the screen](#2-controls-and-the-screen)
- [3. The cards](#3-the-cards) · [4. Who wins an exchange](#4-who-wins-an-exchange)
- [5. Which move happens](#5-which-move-happens) · [6. Damage and health](#6-damage-and-health)
- [7. Pins, cradles and submissions](#7-pins-cradles-and-submissions)
- [8. Time limits](#8-time-limits) · [9. Tag and six-woman matches](#9-tag-and-six-woman-matches)
- [10. The CPU](#10-the-cpu) · [11. Matches you don't watch](#11-matches-you-dont-watch)
- [12. Strategy](#12-strategy) · [13. Differences from the SNES game](#13-differences-from-the-snes-game)
- [14. Quirks and possible bugs](#14-quirks-and-possible-bugs) · [Reference](#reference)

## In plain words

A match is a card game played one round at a time. Each round is an **exchange**.

- **You hold 5 cards.** Each card is a **move type** - Throw, Hold, Power, Strike, Aerial, or
  the rarer Finisher, Double and Other - with a **number from 1 to 10** (10 shows as **A**).
  Each exchange both corners play one card, and you pick which move of that type to try.
- **The higher score wins the exchange, and only the winner's move happens.** A card's score is
  **its number + your attack rating in that type − the opponent's defence rating in that type.**
  The Atk/Def ratings on the match screen are exactly these numbers. There is **no dice roll**:
  the only luck is in the cards you're dealt.
- **Big moves are hard to land on a fresh opponent.** If the move's level is higher than how
  much health she has *lost* (in tenths of her bar), the whole level is taken off your score.
  At full health every move pays; once she's down to 70%, level 1-3 moves are free, and so on.
  **Small moves early, big moves late.**
- **A Finisher card always wins**, and it can't be reversed. If both corners play one, the one
  who lost the previous exchange wins. Finisher cards only start coming once your wrestler is
  hurt; high **grit** makes them likelier.
- **Taking a beating builds a comeback:** after the opponent wins 3, 4, 5, 6, 7+ exchanges in a
  row, your card gets +1, +3, +5, +7, +9. **Ties** go to whoever lost the last exchange.
- **Some big moves can be reversed** by the loser (a Backdrop into a Body Press, a Moonsault
  into raised knees). Low cards and big moves get reversed more often.
- **To win, pin her or make her give up.** A pin almost never works while she has health left;
  at **0 health** only her grit can save her. Cradles are the exception: they can steal a win
  once she's below 40%. In a hold, she chooses each round to crawl to the ropes or try to break
  free. There's **no KO, count-out or disqualification**, and if the exchange limit runs out the
  match is a **draw**.
- **Matches you choose not to watch aren't played at all**: the game compares the two sides'
  ratings and rolls the result.

---

## 1. Before the match
*Code* (0x484a30 control table) and *text*.
- On the match-up screen, move the cursor onto a wrestler and press **L1/R1** to change who
  controls her:
  - **COM** - the computer plays her.
  - **1P-S-AUTO / 2P-S-AUTO** - you pick the card; the game picks the move and shows it as you
    browse your cards.
  - **1P-MANUAL / 2P-MANUAL** - you pick the card and the move.
  - One controller can't run both corners. Fans warn that choosing 2P while holding pad 1 leaves
    you unable to control the match (*fans*).
- On the top button, L1/R1 switch **Watch / Skip**; Skip decides the match without playing it
  (§11). Then press ○ on **Start Match**.
- **Special Match levels** (LEVEL 1/2/3) set each wrestler's growth stage (ages 15/18/20); they
  don't change how the CPU plays (*code*).

## 2. Controls and the screen
*Code* (input states 0x1ddc10-0x1de990) unless marked.

| Where | Button | What it does |
|---|---|---|
| Your cards | LEFT / RIGHT | browse the hand |
| | ○ | play the highlighted card |
| | □ | command list: **Pin**, **Tag**, **Return** |
| | R1 (hold) | hide the cards and gauges to see the wrestlers; the match waits *(R1 also hides the message window during events - verified in game)* |
| Move list (MANUAL) | UP / DOWN, ○ / × | choose the move / back to the cards |
| Command list | UP / DOWN, ○ | toggle Pin or Return for this exchange; Tag asks which partner |
| Double card | UP / DOWN, ○ | choose the partner, then the double-team move (□ = her details) |
| Caught in a hold | UP / DOWN, ○ | **Reach the Ropes** or **Break Free** (§7.3) |
| Messages | ○ | move the commentary along |

- **Commands only happen if your card wins the exchange** (certain for Tag; *inferred* for
  Pin and Return). In the ring you get Pin (and Tag in team matches); outside you only get
  Return.
- There is **no START menu** in a match and no way to skip it once started (*code*).
- **The screen** (*text*): each wrestler's health bar with LEG and ARM meters under it; both
  wrestlers' **Atk / Def ratings** for Throw, Hold, Power, Strike and Aerial (1-9, then A-E =
  10-14, S = 15); the two cards played this exchange; a small ring showing where the wrestlers
  are; and during a move, its name with the attacker's name and "OFFENSE".

## 3. The cards
*Code* (deal 0x1dbcb0; hand in the match block, 8 bytes a card) unless marked.

| Type | Score uses | Notes |
|---|---|---|
| **Throw, Hold, Power, Strike, Aerial** | your attack − her defence in that type | the normal cards |
| **Other** | your Speed − her Speed | weapons, dirty tricks (outside the ring, or wrestlers who use them) |
| **Finisher** | always wins | §4.2 |
| **Double** | +2, plus your team's winning streak | tag and six-woman only (§9) |

**The deal.** A played card is replaced with a new one:
- **Type** follows your wrestler's attack ratings, ranked: **25%** her best type, **21%** second,
  **17%** third, **15%** fourth, **14%** fifth, **8%** Other. So specialists see their best moves
  most (fans quote the same odds from the guide).
- **Number** comes from a shuffled 180-card deck per side, weighted toward **7-8**; 10 shows as A.
- **Finisher cards** appear once she's hurt: chance = grit + 7 − 2 × (her health in tenths).
  At most **two per match**, and the second only when she is 6 or more tenths behind.
- **Double cards** (1 in 6) only in tag and six-woman matches, once she has taken damage and
  while the opponent is below 80% health.

## 4. Who wins an exchange
*Code* (0x1e0e60, scores 0x1e8590 / 0x1e8c40).

### 4.1 The score
```
score = card number
      + attack rating in the card's type − the opponent's defence rating in that type
      − the move's level, if level > (10 − the opponent's health in tenths)   "level cost"
      + comeback bonus  +1 / +3 / +5 / +7 / +9 after the opponent won 3 / 4 / 5 / 6 / 7+ in a row
      + 3 to +6 for some moves against a downed opponent; −1 for some against a standing one
        (Guillotine Drop, Moonsault, Shooting Star Press, Missile Kick, Boston Crab, Scorpion,
        Dragon Screw and others)
      + the tag bonus when you ask to tag (§9)
Other cards: Speed − Speed instead of attack − defence.
Double cards: +2, +2 per exchange your side has won in a row (up to +8), −2/−4/−6 after the
opponent's streak.
```
- **The higher score wins**; only the winner's move happens. **Ties** go to the side that lost
  the previous exchange (a coin flip at the start).
- **No random term, no difficulty bonus**, no advantage for the CPU (*code*; fans long suspected
  the CPU draws better cards - the deal is the same for both).
- The success % the game shows you is a rough guide only (§14).

### 4.2 Finisher cards
- A finisher card **beats any other card** and can't be reversed. If both sides play one, the
  side that lost the previous exchange wins (0x1e8b50).
- Its move does **+40 damage** (+15 for a hold) and ignores the level cost - so it is best saved
  for a big move that would otherwise be too costly (*code*, *fans*).

### 4.3 Reversals
About 25 big moves can be turned around by the loser (0x1e8dd0), e.g. Backdrop → Body Press,
Powerbomb → huracanrana, Moonsault → raised knees or a crash. Chance:
```
reversal % = (move level + 3) − (10 − the loser's health in tenths) + 2 × the loser's Dexterity
           + a bonus if the loser is down + (10 − the winner's card number)
```
Big moves and low cards are reversed more; a badly hurt wrestler reverses less. A reversal counts
as the reverser's win.

## 5. Which move happens
- **MANUAL:** after the card, you choose from your moves of that type that can be done from the
  current position (standing, down, at the ropes, outside...).
- **S-AUTO and the CPU** (0x21fcb0): the biggest move that avoids the level cost, sometimes a
  bigger one when the card is far ahead.
- The level cost (§4.1) is why **small moves win early** and big moves become possible as the
  opponent wears down: at full health every move pays its level; at 70% levels 1-3 are free; at
  50% levels 1-5; at 0, everything.
- Each learned move also adds 10 to the wrestler's rating (docs/MANAGEMENT.md §6).

## 6. Damage and health
*Code* (damage 0x1e9460).
- **Health** = 50 + 10 × Strength + 30 × Stamina. Two hidden **body meters**, upper body (ARM)
  and legs (LEG), are each half that.
- **Damage** = the move's damage at its level + the attacker's Strength. Extras:
  - **finisher card +40** (+15 for a hold, first round only);
  - **outside the ring**, Strength counts twice;
  - against a **bleeding** wrestler, + (10 − her health in tenths).
- **Holds** take a little health and a lot from the ARM or LEG meter, every round they last
  (§7.3).
- **Knockdown**: chance (damage − 40) / 80 when one exchange does more than 40.
- **Outside**: a move that pushes past the ropes can take both wrestlers outside (5-35% by their
  alignments). There is **no count-out**; use **Return** to go back in.
- **Recovery each exchange**: your Recovery stat (1-10 health) in singles; half in tag; none for
  the legal wrestler in a six-woman match. Partners on the apron recover only below half health.
  Bleeding halves it. Kicking out of a pin gives a one-time burst (×1.5 at 2, ×2 at 2.5, ×3 at
  2.8).

## 7. Pins, cradles and submissions
*Code* (pin 0x1ea120, count 0x1ea300).

### 7.1 Pins
- Each move has a **pin type**: never, only with **PIN** chosen, **automatic** (big suplexes,
  bombs, flying presses), or **cradle**.
- **PIN with an ordinary move** goes for the cover with this chance, by the opponent's health in
  tenths: 0 → 100%, 1 → 90%, 2 → 40%, 3 → 20%, 4 → 10%, 5 → 5%, 6 → 2%, 7 → 1%, higher → never.
- **During the count** she can kick out at 1 or 2 (chance from her health), grab the ropes if
  you're beside them, or be saved by a partner. **While she has any health left she kicks out
  at least 89% of the time.**
- **At 0 health only grit saves her**: 2 × grit % in singles, 1.4 × in tag, 1 × in six-woman.
  Fans call the last-second escapes "2.9 kick-outs" (*fans*).

### 7.2 Cradles
Small Package, Inverted Cradle, Rolling Cradle and La Magistral can't win at 40% health or more;
below that they win with **10 × level / (her health in tenths + 1) %**, health left or not. The
classic upset finish.

### 7.3 Submissions
Each round of a hold, the wrestler caught in it chooses:
- **Reach the Ropes** - crawl one step toward the ropes; at the ropes, the hold is broken (a hold
  at the ropes is always broken).
- **Break Free** - Dexterity / 2 + her health in tenths + 2d6 + 2 per earlier try, against the
  holder's Hold attack + 2d6.

If she stays in, she may **give up**: chance (Hold attack − Hold defence + level) / 2, growing
fast once her health or the attacked body part (ARM/LEG meter) drops below 30%. A hold lasts at
most (level + 1) / 2 rounds. Submissions can win with health left.

## 8. Time limits
*Code* (table 0x582d90). The limit counts **exchanges**, not minutes:

| Match | Exchanges |
|---|---|
| Singles | 40 (48 for the main event, *inferred*) |
| Tag | 50 / 60 |
| Six-woman | 66 / 80 |
| Tournaments | none |

**Time up is a draw.** In matches that can't be drawn, the lower-rated side is given the win.
Code for deciding a time-up on points exists but nothing switches it on.

## 9. Tag and six-woman matches
- One **legal** wrestler per side holds the cards; the controller follows whoever is legal, so
  partners can be on different pads (*code*).
- **Tag** (from the command list) happens only if your card wins the exchange. Asking to tag adds
  the gap between your partner's health and yours, in tenths, to your score - doubled when it's
  5 or more, and subtracted if your partner is more hurt than you.
- **Double cards** (in the ring only): choose the partner and a double-team move. The five
  double-team moves have requirements on the pair (fans: a morale gap and combined rating).
- Partners can break up pins; the ARM/LEG meters aren't reduced in team matches.

## 10. The CPU
*Code* (cards 0x21f710, moves 0x21fcb0).
- Plays the card with the best **number + advantage**, plus a bonus for its favourite types
  (each wrestler has a "card strategy"). No randomness except the finisher: it plays one with a
  20 / 40 / 60 / 80 / 100% chance at exchanges 1-5 and later - in practice almost at once.
- Moves: the biggest that avoids the level cost.
- **Pins** whenever the opponent is at 70% health or less; **tags out** to a fresher partner;
  returns to the ring after a few exchanges outside.
- **No difficulty setting** changes how the CPU plays.

## 11. Matches you don't watch
*Code* (0x203470). Nothing is simulated. Each side gets a score:
```
score = rating + 10 × her best style advantage over the opponent + 5 × grit (+50 for the
        champion in a title match)
```
and the gap picks the winner from a table: even → 50/50, +51-100 → about 62%, +251 → certain.
These matches are never drawn. The fans' "auto-win unwatched matches" code skips this roll.

## 12. Strategy
From the mechanics above and the fans (*fans* marks theirs).
1. **Early on, throw away weak cards** while the opponent lands small moves: early damage is low,
   and you build the comeback bonus. Then **rush with your best cards** once her health is down
   and big moves no longer pay the level cost (*fans*).
2. **Play to your strengths:** your best types come most often (25%), and a card wins on attack −
   defence. Off-specialty cards are best in the type where her **defence** is lowest (*fans*).
3. **Save the finisher card** for a big move that would otherwise be too costly; don't waste it
   on a submission at the ropes, which is always broken (*fans*).
4. **Pins need her near 0.** Don't count on a pin above 20-30% health; use a cradle to steal a
   win when she's below 40%.
5. **Submissions**: hold in the centre, after a knockdown, with high-level holds; target a worn
   ARM or LEG meter (*fans*).
6. **Tag**: let the weaker partner take the hits, then tag in the fresh one for the tag bonus;
   play Double cards after a run of wins (*fans*).
7. **Against stronger opponents**, expect "2.9" kick-outs from high grit; cradles and automatic-pin
   moves are your best chance (*fans*).
8. **Growth** (docs/MANAGEMENT.md §6): matches against much stronger opponents teach the most,
   even in a loss; the fans' "+210" and "tag method" tricks book trainees against sides rated
   210+ (singles) or 410+/610+ (tag / six-woman) higher (*fans*).

## 13. Differences from the SNES game
Compared with Super Wrestle Angels' docs/MATCHES.md (*code* in both games):
- **You can choose the move** (MANUAL). In the SNES game the card's type alone decided it: the
  game took the biggest move the opponent was worn down enough for, as S-AUTO does here.
- **The level cost is the same rule**, but the SNES game added the difficulty to human players'
  side of it; here there is no difficulty term anywhere in a match.
- **There is a time limit** (§8); the SNES game had none. Neither has a count-out.
- **The Guillotine/Moonsault bug is fixed**: in the SNES game they got +255 against a standing
  opponent and won almost every exchange; here they get −1, as intended. The SNES CPU's +255 on
  double-team cards is gone too.

## 14. Quirks and possible bugs
*Code* readings; none checked in the game yet.
- **The success % shown** while choosing ignores how far the card is from the midpoint, so it is
  only a rough guide.
- **Lariat reversal** compares the winner's Hold rating where the loser's was probably meant.
- **Pin kick-out roll** applies only when the move's level is below half the pinner's attack
  rating, which looks inverted.
- **Unwatched tag/six-woman matches** give +20 both to the side above and the side below the
  other (looks like a slip).
- Fans report some wrestlers always lose ties because of their card strategy (*fans*); the code's
  tie rule (the loser of the last exchange wins) doesn't show such a case.

## Reference
- **Match state** (*code*): 0x8e51a0 (sides 0x42b8 apart; each wrestler's hand of 5 cards, 8 bytes
  each: type at +2, number at +4). Match random numbers come from their own generator (0x1c9d30).
- **Card types:** 0 Throw, 1 Hold, 2 Power, 3 Strike, 4 Aerial, 5 Finisher, 6 Double, 7 Other.
- **Ratings** (per wrestler): Throw/Hold/Power/Strike/Aerial attack and defence, then Strength,
  Dexterity, Stamina, Recovery, Speed; 1-15 (15 = S). Links: Throw-Strength, Hold-Dexterity,
  Power-Stamina, Strike-Recovery, Aerial-Speed (docs/MANAGEMENT.md §5).
- **Ring position**: 0 centre, ±2 at the ropes, ±3 outside.
- **Moves**: 105 (names 0x47d760, data 0x4a4cec): type, level 1-9, damage per level, pin type,
  where it can be done, reversal. docs/HIDDEN_CONTENT.md lists the unused ones.
