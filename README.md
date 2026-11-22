# HamPiTRC-Experiment

Talking transceiver controller by Jean Weber, LX1WJ, for a Raspberry Pi and
Icom radios connected by USB. Everyday operation uses a USB numeric keypad and
spoken feedback, without a screen or web browser.

HamPiTRC is the Raspberry Pi sister project of the
[Talking Remote Controller LX1WJ (HamTRC)](https://github.com/jewelux/Talking-Remote-Controller-LX1WJ)
and follows its layout: built-in radio profiles, nine keypad banks, one page
per radio under `docs/radios/`. The spoken startup name is still PiHAMTRC.

| I want to… | Read |
| --- | --- |
| get it running quickly | [QUICKSTART.md](QUICKSTART.md) |
| use it on the air | [user-guide.md](user-guide.md) |
| build, adapt, test or add a radio | [builder-guide.md](builder-guide.md) |
| look up a key | [docs/keypad-map.md](docs/keypad-map.md) |
| see which radio does what | [docs/radio-support-matrix.md](docs/radio-support-matrix.md) |
| see what changed | [CHANGELOG.md](CHANGELOG.md) |

## Status

| Radio | Status |
| --- | --- |
| Icom IC-705 | **tested on hardware**: Raspberry Pi 5, USB numeric keypad, PC speakers, demonstrated live |
| Icom IC-7300 | profile ready, not tested on a radio yet |
| Icom IC-7100 | conservative first profile, not tested on a radio yet |

Not every IC-705 function has been exercised on the radio. Treat the S-meter,
memory write/clear and tuner commands with care until they are confirmed;
memory write and clear ask for `D` before anything is sent.

Known limitations:

- Volume keys change an internal value, not ALSA playback volume.
- Tuning Speech toggles a flag; automatic dial announcements are not implemented.
- Many setters announce an action without checking the radio's acknowledgement.
- No voice model, startup service or network transport is included.

## How it works, in one paragraph

A key press runs one handler in `pihamtrc.py`. The handler asks `radio.py`,
which checks the active radio profile (`radio_profiles.py`): a feature the
radio lacks is spoken as "not available" and nothing is sent. Otherwise
`civ.py` sends the Icom CI-V frame (for example `FE FE A4 E0 03 FD` to read
the frequency), decodes the BCD reply, and the handler turns the value into a
short sentence. `speech.py` renders it with Piper and plays it through ALSA.

## Files

| File | What it is |
| --- | --- |
| `pihamtrc.py` | main program: keypad loop, nine banks |
| `radio.py` | active radio: profile selection, capability gate, prefs file |
| `radio_profiles.py` | built-in radio profiles (IC-705, IC-7300, IC-7100) |
| `civ.py` | Icom CI-V protocol (formerly `ic705.py`) |
| `speech.py` | Piper speech output |
| `keymap.py` | keypad keycodes and bank names |
| `config.py` | station settings: first radio, serial ports, keypad, audio, voice |
| `tests/` | host tests with a simulated serial port |
| `tools/legacy/` | old diagnostics from 0.7.0 |

## Branches

As in HamTRC: `main` holds the stable version, `development` integrates
ongoing work, and larger or radio-specific changes get their own branch.

## Licence

To be added (see HamTRC for the code/documentation split used there).
