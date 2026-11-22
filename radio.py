# HamPiTRC - the active radio.
#
# Holds the selected profile, opens its serial port, remembers the choice in a
# small prefs file and gates every radio call on the profile's capabilities.
# pihamtrc.py talks to the radio only through this module:
#
#     radio.get_nr()        -> civ.get_nr() if the profile has 'nr'
#                           -> raises NotAvailable('nr') if it does not
#
# A gated call sends nothing to the radio.

import json
import os

import civ
import radio_profiles
from radio_profiles import FEATURE_NAMES


class NotAvailable(Exception):
    """The active radio does not have this feature."""

    def __init__(self, feature):
        super().__init__(feature)
        self.feature = feature

    def spoken(self):
        return FEATURE_NAMES.get(self.feature, self.feature) + ' not available on ' + current().spoken


class NotConnected(NotAvailable):
    """The active radio's serial port is not open (e.g. after a switch)."""

    def __init__(self):
        super().__init__('connection')

    def spoken(self):
        return current().spoken + ' not connected'


# Which capability each civ function needs. Functions not listed here
# (address, baud rate, connect) are always allowed.
FEATURE_OF = {
    'get_freq': 'freq', 'get_freq_mhz': 'freq', 'set_freq': 'freq',
    'get_mode': 'mode', 'get_mode_filter': 'mode', 'set_mode': 'mode',
    'get_smeter': 'smeter',
    'get_power_meter_percent': 'power_meter',
    'get_rf_power': 'rf_power', 'get_rf_power_percent': 'rf_power',
    'set_rf_power': 'rf_power', 'set_rf_power_percent': 'rf_power',
    'get_swr': 'swr', 'get_tx': 'tx_status',
    'get_tx_freq': 'tx_freq', 'get_tx_freq_mhz': 'tx_freq',
    'get_lock': 'lock', 'set_lock': 'lock',
    'get_nr': 'nr', 'set_nr': 'nr',
    'get_nr_level_percent': 'nr_level', 'set_nr_level_percent': 'nr_level',
    'get_auto_notch': 'auto_notch', 'set_auto_notch': 'auto_notch',
    'get_nb': 'nb', 'set_nb': 'nb',
    'get_nb_level_percent': 'nb_level', 'set_nb_level_percent': 'nb_level',
    'get_notch': 'notch', 'set_notch': 'notch',
    'get_notch_width': 'notch_width', 'set_notch_width': 'notch_width',
    'get_pbt1': 'pbt', 'set_pbt1': 'pbt', 'get_pbt2': 'pbt', 'set_pbt2': 'pbt',
    'get_filter_shape': 'filter_shape', 'set_filter_shape': 'filter_shape',
    'get_filter_width': 'filter_width', 'set_filter_width': 'filter_width',
    'get_preamp': 'preamp', 'set_preamp': 'preamp',
    'get_att': 'att', 'set_att': 'att',
    'get_agc': 'agc', 'set_agc': 'agc',
    'select_vfo_a': 'vfo', 'select_vfo_b': 'vfo', 'swap_vfo': 'vfo',
    'get_split': 'split', 'set_split': 'split',
    'get_vfob_freq': 'vfo_b_direct', 'get_vfob_mode': 'vfo_b_direct',
    'set_vfoa_freq': 'vfo_b_direct', 'set_vfob_freq': 'vfo_b_direct',
    'set_vfoa_mode': 'vfo_b_direct', 'set_vfob_mode': 'vfo_b_direct',
    'set_selected_or_unselected_freq': 'vfo_b_direct',
    'set_selected_or_unselected_mode': 'vfo_b_direct',
    'get_monitor': 'monitor', 'set_monitor': 'monitor',
    'get_monitor_level_percent': 'monitor_level',
    'set_monitor_level_percent': 'monitor_level',
    'get_transceive': 'transceive', 'set_transceive': 'transceive',
    'get_tuner': 'tuner', 'set_tuner': 'tuner', 'start_tune': 'tuner',
    'get_xfc': 'xfc', 'set_xfc': 'xfc',
    'get_rit': 'rit', 'set_rit': 'rit',
    'get_rit_offset_hz': 'rit', 'set_rit_offset_hz': 'rit',
    'get_duplex': 'duplex', 'set_duplex': 'duplex',
    'get_repeater_tone': 'repeater_tone', 'set_repeater_tone': 'repeater_tone',
    'get_tsql': 'tsql', 'set_tsql': 'tsql',
    'get_dtcs': 'dtcs', 'set_dtcs': 'dtcs',
    'get_tone_squelch_mode': 'tone_squelch_mode',
    'set_tone_squelch_mode': 'tone_squelch_mode',
    'get_dsql_csql': 'dsql_csql', 'set_dsql_csql': 'dsql_csql',
    'select_memory_mode': 'memory', 'select_memory_channel': 'memory',
    'memory_write': 'memory', 'memory_copy_to_vfo': 'memory',
    'memory_clear': 'memory_clear',
    'scan_stop': 'scan', 'scan_program_memory': 'scan', 'scan_program': 'scan',
    'scan_memory': 'scan', 'scan_select_memory': 'scan',
    'get_dv_data_tx': 'dv_data', 'set_dv_data_tx': 'dv_data',
    'get_dv_fast_data': 'dv_data', 'set_dv_fast_data': 'dv_data',
    'get_gps_select': 'gps', 'set_gps_select': 'gps',
    'get_gps_position_status': 'gps',
    'get_gps_tx_mode': 'gps', 'set_gps_tx_mode': 'gps',
    'get_proc': 'proc', 'set_proc': 'proc',
    'get_proc_level_percent': 'proc', 'set_proc_level_percent': 'proc',
    'get_vox': 'vox', 'set_vox': 'vox',
    'get_vox_gain_percent': 'vox', 'set_vox_gain_percent': 'vox',
    'get_mic_gain_percent': 'mic_gain', 'set_mic_gain_percent': 'mic_gain',
    'get_vox_delay_ms': 'vox_delay', 'set_vox_delay_ms': 'vox_delay',
    'get_break_in': 'break_in', 'set_break_in': 'break_in',
    'get_cw_pitch_hz': 'cw_pitch', 'set_cw_pitch_hz': 'cw_pitch',
    'get_ctcss_tenths': 'ctcss', 'set_ctcss_tenths': 'ctcss',
    'get_band_stack': 'band_stack', 'recall_band_stack': 'band_stack',
    'get_alc_meter_percent': 'alc_meter', 'get_comp_meter_percent': 'comp_meter',
    'get_voltage': 'vd_meter', 'get_current': 'id_meter',
}

