# HamPiTRC user interface: carries out what keypad_input.py decides.
# After HamTRC's KeypadUiListener (ui_keypad*.cpp, ui_keypad_settings.cpp).
#
# - speaks with verbose on ("noise blanker 40 percent") or off ("40 percent")
# - runs key actions; a feature the radio lacks is spoken as not available
# - the entries and picks: frequency, values, choices, CI-V address
# - A, B and C on the bank's focus

import radio
import settings as settings_mod
from keypad_input import Entry, KeypadInput, DIGITS, STAY

BANK_NAMES = {
    1: 'bank one, status',
    2: 'bank two, receiver',
    3: 'bank three, V F O and split',
    4: 'bank four, phone transmit',
    5: 'bank five, R I T',
    6: 'bank six, repeater and tone',
    7: 'bank seven, C W',
    8: 'bank eight, connection',
    9: 'bank nine, profile and speech',
}

HOME_FOCUS = {5: 'rit_offset', 8: 'baud', 9: 'profile'}


class Ui:
    """The listener of KeypadInput, and the toolbox of the bank actions."""

    def __init__(self, speech, keymap_lookup, prefs=None):
        self.speech = speech              # say(text), beep(), stop(), set_volume(), set_speed()
        self.lookup = keymap_lookup       # lookup(ui, bank, key, focus) -> Binding
        prefs = prefs or {}
        self.verbose = prefs.get('verbose', True)
        self.volume = prefs.get('volume', 5)
        self.speed = prefs.get('speed', 'normal')
        self.tuning_speech = prefs.get('tuning_speech', True)
        self.experimental = False
        self.keypad = KeypadInput(self)
        self.settings = settings_mod.build(self)
        self._named_focus = None          # focus named by the last B/C step
        self.speech.set_volume(self.volume)
        self.speech.set_speed(self.speed)

    # --- speaking ---------------------------------------------------------------

    def say(self, text):
        self.speech.say(text)

    def value(self, label, text):
        """An answer: name first when verbose is on."""
        self.say(label + ' ' + text if self.verbose else text)

    def changed(self, label, text):
        """The result of a change: with 'ok' when verbose is on."""
        self.say(label + ' ' + text + ' ok' if self.verbose else text)

    def switch(self, label, on):
        self.value(label, 'on' if on else 'off')

    def not_available(self, label):
        self.say(label + ' not available')

    # --- listener of KeypadInput -------------------------------------------------

    def interrupt(self):
        self.speech.stop()

    def beep(self):
        self.speech.beep()

    def home_focus(self, bank):
        return HOME_FOCUS.get(bank)

    def binding(self, bank, key, focus):
        return self.lookup(self, bank, key, focus)

    def run(self, action):
        self._named_focus_reset_unless(action)
        try:
            action()
        except radio.NotConnected as e:
            self.say(e.spoken())
        except radio.NotAvailable as e:
            self.say(e.spoken())

    def say_bank(self, bank):
        self.say(BANK_NAMES[bank])

    def say_bank_prompt(self):
        self.say('bank please')

    def bank_changed(self, bank):
        self.say_bank(bank)

    def say_digit(self, key):
        self.say(key)

    def say_help(self, text):
        self.say(text)

    def say_help_mode(self, on):
        self.say('help on' if on else 'help off')

    def say_cancelled(self):
        self.say('cancelled')

    def say_timeout(self):
        self.say('timeout')

    # --- prefs ------------------------------------------------------------------

    def save(self):
        prefs = radio.load_prefs()
        prefs.update(verbose=self.verbose, volume=self.volume, speed=self.speed,
                     tuning_speech=self.tuning_speech)
        radio.save_prefs(prefs)

    def set_volume(self, level):
        self.volume = max(1, min(9, int(level)))
        self.speech.set_volume(self.volume)
        self.save()
        return self.volume

    def set_speed(self, speed):
        self.speed = speed
        self.speech.set_speed(speed)
        self.save()
        return settings_mod.SPEEDS.index(speed)

    def select_profile(self, index):
        import radio_profiles
        key = radio_profiles.profile_keys()[index]
        radio.select(key)
        self.keypad.reset_focus()
        try:
            radio.connect()
            self.say(radio.current().spoken + ' connected')
        except Exception:
            self.say(radio.current().spoken + ' selected, not connected')
        return None   # already spoken

    def reset_profile(self):
        radio.reset_link()
        self.say('profile reset')

    # --- settings: say, entry, next, focus steps ------------------------------------

    def setting(self, key):
        s = self.settings[key]
        if not s.available():
            raise radio.NotAvailable(s.cap)
        return s

    def setting_read(self, s):
        v = s.read()
        if v is None:
            self.say(s.label + ' unavailable')
        return v

    def setting_say(self, key):
        s = self.setting(key)
        v = self.setting_read(s)
        if v is not None:
            self.value(s.label, s.spoken(v))

    def setting_write(self, s, v):
        back = s.write(v)
        if back is None and s.key == 'profile':
            return
        self.changed(s.label, s.spoken(v if back is None else back))

    def setting_entry(self, key, staged=None):
        s = self.setting(key)
        if s.kind == 'list':
            entry = ChoiceEntry(self, s, staged)
        else:
            entry = ValueEntry(self, s, staged)
        self.keypad.begin_entry(entry)
        entry.prompt()

    def setting_next(self, key):
        """A short list or switch steps on a hold; off after the last."""
        s = self.setting(key)
        v = self.setting_read(s)
        if v is None:
            return
        lo, hi = s.limits()
        self.setting_write(s, lo if v >= hi else v + 1)

    def focus_setting(self):
        f = self.keypad.focus_of(self.keypad.one_shot_bank or self.keypad.bank)
        return f

    def focus_say(self):
        key = self.focus_setting()
        if key is None:
            return self.not_available('focus')
        s = self.setting(key)
        v = self.setting_read(s)
        if v is not None:
            self.say(s.label + ' ' + s.spoken(v))

    def focus_entry(self):
        key = self.focus_setting()
        if key is None:
            return self.not_available('focus')
        self.setting_entry(key)

    def focus_centre(self):
        key = self.focus_setting()
        s = self.setting(key)
        if s.centre_action:
            return s.centre_action()
        self.setting_write(s, s.centre)

    def focus_step(self, direction, big=False):
        key = self.focus_setting()
        if key is None:
            return self.not_available('focus')
        s = self.setting(key)
        if big and not s.big_steps:
            return self.not_available(s.label + ' fast')
        v = self.setting_read(s)
        if v is None:
            return
        new = v
        for _ in range(s.big_steps if big else 1):
            new = s.stepped(new, direction)
        lo, hi = s.limits()
        if new > hi or new < lo:
            if v == (hi if direction > 0 else lo):
                return self.say('maximum' if direction > 0 else 'minimum')
            new = max(lo, min(hi, new))
        if s.confirm:
            return self.setting_entry(key, staged=new)
        back = s.write(new)
        shown = new if back is None else back
        if s.key == 'profile':
            return
        if self._named_focus == key:
            self.say(s.spoken(shown))
        else:
            self.value(s.label, s.spoken(shown))
        self._named_focus = key

    def _named_focus_reset_unless(self, action):
        if getattr(action, 'focus_step', False):
            return
        self._named_focus = None

    # --- frequency -------------------------------------------------------------------

    def frequency_entry(self, setter, label='frequency'):
        entry = FrequencyEntry(self, setter, label)
        self.keypad.begin_entry(entry)
        self.say(label + ' please')


