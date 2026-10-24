# SwitchMorse sm_main - the main loop: read the two switches, build the dots and
# dashes, look the code up in map.bin when the user pauses, send it as keys.
# Times are whole milliseconds from supervisor.ticks_ms(): time.monotonic() on
# the SAMD21 loses precision after a few hours, and this device runs for days.
import board
import digitalio
import gc
import supervisor
from neopixel_write import neopixel_write
import config
import sm_hid
import sm_map

VERSION = "0.1"
MAP_PATH = "/map.bin"
_M = (1 << 29) - 1              # ticks_ms() wraps at 2**29
IDLE = 2                        # switch state: 0 = dot held, 1 = dash held

T_KEY, T_MOD, T_GROUP, T_CONSUMER, T_CMD = 1, 2, 3, 4, 5
C_REPEAT, C_PAUSE, C_RELEASE = 1, 2, 3
GROUP_NAMES = ("BASE", "KEYBOARD", "MOUSE", "MACRO", "SCANNING",
               "MEDIA", "GROUP 6", "GROUP 7", "GROUP 8", "SWITCH")
MOD_NAMES = ("Ctrl", "Shift", "Alt", "Win", "RCtrl", "RShift", "RAlt", "RWin")
# Light colours (red, green, blue) per group; index 0 is unused
GROUP_RGB = ((0, 0, 0), (0, 40, 0), (0, 0, 40), (40, 0, 40), (40, 20, 0),
             (0, 30, 30), (30, 30, 0), (30, 0, 15), (15, 0, 30), (40, 40, 40))
PRESS_RGB = (30, 30, 30)
PAUSED_RGB = (40, 0, 0)
ERROR_RGB = (60, 10, 0)

_AD = int(config.ACCEPT_DELAY * 1000)
_LP = int(config.LONG_PRESS * 1000)
_LPC = config.LONG_PRESS_CYCLES_GROUP
_DEB = config.DEBOUNCE_MS
_PC = config.PC_DISPLAY
_BRIGHT = min(1.0, max(0.05, config.PIXEL_BRIGHTNESS))

# -- hardware -----------------------------------------------------------------
_gnd = digitalio.DigitalInOut(getattr(board, config.GROUND_PIN))
_gnd.switch_to_output(value=False)
_dot = digitalio.DigitalInOut(getattr(board, config.DOT_PIN))
_dot.switch_to_input(pull=digitalio.Pull.UP)
_dash = digitalio.DigitalInOut(getattr(board, config.DASH_PIN))
_dash.switch_to_input(pull=digitalio.Pull.UP)
if config.SWAP_SWITCHES:
    _dot, _dash = _dash, _dot

_px_pin = digitalio.DigitalInOut(board.NEOPIXEL)
_px_pin.direction = digitalio.Direction.OUTPUT
_px = bytearray(3)

# -- state --------------------------------------------------------------------
group = config.START_GROUP
armed = 0               # sticky modifier bits waiting for the next key
paused = False
last = None             # last repeatable entry (bytes), for "repeat"
action = " "            # last action, for the Display window
_state = IDLE
_press_at = 0           # debounce: last time a switch read as pressed
_flash_until = 0
_status_last = None
_status_t = 0


def _now():
    return supervisor.ticks_ms()


def _since(t):
    return (supervisor.ticks_ms() - t) & _M


def _pixel(rgb):
    _px[0] = int(rgb[1] * _BRIGHT)      # the NeoPixel wants green, red, blue
    _px[1] = int(rgb[0] * _BRIGHT)
    _px[2] = int(rgb[2] * _BRIGHT)
    neopixel_write(_px_pin, _px)


def _rest_pixel():
    _pixel(PAUSED_RGB if paused else GROUP_RGB[group])


def _flash(rgb, ms):
    global _flash_until
    _pixel(rgb)
    _flash_until = (_now() + ms) & _M or 1


def _read():
    # MorseKey's hold-filter: a press counts at once; a release only after the
    # line has been quiet for DEBOUNCE_MS. Bridges a chattery switch contact.
    global _press_at
    raw = 0 if not _dot.value else (1 if not _dash.value else IDLE)
    if raw != IDLE:
        _press_at = _now()
        return raw
    if _since(_press_at) >= _DEB:
        return IDLE
    return _state


def _code_str(n, p):
    s = ""
    for i in range(n - 1, -1, -1):
        s += "-" if (p >> i) & 1 else "."
    return s


