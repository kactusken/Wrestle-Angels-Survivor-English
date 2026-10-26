#!/usr/bin/env python3
"""Venue names (translation/text/venues.csv): the show-scheduling and venue lists (a build step).

  venues.py check     English that can't be stored

*From the code* (0x19b68c, 0x19b6b0): a one-entry LZ archive at 0x4a2da0 (file 0x3a2e20), read
with 0x13d950 / 0x13d9d0 like the script archive. The entry: u16 count (384), u16 0, then per
venue u16 length + Shift-JIS name + NUL (padded to even) and 7 bytes (u16 capacity, u16 0,
prefecture, rank, indoor/outdoor). The game copies each into a 40-byte record in RAM (0x8dac a0:
name in 36 bytes) and pads names to 26 bytes for its list columns (0x1aa1e8, 0x21e950), so the
English is kept to 26 characters. Most English is WAS2's (the same venues), shortened to fit.

Build: the entry is packed again; it stays in the archive's slot if it fits, else it goes to the
extra segment and the archive's offset points there (the reader adds it to the archive's
address).
"""
import csv
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import exefile  # noqa: E402
import lz  # noqa: E402
import paths  # noqa: E402

EXE = '/SLPM_662.39'
ARCHIVE = 0x4a2da0
END = 0x4a4790                  # the prefecture names follow
COUNT = 384
NAME_MAX = 26


def records(entry):
    """[(name bytes, 7-byte tail)] from the unpacked entry."""
    count = struct.unpack_from('<H', entry, 0)[0]
    out, pos = [], 4
    for _ in range(count):
        n = struct.unpack_from('<H', entry, pos)[0]
        out.append((entry[pos + 2:pos + 2 + n].split(b'\0')[0], entry[pos + 2 + n:pos + 9 + n]))
        pos += 9 + n
    if pos != len(entry) or count != COUNT:
        raise SystemExit('venues: the entry is not the 384 venue records')
    return out


def read_rows():
    with open(paths.TEXT / 'venues.csv', encoding='utf-8', newline='') as f:
        return list(csv.DictReader(f))


def problems(rows):
    bad = []
    for r in rows:
        t = r['english']
        if len(t) > NAME_MAX:
            bad.append(f"{r['key']}: {t!r} is longer than {NAME_MAX}")
        try:
            t.encode('ascii')
        except UnicodeEncodeError:
            bad.append(f"{r['key']}: {t!r} is not ASCII")
    return bad


def step(path, files):
    exe = bytearray(files.get(EXE))
    o = exefile.off(ARCHIVE)
    if struct.unpack_from('<I', exe, o)[0] != 4:
        raise SystemExit('venues: no one-entry archive at 0x4a2da0')
    entry, end = lz.unpack(exe, o + 4)
    if end != exefile.off(END) - 1:
        raise SystemExit('venues: the archive does not end before the prefecture names')
    recs = records(entry)
    rows = read_rows()
    bad = problems(rows)
    if bad:
        raise SystemExit('venues:\n  ' + '\n  '.join(bad))
    out = bytearray(entry[:4])
    done = 0
    for (name, tail), r in zip(recs, rows):
        if name.decode('cp932') != r['japanese']:
            raise SystemExit(f"venues: row {r['key']} is not {name.decode('cp932')}")
        text = r['english'].encode('ascii') if r['english'] else name
        done += bool(r['english'])
        body = text + b'\0'
        body += bytes(len(body) % 2)
        out += struct.pack('<H', len(body)) + body + tail
    packed = lz.pack_best(bytes(out))
    room = END - ARCHIVE - 4
    if len(packed) <= room:
        exe[o + 4:o + 4 + room] = packed + bytes(room - len(packed))
        where = 'in place'
    else:
        exe, at = exefile.alloc(exe, packed)
        exe = bytearray(exe)
        struct.pack_into('<I', exe, o, at - ARCHIVE)
        exe[o + 4:o + 4 + room] = bytes(room)
        where = f'at {at:#x} (extra segment)'
    files.put(EXE, exe)
    print(f'venues: {done} of {len(recs)} translated, {len(packed):#x} bytes {where}')


def main(argv=None):
    argv = paths.configure(sys.argv[1:] if argv is None else argv)
    if argv[:1] == ['check']:
        bad = problems(read_rows())
        print('\n'.join(bad) or 'venues: all fit')
        return 1 if bad else 0
    print(__doc__)
    return 2


if __name__ == '__main__':
    sys.exit(main())
