# SwitchMorse - Morse code keyboard and mouse for the Adafruit TRRS Trinkey.
# The program is in sm_main.mpy, sm_map.mpy and sm_hid.mpy (made from
# ../firmware by build_device.py); the codes are in map.bin; settings in config.py.
import gc
gc.collect()
import sm_main
sm_main.run()
