# HamPiTRC - Icom CI-V protocol (was ic705.py)
#
# One module for every Icom radio. The active profile (radio_profiles.py)
# sets the CI-V address, baud rate and the transceive menu item through
# configure(); radio.py checks the profile's capabilities before a call
# reaches this module.
import serial, time

from radio_profiles import MODE_CODES

CIV_ADDR = 0xA4
CIV_CTRL = 0xE0
BAUDRATE = 115200
TRANSCEIVE_MENU_ITEM = 0x0131
QUERY_RETRIES = 3
QUERY_TIMEOUT = 0.8

MODE_NAMES = {v: k for k, v in MODE_CODES.items()}

# Icom S-meter scale (15 02): 0 = S0, 120 = S9, 241 = S9 + 60 dB
# (IC-7300 / IC-705 CI-V reference, Hamlib; same as HamTRC civ_smeter.cpp).
SMETER_RAW_S9 = 120
SMETER_RAW_S9_PLUS_60 = 241

_ser = None

def configure(civ_addr, baudrate, transceive_menu_item=0, vox_delay_menu_item=0):
    """Take the address, baud rate and menu items of the active profile."""
    global CIV_ADDR, BAUDRATE, TRANSCEIVE_MENU_ITEM, VOX_DELAY_MENU_ITEM
    CIV_ADDR = max(0, min(255, int(civ_addr)))
    BAUDRATE = int(baudrate)
    TRANSCEIVE_MENU_ITEM = int(transceive_menu_item)
    VOX_DELAY_MENU_ITEM = int(vox_delay_menu_item)

def connect(port):
    global _ser
    _ser = serial.Serial(port, BAUDRATE, timeout=0.5)
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

def set_civ_address(addr):
    global CIV_ADDR
    CIV_ADDR = max(0, min(255, int(addr)))

def get_civ_address():
    return CIV_ADDR

def set_baudrate(baud):
    global BAUDRATE
    BAUDRATE = int(baud)
    if _ser is not None:
        _ser.baudrate = BAUDRATE

def get_baudrate():
    return BAUDRATE

def _flush():
    if _ser:
        try:
            _ser.reset_input_buffer()
        except serial.SerialException:
            pass

def _send(cmd, payload=None):
    data = [0xFE, 0xFE, CIV_ADDR, CIV_CTRL, cmd]
    if payload: data.extend(payload)
    data.append(0xFD)
    try:
        _ser.write(bytes(data))
    except serial.SerialException:
        return False
    return True

def _read(timeout=0.5):
    deadline = time.time() + timeout
    buf = []
    preamble = 0
    in_msg = False
    while time.time() < deadline:
        try:
            b = _ser.read(1)
        except serial.SerialException:
            return None
        if not b: continue
        v = b[0]
        if not in_msg:
            if v == 0xFE:
                preamble += 1
                if preamble >= 2: in_msg = True; buf = []
            else: preamble = 0
        else:
            if v == 0xFD: return buf
            buf.append(v)
    return None

def _query_once(cmd, payload=None):
    if not _send(cmd, payload):
        return None
    deadline = time.time() + QUERY_TIMEOUT
    while time.time() < deadline:
        resp = _read(0.1)
        if not resp or len(resp) < 3: continue
        if resp[0] == CIV_CTRL and resp[1] == CIV_ADDR:
            if resp[2] in (0xFB, 0xFA): continue
            if resp[2] != cmd: continue
            if payload and resp[3:3 + len(payload)] != payload: continue
            return resp[3:]
    return None

def _query(cmd, payload=None):
    for attempt in range(QUERY_RETRIES):
        _flush()
        resp = _query_once(cmd, payload)
        if resp is not None:
            return resp
        if attempt < QUERY_RETRIES - 1:
            time.sleep(0.08)
    return None

def _bcd_to_freq(data):
    hz = 0
    mul = 1
    for b in data:
        hz += (b & 0x0F) * mul; mul *= 10
        hz += ((b >> 4) & 0x0F) * mul; mul *= 10
    return hz

def _freq_to_bcd(hz):
    bcd = []
    for _ in range(5):
        d1 = hz % 10; hz //= 10
        d2 = hz % 10; hz //= 10
        bcd.append((d2 << 4) | d1)
    return bcd

