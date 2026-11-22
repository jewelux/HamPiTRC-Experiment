# HamPiTRC keymap: what every bank key does on the active radio.
# After HamTRC's keypad_keymap.cpp (development branch), Icom column.
# The full table is docs/keypad-map.md.
#
# lookup(ui, bank, key, focus) returns the Binding of one key. A, B and C act
# on the bank's focus. A key whose function the radio lacks says "<name> not
# available"; a free key beeps.

import radio
import settings as S
from keypad_input import (Binding, wait_only, SHORT, HOLD, DOUBLE, DOUBLE_HOLD)
from ui import focus_step_action, frequency_words, DigitsEntry, ChoiceEntry


# --- help texts (HamTRC HelpVerb) ----------------------------------------------

def say_(label):
    return label


def toggle_(label):
    return label + ' on off'


def next_(label):
    return 'next ' + label


def choose_(label):
    return 'choose ' + label


def centre_(label):
    return 'reset ' + label


def na_(label):
    return label + ' not available'


def B(short=None, hold=None, double=None, double_hold=None, focus=None, **help):
    """A binding; help: short=..., hold=..., double=..., double_hold=... texts."""
    names = {'short': SHORT, 'hold': HOLD, 'double': DOUBLE, 'double_hold': DOUBLE_HOLD}
    return Binding(short, hold, double, double_hold, focus,
                   {names[k[:-5]]: v for k, v in help.items() if k.endswith('_help') and v})


def not_available(ui, label):
    return B(lambda: ui.not_available(label), short_help=na_(label))


# --- building blocks -----------------------------------------------------------

def setting_key(ui, key):
    """Short says the setting, long opens its entry or pick; it is the focus."""
    s = ui.settings[key]
    if not s.available():
        return not_available(ui, s.label)
    return B(lambda: ui.setting_say(key), lambda: ui.setting_entry(key), focus=key,
             short_help=say_(s.label), hold_help=choose_(s.label))


def list_key(ui, key):
    """Short says, long steps to the next (preamp, attenuator); it is the focus."""
    s = ui.settings[key]
    if not s.available():
        return not_available(ui, s.label)
    return B(lambda: ui.setting_say(key), lambda: ui.setting_next(key), focus=key,
             short_help=say_(s.label), hold_help=next_(s.label))


def switch_key(ui, label, cap, get, put):
    """An on/off switch: short says it, long toggles it."""
    if not radio.has(cap):
        return not_available(ui, label)

    def say():
        v = getattr(radio, get)()
        if v is None:
            return ui.say(label + ' unavailable')
        ui.switch(label, v)

    def toggle():
        v = getattr(radio, get)()
        if v is None:
            return ui.say(label + ' unavailable')
        getattr(radio, put)(not v)
        ui.changed(label, 'off' if v else 'on')
    return B(say, toggle, short_help=say_(label), hold_help=toggle_(label))


def switch_with_level(ui, label, cap, get, put, level):
    """A switch with a level (NR, NB, monitor): double says the level, short
    then hold opens its entry; the level is the focus."""
    sw = switch_key(ui, label, cap, get, put)
    lvl = ui.settings[level]
    if not radio.has(cap) or not lvl.available():
        return sw
    sw.double = lambda: ui.setting_say(level)
    sw.double_hold = lambda: ui.setting_entry(level)
    sw.focus = level
    sw.help[DOUBLE] = say_(lvl.label)
    sw.help[DOUBLE_HOLD] = choose_(lvl.label)
    return sw


def focus_key(ui, key, focus):
    if focus is None:
        return B(lambda: ui.not_available('focus'), short_help=na_('focus'))
    s = ui.settings[focus]
    if key == 'A':
        centre = (lambda: ui.focus_centre()) if (s.centre is not None or s.centre_action) else None
        return B(ui.focus_say, ui.focus_entry, centre,
                 short_help=say_(s.label), hold_help=choose_(s.label),
                 double_help=centre_(s.label) if centre else None)
    d = 1 if key == 'B' else -1
    word = 'up ' if d > 0 else 'down '
    return B(focus_step_action(ui, d), focus_step_action(ui, d, big=True),
             short_help=word + s.label, hold_help=word + 'fast ' + s.label)


