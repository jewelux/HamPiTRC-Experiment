# Key presses end to end: keypad -> bank binding -> radio gate -> CI-V frame,
# with speech recorded instead of played.
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.dirname(__file__))
import fakes
from fakes import FakeSerial
import civ
import radio
import banks
import pihamtrc
from keypad_input import LONG_MS, DOUBLE_MS
from ui import Ui, frequency_words


class FakeSpeech:
    def __init__(self):
        self.log = []

    def say(self, text):
        self.log.append(text)

    def beep(self):
        self.log.append('beep')

    def stop(self):
        pass

    def set_volume(self, level):
        pass

    def set_speed(self, speed):
        pass


def reply(cmd, payload):
    return bytes([0xFE, 0xFE, civ.CIV_CTRL, civ.CIV_ADDR, cmd] + list(payload) + [0xFD])


class FakeDevice:
    def __init__(self, path, name, keypad):
        self.path = path
        self.name = name
        self._keys = [82, 73] if keypad else [30]

    def capabilities(self):
        return {1: self._keys}


class BankTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        radio.PREFS_PATH = os.path.join(self.tmp.name, 'prefs.json')
        radio.set_experimental(False)
        self.use('ic705')
        self.speech = FakeSpeech()
        self.ui = Ui(self.speech, banks.lookup)
        self.k = self.ui.keypad
        self.t = 1000

    def tearDown(self):
        civ._ser = None
        radio.set_experimental(False)
        self.tmp.cleanup()

    def use(self, key):
        radio.select(key, remember=False)
        civ._ser = FakeSerial()
        self.ser = civ._ser

    def answer(self, cmd, payload):
        self.ser.responses += reply(cmd, payload)

    def tap(self, key):
        self.k.press(key, self.t)
        self.t += 50
        self.k.release(key, self.t)
        self.t += DOUBLE_MS + 10
        self.k.poll(self.t)

    def hold(self, key):
        self.k.press(key, self.t)
        self.t += LONG_MS + 10
        self.k.poll(self.t)
        self.k.release(key, self.t)
        self.t += 10

    def bank(self, n):
        self.hold('*')
        self.tap(str(n))

    def said(self):
        return self.speech.log[-1]

    def test_frequency_words(self):
        self.assertEqual(frequency_words(7_123_450), '7 point 1 2 3 4 5')
        self.assertEqual(frequency_words(14_100_000), '1 4 point 1')
        self.assertEqual(frequency_words(7_000_000), '7 point 0')

    def test_bank1_frequency(self):
        self.answer(0x03, [0x00, 0x00, 0x10, 0x07, 0x00])   # 7.100000 MHz
        self.tap('0')
        self.assertEqual(self.said(), 'frequency 7 point 1')

    def test_frequency_entry_in_mhz_with_star(self):
        self.hold('0')
        self.assertEqual(self.said(), 'frequency please')
        for key in '14*25':
            self.tap(key)
        self.tap('D')
        self.assertEqual(self.ser.writes[-1],
                         bytes([0xFE, 0xFE, 0xA4, 0xE0, 0x05, 0x00, 0x00, 0x25, 0x14, 0x00, 0xFD]))
        self.assertEqual(self.said(), 'frequency 1 4 point 2 5 ok')

    def test_verbose_off_gives_value_only(self):
        self.ui.verbose = False
        self.answer(0x16, [0x40, 0x01])
        self.bank(2)
        self.tap('1')
        self.assertEqual(self.said(), 'on')

    def test_nr_level_focus_and_steps(self):
        self.bank(2)
        self.answer(0x14, [0x06, 0x00, 0x51])   # 51 -> 20 percent
        self.k.press('1', self.t)                # double press: NR level, focus
        self.k.release('1', self.t + 30)
        self.k.press('1', self.t + 80)
        self.k.release('1', self.t + 110)
        self.t += 400
        self.k.poll(self.t)
        self.assertEqual(self.said(), 'noise reduction level 20 percent')
        self.answer(0x14, [0x06, 0x00, 0x51])
        self.answer(0x14, [0x06, 0x00, 0x64])   # read back 64 -> 25 percent
        self.tap('B')
        self.assertEqual(self.ser.writes[-2][:6], bytes([0xFE, 0xFE, 0xA4, 0xE0, 0x14, 0x06]))
        self.assertEqual(self.said(), 'noise reduction level 25 percent')

    def test_focus_none_says_not_available(self):
        self.tap('B')
        self.assertEqual(self.said(), 'focus not available')

    def test_rf_power_waits_for_d(self):
        self.answer(0x14, [0x0A, 0x01, 0x28])   # 128 of 255 -> 5.0 W on the IC-705
        self.tap('6')                            # focus RF power
        self.answer(0x14, [0x0A, 0x01, 0x28])
        n = len(self.ser.writes)
        self.tap('B')
        self.assertEqual(self.said(), 'power 6 watts please')
        self.tap('B')
        self.assertEqual(self.said(), '7 watts')
        self.assertEqual(len([w for w in self.ser.writes[n:] if w[5:6] == b'\x0a' and len(w) > 7]), 0)
        self.answer(0x14, [0x0A, 0x01, 0x79])   # read back 179 -> 7 W
        self.tap('D')
        self.assertIn(bytes([0xFE, 0xFE, 0xA4, 0xE0, 0x14, 0x0A, 0x01, 0x78, 0xFD]), self.ser.writes)
        self.assertEqual(self.said(), 'power 7 watts ok')

    def test_mode_pick(self):
        self.hold('9')
        self.assertEqual(self.said(), 'choose mode')
        self.tap('2')
        self.assertEqual(self.said(), 'USB')
        self.answer(0x04, [0x01, 0x01])
        self.tap('D')
        self.assertIn(bytes([0xFE, 0xFE, 0xA4, 0xE0, 0x06, 0x01, 0x01, 0xFD]), self.ser.writes)
        self.assertEqual(self.said(), 'mode USB ok')

    def test_missing_feature_on_ic7300(self):
        self.use('ic7300')
        self.ui.keypad.reset_focus()
        self.bank(6)
        self.tap('0')
        self.assertEqual(self.said(), 'repeater not available')
        self.assertEqual(self.ser.writes, [])

    def test_experimental_opens_features(self):
        self.use('ic7300')
        self.bank(9)
        self.hold('0')
        self.assertEqual(self.said(), 'experimental on ok')
        self.bank(6)
        self.tap('0')
        self.assertEqual(self.ser.writes[-1], bytes([0xFE, 0xFE, 0x94, 0xE0, 0x0F, 0x10, 0xFD]))

    def test_help_mode_says_and_sends_nothing(self):
        self.hold('D')
        self.assertEqual(self.said(), 'help on')
        self.hold('9')
        self.assertEqual(self.said(), 'choose mode')
        self.assertEqual(self.ser.writes, [])
        self.tap('#')
        self.assertEqual(self.said(), 'help off')

    def test_profile_focus_on_bank9(self):
        self.bank(9)
        self.tap('B')                       # next profile, no serial port in tests
        self.assertEqual(radio.current().key, 'ic7300')
        self.assertEqual(self.said(), 'I C seventy-three hundred selected, not connected')
        self.tap('0' if False else 'A')
        self.assertEqual(self.said(), 'profile I C seventy-three hundred')

    def test_volume_entry(self):
        self.bank(9)
        self.hold('7')
        self.assertEqual(self.said(), 'volume please')
        self.tap('8')
        self.tap('D')
        self.assertEqual(self.ui.volume, 8)
        self.assertEqual(self.said(), 'volume 8 ok')

    def test_rit_home_focus(self):
        self.bank(5)
        self.answer(0x21, [0x00, 0x00, 0x00, 0x00])
        self.answer(0x21, [0x00, 0x10, 0x00, 0x00])
        self.tap('B')
        self.assertEqual(self.said(), 'R I T plus 10 hertz')

    def test_pick_keyboard_prefers_keypad_device(self):
        devices = [
            FakeDevice('/dev/input/event11', 'HCT USB Entry Keyboard Consumer Control', False),
            FakeDevice('/dev/input/event10', 'HCT USB Entry Keyboard', True),
            FakeDevice('/dev/input/event3', 'Raspberry Pi 500 Keyboard', False),
        ]
        self.assertEqual(pihamtrc.pick_keyboard(devices, 'HCT').path, '/dev/input/event10')
        self.assertIsNone(pihamtrc.pick_keyboard(devices, 'Cherry'))
        self.assertEqual(pihamtrc.pick_keyboard(devices, '').path, '/dev/input/event10')


