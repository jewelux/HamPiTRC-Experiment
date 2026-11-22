# HamPiTRC main program (spoken name PiHAMTRC)
#
# Reads the USB numeric keypad and hands each press and release to the keypad
# state machine (keypad_input.py). What a key does is in banks.py, how it is
# carried out in ui.py; every radio call goes through radio.py, which checks
# the active profile. Key layout and behaviour follow HamTRC (development).
import evdev, select, sys, time, subprocess
import config
from config import KEYBOARD_NAME, AUDIO_NAME, AUDIO_DEVICE, HDMI_NAME, VERSION, CALLSIGN
import radio
import banks
from keymap import KEY_MAP
from ui import Ui, frequency_words

# --- Discover audio device ---
def _find_audio_card_in_proc(name):
    try:
        with open('/proc/asound/cards', 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except OSError:
        return None

    for line in lines:
        if name in line and '[' in line:
            card_num = line.split('[', 1)[0].strip()
            if card_num.isdigit():
                return 'plughw:' + card_num + ',0'
    return None

def find_audio_device():
    device = _find_audio_card_in_proc(AUDIO_NAME)
    if device:
        return device

    result = subprocess.run(['aplay', '-l'], capture_output=True, text=True)
    for line in result.stdout.splitlines():
        if AUDIO_NAME in line and line.startswith('card'):
            card_num = line.split()[1].rstrip(':')
            return 'plughw:' + card_num + ',0'

    device = _find_audio_card_in_proc(HDMI_NAME)
    if device:
        return device

    for line in result.stdout.splitlines():
        if HDMI_NAME in line and line.startswith('card'):
            card_num = line.split()[1].rstrip(':')
            return 'plughw:' + card_num + ',0'
    return AUDIO_DEVICE

# --- Discover keyboard ---
def _has_keypad_keys(device):
    try:
        keys = device.capabilities().get(evdev.ecodes.EV_KEY, [])
    except (OSError, AttributeError):
        return False
    return evdev.ecodes.KEY_KP0 in keys and evdev.ecodes.KEY_KP9 in keys

def pick_keyboard(devices, name=KEYBOARD_NAME):
    """The keypad among devices: name match first, then numeric keypad keys.

    A keypad usually shows up as several input devices (keyboard, consumer
    control, system control); only the keyboard one has the keypad keys.
    """
    named = [d for d in devices if name and name in d.name]
    for group in (named, devices if not name else []):
        with_keys = [d for d in group if _has_keypad_keys(d)]
        if with_keys:
            return min(with_keys, key=lambda d: d.path)
    # Old rule (0.7.0): name match and a name ending in "Keyboard".
    legacy = [d for d in named if d.name.strip().endswith('Keyboard')]
    if legacy:
        return min(legacy, key=lambda d: d.path)
    return None

def find_keyboard():
    devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
    dev = pick_keyboard(devices)
    if dev is None:
        return None
    print('Keyboard found: ' + dev.path + ' ' + dev.name)
    if getattr(config, 'KEYBOARD_GRAB', True):
        try:
            dev.grab()
        except OSError as e:
            print('Keyboard grab failed: ' + str(e))
    return dev

# --- Main program ---
def now_ms():
    return int(time.monotonic() * 1000)


def startup_announcement(ui):
    profile = radio.current()
    name = profile.spoken
    ui.say('PiHAMTRC ready, version ' + VERSION)
    hz = radio.get_freq()
    mode = radio.get_mode()
    parts = [name + ' connected']
    parts.append(str(mode) if mode else 'mode unavailable')
    parts.append('frequency ' + frequency_words(hz) if hz else 'frequency unavailable')
    ui.say(', '.join(parts))


def main():
    audio = find_audio_device()
    print('Audio device: ' + audio)
    import speech
    speech.AUDIO_DEVICE = audio

    profile = radio.start(getattr(config, 'RADIO_PROFILE', 'ic705'),
                          getattr(config, 'SERIAL_PORTS', {}))
    ui = Ui(speech.Speech(), banks.lookup, radio.load_prefs())
    try:
        radio.connect()
    except Exception as e:
        print(profile.name + ' not found on ' + radio.serial_port() + ': ' + str(e))
        ui.say(profile.spoken + ' not connected')
        speech.wait_idle()
        sys.exit(1)

    startup_announcement(ui)

    dev = find_keyboard()
    if dev is None:
        ui.say('Keyboard not found')
        speech.wait_idle()
        sys.exit(1)

    ui.say('Ready')
    keypad = ui.keypad
    held = set()      # all keys down, for NumLock + Tab

    while True:
        readable, _, _ = select.select([dev.fd], [], [], 0.02)
        if readable:
            for event in dev.read():
                if event.type != evdev.ecodes.EV_KEY:
                    continue
                key_event = evdev.categorize(event)
                code = key_event.keycode
                if isinstance(code, list):
                    code = code[0]
                if key_event.keystate == 1:
                    held.add(code)
                    if code in KEY_MAP:
                        keypad.press(KEY_MAP[code], now_ms())
                elif key_event.keystate == 0:
                    held.discard(code)
                    if code in KEY_MAP:
                        keypad.release(KEY_MAP[code], now_ms())
                if 'KEY_NUMLOCK' in held and 'KEY_TAB' in held:
                    ui.say('PiHAMTRC shutting down')
                    speech.wait_idle()
                    sys.exit(0)
        keypad.poll(now_ms())


if __name__ == '__main__':
    main()
