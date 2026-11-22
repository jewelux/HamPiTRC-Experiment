# Changelog

## Unreleased (development, 0.8.0-dev)

### Yaesu FTDX10

- **new protocol** `yaesu_cat.py` (Yaesu ASCII CAT) beside `civ.py`;
  `radio.py` routes each call by the profile's `protocol`
- FTDX10 profile from HamTRC's development branch: commands and encodings as
  checked there against the FTDX10 CAT manual and Hamlib; status "assisted
  field test pending"
- same keypad layout as the Icoms (HamTRC's FTDX10 column): NR/NB levels in
  the radio's steps, five AGC speeds, attenuator 6/12/18 dB, RF power 5-100 W,
  DATA mode (digit `6`), keyer and keyer speed, break-in on/off and delay, radio
  power switch and ID on Bank 8; RIT, PBT, filter, monitor, transceive and band
  stack say "not available", as HamTRC hides them
- `docs/radios/yaesu-ftdx10.md` and a test list

### Transmit, CW, tone and band stack (Icom)

- Bank 4: processor and level, VOX and gain, mic gain, VOX delay (IC-705
  menu 0359, IC-7300 0191), as HamTRC
- Bank 7: break-in off/semi/full, CW pitch 300-900 Hz
- Bank 6 `3`: CTCSS tone, set as repeater and TSQL tone, `B`/`C` walk the
  50 standard tones
- Bank 3 `7`-`9`: band stack registers 1-3 of the current band, long recalls
- IC-7100: processor, VOX, mic gain, break-in and CW pitch on; VOX delay,
  CTCSS tone and band stack off until checked

### Keypad as in HamTRC

- **layout and behaviour of HamTRC's development branch** (Icom column of its
  keypad map): Bank 1 status, 2 receiver, 3 VFO and split, 4 phone transmit,
  5 RIT, 6 repeater and tone, 7 CW, 8 connection, 9 profile and speech
- gestures as in HamTRC: long press 0.7 s acts at the hold, double press
  within 0.22 s only on keys that have one, short then hold; two keys at once
  beep and are ignored; 30 s entry timeout
- focus: `A`, `B`, `C` say, enter, centre and step the bank's last setting;
  RF power and mode wait for `D`
- `*` long then a digit changes bank; with `*` still held, the next key only
- help mode (`D` long), verbose on/off, speech speed, volume 1-9 (scales the
  audio), experimental mode, profile pick and reset in Bank 9
- frequency entry in MHz with `*` as the point (was kHz); frequencies spoken
  digit by digit
- a new key press stops the current speech; free keys beep
- new: auto notch (Bank 2 `0`), ALC (Bank 1 `5`), round to 500 Hz (Bank 1 `0`
  double), notch off/narrow/mid/wide, RF power in watts
- memory, scan, D-STAR data, GPS, DTCS, tone mode and digital squelch are off
  the keypad, as HamTRC has none; their commands stay in `civ.py`. The memory
  confirmation of the earlier development state went with them
- new modules `keypad_input.py`, `banks.py`, `ui.py`, `settings.py`; `speech.py`
  plays through a queue that a key press can stop

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
- radio switching (now Bank 9 `1` and the profile focus) and the CI-V address
  and baud rate per radio are remembered in `~/.config/hampitrc/prefs.json`
- `config.py`: `RADIO_PROFILE` (first start) and `SERIAL_PORTS` per radio
  replace `DEVICE_RADIO`; `RADIO_NAME` removed (was unused)
- "<radio> not connected" instead of a crash when a key is pressed while no
  serial port is open

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
- tests moved to `tests/`, new tests for profiles, the capability gate, the
  keypad state machine, every key on every radio, and keypad detection; legacy diagnostics in `tools/legacy/`

## 0.7.0

- source snapshot as first published: IC-705 only, nine banks, Piper speech.
  Tested on a real IC-705 with a Raspberry Pi 5, USB numeric keypad and PC
  speakers
