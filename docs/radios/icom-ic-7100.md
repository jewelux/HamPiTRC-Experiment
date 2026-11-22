# Icom IC-7100

## Status

Conservative first profile, **not tested on a radio**.

## Connection

- USB cable to the Pi; appears as `/dev/ttyUSB0` (or use
  `/dev/serial/by-id/...` in `SERIAL_PORTS`).
- CI-V address 88h; the radio's CI-V port goes up to 19200 baud
  (Hamlib `ic7100.c`). Profile default 19200.

## Profile

`IC7100_CAPS` switches on what Hamlib lists for the IC-7100: frequency, mode,
meters, RF power, TX status, lock, NR/NB and levels, manual notch, PBT, filter
width, preamp (1, 2), attenuator (20 dB), AGC, VFO and split, tuner, monitor
level, repeater shift, tone and TSQL, memory and scan.

Off until checked on the radio or in the IC-7100 CI-V reference guide:

| Feature | Why off |
| --- | --- |
| TX frequency `1C 03`, direct VFO B `25`/`26` | Hamlib: "possibly" only |
| Monitor on/off, filter shape, notch width | not in Hamlib's IC-7100 list |
| RIT | Hamlib has no RIT command for the IC-7100 |
| Transceive | menu item number not known yet |
| D-STAR squelch, DV data, GPS, DTCS, tone mode | to check in the CI-V guide |

Modes: LSB, USB, CW, FM, AM, RTTY, CW-R, RTTY-R, WFM, DV.

## First test

Bank 1 (`0`, `9`, `7`, `8`), Bank 2, Bank 3 (`0`, `1` long, `2` long), Bank 6
(`0`, `2`, `5`). Each switched-off feature should say "… not available on I C
seventy-one hundred", for example Bank 5 (RIT). The whole list:
`icom-test-list.txt`.
