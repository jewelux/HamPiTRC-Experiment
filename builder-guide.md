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
pihamtrc.py          keypad loop and the nine banks
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

1. `pihamtrc.py` reads the key, decides short, long or double, and calls the
   bank handler, e.g. `handle_short_bank2('1')`.
2. The handler calls `radio.get_nr()`.
3. `radio.py` looks up `get_nr` in `FEATURE_OF` → `nr`, checks
   `current().caps.nr`. Off: raises `NotAvailable('nr')`, which
   `run_action()` speaks as "Noise reduction not available on …". On: calls
   `civ.get_nr()`.
4. `civ.py` sends `FE FE <addr> E0 16 40 FD` and parses the reply.
5. The handler speaks the result through `speech.say_nice()`.

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
capability gate, the confirmation for memory write/clear and keypad
detection. They do not prove that a radio answers the same way.

Run hardware diagnostics separately from the controller so they do not share
the serial port.

## Prefs file

`~/.config/hampitrc/prefs.json` holds the last radio and, after long `D` in
Bank 8, the CI-V address and baud rate per radio. Delete it to go back to the
defaults. `HAMPITRC_PREFS` overrides the path.

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
