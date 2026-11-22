# Changelog

## Unreleased (development, 0.8.0-dev)

### Several Icom radios

- **built-in radio profiles** (`radio_profiles.py`), modelled on HamTRC's
  profile table: IC-705, IC-7300 and IC-7100. No SD card, no profile files
- `ic705.py` is now `civ.py`, one CI-V module for every Icom radio; address,
  baud rate and the transceive menu item come from the active profile
- `radio.py` gates every radio call on the profile's capabilities. A key the
  radio cannot do says "<feature> not available on <radio>" and sends nothing
- IC-7300: everything of the IC-705 except D-STAR, GPS, repeater shift, DTCS,
  tone mode and XFC; transceive is menu 0071. Not tested on a radio
- IC-7100: conservative first block from Hamlib (address 88h, 19200 baud);
  no monitor switch, RIT, transceive, filter shape, notch width, direct VFO B
  access, D-STAR squelch, DV data or GPS yet. Not tested on a radio
- Bank 9: `1` / `2` switch to the next / previous radio and connect, `A` says
  the active radio. The choice is remembered in `~/.config/hampitrc/prefs.json`
- Bank 8: long `D` keeps the CI-V address and baud rate for the active radio
- `config.py`: `RADIO_PROFILE` (first start) and `SERIAL_PORTS` per radio
  replace `DEVICE_RADIO`; `RADIO_NAME` removed (was unused)
- "<radio> not connected" instead of a crash when a key is pressed while no
  serial port is open

### Safety

- memory write (Bank 7, long `0`) and memory clear (Bank 7, long `2`) ask for
  `D` to confirm, `#` to cancel. Before, one long press overwrote or cleared
  the memory at once

### Keypad

- the keypad is found by name and by having numeric keypad keys, so the
  "consumer control" device of the same keypad is never taken. Empty
  `KEYBOARD_NAME` takes the first keypad found
- the keypad is grabbed while HamPiTRC runs (`KEYBOARD_GRAB`), so key presses
  no longer also reach a desktop or console on the same Pi

### Fixes

- S-meter: Icom's scale (0 = S0, 120 = S9, 241 = S9 + 60 dB), as in HamTRC.
  Before, S9 was spoken "S 9 plus 30" and weak signals all read S0 or S1
- DV mode uses CI-V code 17h (Icom, Hamlib). It was 11h before
- RTTY-R and similar abbreviations are spoken correctly (longest first)
- the Piper voice loads on the first announcement, not at import

### Repository

- layout and documents as in HamTRC: `QUICKSTART.md`, `user-guide.md`,
  `builder-guide.md`, `CHANGELOG.md`, `docs/keypad-map.md` (was `KEYPAD.md`),
  `docs/radio-support-matrix.md`, `docs/radios/`
- licences as in HamTRC: GPL-3.0 for code (`LICENSE`), CC BY-SA 4.0 for
  documentation (`LICENSE-docs`)
- tests moved to `tests/`, new tests for profiles, the capability gate,
  confirmations and keypad detection; legacy diagnostics in `tools/legacy/`

## 0.7.0

- source snapshot as first published: IC-705 only, nine banks, Piper speech.
  Tested on a real IC-705 with a Raspberry Pi 5, USB numeric keypad and PC
  speakers
