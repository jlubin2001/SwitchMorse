# SwitchMorse sm_hid - raw USB HID reports (no adafruit_hid library: it costs
# several KB of the Trinkey's memory). A key is pressed and released in one call,
# so nothing is ever left held down.
import usb_hid

kb = None
mouse = None
media = None
for _d in usb_hid.devices:
    if _d.usage_page == 1 and _d.usage == 6:
        kb = _d
    elif _d.usage_page == 1 and _d.usage == 2:
        mouse = _d
    elif _d.usage_page == 12 and _d.usage == 1:
        media = _d

_kr = bytearray(8)      # modifiers, reserved, 6 keys
_cr = bytearray(2)      # media usage id
_zero8 = bytes(8)
_zero2 = bytes(2)
_zero4 = bytes(4)


def _send(dev, rep):
    # The computer may be asleep or not listening yet: never crash on that.
    try:
        dev.send_report(rep)
        return True
    except Exception:
        return False


def key(mods, a, b, c):
    if kb is None:
        return False
    _kr[0] = mods
    _kr[2] = a
    _kr[3] = b
    _kr[4] = c
    ok = _send(kb, _kr)
    _send(kb, _zero8)
    return ok


def consumer(code):
    if media is None:
        return False
    _cr[0] = code & 0xFF
    _cr[1] = code >> 8
    ok = _send(media, _cr)
    _send(media, _zero2)
    return ok


def release_all():
    if kb is not None:
        _send(kb, _zero8)
    if media is not None:
        _send(media, _zero2)
    if mouse is not None:
        _send(mouse, _zero4)
