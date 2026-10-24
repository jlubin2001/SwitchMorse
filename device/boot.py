# SwitchMorse boot.py - Adafruit TRRS Trinkey (#5954)
# Runs once at power-up, before the computer sees the device.
# Turns on the USB keyboard, mouse and media keys, and names the device.
#
# No boot_device=1 (BIOS keyboard): it needs the keyboard to be USB interface
# #0, which it isn't while the serial port and drive are on - the Trinkey then
# starts in safe mode and runs nothing. Windows sign-in works without it.
import usb_hid

usb_hid.enable((usb_hid.Device.KEYBOARD,
                usb_hid.Device.MOUSE,
                usb_hid.Device.CONSUMER_CONTROL))

try:
    import supervisor
    supervisor.set_usb_identification("Adafruit", "SwitchMorse")
except Exception:
    pass
