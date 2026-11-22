# Icom IC-7300

## Status

Profile ready, **not tested on a radio**. HamTRC supports the IC-7300 on
hardware with the same CI-V commands, which gives a good starting point.

## Connection

- USB cable to the Pi; the radio's USB bridge appears as `/dev/ttyUSB0`
  (with several radios use `/dev/serial/by-id/...` in `SERIAL_PORTS`).
- CI-V address 94h, 115200 baud on USB (profile `ic7300`). Set the radio's
  "CI-V USB Baud Rate" accordingly, or change it in Bank 8 and keep it with
  long `D`.

## Profile

`IC7300_CAPS` = the IC-705 set without D-STAR squelch, DV data, GPS, repeater
shift (Hamlib has no `rptr_shift` for the IC-7300), DTCS, tone mode and XFC.
Transceive is menu item 0071 (HamTRC, Hamlib). Commands `25`/`26` and `1C 03`
are always present (Hamlib `x25x26_always`, `x1cx03_always`).

Modes: LSB, USB, CW, FM, AM, RTTY, CW-R, RTTY-R.

## First test

1. Bank 1: `0` frequency, `9` mode, `7` S-meter, `8` SWR (transmitting).
2. Bank 2: NR, NB, notch, filter shape and width.
3. Bank 3: VFO A/B readout, split.
4. Bank 4: tuner, monitor. Bank 8 `3`: transceive.
5. Bank 5: RIT.
6. Bank 6, key `0`: must say "repeater not available".

The whole list: `icom-test-list.txt`.

Note results with date in this file, then update the support matrix.
