# HamPiTRC Builder Guide

For building, adapting, testing and adding radios. Quick setup:
[QUICKSTART.md](QUICKSTART.md).

## Hardware

- **Raspberry Pi**: developed and tested on a Raspberry Pi 5. Nothing in the
  code is specific to the Pi 5; a Pi 4 is the planned target for a finished
  unit. Piper needs a moment per sentence; slower boards take longer, and a
  smaller ("low") Piper voice helps there. Not benchmarked yet.
- **Raspberry Pi 500**: same Pi 5 inside, so radio and speech should behave
  the same. Use an external USB numeric keypad (the built-in keyboard has no
  number pad). Not tested yet.
- **Cooling**: the program mostly waits for a key, and Piper runs only
  briefly per announcement. A passive heatsink case is enough; the official
  Pi 5 active cooler is temperature-controlled and stays quiet when idle. The
  Pi 500 has no fan.
- **Keypad**: any USB numeric keypad that sends the keypad keycodes in
  `keymap.py`. Check with `python -m evdev.evtest`.
- **Audio**: HDMI, USB audio adapter or the Pi's output; see `AUDIO_NAME`,
  `HDMI_NAME` and `AUDIO_DEVICE` in `config.py`.

## Layout

```
pihamtrc.py          reads the keypad, startup
keypad_input.py      keypad state machine (HamTRC keypad_input.cpp)
banks.py             keymap: every bank key (HamTRC keypad_keymap.cpp)
ui.py                carries out actions: speech, entries, focus steps
settings.py          settings for A/B/C, entries and picks (HamTRC SettingOps)
radio.py             active radio, capability gate, prefs file
radio_profiles.py    built-in radio profiles
civ.py               Icom CI-V protocol
speech.py            Piper speech output
keymap.py            keycodes and bank names
config.py            station settings
tests/               host tests (no radio, no Piper, no keypad needed)
tools/legacy/        0.7.0 diagnostics (Hamlib rigctl, speech experiment)
docs/                keypad map, support matrix, one page per radio
```

The idea is the one in HamTRC's development branch
(`firmware/radio_profile_table.cpp`): a radio is a table entry with link
defaults and capability flags, not a code path. There is no SD card and no
profile file: the table is part of the program.

## How a key reaches the radio

1. `pihamtrc.py` reads the keypad and calls `keypad.press()` / `release()`;
   `poll()` runs every 20 ms for holds, double presses and timeouts.
2. `keypad_input.py` decides the gesture (short, long, double, short then
   hold) and asks `banks.lookup(ui, bank, key, focus)` for the key's
   `Binding`. In help mode it says the binding's help text instead.
3. `ui.run()` runs the action, e.g. Bank 2 `1` short says noise reduction.
4. The action calls `radio.get_nr()`. `radio.py` looks up `get_nr` in
   `FEATURE_OF` → `nr` and checks the profile. Off: `NotAvailable`, spoken as
   "Noise reduction not available on …". On: `civ.get_nr()`.
5. `civ.py` sends `FE FE <addr> E0 16 40 FD` and parses the reply.
6. `ui.value()` speaks the answer, with the name when verbose is on.

## Add a key

Keys are in `banks.py`, one function per bank. Helpers build the usual kinds:
`setting_key` (say, entry, focus), `list_key` (say, next, focus),
`switch_key` (say, on/off), `switch_with_level` (NR, NB, monitor),
`not_available`. A setting for A/B/C goes in `settings.py`. Every gesture
with an action needs a help text; `tests/test_keypad_banks.py` runs every key,
gesture and radio and checks that.

## Add a radio

1. **Sources first.** Take the radio's CI-V reference guide and Hamlib's
   backend (`rigs/icom/<model>.c`). Switch a capability on only where both
   agree, as HamTRC does. "Possibly" in Hamlib (e.g. `x25x26_possibly`) means
   off until tested on the radio.
2. **Profile.** In `radio_profiles.py`, add a `Capabilities(...)` (or
   `replace()` an existing one) and a `RadioProfile` with key, written and
   spoken name, CI-V address, default baud and serial port, mode list and the
   transceive menu item if it has one. Add it to `PROFILES`.
3. **New command?** Put it in `civ.py`, add its capability to `Capabilities`,
   a spoken name to `FEATURE_NAMES`, and the function to `radio.FEATURE_OF`.
   `tests/test_profiles.py` fails if one of these is missing.
4. **Tests.** Add the address and anything special to `tests/test_profiles.py`;
   frame checks go to `tests/test_civ_commands.py`.
5. **Docs.** A row in `docs/radio-support-matrix.md`, a page
   `docs/radios/<vendor>-<model>.md`, a line in `CHANGELOG.md`, and the
   order in Bank 9 in `docs/keypad-map.md`.
6. **On the radio.** Work through `docs/radios/icom-test-list.txt` and
   change the status only for what was checked.

## Tests

```sh
python -m unittest discover -s tests
```

The tests replace the serial port with a fake, and evdev and Piper with
stand-ins, so they run on any computer. They check frames, parsing, the
capability gate, the keypad state machine, every key on every radio and keypad
detection. They do not prove that a radio answers the same way.

Run hardware diagnostics separately from the controller so they do not share
the serial port.

## Prefs file

`~/.config/hampitrc/prefs.json` holds the last radio, the CI-V address and
baud rate per radio (changed in Bank 8), and the speech settings: verbose,
volume, speed, tuning speech. Delete it to go back to the defaults; Bank 9 `1`
double resets one radio. `HAMPITRC_PREFS` overrides the path.

## Autostart (systemd)

```ini
[Unit]
Description=HamPiTRC Talking Remote Controller
After=sound.target

[Service]
ExecStart=/home/pi/pihamtrc/venv/bin/python -B /home/pi/pihamtrc/pihamtrc.py
WorkingDirectory=/home/pi/pihamtrc
User=pi
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```sh
sudo systemctl enable --now pihamtrc
sudo journalctl -u pihamtrc -f
```
