# HamPiTRC Keypad Map

What every bank key does. The layout and the behaviour are HamTRC's (development
branch, `docs/keypad-map.md` there, Icom column), so a HamTRC user finds every
function under the same key number. Where HamPiTRC cannot do something yet, the
key says "not available"; a free key beeps.

## The keypad

HamTRC has a 4x4 keypad; HamPiTRC a PC numeric keypad. The logical keys are the
same, but the digits sit upside down (7 8 9 on top):

| HamTRC 4x4 | | | | | USB numeric keypad | | | |
|---|---|---|---|---|---|---|---|---|
| 1 | 2 | 3 | A | | 7 | 8 | 9 | Backspace = A |
| 4 | 5 | 6 | B | | 4 | 5 | 6 | Minus = B |
| 7 | 8 | 9 | C | | 1 | 2 | 3 | Plus = C |
| * | 0 | # | D | | 0 | Space = * | Dot = # | Enter = D |

`NumLock` + `Tab` ends HamPiTRC (HamPiTRC only).

## Presses

- **short**: on release. Ask or read something.
- **long** (hold 0.7 s): change something. Acts at the hold.
- **double**: a quick second press (within 0.22 s), only where a key has one.
- **short, then hold**: a quick press followed by a hold of the same key.
- One key at a time: a second key while one is down beeps, and both are ignored.
- `*` short: the bank. `*` long, let go, a digit: change bank. `*` long and,
  still holding `*`, a digit: the next key only acts on that bank.
- `D` long: help mode on/off. Each key then says what it would do and does
  nothing. `#` or `D` long ends it.
- `#`: cancel an entry, end help mode. `D`: confirm an entry.
- An entry left for 30 seconds ends with "timeout".
- A new key press stops the current speech.

## Focus: A, B and C

`A`, `B` and `C` act on the bank's focus: the setting of the last key on that
bank that has one. Bank 5 starts on the RIT offset, Bank 8 on the baud rate and
Bank 9 on the profile; the other banks start with none, and `A`, `B`, `C` then
say "focus not available".

| Press | Does |
|---|---|
| `A` short | the focus with its name |
| `A` long | its entry or pick |
| `A` double | back to the centre (PBT 0, RIT 0, normal speed, profile reset) |
| `B` / `C` short | one step up / down; the first names the setting, the next only the value |
| `B` / `C` long | a big step (5 steps; volume 2; RIT 100 Hz); mode, profile, baud: not available |

RF power and the mode wait for `D`: `B` or `C` opens the entry one step away
("power 6 watts please"), more `B`/`C` step, `D` sets, `#` cancels. Past the
end: "maximum" or "minimum".

## Bank 1 - Status

| Key | Short | Long | Double |
|---|---|---|---|
| `0` | frequency | frequency entry (MHz, `*` point) | round to 500 Hz |
| `1` | RX or TX | | |
| `2` | TX frequency | | |
| `3` | lock | lock on/off | |
| `4` | output power | | |
| `5` | ALC | | |
| `6` | RF power setting (focus) | RF power entry | |
| `7` | S-meter | | |
| `8` | SWR (in receive: "swr tx only") | | |
| `9` | mode (focus) | mode select | |

Frequency entry: `14` `D` = 14 MHz, `14*1` `D` = 14.1 MHz, `7*12345` `D` =
7.12345 MHz. Frequencies are spoken digit by digit: "one four point one".

Mode digits: `1` LSB, `2` USB, `3` CW, `4` AM, `5` FM, `7` RTTY, `8` CW-R,
`9` RTTY-R; `0` DV (IC-705, IC-7100, HamPiTRC only). `6` (DATA) is not
available yet.

## Bank 2 - Receiver

| Key | Short | Long | Double | Short, then hold |
|---|---|---|---|---|
| `0` | auto notch | auto notch on/off | | |
| `1` | noise reduction | on/off | NR level (focus) | NR level entry |
| `2` | noise blanker | on/off | NB level (focus) | NB level entry |
| `3` | notch (focus) | off, narrow, mid, wide | | |
| `4` | PBT inner (focus) | PBT inner entry (`*` minus) | | |
| `5` | filter 1-3 (focus) | next filter | filter shape | filter shape soft/sharp |
| `6` | PBT outer (focus) | PBT outer entry | | |
| `7` | AGC (focus) | AGC select: `2` fast, `4` mid, `3` slow | | |
| `8` | preamp (focus) | next: off, 1, 2 | | |
| `9` | attenuator (focus) | off / 20 dB | | |

NR and NB levels in percent, steps of 5. PBT -128 to 127, steps of 10.

## Bank 3 - VFO and Split

