#!/usr/bin/env python3
"""The executable (SLPM_662.39): addresses, code references, and room for data that grew.

  exefile.py refs ADDR        lui/addiu pairs that build ADDR (hex)
  exefile.py extra FILE       the extra segment of a built executable: size, heap patches

One PT_LOAD holds everything (file 0x80 -> RAM 0x100000, .bss up to 0x8ef300); the ELF already
has a second, empty PT_LOAD at 0x8ef300. Data that no longer fits where it was goes there (the
"extra" segment, grown by place()); the code's references to the old address are repointed.
The heap starts after it, as in WAS2 - three things know where memory ends (*from the code*):
  - crt0's SetupHeap(0x8ef300, -1) at 0x1001d0/0x1001d8;
  - sbrk() (0x10dee0) keeps its break in the word at 0x23e374, initialised to 0x8ef300 - malloc
    takes memory from there, so this is the one that matters;
  - 0x13f3b0 sizes the game's memory pool as 0x2000000 - (end + 0x102000) - 0x10.
Moving all three past the extra segment keeps the game's allocations off the moved data.
"""
import struct
import sys

FILE_OFF, BASE = 0x80, 0x100000
CODE_END = 0x240000
BSS_END = 0x8ef300
BREAK_WORD = 0x23e374
END_REFS = [(0x1001d0, 0x1001d8), (0x13f3bc, 0x13f3c0)]      # lui / addiu pairs building BSS_END


def u32(d, o):
    return struct.unpack_from('<I', d, o)[0]


def off(addr):
    if not BASE <= addr < BSS_END:
        raise ValueError(f'{addr:#x} is not in the loaded image')
    return addr - BASE + FILE_OFF


def s16(x):
    return x - 0x10000 if x & 0x8000 else x


def hi_lo(addr):
    return ((addr + 0x8000) >> 16) & 0xffff, addr & 0xffff


def refs(exe, target, window=24):
    """[(lui pc, lo pc)] of lui rX / (addiu|ori|load|store) rX pairs that build target."""
    out = []
    hi, _ = hi_lo(target)
    n = (CODE_END - BASE) // 4
    words = struct.unpack_from(f'<{n}I', exe, FILE_OFF)
    for i, w in enumerate(words):
        if w >> 26 != 15 or w & 0xffff not in (hi, (target >> 16) & 0xffff):
            continue
        reg = (w >> 16) & 31
        for j in range(i + 1, min(n, i + window)):
            w2 = words[j]
            op = w2 >> 26
            if (w2 >> 21) & 31 == reg and op in (9, 13, 32, 33, 35, 36, 37, 40, 41, 43):
                lo = w2 & 0xffff
                a = ((w & 0xffff) << 16) | lo if op == 13 else (((w & 0xffff) << 16) + s16(lo)) & 0xffffffff
                if a == target:
                    out.append((BASE + 4 * i, BASE + 4 * j))
            if op == 15 and (w2 >> 16) & 31 == reg:
                break
    return out


def repoint(exe, pairs, new):
    """Point each lui/lo pair at new (the lo instruction keeps its opcode and registers)."""
    for a, b in pairs:
        w1, w2 = u32(exe, off(a)), u32(exe, off(b))
        hi, lo = hi_lo(new)
        if w2 >> 26 == 13:                       # ori: no carry
            hi = (new >> 16) & 0xffff
        struct.pack_into('<I', exe, off(a), (w1 & 0xffff0000) | hi)
        struct.pack_into('<I', exe, off(b), (w2 & 0xffff0000) | lo)


# --- the extra segment ---------------------------------------------------------------------------

def _phdrs(exe):
    phoff = u32(exe, 28)
    size, num = struct.unpack_from('<HH', exe, 42)
    return [phoff + i * size for i in range(num)]


def _extra_phdr(exe):
    for p in _phdrs(exe):
        t, o, v, pa, fs, ms = struct.unpack_from('<6I', exe, p)
        if t == 1 and v == BSS_END:
            return p, o, fs
    raise SystemExit('exefile: the empty PT_LOAD at 0x8ef300 is missing')


def extra_size(exe):
    return _extra_phdr(exe)[2]


def alloc(exe, blob, align=16):
    """Append blob to the extra segment; returns (new exe, RAM address of blob)."""
    exe = bytearray(exe)
    p, o, fs = _extra_phdr(exe)
    if fs == 0:                                  # first use: the segment goes at the end of the file
        o = (len(exe) + 0x7f) & ~0x7f
        exe += bytes(o - len(exe))
    start = (fs + align - 1) & ~(align - 1)
    data = exe[o:o + fs] + bytes(start - fs) + blob
    if o + fs != len(exe):
        raise SystemExit('exefile: the extra segment is not at the end of the file')
    exe[o:] = data
    end = (BSS_END + len(data) + 15) & ~15
    struct.pack_into('<6I', exe, p, 1, o, BSS_END, BSS_END, len(data), end - BSS_END)
    _move_heap(exe, end)
    return exe, BSS_END + start


def _move_heap(exe, end):
    struct.pack_into('<I', exe, off(BREAK_WORD), end)
    repoint(exe, END_REFS, end)


def place(exe, label, start, stop, blob, ram_addr, expect_refs=None):
    """Put blob where the original was (file offsets start..stop) or, if longer, in the extra
    segment with every lui/addiu reference to ram_addr repointed. Returns the new exe."""
    exe = bytearray(exe)
    if len(blob) <= stop - start:
        exe[start:stop] = blob + bytes(stop - start - len(blob))
        return exe
    pairs = refs(exe, ram_addr)
    if expect_refs is not None and len(pairs) != expect_refs:
        raise SystemExit(f'exefile: {label}: expected {expect_refs} references to {ram_addr:#x}, '
                         f'found {len(pairs)}')
    if not pairs:
        raise SystemExit(f'exefile: {label} grew ({len(blob):#x} > {stop - start:#x} bytes) and '
                         f'nothing in the code points at {ram_addr:#x}')
    exe, new = alloc(exe, blob)
    repoint(exe, pairs, new)
    return exe


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) == 2 and argv[0] == 'refs':
        sys.path.insert(0, __file__.rsplit('/', 1)[0])
        import paths
        exe = (paths.EXTRACTED / 'SLPM_662.39').read_bytes()
        for a, b in refs(exe, int(argv[1], 16)):
            print(f'{a:08x} .. {b:08x}')
    elif len(argv) == 2 and argv[0] == 'extra':
        exe = open(argv[1], 'rb').read()
        print(f'extra segment: {extra_size(exe):#x} bytes; break word: {u32(exe, off(BREAK_WORD)):#x}')
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main())
