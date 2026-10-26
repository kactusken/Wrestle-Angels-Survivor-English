#!/usr/bin/env python3
"""Unlocks that change data rather than code (build.py --unlocks; code ones are CODE_PATCHES).

  alternates   the 52 domestic 2P alternates (roster ids 101-152) can be found in tryouts and
               scouting from year 1 instead of years 3-11 (docs/HIDDEN_CONTENT.md, Wrestlers).

*From the code*: each roster record holds a debut year after its moveset (post byte 12 = master
+0x115); the tryout pool (0x19a7c4) takes a rookie once the years elapsed reach debut year - 1.
The records are found through their table (tools/roster.py) and the blob's address in the code
(the lui/addiu at 0x1947ec), so this works on the original records and on the English ones the
roster step rebuilt, in place or in the extra segment.
"""
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import exefile  # noqa: E402
import roster  # noqa: E402

EXE = '/SLPM_662.39'
ALTERNATES = range(101, 153)
DEBUT_YEAR = 45 + 60 + 12      # after the name: 3 stat groups of 15, 30 moves x 2 bytes, post byte 12


def _file_offset(exe, addr):
    try:
        return exefile.off(addr)
    except ValueError:
        _, o, _ = exefile._extra_phdr(exe)
        return o + addr - exefile.BSS_END


def _blob(exe):
    """File offset of the roster record blob, wherever the roster step put it."""
    w1, w2 = (struct.unpack_from('<I', exe, exefile.off(a))[0] for a in (0x1947ec, 0x1947f0))
    return _file_offset(exe, (((w1 & 0xffff) << 16) + exefile.s16(w2 & 0xffff)) & 0xffffffff)


def alternates(files):
    exe = bytearray(files.get(EXE))
    blob = _blob(exe)
    done = 0
    for o, s in roster.records(exe):
        rid = struct.unpack_from('<H', exe, blob + o)[0]
        if rid not in ALTERNATES:
            continue
        rec = exe[blob + o:blob + o + s]
        at = blob + o + roster.fields(rec)['name'][1] + DEBUT_YEAR
        if not 3 <= exe[at] <= 11:
            raise SystemExit(f'unlocks: roster id {rid} has debut year {exe[at]}, expected 3-11')
        exe[at] = 1
        done += 1
    if done != len(ALTERNATES):
        raise SystemExit(f'unlocks: {done} 2P alternates found, expected {len(ALTERNATES)}')
    files.put(EXE, exe)
    print(f'unlocks: {done} 2P alternates debut in year 1')


DATA_UNLOCKS = {'alternates': alternates}


def apply(files, groups):
    for g in sorted(groups):
        if g in DATA_UNLOCKS:
            DATA_UNLOCKS[g](files)
