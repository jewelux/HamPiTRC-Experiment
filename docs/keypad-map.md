# HamPiTRC keypad map

Start:

```sh
python -B pihamtrc.py
```

Exit: `NumLock` + `Tab`.

## Basic operation

- Short press: function from the active bank.
- Long press: alternative function, from about 0.5 seconds.
- Double-click: reverse or decrease, where implemented.
- `*` short: announce the active bank.
- `*` long: enter a bank number and confirm with `D`.
- `#`: cancel an entry.
- `D`: confirm an entry.

A key whose function the active radio does not have says, for example,
"GPS not available on I C seventy-three hundred" and sends nothing to the
radio. Which radio has what: [radio-support-matrix.md](radio-support-matrix.md).

## Numeric entry

- Frequency: in kHz, confirm with `D`. Example: `14250` = 14.250 MHz.
- Mode: one digit, confirm with `D`.
- RF power and monitor level: percent `0` to `100`, confirm with `D`.
- CI-V address: decimal `0` to `255`, confirm with `D`.
- Memory channel: `0` to `99`, confirm with `D`.
- Memory write and memory clear: `D` confirms, `#` cancels. No other key
  does anything until one of the two is pressed.

## Mode digits

| Key | Mode |
| --- | --- |
| `1` | LSB |
| `2` | USB |
| `3` | CW |
| `4` | FM |
| `5` | AM |
| `6` | RTTY |
| `7` | CW-R |
| `8` | DV (IC-705, IC-7100) |
| `9` | RTTY-R |

## Bank selection

Hold `*`, type the bank number, then press `D`.

| Bank | Name |
| --- | --- |
| `1` | Main functions |
| `2` | Filter |
| `3` | VFO |
| `4` | Monitor |
| `5` | RIT |
| `6` | Repeater |
| `7` | Memory, Scan, D-STAR, GPS |
| `8` | CI-V Setup |
| `9` | System |

## Bank 1: Main functions

| Key | Short | Long | Double-click |
| --- | --- | --- | --- |
| `0` | Announce Frequency | Enter Frequency | No function |
| `1` | Announce TX/RX status | No function | No function |
| `2` | Announce TX-Frequency | No function | No function |
| `3` | Announce Lock status | Lock on/off | No function |
| `4` | Announce Power Meter, otherwise RF Power | No function | No function |
| `5` | No function | No function | No function |
| `6` | Announce RF Power | Enter RF Power | No function |
| `7` | Announce S-Meter | No function | No function |
| `8` | Announce SWR | No function | No function |
| `9` | Announce Mode | Enter Mode | No function |
| `A` | Select VFO A | No function | No function |
| `B` | Select VFO B | No function | No function |
| `C` | Swap VFO A/B | No function | No function |
| `D` | Announce Version and callsign | No function | No function |

## Bank 2: Filter

| Key | Short | Long | Double-click |
| --- | --- | --- | --- |
| `0` | Announce Notch width | Notch width forward | Notch width backward |
| `1` | Noise Reduction status | Noise Reduction on/off | No function |
| `2` | Noise Blanker status | Noise Blanker on/off | No function |
| `3` | Notch status | Notch on/off | No function |
| `4` | Announce NR Level | NR Level +10 percent | NR Level -10 percent |
| `5` | Announce NB Level | NB Level +10 percent | NB Level -10 percent |
| `6` | Announce PBT 1 | PBT 1 +10 | PBT 1 -10 |
| `7` | Announce PBT 2 | PBT 2 +10 | PBT 2 -10 |
| `8` | Announce Filter Shape | Filter Shape sharp/soft toggle | No function |
| `9` | Announce Filter Width | Filter Width forward | Filter Width backward |
| `A` | Announce Preamp | Preamp forward | Preamp backward |
| `B` | Announce Attenuator | Attenuator 0/20 dB toggle | No function |
| `C` | Announce AGC | AGC forward | AGC backward |
| `D` | Announce Filter Width and shape | No function | No function |

## Bank 3: VFO

| Key | Short | Long | Double-click |
| --- | --- | --- | --- |
| `0` | Announce Split status | Split on/off | No function |
| `1` | Announce VFO A Frequency | Select VFO A | Enter VFO A Frequency |
| `2` | Announce VFO B Frequency | Select VFO B | Enter VFO B Frequency |
| `3` | No function | No function | No function |
| `4` | Announce VFO A Mode | Enter VFO A Mode | No function |
| `5` | Announce VFO B Mode | Enter VFO B Mode | No function |
| `6` | Announce TX/RX status | No function | No function |
| `7` | No function | No function | No function |
| `8` | No function | No function | No function |
| `9` | No function | No function | No function |
| `A` | Select VFO A | No function | No function |
| `B` | Select VFO B | No function | No function |
| `C` | Swap VFO A/B | No function | No function |
| `D` | No function | No function | No function |

## Bank 4: Monitor

