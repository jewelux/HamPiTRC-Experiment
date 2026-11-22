# Key actions end to end: key -> bank handler -> radio gate -> CI-V frame,
# with speech captured instead of played.
import os
import sys
import tempfile
import types
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.dirname(__file__))
import fakes
from fakes import FakeSerial
import civ
import radio
import pihamtrc


class FakeDevice:
    def __init__(self, path, name, keypad):
        self.path = path
        self.name = name
        self._keys = [82, 73] if keypad else [30]

    def capabilities(self):
        return {1: self._keys}


class KeypadBankTests(unittest.TestCase):
    def setUp(self):
        self.spoken = []
        pihamtrc.say = self.spoken.append
        self.tmp = tempfile.TemporaryDirectory()
        radio.PREFS_PATH = os.path.join(self.tmp.name, 'prefs.json')
        pihamtrc.input_mode = None
        pihamtrc.input_digits = ''

    def tearDown(self):
        civ._ser = None
        self.tmp.cleanup()

    def use(self, key):
        radio.select(key, remember=False)
        civ._ser = FakeSerial()
        return civ._ser

    def test_feature_missing_on_radio_is_spoken(self):
        ser = self.use('ic7300')
        pihamtrc.bank = 7
        pihamtrc.handle_short('8')        # GPS status
        self.assertEqual(self.spoken[-1], 'GPS not available on I C seventy-three hundred')
        self.assertEqual(ser.writes, [])

    def test_memory_clear_needs_confirmation(self):
        ser = self.use('ic705')
        pihamtrc.bank = 7
        pihamtrc.handle_long('2')
        self.assertEqual(pihamtrc.input_mode, 'confirm_memory_clear')
        self.assertEqual(ser.writes, [])
        pihamtrc.handle_input_key('#')    # cancel
        self.assertEqual(ser.writes, [])
        self.assertEqual(self.spoken[-1], 'Cancelled')

        pihamtrc.handle_long('2')
        pihamtrc.handle_input_key('5')    # other keys do nothing
        self.assertEqual(ser.writes, [])
        pihamtrc.handle_input_key('D')
        self.assertEqual(ser.writes[-1], bytes([0xFE, 0xFE, 0xA4, 0xE0, 0x0B, 0xFD]))
        self.assertEqual(self.spoken[-1], 'Memory cleared')
        self.assertIsNone(pihamtrc.input_mode)

    def test_memory_write_needs_confirmation(self):
        ser = self.use('ic705')
        pihamtrc.bank = 7
        pihamtrc.handle_long('0')
        self.assertEqual(ser.writes, [])
        pihamtrc.handle_input_key('D')
        self.assertEqual(ser.writes[-1], bytes([0xFE, 0xFE, 0xA4, 0xE0, 0x09, 0xFD]))

    def test_profile_name_in_bank9(self):
        self.use('ic7100')
        pihamtrc.bank = 9
        pihamtrc.handle_short('A')
        self.assertEqual(self.spoken[-1], 'I C seventy-one hundred profile')

    def test_switch_radio_without_port(self):
        self.use('ic705')
        pihamtrc.bank = 9
        pihamtrc.handle_short('1')        # next radio, no serial port in tests
        self.assertEqual(radio.current().key, 'ic7300')
        self.assertEqual(self.spoken[-1], 'I C seventy-three hundred selected, not connected')
        pihamtrc.bank = 1
        pihamtrc.handle_short('0')
        self.assertEqual(self.spoken[-1], 'I C seventy-three hundred not connected')

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
