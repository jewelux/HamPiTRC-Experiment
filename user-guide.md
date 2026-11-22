# HamPiTRC User Guide

For practical use on the air. Every key is listed in
[docs/keypad-map.md](docs/keypad-map.md). Keys and behaviour are the same as on
HamTRC, so its user guide applies too, apart from the keypad itself.

## Starting and stopping

HamPiTRC starts with the radio it used last time (on the very first start, the
one in `config.py`). It says "PiHAMTRC ready", then the radio, mode and
frequency. `NumLock` + `Tab` together end the program; the Raspberry Pi keeps
running.

If you hear "<radio> not connected", the radio is off, the USB cable is out, or
the serial port in `config.py` is wrong.

## The keypad

A separate USB numeric keypad, as HamTRC's idea is a small tactile keypad that
belongs to the radio alone. On a Raspberry Pi 500 too: its built-in keyboard
has no number pad. HamPiTRC takes the keypad for itself while it runs, so key
presses do not also type into a desktop or console.

The logical keys are HamTRC's: digits, `*` (Space), `#` (keypad dot), `A`
(Backspace), `B` (minus), `C` (plus), `D` (Enter). The digits on a PC keypad
are upside down compared with HamTRC's 4x4 keypad: 7 8 9 on top.

## Keypad basics

- Short press: ask or read something. Long press: change something.
- `D` confirms, `#` cancels and leaves an entry.
- `*` short says the bank. `*` long, let go, then a digit: that bank. `*` long
  and, still holding it, a digit: only the next key acts on that bank.
- Press one key at a time; two at once beep and are ignored.
- An entry left for 30 seconds ends with "timeout".
- A new key press stops the current speech.
- `D` long: help mode. Every key says what it would do and does nothing. `D`
  long or `#` ends it.

## A, B and C: the focus

`A`, `B` and `C` act on the last setting you used on the bank: RF power, mode,
NR level, PBT, filter, AGC, preamp, attenuator, monitor level, RIT offset,
baud rate, profile, volume, speech speed.

- `A`: say it; `A` long: its entry; `A` double: back to the centre
- `B` / `C`: one step up / down; long: a bigger step
- RF power and mode wait for `D`: `B`/`C` open the entry ("power 6 watts
  please"), `D` sets it

Bank 5 starts on the RIT offset, Bank 8 on the baud rate, Bank 9 on the
profile.

## Frequencies

Entry in MHz with `*` as the point: Bank 1, `0` long, `14*074` `D` is
14.074 MHz. Spoken digit by digit: "one four point zero seven four".
Bank 1 `0` double rounds to the nearest 500 Hz.

## Shorter answers

Bank 9 `5` long switches verbose off: "40 percent" instead of "noise blanker 40
percent", and no "ok" after a change. Prompts and "not available" stay.

## Volume and speed

Bank 9 `7`: volume 1-9 (long: entry; then `B`/`C`). Bank 9 `8`: speech speed
slow, normal, fast (long: next). Both are kept for the next start.

## Several radios

Bank 9: `1` says the radio, `1` long picks one (`1` IC-705, `2` IC-7300, `3`
IC-7100, then `D`), `B`/`C` step to the next or previous radio and connect.
`1` double resets the radio's CI-V address and baud rate to its defaults.

A key the radio cannot do says "<name> not available", and nothing is sent.

## Experimental mode

Bank 9 `0` long: every key tries its command, also where the radio's profile
switches it off. For testing a radio; not saved.

## Good to know

- The S-meter uses Icom's scale (S0 to S9, then S9 plus 10 to plus 60 dB).
- "ok" after a change means the command was sent; most settings are read back
  and the value read is the one spoken.
