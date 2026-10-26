#!/usr/bin/env python3
"""The game's LZ compression and LZ archives (unpacker at 0x13d6e0, size reader 0x13d690).

  lz.py unpack <file> [offset]            unpacked size and the first bytes
  lz.py roundtrip <file> <archive offset> unpack every entry, pack it again, unpack: identical?

Packed data: a 3-byte big-endian unpacked size, then tokens:
  t < 0x80          copy the next t + 1 bytes (1-128 literals)
  t >= 0x80, b      copy ((t & 0x7c) >> 2) + 3 bytes (3-34) from (((t & 3) << 8) | b) + 1 bytes
                    back in the output (1-1024)
An archive: u32 offsets from the archive's start, one per entry (the first one is the table's
size), each entry packed data. 0x13d950 (archive, buffer or 0, index) unpacks an entry;
0x13d9d0 (archive, index) returns its unpacked size.
"""
import struct
import sys

MIN, MAX, WINDOW = 3, 34, 1024


def size_of(data, pos=0):
    return int.from_bytes(data[pos:pos + 3], 'big')


def unpack(data, pos=0):
    """Unpack the packed data at pos; returns (bytes, end position)."""
    size = size_of(data, pos)
    pos += 3
    out = bytearray()
    while len(out) < size:
        t = data[pos]
        pos += 1
        if t < 0x80:
            out += data[pos:pos + t + 1]
            pos += t + 1
        else:
            dist = (((t & 3) << 8) | data[pos]) + 1
            pos += 1
            if dist > len(out):
                raise ValueError(f'copy from before the start at {pos:#x}')
            for _ in range(((t & 0x7c) >> 2) + 3):
                out.append(out[-dist])
    if len(out) != size:
        raise ValueError('a token runs past the stated size')
    return bytes(out), pos


def pack(data):
    """Greedy LZ with hash chains (one step of lookahead); output unpacks with unpack()."""
    data = bytes(data)
    n = len(data)
    if n >= 1 << 24:
        raise ValueError('too big for a 3-byte size')
    out = bytearray(n.to_bytes(3, 'big'))
    heads, prev = {}, [-1] * n
    lits = bytearray()

    def flush():
        for i in range(0, len(lits), 128):
            chunk = lits[i:i + 128]
            out.append(len(chunk) - 1)
            out.extend(chunk)
        lits.clear()

    def insert(i):
        if i + MIN <= n:
            k = data[i:i + MIN]
            prev[i] = heads.get(k, -1)
            heads[k] = i

    def best(i):
        if i + MIN > n:
            return 0, 0
        j = heads.get(data[i:i + MIN], -1)
        bl, bd, tries = 0, 0, 64
        limit = min(MAX, n - i)
        while j >= 0 and i - j <= WINDOW and tries:
            length = 0
            while length < limit and data[j + length] == data[i + length]:
                length += 1
            if length > bl:
                bl, bd = length, i - j
                if length == limit:
                    break
            j = prev[j]
            tries -= 1
        return bl, bd

    i = 0
    while i < n:
        length, dist = best(i)
        if length >= MIN:
            insert(i)
            nl, _ = best(i + 1)
            if nl > length + 1:          # lazy: a literal now buys a longer match
                lits.append(data[i])
                i += 1
                continue
            flush()
            out.append(0x80 | ((length - 3) << 2) | ((dist - 1) >> 8))
            out.append((dist - 1) & 0xff)
            for k in range(i + 1, i + length):
                insert(k)
            i += length
        else:
            insert(i)
            lits.append(data[i])
            i += 1
    flush()
    return bytes(out)


