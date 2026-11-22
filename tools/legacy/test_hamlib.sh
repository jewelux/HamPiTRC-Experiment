#!/bin/bash
RIG="rigctl -m 3085 -r /dev/ttyACM0 -s 115200 2>/dev/null"
echo "=== IC-705 hamlib Test ==="
echo -n "Frequency: "; rigctl -m 3085 -r /dev/ttyACM0 -s 115200 f 2>/dev/null
echo -n "Mode: "; rigctl -m 3085 -r /dev/ttyACM0 -s 115200 m 2>/dev/null
echo -n "Split: "; rigctl -m 3085 -r /dev/ttyACM0 -s 115200 s 2>/dev/null
echo -n "VFO A freq: "; rigctl -m 3085 -r /dev/ttyACM0 -s 115200 \get_vfo_info VFOA 2>/dev/null
echo -n "AF gain: "; rigctl -m 3085 -r /dev/ttyACM0 -s 115200 l AF 2>/dev/null
echo -n "RF gain: "; rigctl -m 3085 -r /dev/ttyACM0 -s 115200 l RF 2>/dev/null
echo "=== End ==="
