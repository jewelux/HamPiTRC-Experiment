# PiHAMTRC configuration
# Keyboard/audio device names used for discovery; radio uses DEVICE_RADIO.

KEYBOARD_NAME   = 'HCT'           # Substring of keyboard device name
RADIO_NAME      = 'ttyACM0'       # IC-705 serial port
AUDIO_NAME      = 'Device'        # USB audio adapter, substring of ALSA card name
HDMI_NAME       = 'vc4hdmi0'      # Fallback: HDMI audio device name

DEVICE_RADIO    = '/dev/ttyACM0'
AUDIO_DEVICE    = 'plughw:0,0'
PIPER_MODEL     = '/home/pi/piper-voices/en_US-lessac-medium.onnx'
VERSION         = '0.7.0'
CALLSIGN        = 'LX1WJ'
