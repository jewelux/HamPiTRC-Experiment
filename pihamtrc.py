# PiHAMTRC main program v0.7.0
# Key mapping based on the ESP32-HAMTRC IC-7300/IC-705 profile
import evdev, select, sys, time, subprocess
from config import KEYBOARD_NAME, DEVICE_RADIO, AUDIO_NAME, AUDIO_DEVICE, HDMI_NAME, VERSION, CALLSIGN
from speech import say, say_nice as say
import ic705
from keymap import KEY_MAP, BANK_NAMES

bank = 1
pressed = set()
press_time = {}
LONG_PRESS_MS = 500
DOUBLE_CLICK_MS = 250
pending_click_key = None
pending_click_time = 0
input_mode = None
input_digits = ''
volume_level = 5
tuning_speech = True
BAUD_RATES = [4800, 9600, 19200, 38400, 115200]
MODE_DIGITS = {
    '1': 'LSB',
    '2': 'USB',
    '3': 'CW',
    '4': 'FM',
    '5': 'AM',
    '6': 'RTTY',
    '7': 'CW-R',
    '8': 'DV',
    '9': 'RTTY-R',
}

# --- Discover audio device ---
def _find_audio_card_in_proc(name):
    try:
        with open('/proc/asound/cards', 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except OSError:
        return None

    for line in lines:
        if name in line and '[' in line:
            card_num = line.split('[', 1)[0].strip()
            if card_num.isdigit():
                return 'plughw:' + card_num + ',0'
    return None

def find_audio_device():
    device = _find_audio_card_in_proc(AUDIO_NAME)
    if device:
        return device

    result = subprocess.run(['aplay', '-l'], capture_output=True, text=True)
    for line in result.stdout.splitlines():
        if AUDIO_NAME in line and line.startswith('card'):
            card_num = line.split()[1].rstrip(':')
            return 'plughw:' + card_num + ',0'

    device = _find_audio_card_in_proc(HDMI_NAME)
    if device:
        return device

    for line in result.stdout.splitlines():
        if HDMI_NAME in line and line.startswith('card'):
            card_num = line.split()[1].rstrip(':')
            return 'plughw:' + card_num + ',0'
    return AUDIO_DEVICE

# --- Discover keyboard ---
def find_keyboard():
    candidates = []
    for path in evdev.list_devices():
        d = evdev.InputDevice(path)
        if KEYBOARD_NAME in d.name and d.name.strip().endswith('Keyboard'):
            candidates.append(d)
    if candidates:
        dev = min(candidates, key=lambda d: d.path)
        print('Keyboard found: ' + dev.path + ' ' + dev.name)
        return dev
    return None

# --- Numeric entry ---
def start_input(mode):
    global input_mode, input_digits
    input_mode = mode
    input_digits = ''
    if mode == 'freq':
        say('Enter frequency in kilohertz, D to confirm, sharp to cancel')
    elif mode == 'vfoa_freq':
        say('Enter VFO Alpha frequency in kilohertz, D to confirm')
    elif mode == 'vfob_freq':
        say('Enter VFO Bravo frequency in kilohertz, D to confirm')
    elif mode == 'rf_power':
        say('Enter RF power percent, D to confirm, sharp to cancel')
    elif mode == 'monitor_level':
        say('Enter monitor level percent, D to confirm, sharp to cancel')
    elif mode == 'mode':
        say('Enter mode digit, D to confirm')
    elif mode == 'vfoa_mode':
        say('Enter VFO Alpha mode digit, D to confirm')
    elif mode == 'vfob_mode':
        say('Enter VFO Bravo mode digit, D to confirm')
    elif mode == 'bank':
        say('Enter bank number, D to confirm')
    elif mode == 'civ_address':
        say('Enter CI V address decimal, D to confirm')
    elif mode == 'memory_channel':
        say('Enter memory channel, D to confirm')

def cancel_input():
    global input_mode, input_digits
    input_mode = None
    input_digits = ''
    say('Cancelled')

def confirm_input():
    global input_mode, input_digits
    if not input_digits:
        say('No entry')
        return

    if input_mode in ('freq', 'vfoa_freq', 'vfob_freq'):
        khz = int(input_digits)
        hz = khz * 1000
        if hz < 30000 or hz > 470000000:
            say('Frequency out of range')
        else:
            if input_mode == 'vfoa_freq':
                ic705.set_vfoa_freq(hz)
                label = 'VFO Alpha frequency'
            elif input_mode == 'vfob_freq':
                ic705.set_vfob_freq(hz)
                label = 'VFO Bravo frequency'
            else:
                ic705.set_freq(hz)
                label = 'Frequency'
            say(label + ' set to ' + '{:.3f}'.format(hz / 1_000_000) + ' megahertz')
    elif input_mode == 'rf_power':
        percent = int(input_digits)
        if percent < 0 or percent > 100:
            say('RF power out of range')
        else:
            ic705.set_rf_power_percent(percent)
            say('RF power ' + str(percent) + ' percent')
    elif input_mode == 'monitor_level':
        percent = int(input_digits)
        if percent < 0 or percent > 100:
            say('Monitor level out of range')
        else:
            ic705.set_monitor_level_percent(percent)
            say('Monitor level ' + str(percent) + ' percent')
    elif input_mode in ('mode', 'vfoa_mode', 'vfob_mode'):
        mode = MODE_DIGITS.get(input_digits)
        if not mode:
            say('Mode unavailable')
        else:
            if input_mode == 'vfoa_mode':
                ok = ic705.set_vfoa_mode(mode)
                label = 'VFO Alpha mode '
            elif input_mode == 'vfob_mode':
                ok = ic705.set_vfob_mode(mode)
                label = 'VFO Bravo mode '
            else:
                ok = ic705.set_mode(mode)
                label = 'Mode '
            say(label + mode if ok else 'Mode unavailable')
    elif input_mode == 'bank':
        selected = int(input_digits)
        if selected in BANK_NAMES:
            set_bank(selected)
        else:
            say('Bank unavailable')
    elif input_mode == 'civ_address':
        addr = int(input_digits)
        if addr < 0 or addr > 255:
            say('CI V address out of range')
        else:
            ic705.set_civ_address(addr)
            say('CI V address ' + str(addr))
    elif input_mode == 'memory_channel':
        channel = int(input_digits)
        if channel < 0 or channel > 99:
            say('Memory channel out of range')
        else:
            ic705.select_memory_channel(channel)
            say('Memory channel ' + str(channel))

    input_mode = None
    input_digits = ''

def handle_input_key(key):
    global input_digits
    if key in '0123456789':
        max_len = 1 if input_mode in ('mode', 'vfoa_mode', 'vfob_mode', 'bank') else 9
        if input_mode in ('civ_address', 'memory_channel'):
            max_len = 3
        if len(input_digits) < max_len:
            input_digits += key
            say(key)
        else:
            say('Entry full')
        return True
    if key == '#':
        cancel_input()
        return True
    if key == 'D':
        confirm_input()
        return True
    return True

def set_bank(selected):
    global bank
    bank = selected
    say(BANK_NAMES[bank])

def adjust_percent(getter, setter, label, delta):
    value = getter()
    if value is None:
        say(label + ' unavailable')
        return
    value = max(0, min(100, value + delta))
    setter(value)
    say(label + ' ' + str(value) + ' percent')

def adjust_centered(getter, setter, label, delta):
    value = getter()
    if value is None:
        say(label + ' unavailable')
        return
    value = max(-128, min(127, value + delta))
    setter(value)
    say(label + ' ' + str(value))

def adjust_rit(delta):
    value = ic705.get_rit_offset_hz()
    if value is None:
        say('RIT unavailable')
        return
    value = max(-9999, min(9999, value + delta))
    ic705.set_rit_offset_hz(value)
    say('RIT ' + str(value) + ' hertz')

def say_preamp(value):
    if value is None:
        say('Preamp unavailable')
    elif value == 0:
        say('Preamp off')
    else:
        say('Preamp ' + str(value))

def say_att(value):
    if value is None:
        say('Attenuator unavailable')
    elif value == 0:
        say('Attenuator off')
    else:
        say('Attenuator ' + str(value) + ' dB')

def say_agc(value):
    names = {1: 'fast', 2: 'mid', 3: 'slow'}
    if value is None:
        say('AGC unavailable')
    else:
        say('AGC ' + names.get(value, str(value)))

def say_notch_width(value):
    names = {0: 'wide', 1: 'mid', 2: 'narrow'}
    if value is None:
        say('Notch width unavailable')
    else:
        say('Notch width ' + names.get(value, str(value)))

def say_duplex(value):
    if value is None:
        say('Duplex unavailable')
    elif value < 0:
        say('Duplex minus')
    elif value > 0:
        say('Duplex plus')
    else:
        say('Simplex')

def say_tone_mode(value):
    names = {
        0: 'Tone squelch off',
        1: 'Tone',
        2: 'TSQL',
        3: 'DTCS',
        6: 'DTCS transmit',
        7: 'Tone transmit DTCS receive',
        8: 'DTCS transmit TSQL receive',
        9: 'Tone transmit TSQL receive',
    }
    say(names.get(value, 'Tone mode unavailable') if value is not None else 'Tone mode unavailable')

def say_dsql_csql(value):
    names = {0: 'Digital squelch off', 1: 'DSQL', 2: 'CSQL'}
    say(names.get(value, 'Digital squelch unavailable') if value is not None else 'Digital squelch unavailable')

# --- BANK 1 short press ---
def handle_short_bank1(key):
    if key == '0':
        freq = ic705.get_freq_mhz()
        if freq:
            say('Frequency ' + '{:.3f}'.format(freq) + ' megahertz')
        else:
            say('Frequency unavailable')
    elif key == '1':
        tx = ic705.get_tx()
        say('Transmitting' if tx else 'Receiving')
    elif key == '2':
        freq = ic705.get_tx_freq_mhz()
        if freq:
            say('TX frequency ' + '{:.3f}'.format(freq) + ' megahertz')
        else:
            say('TX frequency unavailable')
    elif key == '3':
        lock = ic705.get_lock()
        if lock is None:
            say('Lock unavailable')
        else:
            say('Lock on' if lock else 'Lock off')
    elif key == '4':
        power = ic705.get_power_meter_percent()
        if power is not None:
            say('Power ' + str(power) + ' percent')
        else:
            power = ic705.get_rf_power_percent()
            if power is not None:
                say('RF power ' + str(power) + ' percent')
            else:
                say('Power unavailable')
    elif key == '6':
        power = ic705.get_rf_power_percent()
        if power is not None:
            say('RF power ' + str(power) + ' percent')
        else:
            say('RF power unavailable')
    elif key == '7':
        say(ic705.get_smeter())
    elif key == '8':
        swr = ic705.get_swr()
        if swr is None:
            say('SWR unavailable')
        else:
            say('SWR ' + str(swr))
    elif key == '9':
        mode = ic705.get_mode()
        if mode:
            say('Mode ' + mode)
        else:
            say('Mode unavailable')
    elif key == 'A':
        ic705.select_vfo_a()
        say('VFO Alpha')
    elif key == 'B':
        ic705.select_vfo_b()
        say('VFO Bravo')
    elif key == 'C':
        ic705.swap_vfo()
        say('VFO swapped')
    elif key == 'D':
        say('PiHAMTRC version ' + VERSION + ', ' + CALLSIGN)

# --- BANK 1 long press ---
def handle_long_bank1(key):
    if key == '0':
        start_input('freq')
    elif key == '3':
        lock = ic705.get_lock()
        if lock is not None:
            ic705.set_lock(not lock)
            say('Lock on' if not lock else 'Lock off')
    elif key == '6':
        start_input('rf_power')
    elif key == '9':
        start_input('mode')

# --- BANK 2 short press ---
def handle_short_bank2(key):
    if key == '0':
        say_notch_width(ic705.get_notch_width())
    elif key == '1':
        nr = ic705.get_nr()
        if nr is None:
            say('NR unavailable')
        else:
            say('Noise reduction on' if nr else 'Noise reduction off')
    elif key == '2':
        nb = ic705.get_nb()
        if nb is None:
            say('NB unavailable')
        else:
            say('Noise blanker on' if nb else 'Noise blanker off')
    elif key == '3':
        notch = ic705.get_notch()
        if notch is None:
            say('Notch unavailable')
        else:
            say('Notch on' if notch else 'Notch off')
    elif key == '4':
        value = ic705.get_nr_level_percent()
        say('NR level unavailable' if value is None else 'NR level ' + str(value) + ' percent')
    elif key == '5':
        value = ic705.get_nb_level_percent()
        say('NB level unavailable' if value is None else 'NB level ' + str(value) + ' percent')
    elif key == '6':
        value = ic705.get_pbt1()
        say('PBT one unavailable' if value is None else 'PBT one ' + str(value))
    elif key == '7':
        value = ic705.get_pbt2()
        say('PBT two unavailable' if value is None else 'PBT two ' + str(value))
    elif key == '8':
        shape = ic705.get_filter_shape()
        say('Filter shape unavailable' if shape is None else 'Filter shape ' + shape)
    elif key == '9':
        width = ic705.get_filter_width()
        say('Filter width unavailable' if width is None else 'Filter width ' + str(width))
    elif key == 'A':
        say_preamp(ic705.get_preamp())
    elif key == 'B':
        say_att(ic705.get_att())
    elif key == 'C':
        say_agc(ic705.get_agc())
    elif key == 'D':
        shape = ic705.get_filter_shape()
        width = ic705.get_filter_width()
        if shape is None and width is None:
            say('Filter unavailable')
        else:
            say('Filter ' + str(width) + ', ' + str(shape))

# --- BANK 2 long press ---
def handle_long_bank2(key):
    if key == '0':
        width = ic705.get_notch_width()
        if width is None:
            say('Notch width unavailable')
        else:
            width = 0 if width >= 2 else width + 1
            ic705.set_notch_width(width)
            say_notch_width(width)
    elif key == '1':
        nr = ic705.get_nr()
        if nr is not None:
            ic705.set_nr(not nr)
            say('Noise reduction on' if not nr else 'Noise reduction off')
    elif key == '2':
        nb = ic705.get_nb()
        if nb is not None:
            ic705.set_nb(not nb)
            say('Noise blanker on' if not nb else 'Noise blanker off')
    elif key == '3':
        notch = ic705.get_notch()
        if notch is not None:
            ic705.set_notch(not notch)
            say('Notch on' if not notch else 'Notch off')
    elif key == '4':
        adjust_percent(ic705.get_nr_level_percent, ic705.set_nr_level_percent, 'NR level', 10)
    elif key == '5':
        adjust_percent(ic705.get_nb_level_percent, ic705.set_nb_level_percent, 'NB level', 10)
    elif key == '6':
        adjust_centered(ic705.get_pbt1, ic705.set_pbt1, 'PBT one', 10)
    elif key == '7':
        adjust_centered(ic705.get_pbt2, ic705.set_pbt2, 'PBT two', 10)
    elif key == '8':
        shape = ic705.get_filter_shape()
        if shape is None:
            say('Filter shape unavailable')
        else:
            next_shape = 'soft' if shape == 'sharp' else 'sharp'
            ic705.set_filter_shape(next_shape)
            say('Filter shape ' + next_shape)
    elif key == '9':
        width = ic705.get_filter_width()
        if width is None:
            say('Filter width unavailable')
        else:
            width = 1 if width >= 3 else width + 1
            ic705.set_filter_width(width)
            say('Filter width ' + str(width))
    elif key == 'A':
        value = ic705.get_preamp()
        if value is None:
            say('Preamp unavailable')
        else:
            value = 0 if value >= 2 else value + 1
            ic705.set_preamp(value)
            say_preamp(value)
    elif key == 'B':
        value = ic705.get_att()
        if value is None:
            say('Attenuator unavailable')
        else:
            value = 0 if value else 20
            ic705.set_att(value)
            say_att(value)
    elif key == 'C':
        value = ic705.get_agc()
        if value is None:
            say('AGC unavailable')
        else:
            value = 1 if value >= 3 else value + 1
            ic705.set_agc(value)
            say_agc(value)

# --- BANK 2 double-click ---
def handle_double_bank2(key):
    if key == '0':
        width = ic705.get_notch_width()
        if width is None:
            say('Notch width unavailable')
        else:
            width = 2 if width <= 0 else width - 1
            ic705.set_notch_width(width)
            say_notch_width(width)
    elif key == '4':
        adjust_percent(ic705.get_nr_level_percent, ic705.set_nr_level_percent, 'NR level', -10)
    elif key == '5':
        adjust_percent(ic705.get_nb_level_percent, ic705.set_nb_level_percent, 'NB level', -10)
    elif key == '6':
        adjust_centered(ic705.get_pbt1, ic705.set_pbt1, 'PBT one', -10)
    elif key == '7':
        adjust_centered(ic705.get_pbt2, ic705.set_pbt2, 'PBT two', -10)
    elif key == '9':
        width = ic705.get_filter_width()
        if width is None:
            say('Filter width unavailable')
        else:
            width = 3 if width <= 1 else width - 1
            ic705.set_filter_width(width)
            say('Filter width ' + str(width))
    elif key == 'A':
        value = ic705.get_preamp()
        if value is None:
            say('Preamp unavailable')
        else:
            value = 2 if value <= 0 else value - 1
            ic705.set_preamp(value)
            say_preamp(value)
    elif key == 'C':
        value = ic705.get_agc()
        if value is None:
            say('AGC unavailable')
        else:
            value = 3 if value <= 1 else value - 1
            ic705.set_agc(value)
            say_agc(value)

# --- BANK 3 short press ---
def handle_short_bank3(key):
    if key == '0':
        split = ic705.get_split()
        say('Split on' if split else 'Split off')
    elif key == '1':
        freq = ic705.get_freq_mhz()
        if freq:
            say('VFO Alpha frequency ' + '{:.3f}'.format(freq) + ' megahertz')
        else:
            say('VFO Alpha unavailable')
    elif key == '2':
        freq = ic705.get_vfob_freq()
        if freq:
            say('VFO Bravo frequency ' + '{:.3f}'.format(freq) + ' megahertz')
        else:
            say('VFO Bravo unavailable')
    elif key == '4':
        mode = ic705.get_mode()
        if mode:
            say('VFO Alpha mode ' + mode)
        else:
            say('Mode unavailable')
    elif key == '5':
        mode = ic705.get_vfob_mode()
        if mode:
            say('VFO Bravo mode ' + mode)
        else:
            say('VFO Bravo mode unavailable')
    elif key == '6':
        tx = ic705.get_tx()
        say('Transmitting' if tx else 'Receiving')
    elif key == 'A':
        ic705.select_vfo_a()
        say('VFO Alpha selected')
    elif key == 'B':
        ic705.select_vfo_b()
        say('VFO Bravo selected')
    elif key == 'C':
        ic705.swap_vfo()
        say('VFO swapped')

# --- BANK 3 long press ---
def handle_long_bank3(key):
    if key == '0':
        split = ic705.get_split()
        ic705.set_split(not split)
        say('Split on' if not split else 'Split off')
    elif key == '1':
        ic705.select_vfo_a()
        say('VFO Alpha selected')
    elif key == '2':
        ic705.select_vfo_b()
        say('VFO Bravo selected')
    elif key == '4':
        start_input('vfoa_mode')
    elif key == '5':
        start_input('vfob_mode')

# --- BANK 3 double-click ---
def handle_double_bank3(key):
    if key == '1':
        start_input('vfoa_freq')
    elif key == '2':
        start_input('vfob_freq')

# --- BANK 4 short press ---
def handle_short_bank4(key):
    if key == '0':
        tuner = ic705.get_tuner()
        if tuner is None:
            say('Tuner unavailable')
        elif tuner == 0x02:
            say('Tuner tuning')
        else:
            say('Tuner on' if tuner else 'Tuner off')
    elif key == '1':
        monitor = ic705.get_monitor()
        if monitor is None:
            say('Monitor unavailable')
        else:
            say('Monitor on' if monitor else 'Monitor off')
    elif key == '2':
        value = ic705.get_monitor_level_percent()
        if value is None:
            say('Monitor level unavailable')
        else:
            say('Monitor level ' + str(value) + ' percent')
    elif key == '3':
        transceive = ic705.get_transceive()
        if transceive is None:
            say('Transceive unavailable')
        else:
            say('Transceive on' if transceive else 'Transceive off')

# --- BANK 4 long press ---
def handle_long_bank4(key):
    if key == '0':
        tuner = ic705.get_tuner()
        if tuner is not None:
            ic705.set_tuner(tuner == 0)
            say('Tuner on' if tuner == 0 else 'Tuner off')
    elif key == '1':
        monitor = ic705.get_monitor()
        if monitor is not None:
            ic705.set_monitor(not monitor)
            say('Monitor on' if not monitor else 'Monitor off')
    elif key == '2':
        adjust_percent(ic705.get_monitor_level_percent, ic705.set_monitor_level_percent, 'Monitor level', 10)
    elif key == '3':
        transceive = ic705.get_transceive()
        if transceive is not None:
            ic705.set_transceive(not transceive)
            say('Transceive on' if not transceive else 'Transceive off')

# --- BANK 4 double-click ---
def handle_double_bank4(key):
    if key == '0':
        ic705.start_tune()
        say('Tune')
    elif key == '2':
        adjust_percent(ic705.get_monitor_level_percent, ic705.set_monitor_level_percent, 'Monitor level', -10)

# --- BANK 5 short press ---
def handle_short_bank5(key):
    if key == '0':
        rit = ic705.get_rit()
        offset = ic705.get_rit_offset_hz()
        if rit is None:
            say('RIT unavailable')
        elif offset is None:
            say('RIT on' if rit else 'RIT off')
        else:
            say(('RIT on ' if rit else 'RIT off ') + str(offset) + ' hertz')
    elif key == '1':
        adjust_rit(-10)
    elif key == '2':
        adjust_rit(10)
    elif key == '3':
        ic705.set_rit_offset_hz(0)
        say('RIT zero')
    elif key == '4':
        adjust_rit(-1)
    elif key == '5':
        adjust_rit(1)
    elif key == '9':
        rit = ic705.get_rit()
        if rit is None:
            say('RIT unavailable')
        else:
            say('RIT on' if rit else 'RIT off')

# --- BANK 5 long press ---
def handle_long_bank5(key):
    if key == '0':
        rit = ic705.get_rit()
        if rit is not None:
            ic705.set_rit(not rit)
            say('RIT on' if not rit else 'RIT off')
    elif key == '1':
        adjust_rit(-100)
    elif key == '2':
        adjust_rit(100)
    elif key == '3':
        ic705.set_rit(False)
        say('RIT off')
    elif key == '4':
        adjust_rit(-500)
    elif key == '5':
        adjust_rit(500)

# --- BANK 5 double-click ---
def handle_double_bank5(key):
    if key in ('0', '3'):
        ic705.set_rit_offset_hz(0)
        say('RIT zero')

# --- BANK 6 short press ---
def handle_short_bank6(key):
    if key == '0':
        say_duplex(ic705.get_duplex())
    elif key == '1':
        tone = ic705.get_repeater_tone()
        say('Repeater tone unavailable' if tone is None else 'Repeater tone on' if tone else 'Repeater tone off')
    elif key == '2':
        tsql = ic705.get_tsql()
        say('TSQL unavailable' if tsql is None else 'TSQL on' if tsql else 'TSQL off')
    elif key == '3':
        dtcs = ic705.get_dtcs()
        say('DTCS unavailable' if dtcs is None else 'DTCS on' if dtcs else 'DTCS off')
    elif key == '4':
        say_tone_mode(ic705.get_tone_squelch_mode())
    elif key == '5':
        say_dsql_csql(ic705.get_dsql_csql())

# --- BANK 6 long press ---
def handle_long_bank6(key):
    if key == '0':
        value = ic705.get_duplex()
        if value is None:
            say('Duplex unavailable')
        else:
            next_value = -1 if value == 0 else 1 if value < 0 else 0
            ic705.set_duplex(next_value)
            say_duplex(next_value)
    elif key == '1':
        tone = ic705.get_repeater_tone()
        if tone is not None:
            ic705.set_repeater_tone(not tone)
            say('Repeater tone on' if not tone else 'Repeater tone off')
    elif key == '2':
        tsql = ic705.get_tsql()
        if tsql is not None:
            ic705.set_tsql(not tsql)
            say('TSQL on' if not tsql else 'TSQL off')
    elif key == '3':
        dtcs = ic705.get_dtcs()
        if dtcs is not None:
            ic705.set_dtcs(not dtcs)
            say('DTCS on' if not dtcs else 'DTCS off')
    elif key == '4':
        modes = [0, 1, 2, 3, 6, 7, 8, 9]
        value = ic705.get_tone_squelch_mode()
        if value is None:
            say('Tone mode unavailable')
        else:
            next_value = modes[(modes.index(value) + 1) % len(modes)] if value in modes else 0
            ic705.set_tone_squelch_mode(next_value)
            say_tone_mode(next_value)
    elif key == '5':
        value = ic705.get_dsql_csql()
        if value is None:
            say('Digital squelch unavailable')
        else:
            value = 0 if value >= 2 else value + 1
            ic705.set_dsql_csql(value)
            say_dsql_csql(value)

# --- BANK 6 double-click ---
def handle_double_bank6(key):
    if key == '0':
        value = ic705.get_duplex()
        if value is None:
            say('Duplex unavailable')
        else:
            next_value = 1 if value == 0 else -1 if value > 0 else 0
            ic705.set_duplex(next_value)
            say_duplex(next_value)
    elif key == '5':
        value = ic705.get_dsql_csql()
        if value is None:
            say('Digital squelch unavailable')
        else:
            value = 2 if value <= 0 else value - 1
            ic705.set_dsql_csql(value)
            say_dsql_csql(value)

# --- BANK 7 short press ---
def handle_short_bank7(key):
    if key == '0':
        ic705.select_memory_mode()
        say('Memory mode')
    elif key == '1':
        start_input('memory_channel')
    elif key == '2':
        ic705.memory_copy_to_vfo()
        say('Memory copied to VFO')
    elif key == '3':
        ic705.scan_stop()
        say('Scan stop')
    elif key == '4':
        ic705.scan_program_memory()
        say('Program memory scan')
    elif key == '5':
        ic705.scan_memory()
        say('Memory scan')
    elif key == '6':
        value = ic705.get_dv_data_tx()
        say('DV data TX unavailable' if value is None else 'DV data TX auto' if value else 'DV data TX PTT')
    elif key == '7':
        value = ic705.get_dv_fast_data()
        say('DV fast data unavailable' if value is None else 'DV fast data on' if value else 'DV fast data off')
    elif key == '8':
        value = ic705.get_gps_select()
        names = {0: 'GPS off', 1: 'GPS on', 3: 'GPS manual'}
        say(names.get(value, 'GPS unavailable') if value is not None else 'GPS unavailable')
    elif key == '9':
        value = ic705.get_gps_tx_mode()
        names = {0: 'GPS TX off', 1: 'GPS TX DPRS', 2: 'GPS TX NMEA'}
        say(names.get(value, 'GPS TX unavailable') if value is not None else 'GPS TX unavailable')

# --- BANK 7 long press ---
def handle_long_bank7(key):
    if key == '0':
        ic705.memory_write()
        say('Memory write')
    elif key == '2':
        ic705.memory_clear()
        say('Memory clear')
    elif key == '4':
        ic705.scan_program()
        say('Program scan')
    elif key == '5':
        ic705.scan_select_memory()
        say('Select memory scan')
    elif key == '6':
        value = ic705.get_dv_data_tx()
        if value is not None:
            value = 0 if value else 1
            ic705.set_dv_data_tx(value)
            say('DV data TX auto' if value else 'DV data TX PTT')
    elif key == '7':
        value = ic705.get_dv_fast_data()
        if value is not None:
            ic705.set_dv_fast_data(not value)
            say('DV fast data on' if not value else 'DV fast data off')
    elif key == '8':
        value = ic705.get_gps_select()
        if value is not None:
            next_value = 1 if value == 0 else 3 if value == 1 else 0
            ic705.set_gps_select(next_value)
            names = {0: 'GPS off', 1: 'GPS on', 3: 'GPS manual'}
            say(names[next_value])
    elif key == '9':
        value = ic705.get_gps_tx_mode()
        if value is not None:
            next_value = 0 if value >= 2 else value + 1
            ic705.set_gps_tx_mode(next_value)
            names = {0: 'GPS TX off', 1: 'GPS TX DPRS', 2: 'GPS TX NMEA'}
            say(names[next_value])

# --- BANK 8 short press ---
def handle_short_bank8(key):
    if key == '1':
        say('CI V address ' + str(ic705.get_civ_address()))
    elif key == '2':
        say('Baud rate ' + str(ic705.get_baudrate()))

# --- BANK 8 long press ---
def handle_long_bank8(key):
    if key == '1':
        start_input('civ_address')
    elif key == '2':
        baud = ic705.get_baudrate()
        idx = BAUD_RATES.index(baud) if baud in BAUD_RATES else len(BAUD_RATES) - 1
        baud = BAUD_RATES[(idx + 1) % len(BAUD_RATES)]
        ic705.set_baudrate(baud)
        say('Baud rate ' + str(baud))

# --- BANK 8 double-click ---
def handle_double_bank8(key):
    if key == '2':
        baud = ic705.get_baudrate()
        idx = BAUD_RATES.index(baud) if baud in BAUD_RATES else len(BAUD_RATES) - 1
        baud = BAUD_RATES[(idx - 1) % len(BAUD_RATES)]
        ic705.set_baudrate(baud)
        say('Baud rate ' + str(baud))

# --- BANK 9 short press ---
def handle_short_bank9(key):
    global volume_level
    if key == 'A':
        say('Icom IC-705 profile')
    elif key == '1':
        say('Profile next unavailable')
    elif key == '2':
        say('Profile previous unavailable')
    elif key == '4':
        say('Tuning speech on' if tuning_speech else 'Tuning speech off')
    elif key == '5':
        say('Volume ' + str(volume_level))
    elif key == '7':
        volume_level = 1
        say('Volume one')
    elif key == '8':
        volume_level = 2
        say('Volume two')
    elif key == '9':
        volume_level = 3
        say('Volume three')

# --- BANK 9 long press ---
def handle_long_bank9(key):
    global tuning_speech, volume_level
    if key == '4':
        tuning_speech = not tuning_speech
        say('Tuning speech on' if tuning_speech else 'Tuning speech off')
    elif key == '7':
        volume_level = max(1, volume_level - 1)
        say('Volume ' + str(volume_level))
    elif key == '8':
        volume_level = min(9, volume_level + 1)
        say('Volume ' + str(volume_level))

# --- Switch bank ---
def handle_bank_next():
    global bank
    bank = (bank % 9) + 1
    if bank not in BANK_NAMES:
        bank = 1
    say(BANK_NAMES[bank])

def handle_bank_prev():
    global bank
    bank = bank - 1
    if bank < 1 or bank not in BANK_NAMES:
        bank = max(BANK_NAMES.keys())
    say(BANK_NAMES[bank])

# --- Main dispatch ---
def handle_short(key):
    if key == '*':
        say(BANK_NAMES[bank])
        return
    if bank == 1:
        handle_short_bank1(key)
    elif bank == 2:
        handle_short_bank2(key)
    elif bank == 3:
        handle_short_bank3(key)
    elif bank == 4:
        handle_short_bank4(key)
    elif bank == 5:
        handle_short_bank5(key)
    elif bank == 6:
        handle_short_bank6(key)
    elif bank == 7:
        handle_short_bank7(key)
    elif bank == 8:
        handle_short_bank8(key)
    elif bank == 9:
        handle_short_bank9(key)

def handle_long(key):
    if key == '*':
        start_input('bank')
        return
    if bank == 1:
        handle_long_bank1(key)
    elif bank == 2:
        handle_long_bank2(key)
    elif bank == 3:
        handle_long_bank3(key)
    elif bank == 4:
        handle_long_bank4(key)
    elif bank == 5:
        handle_long_bank5(key)
    elif bank == 6:
        handle_long_bank6(key)
    elif bank == 7:
        handle_long_bank7(key)
    elif bank == 8:
        handle_long_bank8(key)
    elif bank == 9:
        handle_long_bank9(key)

def handle_double(key):
    if bank == 2:
        handle_double_bank2(key)
    elif bank == 3:
        handle_double_bank3(key)
    elif bank == 4:
        handle_double_bank4(key)
    elif bank == 5:
        handle_double_bank5(key)
    elif bank == 6:
        handle_double_bank6(key)
    elif bank == 8:
        handle_double_bank8(key)

def flush_pending_click():
    global pending_click_key, pending_click_time
    if pending_click_key is not None:
        key = pending_click_key
        pending_click_key = None
        pending_click_time = 0
        handle_short(key)

def handle_released_key(key, duration_ms):
    global pending_click_key, pending_click_time
    now = time.time()

    if input_mode is not None:
        flush_pending_click()
        handle_input_key(key)
    elif duration_ms >= LONG_PRESS_MS:
        flush_pending_click()
        handle_long(key)
    elif pending_click_key == key and (now - pending_click_time) * 1000 <= DOUBLE_CLICK_MS:
        pending_click_key = None
        pending_click_time = 0
        handle_double(key)
    else:
        flush_pending_click()
        pending_click_key = key
        pending_click_time = now

# --- Main program ---
def main():
    audio = find_audio_device()
    print('Audio device: ' + audio)
    import speech
    speech.AUDIO_DEVICE = audio

    try:
        ic705.connect(DEVICE_RADIO)
    except Exception as e:
        print('IC-705 not found: ' + str(e))
        say('IC-705 not connected')
        sys.exit(1)

    say('PiHAMTRC ready, version ' + VERSION)
    freq = ic705.get_freq_mhz()
    mode = ic705.get_mode()
    if freq is None and mode is None:
        say('IC-705 connected, status unavailable')
    elif freq is None:
        say('IC-705 connected, ' + str(mode) + ', frequency unavailable')
    elif mode is None:
        say('IC-705 connected, mode unavailable, frequency ' + '{:.3f}'.format(freq) + ' megahertz')
    else:
        say('IC-705 connected, ' + str(mode) + ', frequency ' + '{:.3f}'.format(freq) + ' megahertz')

    dev = find_keyboard()
    if dev is None:
        say('Keyboard not found')
        sys.exit(1)

    say('Ready')

    while True:
        timeout = 0.05
        if pending_click_key is not None:
            elapsed = (time.time() - pending_click_time) * 1000
            remaining = max(0, DOUBLE_CLICK_MS - elapsed) / 1000
            timeout = min(timeout, remaining)

        readable, _, _ = select.select([dev.fd], [], [], timeout)
        if readable:
            for event in dev.read():
                if event.type == evdev.ecodes.EV_KEY:
                    key_event = evdev.categorize(event)
                    if key_event.keystate == 1:
                        pressed.add(key_event.keycode)
                        press_time[key_event.keycode] = time.time()
                    elif key_event.keystate == 0:
                        pressed.discard(key_event.keycode)
                        if key_event.keycode in press_time:
                            duration = (time.time() - press_time.pop(key_event.keycode)) * 1000
                            if key_event.keycode in KEY_MAP:
                                handle_released_key(KEY_MAP[key_event.keycode], duration)
                    if 'KEY_NUMLOCK' in pressed and 'KEY_TAB' in pressed:
                        say('PiHAMTRC shutting down')
                        sys.exit(0)

        if pending_click_key is not None and (time.time() - pending_click_time) * 1000 > DOUBLE_CLICK_MS:
            flush_pending_click()

if __name__ == '__main__':
    main()
