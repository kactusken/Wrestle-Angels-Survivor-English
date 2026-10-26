#!/usr/bin/env python3
"""The ring announcer's lines before a match (translation/text/announcer.csv; a build step).

  announcer.py check     English that can't be stored

*From the code* (0x222f48): an LZ block at 0x5852d8 (file 0x485358) unpacked by 0x1c6830 into a
buffer of its stated size. 19 records, each u16 length + text + NUL (padded to even): the title
match opener, then the entrances (blue/red corner, singles/tag/six-person, title and non-title).
In the text 0x0d is a line break and ff 01 NN 00 inserts value NN (0 promotion, 1 division,
8 suffix; 2-4 red corner wrestlers, 5-7 blue) - written {NN} in the table, \\n for a break.

Build: the block is packed again and put in the extra segment (it was 0x10d bytes packed), the
one lui/addiu pair repointed.
"""
import csv
import re
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import exefile  # noqa: E402
import lz  # noqa: E402
import paths  # noqa: E402

EXE = '/SLPM_662.39'
BLOCK = 0x5852d8
COUNT = 19
LINE_MAX = 40                   # characters per line of the message window
WIDTH = {0: 5, 1: 11, 8: 2}     # longest value of {N} (promotion, division, suffix); names 18


def decode(body):
    out, i = '', 0
    while i < len(body) and body[i]:
        c = body[i]
        if c == 0x0d:
            out, i = out + '\\n', i + 1
        elif c == 0xff:
            out, i = out + '{%d}' % body[i + 2], i + 4
        elif 0x81 <= c <= 0x9f or 0xe0 <= c <= 0xef:
            out, i = out + body[i:i + 2].decode('cp932'), i + 2
        else:
            out, i = out + chr(c), i + 1
    return out


def encode(text):
    out = bytearray()
    for part in re.split(r'(\\n|\{\d+\})', text):
        if part == '\\n':
            out.append(0x0d)
        elif re.fullmatch(r'\{\d+\}', part):
            out += bytes([0xff, 1, int(part[1:-1]), 0])
        else:
            out += part.encode('ascii')
    out.append(0)
    return bytes(out + bytes(len(out) % 2))


def records(data):
    out, pos = [], 0
    while pos < len(data):
        n = struct.unpack_from('<H', data, pos)[0]
        out.append(data[pos + 2:pos + 2 + n])
        pos += 2 + n
    return out


def read_rows():
    with open(paths.TEXT / 'announcer.csv', encoding='utf-8', newline='') as f:
        return list(csv.DictReader(f))


def problems(rows):
    bad = []
    for r in rows:
        t = r['english']
        try:
            encode(t)
        except (UnicodeEncodeError, ValueError):
            bad.append(f"{r['key']}: not ASCII")
        if sorted(re.findall(r'\{\d+\}', t)) != sorted(re.findall(r'\{\d+\}', r['japanese'])):
            bad.append(f"{r['key']}: the {{N}} values differ from the Japanese")
        for line in t.split('\\n'):
            if len(re.sub(r'\{(\d+)\}', lambda m: 'x' * WIDTH.get(int(m[1]), 18), line)) > LINE_MAX:
                bad.append(f"{r['key']}: a line may run past {LINE_MAX} characters: {line!r}")
    return bad


def step(path, files):
    exe = bytearray(files.get(EXE))
    data, _ = lz.unpack(exe, exefile.off(BLOCK))
    recs = records(data)
    rows = read_rows()
    if len(recs) != COUNT or [decode(b) for b in recs] != [r['japanese'] for r in rows]:
        raise SystemExit('announcer: the block does not match announcer.csv')
    bad = problems(rows)
    if bad:
        raise SystemExit('announce:\n  ' + '\n  '.join(bad))
    out = bytearray()
    for r, old in zip(rows, recs):
        body = encode(r['english']) if r['english'] else old
        out += struct.pack('<H', len(body)) + body
    pairs = exefile.refs(exe, BLOCK)
    if len(pairs) != 1:
        raise SystemExit(f'announcer: {len(pairs)} references to the block, expected 1')
    exe, at = exefile.alloc(exe, lz.pack_best(bytes(out)))
    exe = bytearray(exe)
    exefile.repoint(exe, pairs, at)
    files.put(EXE, exe)
    print(f'announcer: {sum(bool(r["english"]) for r in rows)} of {COUNT} lines, block at {at:#x}')


def main(argv=None):
    argv = paths.configure(sys.argv[1:] if argv is None else argv)
    if argv[:1] == ['check']:
        bad = problems(read_rows())
        print('\n'.join(bad) or 'announcer: all fit')
        return 1 if bad else 0
    print(__doc__)
    return 2


if __name__ == '__main__':
    sys.exit(main())