# --- actions shared by several banks ---------------------------------------------

def say_frequency(ui, label='frequency', getter='get_freq'):
    hz = getattr(radio, getter)()
    if not hz:
        return ui.say(label + ' unavailable')
    ui.value(label, frequency_words(hz))


def say_rxtx(ui):
    ui.say('transmitting' if radio.get_tx() else 'receiving')


def rf_power_key(ui):
    return setting_key(ui, 'rf_power')


def tuner_key(ui):
    if not radio.has('tuner'):
        return not_available(ui, 'tuner')

    def say():
        t = radio.get_tuner()
        if t is None:
            return ui.say('tuner unavailable')
        ui.value('tuner', 'tuning' if t == 2 else 'on' if t else 'off')

    def toggle():
        t = radio.get_tuner()
        if t is None:
            return ui.say('tuner unavailable')
        radio.set_tuner(t == 0)
        ui.changed('tuner', 'on' if t == 0 else 'off')

    def tune():
        radio.start_tune()
        ui.say('tune')
    return B(say, toggle, tune, short_help='tuner', hold_help=toggle_('tuner'), double_help='tune')


# --- Bank 1: status ----------------------------------------------------------------

def bank1(ui, key):
    if key == '0':
        def round500():
            hz = radio.get_freq()
            if not hz:
                return ui.say('frequency unavailable')
            new = (hz + 250) // 500 * 500
            radio.set_freq(new)
            ui.value('frequency', frequency_words(new))
        return B(lambda: say_frequency(ui), lambda: ui.frequency_entry(radio.set_freq), round500,
                 short_help='frequency', hold_help=choose_('frequency'),
                 double_help='round frequency')
    if key == '1':
        return B(lambda: say_rxtx(ui), double=wait_only, short_help='transceiver')
    if key == '2':
        return B(lambda: say_frequency(ui, 'tx frequency', 'get_tx_freq'), double=wait_only,
                 short_help='tx frequency')
    if key == '3':
        return switch_key(ui, 'lock', 'lock', 'get_lock', 'set_lock')
    if key == '4':
        def po():
            pct = radio.get_power_meter_percent()
            if pct is None:
                return ui.say('tx power unavailable')
            watts = pct * radio.current().rf_power_max_watts / 100
            ui.value('tx power', S.number_words(round(watts * 10), 1) + ' watts')
        return B(po, short_help='tx power')
    if key == '5':
        def alc():
            v = radio.get_alc_meter_percent()
            ui.say('alc unavailable') if v is None else ui.value('alc', str(v) + ' percent')
        return B(alc, short_help='alc')
    if key == '6':
        return rf_power_key(ui)
    if key == '7':
        return B(lambda: ui.say(radio.get_smeter()), short_help='s meter')
    if key == '8':
        def swr():
            if not radio.get_tx():
                return ui.say('swr tx only')
            v = radio.get_swr()
            ui.say('swr unavailable') if v is None else ui.value('swr', S.number_words(round(v * 10), 1))
        return B(swr, short_help='swr')
    if key == '9':
        return setting_key(ui, 'mode')
    return None


# --- Bank 2: receiver ----------------------------------------------------------------

