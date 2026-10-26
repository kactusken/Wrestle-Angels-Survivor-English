#!/usr/bin/env python3
"""The game's data files (/A000/A000. ... /A040/A04A.): the XOR cipher, LZ pieces, offset tables.

  datafile.py info FILE...        what each file is (cipher, LZ pieces, table)

*From the code* (0x16cf50 (buffer, size, mode)): most data files are enciphered with the 30-byte
key at 0x47c4b0 (exe file offset 0x37c530). Starting at k = 0, each byte is XORed with key[k],
then k = ((k + plain byte) & 0x1e) + 1, and k = 0 once it reaches 0x1e. Mode 1 deciphers, mode 0
enciphers (the step uses the plain byte either way).

What is inside (*from the data*; round trip checked by tools/datafile.py roundtrip):
  - a sequence of LZ pieces (tools/lz.py) at 2048-byte boundaries, each enciphered on its own
    (the key restarts at every piece), usually one TIM2 picture each;
  - or one enciphered stream holding a u32 offset table (entries: LZ pieces or raw data);
  - a few files are plain LZ (A001, A01A, A03A).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lz  # noqa: E402

KEY_OFFSET = 0x37c530            # in SLPM_662.39 (RAM 0x47c4b0)
KEY_LEN = 30
SECTOR = 0x800
_key = None


def key():
    global _key
    if _key is None:
        import paths
        _key = (paths.EXTRACTED / 'SLPM_662.39').read_bytes()[KEY_OFFSET:KEY_OFFSET + KEY_LEN]
    return _key


def decipher(data):
    k, out, kk = 0, bytearray(len(data)), key()
    for i, b in enumerate(data):
        p = b ^ kk[k]
        out[i] = p
        k = ((k + p) & 0x1e) + 1
        if k >= 0x1e:
            k = 0
    return bytes(out)


def encipher(data):
    k, out, kk = 0, bytearray(len(data)), key()
    for i, p in enumerate(data):
        out[i] = p ^ kk[k]
        k = ((k + p) & 0x1e) + 1
        if k >= 0x1e:
            k = 0
    return bytes(out)


def _piece_at(data, pos):
    """(unpacked bytes, packed length) of the enciphered LZ piece at pos, or None."""
    size = lz.size_of(decipher(data[pos:pos + 3]))
    # packed data is at most 129/128 of the unpacked size plus the header (all literals)
    plain = decipher(data[pos:pos + size + size // 128 + 8])
    try:
        return lz.unpack(plain)
    except (ValueError, IndexError):
        return None


def pieces(data):
    """[(offset, unpacked bytes)] of separately enciphered LZ pieces: usually at 2048-byte
    boundaries with zeros between, but in A040 they follow each other with no gap (the 2nd starts
    at 0xf7f8); a piece packed again smaller leaves zeros (whole sectors, too) before the next."""
    out, pos = [], 0
    while pos < len(data):
        if out:
            # the first non-zero byte after the last piece, if it is not on a boundary and a piece
            # unpacks there (else the next boundary, as an enciphered piece may start with 0)
            nz = len(data) - len(data[pos:].lstrip(b'\0'))
            if nz < len(data) and nz % SECTOR and _piece_at(data, nz):
                pos = nz
            else:
                pos = (pos + SECTOR - 1) & ~(SECTOR - 1)
        while pos < len(data) and not any(data[pos:pos + 16]):
            pos += SECTOR
        if pos >= len(data):
            break
        r = _piece_at(data, pos)
        if r is None:
            break
        body, end = r
        out.append((pos, body))
        pos += end
    if out:
        pos = (pos + SECTOR - 1) & ~(SECTOR - 1)
    return out, pos


def build_pieces(bodies):
    """Pack and encipher each piece, each starting at a sector boundary."""
    out = bytearray()
    for b in bodies:
        out += bytes(-len(out) % SECTOR)
        out += encipher(lz.pack(b))
    return bytes(out)


def single(data):
    """The unpacked contents of a file that is one enciphered LZ piece."""
    body, end = lz.unpack(decipher(data))
    return body


def build_single(body):
    return encipher(lz.pack(body))


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) >= 2 and argv[0] == 'info':
        for f in argv[1:]:
            data = Path(f).read_bytes()
            ps, end = pieces(data)
            print(f'{f}: {len(data):#x} bytes, {len(ps)} enciphered LZ piece(s) up to {end:#x}'
                  + (', then something else' if end < len(data) - SECTOR else ''))
        return 0
    print(__doc__)
    return 2


if __name__ == '__main__':
    sys.exit(main())
