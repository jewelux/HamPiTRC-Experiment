# Icom IC-705

## Status

**Tested on hardware**: Raspberry Pi 5, USB numeric keypad, PC speakers;
demonstrated live to another radio amateur. Not every function has been
exercised on the radio yet. This is the reference profile: everything
HamPiTRC 0.7.0 did is switched on.

## Connection

- USB cable to the Pi; the CI-V port appears as `/dev/ttyACM0`
  (`/dev/ttyACM1` is the data port).
- CI-V address A4h, 115200 baud on USB (profile `ic705`).
- For transceive data the radio's "CI-V Transceive" must be on (Bank 4, key 3).

## Profile

`radio_profiles.py`: `IC705_CAPS`, transceive menu item 0131, modes LSB, USB,
CW, FM, AM, RTTY, CW-R, RTTY-R, DV. Tuner commands drive an external AH-705.

## Still to confirm on the radio

- S-meter on the new Icom scale (0.8.0-dev): compare with the radio's meter
- DV mode select (CI-V code 17h since 0.8.0-dev)
- memory write and clear (now with confirmation), tuner, GPS, DV data
- power meter percent scale

Use `icom-test-list.txt` and note date and result here.