def focus_step_action(ui, direction, big=False):
    def act():
        ui.focus_step(direction, big)
    act.focus_step = True
    return act


def frequency_words(hz):
    """HamTRC: MHz digits, 'point', the rest without trailing zeros (at least one)."""
    mhz, rest = divmod(int(hz), 1_000_000)
    frac = str(rest).rjust(6, '0').rstrip('0') or '0'
    return ' '.join(str(mhz)) + ' point ' + ' '.join(frac)


# --- entries ------------------------------------------------------------------------

class FrequencyEntry(Entry):
    """MHz, * is the decimal point, up to 5 digits after it (10 Hz)."""

    def __init__(self, ui, setter, label):
        self.ui, self.setter, self.label = ui, setter, label
        self.text = ''

    def key(self, key):
        if key == '*':
            if '*' in self.text or not self.text:
                return False
            self.text += '*'
            self.ui.say('point')
            return True
        if key in DIGITS:
            whole, _, frac = self.text.partition('*')
            if '*' in self.text and len(frac) >= 5:
                return False
            if len(self.text) >= 12:
                return False
            self.text += key
            self.ui.say(key)
            return True
        return False

    def commit(self):
        if not self.text or self.text.endswith('*'):
            return False
        whole, _, frac = self.text.partition('*')
        hz = int(whole) * 1_000_000 + int((frac + '00000')[:5]) * 10
        if hz < 30_000 or hz > 470_000_000:
            self.ui.say('frequency out of range')
            return True
        self.ui.keypad.end_entry()
        self.setter(hz)
        self.ui.changed(self.label, frequency_words(hz))
        return True


