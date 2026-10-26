#!/usr/bin/env python3
"""Game images: the TIM2 pictures inside the data files /A000/A000. - /A040/A04A.

export_all(extracted, out) writes out/<id>.png (indexed, the game's palette) and out/<id>.json.
import_images(images, files) puts English pictures back.

Containers (tools/datafile.py): a file is one of
  plain    one plain LZ piece (A001, A01A, A03A)
  pieces   LZ pieces at 2048-byte boundaries, each enciphered on its own
  table    one enciphered stream: a u32 offset table, entries are LZ pieces
  dir      a plain header of n u32 offsets then n u32 sizes, each entry one enciphered LZ piece
           at a 2048-byte boundary (A006: month and screen-title banners)
  archive16  an LZ archive (u32 offset table, entries at 2048-byte boundaries) under a second
           cipher (A00B; *from the code*: 0x16d010(buffer, size, key, mode)): the first
           min(size - 2, 200000) bytes as u16 halfwords h; deciphered = swap_bytes(h) ^ key, key + 1
           for each; the key is the file's last u16 (the game zeroes it after deciphering). So
           only the head (the table and the first entries) is enciphered. The game loads the whole
           file (its size is a constant at 0x17cef4) and reads entries by number (0x13d950); entries
           keep their places here, the key is kept.
Inside a piece or entry: a TIM2 file (one or more pictures; tools/tim2.py).
Ids: <file>_<part>_<picture>, e.g. A00A_p1_0 (piece 1, picture 0), A013_t3_0 (table entry 3),
A001_0 (plain). Only pieces/entries with a changed picture are packed again.

Some loads pass a file's size as a constant: to the decipher routine (0x16cf50(buffer, size, 1),
e.g. A013 at 0x1aaff0, or as lui/ori for bigger files: A00C 0x171c58, A024 0x1ff488 - patched
automatically) or to a loader (A048, A049: SIZE_CONSTANTS).
Any other code immediate equal to the old size stops the build until it has been checked.
No dependencies here: build.py must run on a plain python3.
"""
import json
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import datafile  # noqa: E402
import exefile  # noqa: E402
import lz  # noqa: E402
import pngio  # noqa: E402
import tim2  # noqa: E402

FILES = [f'/A0{h:02X}/A0{i:02X}.' for h in (0x00, 0x20, 0x40) for i in range(h, min(h + 0x20, 0x4b))]
EXE = '/SLPM_662.39'
SIZE_CONSTANTS = {'/A040/A049.': [0x222b64]}       # ori a2, zero, 0x81b8 (with A048's load)
ARCHIVE16 = {'/A000/A00B.'}
CIPHER16_MAX = 100000                               # halfwords


def _try_unpack(data, pos=0):
    try:
        return lz.unpack(data, pos)
    except (ValueError, IndexError):
        return None


def _table(data):
    if len(data) < 8:
        return None
    first = struct.unpack_from('<I', data, 0)[0]
    if first < 4 or first % 4 or first > min(len(data), 0x10000):
        return None
    offs = list(struct.unpack_from(f'<{first // 4}I', data, 0))
    while len(offs) > 1 and offs[-1] == 0:
        offs.pop()
    if any(offs[i] > offs[i + 1] for i in range(len(offs) - 1)) or offs[-1] > len(data):
        return None
    return first, offs


def _dir(data):
    """[(offset, size)] of a 'dir' header, or None."""
    first = struct.unpack_from('<I', data, 0)[0] if len(data) >= 8 else 0
    if not first or first % datafile.SECTOR or first > len(data):
        return None
    words = list(struct.unpack_from(f'<{first // 4}I', data, 0))
    offs = []
    for w in words:
        if not w or w % datafile.SECTOR or w >= len(data) or (offs and w <= offs[-1]):
            break
        offs.append(w)
    n = len(offs)
    sizes = words[n:2 * n]
    if n < 2 or len(sizes) < n or any(words[2 * n:]):
        return None
    ends = offs[1:] + [len(data)]
    if any(not 0 < s <= e - o for o, s, e in zip(offs, sizes, ends)):
        return None
    return list(zip(offs, sizes))


