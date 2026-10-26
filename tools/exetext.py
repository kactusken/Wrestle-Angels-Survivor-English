#!/usr/bin/env python3
"""The executable's own text (menus, messages, commentary): extract to a table, build it back.

  exetext.py extract [--force]     write translation/text/exe.csv (keeps existing English by id)
  exetext.py check                 English that can't be stored (encoding, references)
  exetext.py stats                 strings by kind of reference, and where English would go
  exetext.py dump [FROM TO]        one line per string: id, room, japanese (\n escaped)
  exetext.py import FILE [--dry-run]
                                   English from `id<TAB>text` lines (\n = line break); checks
                                   each (characters, room for strings that can't move)

Columns: id (address), refs (references that can be repointed; 0 = in place only, max_bytes is
then a hard limit), reach (ptrN pointers, codeN lui/addiu pairs, sharedN pairs whose lui serves
several strings, gpN gp-relative), max_bytes (room in place, without the NUL), japanese,
english, notes.

Strings are Shift-JIS, NUL-terminated, in the data part of the image (0x240000-0x586880). Only strings
the code reaches through something this tool can repoint are listed:
  ptr   a 32-bit word anywhere in the data equal to the string's address (pointer tables)
  code  a lui/addiu (or ori) pair building the address, with the lui used by nothing else
  gp    addiu rX, gp, offset (cannot be repointed: in place only)
Strings reached in other ways (fixed records: rosters, move names, venues) are not listed here;
they need their own tables (tools/records.py).

Build (apply): English that fits in the original's room (its bytes, its NUL and the zero padding
after it) is written in place. Longer English goes to the extra segment after .bss
(tools/exefile.py, which also moves the heap past it); every pointer and lui/addiu pair to the
string is patched. The original string stays where it was, so anything that reaches it some
other way still works.

In the table, a line break is written `\\n`. ASCII is drawn from the font's half-width set: `~`
becomes the full-width ～ and `\\` is not allowed (¥).
"""
import argparse
import csv
import re
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import exefile  # noqa: E402
import paths  # noqa: E402

EXE_FILE = '/SLPM_662.39'
CSV_NAME = 'exe.csv'
BASE, FILE_OFF = 0x100000, 0x80
TEXT = (0x100000, 0x240000)
DATA = (0x240000, 0x586880)
GP = 0x58e670
# Not here: the line-break punctuation list (0x251360), the font (22x22 glyphs), the roster
# records (tools/roster.py) and the script
# archive (tools/script.py).
# Pointers that share a string with another meaning get their own English (in the extra segment):
# the country list (0x47e830) reuses the region list's 中国 (Chugoku) for China.
SPLIT_POINTERS = {0x47e830: ('中国', 'China')}
SKIP = [(0x251360, 0x488000), (0x499350, 0x4a2da0), (0x4a8240, 0x57e7c2)]
# Strings the scan would miss that are text all the same: the new-game data screen's title (in a
# SKIP range); 不参加, the empty tournament/league slots (follows data with no NUL; reached by code
# at 0x1f0cc4, not by a pointer)
INCLUDE = {0x4824d0: 'プレイヤー１', 0x584360: '不参加'}
SJIS = re.compile(rb'(?:[\x81-\x9f\xe0-\xef][\x40-\x7e\x80-\xfc]|[\x20-\x7e\x0a])+\x00')
KANA = re.compile(r'[ぁ-んァ-ヶー一-龯]')
REPLACE = {'’': "'", '‘': "'", '“': '"', '”': '"', '…': '...', '—': '―', '–': '-', '~': '～'}


def plausible(t):
    """Text rather than data that happens to decode: two Japanese characters, or one with nothing
    around it but digits, spaces, colons, format codes and line breaks (list rows like
    "%s　%4d　%2d　%2d名")."""
    n = len(KANA.findall(t))
    if n >= 2:
        return True
    filler = r'(?:[0-9０-９（ 　：:]|%-?\d*(?:\.\d+)?[dsX]|\n)*'
    return n == 1 and re.fullmatch(filler + KANA.pattern + filler, t)