def pack_best(data, tries=256):
    """Optimal parse: the smallest output this format allows for the matches found (longest match
    at each position, every shorter length usable too). Slower than pack(); for pictures that must
    fit their old slot."""
    data = bytes(data)
    n = len(data)
    if n >= 1 << 24:
        raise ValueError('too big for a 3-byte size')
    # longest match (length, distance) at each position
    longest = [(0, 0)] * n
    heads, prev = {}, [-1] * n
    for i in range(n):
        if i + MIN <= n:
            k = data[i:i + MIN]
            j = heads.get(k, -1)
            bl, bd, t = 0, 0, tries
            limit = min(MAX, n - i)
            while j >= 0 and i - j <= WINDOW and t:
                length = 0
                while length < limit and data[j + length] == data[i + length]:
                    length += 1
                if length > bl:
                    bl, bd = length, i - j
                    if length == limit:
                        break
                j = prev[j]
                t -= 1
            if bl >= MIN:
                longest[i] = (bl, bd)
            prev[i] = heads.get(k, -1)
            heads[k] = i
    INF = 1 << 60
    # state at position i: ending in a match (m) or in a literal run of length r (l, run)
    cm = [INF] * (n + 1)
    cl = [INF] * (n + 1)
    run = [0] * (n + 1)
    back_m = [None] * (n + 1)          # (from position, length, distance, from state)
    back_l = [None] * (n + 1)          # from state
    cm[0] = 0
    for i in range(n):
        base_m, base_l = cm[i], cl[i]
        # literal
        if base_l < INF and run[i] < 128 and base_l + 1 < cl[i + 1]:
            cl[i + 1], run[i + 1], back_l[i + 1] = base_l + 1, run[i] + 1, 'l'
        start = min(base_m, base_l if base_l < INF else INF)
        if start + 2 < cl[i + 1]:
            cl[i + 1], run[i + 1], back_l[i + 1] = start + 2, 1, 'm' if base_m <= base_l else 'l*'
        # matches
        bl, bd = longest[i]
        if bl:
            frm = 'm' if base_m <= base_l else 'l'
            c = min(base_m, base_l) + 2
            for length in range(MIN, bl + 1):
                if c < cm[i + length]:
                    cm[i + length], back_m[i + length] = c, (i, length, bd, frm)
    # walk back
    tokens, i = [], n
    state = 'm' if cm[n] <= cl[n] else 'l'
    while i > 0:
        if state == 'm':
            frm_i, length, dist, frm = back_m[i]
            tokens.append(('m', length, dist))
            i, state = frm_i, frm
        else:
            how = back_l[i]
            tokens.append(('l', i - 1))
            i -= 1
            state = 'l' if how in ('l', 'l*') else 'm'
    tokens.reverse()
    out = bytearray(n.to_bytes(3, 'big'))
    lits = bytearray()

    def flush():
        for k in range(0, len(lits), 128):
            chunk = lits[k:k + 128]
            out.append(len(chunk) - 1)
            out.extend(chunk)
        lits.clear()
    for t in tokens:
        if t[0] == 'l':
            lits.append(data[t[1]])
        else:
            flush()
            _, length, dist = t
            out.append(0x80 | ((length - 3) << 2) | ((dist - 1) >> 8))
            out.append((dist - 1) & 0xff)
    flush()
    return bytes(out)


def lengthen(packed, minimum):
    """The same data packed into at least `minimum` bytes: matches from the start turned into
    literals until it is long enough (for a piece whose end must not move back)."""
    size = size_of(packed)
    tokens, pos, out_len = [], 3, 0
    while out_len < size:                # ('l', bytes) or ('m', length, token bytes)
        t = packed[pos]
        if t < 0x80:
            tokens.append(('l', packed[pos + 1:pos + 2 + t]))
            pos += t + 2
            out_len += t + 1
        else:
            n = ((t & 0x7c) >> 2) + 3
            tokens.append(('m', n, packed[pos:pos + 2]))
            pos += 2
            out_len += n
    data, _ = unpack(packed)
    cost = [len(t[1]) + 1 if t[0] == 'l' else 2 for t in tokens]
    suffix = [0] * (len(tokens) + 1)
    for i in range(len(tokens) - 1, -1, -1):
        suffix[i] = suffix[i + 1] + cost[i]
    at = 0
    for k in range(len(tokens) + 1):     # tokens[:k] become one literal prefix
        if 3 + at + (at + 127) // 128 + suffix[k] >= minimum:
            break
        if k < len(tokens):
            at += len(tokens[k][1]) if tokens[k][0] == 'l' else tokens[k][1]
    else:
        raise ValueError('cannot lengthen enough')
    out = bytearray(size.to_bytes(3, 'big'))
    lits = data[:at]
    for i in range(0, len(lits), 128):
        out.append(len(lits[i:i + 128]) - 1)
        out += lits[i:i + 128]
    for tok in tokens[k:]:
        if tok[0] == 'l':
            out.append(len(tok[1]) - 1)
            out += tok[1]
        else:
            out += tok[2]
    if unpack(bytes(out))[0] != data:
        raise ValueError('lengthen: round trip failed')
    return bytes(out)


def archive_entries(data, base):
    """(offset, packed data end) of each entry of the archive at base."""
    first = struct.unpack_from('<I', data, base)[0]
    offs = struct.unpack_from(f'<{first // 4}I', data, base)
    return [(base + o, unpack(data, base + o)[1]) for o in offs]


def read_archive(data, base):
    return [unpack(data, p)[0] for p, _ in archive_entries(data, base)]


def build_archive(entries, align=1):
    """An archive of the given unpacked entries (packed here)."""
    table = 4 * len(entries)
    blobs, offs, pos = [], [], table
    for e in entries:
        b = pack(e)
        offs.append(pos)
        blobs.append(b)
        pos += len(b)
        pad = -pos % align
        if pad:
            blobs[-1] += bytes(pad)
            pos += pad
    return struct.pack(f'<{len(offs)}I', *offs) + b''.join(blobs)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) >= 2 and argv[0] == 'unpack':
        data = open(argv[1], 'rb').read()
        out, end = unpack(data, int(argv[2], 16) if len(argv) > 2 else 0)
        print(f'{len(out):#x} bytes, packed data ends at {end:#x}: {out[:32].hex()}')
    elif len(argv) == 3 and argv[0] == 'roundtrip':
        data = open(argv[1], 'rb').read()
        base = int(argv[2], 16)
        entries = read_archive(data, base)
        old = archive_entries(data, base)
        new = build_archive(entries)
        back = read_archive(new, 0)
        assert back == entries, 'round trip failed'
        print(f'{len(entries)} entries: {old[-1][1] - base:#x} bytes packed by the game, '
              f'{len(new):#x} packed here; all identical after unpacking')
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main())
