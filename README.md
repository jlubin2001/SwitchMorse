# SwitchMorse

A Morse code keyboard on the **[Adafruit TRRS Trinkey](https://www.adafruit.com/product/5954)** (#5954): plug in two
assistive switches (dot and dash), and the Trinkey types — as an ordinary USB
keyboard, so it works anywhere a keyboard does, with no software on the
computer (including the Windows sign-in screen).

> **Status: early and experimental (v0.1).** Only the Keyboard group is done.
> The firmware starts on the Trinkey (CircuitPython 10.2.1, about 8.9 KB of
> memory left over) and passes a full simulation on a PC, but it has not yet
> been tried typing with real switches. For a finished, tested way to use two
> switches with Windows, see **[SwitchMorse Windows](https://github.com/jlubin2001/SwitchMorse-Windows)**
> (the same codes, decoded by a program on the PC).

The codes are the same as **[AeroMorse](https://github.com/jlubin2001/AeroMorse)**
(Groups 0 and 1).

## What you need

- [Adafruit TRRS Trinkey](https://www.adafruit.com/product/5954) (#5954) with CircuitPython 10.2.1.
- Two switches with mono 3.5 mm plugs and a TRRS splitter: dot = TIP,
  dash = SLEEVE, ground = RING_2. (`tools/switchmorse_pin_monitor.py` shows
  which contact each switch lands on — copy it to the Trinkey as `code.py`.)

## Install

1. Copy everything in **`device\`** to the Trinkey's **CIRCUITPY** drive
   (`boot.py`, `code.py`, `config.py`, `map.bin`, `sm_*.mpy`).
2. Unplug and replug the Trinkey (`boot.py` changes need it).
3. The light shows green (Keyboard group); it turns white while a switch is held.

## Using it

| Code | Does |
|---|---|
| `.-` `-...` … | letters, numbers, punctuation, keys (AeroMorse Group 1) |
| `-.-.` | Ctrl (sticky: goes with the next key); `--...-` Shift, `--.--` Alt, `.--.--` Win |
| `..-..` | repeat the last key |
| `-.-.-.-.` | pause / start again (light turns red) |
| `.-.-.-.-` | release everything |
| hold 1 second | next group (only one group so far) |

Light: green = Keyboard, white = switch held, orange flash = unknown code,
red = paused.

## Changing it

- **Settings:** `config.py` on the CIRCUITPY drive (switch pins, timing,
  brightness). Save, and the Trinkey restarts.
- **Codes:** edit `map/morse_map.py` (AeroMorse format), then on the PC run
  `python tools/build_device.py` and copy the new `device/map.bin`.
- **Firmware:** `firmware/sm_*.py`, precompiled to `device/sm_*.mpy` by
  `tools/build_device.py`. It needs Adafruit's `mpy-cross` for the Trinkey's
  CircuitPython version — download it into `tools/mpy-cross/`.
- **Test without hardware:** `python tools/simulate.py` runs the real firmware
  on the PC with pretend switches.

See `DESIGN.md` for how it works and why.

## Licence

MIT — see `LICENSE`.
