import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.dirname(__file__))
import fakes  # noqa: F401  (pyserial stand-in when it is not installed)
import civ


class FakeSerial:
    def __init__(self, responses=None):
        self.writes = []
        self.responses = bytearray(responses or b"")
        self.raise_on_read = False

    def write(self, data):
        self.writes.append(bytes(data))

    def read(self, size=1):
        if self.raise_on_read:
            raise civ.serial.SerialException("device disconnected")
        if not self.responses:
            return b""
        data = self.responses[:size]
        del self.responses[:size]
        return bytes(data)

    def reset_input_buffer(self):
        pass


def frame(cmd, payload=None):
    data = [0xFE, 0xFE, civ.CIV_ADDR, civ.CIV_CTRL, cmd]
    if payload:
        data.extend(payload)
    data.append(0xFD)
    return bytes(data)


def reply(cmd, payload=None):
    data = [0xFE, 0xFE, civ.CIV_CTRL, civ.CIV_ADDR, cmd]
    if payload:
        data.extend(payload)
    data.append(0xFD)
    return bytes(data)


class CivCommandTests(unittest.TestCase):
    def setUp(self):
        civ.configure(0xA4, 115200, 0x0131)
        civ._ser = FakeSerial()

    def test_monitor_uses_official_16_45_not_1c_02(self):
        civ.set_monitor(True)
        self.assertEqual(civ._ser.writes[-1], frame(0x16, [0x45, 0x01]))

    def test_filter_shape_uses_official_16_56(self):
        civ.set_filter_shape("soft")
        self.assertEqual(civ._ser.writes[-1], frame(0x16, [0x56, 0x01]))

    def test_transceive_uses_official_menu_0131(self):
        civ.set_transceive(True)
        self.assertEqual(civ._ser.writes[-1], frame(0x1A, [0x05, 0x01, 0x31, 0x01]))

    def test_tuner_uses_official_1c_01(self):
        civ.start_tune()
        self.assertEqual(civ._ser.writes[-1], frame(0x1C, [0x01, 0x02]))

    def test_xfc_uses_official_1c_02(self):
        civ.set_xfc(True)
        self.assertEqual(civ._ser.writes[-1], frame(0x1C, [0x02, 0x01]))

    def test_notch_width_uses_official_16_57(self):
        civ.set_notch_width(2)
        self.assertEqual(civ._ser.writes[-1], frame(0x16, [0x57, 0x02]))

    def test_preamp_uses_official_16_02(self):
        civ.set_preamp(1)
        self.assertEqual(civ._ser.writes[-1], frame(0x16, [0x02, 0x01]))

    def test_agc_uses_official_16_12(self):
        civ.set_agc(3)
        self.assertEqual(civ._ser.writes[-1], frame(0x16, [0x12, 0x03]))

    def test_attenuator_uses_official_11(self):
        civ.set_att(20)
        self.assertEqual(civ._ser.writes[-1], frame(0x11, [0x20]))

    def test_duplex_uses_official_0f_codes(self):
        civ.set_duplex(-1)
        self.assertEqual(civ._ser.writes[-1], frame(0x0F, [0x11]))
        civ.set_duplex(1)
        self.assertEqual(civ._ser.writes[-1], frame(0x0F, [0x12]))

    def test_tone_digital_squelch_commands(self):
        civ.set_tone_squelch_mode(2)
        self.assertEqual(civ._ser.writes[-1], frame(0x16, [0x5D, 0x02]))
        civ.set_dsql_csql(1)
        self.assertEqual(civ._ser.writes[-1], frame(0x16, [0x5B, 0x01]))

    def test_memory_and_scan_commands(self):
        civ.select_memory_channel(12)
        self.assertEqual(civ._ser.writes[-1], frame(0x08, [0x00, 0x12]))
        civ.scan_memory()
        self.assertEqual(civ._ser.writes[-1], frame(0x0E, [0x22]))

    def test_dv_and_gps_commands(self):
        civ.set_dv_fast_data(True)
        self.assertEqual(civ._ser.writes[-1], frame(0x22, [0x03, 0x01]))
        civ.set_gps_select(3)
        self.assertEqual(civ._ser.writes[-1], frame(0x23, [0x01, 0x03]))

    def test_rit_offset_encoding(self):
        civ.set_rit_offset_hz(-1234)
        self.assertEqual(civ._ser.writes[-1], frame(0x21, [0x00, 0x34, 0x12, 0x01]))

    def test_tx_frequency_query_decodes_official_1c_03(self):
        hz = 14_250_000
        civ._ser = FakeSerial(reply(0x1C, [0x03] + civ._freq_to_bcd(hz)))
        self.assertEqual(civ.get_tx_freq(), hz)
        self.assertEqual(civ._ser.writes[-1], frame(0x1C, [0x03]))

    def test_query_ignores_unrelated_frames_before_command_reply(self):
        hz = 14_099_000
        unrelated = reply(0x15, [0x12, 0x00, 0x48])
        civ._ser = FakeSerial(unrelated + reply(0x03, civ._freq_to_bcd(hz)))
        self.assertEqual(civ.get_freq(), hz)
        self.assertEqual(civ._ser.writes[-1], frame(0x03))

    def test_query_ignores_same_command_with_different_subcommand(self):
        unrelated = reply(0x15, [0x02, 0x00, 0x00])
        civ._ser = FakeSerial(unrelated + reply(0x15, [0x12, 0x00, 0x48]))
        self.assertEqual(civ.get_swr(), 1.5)
        self.assertEqual(civ._ser.writes[-1], frame(0x15, [0x12]))

    def test_serial_read_exception_returns_unavailable_instead_of_crashing(self):
        civ._ser = FakeSerial()
        civ._ser.raise_on_read = True
        self.assertIsNone(civ.get_tx_freq())
        self.assertEqual(civ._ser.writes[-1], frame(0x1C, [0x03]))

    def test_filter_number_comes_from_mode_filter_query(self):
        civ._ser = FakeSerial(reply(0x04, [0x01, 0x02]))
        self.assertEqual(civ.get_filter_width(), 2)
        self.assertEqual(civ._ser.writes[-1], frame(0x04))

    def test_power_meter_uses_ic705_scale(self):
        civ._ser = FakeSerial(reply(0x15, [0x11, 0x01, 0x43]))
        self.assertEqual(civ.get_power_meter_percent(), 50)
        civ._ser = FakeSerial(reply(0x15, [0x11, 0x02, 0x13]))
        self.assertEqual(civ.get_power_meter_percent(), 100)

    def test_swr_meter_uses_ic705_scale(self):
        civ._ser = FakeSerial(reply(0x15, [0x12, 0x00, 0x48]))
        self.assertEqual(civ.get_swr(), 1.5)
        civ._ser = FakeSerial(reply(0x15, [0x12, 0x00, 0x80]))
        self.assertEqual(civ.get_swr(), 2.0)
        civ._ser = FakeSerial(reply(0x15, [0x12, 0x01, 0x20]))
        self.assertEqual(civ.get_swr(), 3.0)


if __name__ == "__main__":
    unittest.main()
