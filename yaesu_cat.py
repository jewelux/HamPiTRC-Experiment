# HamPiTRC - Yaesu ASCII CAT (FTDX10 family), after HamTRC's
# protocol_ops_ascii.cpp and cat_setting_codec.cpp (development branch).
#
# Text commands ending in ';', e.g. "FA;" -> "FA007100000;". The functions
# have the names civ.py uses, so radio.py can route a call to either module;
# a function a radio lacks is simply not here, and radio.py says "not
# available". Every command and encoding below is the one HamTRC checked
# against the FTDX10 CAT manual and Hamlib newcat; HamTRC lists the FTDX10 as
# "assisted field test pending", and so does HamPiTRC.

import time

import serial

from radio_profiles import MODE_CODES

BAUDRATE = 38400
TIMEOUT = 0.5
RETRIES = 2

_ser = None

# MD0<code>: HamTRC kYaesuAsciiModes. Read only: B FM-N, D AM-N, A/C/E/F data.
MODE_TO_CODE = {'LSB': '1', 'USB': '2', 'CW': '3', 'FM': '4', 'AM': '5',
                'RTTY': '6', 'CW-R': '7', 'DATA': '8', 'RTTY-R': '9'}
CODE_TO_MODE = {v: k for k, v in MODE_TO_CODE.items()}
CODE_TO_MODE.update({'B': 'FM', 'D': 'AM', 'A': 'DATA', 'C': 'DATA', 'E': 'DATA', 'F': 'DATA'})

# S-meter SM0 000..255 -> dB relative to S9: Hamlib newcat yaesu_default_str_cal.
SMETER_CAL = ((0, -54), (26, -42), (51, -30), (81, -18), (105, -9), (130, 0),
              (157, 12), (186, 25), (203, 35), (237, 50), (255, 60))
# SWR RM6 000..255 -> SWR x100: Hamlib FTDX10_SWR_CAL.
SWR_CAL = ((0, 100), (26, 120), (52, 150), (89, 200), (126, 300), (173, 400), (236, 500), (255, 2500))

# 50 CTCSS tones in tenths of a Hz; CN00nnn is the index (the CAT manual's table).
CTCSS_TONES = (
    670, 693, 719, 744, 770, 797, 825, 854, 885, 915,
    948, 974, 1000, 1035, 1072, 1109, 1148, 1188, 1230, 1273,
    1318, 1365, 1413, 1462, 1514, 1567, 1598, 1622, 1655, 1679,
    1713, 1738, 1773, 1799, 1835, 1862, 1899, 1928, 1966, 1995,
    2035, 2065, 2107, 2181, 2257, 2291, 2336, 2418, 2503, 2541,
)


# --- link --------------------------------------------------------------------

def configure(baudrate, **_ignored):
    global BAUDRATE
    BAUDRATE = int(baudrate)


def connect(port):
    global _ser
    _ser = serial.Serial(port, BAUDRATE, timeout=0.1)
    time.sleep(0.1)


def disconnect():
    global _ser
    if _ser is not None:
        try:
            _ser.close()
        except (serial.SerialException, AttributeError):
            pass
    _ser = None


def is_connected():
    return _ser is not None


def get_baudrate():
    return BAUDRATE


def set_baudrate(baud):
    global BAUDRATE
    BAUDRATE = int(baud)
    if _ser is not None:
        _ser.baudrate = BAUDRATE


def _send(cmd):
    try:
        _ser.reset_input_buffer()
        _ser.write(cmd.encode('ascii'))
    except serial.SerialException:
        return False
    return True


def _read_line(timeout):
    deadline = time.time() + timeout
    buf = b''
    while time.time() < deadline:
        try:
            b = _ser.read(1)
        except serial.SerialException:
            return None
        if not b:
            continue
        if b == b';':
            return buf.decode('ascii', errors='replace')
        buf += b
    return None


def query(cmd, prefix):
    """Send cmd and return what follows prefix in the reply, or None."""
    for _ in range(RETRIES):
        if not _send(cmd):
            return None
        deadline = time.time() + TIMEOUT
        while time.time() < deadline:
            line = _read_line(deadline - time.time())
            if line is None:
                break
            if line.startswith(prefix):
                return line[len(prefix):]
            if line == '?':
                break       # the radio refused the command
        time.sleep(0.05)
    return None


