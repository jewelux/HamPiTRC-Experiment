# HamPiTRC keypad state machine, after HamTRC's KeypadInput (keypad_input.cpp).
#
# Decides what a key press means; never talks to the radio or the speaker.
# Everything goes out through the listener (ui.py in the program, a fake in
# tests). Times are in milliseconds and come from the caller, so tests can
# drive the clock.
#
# Gestures (Normal mode):
#   short        acts on release
#   long         acts at the hold (LONG_MS); the release is swallowed
#   double       two presses of the same key within DOUBLE_MS; only keys
#                whose binding waits for a double notice it
#   double hold  a short press, then within DOUBLE_MS a hold of the same key
# Keys:
#   *  short: say the bank. Long: "bank please", then a digit changes bank.
#      A digit while * is still held: the next key acts on that bank only.
#   D  long: help mode on/off. In an entry: commit.
#   #  cancel an entry or selection, end help mode.
# Two keys down at once: beep, and both are ignored until all are released.
# Any mode but Normal acts on the press, ignores holds and ends after
# ENTRY_TIMEOUT_MS without a key ("timeout").

from dataclasses import dataclass, field
from typing import Callable, Optional

LONG_MS = 700
DOUBLE_MS = 220
ENTRY_TIMEOUT_MS = 30000

SHORT, HOLD, DOUBLE, DOUBLE_HOLD = 'short', 'hold', 'double', 'double_hold'
GESTURES = (SHORT, HOLD, DOUBLE, DOUBLE_HOLD)

NORMAL, BANK_SELECT, ENTRY = 'normal', 'bank_select', 'entry'

FOCUS_KEYS = ('A', 'B', 'C')
STAY = 'stay'   # Entry.commit(): keep the entry open, no beep
DIGITS = '0123456789'


def wait_only():
    """Double action of a key that waits for a double but does nothing on it."""


@dataclass
class Binding:
    """What one key does on one bank for the active radio."""
    short: Optional[Callable] = None
    hold: Optional[Callable] = None
    double: Optional[Callable] = None
    double_hold: Optional[Callable] = None
    focus: Optional[str] = None          # setting A, B and C act on after this key
    help: dict = field(default_factory=dict)  # gesture -> spoken help text

    @property
    def waits_for_double(self):
        return self.double is not None or self.double_hold is not None

    def action(self, gesture):
        a = getattr(self, gesture)
        return None if a is wait_only else a


class Entry:
    """An entry or selection: the keys it takes, and what D and # do.

    key() returns True when it took the key (False: beep).
    commit() returns True when the entry is done (False: beep, stay).
    """

    def key(self, key):
        return False

    def commit(self):
        return True

    def cancel(self):
        pass

    def timeout(self):
        pass


