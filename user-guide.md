# HamPiTRC User Guide

For practical use on the air. Every key is listed in
[docs/keypad-map.md](docs/keypad-map.md).

## Starting and stopping

HamPiTRC starts with the radio it used last time (on the very first start,
the one in `config.py`). It says "PiHAMTRC ready", then the radio, mode and
frequency. `NumLock` + `Tab` together end the program; the Raspberry Pi keeps
running.

If you hear "<radio> not connected", the radio is off, the USB cable is out,
or the serial port in `config.py` is wrong.

## Why an external keypad

HamPiTRC follows the HamTRC idea: a small, tactile keypad that belongs to the
radio alone, where every key has a fixed place you find by touch. A separate
USB numeric keypad is recommended on every Raspberry Pi, including the Pi 500:
its built-in keyboard has no number pad, and the key map expects one.

HamPiTRC takes the keypad for itself while it runs, so key presses do not also
type into a desktop or console on the same Pi (`KEYBOARD_GRAB` in
`config.py`).

## Keys

- **Short press**: the bank's main function, usually "tell me".
- **Long press** (about half a second): change something.
- **Double-click**: step back or down, where there is one.
- `*` short says the bank; `*` long, a number and `D` changes bank.
- `#` cancels, `D` confirms.

## Banks

| Bank | For |
| --- | --- |
| 1 | frequency, mode, power, S-meter, SWR, VFO |
| 2 | noise reduction, blanker, notch, filters, preamp, attenuator, AGC |
| 3 | VFO A/B, split |
| 4 | tuner, monitor, transceive |
| 5 | RIT |
| 6 | repeater, tones, digital squelch |
| 7 | memory, scan, D-STAR data, GPS |
| 8 | CI-V address and baud rate |
| 9 | radio selection, tuning speech, volume |

## Several radios

Bank 9, key `1` selects the next radio and connects to it, key `2` the
previous one, key `A` says which radio is active. The order is IC-705,
IC-7300, IC-7100. The choice is remembered for the next start.

A key the active radio cannot do says so, for example "GPS not available on
I C seventy-three hundred", and nothing is sent to the radio.

## Memory write and memory clear

Both ask first: "Memory clear. D to confirm, sharp to cancel". Only `D` sends
the command; `#` cancels; other keys only repeat the question.

## CI-V settings

Bank 8 changes the CI-V address and baud rate at once, for the active radio.
Long `D` in Bank 8 keeps them for the next start.

## Good to know

- The S-meter uses Icom's scale (S0 to S9, then S9 plus 10 to plus 60 dB).
- Announcements for settings ("Noise reduction on") mean the command was
  sent; the radio's acknowledgement is not checked yet.
