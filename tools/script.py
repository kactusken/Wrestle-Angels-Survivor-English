#!/usr/bin/env python3
"""Event scripts: the LZ archive in the executable (330 entries), to block files and back.

  script.py extract [--force]     write translation/script/NNN.txt (keeps English by block id)
  script.py roundtrip             rebuild every entry with its own text: identical?
  script.py check                 English that can't be encoded or doesn't fit the window
  script.py wrap [NNN...]         re-break EN lines that are too wide (all files by default)
  script.py dump NNN              the entry's instructions, one per line (research)

The archive (tools/lz.py) is at file 0x3a82c0 of SLPM_662.39 (RAM 0x4a8240), referenced by
lui/addiu pairs (ARCHIVE_REFS). Entries are bytecode: little-endian u16 opcodes, operand sizes
from the table at 0x57e680 (8 bytes per opcode: s8 size, ..., u32 handler). Variable ones:
  0x14 header: u16 n, n x u32 label offsets, u16 m, m x s16   (jumps via labels: 0x3e)
  0x37 text: u16 len, then len bytes: Shift-JIS, \\r line breaks, NUL, padded to even
  0x3e 6 bytes; 0x3f var, n, n x u32 offsets (branch); 0x40 u32 offset (goto); 0x51 4 bytes
Offsets are from the start of the entry; the build moves them when text changes length.
Text codes: FF 01 + u16 n inserts wrestler n's name (whole-line codes, kept as they are).
Entry 321 is not a script but a list of messages (u16 length, text, NUL, padded to even): the
play-by-play lines for moves, {name:2} being the move's name. It is translated like the rest.

Speakers (opcode 0x35 before the line): 2 President, 1 secretary, 0 wrestlers and others;
a line after opcode 0x42 (voice clip) is a wrestler's.

Each distinct Japanese message gets one block, at its first use; every other use takes the
same English. Block id: entry.index (index of the text instruction in the entry).
"""
import argparse
import re
import struct
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import blocks  # noqa: E402
import lz  # noqa: E402
import paths  # noqa: E402

EXE = '/SLPM_662.39'
FILE_OFF, BASE = 0x80, 0x100000
ARCHIVE = 0x3a82c0                       # file offset
ARCHIVE_RAM = ARCHIVE - FILE_OFF + BASE
ARCHIVE_END = 0x47e6fa                   # end of the last entry's packed data (file offset); the
# VM's opcode table follows at 0x47e700 (RAM 0x57e680). test10 used 0x47e842 and zeroed it.
OPTABLE = 0x57e680
NOT_SCRIPT = {321}
LISTS = {321}                            # not bytecode: u16 length + message, ... (match commentary)
SPEAKER = {2: 'President', 1: 'Secretary', 0: 'other'}

LINES = 3                                # lines in the message window
WIDTH = 396                              # pixels per line: 36 half-width cells of 11 px (the
                                         # longest Japanese lines are 38 cells; the window wraps at 47)

# English characters: ASCII is drawn from the font's half-width set (0x5c is ¥, 0x7e an overline,
# so they are mapped); these are written as Shift-JIS.
SJIS_MAP = {'~': '～', '♪': '♪', '♥': '♥', '…': '…', '★': '★', '☆': '☆', '×': '×', '・': '・',
            '「': '「', '」': '」', '『': '『', '』': '』', '（': '（', '）': '）'}


def ram(off):
    return off - FILE_OFF + BASE


def _optable(exe):
    sizes = {}
    off = OPTABLE - BASE + FILE_OFF
    for op in range(0x54):
        size, _, _, _, handler = struct.unpack_from('<bBBBI', exe, off + 8 * op)
        if handler:
            sizes[op] = size
    return sizes


class Ins:
    __slots__ = ('pc', 'op', 'raw')

    def __init__(self, pc, op, raw):
        self.pc, self.op, self.raw = pc, op, raw