class ValueEntry(Entry):
    """A number setting: digits, * as sign or point, A says, B/C step, D sets."""

    def __init__(self, ui, setting, staged=None):
        self.ui, self.s = ui, setting
        self.text = ''
        self.staged = staged      # a value stepped to with B/C (confirm settings)

    def prompt(self):
        if self.staged is not None:
            self.ui.say(self.s.label + ' ' + self.s.spoken(self.staged) + ' please')
        else:
            self.ui.say(self.s.label + ' please')

    def _typed(self):
        t = self.text
        neg = t.startswith('*') and self.s.sign
        if neg:
            t = t[1:]
        if self.s.point_digits and '*' in t:
            whole, _, frac = t.partition('*')
            v = int(whole or '0') * 10 ** self.s.point_digits + int((frac + '000')[:self.s.point_digits])
        else:
            v = int(t or '0') * self.s.scale
        return -v if neg else v

    def current(self):
        if self.text:
            return self._typed()
        return self.staged

    def key(self, key):
        s = self.s
        if key in DIGITS:
            if len(self.text) >= 6:
                return False
            self.text += key
            self.staged = None
            self.ui.say(key)
            return True
        if key == '*':
            if s.sign and not self.text:
                self.text = '*'
                self.ui.say('minus')
                return True
            if s.point_digits and self.text and '*' not in self.text.lstrip('*'):
                self.text += '*'
                self.ui.say('point')
                return True
            return False
        if key == 'A':
            v = self.current()
            self.ui.say(s.spoken(v) if v is not None else s.label + ' please')
            return True
        if key in ('B', 'C'):
            v = self.current()
            if v is None:
                v = s.read()
                if v is None:
                    return False
            lo, hi = s.limits()
            new = s.stepped(v, 1 if key == 'B' else -1)
            if new > hi or new < lo:
                self.ui.say('maximum' if key == 'B' else 'minimum')
                return True
            self.text = ''
            self.staged = new
            self.ui.say(s.spoken(new))
            return True
        return False

    def commit(self):
        v = self.current()
        if v is None:
            return False
        lo, hi = self.s.limits()
        if v > hi or v < lo:
            # Snapped to the end of the range and staged: the next D sets it.
            self.text = ''
            self.staged = max(lo, min(hi, v))
            self.ui.say(('maximum ' if v > hi else 'minimum ') + self.s.spoken(self.staged))
            return STAY
        self.ui.keypad.end_entry()
        self.ui.setting_write(self.s, v)
        return True


class ChoiceEntry(Entry):
    """A list setting: the choice's digit, or A/B/C; D sets."""

    def __init__(self, ui, setting, staged=None):
        self.ui, self.s = ui, setting
        self.choice = staged

    def prompt(self):
        if self.choice is not None:
            self.ui.say(self.s.label + ' ' + self.s.spoken(self.choice) + ' please')
        else:
            self.ui.say('choose ' + self.s.label)

    def key(self, key):
        choices = self.s.choices()
        for i, (digit, _name) in enumerate(choices):
            if digit == key:
                self.choice = i
                self.ui.say(self.s.spoken(i))
                return True
        if key == 'A':
            self.ui.say(self.s.spoken(self.choice) if self.choice is not None else 'choose ' + self.s.label)
            return True
        if key in ('B', 'C'):
            v = self.choice
            if v is None:
                v = self.s.read()
                if v is None:
                    v = 0
            lo, hi = self.s.limits()
            new = v + (1 if key == 'B' else -1)
            if self.s.wrap:
                new = lo + (new - lo) % (hi - lo + 1)
            elif new > hi or new < lo:
                self.ui.say('maximum' if key == 'B' else 'minimum')
                return True
            self.choice = new
            self.ui.say(self.s.spoken(new))
            return True
        return False

    def commit(self):
        if self.choice is None:
            return False
        self.ui.keypad.end_entry()
        self.ui.setting_write(self.s, self.choice)
        return True


class DigitsEntry(Entry):
    """Plain digits up to max_len, then D: on_commit(number) does the rest."""

    def __init__(self, ui, max_len, on_commit):
        self.ui, self.max_len, self.on_commit = ui, max_len, on_commit
        self.text = ''

    def key(self, key):
        if key in DIGITS and len(self.text) < self.max_len:
            self.text += key
            self.ui.say(key)
            return True
        return False

    def commit(self):
        if not self.text:
            return False
        self.ui.keypad.end_entry()
        self.on_commit(int(self.text))
        return True
