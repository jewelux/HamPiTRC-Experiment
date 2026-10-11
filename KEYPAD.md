# PiHAMTRC keypad reference

Start:

```sh
python -B pihamtrc.py
```

Exit: `NumLock` + `Tab`.

Basic operation:

- Short press: function from the active bank.
- Long press: alternative function, starting at approximately 0.5 seconds.
- Double-click: reverse/decrease function, where implemented.
 Announce - `*` short: active bank.
 Enter - `*` long: bank number and confirm with `D`.
- `#`: cancel entry.
- `D`: confirm entry.

Numeric entry:

 Enter - Frequency: in kHz and confirm with `D`. Example: `14250` = 14.250 MHz.
 Enter - Mode: one digit and confirm with `D`.
- RF Power and Monitor Level: percentage `0` to `100`, confirmed with `D`.
- CI-V address: decimal value `0` to `255`, confirmed with `D`.
- Memory Channel: channel `0` to `99`, confirmed with `D`.

Mode digits:

| Key | Mode |
| --- | --- |
| `1` | LSB |
| `2` | USB |
| `3` | CW |
| `4` | FM |
| `5` | AM |
| `6` | RTTY |
| `7` | CW-R |
| `8` | DV |
| `9` | RTTY-R |

 Select ## Bankion

 Enter Hold `*`, the bank number, then press `D`.

| Bank | Name |
| --- | --- |
| `1` | Main functions |
| `2` | Filter |
| `3` | VFO |
| `4` | Monitor |
| `5` | RIT |
| `6` | Repeater |
| `7` | Memory, Scan, D-Star, GPS |
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
| `0` | Select Memory Mode | Memory Write | No function |
| `1` | Enter Memory Channel | No function | No function |
| `2` | Memory copy to VFO | Memory Clear | No function |
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
| `D` | No function | No function | No function |

Baud-rate order: `4800`, `9600`, `19200`, `38400`, `115200`.

## Bank 9: System

| Key | Short | Long | Double-click |
| --- | --- | --- | --- |
| `0` | No function | No function | No function |
| `1` | Profile next unavailable | No function | No function |
| `2` | Profile previous unavailable | No function | No function |
| `3` | No function | No function | No function |
| `4` | Announce Tuning Speech status | Tuning Speech on/off | No function |
| `5` | Announce Volume | No function | No function |
| `6` | No function | No function | No function |
| `7` | Set volume 1 | Volume -1 | No function |
| `8` | Set volume 2 | Volume +1 | No function |
| `9` | Set volume 3 | No function | No function |
| `A` | Announce IC-705 profile | No function | No function |
| `B` | No function | No function | No function |
| `C` | No function | No function | No function |
| `D` | No function | No function | No function |

Note: Volume functions currently manage the internal PiHAMTRC value. They do not change ALSA playback volume.