def parse(entry, sizes):
    """The entry's instructions; raises ValueError if it isn't a script."""
    out, pc = [], 0
    while pc < len(entry):
        op = struct.unpack_from('<H', entry, pc)[0]
        if op not in sizes:
            raise ValueError(f'unknown opcode {op:#x} at {pc:#x}')
        if op == 0x14:
            n = struct.unpack_from('<h', entry, pc + 2)[0]
            q = pc + 4 + 4 * n
            m = struct.unpack_from('<h', entry, q)[0]
            ln = q + 2 + 2 * m - pc
        elif op == 0x37:
            ln = 4 + struct.unpack_from('<H', entry, pc + 2)[0]
        elif op == 0x3f:
            ln = 6 + 4 * struct.unpack_from('<h', entry, pc + 4)[0]
        elif op in (0x3e, 0x40):
            ln = 6
        elif op == 0x51:
            ln = 4
        else:
            ln = sizes[op] + 2
        out.append(Ins(pc, op, entry[pc:pc + ln]))
        pc += ln
    if pc != len(entry):
        raise ValueError('the last instruction runs past the end')
    return out


def text_of(ins):
    """The message bytes up to the terminating NUL (FF 01 + u16 is a name code)."""
    raw, i = ins.raw[4:], 0
    while i < len(raw) and raw[i]:
        if raw[i] == 0xff:
            i += 4
        elif 0x81 <= raw[i] < 0xa0 or 0xe0 <= raw[i] < 0xff:
            i += 2
        else:
            i += 1
    return raw[:i]


def decode(t):
    """Message bytes as text: line breaks as \\r, name codes as {name:N}."""
    out, i = [], 0
    while i < len(t):
        if t[i] == 0xff:
            out.append('{name:%d}' % struct.unpack_from('<H', t, i + 2)[0])
            i += 4
        elif 0x81 <= t[i] < 0xa0 or 0xe0 <= t[i] < 0xff:
            out.append(t[i:i + 2].decode('cp932', 'replace'))
            i += 2
        else:
            out.append(chr(t[i]) if t[i] != 0x0d else '\r')
            i += 1
    return ''.join(out)


def offsets(ins):
    """(position in raw, value) of each u32 entry offset in an instruction."""
    if ins.op == 0x14:
        n = struct.unpack_from('<h', ins.raw, 2)[0]
        return [(4 + 4 * i, struct.unpack_from('<I', ins.raw, 4 + 4 * i)[0]) for i in range(n)]
    if ins.op == 0x3f:
        n = struct.unpack_from('<h', ins.raw, 4)[0]
        return [(6 + 4 * i, struct.unpack_from('<I', ins.raw, 6 + 4 * i)[0]) for i in range(n)]
    if ins.op == 0x40:
        return [(2, struct.unpack_from('<I', ins.raw, 2)[0])]
    return []


def text_ins(raw):
    """A text instruction for the encoded message (NUL added, padded to even)."""
    body = raw + b'\0'
    if len(body) % 2:
        body += b'\0'
    if len(body) > 0xffff:
        raise ValueError('message too long')
    return struct.pack('<HH', 0x37, len(body)) + body


def rebuild(ins_list, new_text):
    """The entry with new_text {instruction index: encoded message} and every offset moved."""
    moved, pos, parts = {}, 0, []
    for i, ins in enumerate(ins_list):
        moved[ins.pc] = pos
        raw = text_ins(new_text[i]) if i in new_text else ins.raw
        parts.append(raw)
        pos += len(raw)
    moved[ins_list[-1].pc + len(ins_list[-1].raw)] = pos
    out = []
    for ins, raw in zip(ins_list, parts):
        offs = offsets(ins)
        if offs:
            raw = bytearray(raw)
            for p, v in offs:
                if v not in moved:
                    raise ValueError(f'offset {v:#x} is not an instruction start')
                struct.pack_into('<I', raw, p, moved[v])
            raw = bytes(raw)
        out.append(raw)
    return b''.join(out)


def parse_list(entry):
    """[(offset, message bytes)] of a list entry."""
    out, pos = [], 0
    while pos < len(entry):
        n = struct.unpack_from('<H', entry, pos)[0]
        if n == 0 or pos + 2 + n > len(entry):
            raise ValueError(f'bad list item at {pos:#x}')
        out.append((pos, entry[pos + 2:pos + 2 + n].split(b'\0')[0] if b'\xff' not in entry[pos + 2:pos + 2 + n]
                    else _until_nul(entry[pos + 2:pos + 2 + n])))
        pos += 2 + n
    return out