def bank2(ui, key):
    if key == '0':
        return switch_key(ui, 'auto notch', 'auto_notch', 'get_auto_notch', 'set_auto_notch')
    if key == '1':
        return switch_with_level(ui, 'noise reduction', 'nr', 'get_nr', 'set_nr', 'nr_level')
    if key == '2':
        return switch_with_level(ui, 'noise blanker', 'nb', 'get_nb', 'set_nb', 'nb_level')
    if key == '3':
        # The Icom notch toggle walks its widths: off, narrow, mid, wide.
        return list_key(ui, 'notch')
    if key == '4':
        return setting_key(ui, 'pbt_inner')
    if key == '5':
        b = list_key(ui, 'filter')
        if radio.has('filter_width') and radio.has('filter_shape'):
            def shape_say():
                v = radio.get_filter_shape()
                ui.say('filter shape unavailable') if v is None else ui.value('filter shape', v)

            def shape_toggle():
                v = radio.get_filter_shape()
                if v is None:
                    return ui.say('filter shape unavailable')
                new = 'soft' if v == 'sharp' else 'sharp'
                radio.set_filter_shape(new)
                ui.changed('filter shape', new)
            b.double, b.double_hold = shape_say, shape_toggle
            b.help[DOUBLE] = 'filter shape'
            b.help[DOUBLE_HOLD] = toggle_('filter shape')
        return b
    if key == '6':
        return setting_key(ui, 'pbt_outer')
    if key == '7':
        return setting_key(ui, 'agc')
    if key == '8':
        return list_key(ui, 'preamp')
    if key == '9':
        return list_key(ui, 'att')
    return None


# --- Bank 3: VFO and split -------------------------------------------------------------

def vfo_mode_pick(ui, which):
    """VFO A or B mode select: the mode digits, then D."""
    base = ui.settings['mode']
    label = 'vfo ' + which + ' mode'
    setter = radio.set_vfoa_mode if which == 'a' else radio.set_vfob_mode

    def write(i):
        setter(S.mode_choices()[i][1])
        return None

    s = S.Setting('vfo_mode', label, 'list', cap='vfo_b_direct', read=lambda: None, write=write,
                  choices=base.choices, wrap=True, big_steps=0)

    def begin():
        if not s.available():
            raise radio.NotAvailable('vfo_b_direct')
        entry = ChoiceEntry(ui, s)
        ui.keypad.begin_entry(entry)
        entry.prompt()
    return begin


def bank3(ui, key):
    if key == '0':
        def split_say():
            ui.switch('split', radio.get_split())

        def split_toggle():
            on = radio.get_split()
            radio.set_split(not on)
            ui.changed('split', 'off' if on else 'on')
        return B(split_say, split_toggle, lambda: say_frequency(ui, 'tx frequency', 'get_tx_freq'),
                 short_help='split', hold_help=toggle_('split'), double_help='tx frequency')
    if key in ('1', '2'):
        ab = 'a' if key == '1' else 'b'
        label = 'vfo ' + ab

        def say_vfo():
            if ab == 'a':
                return say_frequency(ui, 'vfo a frequency')
            mhz = radio.get_vfob_freq()
            if not mhz:
                return ui.say('vfo b unavailable')
            ui.value('vfo b frequency', frequency_words(round(mhz * 1_000_000)))

        def select():
            radio.select_vfo_a() if ab == 'a' else radio.select_vfo_b()
            ui.say(label)

        setter = radio.set_vfoa_freq if ab == 'a' else radio.set_vfob_freq
        return B(say_vfo, select, lambda: ui.frequency_entry(setter, label + ' frequency'),
                 short_help=label, hold_help=choose_(label), double_help=choose_(label + ' frequency'))
    if key in ('4', '5'):
        ab = 'a' if key == '4' else 'b'
        label = 'vfo ' + ab + ' mode'

        def say_mode():
            m = radio.get_mode() if ab == 'a' else radio.get_vfob_mode()
            ui.say(label + ' unavailable') if not m else ui.value(label, m)
        return B(say_mode, vfo_mode_pick(ui, ab), short_help=label, hold_help=choose_(label))
    if key == '6':
        return B(lambda: say_rxtx(ui), short_help='transceiver')
    if key in ('7', '8', '9'):
        reg = {'7': 1, '8': 2, '9': 3}[key]
        label = 'band stack ' + {1: 'one', 2: 'two', 3: 'three'}[reg]
        if not radio.has('band_stack'):
            return not_available(ui, label)

        def say():
            e = radio.get_band_stack(reg)
            if e is None:
                return ui.say(label + ' unavailable')
            ui.value(label, frequency_words(e[0]) + ', ' + e[1])

        def recall():
            e = radio.recall_band_stack(reg)
            if e is None:
                return ui.say(label + ' unavailable')
            ui.changed(label, frequency_words(e[0]) + ', ' + e[1])
        return B(say, recall, short_help=label, hold_help=choose_(label))
    return None


