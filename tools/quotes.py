#!/usr/bin/env python3
"""Pre-match quotes (/A040/A048.): to translation/script/quotes.txt and back.

  quotes.py extract       write the block file (keeps English by id)

The file is one enciphered LZ piece (tools/datafile.py) holding a list like script entry 321:
u16 length + Shift-JIS message + NUL, padded to even; 334 messages. The code loads it with its
size written in as a constant (*from the code*: addiu a1/a2, zero, 0x14fc at 0x222b50 and
0x222e1c); the build writes the new size there.
Line breaks, width and characters as in the event scripts (tools/script.py).
"""
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import blocks  # noqa: E402
import datafile  # noqa: E402
import exefile  # noqa: E402
import paths  # noqa: E402
import script  # noqa: E402

FILE = '/A040/A048.'
EXE = '/SLPM_662.39'
SIZE_AT = [0x222b50, 0x222e1c]           # addiu rX, zero, size
NAME = 'quotes.txt'

HEADER = """# Pre-match quotes (/A040/A048.): what a wrestler says before a match.
# One block per quote; write EN lines (at most 3 lines; `python3 tools/script.py wrap` re-breaks
# lines wider than 396 pixels - about 36 characters). Characters as in the event scripts.
"""


def items(data):
    return [t for _, t in script.parse_list(datafile.single(data))]


def extract():
    data = (paths.EXTRACTED / FILE.lstrip('/')).read_bytes()
    p = paths.SCRIPT / NAME
    old = {}
    if p.exists():
        old = {b.id: b.english for b in blocks.BlockFile(p).blocks if b.english}
    out = [HEADER]
    for i, t in enumerate(items(data)):
        bid = f'q.{i}'
        out.append(f'@ {bid}')
        for line in script.decode(t).split('\r'):
            out.append(f'JP {line}')
        for line in old.get(bid, []):
            out.append(f'EN {line}')
        out.append('')
    p.write_text('\n'.join(out), encoding='utf-8')
    print(f'{len(items(data))} quotes to {paths.show(p)}')


def step(path, files):
    p = paths.SCRIPT / NAME
    if not p.exists():
        return
    english = {b.id: b.english for b in blocks.BlockFile(p).blocks if b.english}
    if not english:
        return
    data = files.get(FILE)
    old = items(bytes(data))
    new = [script.english_message(english[f'q.{i}']) if f'q.{i}' in english else t
           for i, t in enumerate(old)]
    out = datafile.build_single(script.build_list(new))
    if len(out) > 0x7fff:
        raise SystemExit(f'quotes: {len(out):#x} bytes - the size must fit an addiu (0x7fff)')
    exe = files.get(EXE)
    for at in SIZE_AT:
        o = exefile.off(at)
        w = struct.unpack_from('<I', exe, o)[0]
        if w >> 26 != 9 or (w >> 21) & 31 != 0 or w & 0xffff != len(bytes(files.get(FILE))) and \
                w & 0xffff != 0x14fc:
            raise SystemExit(f'quotes: unexpected instruction at {at:#x}')
        struct.pack_into('<I', exe, o, (w & 0xffff0000) | len(out))
    files.put(EXE, exe)
    files.put(FILE, out)
    print(f'quotes: {len(english)} of {len(old)} translated ({len(out):#x} bytes)')


def main(argv=None):
    argv = paths.configure(sys.argv[1:] if argv is None else argv)
    if argv == ['extract']:
        extract()
        return 0
    print(__doc__)
    return 2


if __name__ == '__main__':
    sys.exit(main())
