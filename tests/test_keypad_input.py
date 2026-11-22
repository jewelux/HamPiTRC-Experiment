# The keypad state machine alone, with a recording listener and a test clock.
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from keypad_input import (KeypadInput, Binding, Entry, wait_only, LONG_MS, DOUBLE_MS,
                          ENTRY_TIMEOUT_MS, SHORT, HOLD, DOUBLE, DOUBLE_HOLD)


class Listener:
    def __init__(self):
        self.log = []
        self.bindings = {}

    def interrupt(self):
        self.log.append('stop')

    def beep(self):
        self.log.append('beep')

    def home_focus(self, bank):
        return {5: 'rit'}.get(bank)

    def binding(self, bank, key, focus):
        b = self.bindings.get((bank, key))
        if b is None and key in 'ABC':
            return Binding(short=lambda: self.log.append('focus ' + str(focus)))
        return b

    def run(self, action):
        action()

    def say_bank(self, bank):
        self.log.append('bank %d' % bank)

    def say_bank_prompt(self):
        self.log.append('bank please')

    def bank_changed(self, bank):
        self.log.append('bank %d' % bank)

    def say_digit(self, key):
        self.log.append(key)

    def say_help(self, text):
        self.log.append('help ' + text)

    def say_help_mode(self, on):
        self.log.append('help on' if on else 'help off')

    def say_cancelled(self):
        self.log.append('cancelled')

    def say_timeout(self):
        self.log.append('timeout')


class KeypadInputTests(unittest.TestCase):
    def setUp(self):
        self.l = Listener()
        self.k = KeypadInput(self.l)
        self.t = 1000

    def rec(self, name):
        return lambda: self.l.log.append(name)

    def bind(self, bank, key, **kw):
        self.l.bindings[(bank, key)] = Binding(**kw)

    def tap(self, key, ms=50):
        self.k.press(key, self.t)
        self.t += ms
        self.k.poll(self.t)
        self.k.release(key, self.t)
        self.k.poll(self.t)

    def hold(self, key):
        self.k.press(key, self.t)
        self.t += LONG_MS + 10
        self.k.poll(self.t)
        self.k.release(key, self.t)

    def wait(self, ms):
        self.t += ms
        self.k.poll(self.t)

    def events(self):
        return [e for e in self.l.log if e != 'stop']

    def test_short_acts_on_release_without_double(self):
        self.bind(1, '7', short=self.rec('smeter'))
        self.tap('7')
        self.assertEqual(self.events(), ['smeter'])

    def test_long_acts_at_hold_and_swallows_release(self):
        self.bind(1, '9', short=self.rec('say'), hold=self.rec('pick'))
        self.hold('9')
        self.assertEqual(self.events(), ['pick'])

    def test_double_and_waiting_short(self):
        self.bind(1, '0', short=self.rec('freq'), double=self.rec('round'))
        self.tap('0')
        self.assertEqual(self.events(), [])          # waits for a double
        self.wait(DOUBLE_MS + 5)
        self.assertEqual(self.events(), ['freq'])
        self.tap('0')
        self.wait(50)
        self.tap('0')
        self.assertEqual(self.events(), ['freq', 'round'])

    def test_double_hold(self):
        self.bind(2, '1', short=self.rec('nr'), hold=self.rec('toggle'),
                  double=self.rec('level'), double_hold=self.rec('entry'), focus='nr_level')
        self.k.bank = 2
        self.tap('1')
        self.wait(30)
        self.hold('1')
        self.assertEqual(self.events(), ['entry'])
        self.assertEqual(self.k.focus_of(2), 'nr_level')

    def test_wait_only_runs_short_once(self):
        self.bind(1, '1', short=self.rec('rxtx'), double=wait_only)
        self.tap('1')
        self.wait(30)
        self.tap('1')
        self.wait(DOUBLE_MS + 5)
        self.assertEqual(self.events(), ['beep'])  # double has no action: free

    def test_free_key_beeps(self):
        self.tap('3')
        self.assertEqual(self.events(), ['beep'])

    def test_two_keys_at_once_beep_and_ignore(self):
        self.bind(1, '7', short=self.rec('smeter'))
        self.bind(1, '8', short=self.rec('swr'))
        self.k.press('7', self.t)
        self.k.press('8', self.t + 10)
        self.k.release('8', self.t + 20)
        self.k.release('7', self.t + 30)
        self.k.poll(self.t + 1000)
        self.assertEqual(self.events(), ['beep'])

    def test_bank_select_and_one_shot(self):
        self.bind(3, '0', short=self.rec('split'))
        self.hold('*')
        self.assertEqual(self.events(), ['bank please'])
        self.tap('3')
        self.assertEqual(self.k.bank, 3)
        # one-shot: hold *, press 1 while * is down, then a key on bank 1
        self.bind(1, '7', short=self.rec('smeter'))
        self.k.press('*', self.t)
        self.t += LONG_MS + 10
        self.k.poll(self.t)
        self.k.press('1', self.t)
        self.k.release('1', self.t + 5)
        self.k.release('*', self.t + 10)
        self.t += 20
        self.tap('7')
        self.assertEqual(self.k.bank, 3)
        self.assertIn('smeter', self.events())
        self.tap('0')
        self.assertEqual(self.events()[-1], 'split')

    def test_star_short_says_bank(self):
        self.tap('*')
        self.assertEqual(self.events(), ['bank 1'])

    def test_help_mode(self):
        b = Binding(short=self.rec('nr'), focus='nr_level', help={SHORT: 'noise reduction'})
        self.l.bindings[(1, '1')] = b
        self.hold('D')
        self.tap('1')
        self.assertEqual(self.events(), ['help on', 'help noise reduction'])
        self.assertEqual(self.k.focus_of(1), 'nr_level')
        self.tap('#')
        self.assertEqual(self.events()[-1], 'help off')
        self.tap('1')
        self.assertEqual(self.events()[-1], 'nr')

    def test_home_focus(self):
        self.k.bank = 5
        self.tap('B')
        self.assertEqual(self.events(), ['focus rit'])

    def test_entry_takes_keys_on_press_and_times_out(self):
        log = []

        class E(Entry):
            def key(self, key):
                log.append(key)
                return key.isdigit()

            def commit(self):
                log.append('commit')
                return True
        self.k.begin_entry(E())
        self.k.press('1', self.t)
        self.assertEqual(log, ['1'])
        self.k.release('1', self.t + 900)
        self.k.poll(self.t + 900)                   # no hold in an entry
        self.tap('A')
        self.assertEqual(self.events()[-1], 'beep')  # not taken
        self.tap('D')
        self.assertEqual(log[-1], 'commit')
        self.assertEqual(self.k.mode, 'normal')
        self.k.begin_entry(E())
        self.wait(ENTRY_TIMEOUT_MS + 1)
        self.assertEqual(self.events()[-1], 'timeout')
        self.assertEqual(self.k.mode, 'normal')

    def test_entry_cancel(self):
        self.k.begin_entry(Entry())
        self.tap('#')
        self.assertEqual(self.events()[-1], 'cancelled')
        self.assertEqual(self.k.mode, 'normal')


if __name__ == '__main__':
    unittest.main()