def status(buf):
    """One line for the SwitchMorse Display window:
    ~SM<tab>group<tab>dots and dashes<tab>last action<tab>armed keys / paused"""
    global _status_last, _status_t
    if not _PC:
        return
    mods = ""
    for i in range(8):
        if armed & (1 << i):
            mods += MOD_NAMES[i] + " "
    if paused:
        mods = "PAUSED " + mods
    key = (group, buf, action, mods)
    if key == _status_last and _since(_status_t) < 2000:
        return
    _status_last = key
    _status_t = _now()
    print("~SM\t[ " + GROUP_NAMES[group] + " ]\t" + (buf or " ") + "\t"
          + action + "\t" + (mods.strip() or " "))


def _cycle_group():
    global group, action
    gs = sm_map.groups
    if group in gs and len(gs) > 1:
        group = gs[(gs.index(group) + 1) % len(gs)]
    elif gs:
        group = gs[0]
    action = "Group %d %s" % (group, GROUP_NAMES[group].title())
    _rest_pixel()


def _do(e):
    """Carry out one map entry."""
    global armed, group, paused, last, action
    t = e[1]
    if t == T_KEY:
        sm_hid.key(e[2] | armed, e[3], e[4], e[5])
        last = bytes(e)
        if armed:
            pre = ""
            for i in range(8):
                if armed & (1 << i):
                    pre += MOD_NAMES[i] + "+"
            armed = 0
            action = pre + sm_map.label(e)
            return
    elif t == T_MOD:
        armed ^= e[2]
    elif t == T_GROUP:
        group = e[2]
    elif t == T_CONSUMER:
        sm_hid.consumer(e[2] | (e[3] << 8))
        last = bytes(e)
    elif t == T_CMD:
        c = e[2]
        if c == C_REPEAT:
            if last is not None:
                _do(last)
                action = "Repeat " + sm_map.label(last)
            else:
                action = "Repeat (nothing yet)"
            return
        if c == C_PAUSE:
            paused = not paused
            sm_hid.release_all()
            armed = 0
            action = "Paused" if paused else "Started again"
            return
        if c == C_RELEASE:
            sm_hid.release_all()
            armed = 0
    action = sm_map.label(e)


def _accept(n, p):
    global action
    if n > 8:
        action = "? too long"
        _flash(ERROR_RGB, 300)
        return
    e = sm_map.find(0, n, p)
    if e is None and group:
        e = sm_map.find(group, n, p)
    if e is None:
        action = "? " + _code_str(n, p)
        _flash(ERROR_RGB, 300)
        return
    if paused and not (e[1] == T_CMD and e[2] == C_PAUSE):
        action = "(paused) " + _code_str(n, p)
        _flash(ERROR_RGB, 150)
        return
    _do(e)
    _rest_pixel()


def _blink_forever(msg):
    print("SwitchMorse:", msg)
    on = False
    while True:
        on = not on
        _pixel(ERROR_RGB if on else (0, 0, 0))
        t = _now()
        while _since(t) < 400:
            pass


def run():
    global _state, _flash_until, group
    try:
        sm_map.open_map(MAP_PATH)
    except Exception as ex:
        _blink_forever("can't read map.bin - %s" % ex)
    if group not in sm_map.groups:
        group = sm_map.groups[0] if sm_map.groups else 0
    gc.collect()
    print("SwitchMorse v%s | groups %s | free memory %d bytes"
          % (VERSION, sm_map.groups, gc.mem_free()))
    _rest_pixel()

    pend = 0            # the dots (0) and dashes (1) so far, oldest first
    n = 0               # how many
    t_trans = _now()    # last time a switch went down or up
    t_down = 0          # when the current press started
    hinted = False      # long-press colour shown for this press
    status("")
    while True:
        s = _read()
        if s != _state:
            now = _now()
            if _state != IDLE:                      # a press just ended
                if _LPC and ((now - t_down) & _M) >= _LP:
                    _cycle_group()
                    pend = n = 0
                else:
                    pend = (pend << 1) | _state
                    n += 1
            if s != IDLE:                           # a press just started
                t_down = now
                hinted = False
                _pixel(PRESS_RGB)
            else:
                _rest_pixel()
            t_trans = now
            _state = s
            status(_code_str(n, pend) if n <= 8 else "(too long)")
        elif _state == IDLE:
            if n and _since(t_trans) >= _AD:
                _accept(n, pend)
                pend = n = 0
                status("")
        elif _LPC and not hinted and _since(t_down) >= _LP:
            # Held long enough: show the next group's colour - let go to switch.
            hinted = True
            gs = sm_map.groups
            if len(gs) > 1 and group in gs:
                _pixel(GROUP_RGB[gs[(gs.index(group) + 1) % len(gs)]])
            else:
                _pixel(GROUP_RGB[group])
        if _flash_until and _since(_flash_until) < (1 << 28):
            _flash_until = 0
            if _state == IDLE:
                _rest_pixel()
        if _PC and _since(_status_t) >= 2000:     # so a window opened later catches up
            status(_code_str(n, pend) if n <= 8 else "(too long)")
