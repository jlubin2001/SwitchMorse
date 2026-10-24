# SwitchMorse build_map.py - turns morse_map.py into the files the device and
# the Display window read. Runs on the PC (Python 3), never on the Trinkey.
#
#   python build_map.py            -> ../device/map.bin  and  map.json
#   python build_map.py --check    -> only checks the map, writes nothing
#
# Why: the Trinkey (SAMD21) has about 17 KB of memory for Python. A map held as
# dictionaries does not fit. map.bin stays on the flash drive and the device
# reads one small piece of it each time a code is accepted.
#
# map.bin layout (all numbers little-endian):
#   0   4  b"SMAP"
#   4   1  format version (1)
#   5   1  number of groups G
#   6   2  reserved
#   8      index: for each group 0..G-1, for each length 1..8:
#            u16 offset of its first entry, u8 entry count, u8 reserved
#   ...    entries, 8 bytes each, sorted by pattern within a (group, length):
#            u8 pattern, u8 type, u8 a, u8 b, u8 c, u8 d, u16 label offset
#   ...    labels: u8 length + UTF-8 text
#
# Entry types (a b c d):
#   1 KEY       mods bitmask, key1, key2, key3   (0 = no key)
#   2 MOD       modifier bit (sticky: arms for the next key)
#   3 GROUP     group number
#   4 CONSUMER  usage id low, usage id high
#   5 CMD       command id: 1 repeat, 2 pause, 3 releaseall

import json
import os
import struct
import sys
import types

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import hid_names  # noqa: E402

N_GROUPS = 4            # SwitchMorse uses groups 0-3 only
GROUP_NAMES = ["BASE", "KEYBOARD", "MOUSE", "MACRO"]
T_KEY, T_MOD, T_GROUP, T_CONSUMER, T_CMD = 1, 2, 3, 4, 5
COMMANDS = {"repeat": 1, "pause": 2, "releaseall": 3}
CMD_LABELS = {1: "Repeat", 2: "Pause", 3: "Release all"}


class CC:
    """Same marker as AeroMorse: a Consumer Control (media) code."""
    __slots__ = ("code",)

    def __init__(self, code):
        self.code = code


def _cc(name, usage_id):
    return CC(getattr(hid_names.ConsumerControlCode, name, usage_id))


def load_map(path):
    # morse_map.py is written like an AeroMorse map: it imports adafruit_hid.
    # Hand it the PC stand-ins instead of the real library.
    pkg = types.ModuleType("adafruit_hid")
    kc = types.ModuleType("adafruit_hid.keycode")
    kc.Keycode = hid_names.Keycode
    ccc = types.ModuleType("adafruit_hid.consumer_control_code")
    ccc.ConsumerControlCode = hid_names.ConsumerControlCode
    sys.modules.update({"adafruit_hid": pkg, "adafruit_hid.keycode": kc,
                        "adafruit_hid.consumer_control_code": ccc})
    ns = {"__name__": "morse_map", "CC": CC, "_cc": _cc}
    with open(path, encoding="utf-8") as f:
        src = f.read()
    exec(compile(src, path, "exec"), ns)
    return ns["groups"]


def code_str(n, p):
    return "".join("-" if (p >> (n - 1 - i)) & 1 else "." for i in range(n))


def mod_bit(kc):
    return 1 << (kc - 0xE0) if 0xE0 <= kc <= 0xE7 else 0


def key_label(mods, keys):
    parts = [hid_names.MOD_LABELS[i] for i in range(8) if mods & (1 << i)]
    parts += [hid_names.KEY_LABELS.get(k, "Key %d" % k) for k in keys]
    return "+".join(parts)


def convert(value, where, problems):
    """One map value -> (type, (a, b, c, d), label), or None to leave it out."""
    if isinstance(value, str):
        if len(value) == 1:
            if value not in hid_names.US_CHARS:
                problems.append("%s: no US key for %r" % (where, value))
                return None
            shift, k = hid_names.US_CHARS[value]
            label = {" ": "Space", "\n": "Enter", "\t": "Tab"}.get(value, value)
            return T_KEY, (2 if shift else 0, k, 0, 0), label
        words = value.split()
        if len(words) == 2 and words[0] == "group" and words[1].isdigit():
            g = int(words[1])
            if g >= N_GROUPS:
                problems.append("%s: SwitchMorse has no group %d - left out" % (where, g))
                return None
            return T_GROUP, (g, 0, 0, 0), "Group %d %s" % (g, GROUP_NAMES[g].title())
        if value in COMMANDS:
            c = COMMANDS[value]
            return T_CMD, (c, 0, 0, 0), CMD_LABELS[c]
        problems.append("%s: %r is not supported yet - left out" % (where, value))
        return None
    if isinstance(value, int):
        value = (value,)
    if isinstance(value, tuple) and all(isinstance(v, int) for v in value):
        if len(value) == 1 and mod_bit(value[0]):
            b = mod_bit(value[0])
            return T_MOD, (b, 0, 0, 0), hid_names.MOD_LABELS[b.bit_length() - 1]
        mods = 0
        keys = []
        for v in value:
            if mod_bit(v):
                mods |= mod_bit(v)
            else:
                keys.append(v)
        if len(keys) > 3:
            problems.append("%s: more than 3 keys at once - left out" % where)
            return None
        k = keys + [0] * (3 - len(keys))
        return T_KEY, (mods, k[0], k[1], k[2]), key_label(mods, keys)
    if isinstance(value, CC):
        return (T_CONSUMER, (value.code & 0xFF, value.code >> 8, 0, 0),
                "Media %#x" % value.code)
    problems.append("%s: %r is not supported yet - left out" % (where, value))
    return None


