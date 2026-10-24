# SwitchMorse morse_map.py - Phase 1 (Group 0 + Group 1 Keyboard)
# Same codes and same layout as AeroMorse morse_map.py v1.31, so the AeroMorse
# cheat sheet works for these groups.
#
# This file is NOT copied to the Trinkey. After editing it, run build_map.py:
# it checks the map and writes device/map.bin (what the Trinkey reads) and
# map/map.json (for the SwitchMorse Display window).
#
# How a code is written: the 1s and 0s after 0b, read left to right in the order
# you send them. 0 = dot (dot switch), 1 = dash (dash switch).
# Example: g1[4][0b1000] is -... (one dash, three dots), the letter B.
#
# A value can be:
#   a character        'a'  '?'  'A'
#   a key              Keycode.ENTER
#   keys together      Keycode.CONTROL, Keycode.C
#   a sticky modifier  Keycode.LEFT_CONTROL  (arms; applies to the next key)
#   a command          "group 2"  "repeat"  "pause"  "releaseall"
from adafruit_hid.keycode import Keycode

groups = {}

def init_group():
    """Helper to create the length-based dictionary structure"""
    return {1: {}, 2: {}, 3: {}, 4: {}, 5: {}, 6: {}, 7: {}, 8: {}}

############################################
# Begin Group 0
# ALWAYS AVAILABLE (System / Group toggles)
############################################
# Checked before the active group on every lookup - a code here wins in
# every group. All group codes are 8 symbols, too long to send by accident.
#
#   ........  (0 dashes)  -> g1  Keyboard
#   ....----  (4 dashes)  -> g3  Macros              (Phase 3)
#   --------  (8 dashes)  -> g2  Mouse / Shortcuts   (Phase 3)
# SwitchMorse has only groups 0-3; AeroMorse's codes for groups 4-9 are free.

g0 = init_group()

g0[8][0b00000000] = "group 1"   # ........  -> Keyboard
g0[8][0b00001111] = "group 3"   # ....----  -> Macros
g0[8][0b11111111] = "group 2"   # --------  -> Mouse/Shortcuts

# Safety codes (new in SwitchMorse)
g0[8][0b10101010] = "pause"       # -.-.-.-.  stop all output / start again (same code)
g0[8][0b01010101] = "releaseall"  # .-.-.-.-  let go of every key and button

groups[0] = g0

############################################
# Begin Group 1
# KEYBOARD (Letters, Numbers, Punctuation)
############################################
# Two letters deliberately use non-standard patterns to free up
# high-frequency control keys on their original ITU Morse codes:
#   --   (standard M) -> BACKSPACE   M relocated to ----
#   -.-. (standard C) -> LEFT_CTRL   C relocated to ---.

g1 = init_group()

g1[5][0b00010]    = "group 2"   # ...-. -> Switch to Mouse/Shortcuts

# -- Letters ------------------------------------------------------------------
g1[2][0b01]='a'             # .-
g1[4][0b1000]='b'           # -...
g1[4][0b1110]='c'           # ---.   (non-standard; -.-. freed for LEFT_CONTROL)
g1[3][0b100]='d'            # -..
g1[1][0b0]='e'              # .
g1[4][0b0010]='f'           # ..-.
g1[3][0b110]='g'            # --.
g1[4][0b0000]='h'           # ....
g1[2][0b00]='i'             # ..
g1[4][0b0111]='j'           # .---
g1[3][0b101]='k'            # -.-
g1[4][0b0100]='l'           # .-..
g1[4][0b1111]='m'           # ----   (non-standard; -- freed for BACKSPACE)
g1[2][0b10]='n'             # -.
g1[3][0b111]='o'            # ---
g1[4][0b0110]='p'           # .--.
g1[4][0b1101]='q'           # --.-
g1[3][0b010]='r'            # .-.
g1[3][0b000]='s'            # ...
g1[1][0b1]='t'              # -
g1[3][0b001]='u'            # ..-
g1[4][0b0001]='v'           # ...-
g1[3][0b011]='w'            # .--
g1[4][0b1001]='x'           # -..-
g1[4][0b1011]='y'           # -.--
g1[4][0b1100]='z'           # --..

# -- Numbers ------------------------------------------------------------------
g1[5][0b01111]='1'          # .----
g1[5][0b00111]='2'          # ..---
g1[5][0b00011]='3'          # ...--
g1[5][0b00001]='4'          # ....-
g1[5][0b00000]='5'          # .....
g1[5][0b10000]='6'          # -....
g1[5][0b11000]='7'          # --...
g1[5][0b11100]='8'          # ---..
g1[5][0b11110]='9'          # ----.
g1[5][0b11111]='0'          # -----

