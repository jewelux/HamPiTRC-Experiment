# Stage 2 CI-V commands, frames as in HamTRC protocol_ops_civ.cpp.
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


def frame(addr, cmd, payload):
    return bytes([0xFE, 0xFE, addr, 0xE0, cmd] + list(payload) + [0xFD])


def reply(addr, cmd, payload):
    return bytes([0xFE, 0xFE, 0xE0, addr, cmd] + list(payload) + [0xFD])


class TransmitCommandTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        radio.PREFS_PATH = os.path.join(self.tmp.name, 'prefs.json')

    def tearDown(self):
        civ._ser = None
        self.tmp.cleanup()

    def use(self, key):
        radio.select(key, remember=False)
        civ._ser = FakeSerial()
        return civ._ser

    def test_vox_delay_menu_per_radio(self):
        ser = self.use('ic705')
        radio.set_vox_delay_ms(1200)
        self.assertEqual(ser.writes[-1], frame(0xA4, 0x1A, [0x05, 0x03, 0x59, 0x12]))
        ser = self.use('ic7300')
        ser.responses += reply(0x94, 0x1A, [0x05, 0x01, 0x91, 0x05])
        self.assertEqual(radio.get_vox_delay_ms(), 500)

    def test_vox_delay_not_on_ic7100(self):
        ser = self.use('ic7100')
        with self.assertRaises(radio.NotAvailable):
            radio.get_vox_delay_ms()
        self.assertEqual(ser.writes, [])

    def test_proc_vox_mic(self):
        ser = self.use('ic7300')
        radio.set_proc(True)
        self.assertEqual(ser.writes[-1], frame(0x94, 0x16, [0x44, 0x01]))
        radio.set_vox(False)
        self.assertEqual(ser.writes[-1], frame(0x94, 0x16, [0x46, 0x00]))
        radio.set_mic_gain_percent(50)
        self.assertEqual(ser.writes[-1], frame(0x94, 0x14, [0x0B, 0x01, 0x28]))

    def test_break_in_and_pitch(self):
        ser = self.use('ic705')
        radio.set_break_in(2)
        self.assertEqual(ser.writes[-1], frame(0xA4, 0x16, [0x47, 0x02]))
        self.assertEqual(civ.cw_pitch_raw_to_hz(0), 300)
        self.assertEqual(civ.cw_pitch_raw_to_hz(255), 900)
        self.assertEqual(civ.cw_pitch_raw_to_hz(civ.cw_pitch_hz_to_raw(600)), 600)

    def test_ctcss_both_tones(self):
        ser = self.use('ic705')
        radio.set_ctcss_tenths(885)
        self.assertEqual(ser.writes[-2], frame(0xA4, 0x1B, [0x00, 0x00, 0x08, 0x85]))
        self.assertEqual(ser.writes[-1], frame(0xA4, 0x1B, [0x01, 0x00, 0x08, 0x85]))
        self.assertEqual(civ.tone_decode([0x00, 0x12, 0x30]), 1230)

    def test_band_stack(self):
        ser = self.use('ic7300')
        ser.responses += reply(0x94, 0x03, [0x00, 0x00, 0x10, 0x07, 0x00])       # 7.100 MHz
        ser.responses += reply(0x94, 0x1A, [0x01, 0x03, 0x02,
                                            0x00, 0x50, 0x07, 0x07, 0x00, 0x03, 0x02])
        self.assertEqual(radio.get_band_stack(2), (7_075_000, 'CW', 2))
        self.assertEqual(ser.writes[-1], frame(0x94, 0x1A, [0x01, 0x03, 0x02]))
        self.assertEqual(civ.band_code(14_074_000), 0x05)
        self.assertEqual(civ.band_code(144_300_000), 0x0B)


if __name__ == '__main__':
    unittest.main()