def _until_nul(raw):
    i = 0
    while i < len(raw) and raw[i]:
        i += 4 if raw[i] == 0xff else 2 if (0x81 <= raw[i] < 0xa0 or 0xe0 <= raw[i] < 0xff) else 1
    return raw[:i]


def build_list(items):
    out = bytearray()
    for t in items:
        body = t + b'\0'
        body += bytes(len(body) % 2)
        out += struct.pack('<H', len(body)) + body
    return bytes(out)


def read_entries(exe):
    return lz.read_archive(exe, ARCHIVE)


def messages(exe):
    """[(entry, index, sjis bytes, speaker, voiced, case)] for every non-empty text instruction."""
    sizes = _optable(exe)
    out = []
    for e, entry in enumerate(read_entries(exe)):
        if e in LISTS:
            for i, (_, t) in enumerate(parse_list(entry)):
                out.append((e, i, t, None, False, None))
            continue
        if e in NOT_SCRIPT:
            continue
        ins_list = parse(entry, sizes)
        cases = {}
        for ins in ins_list:
            if ins.op == 0x3f:
                for k, (_, v) in enumerate(offsets(ins)):
                    cases.setdefault(v, k)
        mode, voiced, case = None, False, None
        for i, ins in enumerate(ins_list):
            if ins.pc in cases:
                case = cases[ins.pc]
            if ins.op == 0x35:
                mode = struct.unpack_from('<H', ins.raw, 2)[0]
            elif ins.op == 0x42:
                voiced = True
            elif ins.op == 0x37:
                t = text_of(ins)
                if t and not (t[0] == 0xff and len(t) == 4):
                    out.append((e, i, t, mode, voiced, case))
                voiced = False
    return out


# --- English -----------------------------------------------------------------------------------

def encode(text):
    out = bytearray()
    for part in re.split(r'(\{name:\d+\})', text):
        if part.startswith('{name:'):
            out += b'\xff\x01' + struct.pack('<H', int(part[6:-1]))
        else:
            out += _encode(part)
    return bytes(out)


def _encode(text):
    out = bytearray()
    for ch in text:
        if ch == '\\':
            raise ValueError('\\ is not allowed (the font draws ¥)')
        if ch in SJIS_MAP:
            out += SJIS_MAP[ch].encode('cp932')
        elif ' ' <= ch < '\x7f':
            out.append(ord(ch))
        else:
            try:
                out += ch.encode('cp932')
            except UnicodeEncodeError:
                raise ValueError(f'{ch!r} can not be shown') from None
    return bytes(out)


def advance_table():
    """Pixel advance of each ASCII character: the message window draws the font's half-width set in
    11 px cells (tools/font.py's table once the font is made proportional)."""
    try:
        import font
        return font.ADVANCE
    except (ImportError, AttributeError):
        return {chr(c): 11 for c in range(0x20, 0x7f)}


def width(text, adv=None):
    adv = adv or advance_table()
    w = 0
    for ch in text:
        w += adv.get(ch, 22) if ch < '\x7f' else 22
    return w


def wrap_lines(lines, limit=WIDTH, adv=None):
    """Re-break lines that are too wide at spaces; keeps the author's own breaks."""
    adv = adv or advance_table()
    out = []
    for line in lines:
        words, cur = line.split(' '), ''
        for w in words:
            cand = w if not cur else cur + ' ' + w
            if width(cand, adv) <= limit or not cur:
                cur = cand
            else:
                out.append(cur)
                cur = w
        out.append(cur)
    return out


def english_message(lines):
    return b'\r'.join(encode(l) for l in lines)


# --- files ---------------------------------------------------------------------------------------

HEADER = """# Event script entry {e:03d} of the archive in SLPM_662.39 (Wrestle Angels Survivor).
# One block per message; JP lines are the original's screen lines. Write the English as EN lines.
# The window shows {lines} lines; `python3 tools/script.py wrap` re-breaks lines wider than
# {width} pixels, so write naturally and add a line break only where you want one.
# Comments: the speaker (President = the player, Secretary, or the line's speaker if voiced) and,
# inside a branch, `case N` (the branch taken - often one per wrestler personality).
# A message used again later (here or in another entry) takes the same English.
# Allowed: plain ASCII except \\ ; ~ is drawn as ～; ♪ ♥ … are fine.
# {{name:N}} is a wrestler's name (filled in by the game): keep it, move it where English needs it.
"""