def command(cmd):
    """A set command; the radio answers nothing."""
    ok = _send(cmd)
    time.sleep(0.04)
    return ok


def _digits(text, n=None):
    if text is None or not text.isdigit() or (n is not None and len(text) != n):
        return None
    return int(text)


def _on_off(cmd, prefix):
    v = query(cmd, prefix)
    if v is None or not v.isdigit():
        return None
    return int(v) != 0


# --- frequency, mode, VFO ------------------------------------------------------

def get_freq():
    return _digits(query('FA;', 'FA'))


def get_freq_mhz():
    hz = get_freq()
    return None if hz is None else hz / 1_000_000


def set_freq(hz):
    command('FA%09d;' % int(hz))


def get_mode():
    code = query('MD0;', 'MD0')
    return CODE_TO_MODE.get(code) if code else None


def get_mode_filter():
    return get_mode(), None


def set_mode(mode_name, filt=1):
    code = MODE_TO_CODE.get(mode_name.upper())
    if code is None:
        return False
    command('MD0%s;' % code)
    return True


def get_vfo_is_a():
    v = query('VS;', 'VS')
    return None if v not in ('0', '1') else v == '0'


def select_vfo_a():
    command('VS0;')


def select_vfo_b():
    command('VS1;')


def swap_vfo():
    command('SV;')


def get_vfob_freq():
    hz = _digits(query('FB;', 'FB'))
    return None if hz is None else hz / 1_000_000


def set_vfoa_freq(hz):
    command('FA%09d;' % int(hz))


def set_vfob_freq(hz):
    command('FB%09d;' % int(hz))


def _on_vfo(vfo_a, fn):
    """Run fn with VFO A or B selected, then go back (HamTRC queryVfoMode)."""
    prior = get_vfo_is_a()
    if prior is None:
        return None
    if prior != vfo_a:
        command('VS0;' if vfo_a else 'VS1;')
        time.sleep(0.04)
    try:
        return fn()
    finally:
        if prior != vfo_a:
            command('VS0;' if prior else 'VS1;')


def get_vfob_mode():
    return _on_vfo(False, get_mode)


def set_vfoa_mode(mode_name, filt=1):
    return _on_vfo(True, lambda: set_mode(mode_name))


def set_vfob_mode(mode_name, filt=1):
    return _on_vfo(False, lambda: set_mode(mode_name))


def get_split():
    return _on_off('ST;', 'ST')


def set_split(on):
    command('ST1;' if on else 'ST0;')


def get_tx():
    """TX;: 0 receive, 1 CAT TX, 2 radio TX."""
    v = query('TX;', 'TX')
    return v in ('1', '2')


def get_tx_freq():
    if get_split():
        return _digits(query('FB;', 'FB'))
    return get_freq()


def get_tx_freq_mhz():
    hz = get_tx_freq()
    return None if hz is None else hz / 1_000_000


def get_lock():
    v = query('LK;', 'LK')
    return None if not v else v[0] != '0'


def set_lock(on):
    command('LK1;' if on else 'LK0;')


# --- meters --------------------------------------------------------------------

def _meter(cmd, prefix):
    """RMnPPP000 or three digits (HamTRC yaesuMeterDecode)."""
    v = query(cmd, prefix)
    if v is None or not v.isdigit():
        return None
    if len(v) == 6:
        v = v[:3]
    if len(v) != 3:
        return None
    return int(v) if int(v) <= 255 else None


def _interpolate(cal, raw):
    if raw <= cal[0][0]:
        return cal[0][1]
    for (r0, v0), (r1, v1) in zip(cal, cal[1:]):
        if raw <= r1:
            return v0 + (raw - r0) * (v1 - v0) / (r1 - r0)
    return cal[-1][1]


def smeter_text(raw):
    db = _interpolate(SMETER_CAL, raw)
    if db < 0:
        return 'S %d' % max(0, 9 + round(db / 6))
    tens = min(6, round(db / 10))
    return 'S 9' if tens == 0 else 'S 9 plus %d' % (tens * 10)


def get_smeter():
    v = query('SM0;', 'SM0')
    if v is None or not v.isdigit():
        return 'S meter unavailable'
    return smeter_text(int(v))


