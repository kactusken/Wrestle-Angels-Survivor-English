#!/usr/bin/env python3
"""The wrestler info screen and the roster lists: room for English values (a build step).

*From the code* (0x178440, the status screen function): each page is printed with sprintf into
rows of 54 bytes (sp+0x660, 0x696, ...) that are drawn into a text texture, 11 px per byte; a
layout table of 24-byte sprites (w, h, screen x, y, texture u, v) then cuts each value out of its
row at a fixed byte column. The Japanese values had fixed byte lengths, the English ones don't, so
everything after a longer value moved into the wrong sprite (page 1 showed "Normal  Regu" as the
status and the hometown under HP). Fixed here:

  page 1   the row of rating / status + faction / age / hometown / HP / trust: its sprintf gets
           its arguments in a new order (ROW2_ARGS) and prints "%4d%2d%-9.9s%4d%4d%s %s" -
           fixed widths first, the status and faction (no 軍; short English, exe.csv) last, so
           they need no padding; the coach variant the same without them.
           The hometown is no longer padded by length (it centred 4- and 6-byte Japanese names
           in 8 bytes, 0x17941c/0x179464): the row's %-9.9s pads it.
           The English labels are wider than the 2-character Japanese ones: the long values
           (name, promotion, coach, wrestlers) move to x = 118 and the right column's hometown
           and popularity to x = 258 on screen. Status and alignment stay at 231: their labels
           are short, and the alignment bar ends at 295 (NORMAL at 258 ran past it, test7).
  page 2   the row of stats + nickname (寸評) was turned into full-width characters (0x13ce30),
           which spaced the English out, and a loop turned every 'F' into 'S' (stat 15 shows as
           rank S). The nickname now leaves that row: save_nick (at the row's sprintf, 0x17aca0)
           copies the nickname into a buffer of its own, and copy_nick (at the last copy of the
           converted rows, 0x17ad80) puts it back into row 1 at byte 20, where the Japanese had it
           and where its sprite reads it (two spaces bridge the 18 bytes of full-width stats).
           Rows 4 (test4) and 3 (test6) as the nickname's row both showed garbage. Its label is
           now Nickname (titles from 0x19c150: "Suplex Goddess", "%s World Champ"), and the value
           moves to x = 118 like page 1's, cut to 27 cells so it ends with its bar (x 415).
  F -> S   the same loop runs over the roster lists' rows (0x179cc8), names included ("Gold
           Fenrir" became "Gold Senrir"). Both loops now call a routine that changes an 'F' only
           when it stands alone (after NUL, a space or a full-width space, before NUL, a space
           or a full-width character): a stat value.
"""
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import exefile  # noqa: E402

EXE = '/SLPM_662.39'
SPRINTF, STRCPY = 0x128bd8, 0x1292b8

# (address, original, new) - format strings, in place (the new ones are shorter)
STRINGS = [
    (0x4969d0, '%4d　%s　%s軍　%2d　%s　%4d　%4d', '%4d%2d%-9.9s%4d%4d%s %s'),
    (0x496a00, '%4d　　　　　　　　%2d　%s　%4d　%4d', '%4d%2d%-9.9s%4d%4d'),
    (0x496a80, '%X　%X　%X　%X　%X　%s', '%X　%X　%X　%X　%X'),
]
# layout tables: (table, entries); sprite (u, v) -> (new u, v, new w)
LAYOUTS = [(0x4930d0, 13), (0x4934b0, 10), (0x493210, 16)]
SPRITES = {
    (66, 44): (253, 44, 143),    # status + faction: last in the row, up to 13 cells
    (220, 44): (44, 44, 22),     # age
    (264, 44): (66, 44, 99),     # hometown
    (374, 44): (165, 44, 44),    # HP
    (440, 44): (209, 44, 44),    # trust
    (220, 22): (220, 22, 297),   # page 2's nickname: 27 cells from x 118
}
# screen x of value sprites, by (x, y)
DESTS = {(98, 62): 118, (98, 92): 118, (101, 272): 118, (101, 302): 118,
         (231, 152): 258, (231, 212): 258, (102, 62): 118}
