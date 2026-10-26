#!/usr/bin/env python3
"""Roster records in the executable: wrestler and coach names, finishers (translation/text/roster.csv).

  roster.py extract [--force]     write the CSV (keeps English by key)
  roster.py check                 English that can't be stored

*From the code* (0x1947a0): a table at 0x47d930 of (u32 offset, u32 size) pairs, one per record,
offsets from the record blob at 0x499350 (reached by one lui/addiu pair, 0x1947ec). A record:
u16 id, then the name as u16 length + Shift-JIS + NUL (padded to even), numbers, and - for
wrestlers - the finisher's name in the same form as the record's last field. 279 records:
206 wrestlers (ids 1-343), coaches and staff (401-), and "棄権" placeholders (701-).
The game copies the name into the wrestler only if its length / 2 < 11, so names stay
under 22 bytes.

Build: every record is rebuilt with its English, the table rewritten in place, and the blob
written back - in place if it fits, else to the extra segment (tools/exefile.py).
"""
import argparse
import csv
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import exefile  # noqa: E402
import paths  # noqa: E402

EXE = '/SLPM_662.39'
TABLE = 0x47d930
BLOB = 0x499350
NAME_MAX = 21
# Data pointers straight at a record's text, moved with it. None: the two once listed here
# (0x520c10, 0x52ebd4 -> record 181's name) are the starts of script entries 195 and 232 in the
# packed archive (size 0x000f1a, then a literal run), not pointers - patching them broke those
# entries once the archive stayed in place (test10).
POINTERS = {}
FIELDS = ['key', 'id', 'field', 'japanese', 'english']
REPLACE = {'~': '～', '’': "'", '“': '"', '”': '"'}


def u16(d, o):
    return struct.unpack_from('<H', d, o)[0]


def records(exe):
    """[(offset in blob, size)] from the table."""
    out, pos, i = [], 0, 0
    while True:
        o, s = struct.unpack_from('<II', exe, exefile.off(TABLE) + 8 * i)
        if o != pos or not 0 < s < 0x400:
            return out
        out.append((o, s))
        pos, i = o + s, i + 1


def fields(rec):
    """{'name': (start, end), 'finisher': (start, end)} - byte ranges of the length + text fields."""
    out = {'name': (2, 4 + u16(rec, 2))}
    for back in range(4, 64, 2):
        p = len(rec) - back
        if p > out['name'][1] and u16(rec, p) == back - 2:
            t = rec[p + 2:].split(b'\0')[0]
            try:
                if t and t.decode('cp932').strip():
                    out['finisher'] = (p, len(rec))
            except UnicodeDecodeError:
                pass
            break
    return out


def text(rec, span):
    return rec[span[0] + 2:span[1]].split(b'\0')[0].decode('cp932')


def field_bytes(enc):
    body = enc + b'\0'
    body += bytes(len(body) % 2)
    return struct.pack('<H', len(body)) + body


def encode(t):
    for a, b in REPLACE.items():
        t = t.replace(a, b)
    if '\\' in t:
        raise ValueError('backslash is drawn as ¥')
    return t.encode('cp932')


def csv_path():
    return paths.TEXT / 'roster.csv'


def read_rows():
    with open(csv_path(), encoding='utf-8', newline='') as f:
        return list(csv.DictReader(f))


