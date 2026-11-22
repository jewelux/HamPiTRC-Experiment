# HamPiTRC settings: what A, B and C act on, and what entries and picks set.
# After HamTRC's SettingOps (keypad_setting_ops*.cpp).
#
# A setting is a number (RF power, a level, the RIT offset) or a list of named
# choices (mode, AGC, preamp). It knows how to read and write itself, its
# range and steps, and how its value is spoken. Values of a list are indices
# into its choices.

from dataclasses import dataclass, field
from typing import Callable, Optional

import radio


@dataclass
class Setting:
    key: str
    label: str                      # spoken name, e.g. "noise reduction level"
    kind: str = 'number'            # 'number' or 'list'
    cap: Optional[str] = None       # profile capability it needs (None: always)
    read: Optional[Callable] = None
    write: Optional[Callable] = None   # write(value) -> value read back (or None)
    min: int = 0
    max: int = 100
    step: int = 1
    big_steps: int = 5              # a long B/C is this many steps (0: none)
    step_fn: Optional[Callable] = None  # step_fn(value, direction) -> value
    unit: str = ''                  # spoken after the value
    sign: bool = False              # * types a minus in an entry
    point_digits: int = 0           # * types a decimal point, this many digits
    scale: int = 1                  # value = typed number * scale
    choices: Callable = None        # list: choices() -> [(digit or None, name)]
    wrap: bool = False              # list: B and C go round
    centre: Optional[int] = None    # A double sets this
    centre_action: Optional[Callable] = None  # or does this
    confirm: bool = False           # B/C open the entry staged; D writes
    text: Optional[Callable] = None  # text(value) -> spoken value

    def available(self):
        return self.cap is None or radio.has(self.cap)

    def limits(self):
        if self.kind == 'list':
            return 0, len(self.choices()) - 1
        lo, hi = self.min, self.max
        return (lo() if callable(lo) else lo), (hi() if callable(hi) else hi)

    def spoken(self, value):
        if self.text:
            return self.text(value)
        if self.kind == 'list':
            names = [n for _d, n in self.choices()]
            return names[value] if 0 <= value < len(names) else str(value)
        return number_words(value, self.point_digits) + self.unit

    def stepped(self, value, direction):
        lo, hi = self.limits()
        if self.step_fn:
            new = self.step_fn(value, direction)
        else:
            new = value + direction * self.step
        if self.kind == 'list' and self.wrap:
            return lo + (new - lo) % (hi - lo + 1)
        return new


def number_words(value, point_digits=0):
    """A number for speech: 45 -> '45', 455 with one point digit -> '45.5'."""
    if point_digits:
        neg = value < 0
        v = abs(value)
        whole, frac = divmod(v, 10 ** point_digits)
        s = str(whole)
        frac_s = str(frac).rjust(point_digits, '0').rstrip('0')
        if frac_s:
            s += ' point ' + ' '.join(frac_s)
        return ('minus ' if neg else '') + s
    return str(value)


# --- RF power, in tenths of a watt (HamTRC: 1 W steps up to 20 W, 5 W above) ---

def _rf_max_tenths():
    return radio.current().rf_power_max_watts * 10


def _rf_read():
    raw = radio.get_rf_power()
    if raw is None:
        return None
    return round(raw * _rf_max_tenths() / 255)


def _rf_write(tenths):
    raw = round(max(0, tenths) * 255 / _rf_max_tenths())
    radio.set_rf_power(min(255, raw))
    return _rf_read()