# Mode setters: the mode must be in the profile's list too.
_MODE_SETTERS = {'set_mode', 'set_vfoa_mode', 'set_vfob_mode'}

PREFS_PATH = os.path.expanduser(os.environ.get(
    'HAMPITRC_PREFS', '~/.config/hampitrc/prefs.json'))

_profile = radio_profiles.get_profile(radio_profiles.DEFAULT_PROFILE)
_serial_ports = {}   # per-profile overrides from config.py


def current():
    return _profile


_experimental = False


def set_experimental(on):
    """HamTRC experimental mode: every feature counts as supported."""
    global _experimental
    _experimental = bool(on)


def has(feature):
    return _experimental or bool(getattr(_profile.caps, feature))


def __getattr__(name):
    # Module-level proxy: radio.<civ function>, gated by FEATURE_OF.
    target = getattr(civ, name)
    feature = FEATURE_OF.get(name)
    if feature is None:
        return target

    def gated(*args, **kwargs):
        if not has(feature):
            raise NotAvailable(feature)
        if not civ.is_connected():
            raise NotConnected()
        if name in _MODE_SETTERS and args:
            if str(args[0]).upper() not in _profile.modes:
                raise NotAvailable('mode')
        return target(*args, **kwargs)

    gated.__name__ = name
    return gated


# --- prefs file: selected radio, and CI-V address / baud per radio ----------

def load_prefs(path=None):
    try:
        with open(path or PREFS_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def save_prefs(prefs, path=None):
    path = path or PREFS_PATH
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        tmp = path + '.tmp'
        with open(tmp, 'w', encoding='utf-8') as f:
            json.dump(prefs, f, indent=2, sort_keys=True)
        os.replace(tmp, path)
        return True
    except OSError:
        return False


def _link_for(profile, prefs):
    saved = prefs.get('radios', {}).get(profile.key, {})
    addr = saved.get('civ_addr', profile.civ_addr)
    baud = saved.get('baud', profile.baud)
    port = _serial_ports.get(profile.key) or profile.serial_port
    return int(addr), int(baud), port


def serial_port():
    return _link_for(_profile, load_prefs())[2]


def select(key, serial_ports=None, remember=True):
    """Make `key` the active profile and configure civ for it (no connect)."""
    global _profile, _serial_ports
    if serial_ports is not None:
        _serial_ports = dict(serial_ports)
    _profile = radio_profiles.get_profile(key)
    prefs = load_prefs()
    addr, baud, _port = _link_for(_profile, prefs)
    civ.configure(addr, baud, _profile.transceive_menu_item, _profile.vox_delay_menu_item)
    if remember:
        prefs['profile'] = key
        save_prefs(prefs)
    return _profile


def start(default_key, serial_ports=None):
    """Select the remembered profile, or default_key on the first start."""
    key = load_prefs().get('profile', default_key)
    if key not in radio_profiles.profile_keys():
        key = default_key
    return select(key, serial_ports, remember=False)


def connect():
    """Open the active profile's serial port. Raises on failure."""
    civ.disconnect()
    civ.connect(serial_port())


def switch(step):
    """Select the next (step=1) or previous (step=-1) profile and connect."""
    keys = radio_profiles.profile_keys()
    idx = (keys.index(_profile.key) + step) % len(keys)
    select(keys[idx])
    try:
        connect()
        return True
    except Exception:
        return False


def reset_link():
    """Back to the profile's CI-V address and baud rate (HamTRC: profile reset)."""
    prefs = load_prefs()
    prefs.get('radios', {}).pop(_profile.key, None)
    save_prefs(prefs)
    civ.configure(_profile.civ_addr, _profile.baud, _profile.transceive_menu_item,
                  _profile.vox_delay_menu_item)
    civ.set_baudrate(_profile.baud)


def remember_link():
    """Save the running CI-V address and baud rate for the active radio."""
    prefs = load_prefs()
    radios = prefs.setdefault('radios', {})
    radios[_profile.key] = {'civ_addr': civ.get_civ_address(), 'baud': civ.get_baudrate()}
    return save_prefs(prefs)
