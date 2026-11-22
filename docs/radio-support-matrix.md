# Radio Support Matrix

The current support state per radio. A short engineering overview, not a
promise list. "on" means the profile switches the feature on; it does not mean
it was checked on a radio. The hardware status column says what was.

Sources: each radio's CI-V reference guide or CAT manual and Hamlib. A
feature is switched on where both agree, as in HamTRC. The FTDX10 profile is
HamTRC's (development branch); details in `radios/yaesu-ftdx10.md`.

| Radio | Profile key | CI-V address | Default baud | Serial port | Hardware status |
| --- | --- | --- | --- | --- | --- |
| Icom IC-705 | `ic705` | A4h | 115200 | `/dev/ttyACM0` | **tested on hardware** (Pi 5, USB keypad, PC speakers) |
| Icom IC-7300 | `ic7300` | 94h | 115200 | `/dev/ttyUSB0` | not tested |
| Icom IC-7100 | `ic7100` | 88h | 19200 | `/dev/ttyUSB0` | not tested |
| Yaesu FTDX10 | `ftdx10` | – (ASCII CAT) | 38400 | `/dev/ttyUSB0` (Enhanced COM) | assisted field test pending |

## Features per radio

Bank and key as in [keypad-map.md](keypad-map.md).

| Feature (bank key) | IC-705 | IC-7300 | IC-7100 | FTDX10 |
| --- | --- | --- | --- | --- |
| Frequency, entry, round (1 `0`) | on | on | on | on |
| RX/TX (1 `1`) | on | on | on | on (`TX;`) |
| TX frequency `1C 03` (1 `2`, 3 `0` double) | on | on | off: Hamlib "possibly" | on (FB in split) |
| Lock (1 `3`) | on | on | on | on |
| Output power, ALC (1 `4`, `5`) | on | on | on | on, percent |
| RF power (1 `6`, 4 `8`, 7 `8`) | on, 10 W | on, 100 W | on, 100 W | on, 5-100 W |
| S-meter, SWR (1 `7`, `8`) | on | on | on | on, Hamlib scale |
| Mode (1 `9`) | on, with DV | on | on, with DV | on, with DATA |
| Auto notch `16 41` (2 `0`) | on | on | on | on (`BC0`) |
| NR, NB, levels (2 `1`, `2`) | on | on | on | on, levels 1-15 / 0-10 |
| Notch (2 `3`) | off/narrow/mid/wide | off/narrow/mid/wide | off/on: no width in Hamlib | off/on |
| PBT (2 `4`, `6`) | on | on | on | – |
| Filter (2 `5`) | on, with shape | on, with shape | on, no shape in Hamlib | – |
| AGC, preamp, attenuator (2 `7`-`9`) | on | on | on | on, 5 AGC speeds, 6/12/18 dB |
| Split, VFO A/B select (3 `0`-`2` long) | on | on | on | on |
| VFO B readout and entry `25`/`26` (3 `2`, `4`, `5`) | on | on | off: Hamlib "possibly" | on (FB, MD0 on VFO B) |
| Tuner (4 `0`, 7 `0`) | on (AH-705) | on | on (AH-4) | on |
| Monitor on/off (4 `3`) | on | on | off: not in Hamlib | – |
| Monitor level (4 `3` double) | on | on | on | – |
| RIT `21` (5) | on | on | off: no RIT command in Hamlib | – |
| Repeater shift `0F 1x` (6 `0`) | on | – | on | on (`OS0`, FM) |
| Tone type and direction (6 `2`, `5`) | on | on | on | on (`CT0`) |
| CI-V address, baud (8 `1`, `2`) | on | on | on | baud only |
| Transceive (8 `3`) | on, menu 0131 | on, menu 0071 | off: menu item unknown | – |
| Processor and level, VOX and gain, mic gain (4 `1`, `2`, `7`) | on | on | on | on |
| VOX delay (4 `9`) | on, menu 0359 | on, menu 0191 | off: menu item in Hamlib only | on, 30-3000 ms |
| Break-in off/semi/full, CW pitch (7 `2`, `5`) | on | on | on | break-in on/off, pitch 300-1050 Hz |
| CTCSS tone (6 `3`) | on | on | off: no tone command in Hamlib | on (`CN00`) |
| Band stack (3 `7`-`9`) | on | on | off: not in Hamlib | – |

"–" means not available on that radio: the radio lacks it, or (FTDX10) HamTRC
has no tested command for it and hides the key. "off" means the radio may have
it but the profile does not switch it on yet; experimental mode (Bank 9 `0`
long) tries it anyway.

Yaesu only (FTDX10): keyer and keyer speed (7 `1`), break-in delay (7 `9`),
radio power switch and ID (8 `4`, `5`).

Not on the keypad (as in HamTRC), commands kept in `civ.py`: memory, scan,
D-STAR data, GPS, DTCS, tone mode, digital squelch.
