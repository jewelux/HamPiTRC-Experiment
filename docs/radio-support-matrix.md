# Radio Support Matrix

The current support state per radio. A short engineering overview, not a
promise list. "on" means the profile switches the feature on; it does not mean
it was checked on a radio. The hardware status column says what was.

Sources: each radio's CI-V reference guide and Hamlib (`rigs/icom/*.c`). A
feature is switched on where both agree, as in HamTRC.

| Radio | Profile key | CI-V address | Default baud | Serial port | Hardware status |
| --- | --- | --- | --- | --- | --- |
| Icom IC-705 | `ic705` | A4h | 115200 | `/dev/ttyACM0` | **tested on hardware** (Pi 5, USB keypad, PC speakers) |
| Icom IC-7300 | `ic7300` | 94h | 115200 | `/dev/ttyUSB0` | not tested |
| Icom IC-7100 | `ic7100` | 88h | 19200 | `/dev/ttyUSB0` | not tested |

## Features per radio

| Feature (bank) | IC-705 | IC-7300 | IC-7100 |
| --- | --- | --- | --- |
| Frequency, mode, entry (1) | on | on | on |
| S-meter, power meter, SWR (1) | on | on | on |
| RF power (1) | on | on | on |
| TX/RX status (1) | on | on | on |
| TX frequency `1C 03` (1) | on | on | off: Hamlib "possibly" |
| Lock (1) | on | on | on |
| NR, NB, levels (2) | on | on | on |
| Manual notch (2) | on | on | on |
| Notch width `16 57` (2) | on | on | off: not in Hamlib |
| PBT (2) | on | on | on |
| Filter shape `16 56` (2) | on | on | off: not in Hamlib |
| Filter width (2) | on | on | on |
| Preamp, attenuator, AGC (2) | on | on | on |
| VFO A/B, swap, split (3) | on | on | on |
| Direct VFO B access `25`/`26` (3) | on | on | off: Hamlib "possibly" |
| Tuner (4) | on (AH-705) | on | on (AH-4) |
| Monitor on/off (4) | on | on | off: not in Hamlib |
| Monitor level (4) | on | on | on |
| Transceive (4) | on, menu 0131 | on, menu 0071 | off: menu item unknown |
| RIT `21` (5) | on | on | off: no RIT command in Hamlib |
| Duplex `0F 1x` (6) | on | off: none over CI-V | on |
| Repeater tone, TSQL (6) | on | on | on |
| DTCS, tone mode (6) | on | off | off |
| D-STAR digital squelch (6) | on | – | off: to check |
| Memory, memory clear, scan (7) | on | on | on |
| DV data, GPS (7) | on | – | off: to check |
| DV mode | on | – | on |
| WFM mode | – | – | on |

"–" means the radio does not have it. "off" means the radio may have it but
the profile does not switch it on yet.