# -- Punctuation --------------------------------------------------------------
g1[5][0b10001]='+'          # -...-
g1[5][0b01110]='-'          # .---.
g1[5][0b11101]='='          # ---.-
g1[5][0b10011]='*'          # -..--
g1[6][0b010000]='!'         # .-....
g1[6][0b111001]='@'         # ---..-
g1[6][0b001110]='#'         # ..---.
g1[6][0b001111]='$'         # ..----
g1[6][0b000101]='%'         # ...-.-
g1[6][0b100011]='^'         # -...--
g1[6][0b011100]='&'         # .---..
g1[6][0b011111]='.'         # .-----
g1[6][0b100000]=','         # -.....
g1[6][0b011110]=':'         # .----.
g1[6][0b100001]=';'         # -....-
g1[6][0b000111]=')'         # ...---
g1[6][0b111000]='('         # ---...
g1[6][0b100111]=']'         # -..---
g1[6][0b011000]='['         # .--...
g1[5][0b11001]='}'          # --..-
g1[5][0b00110]='{'          # ..--.
g1[6][0b110011]='<'         # --..--
g1[6][0b001100]='>'         # ..--..
g1[6][0b101111]='?'         # -.----
g1[6][0b000011]='/'         # ....--    (forward slash)
g1[6][0b111100]='\\'        # ----..    (backslash)
g1[6][0b000010]='|'         # ....-.
g1[6][0b111101]='_'         # ----.-
g1[6][0b000110]='\"'        # ...--.    (double quote)
g1[6][0b001000]='\''        # ..-...    (single quote)
g1[6][0b110111]='`'         # --.---
g1[6][0b111011]='~'         # ---.--

# -- Function Keys ------------------------------------------------------------
g1[7][0b1101111]=Keycode.F1   # --.---- (--1)
g1[7][0b1100111]=Keycode.F2   # --..--- (--2)
g1[7][0b1100011]=Keycode.F3   # --...-- (--3)
g1[7][0b1100001]=Keycode.F4   # --....- (--4)
g1[7][0b1100000]=Keycode.F5   # --..... (--5)
g1[7][0b1110000]=Keycode.F6   # ---.... (--6)
g1[7][0b1111000]=Keycode.F7   # ----... (--7)
g1[7][0b1111100]=Keycode.F8   # -----.. (--8)
g1[7][0b1111110]=Keycode.F9   # ------. (--9)
g1[7][0b1111111]=Keycode.F10  # ------- (--0)
g1[7][0b0111111]=Keycode.F11  # .------ (1--)
g1[7][0b0011111]=Keycode.F12  # ..----- (2--)

# -- Non-printable keyboard keys ----------------------------------------------
g1[5][0b01001]=Keycode.UP_ARROW      # .-..-    (au)
g1[5][0b01100]=Keycode.DOWN_ARROW    # .--..    (ad)
g1[6][0b010100]=Keycode.LEFT_ARROW   # .-.-..   (al)
g1[5][0b01010]=Keycode.RIGHT_ARROW   # .-.-.    (ar)
g1[7][0b0000000]=Keycode.HOME        # .......  (sh) (7 dots)
g1[7][0b0001000]=Keycode.END         # ...-...  (sb)
g1[6][0b000001]=Keycode.PAGE_UP      # .....-   (su)
g1[6][0b000100]=Keycode.PAGE_DOWN    # ...-..   (sd)
g1[4][0b0101]=Keycode.ENTER          # .-.-
g1[6][0b110000]=Keycode.ESCAPE       # --....   (gs)
g1[6][0b101100]=Keycode.DELETE       # -.--..   (kd)
g1[5][0b10100]=Keycode.INSERT        # -.-..    (ki)
g1[2][0b11]=Keycode.BACKSPACE        # --     (freed from M)
g1[4][0b0011]=Keycode.SPACE          # ..--
g1[7][0b1110010]=Keycode.TAB         # ---..-.  (of)
g1[6][0b111010]=Keycode.SHIFT,Keycode.TAB         # ---.-.  Shift+Tab, reverse tab  (or)

g1[5][0b00100] = "repeat"            # ..-..    repeat

# -- Modifier keys ------------------------------------------------------------
# Sticky: press once to arm, next key fires with the modifier, then it releases.
# Press again while armed to cancel.
g1[4][0b1010]=Keycode.LEFT_CONTROL   # -.-. (freed from C)
g1[6][0b110001]=Keycode.LEFT_SHIFT   # --...-
g1[5][0b11011]=Keycode.LEFT_ALT      # --.--
g1[6][0b011011]=Keycode.LEFT_GUI     # .--.--
g1[6][0b111110]=Keycode.CAPS_LOCK    # -----.
g1[6][0b110100]=Keycode.SCROLL_LOCK  # --.-..
g1[7][0b1110001]=Keycode.KEYPAD_NUMLOCK  # ---...-
g1[6][0b110110]=Keycode.PRINT_SCREEN # --.--.

groups[1] = g1