# --- Bank 4: phone transmit --------------------------------------------------------------

def bank4(ui, key):
    if key == '0':
        return tuner_key(ui)
    if key == '1':
        return switch_with_level(ui, 'processor', 'proc', 'get_proc', 'set_proc', 'proc_level')
    if key == '2':
        return switch_with_level(ui, 'vox', 'vox', 'get_vox', 'set_vox', 'vox_gain')
    if key == '3':
        return switch_with_level(ui, 'monitor', 'monitor', 'get_monitor', 'set_monitor',
                                 'monitor_level')
    if key == '4':
        return not_available(ui, 'tx low cut')
    if key == '5':
        return not_available(ui, 'tx equalizer')
    if key == '6':
        return not_available(ui, 'tx high cut')
    if key == '7':
        return setting_key(ui, 'mic_gain')
    if key == '8':
        return rf_power_key(ui)
    if key == '9':
        return setting_key(ui, 'vox_delay')
    return None


# --- Bank 5: RIT ---------------------------------------------------------------------------

def bank5(ui, key):
    if not radio.has('rit'):
        return not_available(ui, 'R I T') if key in '012345' else None
    s = ui.settings['rit_offset']

    def adjust(delta):
        def act():
            v = radio.get_rit_offset_hz()
            if v is None:
                return ui.say('R I T unavailable')
            v = max(-9999, min(9999, v + delta))
            radio.set_rit_offset_hz(v)
            ui.say(s.spoken(v))
        return act

    def zero():
        radio.set_rit_offset_hz(0)
        ui.value('R I T', s.spoken(0))

    if key == '0':
        def say():
            on = radio.get_rit()
            off = radio.get_rit_offset_hz()
            ui.value('R I T', ('on ' if on else 'off ') + (s.spoken(off) if off is not None else ''))

        def toggle():
            on = radio.get_rit()
            radio.set_rit(not on)
            ui.changed('R I T', 'off' if on else 'on')
        return B(say, toggle, zero, short_help='R I T', hold_help=toggle_('R I T'),
                 double_help=centre_('R I T'))
    steps = {'1': (-10, -100), '2': (10, 100), '4': (-1, -500), '5': (1, 500)}
    if key in steps:
        small, big = steps[key]
        word = 'up ' if small > 0 else 'down '
        return B(adjust(small), adjust(big), focus='rit_offset',
                 short_help=word + 'R I T', hold_help=word + 'fast R I T')
    if key == '3':
        def rit_off():
            radio.set_rit(False)
            ui.changed('R I T', 'off')
        return B(zero, rit_off, focus='rit_offset', short_help=centre_('R I T'), hold_help='R I T off')
    return None


# --- Bank 6: repeater and tone ---------------------------------------------------------------

