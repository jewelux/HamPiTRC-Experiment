# HamPiTRC Quickstart

The short path from a fresh Raspberry Pi to a talking radio. Details are in
[builder-guide.md](builder-guide.md).

## You need

- Raspberry Pi with Raspberry Pi OS / Debian (tested on a Pi 5)
- Icom IC-705, IC-7300, IC-7100 or Yaesu FTDX10 with a USB cable
- an external USB numeric keypad (see "Why an external keypad" in the user guide)
- speakers or headphones on HDMI, USB audio or the Pi's audio output

## 1. Install

```sh
sudo apt install python3-venv python3-dev build-essential alsa-utils git
git clone https://github.com/jewelux/HamPiTRC-Experiment ~/pihamtrc
cd ~/pihamtrc
python3 -m venv venv
. venv/bin/activate
python -m pip install -r requirements.txt
sudo usermod -aG dialout,input $USER     # then log out and in again
```

## 2. Voice

Download `en_US-lessac-medium.onnx` and `en_US-lessac-medium.onnx.json` from
the [Piper voices](https://huggingface.co/rhasspy/piper-voices) into
`~/piper-voices/`. Observe the voice licence.

## 3. Radio

On the radio, set the USB CI-V port so that address and baud rate match the
profile:

| Radio | CI-V address | Baud rate |
| --- | --- | --- |
| IC-705 | A4h | 115200 |
| IC-7300 | 94h | 115200 |
| IC-7100 | 88h | 19200 |
| FTDX10 | – (CAT) | 38400 (menu CAT RATE) |

Find the serial port: `ls /dev/ttyACM* /dev/ttyUSB* /dev/serial/by-id/`.

## 4. config.py

```python
RADIO_PROFILE = 'ic705'            # or 'ic7300', 'ic7100', 'ftdx10'
SERIAL_PORTS  = {'ic705': '/dev/ttyACM0'}
KEYBOARD_NAME = 'HCT'              # part of your keypad's name, '' = any keypad
PIPER_MODEL   = '/home/pi/piper-voices/en_US-lessac-medium.onnx'
CALLSIGN      = 'LX1WJ'
```

`python -m evdev.evtest` lists input device names.

## 5. Run

```sh
. venv/bin/activate
python -B pihamtrc.py
```

You hear "PiHAMTRC ready" and the radio, mode and frequency. Bank 1 `0`
short speaks the frequency. `D` long turns on help mode: every key then says
what it does. `NumLock` + `Tab` exits. All keys: `docs/keypad-map.md`.

## 6. Check without a radio

```sh
python -m unittest discover -s tests
```