def get_swr():
    raw = _meter('RM6;', 'RM6')
    if raw is None:
        return None
    return max(1.0, round(_interpolate(SWR_CAL, raw) / 100, 1))


def get_power_meter_percent():
    raw = _meter('RM5;', 'RM5')
    return None if raw is None else round(raw * 100 / 255)


def get_alc_meter_percent():
    raw = _meter('RM4;', 'RM4')
    return None if raw is None else round(raw * 100 / 255)


# --- RF power PC in watts, 5..100 ------------------------------------------------

def get_rf_power_watts():
    v = query('PC;', 'PC')
    if v is None or not v.isdigit():
        return None
    return int(v[:3]) if len(v) >= 3 else int(v)


def set_rf_power_watts(watts):
    command('PC%03d;' % max(5, min(100, int(watts))))


# --- receive ---------------------------------------------------------------------

def get_nr():
    return _on_off('NR0;', 'NR0')


def set_nr(on):
    command('NR01;' if on else 'NR00;')


def get_nr_level():
    """RL0nn, 1..15."""
    v = _digits(query('RL0;', 'RL0'), 2)
    return v if v is not None and 1 <= v <= 15 else None


def set_nr_level(value):
    command('RL0%02d;' % max(1, min(15, int(value))))


def get_nb():
    return _on_off('NB0;', 'NB0')


def set_nb(on):
    command('NB01;' if on else 'NB00;')


def get_nb_level():
    """NL0nnn, 0..10."""
    v = _digits(query('NL0;', 'NL0'), 3)
    return v if v is not None and v <= 10 else None


def set_nb_level(value):
    command('NL0%03d;' % max(0, min(10, int(value))))


def get_notch():
    return _on_off('BP00;', 'BP00')


def set_notch(on):
    command('BP0001;' if on else 'BP0000;')


def get_auto_notch():
    return _on_off('BC0;', 'BC0')


def set_auto_notch(on):
    command('BC01;' if on else 'BC00;')


def get_preamp():
    """PA0n: 0 IPO, 1 AMP1, 2 AMP2."""
    v = _digits(query('PA0;', 'PA0'), 1)
    return v if v is not None and v <= 2 else None


def set_preamp(level):
    command('PA0%d;' % max(0, min(2, int(level))))


def get_att():
    """RA0n: 0 off, 1..3 = 6, 12, 18 dB. Returns the step."""
    v = _digits(query('RA0;', 'RA0'), 1)
    return v if v is not None and v <= 3 else None


def set_att(step):
    command('RA0%d;' % max(0, min(3, int(step))))


def get_agc():
    """GT0n: 0 off, 1 fast, 2 mid, 3 slow, 4 auto (5, 6 read as auto)."""
    v = _digits(query('GT0;', 'GT0'), 1)
    if v is None or v > 6:
        return None
    return min(v, 4)


def set_agc(code):
    command('GT0%d;' % max(0, min(4, int(code))))


# --- tuner -----------------------------------------------------------------------------

def get_tuner():
    """AC: 0 off, 1 on, 2 tuning."""
    v = query('AC;', 'AC')
    if v is None or not v.isdigit():
        return None
    return int(v[-1]) if int(v[-1]) <= 2 else None


def set_tuner(on):
    command('AC001;' if on else 'AC000;')


def start_tune():
    command('AC002;')


# --- repeater and tone ---------------------------------------------------------------

def get_duplex():
    """OS0n: 0 simplex, 1 plus, 2 minus (FM only)."""
    v = _digits(query('OS0;', 'OS0'), 1)
    return {0: 0, 1: 1, 2: -1}.get(v)


def set_duplex(value):
    command({0: 'OS00;', 1: 'OS01;', -1: 'OS02;'}.get(int(value), 'OS00;'))


def _tone_code():
    """CT0n: 0 off, 1 encode and decode, 2 encode only."""
    v = _digits(query('CT0;', 'CT0'), 1)
    return v if v is not None and v <= 3 else None


# civ.py's names: repeater tone = encode only, TSQL = encode and decode.
def get_repeater_tone():
    c = _tone_code()
    return None if c is None else c == 2


def set_repeater_tone(on):
    if on:
        command('CT02;')
    elif _tone_code() == 2:
        command('CT00;')