def bank6(ui, key):
    if key == '0':
        if not radio.has('duplex'):
            return not_available(ui, 'repeater')

        def shift(value, word):
            def act():
                radio.set_duplex(value)
                ui.say('repeater ' + word)
            return act
        return B(shift(0, 'off'), shift(-1, 'minus'), shift(1, 'plus'),
                 short_help='repeater off', hold_help='repeater minus', double_help='repeater plus')
    if key == '1':
        return not_available(ui, 'repeater frequency')
    tone = radio.has('repeater_tone') and radio.has('tsql')
    if key == '2':
        if not tone:
            return not_available(ui, 'tone')

        def say():
            on = radio.get_repeater_tone() or radio.get_tsql()
            ui.value('tone', 'C T C S S' if on else 'off')

        def ctcss():
            if not (radio.get_repeater_tone() or radio.get_tsql()):
                radio.set_repeater_tone(True)
            ui.say('tone C T C S S')

        def off():
            radio.set_repeater_tone(False)
            radio.set_tsql(False)
            ui.say('tone off')
        return B(say, ctcss, off, short_help='tone', hold_help='tone C T C S S', double_help='tone off')
    if key == '3':
        return setting_key(ui, 'ctcss')
    if key == '4':
        return not_available(ui, 'D C S')
    if key == '5':
        if not tone:
            return not_available(ui, 'tone')

        def say():
            if radio.get_tsql():
                ui.value('tone', 'both')
            elif radio.get_repeater_tone():
                ui.value('tone', 'T X')
            else:
                ui.value('tone', 'off')

        def step():
            if radio.get_tsql():
                radio.set_repeater_tone(True)
                ui.changed('tone', 'T X')
            else:
                radio.set_tsql(True)
                ui.changed('tone', 'both')
        return B(say, step, short_help='tone', hold_help=next_('tone'))
    return None


# --- Bank 7: CW ---------------------------------------------------------------------------------

def bank7(ui, key):
    # Icom: break-in off, semi, full and the CW pitch; the rest is FT-8x7 and
    # Yaesu in HamTRC and says "not available".
    names = {'1': 'keyer', '3': 'sidetone', '4': 'paddle',
             '6': 'C W weight', '7': 'paddle reverse', '9': 'break in delay'}
    if key == '0':
        return tuner_key(ui)
    if key == '2':
        return list_key(ui, 'break_in')
    if key == '5':
        return setting_key(ui, 'cw_pitch')
    if key == '8':
        return rf_power_key(ui)
    if key in names:
        return not_available(ui, names[key])
    return None


# --- Bank 8: connection -------------------------------------------------------------------------

def bank8(ui, key):
    if key == '1':
        def say():
            ui.value('C I V address', str(radio.get_civ_address()))

        def entry():
            def done(addr):
                if addr > 255:
                    return ui.say('C I V address out of range')
                radio.set_civ_address(addr)
                radio.remember_link()
                ui.changed('C I V address', str(addr))
            ui.keypad.begin_entry(DigitsEntry(ui, 3, done))
            ui.say('C I V address please')
        return B(say, entry, short_help='C I V address', hold_help=choose_('C I V address'))
    if key == '2':
        return setting_key(ui, 'baud')
    if key == '3':
        return switch_key(ui, 'transceive', 'transceive', 'get_transceive', 'set_transceive')
    return None


# --- Bank 9: profile and speech -------------------------------------------------------------------

def bank9(ui, key):
    if key == '0':
        def say():
            ui.switch('experimental', ui.experimental)

        def toggle():
            ui.experimental = not ui.experimental
            radio.set_experimental(ui.experimental)
            ui.changed('experimental', 'on' if ui.experimental else 'off')
        return B(say, toggle, short_help='experimental', hold_help=toggle_('experimental'))
    if key == '1':
        b = setting_key(ui, 'profile')
        b.double = ui.reset_profile
        b.help[DOUBLE] = centre_('profile')
        return b
    if key in ('4', '5'):
        attr, label = ('tuning_speech', 'auto frequency') if key == '4' else ('verbose', 'verbose')

        def say():
            ui.switch(label, getattr(ui, attr))

        def toggle():
            setattr(ui, attr, not getattr(ui, attr))
            ui.save()
            ui.changed(label, 'on' if getattr(ui, attr) else 'off')
        return B(say, toggle, short_help=label, hold_help=toggle_(label))
    if key == '7':
        return setting_key(ui, 'volume')
    if key == '8':
        return list_key(ui, 'speed')
    return None


BANKS = {1: bank1, 2: bank2, 3: bank3, 4: bank4, 5: bank5, 6: bank6, 7: bank7, 8: bank8, 9: bank9}


def lookup(ui, bank, key, focus):
    if key in ('A', 'B', 'C'):
        return focus_key(ui, key, focus)
    fn = BANKS.get(bank)
    return fn(ui, key) if fn else None