| Key | Short | Long | Double-click |
| --- | --- | --- | --- |
| `0` | Announce Tuner status | Tuner on/off | Start tuning |
| `1` | Announce Monitor status | Monitor on/off | No function |
| `2` | Announce Monitor Level | Monitor Level +10 percent | Monitor Level -10 percent |
| `3` | Announce Transceive status | Transceive on/off | No function |
| `4` | No function | No function | No function |
| `5` | No function | No function | No function |
| `6` | No function | No function | No function |
| `7` | No function | No function | No function |
| `8` | No function | No function | No function |
| `9` | No function | No function | No function |
| `A` | No function | No function | No function |
| `B` | No function | No function | No function |
| `C` | No function | No function | No function |
| `D` | No function | No function | No function |

## Bank 5: RIT

| Key | Short | Long | Double-click |
| --- | --- | --- | --- |
| `0` | Announce RIT status and offset | RIT on/off | RIT Offset to zero |
| `1` | RIT -10 Hz | RIT -100 Hz | No function |
| `2` | RIT +10 Hz | RIT +100 Hz | No function |
| `3` | RIT Offset to zero | RIT off | RIT Offset to zero |
| `4` | RIT -1 Hz | RIT -500 Hz | No function |
| `5` | RIT +1 Hz | RIT +500 Hz | No function |
| `6` | No function | No function | No function |
| `7` | No function | No function | No function |
| `8` | No function | No function | No function |
| `9` | Announce RIT status | No function | No function |
| `A` | No function | No function | No function |
| `B` | No function | No function | No function |
| `C` | No function | No function | No function |
| `D` | No function | No function | No function |

## Bank 6: Repeater

| Key | Short | Long | Double-click |
| --- | --- | --- | --- |
| `0` | Announce Duplex | Duplex forward: simplex/minus/plus | Duplex backward: simplex/plus/minus |
| `1` | Repeater Tone status | Repeater Tone on/off | No function |
| `2` | TSQL status | TSQL on/off | No function |
| `3` | DTCS status | DTCS on/off | No function |
| `4` | Announce Tone Mode | Tone Mode forward | No function |
| `5` | Announce Digital Squelch | Digital Squelch forward | Digital Squelch backward |
| `6` | No function | No function | No function |
| `7` | No function | No function | No function |
| `8` | No function | No function | No function |
| `9` | No function | No function | No function |
| `A` | No function | No function | No function |
| `B` | No function | No function | No function |
| `C` | No function | No function | No function |
| `D` | No function | No function | No function |

## Bank 7: Memory, Scan, D-Star, GPS

| Key | Short | Long | Double-click |
| --- | --- | --- | --- |
| `0` | Select Memory Mode | Memory Write, after `D` to confirm | No function |
| `1` | Enter Memory Channel | No function | No function |
| `2` | Memory copy to VFO | Memory Clear, after `D` to confirm | No function |
| `3` | Scan Stop | No function | No function |
| `4` | Program Memory Scan | Program Scan | No function |
| `5` | Memory Scan | Select Memory Scan | No function |
| `6` | Announce DV Data TX | DV Data TX PTT/Auto toggle | No function |
| `7` | Announce DV Fast Data | DV Fast Data on/off | No function |
| `8` | Announce GPS Select | GPS Select off/on/manual toggle | No function |
| `9` | Announce GPS TX Mode | GPS TX Mode off/DPRS/NMEA toggle | No function |
| `A` | No function | No function | No function |
| `B` | No function | No function | No function |
| `C` | No function | No function | No function |
| `D` | No function | No function | No function |

## Bank 8: CI-V Setup

| Key | Short | Long | Double-click |
| --- | --- | --- | --- |
| `0` | No function | No function | No function |
| `1` | Announce CI-V address | Enter CI-V address | No function |
| `2` | Announce Baud rate | Baud rate forward | Baud rate backward |
| `3` | No function | No function | No function |
| `4` | No function | No function | No function |
| `5` | No function | No function | No function |
| `6` | No function | No function | No function |
| `7` | No function | No function | No function |
| `8` | No function | No function | No function |
| `9` | No function | No function | No function |
| `A` | No function | No function | No function |
| `B` | No function | No function | No function |
| `C` | No function | No function | No function |
| `D` | No function | Save CI-V address and baud rate for this radio | No function |

Baud-rate order: `4800`, `9600`, `19200`, `38400`, `115200`.

Changes made with keys `1` and `2` apply at once. Long `D` keeps them for the
next start (in `~/.config/hampitrc/prefs.json`, per radio).

## Bank 9: System

| Key | Short | Long | Double-click |
| --- | --- | --- | --- |
| `0` | No function | No function | No function |
| `1` | Next radio, connect to it | No function | No function |
| `2` | Previous radio, connect to it | No function | No function |
| `3` | No function | No function | No function |
| `4` | Announce Tuning Speech status | Tuning Speech on/off | No function |
| `5` | Announce Volume | No function | No function |
| `6` | No function | No function | No function |
| `7` | Set volume 1 | Volume -1 | No function |
| `8` | Set volume 2 | Volume +1 | No function |
| `9` | Set volume 3 | No function | No function |
| `A` | Announce the active radio | No function | No function |
| `B` | No function | No function | No function |
| `C` | No function | No function | No function |
| `D` | No function | No function | No function |

Radio order: IC-705, IC-7300, IC-7100. The chosen radio is remembered for the
next start. If its serial port is not there, HamPiTRC says "selected, not
connected"; press `1` or `2` again to go on.

Note: Volume functions currently manage the internal PiHAMTRC value. They do not change ALSA playback volume.