if __name__ == '__main__':
    unittest.main()


class EveryKeyTests(unittest.TestCase):
    """Every key, gesture and radio: runs without an exception, and has help."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        radio.PREFS_PATH = os.path.join(self.tmp.name, 'prefs.json')
        import yaesu_cat
        self.timeout, civ.QUERY_TIMEOUT = civ.QUERY_TIMEOUT, 0.01
        self.retries, civ.QUERY_RETRIES = civ.QUERY_RETRIES, 1
        self.ytimeout, yaesu_cat.TIMEOUT = yaesu_cat.TIMEOUT, 0.01
        self.yretries, yaesu_cat.RETRIES = yaesu_cat.RETRIES, 1

    def tearDown(self):
        import yaesu_cat
        civ.QUERY_TIMEOUT, civ.QUERY_RETRIES = self.timeout, self.retries
        yaesu_cat.TIMEOUT, yaesu_cat.RETRIES = self.ytimeout, self.yretries
        civ._ser = None
        yaesu_cat._ser = None
        radio.set_experimental(False)
        self.tmp.cleanup()

    def test_all(self):
        from keypad_input import GESTURES
        import radio_profiles
        for experimental in (False, True):
            for key in radio_profiles.profile_keys():
                radio.set_experimental(experimental)
                radio.select(key, remember=False)
                for bank in range(1, 10):
                    for k in '0123456789ABC':
                        speech = FakeSpeech()
                        ui = Ui(speech, banks.lookup)
                        ui.keypad.bank = bank
                        focus = ui.keypad.focus_of(bank)
                        b = banks.lookup(ui, bank, k, focus)
                        if b is None:
                            continue
                        for g in GESTURES:
                            action = b.action(g)
                            if action is None:
                                continue
                            with self.subTest(radio=key, bank=bank, key=k, gesture=g,
                                              experimental=experimental):
                                self.assertTrue(b.help.get(g), 'no help text')
                                radio.select(key, remember=False)
                                radio.proto()._ser = FakeSerial()
                                ui.run(action)
                                if ui.keypad.entry is not None:
                                    ui.keypad.end_entry()