class KeypadInput:
    def __init__(self, listener, banks=9):
        self.ui = listener
        self.banks = banks
        self.bank = 1
        self.focus = {}            # bank -> setting key (None: home focus)
        self.help_mode = False
        self.mode = NORMAL
        self.entry = None
        self.one_shot_bank = None
        self._down = {}            # key -> press time
        self._fired = set()        # keys whose hold already ran (release swallowed)
        self._swallow = set()      # releases to ignore
        self._blocked = False
        self._pending = None       # (key, release_time, binding, bank)
        self._second = None        # key of a second press of the pending key
        self._last_event = 0

    # --- public --------------------------------------------------------------

    def focus_of(self, bank):
        f = self.focus.get(bank)
        return f if f is not None else self.ui.home_focus(bank)

    def set_bank(self, bank):
        self.bank = bank
        self.ui.bank_changed(bank)

    def begin_entry(self, entry):
        """Called by an action: from now on keys go to entry."""
        self.entry = entry
        self.mode = ENTRY

    def end_entry(self):
        self.entry = None
        self.mode = NORMAL

    def reset_focus(self):
        """A profile change puts every bank back on its starting focus."""
        self.focus = {}

    def press(self, key, now):
        self._last_event = now
        self.ui.interrupt()
        star_held = '*' in self._down and '*' in self._fired
        if self._down and not (star_held and key in DIGITS and self.mode == BANK_SELECT):
            if not self._blocked:
                self._blocked = True
                self.ui.beep()
            self._down[key] = now
            return
        self._down[key] = now
        if self._blocked:
            return

        if self.mode == BANK_SELECT:
            self._swallow.add(key)
            self._bank_select_key(key, one_shot=star_held)
            return
        if self.mode == ENTRY:
            self._swallow.add(key)
            self._entry_key(key)
            return

        if self._pending is not None:
            if self._pending[0] == key and now - self._pending[1] <= DOUBLE_MS:
                self._second = key
            else:
                self._flush_pending()

    def release(self, key, now):
        self._last_event = now
        self._down.pop(key, None)
        if self._blocked:
            if not self._down:
                self._blocked = False
                self._fired.clear()
                self._swallow.clear()
            return
        if key in self._swallow:
            self._swallow.discard(key)
            return
        if key in self._fired:
            self._fired.discard(key)
            return
        if self.mode != NORMAL:
            return

        if key == '*':
            self.ui.say_bank(self.bank)
            return
        if key == '#':
            self._clear()
            return
        if key == 'D':
            self.ui.beep()          # Enter with nothing pending
            return

        if self._second == key:
            self._second = None
            p = self._pending
            self._pending = None
            self._run(p[2], DOUBLE, key, p[3])
            return

        bank = self._take_bank()
        binding = self._binding(bank, key)
        if binding.waits_for_double:
            self._pending = (key, now, binding, bank)
        else:
            self._run(binding, SHORT, key, bank)

    def poll(self, now):
        # Hold
        for key, t in list(self._down.items()):
            if self._blocked or key in self._fired or now - t < LONG_MS:
                continue
            self._fired.add(key)
            if key in self._swallow:
                continue
            if self.mode != NORMAL:
                continue
            self._hold(key)
        # Pending short whose double window ran out
        if self._pending is not None and self._second is None:
            if now - self._pending[1] > DOUBLE_MS:
                self._flush_pending()
        # Entry timeout
        if self.mode != NORMAL and now - self._last_event >= ENTRY_TIMEOUT_MS:
            if self.mode == ENTRY and self.entry is not None:
                self.entry.timeout()
            self.end_entry()
            self.ui.say_timeout()

    # --- internals -------------------------------------------------------------

    def _take_bank(self):
        bank = self.one_shot_bank or self.bank
        return bank

    def _binding(self, bank, key):
        return self.ui.binding(bank, key, self.focus_of(bank)) or Binding()

    def _flush_pending(self):
        p = self._pending
        self._pending = None
        self._second = None
        if p is not None:
            self._run(p[2], SHORT, p[0], p[3])

    def _hold(self, key):
        if key == '*':
            self._flush_pending()
            self.mode = BANK_SELECT
            self.ui.say_bank_prompt()
            return
        if key == 'D':
            self._flush_pending()
            self.help_mode = not self.help_mode
            self.ui.say_help_mode(self.help_mode)
            return
        if key == '#':
            self._flush_pending()
            self._clear()
            return
        if self._second == key:
            self._second = None
            p = self._pending
            self._pending = None
            self._run(p[2], DOUBLE_HOLD, key, p[3])
            return
        self._flush_pending()
        bank = self._take_bank()
        self._run(self._binding(bank, key), HOLD, key, bank)

    def _run(self, binding, gesture, key, bank):
        if bank == self.one_shot_bank:
            self.one_shot_bank = None
        action = binding.action(gesture)
        if binding.focus and (action is not None or self.help_mode):
            self.focus[bank] = binding.focus
        if self.help_mode:
            text = binding.help.get(gesture)
            if text:
                self.ui.say_help(text)
            else:
                self.ui.beep()
            return
        if action is None:
            self.ui.beep()
            return
        self.ui.run(action)

    def _clear(self):
        self._pending = None
        self._second = None
        if self.help_mode:
            self.help_mode = False
            self.ui.say_help_mode(False)
        else:
            self.ui.beep()

    def _bank_select_key(self, key, one_shot):
        if key == '#':
            self.mode = NORMAL
            self.ui.say_cancelled()
            return
        if key in DIGITS and key != '0' and int(key) <= self.banks:
            self.mode = NORMAL
            if one_shot:
                self.one_shot_bank = int(key)
                self.ui.say_digit(key)
            else:
                self.set_bank(int(key))
            return
        self.ui.beep()

    def _entry_key(self, key):
        entry = self.entry
        if key == '#':
            entry.cancel()
            self.end_entry()
            self.ui.say_cancelled()
            return
        if key == 'D':
            result = entry.commit()
            if result == STAY:
                return
            if result:
                if self.entry is entry:
                    self.end_entry()
            else:
                self.ui.beep()
            return
        if not entry.key(key):
            self.ui.beep()
