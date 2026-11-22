# FTDX10 ASCII CAT, commands and encodings as in HamTRC (protocol_ops_ascii.cpp,
# cat_setting_codec.cpp), and FTDX10 keys end to end.
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.dirname(__file__))
import fakes
from fakes import FakeSerial
import radio
import banks
import yaesu_cat
from keypad_input import LONG_MS, DOUBLE_MS
from ui import Ui
from test_keypad_banks import FakeSpeech


class YaesuTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        radio.PREFS_PATH = os.path.join(self.tmp.name, 'prefs.json')
        self.timeout, yaesu_cat.TIMEOUT = yaesu_cat.TIMEOUT, 0.05
        radio.select('ftdx10', remember=False)
        yaesu_cat._ser = FakeSerial()
        self.ser = yaesu_cat._ser

    def tearDown(self):
        yaesu_cat.TIMEOUT = self.timeout
        yaesu_cat._ser = None
        self.tmp.cleanup()

    def answer(self, *lines):
        for line in lines:
            self.ser.responses += line.encode('ascii')

    def sent(self):
        return [w.decode('ascii') for w in self.ser.writes]


class CommandTests(YaesuTest):
    def test_profile(self):
        p = radio.current()
        self.assertEqual((p.protocol, p.baud), ('yaesu', 38400))
        self.assertEqual(yaesu_cat.get_baudrate(), 38400)

    def test_frequency_and_mode(self):
        self.answer('FA007100000;', 'MD02;')
        self.assertEqual(radio.get_freq(), 7_100_000)
        self.assertEqual(radio.get_mode(), 'USB')
        radio.set_freq(14_074_000)
        radio.set_mode('CW-R')
        self.assertEqual(self.sent()[-2:], ['FA014074000;', 'MD07;'])

    def test_read_only_modes(self):
        self.answer('MD0C;')
        self.assertEqual(radio.get_mode(), 'DATA')

    def test_levels_in_radio_steps(self):
        self.answer('RL007;', 'NL0010;')
        self.assertEqual(radio.get_nr_level(), 7)
        self.assertEqual(radio.get_nb_level(), 10)
        radio.set_nr_level(15)
        self.assertEqual(self.sent()[-1], 'RL015;')

    def test_meters(self):
        self.answer('SM0130;', 'RM6052000;')
        self.assertEqual(radio.get_smeter(), 'S 9')
        self.assertEqual(radio.get_swr(), 1.5)
        self.assertEqual(yaesu_cat.smeter_text(0), 'S 0')
        self.assertEqual(yaesu_cat.smeter_text(255), 'S 9 plus 60')

    def test_tone_code_maps_to_icom_names(self):
        self.answer('CT02;', 'CT02;')
        self.assertTrue(radio.get_repeater_tone())
        self.assertFalse(radio.get_tsql())
        radio.set_tsql(True)
        self.assertEqual(self.sent()[-1], 'CT01;')

    def test_ctcss_index(self):
        self.answer('CN00008;')
        self.assertEqual(radio.get_ctcss_tenths(), 885)
        radio.set_ctcss_tenths(1000)
        self.assertEqual(self.sent()[-1], 'CN00012;')

    def test_delay_steps(self):
        self.assertEqual(yaesu_cat.DELAY_STEPS[0], 30)
        self.assertEqual(yaesu_cat.DELAY_STEPS[6], 300)
        self.assertEqual(len(yaesu_cat.DELAY_STEPS), 34)
        radio.set_vox_delay_ms(500)
        self.assertEqual(self.sent()[-1], 'VD08;')

    def test_pitch_and_speed(self):
        self.answer('KP30;')
        self.assertEqual(radio.get_cw_pitch_hz(), 600)
        radio.set_cw_speed(25)
        self.assertEqual(self.sent()[-1], 'KS025;')

    def test_civ_only_features_not_available(self):
        n = len(self.ser.writes)
        for fn in ('get_rit', 'get_monitor', 'get_transceive', 'get_band_stack'):
            with self.assertRaises(radio.NotAvailable, msg=fn):
                getattr(radio, fn)() if fn != 'get_band_stack' else radio.get_band_stack(1)
        self.assertEqual(len(self.ser.writes), n)


class KeyTests(YaesuTest):
    def setUp(self):
        super().setUp()
        self.speech = FakeSpeech()
        self.ui = Ui(self.speech, banks.lookup)
        self.k = self.ui.keypad
        self.t = 1000

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

    def test_frequency(self):
        self.answer('FA014074000;')
        self.tap('0')
        self.assertEqual(self.said(), 'frequency 1 4 point 0 7 4')

    def test_agc_pick_has_five_speeds(self):
        self.bank(2)
        self.hold('7')
        self.tap('1')
        self.assertEqual(self.said(), 'auto')
        self.answer('GT04;')
        self.tap('D')
        self.assertEqual(self.sent()[-2], 'GT04;')
        self.assertEqual(self.said(), 'A G C auto ok')

    def test_attenuator_steps(self):
        self.bank(2)
        self.answer('RA01;', 'RA02;')
        self.hold('9')
        self.assertEqual(self.sent()[-2], 'RA02;')
        self.assertEqual(self.said(), 'attenuator 12 dB ok')

    def test_nr_level_steps_of_one(self):
        self.bank(2)
        self.answer('RL005;')
        self.k.press('1', self.t)
        self.k.release('1', self.t + 30)
        self.k.press('1', self.t + 80)
        self.k.release('1', self.t + 110)
        self.t += 400
        self.k.poll(self.t)
        self.assertEqual(self.said(), 'noise reduction level 5')
        self.answer('RL005;', 'RL006;')
        self.tap('B')
        self.assertIn('RL006;', self.sent())

    def test_rf_power_watts(self):
        self.answer('PC050;')
        self.tap('6')
        self.assertEqual(self.said(), 'power 50 watts')
        self.answer('PC050;')
        self.tap('B')
        self.assertEqual(self.said(), 'power 55 watts please')

    def test_power_switch_and_civ_address(self):
        self.bank(8)
        self.tap('1')
        self.assertEqual(self.said(), 'C I V address not available')
        self.answer('PS1;')
        self.tap('4')
        self.assertEqual(self.said(), 'power on')

    def test_rit_not_available(self):
        self.bank(5)
        self.tap('0')
        self.assertEqual(self.said(), 'R I T not available')


if __name__ == '__main__':
    unittest.main()