def _cipher16(data, decipher):
    """A00B's halfword cipher over a copy of data (key = the last u16, kept)."""
    out = bytearray(data)
    key = struct.unpack_from('<H', data, len(data) - 2)[0]
    for i in range(min((len(data) - 2) // 2, CIPHER16_MAX)):
        h = struct.unpack_from('<H', out, 2 * i)[0]
        if decipher:
            h = (((h & 0xff) << 8) | (h >> 8)) ^ key
        else:
            h ^= key
            h = ((h & 0xff) << 8) | (h >> 8)
        struct.pack_into('<H', out, 2 * i, h)
        key = (key + 1) & 0xffff
    return out


def _archive16(data):
    plain = _cipher16(data, True)
    first = struct.unpack_from('<I', plain, 0)[0]
    offs = [o for o in struct.unpack_from(f'<{first // 4}I', plain, 0) if o]
    ends = offs[1:] + [len(data) - 2]
    return plain, [(o, e, lz.unpack(plain, o)[0]) for o, e in zip(offs, ends)]


def container(data, f=None):
    """(kind, parts) - parts: [(start, end, unpacked bytes or None)]."""
    if f in ARCHIVE16:
        return 'archive16', _archive16(data)[1]
    d = _dir(data)
    if d:
        return 'dir', [(o, o + s, datafile.single(data[o:o + s])) for o, s in d]
    r = _try_unpack(data)
    if r and r[1] >= len(data) - 16 and not data[0] & 0x80:
        return 'plain', [(0, len(data), r[0])]
    plain = datafile.decipher(data)
    t = _table(plain)
    r0 = _try_unpack(plain)
    if t and not (r0 and r0[0][:4] == b'TIM2'):
        _, offs = t
        bounds = offs + [len(plain)]
        parts = []
        for i in range(len(offs)):
            s, e = bounds[i], bounds[i + 1]
            u = _try_unpack(plain, s)
            parts.append((s, e, u[0] if u and u[1] <= e else None))
        return 'table', parts
    ps, end = datafile.pieces(data)
    parts = []
    for i, (pos, body) in enumerate(ps):
        nxt = ps[i + 1][0] if i + 1 < len(ps) else end
        parts.append((pos, nxt, body))
    if end < len(data):
        parts.append((end, len(data), None))          # the rest, kept as it is
    return 'pieces', parts


def _pictures(body):
    if not body or body[:4] != b'TIM2':
        return []
    try:
        return tim2.parse(body, 0)
    except Exception:
        return []


def _stem(f):
    return f.split('/')[-1].rstrip('.')


def export_all(extracted, out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    n = 0
    for f in FILES:
        p = Path(extracted) / f.lstrip('/')
        if not p.exists() or p.stat().st_size > 40_000_000:
            continue
        kind, parts = container(p.read_bytes(), f)
        tag = {'plain': '', 'pieces': 'p', 'table': 't', 'dir': 'p', 'archive16': 'p'}[kind]
        for i, (s, e, body) in enumerate(parts):
            for k, pic in enumerate(_pictures(body)):
                ident = f'{_stem(f)}_{tag}{i}_{k}' if tag else f'{_stem(f)}_{k}'
                try:
                    tim2.to_png(body, pic, out / f'{ident}.png')
                except Exception:
                    continue
                (out / f'{ident}.json').write_text(json.dumps(
                    {'file': f, 'kind': kind, 'part': i, 'picture': k}))
                n += 1
    return n


def _parse_id(ident):
    stem, *rest = ident.split('_')
    f = next(x for x in FILES if _stem(x) == stem)
    if len(rest) == 1:
        return f, 0, int(rest[0])
    return f, int(rest[0][1:]), int(rest[1])


def _size_refs(exe, size):
    """Code addresses of addiu/ori rX, zero, size."""
    if size > 0xffff:
        return []
    n = (exefile.CODE_END - exefile.BASE) // 4
    words = struct.unpack_from(f'<{n}I', exe, exefile.FILE_OFF)
    return [exefile.BASE + 4 * i for i, w in enumerate(words)
            if w >> 26 in (9, 13) and (w >> 21) & 31 == 0 and w & 0xffff == size]


DECIPHER = 0x16cf50
SIZE_WORDS = (0x480000, 0x586880)        # data where (offset, size) / (size, count) tables live


def _patch_size_words(files, f, old, new):
    """Aligned u32 words equal to a file's old size in the data tables (e.g. 0x5854a0: size,
    count of A027-A039) take the new size. Small sizes are too likely to be other numbers."""
    exe = files.get(EXE)
    lo, hi = exefile.off(SIZE_WORDS[0]), exefile.off(SIZE_WORDS[1])
    hits = [o for o in range(lo, hi, 4) if struct.unpack_from('<I', exe, o)[0] == old]
    if hits and old < 0x4000:
        raise SystemExit(f'gfx: {f}: its size {old:#x} occurs in the data tables and is too small to '
                         f'tell from other numbers - check {[hex(o - exefile.FILE_OFF + exefile.BASE) for o in hits]}')
    for o in hits:
        struct.pack_into('<I', exe, o, new)
    if hits:
        files.put(EXE, exe)


def _feeds_decipher(exe, at):
    """True if the size constant at `at` is an argument of a call to the decipher routine
    within the next 3 instructions (0x16cf50(buffer, size, 1))."""
    jal = (3 << 26) | (DECIPHER >> 2)
    return any(struct.unpack_from('<I', exe, exefile.off(at + 4 * k))[0] == jal for k in range(1, 4))


def _used(data, s):
    """Packed length of the piece at s."""
    size = lz.size_of(datafile.decipher(data[s:s + 3]))
    return lz.unpack(datafile.decipher(data[s:s + size + size // 128 + 8]))[1]


def _piece_table(exe, data, parts):
    """Address of the (offset, packed size) table that lists every piece, or None.
    *From the code*: e.g. 0x484a70 for A04A (read at 0x222bac)."""
    pairs = b''.join(struct.pack('<II', s, _used(data, s)) for s, _, b in parts if b is not None)
    i = exe.find(pairs)
    if i < 0 or (i - exefile.FILE_OFF) % 4:
        return None
    return i - exefile.FILE_OFF + exefile.BASE


def _pack_fit(body, room):
    """The quick packer if its output fits `room` bytes, else the optimal one (slower)."""
    pk = lz.pack(body)
    return pk if len(pk) <= room else lz.pack_best(body)


def _rebuild_pieces(f, data, parts, bodies, files):
    """Changed pieces in their old slots if they fit (their sizes in the executable's table of
    (offset, size) updated); otherwise every piece is laid out again at 2048-byte boundaries and
    the table rewritten."""
    packed = {i: datafile.encipher(_pack_fit(b, min(parts[i][1], len(data)) - parts[i][0]))
              for i, b in bodies.items()}
    real = [i for i, (_, _, b) in enumerate(parts) if b is not None]
    fits = all(len(packed[i]) <= min(parts[i][1], len(data)) - parts[i][0] for i in packed)
    exe = files.get(EXE)
    table = _piece_table(bytes(exe), data, parts)
    if fits:
        # the game reads a piece's size from the table: a piece packed bigger than before was cut
        # short there, losing its CLUT (the end of the TIM2) - name strips in odd colours (test12)
        out = bytearray(data)
        for i, pk in packed.items():
            s_, e_ = parts[i][0], min(parts[i][1], len(data))
            out[s_:e_] = pk + bytes(e_ - s_ - len(pk))
            if table is not None:
                struct.pack_into('<I', exe, exefile.off(table) + 8 * real.index(i) + 4, len(pk))
        if table is not None and packed:
            files.put(EXE, exe)
        return bytes(out)
    if len(real) > 1 and table is None:
        bad = [i for i in packed if len(packed[i]) > parts[i][1] - parts[i][0]]
        raise SystemExit(f'gfx: {f}: piece(s) {bad} outgrow their slots and no (offset, size) table '
                         f'for the file was found in the executable')
    out, entries = bytearray(), []
    for i, (s_, e_, b) in enumerate(parts):
        if b is None:                          # an unknown rest stays at the end
            out += bytes(-len(out) % datafile.SECTOR) + data[s_:e_]
            continue
        out += bytes(-len(out) % datafile.SECTOR)
        pk = packed[i] if i in packed else data[s_:s_ + _used(data, s_)]
        entries.append((len(out), len(pk)))
        out += pk
    if table is not None:
        o = exefile.off(table)
        for k, (off, size) in enumerate(entries):
            struct.pack_into('<II', exe, o + 8 * k, off, size)
        files.put(EXE, exe)
    return bytes(out)


def import_images(images, files):
    by_file = {}
    for ident, path in images.items():
        f, part, k = _parse_id(ident)
        by_file.setdefault(f, {}).setdefault(part, {})[k] = path
    count = 0
    for f, parts_new in sorted(by_file.items()):
        data = bytes(files.get(f))
        kind, parts = container(data, f)
        bodies = {}
        for part, pics in parts_new.items():
            body = bytearray(parts[part][2])
            for k, path in pics.items():
                pic = _pictures(bytes(body))[k]
                png = pngio.read(path)
                if (png.width, png.height) != (pic.width, pic.height):
                    raise SystemExit(f'gfx: {path}: {png.width}x{png.height}, the original is '
                                     f'{pic.width}x{pic.height}')
                tim2.put_indices(body, pic, png.rows)
                count += 1
            bodies[part] = bytes(body)
        if kind == 'plain':
            new = lz.pack(bodies[0])
        elif kind == 'pieces':
            # pieces are read by absolute offset (tables like 0x480a80: offset, size): every piece
            # keeps its place, and a changed one must fit its slot
            new = _rebuild_pieces(f, data, parts, bodies, files)
            out = bytearray(new)
            new = bytes(out)
        elif kind == 'archive16':
            plain, _ = _archive16(data)
            out = bytearray(plain)
            for i, body in bodies.items():
                s, e = parts[i][0], parts[i][1]
                pk = _pack_fit(body, e - s)
                if len(pk) > e - s:
                    raise SystemExit(f'gfx: {f}: entry {i} packs to {len(pk):#x} bytes, more than '
                                     f'its {e - s:#x}-byte slot')
                out[s:e] = pk + bytes(e - s - len(pk))
            new = bytes(_cipher16(out, False))
        elif kind == 'dir':
            # the header lists (offset, size): pieces stay where they are if they fit their slot
            # (the game may read the file whole), else the file is laid out again
            n = len(parts)
            packed = {i: datafile.encipher(lz.pack(b)) for i, b in bodies.items()}
            ends = [p[0] for p in parts[1:]] + [len(data)]
            if all(len(pk) <= ends[i] - parts[i][0] for i, pk in packed.items()):
                out = bytearray(data)
                for i, pk in packed.items():
                    s = parts[i][0]
                    out[s:ends[i]] = pk + bytes(ends[i] - s - len(pk))
                    struct.pack_into('<I', out, 4 * (n + i), len(pk))
            else:
                out = bytearray(parts[0][0])
                entries = []
                for i, (s, e, _) in enumerate(parts):
                    out += bytes(-len(out) % datafile.SECTOR)
                    pk = packed[i] if i in packed else data[s:e]
                    entries.append((len(out), len(pk)))
                    out += pk
                struct.pack_into(f'<{2 * n}I', out, 0, *[o for o, _ in entries], *[z for _, z in entries])
            new = bytes(out)
        else:
            plain = datafile.decipher(data)
            first = struct.unpack_from('<I', plain, 0)[0]
            aligned = all(s % datafile.SECTOR == 0 for s, _, _ in parts)
            out = bytearray(plain[:first])
            offs = []
            for i, (s, e, body) in enumerate(parts):
                if aligned:
                    out += bytes(-len(out) % datafile.SECTOR)
                offs.append(len(out))
                out += lz.pack(bodies[i]) if i in bodies else plain[s:e]
            struct.pack_into(f'<{len(offs)}I', out, 0, *offs)
            new = datafile.encipher(bytes(out))
        if len(new) != len(data):
            if f in SIZE_CONSTANTS:
                exe = files.get(EXE)
                for at in SIZE_CONSTANTS[f]:
                    o = exefile.off(at)
                    w = struct.unpack_from('<I', exe, o)[0]
                    if w & 0xffff != len(data) or len(new) > (0x7fff if w >> 26 == 9 else 0xffff):
                        raise SystemExit(f'gfx: {f}: unexpected size constant at {at:#x}')
                    struct.pack_into('<I', exe, o, (w & 0xffff0000) | len(new))
                files.put(EXE, exe)
            else:
                exe = files.get(EXE)
                refs = _size_refs(bytes(exe), len(data))
                safe = [a for a in refs if _feeds_decipher(exe, a)]
                if set(refs) - set(safe):
                    raise SystemExit(f'gfx: {f} changes size ({len(data):#x} -> {len(new):#x}) and the '
                                     f'code has its size as a constant at '
                                     f'{", ".join(hex(a) for a in sorted(set(refs) - set(safe)))}'
                                     f' - check them and list them in SIZE_CONSTANTS')
                for at in safe:
                    o = exefile.off(at)
                    w = struct.unpack_from('<I', exe, o)[0]
                    if len(new) > (0x7fff if w >> 26 == 9 else 0xffff):
                        raise SystemExit(f'gfx: {f}: {len(new):#x} bytes no longer fits the constant at {at:#x}')
                    struct.pack_into('<I', exe, o, (w & 0xffff0000) | len(new))
                # sizes over 0xffff: lui/ori pairs feeding the decipher call
                pairs = [(a, b) for a, b in exefile.refs(bytes(exe), len(data)) if _feeds_decipher(exe, b)]
                if pairs:
                    exefile.repoint(exe, pairs, len(new))
                if safe or pairs:
                    files.put(EXE, exe)
                _patch_size_words(files, f, len(data), len(new))
        files.put(f, new)
    return count