def extract(force=False):
    exe = (paths.EXTRACTED / EXE.lstrip('/')).read_bytes()
    old = {}
    if csv_path().exists():
        if not force:
            sys.exit(f'{paths.show(csv_path())} exists (--force rewrites it, keeping the English)')
        old = {r['key']: r['english'] for r in read_rows()}
    rows = []
    blob = exefile.off(BLOB)
    for k, (o, s) in enumerate(records(exe)):
        rec = exe[blob + o:blob + o + s]
        for name, span in fields(rec).items():
            key = f'{k}.{name}'
            rows.append({'key': key, 'id': u16(rec, 0), 'field': name, 'japanese': text(rec, span),
                         'english': old.get(key, '')})
    with open(csv_path(), 'w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, FIELDS, lineterminator='\n')
        w.writeheader()
        w.writerows(rows)
    print(f'extract: {len(rows)} names to {paths.show(csv_path())}')


def plan():
    rows = read_rows()
    out, errors = {}, []
    for r in rows:
        if not r['english'].strip():
            continue
        try:
            enc = encode(r['english'])
        except (ValueError, UnicodeEncodeError) as x:
            errors.append(f"{r['key']}: {x}")
            continue
        if r['field'] == 'name' and len(enc) > NAME_MAX:
            errors.append(f"{r['key']}: {r['english']!r} is {len(enc)} bytes (at most {NAME_MAX})")
        out[r['key']] = (r['japanese'], enc)
    return out, errors


def check():
    _, errors = plan()
    for e in errors:
        print(e)
    print(f'{len(errors)} problem(s)')
    return 1 if errors else 0


def step(path, files):
    """Build step: names and finishers into the records."""
    if not csv_path().exists():
        return
    english, errors = plan()
    if errors:
        raise SystemExit('roster: ' + '\n  '.join(errors))
    if not english:
        return
    exe = files.get(EXE)
    blob_off = exefile.off(BLOB)
    recs = records(exe)
    new, table, pos = bytearray(), bytearray(), 0
    text_at = {}                         # (record, field) -> offset of its text in the new blob
    for at, (k, field) in POINTERS.items():
        o, _ = recs[k]
        want = BLOB + o + fields(bytes(exe[blob_off + o:blob_off + o + recs[k][1]]))[field][0] + 2
        if struct.unpack_from('<I', exe, exefile.off(at))[0] != want:
            raise SystemExit(f'roster: the pointer at {at:#x} does not point at record {k} {field}')
    for k, (o, s) in enumerate(recs):
        rec = bytes(exe[blob_off + o:blob_off + o + s])
        spans = fields(rec)
        parts, last = [], 0
        for name, span in sorted(spans.items(), key=lambda x: x[1]):
            key = f'{k}.{name}'
            parts.append(rec[last:span[0]])
            if key in english:
                jp, enc = english[key]
                if text(rec, span) != jp:
                    raise SystemExit(f'roster: {key}: the executable has different text - re-extract')
                parts.append(field_bytes(enc))
            else:
                parts.append(rec[span[0]:span[1]])
            last = span[1]
        parts.append(rec[last:])
        r = b''.join(parts)
        acc, last = 0, 0
        for name, span in sorted(spans.items(), key=lambda x: x[1]):
            acc += span[0] - last
            text_at[(k, name)] = pos + acc + 2
            key = f'{k}.{name}'
            acc += len(field_bytes(english[key][1])) if key in english else span[1] - span[0]
            last = span[1]
        table += struct.pack('<II', pos, len(r))
        new += r
        pos += len(r)
    end = recs[-1][0] + recs[-1][1]
    exe[exefile.off(TABLE):exefile.off(TABLE) + len(table)] = table
    exe = exefile.place(exe, 'roster records', blob_off, blob_off + end, bytes(new), BLOB, 1)
    w1, w2 = (struct.unpack_from('<I', exe, exefile.off(a))[0] for a in (0x1947ec, 0x1947f0))
    base = (((w1 & 0xffff) << 16) + exefile.s16(w2 & 0xffff)) & 0xffffffff
    for at, key in POINTERS.items():
        struct.pack_into('<I', exe, exefile.off(at), base + text_at[key])
    files.put(EXE, exe)
    print(f'roster: {len(english)} names ({len(new):#x} bytes, room {end:#x})')


def main(argv=None):
    argv = paths.configure(sys.argv[1:] if argv is None else argv)
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    sub = ap.add_subparsers(dest='cmd', required=True)
    x = sub.add_parser('extract')
    x.add_argument('--force', action='store_true')
    sub.add_parser('check')
    args = ap.parse_args(argv)
    if args.cmd == 'extract':
        extract(args.force)
        return 0
    return check()


if __name__ == '__main__':
    sys.exit(main())