def get_tsql():
    c = _tone_code()
    return None if c is None else c == 1


def set_tsql(on):
    if on:
        command('CT01;')
    elif _tone_code() == 1:
        command('CT00;')


def get_ctcss_tenths():
    v = _digits(query('CN00;', 'CN00'), 3)
    return CTCSS_TONES[v] if v is not None and v < len(CTCSS_TONES) else None


def set_ctcss_tenths(tenths):
    tone = min(CTCSS_TONES, key=lambda t: abs(t - tenths))
    command('CN00%03d;' % CTCSS_TONES.index(tone))


# --- transmit ------------------------------------------------------------------------

# VD and SD steps 00..33: 30, 50, 100, 150, 200, 250, then 300..3000 by 100 ms.
DELAY_STEPS = (30, 50, 100, 150, 200, 250) + tuple(range(300, 3001, 100))


def delay_step_of(ms):
    return min(range(len(DELAY_STEPS)), key=lambda i: abs(DELAY_STEPS[i] - ms))


def get_proc():
    """PR0n: 0 off, 1 on (2 also on: the FTDX10 manual's value)."""
    v = query('PR0;', 'PR0')
    if not v or v[0] not in '012':
        return None
    return v[0] != '0'


def set_proc(on):
    command('PR01;' if on else 'PR00;')


def _level(code):
    v = _digits(query(code + ';', code))
    return v if v is not None and v <= 100 else None


def get_proc_level_percent():
    return _level('PL')


def set_proc_level_percent(value):
    command('PL%03d;' % max(0, min(100, int(value))))


def get_mic_gain_percent():
    return _level('MG')


def set_mic_gain_percent(value):
    command('MG%03d;' % max(0, min(100, int(value))))


def get_vox():
    v = _digits(query('VX;', 'VX'))
    return None if v is None or v > 1 else v == 1


def set_vox(on):
    command('VX1;' if on else 'VX0;')


def get_vox_gain_percent():
    return _level('VG')


def set_vox_gain_percent(value):
    command('VG%03d;' % max(0, min(100, int(value))))


def get_vox_delay_ms():
    v = _digits(query('VD;', 'VD'))
    return DELAY_STEPS[v] if v is not None and v < len(DELAY_STEPS) else None


def set_vox_delay_ms(ms):
    command('VD%02d;' % delay_step_of(ms))


# --- CW --------------------------------------------------------------------------------

def get_break_in():
    """BI: 0 off, 1 on."""
    v = _digits(query('BI;', 'BI'), 1)
    return v if v in (0, 1) else None


def set_break_in(value):
    command('BI1;' if value else 'BI0;')


def get_keyer():
    v = _digits(query('KR;', 'KR'), 1)
    return None if v not in (0, 1) else v == 1


def set_keyer(on):
    command('KR1;' if on else 'KR0;')


def get_cw_speed():
    """KS, 4..60 WPM."""
    v = _digits(query('KS;', 'KS'), 3)
    return v if v is not None and v <= 60 else None


def set_cw_speed(wpm):
    command('KS%03d;' % max(4, min(60, int(wpm))))


def get_cw_pitch_hz():
    """KP 00..75 = 300..1050 Hz."""
    v = _digits(query('KP;', 'KP'), 2)
    return 300 + v * 10 if v is not None and v <= 75 else None


def set_cw_pitch_hz(hz):
    hz = max(300, min(1050, int(hz)))
    command('KP%02d;' % ((hz - 300 + 5) // 10))


def get_cw_delay_ms():
    v = _digits(query('SD;', 'SD'), 2)
    return DELAY_STEPS[v] if v is not None and v < len(DELAY_STEPS) else None


def set_cw_delay_ms(ms):
    command('SD%02d;' % delay_step_of(ms))


# --- radio ------------------------------------------------------------------------------

def get_power_state():
    v = _digits(query('PS;', 'PS'))
    return None if v is None else v != 0


def set_power_state(on):
    if on:
        # FTDX10/101: power-on needs the command twice, about a second apart.
        command('PS1;')
        time.sleep(1.1)
        command('PS1;')
    else:
        command('PS0;')


def get_radio_id():
    return query('ID;', 'ID')
