#!/usr/bin/env python3
"""Data for the player's guide (docs/guide/index.html), read from the original executable.

  guidedata.py [--check]        fill the page's data block (tools/pagedata.py)
  guidedata.py --json FILE      write the data to FILE instead (the page isn't needed)

Every number comes from the original's tables in extracted/SLPM_662.39 (RAM = file offset +
0xfff80); every English name from translation/ - roster.csv (wrestlers, finishers), exe.csv (move
names, descriptions, belt and title words), venues.csv, and tools/screens.py (the nine CPU
promotion names, which it writes in place). Untranslated names fall back to the Japanese, as the
patch shows them. While docs/guide/index.html doesn't exist, --check passes (nothing to check).

*From the code* (private/research/hidden_roster.md, match_damage.md, systems.md):
  0x47d930 / 0x499350  roster records (tools/roster.py): after the name, 3 x 15 stat bytes, then
                       6 groups (Throw, Hold, Power, Strike, Aerial, Other) x 5 move slots of
                       (move id, level), id 0 = empty; then personality bytes (loader 0x1947a0):
                       +0 finisher slot (0-29, that slot's move is renamed), +1 CPU card style,
                       +3 grit, +4 alignment; domestic only: +10 starting age, +11 start type,
                       +12 debut year.
  grades               the 15 stat bytes [Throw atk, def, Hold atk, def, Power, Power, Strike,
                       Strike, Aerial, Aerial, Str, Dex, Stam, Recov, Speed], 1-15 (10-14 show as
                       A-E, 15 as S). Exhibition (0x197850): ids < 200 take stat group 2 scaled by
                       the LEVEL percentage (table 0x47e8c0, 50/75/100 for LEVEL1/2/3, floor, at
                       least 1); foreign wrestlers take group 0 unscaled. The roster here holds
                       the LEVEL3 (100 %) values, which the match screen shows.
  0x47d760             move names (108 pointers; group starts at 0x47d910); move id 1-77 = name
                       index id - 1, reversal moves 78-105 = name index id + 2
  0x4a4cec             move data, 28 bytes per move id - 1: 0-1 reversals, 2 what it hits, 3-20
                       nine (HP, meter) damage pairs by level, 21 -1 vs standing, 22 bonus vs a
                       downed foe, 23 pin type, 25 bleeding %, 26 knockback, 27 where it can be done
  0x19a220-0x19a320    which wrestlers each CPU promotion starts with (calls to 0x198190)
  0x4a4b20             the nine CPU promotions, 0x30 bytes: name, abbreviation (+0x16), AP
                       (+0x20), home venue (+0x22 bits 0-8), touring type (+0x24), description
                       pointers (+0x28, +0x2c)
  0x4a6290             7 foreign groups x (6 originals, 6 successors)
  0x47e4c0 / 0x4a6250  foreign promotions: names (24 bytes each), partnership values
  0x499348 / 0x4a6d98  creating your own belts: costs; (rating, wrestlers) needed
"""
import argparse
import csv
import json
import struct
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import exefile  # noqa: E402
import pagedata  # noqa: E402
import paths  # noqa: E402
import roster  # noqa: E402
import screens  # noqa: E402

EXE = 'SLPM_662.39'
MOVE_NAMES, GROUP_STARTS, MOVE_DATA, MOVES = 0x47d760, 0x47d910, 0x4a4cec, 105
LEVEL_PCT = 0x47e8c0           # words; exhibition LEVEL n (0-2) of talent t: [60 + 5 t + n]
ALIGNMENTS = 0x47c8a0          # pointers to GOOD / NORMAL / EVIL
PROMOS, PROMO_SIZE, PROMO_COUNT = 0x4a4b20, 0x30, 9
START_CODE = (0x19a220, 0x19a338)   # per-promotion starting wrestlers; a1 = 1 on entry (0x19a1ec)
ADD_WRESTLER = 0x198190
PLAYER_NAMES = 0x47e2e0        # 4 pointers: suggested names for your promotion
FOREIGN_GROUPS = 0x4a6290
FOREIGN_NAMES, FOREIGN_VALUES, FOREIGN_STYLES = 0x47e4c0, 0x4a6250, 0x4981d0   # styles: 6 texts 0x60 apart
BELT_COSTS, BELT_NEEDS = 0x499348, 0x4a6d98
BELT_TYPES = (0x498b50, 0x498b58, 0x498b60)
TITLE_FORMATS = (0x4a58e8, 0x4a5900, 0x4a5920, 0x4a5938, 0x4a5950, 0x4a5970)