class Exe:
    def __init__(self, data):
        self.data = data
        self.words = struct.unpack_from(f'<{(DATA[1] - BASE) // 4}I', data, FILE_OFF)

    def off(self, addr):
        return addr - BASE + FILE_OFF

    def strings(self):
        """{address: bytes} of NUL-terminated Shift-JIS strings starting right after a NUL."""
        out = {}
        seg = self.data[self.off(DATA[0]):self.off(DATA[1])]
        pointed = None
        for m in SJIS.finditer(seg):
            s = m.group()[:-1]
            a = DATA[0] + m.start()
            if self.data[self.off(a) - 1] != 0:
                # a string can follow other data with no NUL between (0x4964d0 通常の練習です。
                # follows 0x01): take the string from where a pointer in the data points
                if pointed is None:
                    pointed = {w for i, w in enumerate(self.words) if BASE + 4 * i >= DATA[0]}
                for k in range(len(s)):
                    if (a + k in pointed or a + k in INCLUDE) and (a + k) % 4 == 0 and 0x81 <= s[k] <= 0xef:
                        s, a = s[k:], a + k
                        break
                else:
                    continue
            if not re.search(rb'[\x81-\x9f\xe0-\xef]', s):
                continue
            if any(lo <= a < hi for lo, hi in SKIP) and a not in INCLUDE:
                continue
            try:
                t = s.decode('cp932')
            except UnicodeDecodeError:
                continue
            if plausible(t):
                out[a] = s
        return out

    def references(self, targets):
        """{address: [('ptr', at) | ('code', lui_at, lo_at) | ('gp', at) | ('shared', lui_at, lo_at)]}"""
        refs = {a: [] for a in targets}
        for i, w in enumerate(self.words):
            at = BASE + i * 4
            if w in refs and not (TEXT[0] <= at < TEXT[1]):
                refs[w].append(('ptr', at))
        n = (TEXT[1] - BASE) // 4
        words = self.words
        for i in range(n):
            x = words[i]
            if x >> 26 != 0xf:
                continue
            rt, hi = (x >> 16) & 31, (x & 0xffff) << 16
            uses = follow(words, n, i, rt)
            for u in uses:
                y = words[u]
                op, imm = y >> 26, y & 0xffff
                if op not in (9, 0xd) or (y >> 21) & 31 != rt:
                    continue
                v = (hi + (imm - 0x10000 if op == 9 and imm & 0x8000 else imm)) & 0xffffffff
                if v in refs:
                    kind = 'code' if len(uses) == 1 else 'shared'
                    refs[v].append((kind, BASE + i * 4, BASE + u * 4))
        for i in range(n):
            x = words[i]
            if x >> 26 == 9 and (x >> 21) & 31 == 28:
                imm = x & 0xffff
                v = GP + (imm - 0x10000 if imm & 0x8000 else imm)
                if v in refs:
                    refs[v].append(('gp', BASE + i * 4))
        return refs

    def room(self, addr, strings):
        """Bytes available in place: the string, its NUL and the zeros after it."""
        end = self.off(addr) + len(strings[addr]) + 1
        while end < self.off(DATA[1]) and self.data[end] == 0 and (BASE + end - FILE_OFF) not in strings:
            end += 1
        return end - self.off(addr)


def branch_of(x, j):
    """(target index or None, falls through) for a branch or jump at word j, else None. Indexes
    are words from BASE."""
    op, rs, rt = x >> 26, (x >> 21) & 31, (x >> 16) & 31
    off = x & 0xffff
    target = j + 1 + (off - 0x10000 if off & 0x8000 else off)
    if op in (4, 0x14) and rs == rt == 0:                         # b (beq zero, zero)
        return target, False
    if op in (4, 5, 6, 7, 0x14, 0x15, 0x16, 0x17) or (op == 1 and rt in (0, 1, 2, 3, 0x10, 0x11, 0x12, 0x13)):
        return target, True
    if op == 2:                                                   # j
        return ((x & 0x3ffffff) * 4 - BASE) // 4, False
    if op == 0 and x & 0x3f == 8:                                 # jr
        return None, False
    return None