| Key | Short | Long | Double |
|---|---|---|---|
| `0` | split | split on/off | TX frequency |
| `1` | VFO A frequency | select VFO A | VFO A frequency entry |
| `2` | VFO B frequency | select VFO B | VFO B frequency entry |
| `4` | VFO A mode | VFO A mode select | |
| `5` | VFO B mode | VFO B mode select | |
| `6` | RX or TX | | |
| `7` `8` `9` | band stack 1-3 of the current band | recall it (frequency and mode) | |

## Bank 4 - Phone Transmit

| Key | Short | Long | Double | Short, then hold |
|---|---|---|---|---|
| `0` | tuner | tuner on/off | tune | |
| `1` | processor | on/off | processor level (focus) | processor level entry |
| `2` | VOX | on/off | VOX gain (focus) | VOX gain entry |
| `3` | monitor | on/off | monitor level (focus) | monitor level entry |
| `4` `5` `6` | not available (TX low cut, equalizer, high cut) | | | |
| `7` | mic gain (focus) | mic gain entry | | |
| `8` | RF power setting (focus) | RF power entry | | |
| `9` | VOX delay (focus) | VOX delay entry (ms) | | |

Levels 0-100 percent, `B`/`C` steps of 5. VOX delay 0-2000 ms in steps of
100.

## Bank 5 - RIT

Home focus: the RIT offset.

| Key | Short | Long | Double |
|---|---|---|---|
| `0` | RIT on/off and offset | RIT on/off | offset to 0 |
| `1` / `2` | offset -10 / +10 Hz | -100 / +100 Hz | |
| `3` | offset to 0 | RIT off | |
| `4` / `5` | offset -1 / +1 Hz | -500 / +500 Hz | |
| `A` `B` `C` | the offset; `B`/`C` 10 Hz, long 100 Hz; `A` long entry, `*` first for minus; `A` double 0 | | |

## Bank 6 - Repeater and Tone

| Key | Short | Long | Double |
|---|---|---|---|
| `0` | repeater shift off | shift minus | shift plus |
| `1` | repeater frequency: not available | | |
| `2` | tone type: off or CTCSS | CTCSS | tone off |
| `3` | CTCSS tone (focus) | CTCSS tone entry: `885` or `88*5` = 88.5 Hz | |
| `4` | DCS: not available | | |
| `5` | encode only (TX) or encode and decode (both) | step between both and TX | |

`B`/`C` walk the 50 standard CTCSS tones (long: 5 tones) and set each at once.

## Bank 7 - CW

| Key | Short | Long | Double |
|---|---|---|---|
| `0` | tuner | tuner on/off | tune |
| `2` | break-in (focus) | next: off, semi, full | |
| `5` | CW pitch (focus) | CW pitch entry (Hz) | |
| `8` | RF power setting (focus) | RF power entry | |
| `1` `3` `4` `6` `7` `9` | keyer, sidetone, paddle, weight, paddle reverse, break-in delay: not available on Icom (as in HamTRC) | | |

CW pitch 300-900 Hz, `B`/`C` steps of 10 Hz.

## Bank 8 - Connection

Home focus: the baud rate.

| Key | Short | Long |
|---|---|---|
| `1` | CI-V address | CI-V address entry (decimal, `D`) |
| `2` | baud rate (focus) | baud rate pick: `1` the slowest, `2` the next … |
| `3` | transceive | transceive on/off |

`B`/`C` step the baud rate and go round. A changed address or baud rate is kept
for the radio. Set the same on the radio.

## Bank 9 - Profile and Speech

Home focus: the profile.

| Key | Short | Long | Double |
|---|---|---|---|
| `0` | experimental mode | on/off | |
| `1` | profile (focus) | profile select: `1` IC-705, `2` IC-7300, `3` IC-7100, `4` FTDX10 | profile reset (address and baud) |
| `4` | tuning speech | on/off | |
| `5` | verbose | on/off | |
| `7` | volume (focus) | volume entry 1-9 | |
| `8` | speech speed (focus) | next: slow, normal, fast | |

With the profile as focus, `B` / `C` select the next / previous radio and
connect to it. Verbose off gives values only ("40 percent" instead of "noise
blanker 40 percent"). Experimental mode lets every key try its command, also
where the profile switches it off; it is not saved. Volume, speed, verbose and
the radio are kept for the next start.

## FTDX10

The FTDX10 has the same layout; HamTRC's FTDX10 column. What differs (levels in
the radio's own steps, keyer and break-in delay on Bank 7, radio power and ID
on Bank 8, no RIT, PBT or band stack) is listed in
[radios/yaesu-ftdx10.md](radios/yaesu-ftdx10.md).

## Not on a key any more

HamPiTRC 0.7.0 had memory, scan, D-STAR data, GPS, DTCS, tone mode and
digital squelch keys. HamTRC has none of them, so they are off the keypad for
now; the commands stay in `civ.py`.
