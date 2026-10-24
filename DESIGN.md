# SwitchMorse — how it works

The Trinkey decodes the Morse itself and is a real USB HID keyboard, so it
needs no software on the computer and works on the Windows sign-in screen and
on any computer.

## Fitting in the Trinkey

The TRRS Trinkey's SAMD21 leaves about 17 KB for Python. Earlier firmware on
this board ran out of memory again and again, mostly while CircuitPython
compiled `.py` files at start-up. So:

1. **Precompiled `.mpy` files** (`tools/build_device.py` with Adafruit's
   `mpy-cross` for the matching CircuitPython version) — nothing is compiled
   on the board.
2. **The map stays on flash.** `map/build_map.py` turns an AeroMorse-style
   `morse_map.py` into `device/map.bin`: an index by group and code length,
   then 8-byte entries sorted by pattern, then labels. The firmware reads one
   entry when a code is accepted instead of holding dictionaries in memory.
3. **No adafruit_hid library:** `sm_hid.py` sends raw keyboard / media
   reports. Every key is pressed and released in one call, so nothing stays
   held down.
4. **Whole-millisecond timing** from `supervisor.ticks_ms()` (wraps at 2^29):
   `time.monotonic()` loses precision after hours on this chip.

Result on CircuitPython 10.2.1: about 8.9 KB free after start-up.

## Decoding (`firmware/sm_main.py`)

- Switch debounce: a press counts at once; a release only after `DEBOUNCE_MS`
  of quiet (bridges a chattery contact).
- Each release adds a dot or dash; `ACCEPT_DELAY` of idle finishes the code;
  a press held `LONG_PRESS` goes to the next group.
- Lookup: Group 0 first (works in every group), then the current group.
- Sticky modifiers, repeat, pause, release-all.
- Optional status lines on the USB serial log (`~SM<tab>group<tab>buffer<tab>
  action<tab>status`) for a feedback window on the PC.

## Lesson learned

`usb_hid.enable(..., boot_device=1)` (a keyboard that works in the BIOS) needs
the keyboard to be USB interface #0, which it is not while the CIRCUITPY drive
and serial port are on: after the next replug the board starts in **safe mode**
and runs nothing. A `try/except` doesn't catch it. So `boot.py` doesn't use it.

## Not done yet

Mouse group, Macros group, a PC feedback window, and testing with real
switches. SwitchMorse Windows (decoding on the PC) covers those.