def extract(force=False):
    exe = (paths.EXTRACTED / EXE.lstrip('/')).read_bytes()
    first, uses = {}, defaultdict(int)
    for m in messages(exe):
        uses[m[2]] += 1
        first.setdefault(m[2], m)
    by_entry = defaultdict(list)
    for m in first.values():
        by_entry[m[0]].append(m)
    paths.SCRIPT.mkdir(parents=True, exist_ok=True)
    old = {}
    for p in paths.SCRIPT.glob('*.txt'):
        for b in blocks.BlockFile(p).blocks:
            if b.english:
                old[b.id] = b.english
    written = 0
    for e, ms in sorted(by_entry.items()):
        p = paths.SCRIPT / f'{e:03d}.txt'
        if p.exists() and not force and not old:
            raise SystemExit(f'{p} exists; use --force to rewrite (English is kept by id)')
        out = [HEADER.format(e=e, lines=LINES, width=WIDTH)]
        for e_, i, t, mode, voiced, case in sorted(ms, key=lambda m: m[1]):
            bid = f'{e_:03d}.{i}'
            out.append(f'@ {bid}')
            who = 'wrestler (voiced)' if voiced else SPEAKER.get(mode, 'other')
            note = [who]
            if case is not None:
                note.append(f'case {case}')
            if uses[t] > 1:
                note.append(f'used {uses[t]}x')
            out.append('# ' + ', '.join(note))
            for line in decode(t).split('\r'):
                out.append(f'JP {line}')
            for line in old.get(bid, []):
                out.append(f'EN {line}')
            out.append('')
        p.write_text('\n'.join(out), encoding='utf-8')
        written += 1
    print(f'{len(first)} distinct messages in {written} files under {paths.SCRIPT}')


def english_table():
    """{sjis message: [EN lines]} from the block files."""
    exe = (paths.EXTRACTED / EXE.lstrip('/')).read_bytes()
    jp = {f'{e:03d}.{i}': t for e, i, t, *_ in messages(exe)}
    table = {}
    for p in sorted(paths.SCRIPT.glob('*.txt')):
        for b in blocks.BlockFile(p).blocks:
            if b.english and b.id in jp:
                table[jp[b.id]] = b.english
    return table


def build_entries(exe, table):
    sizes = _optable(exe)
    out = []
    for e, entry in enumerate(read_entries(exe)):
        if e in LISTS:
            items = [t for _, t in parse_list(entry)]
            new = [english_message(table[t]) if t in table else t for t in items]
            out.append(build_list(new) if new != items else entry)
            continue
        if e in NOT_SCRIPT:
            out.append(entry)
            continue
        ins_list = parse(entry, sizes)
        new = {}
        for i, ins in enumerate(ins_list):
            if ins.op == 0x37:
                t = text_of(ins)
                if t in table:
                    new[i] = english_message(table[t])
        out.append(rebuild(ins_list, new) if new else entry)
    return out


def check():
    table = english_table()
    adv = advance_table()
    bad = 0
    for p in sorted(paths.SCRIPT.glob('*.txt')):
        for b in blocks.BlockFile(p).blocks:
            en = b.english
            if not en:
                continue
            try:
                english_message(en)
            except ValueError as err:
                print(f'{p.name} @{b.id}: {err}')
                bad += 1
                continue
            if len(en) > LINES:
                print(f'{p.name} @{b.id}: {len(en)} lines (window: {LINES})')
                bad += 1
            for line in en:
                if width(line, adv) > WIDTH:
                    print(f'{p.name} @{b.id}: {width(line, adv)} px: {line}')
                    bad += 1
    print(f'{len(table)} messages translated; {bad} problem(s)')
    return 1 if bad else 0


def wrap(names=None):
    adv = advance_table()
    files = [paths.SCRIPT / f'{n}.txt' for n in names] if names else sorted(paths.SCRIPT.glob('*.txt'))
    changed = 0
    for p in files:
        bf = blocks.BlockFile(p)
        dirty = False
        for b in bf.blocks:
            if b.english and any(width(l, adv) > WIDTH for l in b.english):
                b.english = wrap_lines(b.english, WIDTH, adv)
                dirty = True
                changed += 1
        if dirty:
            bf.save()
    print(f'{changed} block(s) re-broken')