DEST_TABLES = (0x4930d0, 0x4934b0, 0x493210)
NICKNAME_AT = 20                 # byte of row 1 where the nickname stood (its sprite: u = 220)
# page 1's row-2 sprintf (0x17a8c0-0x17a904): the arguments in a new order - rating, age,
# hometown, HP, trust, status (t3), faction (on the stack) - so the variable-length status and
# faction come last and need no padding: (original, new)
ROW2_ARGS = [
    (0x8fa20470, 0x8e420000),   # lw v0, 0x470(sp) (trust)     -> lw v0, 0(s2)    status index
    (0xffa20000, 0x00021080),   # sd v0, 0(sp)                 -> sll v0, v0, 2
    (0x8e420000, 0x005d1821),   # lw v0, 0(s2)                 -> addu v1, v0, sp
    (0x00021080, 0x27a204bc),   # sll v0, v0, 2                -> addiu v0, sp, 0x4bc (faction index)
    (0x005d1821, 0x8c420000),   # addu v1, v0, sp              -> lw v0, 0(v0)
    (0x27a204bc, 0x00021080),   # addiu v0, sp, 0x4bc          -> sll v0, v0, 2
    (0x8c420000, 0x005d1021),   # lw v0, 0(v0)                 -> addu v0, v0, sp
    (0x00021080, 0x8c6b0510),   # sll v0, v0, 2                -> lw t3, 0x510(v1)  status
    (0x005d1021, 0x8c420950),   # addu v0, v0, sp              -> lw v0, 0x950(v0)  faction
    (0x27a406cc, 0xffa20000),   # addiu a0, sp, 0x6cc          -> sd v0, 0(sp)
    (0x3c050049, 0x27a406cc),   # lui a1, 0x49                 -> addiu a0, sp, 0x6cc
    (0x24a569d0, 0x3c050049),   # addiu a1, a1, 0x69d0         -> lui a1, 0x49
    (0x8fa604b0, 0x24a569d0),   # lw a2, 0x4b0(sp)             -> addiu a1, a1, 0x69d0
    (0x8c670510, 0x8fa604b0),   # lw a3, 0x510(v1)             -> lw a2, 0x4b0(sp)  rating
    (0x8c480950, 0x8fc70000),   # lw t0, 0x950(v0)             -> lw a3, 0(fp)      age
    (0x8fc90000, 0x27a80540),   # lw t1, 0(fp)                 -> addiu t0, sp, 0x540 hometown
    (0x27aa0540, 0x8fa90490),   # addiu t2, sp, 0x540          -> lw t1, 0x490(sp)  HP
    (0x8fab0490, 0x8faa0470),   # lw t3, 0x490(sp)             -> lw t2, 0x470(sp)  trust
]
# instruction words: (address, original, new or a label)
PATCHES = [
    *[(0x17a8c0 + 4 * i, old, new) for i, (old, new) in enumerate(ROW2_ARGS)],
    (0x17941c, 0x24030004, 0x2403007f),     # strlen == 4 -> never: no centring
    (0x179464, 0x24030006, 0x2403007f),     # strlen == 6 -> never
    (0x17aca0, 0x0c000000 | SPRINTF >> 2, 'save_nick'),
    (0x17ad80, 0x0c000000 | STRCPY >> 2, 'copy_nick'),
    (0x179cd4, 0x24020053, 'fix_f'), (0x179cd8, 0xa0820000, 0),
    (0x17acdc, 0x24020053, 'fix_f'), (0x17ace0, 0xa0820000, 0),
]


def _jal(target):
    return 0x0c000000 | (target & 0x0fffffff) >> 2


def _hi_lo(addr):
    return ((addr + 0x8000) >> 16) & 0xffff, addr & 0xffff


