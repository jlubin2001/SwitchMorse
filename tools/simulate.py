# SwitchMorse simulate.py - runs the real firmware (firmware/*.py) on the PC with
# pretend switches, so the decoding can be tested without a Trinkey.
#
#   python tools/simulate.py
#
# A script of presses is played through fake board/digitalio/usb_hid modules;
# every USB report and status line is recorded and checked.
import os
import sys
import types

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Done(Exception):
    pass


class Clock:
    t = 0
    end = 0

    def ticks_ms(self):
        Clock.t += 1                        # each read moves time on 1 ms
        if Clock.t > Clock.end:
            raise Done()
        return Clock.t & ((1 << 29) - 1)


PRESSES = []    # (start ms, end ms, "dot" | "dash")


class Pin:
    def __init__(self, name):
        self.name = name

    def switch_to_output(self, value=False):
        pass

    def switch_to_input(self, pull=None):
        pass

    @property
    def value(self):
        want = {"TIP": "dot", "SLEEVE": "dash"}.get(self.name)
        for a, b, which in PRESSES:
            if which == want and a <= Clock.t < b:
                return False                # pressed = pulled low
        return True


class Dev:
    def __init__(self, page, usage, name):
        self.usage_page, self.usage, self.name = page, usage, name

    def send_report(self, rep):
        REPORTS.append((self.name, bytes(rep)))


REPORTS = []


def install_fakes():
    board = types.ModuleType("board")
    for n in ("TIP", "RING_1", "RING_2", "SLEEVE", "NEOPIXEL"):
        setattr(board, n, n)
    dio = types.ModuleType("digitalio")
    dio.DigitalInOut = Pin
    dio.Pull = types.SimpleNamespace(UP=1)
    dio.Direction = types.SimpleNamespace(OUTPUT=1)
    sup = types.ModuleType("supervisor")
    sup.ticks_ms = Clock().ticks_ms
    npw = types.ModuleType("neopixel_write")
    npw.neopixel_write = lambda pin, buf: None
    hid = types.ModuleType("usb_hid")
    hid.devices = [Dev(1, 6, "kb"), Dev(1, 2, "mouse"), Dev(12, 1, "media")]
    gc = types.ModuleType("gc")
    gc.collect = lambda: None
    gc.mem_free = lambda: 0
    sys.modules.update({"board": board, "digitalio": dio, "supervisor": sup,
                        "neopixel_write": npw, "usb_hid": hid, "gc": gc})
    sys.path[:0] = [os.path.join(ROOT, "firmware"), os.path.join(ROOT, "device")]


def morse(code, start, unit=120, gap=120):
    """Add presses for a code like '.-' starting at `start`; returns end time."""
    t = start
    for ch in code:
        PRESSES.append((t, t + unit, "dot" if ch == "." else "dash"))
        t += unit + gap
    return t


def typed():
    """The key reports turned back into what was typed."""
    import hid_names
    rev = {v: k for k, v in hid_names.US_CHARS.items()}
    out = []
    for dev, rep in REPORTS:
        if dev != "kb" or rep == bytes(8):
            continue
        mods, keys = rep[0], [k for k in rep[2:] if k]
        shift = bool(mods & 0x22)
        other = mods & ~0x22
        if len(keys) == 1 and not other and (shift, keys[0]) in rev:
            out.append(rev[(shift, keys[0])])
        else:
            out.append("<%02x:%s>" % (mods, ",".join("%02x" % k for k in keys)))
    return "".join(out)


def main():
    sys.path.insert(0, os.path.join(ROOT, "map"))
    install_fakes()
    import config
    config.ACCEPT_DELAY = 0.3
    t = 100
    word_gap = 400                      # > accept delay
    # "hi" : h = ....  i = ..
    for code in ("....", ".."):
        t = morse(code, t) + word_gap
    # Space ..--
    t = morse("..--", t) + word_gap
    # Ctrl (sticky) -.-. then c (---.) -> Ctrl+C
    t = morse("-.-.", t) + word_gap
    t = morse("---.", t) + word_gap
    # Shift (sticky) --...- then a -> 'A'
    t = morse("--...-", t) + word_gap
    t = morse(".-", t) + word_gap
    # '?' -.----
    t = morse("-.----", t) + word_gap
    # repeat ..-..
    t = morse("..-..", t) + word_gap
    # unknown code .-.-.-.- is releaseall (g0) ; try an unused 7-symbol code
    t = morse(".-.-.-.", t) + word_gap
    # pause -.-.-.-.  then 'e' (ignored)  then pause again  then 'e'
    t = morse("-.-.-.-.", t) + word_gap
    t = morse(".", t) + word_gap
    t = morse("-.-.-.-.", t) + word_gap
    t = morse(".", t) + word_gap
    # Chattery dash: one press with 5 ms drop-outs must still be ONE dash (t)
    a = t
    PRESSES.extend([(a, a + 40, "dash"), (a + 45, a + 90, "dash"),
                    (a + 100, a + 150, "dash")])
    t = a + 150 + word_gap
    # Long hold (1.2 s) = next group, never a symbol; then Enter .-.-
    PRESSES.append((t, t + 1200, "dot"))
    t += 1200 + word_gap
    t = morse(".-.-", t) + word_gap
    Clock.end = t + 500

    import io
    from contextlib import redirect_stdout
    buf = io.StringIO()
    import sm_main
    sm_main.MAP_PATH = os.path.join(ROOT, "device", "map.bin")
    try:
        with redirect_stdout(buf):
            sm_main.run()
    except Done:
        pass
    lines = [l for l in buf.getvalue().splitlines() if l.startswith("~SM")]
    got = typed()
    want = "hi <01:06>A??e" + "t" + "\n"
    print("typed :", repr(got))
    print("wanted:", repr(want))
    actions = []
    for l in lines:
        a = l.split("\t")[3]
        if not actions or actions[-1] != a:
            actions.append(a)
    print("actions shown:", actions)
    print("PASS" if got == want else "FAIL")
    return 0 if got == want else 1


if __name__ == "__main__":
    sys.exit(main())