# Move groups by name index (the starts at GROUP_STARTS). The Other group's list shows its first
# 10 (0x195c90); the next 5 are the tag double-team moves, then Pin and Break Up (match actions).
TYPES = ['Throw', 'Hold', 'Power', 'Strike', 'Aerial', 'Other', 'Reversal']
OTHER_LISTED, DOUBLES = 10, 5
PIN = {0: 'no', 1: 'req', 2: 'auto', 3: 'cradle', 4: 'auto'}
HITS = {1: 'hp', 3: 'arm', 5: 'leg'}     # HP only, HP + upper-body meter, HP + leg meter
KNOCKBACK = {0: '', 1: 'step', 2: 'two steps', 3: 'swap', 4: 'centre', 5: 'hold'}
WHERE = {0: 'ring', 1: 'any', 2: 'out'}  # 2: ropes and outside only (Chair Shot, Ring Post, Body Throw)
START_TYPES = {0: 'rookie', 1: 'veteran', 2: 'prospect', 3: 'njwp'}
CPU_STYLES = ['Strike, Aerial', 'Power, Strike', 'Throw, Hold']   # table 0x5849d8 (match_controls.md)
TOURING = ['nationwide', 'mid-size', 'big cities', 'regional']    # inferred from the descriptions


def u16(d, o):
    return struct.unpack_from('<H', d, o)[0]


class Exe:
    def __init__(self):
        p = paths.EXTRACTED / EXE
        if not p.exists():
            sys.exit(f'{paths.show(p)} not found - run tools/extract.py first')
        self.d = p.read_bytes()

    def at(self, addr, n):
        o = exefile.off(addr)
        return self.d[o:o + n]

    def u16(self, addr):
        return u16(self.d, exefile.off(addr))

    def s16(self, addr):
        return struct.unpack_from('<h', self.d, exefile.off(addr))[0]

    def u32(self, addr):
        return struct.unpack_from('<I', self.d, exefile.off(addr))[0]

    def sjis(self, addr, n=64):
        return self.at(addr, n).split(b'\0')[0].decode('cp932')


def read_csv(name):
    with open(paths.TEXT / name, encoding='utf-8', newline='') as f:
        return list(csv.DictReader(f))


def english(rows, key):
    """{key: English, or the Japanese where it isn't translated} of a text table."""
    return {r[key]: r['english'] or r['japanese'] for r in rows}


def half(t):
    return unicodedata.normalize('NFKC', t).strip()


def last_line(t):
    return t.split('\\n')[-1]


