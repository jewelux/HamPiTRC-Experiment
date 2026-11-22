# Yaesu FTDX10

## Status

**Assisted field test pending**, as in HamTRC. Every command and encoding is
the one HamTRC's development branch uses for its FTDX10 profile, checked there
against the FTDX10 CAT Operation Reference Manual and Hamlib newcat. Not yet
run on a radio with HamPiTRC.

## Connection

- One USB cable from the FTDX10's USB port to the Raspberry Pi. The radio has a
  dual serial bridge and shows two ports: the **Enhanced COM port** carries
  CAT; the Standard port is for PTT/keying. On the Pi they appear as
  `/dev/ttyUSB0` and `/dev/ttyUSB1`; the stable names are under
  `/dev/serial/by-id/` (the CAT port usually ends in `-if00-port0`).
- Put the CAT port into `config.py`:
  `SERIAL_PORTS = {'ftdx10': '/dev/serial/by-id/...-if00-port0'}`
- On the radio set **CAT RATE** to 38400 (profile default). 4800, 9600 and
  19200 are offered too; change both the radio and Bank 8 `2`.
- There is no CI-V address; Bank 8 `1` says "not available".

## Protocol

Yaesu ASCII CAT, `yaesu_cat.py`: text commands ending in `;`, e.g. `FA;` →
`FA007100000;`. `radio.py` routes every call there because the profile says
`protocol='yaesu'`.

## Keys (HamTRC layout, FTDX10 column)

What differs from the Icoms:

| Bank key | FTDX10 |
|---|---|
| 1 `9`, mode digit `6` | DATA (read: DATA-U, DATA-FM, PSK as DATA; FM-N as FM; AM-N as AM) |
| 2 `1` / `2` double | NR level 1-15, NB level 0-10 (the radio's steps, not percent) |
| 2 `3` | notch on/off (no widths) |
| 2 `4` `5` `6` | PBT and filter: not available |
| 2 `7` | AGC: off, fast, mid, slow, auto (`0` off, `1` auto, `2` fast, `3` slow, `4` mid) |
| 2 `9` | attenuator off, 6, 12, 18 dB |
| 1 `6` | RF power 5-100 W (`PC`) |
| 3 `7`-`9` | band stack: not available (HamTRC hides it on the FTDX10) |
| 4 `3` | monitor: not available |
| 4 `9` | VOX delay 30-3000 ms in the radio's steps |
| 5 | RIT: not available (HamTRC: Icom only) |
| 6 `0` | repeater shift `OS0` (FM only) |
| 6 `2` `5` | tone `CT0`: off, encode and decode (both), encode only (TX) |
| 7 `1` | keyer on/off, double: keyer speed 4-60 WPM |
| 7 `2` | break-in on/off |
| 7 `5` | CW pitch 300-1050 Hz |
| 7 `9` | break-in delay 30-3000 ms |
| 8 `3` | transceive: not available |
| 8 `4` | radio power: short state, long off, double on (sent twice, 1.1 s apart) |
| 8 `5` | radio ID |

S-meter and SWR use Hamlib's FTDX10 calibration (S9 = 130 of 255), as HamTRC;
not yet compared with the radio's own meter. Output power and ALC are said in
percent of full scale.

## First test

Follow `yaesu-ftdx10-test-list.txt`. Start with reading keys only (frequency,
mode, S-meter), then switches, then transmit keys with a dummy load.