def follow(words, n, i, rt, limit=1024):
    """Indexes of the instructions that read register rt as set by the instruction at i, up to
    its next write or the function's return. Branches are followed both ways: the compiler often
    puts a lui in a delay slot and the addiu after the branch target."""
    uses, seen = [], set()
    todo = [i + 1]
    b = branch_of(words[i - 1], i - 1) if i else None
    if b is not None:                                             # i is a delay slot
        target, falls = b
        todo = ([i + 1] if falls else []) + ([target] if target is not None else [])
    steps = 0
    while todo and steps < limit:
        j = todo.pop()
        while 0 <= j < n and j not in seen and steps < limit:
            seen.add(j)
            steps += 1
            reads, writes = regs_of(words[j])
            if rt in reads:
                uses.append(j)
            if rt in writes or words[j] == 0x03e00008:
                break
            b = branch_of(words[j], j)
            if b is None:
                j += 1
                continue
            target, falls = b
            slot = j + 1                                          # the delay slot runs either way
            if slot < n and slot not in seen:
                seen.add(slot)
                r, w = regs_of(words[slot])
                if rt in r:
                    uses.append(slot)
                if rt in w:
                    break
            if target is not None and 0 <= target < n:
                todo.append(target)
            if not falls:
                break
            j = slot + 1
    return sorted(set(uses))


def regs_of(x):
    """(registers read, registers written) by one R5900 instruction - conservative."""
    op, rs, rt, rd = x >> 26, (x >> 21) & 31, (x >> 16) & 31, (x >> 11) & 31
    if op == 0:
        fn = x & 0x3f
        if fn in (0, 2, 3, 0x38, 0x3a, 0x3b, 0x3c, 0x3e, 0x3f):   # shifts by constant
            return {rt}, {rd}
        if fn in (8, 9):                                          # jr / jalr
            return {rs}, ({rd} if fn == 9 else set())
        if fn in (0x10, 0x12):                                    # mfhi / mflo
            return set(), {rd}
        if fn in (0x18, 0x19, 0x1a, 0x1b, 0x11, 0x13):            # mult/div/mthi/mtlo
            return {rs, rt}, {rd}
        return {rs, rt}, {rd}
    if op == 0xf:
        return set(), {rt}
    if 8 <= op <= 0xe or op in (0x18, 0x19):                      # immediate arithmetic
        return {rs}, {rt}
    if 0x20 <= op <= 0x27 or op in (0x37, 0x1e, 0x1a, 0x1b, 0x31, 0x35):   # loads
        return {rs}, ({rt} if op not in (0x31, 0x35) else set())
    if 0x28 <= op <= 0x2f or op in (0x3f, 0x1f, 0x2c, 0x2d, 0x39, 0x3d):   # stores
        return {rs, rt}, set()
    if op in (4, 5, 0x14, 0x15):                                  # beq/bne(l)
        return {rs, rt}, set()
    if op in (1, 6, 7, 0x16, 0x17):                               # regimm, blez/bgtz(l)
        return {rs}, ({31} if op == 1 and rt in (0x10, 0x11, 0x12, 0x13) else set())
    if op == 3:                                                   # jal
        return set(), {31}
    if op == 0x1c:                                                # MMI: assume it reads and writes
        return {rs, rt}, {rd}
    return {rs, rt}, set()


def refs_text(refs):
    kinds = {}
    for r in refs:
        kinds[r[0]] = kinds.get(r[0], 0) + 1
    return ' '.join(f'{k}{n}' for k, n in sorted(kinds.items()))


def escape(s):
    return s.replace('\n', '\\n')


def unescape(s):
    return s.replace('\\n', '\n')


def encode(text):
    for a, b in REPLACE.items():
        text = text.replace(a, b)
    if '\\' in text.replace('\\n', '').replace('\\k', ''):      # \\k: new page (winner messages)
        raise UnicodeEncodeError('cp932', text, text.index('\\'), text.index('\\') + 1, 'backslash is ¥')
    return unescape(text).encode('cp932')


def record_ranges():
    """Address ranges the fixed-record tables (tools/records.py) own: their text is translated
    there, so it is left out here."""
    import records
    out = []
    for t in getattr(records, 'TABLES', {}).values():
        if t['source'] == ('file', EXE_FILE):
            first = t['first'] + records.ELF
            out.append((first, first + t['stride'] * t['count']))
    return out


def in_records(a, ranges):
    return any(lo <= a < hi for lo, hi in ranges)


def csv_path():
    return paths.TEXT / CSV_NAME