def _level_to_bcd(value):
    value = max(0, min(255, int(value)))
    hundreds = value // 100
    tens = (value // 10) % 10
    ones = value % 10
    return [hundreds, (tens << 4) | ones]

def _query_14_value(subcmd):
    resp = _query(0x14, [subcmd])
    if resp and len(resp) >= 3 and resp[0] == subcmd:
        value = (resp[1] & 0x0F) * 100 + ((resp[2] >> 4) & 0x0F) * 10 + (resp[2] & 0x0F)
        if value <= 255:
            return value
    return None

def _set_14_value(subcmd, value):
    _flush()
    _send(0x14, [subcmd] + _level_to_bcd(value))
    time.sleep(0.05)
    _ser.reset_input_buffer()

def _raw_to_percent(raw):
    if raw is None:
        return None
    return round(max(0, min(255, raw)) * 100 / 255)

def _percent_to_raw(percent):
    return round(max(0, min(100, int(percent))) * 255 / 100)

def _query_menu_byte(group, item):
    resp = _query(0x1A, [group, (item >> 8) & 0xFF, item & 0xFF])
    if resp and len(resp) >= 4 and resp[0] == group and resp[1] == ((item >> 8) & 0xFF) and resp[2] == (item & 0xFF):
        return resp[3]
    return None

def _set_menu_byte(group, item, value):
    _flush()
    _send(0x1A, [group, (item >> 8) & 0xFF, item & 0xFF, value])
    time.sleep(0.05)
    _ser.reset_input_buffer()

def _query_16_byte(subcmd):
    resp = _query(0x16, [subcmd])
    if resp and len(resp) >= 2 and resp[0] == subcmd:
        return resp[1]
    return None

def _set_16_byte(subcmd, value):
    _flush()
    _send(0x16, [subcmd, value])
    time.sleep(0.05)
    _ser.reset_input_buffer()

def _query_1c_byte(subcmd):
    resp = _query(0x1C, [subcmd])
    if resp and len(resp) >= 2 and resp[0] == subcmd:
        return resp[1]
    return None

def _set_1c_byte(subcmd, value):
    _flush()
    _send(0x1C, [subcmd, value])
    time.sleep(0.05)
    _ser.reset_input_buffer()

def get_freq():
    resp = _query(0x03)
    if resp and len(resp) >= 5:
        return _bcd_to_freq(resp[:5])
    return None

def get_freq_mhz():
    hz = get_freq()
    if hz is None: return None
    return hz / 1_000_000

def set_freq(hz):
    _flush()
    _send(0x05, _freq_to_bcd(int(hz)))
    time.sleep(0.05)
    _ser.reset_input_buffer()

def get_mode():
    resp = _query(0x04)
    if resp and len(resp) >= 1:
        return MODE_NAMES.get(resp[0], "?")
    return None

def get_mode_filter():
    resp = _query(0x04)
    if resp and len(resp) >= 2:
        return MODE_NAMES.get(resp[0], "?"), resp[1]
    if resp and len(resp) >= 1:
        return MODE_NAMES.get(resp[0], "?"), None
    return None, None

def set_mode(mode_name, filt=1):
    code = MODE_CODES.get(mode_name.upper())
    if code is None: return False
    _flush()
    _send(0x06, [code, filt])
    time.sleep(0.05)
    _ser.reset_input_buffer()
    return True

def smeter_text(raw):
    """Spoken S-meter value for a raw 15 02 reading on Icom's scale."""
    raw = max(0, int(raw))
    if raw < SMETER_RAW_S9:
        units = (raw * 9 + SMETER_RAW_S9 // 2) // SMETER_RAW_S9
        return f"S {units}"
    raw = min(raw, SMETER_RAW_S9_PLUS_60)
    span = SMETER_RAW_S9_PLUS_60 - SMETER_RAW_S9
    over = ((raw - SMETER_RAW_S9) * 6 + span // 2) // span * 10
    return "S 9" if over == 0 else f"S 9 plus {over}"

def get_smeter():
    raw = _get_meter_raw(0x02)
    if raw is None:
        return "S meter unavailable"
    return smeter_text(raw)

def _get_meter_raw(meter_id):
    resp = _query(0x15, [meter_id])
    if resp and len(resp) >= 3 and resp[0] == meter_id:
        return (resp[1] & 0x0F) * 100 + ((resp[2] >> 4) & 0x0F) * 10 + (resp[2] & 0x0F)
    return None

def get_power_meter_percent():
    raw = _get_meter_raw(0x11)
    if raw is None:
        return None
    if raw <= 143:
        return round(raw * 50 / 143)
    return round(50 + (min(raw, 213) - 143) * 50 / 70)

def get_swr():
    raw = _get_meter_raw(0x12)
    if raw is None:
        return None
    raw = max(0, min(120, raw))
    if raw <= 48:
        swr = 1.0 + raw * 0.5 / 48
    elif raw <= 80:
        swr = 1.5 + (raw - 48) * 0.5 / 32
    else:
        swr = 2.0 + (raw - 80) * 1.0 / 40
    return round(swr, 1)

def get_tx():
    value = _query_1c_byte(0x00)
    if value is None:
        return False
    return value == 0x01

def get_tx_freq():
    resp = _query(0x1C, [0x03])
    if resp and len(resp) >= 6 and resp[0] == 0x03:
        return _bcd_to_freq(resp[1:6])
    return None

def get_tx_freq_mhz():
    hz = get_tx_freq()
    if hz is None:
        return None
    return hz / 1_000_000

def get_split():
    resp = _query(0x0F)
    if resp and len(resp) >= 1:
        return resp[0] != 0x00
    return False

def set_split(on):
    _flush()
    _send(0x0F, [0x01 if on else 0x00])
    time.sleep(0.05)
    _ser.reset_input_buffer()

def get_duplex():
    resp = _query(0x0F)
    if resp and len(resp) >= 1:
        if resp[0] == 0x10:
            return 0
        if resp[0] == 0x11:
            return -1
        if resp[0] == 0x12:
            return 1
        return 0
    return None

def set_duplex(value):
    code = {0: 0x10, -1: 0x11, 1: 0x12}.get(int(value), 0x10)
    _flush()
    _send(0x0F, [code])
    time.sleep(0.05)
    _ser.reset_input_buffer()

def get_tone_squelch_mode():
    return _query_16_byte(0x5D)

def set_tone_squelch_mode(value):
    _set_16_byte(0x5D, max(0, min(9, int(value))))

def get_repeater_tone():
    value = _query_16_byte(0x42)
    if value is None:
        return None
    return value != 0x00

def set_repeater_tone(on):
    _set_16_byte(0x42, 0x01 if on else 0x00)

def get_tsql():
    value = _query_16_byte(0x43)
    if value is None:
        return None
    return value != 0x00

def set_tsql(on):
    _set_16_byte(0x43, 0x01 if on else 0x00)

def get_dtcs():
    value = _query_16_byte(0x4B)
    if value is None:
        return None
    return value != 0x00

def set_dtcs(on):
    _set_16_byte(0x4B, 0x01 if on else 0x00)

def get_dsql_csql():
    return _query_16_byte(0x5B)

def set_dsql_csql(value):
    _set_16_byte(0x5B, max(0, min(2, int(value))))

def select_memory_mode():
    _flush()
    _send(0x08)
    time.sleep(0.05)
    _ser.reset_input_buffer()

def select_memory_channel(channel):
    channel = max(0, min(99, int(channel)))
    _flush()
    _send(0x08, _level_to_bcd(channel))
    time.sleep(0.05)
    _ser.reset_input_buffer()

def memory_write():
    _flush()
    _send(0x09)
    time.sleep(0.05)
    _ser.reset_input_buffer()

def memory_copy_to_vfo():
    _flush()
    _send(0x0A)
    time.sleep(0.05)
    _ser.reset_input_buffer()

def memory_clear():
    _flush()
    _send(0x0B)
    time.sleep(0.05)
    _ser.reset_input_buffer()

def scan_stop():
    _flush()
    _send(0x0E, [0x00])
    time.sleep(0.05)
    _ser.reset_input_buffer()

def scan_program_memory():
    _flush()
    _send(0x0E, [0x01])
    time.sleep(0.05)
    _ser.reset_input_buffer()

def scan_program():
    _flush()
    _send(0x0E, [0x02])
    time.sleep(0.05)
    _ser.reset_input_buffer()

def scan_memory():
    _flush()
    _send(0x0E, [0x22])
    time.sleep(0.05)
    _ser.reset_input_buffer()

def scan_select_memory():
    _flush()
    _send(0x0E, [0x23])
    time.sleep(0.05)
    _ser.reset_input_buffer()

def select_vfo_a():
    _flush(); _send(0x07, [0x00])
    time.sleep(0.05); _ser.reset_input_buffer()

def select_vfo_b():
    _flush(); _send(0x07, [0x01])
    time.sleep(0.05); _ser.reset_input_buffer()

def swap_vfo():
    _flush(); _send(0x07, [0xB0])
    time.sleep(0.05); _ser.reset_input_buffer()

def get_nr():
    value = _query_16_byte(0x40)
    if value is None:
        return None
    return value != 0x00

def set_nr(on):
    _set_16_byte(0x40, 0x01 if on else 0x00)

def get_auto_notch():
    value = _query_16_byte(0x41)
    if value is None:
        return None
    return value != 0x00

def set_auto_notch(on):
    _set_16_byte(0x41, 0x01 if on else 0x00)

def get_nb():
    value = _query_16_byte(0x22)
    if value is None:
        return None
    return value != 0x00

def set_nb(on):
    _set_16_byte(0x22, 0x01 if on else 0x00)

def get_lock():
    value = _query_16_byte(0x50)
    if value is None:
        return None
    return value != 0x00

def set_lock(on):
    _set_16_byte(0x50, 0x01 if on else 0x00)

def get_rit():
    resp = _query(0x21, [0x01])
    if resp and len(resp) >= 2 and resp[0] == 0x01:
        return resp[1] != 0x00
    return None

def set_rit(on):
    _flush(); _send(0x21, [0x01, 0x01 if on else 0x00])
    time.sleep(0.05); _ser.reset_input_buffer()

def get_rit_offset_hz():
    resp = _query(0x21, [0x00])
    if resp and len(resp) >= 4 and resp[0] == 0x00:
        low = resp[1]
        high = resp[2]
        value = ((high >> 4) & 0x0F) * 1000
        value += (high & 0x0F) * 100
        value += ((low >> 4) & 0x0F) * 10
        value += low & 0x0F
        return -value if resp[3] == 0x01 else value
    return None

def set_rit_offset_hz(hz):
    hz = max(-9999, min(9999, int(hz)))
    value = abs(hz)
    sign = 0x01 if hz < 0 else 0x00
    ones = value % 10
    tens = (value // 10) % 10
    hundreds = (value // 100) % 10
    thousands = (value // 1000) % 10
    _flush()
    _send(0x21, [0x00, (tens << 4) | ones, (thousands << 4) | hundreds, sign])
    time.sleep(0.05)
    _ser.reset_input_buffer()

def get_af():
    resp = _query(0x14, [0x01])
    if resp and len(resp) >= 3 and resp[0] == 0x01:
        raw = (resp[1] & 0x0F) * 100 + ((resp[2] >> 4) & 0x0F) * 10 + (resp[2] & 0x0F)
        return raw
    return None

def get_rf_power():
    return _query_14_value(0x0A)

def get_rf_power_percent():
    raw = get_rf_power()
    if raw is None:
        return None
    return round(raw * 100 / 255)

def set_rf_power(raw):
    _set_14_value(0x0A, raw)

def set_rf_power_percent(percent):
    set_rf_power(_percent_to_raw(percent))

def get_nr_level_percent():
    return _raw_to_percent(_query_14_value(0x06))

def set_nr_level_percent(percent):
    _set_14_value(0x06, _percent_to_raw(percent))

def get_nb_level_percent():
    return _raw_to_percent(_query_14_value(0x12))

def set_nb_level_percent(percent):
    _set_14_value(0x12, _percent_to_raw(percent))

def get_pbt1():
    raw = _query_14_value(0x07)
    if raw is None:
        return None
    return raw - 128

def set_pbt1(value):
    _set_14_value(0x07, max(0, min(255, int(value) + 128)))

def get_pbt2():
    raw = _query_14_value(0x08)
    if raw is None:
        return None
    return raw - 128

def set_pbt2(value):
    _set_14_value(0x08, max(0, min(255, int(value) + 128)))

def get_filter_shape():
    raw = _query_16_byte(0x56)
    if raw == 0x00:
        return 'sharp'
    if raw == 0x01:
        return 'soft'
    return None

def set_filter_shape(shape):
    shape = shape.lower()
    if shape == 'sharp':
        _set_16_byte(0x56, 0x00)
        return True
    if shape == 'soft':
        _set_16_byte(0x56, 0x01)
        return True
    return False

def get_filter_width():
    _mode, filt = get_mode_filter()
    return filt

def set_filter_width(raw):
    mode = get_mode()
    if not mode:
        return False
    return set_mode(mode, max(1, min(3, int(raw))))

def get_monitor():
    value = _query_16_byte(0x45)
    if value is None:
        return None
    return value != 0x00

def set_monitor(on):
    _set_16_byte(0x45, 0x01 if on else 0x00)

def get_monitor_level_percent():
    return _raw_to_percent(_query_14_value(0x15))

def set_monitor_level_percent(percent):
    _set_14_value(0x15, _percent_to_raw(percent))

def get_transceive():
    raw = _query_menu_byte(0x05, TRANSCEIVE_MENU_ITEM)
    if raw is None:
        return None
    return raw != 0x00

def set_transceive(on):
    _set_menu_byte(0x05, TRANSCEIVE_MENU_ITEM, 0x01 if on else 0x00)

def get_notch():
    value = _query_16_byte(0x48)
    if value is None:
        return None
    return value != 0x00

def set_notch(on):
    _set_16_byte(0x48, 0x01 if on else 0x00)

def get_notch_width():
    return _query_16_byte(0x57)

def set_notch_width(value):
    _set_16_byte(0x57, max(0, min(2, int(value))))

def get_preamp():
    return _query_16_byte(0x02)

def set_preamp(value):
    _set_16_byte(0x02, max(0, min(2, int(value))))

def get_agc():
    return _query_16_byte(0x12)

def set_agc(value):
    _set_16_byte(0x12, max(1, min(3, int(value))))

def get_att():
    resp = _query(0x11)
    if resp and len(resp) >= 1:
        return 20 if resp[0] == 0x20 else 0
    return None

def set_att(db):
    _flush()
    _send(0x11, [0x20 if int(db) else 0x00])
    time.sleep(0.05)
    _ser.reset_input_buffer()

def get_tuner():
    return _query_1c_byte(0x01)

def set_tuner(on):
    _set_1c_byte(0x01, 0x01 if on else 0x00)

def start_tune():
    _set_1c_byte(0x01, 0x02)

def get_xfc():
    value = _query_1c_byte(0x02)
    if value is None:
        return None
    return value != 0x00

def set_xfc(on):
    _set_1c_byte(0x02, 0x01 if on else 0x00)

def get_alc_meter_percent():
    return _raw_to_percent(_get_meter_raw(0x13))

def get_comp_meter_percent():
    return _raw_to_percent(_get_meter_raw(0x14))

def get_voltage():
    raw = _get_meter_raw(0x15)
    if raw is None:
        return None
    return round(raw * 16 / 241, 1)

def get_current():
    raw = _get_meter_raw(0x16)
    if raw is None:
        return None
    return round(raw * 4 / 241, 1)

def get_gps_select():
    resp = _query(0x23, [0x01])
    if resp and len(resp) >= 2 and resp[0] == 0x01:
        return resp[1]
    return None

def set_gps_select(value):
    _flush()
    _send(0x23, [0x01, max(0, min(3, int(value)))])
    time.sleep(0.05)
    _ser.reset_input_buffer()

def get_gps_position_status():
    resp = _query(0x23, [0x00])
    if resp and len(resp) >= 2 and resp[0] == 0x00:
        return resp[1:]
    return None

def get_gps_tx_mode():
    return _query_16_byte(0x5C)

def set_gps_tx_mode(value):
    _set_16_byte(0x5C, max(0, min(2, int(value))))

def get_dv_data_tx():
    resp = _query(0x22, [0x02])
    if resp and len(resp) >= 2 and resp[0] == 0x02:
        return resp[1]
    return None

def set_dv_data_tx(value):
    _flush()
    _send(0x22, [0x02, 0x01 if int(value) else 0x00])
    time.sleep(0.05)
    _ser.reset_input_buffer()

def get_dv_fast_data():
    resp = _query(0x22, [0x03])
    if resp and len(resp) >= 2 and resp[0] == 0x03:
        return resp[1]
    return None

def set_dv_fast_data(on):
    _flush()
    _send(0x22, [0x03, 0x01 if on else 0x00])
    time.sleep(0.05)
    _ser.reset_input_buffer()

def get_vfob_freq():
    # Cmd 0x25 subcmd 0x01 = VFO B
    resp = _query(0x25, [0x01])
    if resp and len(resp) >= 6:
        return _bcd_to_freq(resp[1:6]) / 1_000_000
    return None

def set_selected_or_unselected_freq(selector, hz):
    payload = [selector]
    payload.extend(_freq_to_bcd(int(hz)))
    _flush()
    _send(0x25, payload)
    time.sleep(0.05)
    _ser.reset_input_buffer()

def set_vfoa_freq(hz):
    select_vfo_a()
    set_selected_or_unselected_freq(0x00, hz)

def set_vfob_freq(hz):
    select_vfo_a()
    set_selected_or_unselected_freq(0x01, hz)

def get_vfob_mode():
    # Cmd 0x26 subcmd 0x01 = VFO B
    resp = _query(0x26, [0x01])
    if resp and len(resp) >= 2:
        return MODE_NAMES.get(resp[1], "?")
    return None

def set_selected_or_unselected_mode(selector, mode_name, filt=1):
    code = MODE_CODES.get(mode_name.upper())
    if code is None:
        return False
    _flush()
    _send(0x26, [selector, code, 0x00, filt])
    time.sleep(0.05)
    _ser.reset_input_buffer()
    return True

def set_vfoa_mode(mode_name, filt=1):
    select_vfo_a()
    return set_selected_or_unselected_mode(0x00, mode_name, filt)

def set_vfob_mode(mode_name, filt=1):
    select_vfo_a()
    return set_selected_or_unselected_mode(0x01, mode_name, filt)


# --- Stage 2: transmit, CW, tone and band stack (as HamTRC protocol_ops_civ.cpp) ---

VOX_DELAY_MENU_ITEM = 0   # 1A 05 menu number of the VOX delay (profile)

def get_proc():
    value = _query_16_byte(0x44)
    return None if value is None else value != 0x00

def set_proc(on):
    _set_16_byte(0x44, 0x01 if on else 0x00)

def get_proc_level_percent():
    return _raw_to_percent(_query_14_value(0x0E))

def set_proc_level_percent(percent):
    _set_14_value(0x0E, _percent_to_raw(percent))

def get_vox():
    value = _query_16_byte(0x46)
    return None if value is None else value != 0x00

def set_vox(on):
    _set_16_byte(0x46, 0x01 if on else 0x00)

def get_vox_gain_percent():
    return _raw_to_percent(_query_14_value(0x16))

def set_vox_gain_percent(percent):
    _set_14_value(0x16, _percent_to_raw(percent))

def get_mic_gain_percent():
    return _raw_to_percent(_query_14_value(0x0B))

def set_mic_gain_percent(percent):
    _set_14_value(0x0B, _percent_to_raw(percent))

def get_vox_delay_ms():
    """1A 05 <item>: 00..20 in BCD, tenths of a second."""
    raw = _query_menu_byte(0x05, VOX_DELAY_MENU_ITEM)
    if raw is None:
        return None
    tenths = (raw >> 4) * 10 + (raw & 0x0F)
    return tenths * 100 if 0 <= tenths <= 20 else None

def set_vox_delay_ms(ms):
    tenths = max(0, min(20, (int(ms) + 50) // 100))
    _set_menu_byte(0x05, VOX_DELAY_MENU_ITEM, ((tenths // 10) << 4) | (tenths % 10))

BREAK_IN = ('off', 'semi', 'full')   # 16 47: 00 off, 01 semi, 02 full

def get_break_in():
    value = _query_16_byte(0x47)
    return value if value in (0, 1, 2) else None

def set_break_in(value):
    _set_16_byte(0x47, max(0, min(2, int(value))))

def cw_pitch_raw_to_hz(raw):
    raw = max(0, min(255, raw))
    hz = 300 + (raw * 600 + 127) // 255
    return (hz + 2) // 5 * 5

def cw_pitch_hz_to_raw(hz):
    hz = max(300, min(900, int(hz)))
    return ((hz - 300) * 255 + 300) // 600

def get_cw_pitch_hz():
    raw = _query_14_value(0x09)
    return None if raw is None else cw_pitch_raw_to_hz(raw)

def set_cw_pitch_hz(hz):
    _set_14_value(0x09, cw_pitch_hz_to_raw(hz))

# The 50 standard CTCSS tones, in tenths of a Hz.
CTCSS_TONES = (
    670, 693, 719, 744, 770, 797, 825, 854, 885, 915,
    948, 974, 1000, 1035, 1072, 1109, 1148, 1188, 1230, 1273,
    1318, 1365, 1413, 1462, 1514, 1567, 1598, 1622, 1655, 1679,
    1713, 1738, 1773, 1799, 1835, 1862, 1899, 1928, 1966, 1995,
    2035, 2065, 2107, 2181, 2257, 2291, 2336, 2418, 2503, 2541,
)

def tone_encode(tenths):
    tenths = max(0, min(9999, int(tenths)))
    return [0x00, ((tenths // 1000) << 4) | ((tenths // 100) % 10),
            (((tenths // 10) % 10) << 4) | (tenths % 10)]

def tone_decode(data):
    if len(data) < 3 or data[0] != 0x00:
        return None
    value = 0
    for b in data[1:3]:
        hi, lo = b >> 4, b & 0x0F
        if hi > 9 or lo > 9:
            return None
        value = value * 100 + hi * 10 + lo
    return value

def get_ctcss_tenths():
    """1B 00: the repeater tone."""
    resp = _query(0x1B, [0x00])
    if resp and len(resp) >= 4 and resp[0] == 0x00:
        return tone_decode(resp[1:4])
    return None

def set_ctcss_tenths(tenths):
    """1B 00 and 1B 01: repeater and TSQL tone alike (HamTRC)."""
    for sub in (0x00, 0x01):
        _flush()
        _send(0x1B, [sub] + tone_encode(tenths))
        time.sleep(0.05)
        _ser.reset_input_buffer()

def band_code(hz):
    """Icom band stack band code of a frequency (HamTRC ui_console.cpp)."""
    bands = ((1800000, 1999999, 0x01), (3400000, 4099999, 0x02), (6900000, 7499999, 0x03),
             (9900000, 10499999, 0x04), (13900000, 14499999, 0x05), (17900000, 18499999, 0x06),
             (20900000, 21499999, 0x07), (24400000, 25099999, 0x08), (28000000, 29999999, 0x09),
             (50000000, 54000000, 0x0A))
    for lo, hi, code in bands:
        if lo <= hz <= hi:
            return code
    return 0x0B

def get_band_stack(register):
    """1A 01 <band> <register>: (hz, mode name, filter) of the current band."""
    hz = get_freq()
    if not hz:
        return None
    band = band_code(hz)
    resp = _query(0x1A, [0x01, band, register])
    if resp and len(resp) >= 10 and resp[0] == 0x01 and resp[1] == band and resp[2] == register:
        return _bcd_to_freq(resp[3:8]), MODE_NAMES.get(resp[8], '?'), resp[9]
    return None

def recall_band_stack(register):
    entry = get_band_stack(register)
    if entry is None:
        return None
    hz, mode, filt = entry
    set_freq(hz)
    if mode in MODE_CODES:
        set_mode(mode, filt if filt in (1, 2, 3) else 1)
    return entry
