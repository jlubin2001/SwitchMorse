# SwitchMorse config.py - settings you can change. Save, and the device restarts.
# Names match AeroMorse config.py where they mean the same thing.

# -- Switches -----------------------------------------------------------------
# Jack contacts on the Trinkey: "TIP", "RING_1", "RING_2", "SLEEVE".
# These are the MorseKey wiring (splitter, RING_2 = ground). If dot and dash
# come out the wrong way round, set SWAP_SWITCHES = True.
DOT_PIN    = "TIP"
DASH_PIN   = "SLEEVE"
GROUND_PIN = "RING_2"
SWAP_SWITCHES = False
DEBOUNCE_MS = 15        # a release only counts after this many ms of quiet.
                        # Raise it if one press types two symbols.

# -- Timing (seconds) -----------------------------------------------------------
ACCEPT_DELAY = 0.3      # pause after the last symbol before the code is sent
LONG_PRESS   = 1.0      # hold a switch this long, then let go = next group
LONG_PRESS_CYCLES_GROUP = True

# -- Groups -------------------------------------------------------------------
START_GROUP = 1         # 1 = Keyboard

# -- Feedback -----------------------------------------------------------------
PC_DISPLAY = True       # send status lines for the SwitchMorse Display window
PIXEL_BRIGHTNESS = 0.5  # the light on the Trinkey: 0.1 (dim) to 1.0