def moves(exe, text):
    starts = [(exe.u32(GROUP_STARTS + 4 * g) - MOVE_NAMES) // 4 for g in range(7)]
    if starts != [0, 12, 24, 36, 48, 60, 80]:
        sys.exit(f'guidedata: move group starts {starts} are not the original\'s')
    out = []
    for mid in range(1, MOVES + 1):
        idx = mid - 1 if mid <= 77 else mid + 2
        g = max(i for i, s in enumerate(starts) if idx >= s)
        t = TYPES[g]
        if g == 5 and idx - starts[5] >= OTHER_LISTED:
            t = 'Double' if idx - starts[5] < OTHER_LISTED + DOUBLES else 'Action'
        ptr = exe.u32(MOVE_NAMES + 4 * idx)
        rec = exe.at(MOVE_DATA + 28 * (mid - 1), 28)
        dmg = [(lv + 1, rec[3 + 2 * lv], rec[4 + 2 * lv]) for lv in range(9)
               if rec[3 + 2 * lv] or rec[4 + 2 * lv]]
        m = {'id': mid, 'n': text.get(f'{ptr:#x}', exe.sjis(ptr)), 'ja': exe.sjis(ptr), 't': t,
             'pin': PIN[rec[23]], 'at': WHERE[rec[27]]}
        if dmg:
            m['lv'] = [dmg[0][0], dmg[-1][0]]
            m['hp'] = [h for _, h, _ in dmg]
            if rec[2] in (3, 5):
                m['mt'] = [x for _, _, x in dmg]
        m['hit'] = HITS.get(rec[2], rec[2])
        rev = [b for b in rec[:2] if b]
        if rev:
            m['rev'] = rev
        if rec[25]:
            m['bl'] = rec[25]
        if rec[26]:
            m['kb'] = KNOCKBACK[rec[26]]
        if rec[21]:
            m['vs'] = -1 if rec[21] == 0xff else rec[21]
        if rec[22]:
            m['vd'] = rec[22]
        out.append(m)
    return out


def starting_rosters(exe):
    """{promotion index: [wrestler ids]}: runs the code at START_CODE once per promotion (s4 =
    the promotion, a1 = 1 as on entry), following its branches and noting a1 at each call to
    ADD_WRESTLER. Only the few instructions found there are understood; anything else stops."""
    regs = {0: 'zero', 2: 'v0', 5: 'a1', 20: 's4'}
    out = {}
    for p in range(PROMO_COUNT):
        reg, pc, pending, got = {'zero': 0, 'a1': 1, 's4': p}, START_CODE[0], None, []
        for _ in range(200):
            if not START_CODE[0] <= pc < START_CODE[1]:
                break
            w = exe.u32(pc)
            op, rs, rt = w >> 26, (w >> 21) & 31, (w >> 16) & 31
            imm = (w & 0xffff) - ((w & 0x8000) << 1)
            jump = None
            if w == 0 or (op == 0 and w & 0x3f == 0x2d and rt == 0 and (w >> 11) & 31 == 4):
                pass                                            # nop; move a0, x
            elif op == 9 and rs == 0 and rt in regs:
                reg[regs[rt]] = imm                             # li rt, imm
            elif op in (4, 5) and rs in regs and rt in regs:    # beq / bne
                if (reg[regs[rs]] == reg[regs[rt]]) == (op == 4):
                    jump = pc + 4 + 4 * imm
            elif op == 3:                                       # jal
                if (w & 0x3ffffff) << 2 == ADD_WRESTLER:
                    got.append(reg['a1'])
            else:
                sys.exit(f'guidedata: unexpected instruction {w:#010x} at {pc:#x} - not the original code?')
            if pending is not None:                             # this was a delay slot
                pc, pending = pending, None
            else:
                pc += 4
                if op in (4, 5) and jump is not None:
                    pending = jump
        out[p] = got
    return out


def wrestlers(exe, names, start_rosters):
    pct = exe.at(LEVEL_PCT, 124 * 4)
    word = lambda i: struct.unpack_from('<i', pct, 4 * i)[0]
    align = [exe.sjis(exe.u32(ALIGNMENTS + 4 * i)) for i in range(3)]
    groups = {}
    for g in range(7):
        for s in range(12):
            groups[exe.s16(FOREIGN_GROUPS + 2 * (12 * g + s))] = g
    promo_of = {w: p for p, ids in start_rosters.items() for w in ids}
    out, levels = [], set()
    blob = exefile.off(roster.BLOB)
    recs = [exe.d[blob + o:blob + o + s] for o, s in roster.records(exe.d)]
    ids = {u16(r, 0) for r in recs}
    for k, rec in enumerate(recs):
        wid = u16(rec, 0)
        if wid >= 400:
            continue
        span = roster.fields(rec)
        p = span['name'][1]
        stats = [b & 0xf for b in rec[p:p + 45]]
        p += 45
        slots = []
        for _ in range(30):
            slots.append((rec[p], rec[p + 1]) if rec[p] else None)
            p += 2
        post = rec[p:]
        domestic = wid < 200
        talent = None
        if domestic:
            talent = (post[17] & 7)
            levels.add(tuple(word(60 + 5 * talent + n) for n in range(3)))
        g = stats[30:45] if domestic else stats[0:15]
        fslot = post[0] & 0x1f
        w = {'id': wid, 'n': names.get(f'{k}.name', roster.text(rec, span['name'])),
             'ja': roster.text(rec, span['name'])}
        if 'finisher' in span:
            w['fin'] = names.get(f'{k}.finisher', roster.text(rec, span['finisher']))
            w['fja'] = roster.text(rec, span['finisher'])
            if slots[fslot]:
                w['fm'] = slots[fslot][0]
        w['g'] = [max(1, x) for x in g]
        w['mv'] = [list(x) for x in slots if x]
        w['al'] = align[(post[4] & 3)] if (post[4] & 3) < 3 else post[4] & 3
        w['grit'] = post[3] & 0xf
        w['cpu'] = post[1] & 3
        if wid % 200 > 100 and wid - 100 in ids:                 # 101-152, 301-343
            w['alt'] = wid - 100
        if domestic:
            st = post[11] & 3
            w['st'] = START_TYPES[st]
            if st == 0:
                w['dy'] = post[12]
            if post[10] & 0x3f:
                w['age'] = post[10] & 0x3f
        if wid in promo_of:
            w['p'] = promo_of[wid]
        if wid in groups:
            w['fg'] = groups[wid]
        out.append(w)
    if len(levels) != 1:
        sys.exit(f'guidedata: the LEVEL percentages differ by talent ({levels}) - the roster needs them per wrestler')
    return out, list(levels.pop())


def promotions(exe, text, venues, start_rosters):
    en = {a: new for a, _, new, _ in screens.STRINGS if PROMOS <= a < PROMOS + PROMO_SIZE * PROMO_COUNT}
    out = []
    for i in range(PROMO_COUNT):
        a = PROMOS + PROMO_SIZE * i
        ja = exe.sjis(a, 22)
        d1, d2 = exe.u32(a + 0x28), exe.u32(a + 0x2c)
        out.append({'i': i, 'n': en.get(a, ja), 'ja': ja, 'ab': half(exe.sjis(a + 0x16, 10)),
                    'ap': exe.u16(a + 0x20), 'home': venues.get(str(exe.u16(a + 0x22) & 0x1ff)),
                    'tour': TOURING[exe.at(a + 0x24, 1)[0]],
                    'd': [text.get(f'{x:#x}', exe.sjis(x)) for x in dict.fromkeys((d1, d2)) if exe.sjis(x)],
                    'w': start_rosters[i]})
    return out


def foreign(exe, text):
    out = []
    for i in range(6):
        style = FOREIGN_STYLES + 0x60 * i
        out.append({'n': half(exe.sjis(FOREIGN_NAMES + 24 * i, 24)), 'v': exe.s16(FOREIGN_VALUES + 2 * i),
                    'st': last_line(text.get(f'{style:#x}', exe.sjis(style, 0x60)))})
    return out


def belts(exe, text):
    return {'own': [{'ap': exe.u16(BELT_COSTS + 2 * i), 'rt': exe.u16(BELT_NEEDS + 4 * i),
                     'roster': exe.u16(BELT_NEEDS + 4 * i + 2)} for i in range(3)],
            'types': [text.get(f'{a:#x}', exe.sjis(a)) for a in BELT_TYPES],
            'titles': [text.get(f'{a:#x}', exe.sjis(a)) for a in TITLE_FORMATS]}


def build():
    exe = Exe()
    text = english(read_csv('exe.csv'), 'id')
    names = english(read_csv('roster.csv'), 'key')
    venues = english(read_csv('venues.csv'), 'key')
    starts = starting_rosters(exe)
    roster_, levels = wrestlers(exe, names, starts)
    return {
        'notes': {
            'g': 'Throw, Hold, Power, Strike, Aerial (attack, defence each), Str, Dex, Stam, Recov, '
                 'Speed; 1-15, 10-14 show as A-E, 15 as S; exhibition LEVEL3 values',
            'lvl': f'ids under 200: LEVEL1/2/3 = {levels[0]}/{levels[1]}/{levels[2]} % of g, '
                   'rounded down, at least 1; foreign wrestlers (200+) are the same at every LEVEL',
            'cpu': CPU_STYLES,
            'st': 'start type: rookie (appears at 15 in debut year dy), veteran (free agent or CPU '
                  'ace from the start), prospect (tryout pool from year 1), njwp',
            'fg': 'foreign group (0-6) of table 0x4a6290; which foreign promotion is which is not known',
            'pin': 'no / req (only with PIN chosen) / auto / cradle',
            'at': 'ring (in the ring only) / any / out (ropes and outside only)',
            'hit': 'hp / arm (also the upper-body meter, mt) / leg (also the leg meter, mt)',
        },
        'levels': levels,
        'wrestlers': roster_,
        'moves': moves(exe, text),
        'promotions': promotions(exe, text, venues, starts),
        'player_names': [text.get(f'{exe.u32(PLAYER_NAMES + 4 * i):#x}') for i in range(4)],
        'foreign': foreign(exe, text),
        'belts': belts(exe, text),
    }


def summary(data):
    w = data['wrestlers']
    print(f"guidedata: {len(w)} wrestlers ({sum(1 for x in w if 'alt' in x)} 2P alternates, "
          f"{sum(1 for x in w if 'fin' in x)} finishers), {len(data['moves'])} moves, "
          f"{len(data['promotions'])} CPU promotions ({sum(len(p['w']) for p in data['promotions'])} "
          f"starting wrestlers), {len(data['foreign'])} foreign promotions, "
          f"{len(data['belts']['own'])} belt tiers")


def main(argv=None):
    argv = paths.configure(sys.argv[1:] if argv is None else argv)
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0], epilog=paths.FOLDER_HELP,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--check', action='store_true', help='only check that the page is up to date')
    ap.add_argument('--json', type=Path, metavar='FILE', help='write the data to FILE instead of the page')
    args = ap.parse_args(argv)
    data = build()
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding='utf-8')
        summary(data)
        print(f'guidedata: written to {paths.show(args.json)}')
        return 0
    page = paths.DOCS / 'guide' / 'index.html'
    if not page.exists():
        print(f'guidedata: {paths.show(page)} does not exist yet - nothing to fill')
        return 0
    if pagedata.write(page, data, check=args.check) and args.check:
        print(f'guidedata: {paths.show(page)} is up to date')
    elif not args.check:
        summary(data)
    return 0


if __name__ == '__main__':
    sys.exit(main())