def _rf_step(tenths, d):
    if d > 0:
        return tenths + 10 if tenths < 200 else (tenths // 50 + 1) * 50
    return tenths - 10 if tenths <= 200 else (tenths - 1) // 50 * 50


def _rf_text(tenths):
    return number_words(tenths, 1) + (' watt' if tenths == 10 else ' watts')


# --- Mode: the profile's modes in the order of the mode digits ---------------

# HamTRC mode digits; DV on 0 is a HamPiTRC extension (IC-705, IC-7100).
MODE_DIGITS = (('1', 'LSB'), ('2', 'USB'), ('3', 'CW'), ('4', 'AM'), ('5', 'FM'),
               ('7', 'RTTY'), ('8', 'CW-R'), ('9', 'RTTY-R'), ('0', 'DV'))


def mode_choices():
    modes = radio.current().modes
    return [(d, m) for d, m in MODE_DIGITS if m in modes]


def _mode_read():
    mode = radio.get_mode()
    names = [m for _d, m in mode_choices()]
    return names.index(mode) if mode in names else None


def _mode_write(index):
    radio.set_mode(mode_choices()[index][1])
    return _mode_read()


# --- Icom notch: 0 off, 1 narrow, 2 mid, 3 wide (16 48 and 16 57) -------------
# 16 57: 0 wide, 1 mid, 2 narrow.

def _notch_choices():
    if radio.has('notch_width'):
        return [('0', 'off'), ('1', 'narrow'), ('2', 'mid'), ('3', 'wide')]
    return [('0', 'off'), ('1', 'on')]


def _notch_read():
    on = radio.get_notch()
    if on is None:
        return None
    if not on:
        return 0
    if not radio.has('notch_width'):
        return 1
    width = radio.get_notch_width()
    return {2: 1, 1: 2, 0: 3}.get(width, 1)


def _notch_write(value):
    if value == 0:
        radio.set_notch(False)
    else:
        if radio.has('notch_width'):
            radio.set_notch_width({1: 2, 2: 1, 3: 0}[value])
        radio.set_notch(True)
    return _notch_read()


# --- simple read/write pairs ---------------------------------------------------

def _pair(get, put):
    def read():
        return getattr(radio, get)()

    def write(v):
        getattr(radio, put)(v)
        return getattr(radio, get)()
    return read, write


def _list_index(get, put, codes):
    """A list setting whose radio values are codes[index]."""
    def read():
        v = getattr(radio, get)()
        return codes.index(v) if v in codes else None

    def write(i):
        getattr(radio, put)(codes[i])
        return read()
    return read, write


def _preamp_choices():
    return [('0', 'off'), ('1', 'one'), ('2', 'two')]


def _att_choices():
    return [('0', 'off'), ('1', '20 dB')]


AGC_CODES = (1, 2, 3)


def _agc_choices():
    # HamTRC AGC digits: 0 off, 1 auto, 2 fast, 3 slow, 4 mid; Icom has fast, mid, slow.
    return [('2', 'fast'), ('4', 'mid'), ('3', 'slow')]


def _filter_choices():
    return [('1', 'one'), ('2', 'two'), ('3', 'three')]


def _rit_text(hz):
    if hz == 0:
        return '0 hertz'
    return ('plus ' if hz > 0 else 'minus ') + str(abs(hz)) + ' hertz'


def _baud_choices():
    return [(str(i + 1), str(b)) for i, b in enumerate(radio.current().bauds)]


def _baud_read():
    bauds = radio.current().bauds
    b = radio.get_baudrate()
    return bauds.index(b) if b in bauds else None


def _baud_write(i):
    radio.set_baudrate(radio.current().bauds[i])
    radio.remember_link()
    return _baud_read()


def _profile_choices():
    import radio_profiles
    return [(str(i + 1), p.spoken) for i, p in enumerate(radio_profiles.PROFILES)]


def _profile_read():
    import radio_profiles
    return radio_profiles.profile_keys().index(radio.current().key)


SPEEDS = ('slow', 'normal', 'fast')


def build(ui):
    """The settings, given the ui (for volume, speed and profile switching)."""
    nr_r, nr_w = _pair('get_nr_level_percent', 'set_nr_level_percent')
    nb_r, nb_w = _pair('get_nb_level_percent', 'set_nb_level_percent')
    p1_r, p1_w = _pair('get_pbt1', 'set_pbt1')
    p2_r, p2_w = _pair('get_pbt2', 'set_pbt2')
    mon_r, mon_w = _pair('get_monitor_level_percent', 'set_monitor_level_percent')
    rit_r, rit_w = _pair('get_rit_offset_hz', 'set_rit_offset_hz')
    flt_r, flt_w = _list_index('get_filter_width', 'set_filter_width', (1, 2, 3))
    pre_r, pre_w = _list_index('get_preamp', 'set_preamp', (0, 1, 2))
    att_r, att_w = _list_index('get_att', 'set_att', (0, 20))
    agc_r, agc_w = _list_index('get_agc', 'set_agc', AGC_CODES)
    level = dict(min=0, max=100, step=5, unit=' percent')
    items = [
        Setting('rf_power', 'power', cap='rf_power', read=_rf_read, write=_rf_write,
                min=0, max=_rf_max_tenths, step_fn=_rf_step, scale=10, text=_rf_text,
                confirm=True),
        Setting('mode', 'mode', 'list', cap='mode', read=_mode_read, write=_mode_write,
                choices=mode_choices, wrap=True, big_steps=0, confirm=True),
        Setting('nr_level', 'noise reduction level', cap='nr_level', read=nr_r, write=nr_w, **level),
        Setting('nb_level', 'noise blanker level', cap='nb_level', read=nb_r, write=nb_w, **level),
        Setting('notch', 'notch filter', 'list', cap='notch', read=_notch_read, write=_notch_write,
                choices=_notch_choices, big_steps=1),
        Setting('pbt_inner', 'P B T one', cap='pbt', read=p1_r, write=p1_w,
                min=-128, max=127, step=10, sign=True, centre=0),
        Setting('pbt_outer', 'P B T two', cap='pbt', read=p2_r, write=p2_w,
                min=-128, max=127, step=10, sign=True, centre=0),
        Setting('filter', 'filter', 'list', cap='filter_width', read=flt_r, write=flt_w,
                choices=_filter_choices, big_steps=1),
        Setting('agc', 'A G C', 'list', cap='agc', read=agc_r, write=agc_w,
                choices=_agc_choices, wrap=True, big_steps=1),
        Setting('preamp', 'preamplifier', 'list', cap='preamp', read=pre_r, write=pre_w,
                choices=_preamp_choices, big_steps=1),
        Setting('att', 'attenuator', 'list', cap='att', read=att_r, write=att_w,
                choices=_att_choices, big_steps=1),
        Setting('monitor_level', 'monitor level', cap='monitor_level', read=mon_r, write=mon_w,
                **level),
        Setting('rit_offset', 'R I T', cap='rit', read=rit_r, write=rit_w,
                min=-9999, max=9999, step=10, big_steps=10, sign=True, centre=0, text=_rit_text),
        Setting('baud', 'baud', 'list', read=_baud_read, write=_baud_write,
                choices=_baud_choices, wrap=True, big_steps=0),
        Setting('profile', 'profile', 'list', read=_profile_read, write=ui.select_profile,
                choices=_profile_choices, wrap=True, big_steps=0,
                centre_action=ui.reset_profile),
        Setting('volume', 'volume', read=lambda: ui.volume, write=ui.set_volume,
                min=1, max=9, big_steps=2),
        Setting('speed', 'speed', 'list', read=lambda: SPEEDS.index(ui.speed),
                write=lambda i: ui.set_speed(SPEEDS[i]),
                choices=lambda: [(str(i + 1), s) for i, s in enumerate(SPEEDS)],
                big_steps=1, centre=1),
    ]
    return {s.key: s for s in items}