def build(groups):
    problems = []
    for g in sorted(groups):
        if g >= N_GROUPS and any(groups[g].values()):
            problems.append("group %d: SwitchMorse has groups 0-%d only - left out"
                            % (g, N_GROUPS - 1))
    table = {}          # (group, length) -> [(pattern, type, data, label)]
    for g in range(N_GROUPS):
        for n in range(1, 9):
            rows = []
            for p, v in sorted(groups.get(g, {}).get(n, {}).items()):
                where = "g%d %s" % (g, code_str(n, p))
                if not 0 <= p < (1 << n):
                    problems.append("%s: pattern 0b%s is longer than %d symbols"
                                    % (where, bin(p)[2:], n))
                    continue
                r = convert(v, where, problems)
                if r:
                    rows.append((p,) + r)
            table[(g, n)] = rows

    # A group command that leads to an empty group would leave the user stuck
    # with nothing to send - leave those out until the group exists.
    filled = {g for g in range(1, N_GROUPS)
              if any(table[(g, n)] for n in range(1, 9))}
    for key, rows in table.items():
        keep = []
        for r in rows:
            if r[1] == T_GROUP and r[2][0] not in filled:
                problems.append("g%d %s: group %d has no codes yet - left out"
                                % (key[0], code_str(key[1], r[0]), r[2][0]))
            else:
                keep.append(r)
        table[key] = keep

    # Group 0 wins over every group: a g0 code hides the same code elsewhere.
    for n in range(1, 9):
        g0 = {r[0] for r in table[(0, n)]}
        for g in range(1, N_GROUPS):
            for r in table[(g, n)]:
                if r[0] in g0:
                    problems.append("g%d %s (%s) is hidden by Group 0"
                                    % (g, code_str(n, r[0]), r[3]))

    # ---- write ----
    labels = bytearray()
    label_at = {}

    def label_off(text):
        if text not in label_at:
            raw = text.encode("utf-8")[:40]
            label_at[text] = len(labels)
            labels.append(len(raw))
            labels.extend(raw)
        return label_at[text]

    index = bytearray()
    entries = bytearray()
    entries_start = 8 + N_GROUPS * 8 * 4
    for g in range(N_GROUPS):
        for n in range(1, 9):
            rows = table[(g, n)]
            index += struct.pack("<HBB", entries_start + len(entries), len(rows), 0)
            for p, t, d, lab in rows:
                entries += struct.pack("<BBBBBBH", p, t, d[0], d[1], d[2], d[3], 0)
    labels_start = entries_start + len(entries)
    # second pass for label offsets (now that the labels area start is known)
    entries = bytearray()
    for g in range(N_GROUPS):
        for n in range(1, 9):
            for p, t, d, lab in table[(g, n)]:
                entries += struct.pack("<BBBBBBH", p, t, d[0], d[1], d[2], d[3],
                                       labels_start + label_off(lab))
    blob = b"SMAP" + bytes([1, N_GROUPS, 0, 0]) + index + entries + labels

    as_json = {"groups": {str(g): {"name": GROUP_NAMES[g], "codes": {
        code_str(n, r[0]): r[3] for n in range(1, 9) for r in table[(g, n)]}}
        for g in range(N_GROUPS)}}
    return blob, as_json, problems


def main():
    check_only = "--check" in sys.argv
    groups = load_map(os.path.join(HERE, "morse_map.py"))
    blob, as_json, problems = build(groups)
    for p in problems:
        print("NOTE:", p)
    count = sum(len(v["codes"]) for v in as_json["groups"].values())
    print("%d codes, map.bin %d bytes" % (count, len(blob)))
    if check_only:
        return
    out = os.path.join(HERE, "..", "device", "map.bin")
    with open(out, "wb") as f:
        f.write(blob)
    with open(os.path.join(HERE, "map.json"), "w", encoding="utf-8") as f:
        json.dump(as_json, f, indent=1, ensure_ascii=False)
    print("wrote", os.path.normpath(out), "and map.json")


if __name__ == "__main__":
    main()
