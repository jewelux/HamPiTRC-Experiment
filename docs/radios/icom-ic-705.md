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

- the HamTRC keypad layout of 0.8.0-dev, with `icom-test-list.txt`
- S-meter on the new Icom scale: compare with the radio's meter
- DV mode select (mode digit `0`, CI-V code 17h)
- RF power in watts, output power and ALC readings
- auto notch and the notch widths

Use `icom-test-list.txt` and note date and result here.
