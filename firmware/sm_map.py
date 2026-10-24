# SwitchMorse sm_map - reads codes from map.bin on the flash drive, one entry at
# a time, so the whole map never has to sit in memory. map.bin is made on the PC
# by map/build_map.py (its top comment describes the layout).

_f = None
_e = bytearray(8)       # the entry found by find(); reused, copy it to keep it
_i = bytearray(4)
groups = ()             # groups 1-9 that have at least one code


def open_map(path="/map.bin"):
    global _f, groups
    _f = open(path, "rb")
    head = _f.read(8)
    if head[:4] != b"SMAP" or head[4] != 1:
        raise ValueError("map.bin is not a SwitchMorse map (run build_map.py)")
    found = []
    for g in range(1, head[5]):
        for n in range(1, 9):
            _f.seek(8 + (g * 8 + n - 1) * 4)
            _f.readinto(_i)
            if _i[2]:
                found.append(g)
                break
    groups = tuple(found)
    return head[5]


def find(g, n, p):
    """The entry for pattern p of length n in group g, or None."""
    if n < 1 or n > 8:
        return None
    _f.seek(8 + (g * 8 + n - 1) * 4)
    _f.readinto(_i)
    _f.seek(_i[0] | (_i[1] << 8))
    for _ in range(_i[2]):
        _f.readinto(_e)
        if _e[0] == p:
            return _e
        if _e[0] > p:       # entries are sorted by pattern
            break
    return None


def label(e):
    _f.seek(e[6] | (e[7] << 8))
    n = _f.read(1)[0]
    return _f.read(n).decode()
