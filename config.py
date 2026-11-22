# HamPiTRC configuration
# Values for this station. What each radio is lives in radio_profiles.py.

# Radio used on the very first start. Afterwards Bank 9 (keys 1 and 2)
# switches radios and the choice is remembered in ~/.config/hampitrc/prefs.json.
# One of: 'ic705', 'ic7300', 'ic7100'
RADIO_PROFILE   = 'ic705'

# Serial port per radio. Leave a radio out to use its profile default
# (IC-705 /dev/ttyACM0, IC-7300 and IC-7100 /dev/ttyUSB0). With more than one
# radio connected, the stable names under /dev/serial/by-id/ are safer.
SERIAL_PORTS = {
    'ic705': '/dev/ttyACM0',
}

# Keypad: a substring of the input device name (python -m evdev.evtest lists
# them). Among matching devices, one with numeric keypad keys is taken.
# Empty string: the first device that has numeric keypad keys.
KEYBOARD_NAME   = 'HCT'
# Take the keypad exclusively, so key presses do not also reach a desktop or
# console on the same Raspberry Pi.
KEYBOARD_GRAB   = True

AUDIO_NAME      = 'Device'        # USB audio adapter, substring of ALSA card name
HDMI_NAME       = 'vc4hdmi0'      # Fallback: HDMI audio device name
AUDIO_DEVICE    = 'plughw:0,0'    # Last fallback
PIPER_MODEL     = '/home/pi/piper-voices/en_US-lessac-medium.onnx'
VERSION         = '0.8.0-dev'
CALLSIGN        = 'LX1WJ'
