#!/usr/bin/env python3
"""Who says what: every wrestler's voiced lines, for a voice-consistency pass.

  voices.py [--out DIR]     write DIR/<case>_<name>.md (default private/voices/) and an index

*From the code*: per-wrestler scenes jump through a table of 120 labels (206 with the foreign
wrestlers; script op 0x14) indexed by the wrestler's "voice case", which 0x1aede0 computes from
her roster id: ids 1-99 -> id-1, 100-199 -> id-33, 200-299 -> id-81, 300+ -> id-138. So cases
0-67 are ids 1-68, 68-119 the 2P/B alternates 101-152 (who share the A-type's lines), 120-205
the foreign wrestlers. The `case N`
comments in translation/script/*.txt are op 0x3f branch numbers, not these cases. Scenes with
several lines per wrestler hold 2-5 such tables back to back (label = case + 120 n).

Each file lists, per scene, the wrestler's lines: the block id in translation/script (where the
English is edited; a message used several times lives in the file of its first use), the
Japanese, the English, and how many wrestlers share the message (a shared line must suit all).
"""
import argparse
import csv
import struct
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import paths  # noqa: E402
import script  # noqa: E402

EXE = '/SLPM_662.39'


def case_of(rid):
    if rid < 100:
        return rid - 1
    if rid < 200:
        return rid - 33
    if rid < 300:
        return rid - 81
    return rid - 138


def case_names():
    """{case: English name} from roster.csv (the wrestlers' name rows)."""
    out = {}
    with open(paths.TEXT / 'roster.csv', encoding='utf-8', newline='') as f:
        for r in csv.DictReader(f):
            if r['field'] == 'name' and r['id'].isdigit():
                rid = int(r['id'])
                if rid < 400:
                    out.setdefault(case_of(rid), r['english'] or r['japanese'])
    return out


def scenes(exe):
    """{case: [(entry, block id, sjis)]} for every voiced line inside a per-wrestler branch."""
    sizes = script._optable(exe)
    first = {}
    for e, i, t, *_ in script.messages(exe):
        first.setdefault(t, f'{e:03d}.{i}')
    out = defaultdict(list)
    for e, ent in enumerate(script.read_entries(exe)):
        if e in script.LISTS or e in script.NOT_SCRIPT:
            continue
        ins = script.parse(ent, sizes)
        at = {}                                  # pc -> [cases starting here]
        for x in ins:
            if x.op == 0x14:
                n = struct.unpack_from('<h', x.raw, 2)[0]
                # 120 labels per variant (206 with the foreign wrestlers); scenes with several
                # lines per wrestler have 2-5 variants picked by an offset, and a few tables
                # carry 1-7 more labels after them
                size = 206 if n >= 206 and n % 206 < 8 else 120
                if n < size:
                    continue
                for k, o in enumerate(struct.unpack_from(f'<{n}I', x.raw, 4)):
                    if k < size * (n // size):
                        at.setdefault(o, []).append(k % size)
        current, voiced = [], False
        for x in ins:
            if x.pc in at:
                current = at[x.pc]
            if x.op == 0x42:
                voiced = True
            elif x.op == 0x37:
                t = script.text_of(x)
                if t and voiced and current:
                    for k in current:
                        out[k].append((e, first.get(t, '?'), t))
                voiced = False
    return out


def main(argv=None):
    argv = paths.configure(sys.argv[1:] if argv is None else argv)
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--out')
    args = ap.parse_args(argv)
    exe = (paths.EXTRACTED / EXE.lstrip('/')).read_bytes()
    names = case_names()
    table = script.english_table()
    by_case = scenes(exe)
    users = defaultdict(set)
    for k, lines in by_case.items():
        for _, _, t in lines:
            users[t].add(k)
    out = Path(args.out) if args.out else paths.ROOT / 'private' / 'voices'
    out.mkdir(parents=True, exist_ok=True)
    index = []
    for k in sorted(by_case):
        name = names.get(k, f'case {k}')
        rows = [f'# {name} (voice case {k})', '']
        seen = set()
        for e, bid, t in by_case[k]:
            if (e, t) in seen:
                continue
            seen.add((e, t))
            en = ' / '.join(table.get(t, ['(no English)']))
            jp = script.decode(t).replace('\r', ' ')
            shared = len(users[t])
            rows.append(f'- {bid} (entry {e:03d}){" - shared by " + str(shared) if shared > 1 else ""}')
            rows.append(f'  JP: {jp}')
            rows.append(f'  EN: {en}')
        safe = ''.join(c if c.isalnum() else '_' for c in name)
        f = out / f'{k:03d}_{safe}.md'
        f.write_text('\n'.join(rows) + '\n', encoding='utf-8')
        index.append(f'{k:03d}\t{name}\t{len(seen)} lines')
    (out / 'INDEX.tsv').write_text('\n'.join(index) + '\n', encoding='utf-8')
    print(f'voices: {len(by_case)} wrestlers -> {out}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
