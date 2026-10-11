# HamPiTRC-Experiment

Experimental talking transceiver controller by Jean Weber, LX1WJ, for a Raspberry Pi 5 and an Icom IC-705 connected by USB. Everyday operation uses a USB keypad and spoken feedback, without a screen or web browser.

This repository preserves the supplied PiHAMTRC **0.7.0** source snapshot. HamPiTRC is the publication name; existing Python filenames and spoken startup name remain PiHAMTRC. It is a separate experiment related to [Talking Remote Controller LX1WJ](https://github.com/jewelux/Talking-Remote-Controller-LX1WJ).

## Status

The source implements nine banks covering frequency/mode, filters, VFO, monitor, RIT, repeater, memory/scan/D-Star/GPS, CI-V setup, and system functions. See [KEYPAD.md](KEYPAD.md) for the complete English key reference. Implementation does not establish that every function has been verified on a radio.

Known limitations in this snapshot:

- `ic705.py` currently starts with CI-V address **0xA4** and baud rate **115200**. Match these to the actual radio settings; do not assume they are the IC-705 factory settings. Bank 8 changes them for the running process only.
- The serial path is configured explicitly; it is not automatically discovered.
- Volume keys change an internal value, not ALSA playback volume.
- Tuning Speech toggles a flag; automatic dial-frequency announcements are not implemented in the main loop.
- The S-meter conversion needs hardware validation. Treat meter readings as experimental.
- Many setters announce an action without checking a positive radio acknowledgement.
- No voice model, automatic startup service, or network transport is included.

## Hardware and software

Raspberry Pi running Linux, IC-705 with a USB data cable, USB keypad/keyboard, and a working ALSA audio output. Speech uses Piper with the English `en_US-lessac-medium` model. The model and its matching `.onnx.json` configuration must be obtained separately; observe their model license.

The supplied environment used pyserial 3.5, evdev 1.9.3 and piper-tts 1.4.2. The environment itself is intentionally excluded.

## Setup

```sh
sudo apt install python3-venv python3-dev build-essential alsa-utils
python3 -m venv venv
. venv/bin/activate
python -m pip install -r requirements.txt
```

Place the Piper `.onnx` and matching `.onnx.json` files together. Adjust `config.py`:

| Setting | Purpose |
| --- | --- |
| `DEVICE_RADIO` | CI-V serial port, initially `/dev/ttyACM0` |
| `KEYBOARD_NAME` | Device-name substring, initially `HCT`; selected name must also end in `Keyboard` |
| `PIPER_MODEL` | Absolute path to the voice model |
| `AUDIO_NAME` / `HDMI_NAME` | Preferred audio card and fallback name |
| `AUDIO_DEVICE` | ALSA device fallback |
| `CALLSIGN` | Spoken callsign |

Also adjust `CIV_ADDR` and `BAUDRATE` in `ic705.py`. `RADIO_NAME` in `config.py` is currently unused. Give your login appropriate access to the serial and input devices according to your Linux setup (commonly the `dialout` and `input` groups); a new login is needed after group changes.

```sh
ls /dev/ttyACM* /dev/ttyUSB*
aplay -l
python -m evdev.evtest
python -B pihamtrc.py
```

## First use

Start in Bank 1. Short `0` speaks frequency; long `0` enters frequency in kHz, confirmed with `D`. Short `9` speaks mode; long `9` starts mode entry. Long `*` starts bank selection. `#` cancels entry. `NumLock` + `Tab` exits the program, without shutting down the Raspberry Pi.

This is a USB numeric keypad mapping, not an ESP32 GPIO matrix:

| Physical key | Logical key |
| --- | --- |
| Numeric keypad 0–9 | 0–9 |
| Space | `*` |
| Keypad decimal | `#` |
| Keypad Enter | `D` |
| Backspace | `A` |
| Keypad minus | `B` |
| Keypad plus | `C` |

Long press is 500 ms; double-click window is 250 ms. Ensure the keypad sends the keycodes listed in `keymap.py`.

## Verification

```sh
python -m unittest discover -p test_ic705_official.py
```

The existing tests use a fake serial connection. They check selected frames, parsing and error handling; they do not prove hardware compatibility or independently validate the protocol against an Icom manual.

`test_hamlib.sh` is an optional legacy hardware diagnostic requiring Hamlib (`rigctl`). `test_freq.py` is a legacy speech experiment using an extra frequency multiplier; it is not part of normal operation and its scaling needs review. Run hardware diagnostics separately from the controller so they do not share the serial port.

Memory write/clear operations and tuner commands are present. Consult the key reference before using them on a radio.
