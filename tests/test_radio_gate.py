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


def reply(cmd, payload):
    return bytes([0xFE, 0xFE, civ.CIV_CTRL, civ.CIV_ADDR, cmd] + list(payload) + [0xFD])


class RadioGateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        radio.PREFS_PATH = os.path.join(self.tmp.name, 'prefs.json')

    def tearDown(self):
        civ._ser = None
        self.tmp.cleanup()

    def use(self, key, responses=b''):
        radio.select(key, remember=False)
        civ._ser = FakeSerial(responses)
        return civ._ser

    def test_select_configures_address_and_menu_item(self):
        self.use('ic7300')
        self.assertEqual(civ.get_civ_address(), 0x94)
        self.assertEqual(civ.TRANSCEIVE_MENU_ITEM, 0x0071)
        self.use('ic7100')
        self.assertEqual(civ.get_civ_address(), 0x88)
        self.assertEqual(civ.get_baudrate(), 19200)

    def test_missing_feature_sends_nothing(self):
        ser = self.use('ic7300')
        with self.assertRaises(radio.NotAvailable) as ctx:
            radio.get_dsql_csql()
        self.assertEqual(ser.writes, [])
        self.assertEqual(ctx.exception.spoken(),
                         'Digital squelch not available on I C seventy-three hundred')

    def test_present_feature_reaches_the_radio(self):
        ser = self.use('ic7300')
        ser.responses += reply(0x16, [0x40, 0x01])
        self.assertTrue(radio.get_nr())
        self.assertEqual(ser.writes[0], bytes([0xFE, 0xFE, 0x94, 0xE0, 0x16, 0x40, 0xFD]))

    def test_mode_not_on_radio(self):
        ser = self.use('ic7300')
        with self.assertRaises(radio.NotAvailable):
            radio.set_mode('DV')
        self.assertEqual(ser.writes, [])

    def test_not_connected(self):
        radio.select('ic705', remember=False)
        civ._ser = None
        with self.assertRaises(radio.NotConnected) as ctx:
            radio.get_freq_mhz()
        self.assertEqual(ctx.exception.spoken(), 'I C seven oh five not connected')

    def test_profile_and_link_are_remembered(self):
        self.use('ic7100')
        radio.select('ic7100')
        civ.set_civ_address(0x70)
        self.assertTrue(radio.remember_link())
        radio.select('ic705', remember=False)
        self.assertEqual(radio.start('ic705').key, 'ic7100')
        self.assertEqual(civ.get_civ_address(), 0x70)

    def test_serial_port_override(self):
        radio.select('ic7300', serial_ports={'ic7300': '/dev/serial/by-id/icom'}, remember=False)
        self.assertEqual(radio.serial_port(), '/dev/serial/by-id/icom')
        radio.select('ic705', serial_ports={}, remember=False)
        self.assertEqual(radio.serial_port(), '/dev/ttyACM0')


class SmeterScaleTests(unittest.TestCase):
    # Icom: 0 = S0, 120 = S9, 241 = S9 + 60 dB.
    def test_scale(self):
        self.assertEqual(civ.smeter_text(0), 'S 0')
        self.assertEqual(civ.smeter_text(67), 'S 5')
        self.assertEqual(civ.smeter_text(120), 'S 9')
        self.assertEqual(civ.smeter_text(140), 'S 9 plus 10')
        self.assertEqual(civ.smeter_text(241), 'S 9 plus 60')
        self.assertEqual(civ.smeter_text(255), 'S 9 plus 60')

    def test_reads_bcd_meter(self):
        civ.configure(0xA4, 115200, 0x0131)
        civ._ser = FakeSerial(reply(0x15, [0x02, 0x01, 0x20]))
        try:
            self.assertEqual(civ.get_smeter(), 'S 9')
        finally:
            civ._ser = None

    def test_dv_mode_code(self):
        civ.configure(0xA4, 115200, 0x0131)
        civ._ser = FakeSerial(reply(0x04, [0x17, 0x01]))
        try:
            self.assertEqual(civ.get_mode(), 'DV')
        finally:
            civ._ser = None


if __name__ == '__main__':
    unittest.main()