def read_rows():
    with open(csv_path(), encoding='utf-8', newline='') as f:
        return list(csv.DictReader(f))


FIELDS = ['id', 'refs', 'reach', 'max_bytes', 'japanese', 'english', 'notes']


def extract(force=False):
    exe = Exe((paths.EXTRACTED / EXE_FILE.lstrip('/')).read_bytes())
    strings = exe.strings()
    refs = exe.references(strings)
    old = {}
    if csv_path().exists():
        if not force:
            sys.exit(f'{paths.show(csv_path())} exists (--force rewrites it, keeping the English)')
        old = {r['id']: r for r in read_rows()}
    rows = []
    owned = record_ranges()
    for a, s in sorted(strings.items()):
        if not refs[a] or in_records(a, owned):
            continue
        ident = f'{a:#x}'
        prev = old.get(ident, {})
        movable = not any(r[0] in ('gp', 'shared') for r in refs[a])
        rows.append({'id': ident, 'refs': len(refs[a]) if movable else 0, 'reach': refs_text(refs[a]),
                     'max_bytes': exe.room(a, strings) - 1,
                     'japanese': escape(s.decode('cp932')), 'english': prev.get('english', ''),
                     'notes': prev.get('notes', '')})
    with open(csv_path(), 'w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, FIELDS, lineterminator='\n')
        w.writeheader()
        w.writerows(rows)
    print(f'extract: {len(rows)} strings to {paths.show(csv_path())}')


def plan(data):
    """[(address, english bytes, refs, room)] for every row with English, or SystemExit."""
    exe = Exe(data)
    strings = exe.strings()
    owned = record_ranges()
    rows = [r for r in read_rows() if r['english'].strip() and not in_records(int(r['id'], 16), owned)]
    refs = exe.references({int(r['id'], 16) for r in rows})
    out, errors = [], []
    for r in rows:
        a = int(r['id'], 16)
        if a not in strings or strings[a].decode('cp932') != unescape(r['japanese']):
            errors.append(f'{r["id"]}: the executable has different text there - re-extract')
            continue
        try:
            enc = encode(r['english'])
        except UnicodeEncodeError as x:
            errors.append(f'{r["id"]}: character the game cannot show: {x.object[x.start]!r}')
            continue
        out.append((a, enc, refs[a], exe.room(a, strings)))
    if errors:
        raise SystemExit('exetext: ' + '\n  '.join(errors))
    return out


def apply(path, files):
    """Build step: the executable's English (tools/exetext.py)."""
    if not csv_path().exists():
        return
    data = files.get(EXE_FILE)
    original = bytes(data)
    items = plan(original)
    extra = bytearray()
    fixups = []
    moved = kept = 0
    for a, enc, refs, room in items:
        off = a - BASE + FILE_OFF
        if len(enc) + 1 <= room:
            data[off:off + room] = enc + bytes(room - len(enc))
            kept += 1
            continue
        if any(r[0] in ('gp', 'shared') for r in refs):
            raise SystemExit(f'exetext: {a:#x} needs {len(enc) + 1} bytes, has {room}, and a reference that '
                             f'cannot be repointed ({refs_text(refs)}) - shorten it')
        rel = len(extra)
        extra += enc + b'\0'
        extra += bytes(-len(extra) % 4)
        for r in refs:
            fixups.append((r[1], 'ptr', rel) if r[0] == 'ptr' else ((r[1], r[2]), 'code', rel))
        moved += 1
    for at, (old, text) in SPLIT_POINTERS.items():
        if struct.unpack_from('<I', original, at - BASE + FILE_OFF)[0] not in \
                [a for a, s_ in Exe(original).strings().items() if s_ == old.encode('cp932')]:
            raise SystemExit(f'exetext: the pointer at {at:#x} does not point at {old}')
        fixups.append((at, 'ptr', len(extra)))
        extra += encode(text) + b'\0'
        extra += bytes(-len(extra) % 4)
    if extra:
        data, start = exefile.alloc(data, bytes(extra))
        for at, kind, rel in fixups:
            new = start + rel
            if kind == 'ptr':
                struct.pack_into('<I', data, at - BASE + FILE_OFF, new)
            else:
                lui_at, lo_at = at
                lo_word = struct.unpack_from('<I', data, lo_at - BASE + FILE_OFF)[0]
                ori = lo_word >> 26 == 0xd
                hi = (new >> 16) if ori else ((new + 0x8000) >> 16) & 0xffff
                lui_word = struct.unpack_from('<I', data, lui_at - BASE + FILE_OFF)[0]
                struct.pack_into('<I', data, lui_at - BASE + FILE_OFF, (lui_word & 0xffff0000) | hi)
                struct.pack_into('<I', data, lo_at - BASE + FILE_OFF, (lo_word & 0xffff0000) | (new & 0xffff))
    files.put(EXE_FILE, data)
    print(f'executable text: {kept} strings in place, {moved} moved ({len(extra)} bytes to the extra segment)')


def dump(lo=0, hi=1 << 32):
    for r in read_rows():
        a = int(r['id'], 16)
        if lo <= a < hi:
            room = r['max_bytes'] + ('' if int(r['refs']) else ' FIXED')
            print(f"{r['id']}\t{room}\t{r['japanese']}" + (f"\t= {r['english']}" if r['english'] else ''))


def import_tsv(path, dry_run=False):
    rows = read_rows()
    by = {r['id']: r for r in rows}
    n, problems = 0, []
    for ln in Path(path).read_text(encoding='utf-8').splitlines():
        if not ln.strip() or ln.startswith('#'):
            continue
        ident, _, text = ln.partition('\t')
        ident, text = ident.strip(), text.strip()
        r = by.get(ident)
        if r is None:
            problems.append(f'{ident}: no such string')
            continue
        try:
            enc = encode(text)
        except UnicodeEncodeError as x:
            problems.append(f'{ident}: character the game cannot show: {x.object[x.start]!r} in {text!r}')
            continue
        if not int(r['refs']) and len(enc) > int(r['max_bytes']):
            problems.append(f'{ident}: {len(enc)} bytes, this string cannot move and has room for {r["max_bytes"]}: {text!r}')
            continue
        jp_lines, en_lines = r['japanese'].count('\\n'), text.count('\\n')
        if jp_lines != en_lines:
            problems.append(f'{ident}: {en_lines} line breaks, the original has {jp_lines} (warning): {text!r}')
        r['english'] = text
        n += 1
    for p in problems:
        print(p)
    if not dry_run:
        with open(csv_path(), 'w', encoding='utf-8', newline='') as f:
            w = csv.DictWriter(f, FIELDS, lineterminator='\n')
            w.writeheader()
            w.writerows(rows)
    print(f'import: {n} strings' + (' checked (dry run)' if dry_run else ' set') + f', {len(problems)} problems')
    return problems


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0], epilog=paths.FOLDER_HELP,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    e = sub.add_parser('extract')
    e.add_argument('--force', action='store_true')
    sub.add_parser('check')
    sub.add_parser('stats')
    d = sub.add_parser('dump')
    d.add_argument('range', nargs='*', help='FROM TO addresses (hex)')
    i = sub.add_parser('import')
    i.add_argument('file')
    i.add_argument('--dry-run', action='store_true')
    args = ap.parse_args(paths.configure(sys.argv[1:] if argv is None else argv))
    if args.cmd == 'extract':
        extract(args.force)
    elif args.cmd == 'check':
        if csv_path().exists():
            items = plan((paths.EXTRACTED / EXE_FILE.lstrip('/')).read_bytes())
            bad = [(a, refs) for a, enc, refs, room in items
                   if len(enc) + 1 > room and any(r[0] in ('gp', 'shared') for r in refs)]
            for a, refs in bad:
                print(f'{a:#x}: too long for its room and not movable ({refs_text(refs)})')
            sys.exit(1 if bad else 0)
    elif args.cmd == 'dump':
        dump(*[int(x, 16) for x in args.range])
    elif args.cmd == 'import':
        import_tsv(args.file, args.dry_run)
    else:
        rows = read_rows()
        kinds = {}
        for r in rows:
            k = 'movable' if int(r['refs']) else 'in place only'
            kinds[k] = kinds.get(k, 0) + 1
        print(f'{len(rows)} strings: ' + ', '.join(f'{n} {k}' for k, n in kinds.items()))


if __name__ == '__main__':
    main()