def _routines(base, nick):
    """MIPS for the routines, assembled at base; nick = a 64-byte buffer for the nickname.
    ({label: address}, bytes)."""
    hi, lo = _hi_lo(nick)
    save_nick = [                   # at the sprintf (t3 = the nickname): copy it now, then sprintf
        0x3c010000 | hi,            # 0 lui at, hi(nick)
        0x24210000 | lo,            # 1 addiu at, at, lo(nick)
        0x01601825,                 # 2 or v1, t3, zero
        0x00000000,                 # 3 nop
        0x90620000,                 # 4 loop: lbu v0, 0(v1)
        0xa0220000,                 # 5 sb v0, 0(at)
        0x24630001,                 # 6 addiu v1, v1, 1
        0x1440fffc,                 # 7 bnez v0, loop (-4 -> 4)
        0x24210001,                 # 8 addiu at, at, 1 (delay slot)
        0x08000000 | SPRINTF >> 2,  # 9 j sprintf (returns to the caller)
        0x00000000,                 # 10
    ]
    copy_nick = [                   # at strcpy(row 1, row 3): then the nickname into row 1
        0x27bdffe0,                 # addiu sp, sp, -32
        0xffbf0000,                 # sd ra, 0(sp)
        0x7fb00010,                 # sq s0, 16(sp)  (the EE's registers are 128-bit)
        0x00808025,                 # or s0, a0, zero
        _jal(STRCPY),               # the game's copy: row 1 = 5 full-width stats, 18 bytes
        0x00000000,
        0x24022020,                 # addiu v0, zero, 0x2020
        0xa6020000 | NICKNAME_AT - 2,   # sh v0, 18(s0): two spaces where its NUL was
        0x26040000 | NICKNAME_AT,   # addiu a0, s0, 20
        0x3c050000 | hi,            # lui a1, hi(nick)
        _jal(STRCPY),
        0x24a50000 | lo,            # addiu a1, a1, lo(nick) (delay slot)
        0xdfbf0000,                 # ld ra, 0(sp)
        0x7bb00010,                 # lq s0, 16(sp)
        0x03e00008,                 # jr ra
        0x27bd0020,                 # addiu sp, sp, 32
    ]
    # fix_f(a0 -> 'F'): leaf, v0/v1 only, a0 kept (the loop passes it on)
    fix_f = [
        0x90830001,                 # 0  lbu v1, 1(a0)
        0x10600007,                 # 1  beqz v1, prev (+7 -> 9)
        0x00000000,                 # 2
        0x24020020,                 # 3  addiu v0, zero, 0x20
        0x10620005,                 # 4  beq v1, v0, prev
        0x00000000,                 # 5
        0x28620081,                 # 6  slti v0, v1, 0x81  (full-width lead bytes 0x81-0x9f, 0xe0-)
        0x1440000d,                 # 7  bnez v0, ret (+13 -> 21)
        0x00000000,                 # 8
        0x9083ffff,                 # 9  prev: lbu v1, -1(a0)
        0x10600007,                 # 10 beqz v1, set (+7 -> 18)
        0x00000000,                 # 11
        0x24020020,                 # 12 addiu v0, zero, 0x20
        0x10620004,                 # 13 beq v1, v0, set (+4 -> 18)
        0x00000000,                 # 14
        0x24020040,                 # 15 addiu v0, zero, 0x40  (second byte of 　)
        0x14620003,                 # 16 bne v1, v0, ret
        0x00000000,                 # 17
        0x24020053,                 # 18 set: addiu v0, zero, 'S'
        0xa0820000,                 # 19 sb v0, 0(a0)
        0x03e00008,                 # 20 ret: jr ra
        0x00000000,                 # 21
    ]
    # branch offsets are counted from the delay slot: target = pc + 4 + 4 * offset
    fix_f[1] = 0x10600000 | (9 - 2)
    fix_f[4] = 0x10620000 | (9 - 5)
    fix_f[7] = 0x14400000 | (20 - 8)
    fix_f[10] = 0x10600000 | (18 - 11)
    fix_f[13] = 0x10620000 | (18 - 14)
    fix_f[16] = 0x14620000 | (20 - 17)
    code = save_nick + copy_nick + fix_f
    labels = {'save_nick': base, 'copy_nick': base + 4 * len(save_nick),
              'fix_f': base + 4 * (len(save_nick) + len(copy_nick))}
    return labels, struct.pack(f'<{len(code)}I', *code)


def _u32(exe, a):
    return struct.unpack_from('<I', exe, exefile.off(a))[0]


def step(path, files):
    exe = files.get(EXE)
    for a, old, new in STRINGS:
        o = exefile.off(a)
        ob, nb = old.encode('cp932'), new.encode('cp932')
        if exe[o:o + len(ob) + 1] != ob + b'\0':
            raise SystemExit(f'infopage: the format at {a:#x} is not {old!r}')
        exe[o:o + len(ob) + 1] = nb + bytes(len(ob) + 1 - len(nb))
    moved = 0
    for table, n in LAYOUTS:
        for i in range(n):
            o = exefile.off(table) + 24 * i
            w, h, dx, dy, u, v = struct.unpack_from('<6H', exe, o + 8)
            key = (u, v, w) if (u, v, w) in SPRITES else (u, v)
            if key in SPRITES:
                nu, nv, nw = SPRITES[key]
                struct.pack_into('<6H', exe, o + 8, nw, h, dx, dy, nu, nv)
                moved += 1
    if moved != 10:
        raise SystemExit(f'infopage: {moved} sprites matched, expected 10 (5, 4 coach, 1 page 2)')
    placed = 0
    for table in DEST_TABLES:
        n = dict(LAYOUTS)[table]
        for i in range(n):
            o = exefile.off(table) + 24 * i + 12
            dx, dy = struct.unpack_from('<2H', exe, o)
            if (dx, dy) in DESTS:
                struct.pack_into('<H', exe, o, DESTS[(dx, dy)])
                placed += 1
    if placed != 11:
        raise SystemExit(f'infopage: {placed} sprites moved on screen, expected 11 (6, 4 coach, 1)')
    for a, old, _ in PATCHES:
        if _u32(exe, a) != old:
            raise SystemExit(f'infopage: the instruction at {a:#x} is not {old:#010x}')
    exe, nick = exefile.alloc(exe, bytes(64))
    _, code = _routines(0, nick)            # position independent but for `nick`
    exe, base = exefile.alloc(exe, code)
    labels, code2 = _routines(base, nick)
    assert code2 == code
    for a, _, new in PATCHES:
        word = _jal(labels[new]) if isinstance(new, str) else new
        struct.pack_into('<I', exe, exefile.off(a), word)
    files.put(EXE, exe)
    print(f'infopage: formats, {moved} sprites, routines at {base:#x}')
