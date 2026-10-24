# SwitchMorse build_device.py - makes everything in device/ that is built:
#   map.bin       from map/morse_map.py   (map/build_map.py)
#   sm_*.mpy      from firmware/sm_*.py   (precompiled with mpy-cross)
#
#   python tools/build_device.py [--mpy-cross PATH]
#
# Precompiled .mpy files load without being compiled on the Trinkey. Compiling
# at start-up is what ran the MorseKey firmware out of memory on this board.
# mpy-cross must match the CircuitPython version on the Trinkey (9.x or 10.x):
# download Adafruit's mpy-cross for that version and put it in tools/mpy-cross/, or pass
# its path with --mpy-cross.
import glob
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def find_mpy_cross():
    if "--mpy-cross" in sys.argv:
        return sys.argv[sys.argv.index("--mpy-cross") + 1]
    found = sorted(glob.glob(os.path.join(ROOT, "tools", "mpy-cross", "mpy-cross*.exe")))
    return found[-1] if found else "mpy-cross"


def main():
    r = subprocess.run([sys.executable, os.path.join(ROOT, "map", "build_map.py")])
    if r.returncode:
        return r.returncode
    mc = find_mpy_cross()
    ver = subprocess.run([mc, "--version"], capture_output=True, text=True)
    print("mpy-cross:", mc, "-", ver.stdout.strip())
    if "CircuitPython" not in ver.stdout:
        print("NOTE: this is not CircuitPython's mpy-cross - the .mpy files may "
              "not load on the Trinkey. Get Adafruit's mpy-cross for its version.")
    for src in sorted(glob.glob(os.path.join(ROOT, "firmware", "sm_*.py"))):
        out = os.path.join(ROOT, "device", os.path.basename(src)[:-3] + ".mpy")
        r = subprocess.run([mc, "-o", out, src])
        if r.returncode:
            return r.returncode
        print("  %-12s %5d bytes" % (os.path.basename(out), os.path.getsize(out)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