def roundtrip():
    exe = (paths.EXTRACTED / EXE.lstrip('/')).read_bytes()
    sizes = _optable(exe)
    entries = read_entries(exe)
    n = 0
    for e, entry in enumerate(entries):
        if e in NOT_SCRIPT:
            continue
        ins_list = parse(entry, sizes)
        same = {i: text_of(ins) for i, ins in enumerate(ins_list) if ins.op == 0x37}
        # rebuilding with the same text, but re-encoded (NUL + even padding): same bytes?
        if rebuild(ins_list, same) != entry:
            print(f'entry {e}: differs')
            n += 1
        # and with every message one byte longer: offsets must still land on instructions
        longer = {i: t + b'X' for i, t in same.items()}
        new = rebuild(ins_list, longer)
        parse(new, sizes)
    print(f'{len(entries) - len(NOT_SCRIPT)} entries rebuilt: {n} differ')
    return 1 if n else 0


def step(path, files):
    """Build step: the English in translation/script/ into the archive in the executable."""
    import exefile
    exe = files.get(EXE)
    table = english_table()
    if not table:
        return
    packed = [lz.pack_best(e) for e in build_entries(exe, table)]
    exe, spill = place_archive(exe, packed)
    print(f"script: {len(table)} messages, archive {4 * len(packed) + sum(map(len, packed)):#x} "
          f"bytes (room {ARCHIVE_END - ARCHIVE:#x}), {spill:#x} of them in the extra segment")
    files.put(EXE, exe)


def place_archive(exe, packed):
    """The archive stays where it was; the entries that no longer fit go to the extra segment,
    reached through the archive's own offsets (the readers 0x13d950 / 0x13d9d0 add the offset to
    the archive's address, nothing else - the 7 references all go through them). Moving the whole
    archive (test1-test9) took 0xe0000 bytes from the game's memory pool, and tag matches stopped
    drawing pictures. Returns (exe, bytes in the extra segment)."""
    import exefile
    if lz.archive_entries(exe, ARCHIVE)[-1][1] != ARCHIVE_END:
        raise SystemExit('script: the archive does not end at ARCHIVE_END')
    room = ARCHIVE_END - ARCHIVE
    pos, k = 4 * len(packed), 0
    while k < len(packed) and pos + len(packed[k]) <= room:
        pos += len(packed[k])
        k += 1
    spill = b''.join(packed[k:])
    base = ARCHIVE_RAM
    if spill:
        exe, base = exefile.alloc(exe, spill)
    offs, at, out = [], 4 * len(packed), bytearray()
    for i, pk in enumerate(packed):
        if i == k:
            at = base - ARCHIVE_RAM
        offs.append(at)
        at += len(pk)
        if i < k:
            out += pk
    head = struct.pack(f'<{len(offs)}I', *offs) + out
    exe = bytearray(exe)
    exe[ARCHIVE:ARCHIVE_END] = head + bytes(room - len(head))
    return exe, len(spill)


def dump(e):
    exe = (paths.EXTRACTED / EXE.lstrip('/')).read_bytes()
    entry = read_entries(exe)[e]
    for ins in parse(entry, _optable(exe)):
        if ins.op == 0x37:
            print(f'{ins.pc:05x} TEXT {text_of(ins).decode("cp932", "replace")!r}')
        else:
            print(f'{ins.pc:05x} {ins.op:02x} {ins.raw[2:].hex(" ")}')


def main(argv=None):
    argv = paths.configure(sys.argv[1:] if argv is None else argv)
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    sub = ap.add_subparsers(dest='cmd', required=True)
    x = sub.add_parser('extract')
    x.add_argument('--force', action='store_true')
    sub.add_parser('roundtrip')
    sub.add_parser('check')
    w = sub.add_parser('wrap')
    w.add_argument('names', nargs='*')
    d = sub.add_parser('dump')
    d.add_argument('entry', type=int)
    args = ap.parse_args(argv)
    if args.cmd == 'extract':
        extract(args.force)
    elif args.cmd == 'roundtrip':
        return roundtrip()
    elif args.cmd == 'check':
        return check()
    elif args.cmd == 'wrap':
        wrap(args.names)
    elif args.cmd == 'dump':
        dump(args.entry)
    return 0


if __name__ == '__main__':
    sys.exit(main())
