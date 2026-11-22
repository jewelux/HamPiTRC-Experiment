# HamPiTRC-Experiment

Talking transceiver controller by Jean Weber, LX1WJ, for a Raspberry Pi and radios connected by USB. Everyday operation uses a USB numeric keypad and
spoken feedback, without a screen or web browser.

HamPiTRC is the Raspberry Pi sister project of the
[Talking Remote Controller LX1WJ (HamTRC)](https://github.com/jewelux/Talking-Remote-Controller-LX1WJ)
and follows its layout: built-in radio profiles, nine keypad banks, one page
per radio under `docs/radios/`, and since 0.8.0-dev HamTRC's keypad layout and
behaviour: focus keys A/B/C, help mode, verbose, speech speed and volume. The
spoken startup name is still PiHAMTRC.

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

The IC-705 test was done with the 0.7.0 layout. The HamTRC layout of
0.8.0-dev is new and needs a test on the radio.

Known limitations:

- Tuning speech (Bank 9 `4`) is a switch only; automatic dial announcements are
  not implemented.
- No voice model, startup service or network transport is included.

## How it works, in one paragraph

`keypad_input.py` turns key presses into short, long and double presses.
`banks.py` says what that key does on the active radio, `ui.py` carries it
out. Radio calls go through `radio.py`, which checks the radio's profile
(`radio_profiles.py`): a feature the radio lacks is spoken as "not available"
and nothing is sent. Otherwise `civ.py` sends the Icom CI-V frame (for example
`FE FE A4 E0 03 FD` to read the frequency) and decodes the BCD reply, and the
action turns the value into a short sentence. `speech.py` renders it with Piper
and plays it through ALSA; a new key press stops it.

## Files

| File | What it is |
| --- | --- |
| `pihamtrc.py` | main program: reads the keypad, startup |
| `keypad_input.py` | keypad state machine: gestures, banks, entries, focus, help mode |
| `banks.py` | the keymap: what each key does on each bank |
| `ui.py` | carries out key actions: speech, entries, A/B/C focus steps |
| `settings.py` | the settings A, B and C act on: range, steps, read, write |
| `radio.py` | active radio: profile selection, capability gate, prefs file |
| `radio_profiles.py` | built-in radio profiles (IC-705, IC-7300, IC-7100) |
| `civ.py` | Icom CI-V protocol (formerly `ic705.py`) |
| `speech.py` | Piper speech output |
| `keymap.py` | USB keypad keycodes -> HamTRC logical keys |
| `config.py` | station settings: first radio, serial ports, keypad, audio, voice |
| `tests/` | host tests with a simulated serial port |
| `tools/legacy/` | old diagnostics from 0.7.0 |

## Branches

As in HamTRC: `main` holds the stable version, `development` integrates
ongoing work, and larger or radio-specific changes get their own branch.

## License

As in HamTRC: code under the GNU General Public License v3 (`LICENSE`),
documentation under Creative Commons Attribution-ShareAlike 4.0
(`LICENSE-docs`).
