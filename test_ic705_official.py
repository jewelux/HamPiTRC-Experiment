import unittest

import ic705


class FakeSerial:
    def __init__(self, responses=None):
        self.writes = []
        self.responses = bytearray(responses or b"")
        self.raise_on_read = False

    def write(self, data):
        self.writes.append(bytes(data))

    def read(self, size=1):
        if self.raise_on_read:
            raise ic705.serial.SerialException("device disconnected")
        if not self.responses:
            return b""
        data = self.responses[:size]
        del self.responses[:size]
        return bytes(data)

    def reset_input_buffer(self):
        pass


def frame(cmd, payload=None):
    data = [0xFE, 0xFE, ic705.CIV_ADDR, ic705.CIV_CTRL, cmd]
    if payload:
        data.extend(payload)
    data.append(0xFD)
    return bytes(data)


def reply(cmd, payload=None):
    data = [0xFE, 0xFE, ic705.CIV_CTRL, ic705.CIV_ADDR, cmd]
    if payload:
        data.extend(payload)
    data.append(0xFD)
    return bytes(data)


class Ic705OfficialCommandTests(unittest.TestCase):
    def setUp(self):
        ic705._ser = FakeSerial()

    def test_monitor_uses_official_16_45_not_1c_02(self):
        ic705.set_monitor(True)
        self.assertEqual(ic705._ser.writes[-1], frame(0x16, [0x45, 0x01]))

    def test_filter_shape_uses_official_16_56(self):
        ic705.set_filter_shape("soft")
        self.assertEqual(ic705._ser.writes[-1], frame(0x16, [0x56, 0x01]))

    def test_transceive_uses_official_menu_0131(self):
        ic705.set_transceive(True)
        self.assertEqual(ic705._ser.writes[-1], frame(0x1A, [0x05, 0x01, 0x31, 0x01]))

    def test_tuner_uses_official_1c_01(self):
        ic705.start_tune()
        self.assertEqual(ic705._ser.writes[-1], frame(0x1C, [0x01, 0x02]))

    def test_xfc_uses_official_1c_02(self):
        ic705.set_xfc(True)
        self.assertEqual(ic705._ser.writes[-1], frame(0x1C, [0x02, 0x01]))

    def test_notch_width_uses_official_16_57(self):
        ic705.set_notch_width(2)
        self.assertEqual(ic705._ser.writes[-1], frame(0x16, [0x57, 0x02]))

    def test_preamp_uses_official_16_02(self):
        ic705.set_preamp(1)
        self.assertEqual(ic705._ser.writes[-1], frame(0x16, [0x02, 0x01]))

    def test_agc_uses_official_16_12(self):
        ic705.set_agc(3)
        self.assertEqual(ic705._ser.writes[-1], frame(0x16, [0x12, 0x03]))

    def test_attenuator_uses_official_11(self):
        ic705.set_att(20)
        self.assertEqual(ic705._ser.writes[-1], frame(0x11, [0x20]))

    def test_duplex_uses_official_0f_codes(self):
        ic705.set_duplex(-1)
        self.assertEqual(ic705._ser.writes[-1], frame(0x0F, [0x11]))
        ic705.set_duplex(1)
        self.assertEqual(ic705._ser.writes[-1], frame(0x0F, [0x12]))

    def test_tone_digital_squelch_commands(self):
        ic705.set_tone_squelch_mode(2)
        self.assertEqual(ic705._ser.writes[-1], frame(0x16, [0x5D, 0x02]))
        ic705.set_dsql_csql(1)
        self.assertEqual(ic705._ser.writes[-1], frame(0x16, [0x5B, 0x01]))

    def test_memory_and_scan_commands(self):
        ic705.select_memory_channel(12)
        self.assertEqual(ic705._ser.writes[-1], frame(0x08, [0x00, 0x12]))
        ic705.scan_memory()
        self.assertEqual(ic705._ser.writes[-1], frame(0x0E, [0x22]))

    def test_dv_and_gps_commands(self):
        ic705.set_dv_fast_data(True)
        self.assertEqual(ic705._ser.writes[-1], frame(0x22, [0x03, 0x01]))
        ic705.set_gps_select(3)
        self.assertEqual(ic705._ser.writes[-1], frame(0x23, [0x01, 0x03]))

    def test_rit_offset_encoding(self):
        ic705.set_rit_offset_hz(-1234)
        self.assertEqual(ic705._ser.writes[-1], frame(0x21, [0x00, 0x34, 0x12, 0x01]))

    def test_tx_frequency_query_decodes_official_1c_03(self):
        hz = 14_250_000
        ic705._ser = FakeSerial(reply(0x1C, [0x03] + ic705._freq_to_bcd(hz)))
        self.assertEqual(ic705.get_tx_freq(), hz)
        self.assertEqual(ic705._ser.writes[-1], frame(0x1C, [0x03]))

    def test_query_ignores_unrelated_frames_before_command_reply(self):
        hz = 14_099_000
        unrelated = reply(0x15, [0x12, 0x00, 0x48])
        ic705._ser = FakeSerial(unrelated + reply(0x03, ic705._freq_to_bcd(hz)))
        self.assertEqual(ic705.get_freq(), hz)
        self.assertEqual(ic705._ser.writes[-1], frame(0x03))

    def test_query_ignores_same_command_with_different_subcommand(self):
        unrelated = reply(0x15, [0x02, 0x00, 0x00])
        ic705._ser = FakeSerial(unrelated + reply(0x15, [0x12, 0x00, 0x48]))
        self.assertEqual(ic705.get_swr(), 1.5)
        self.assertEqual(ic705._ser.writes[-1], frame(0x15, [0x12]))

    def test_serial_read_exception_returns_unavailable_instead_of_crashing(self):
        ic705._ser = FakeSerial()
        ic705._ser.raise_on_read = True
        self.assertIsNone(ic705.get_tx_freq())
        self.assertEqual(ic705._ser.writes[-1], frame(0x1C, [0x03]))

    def test_filter_number_comes_from_mode_filter_query(self):
        ic705._ser = FakeSerial(reply(0x04, [0x01, 0x02]))
        self.assertEqual(ic705.get_filter_width(), 2)
        self.assertEqual(ic705._ser.writes[-1], frame(0x04))

    def test_power_meter_uses_ic705_scale(self):
        ic705._ser = FakeSerial(reply(0x15, [0x11, 0x01, 0x43]))
        self.assertEqual(ic705.get_power_meter_percent(), 50)
        ic705._ser = FakeSerial(reply(0x15, [0x11, 0x02, 0x13]))
        self.assertEqual(ic705.get_power_meter_percent(), 100)

    def test_swr_meter_uses_ic705_scale(self):
        ic705._ser = FakeSerial(reply(0x15, [0x12, 0x00, 0x48]))
        self.assertEqual(ic705.get_swr(), 1.5)
        ic705._ser = FakeSerial(reply(0x15, [0x12, 0x00, 0x80]))
        self.assertEqual(ic705.get_swr(), 2.0)
        ic705._ser = FakeSerial(reply(0x15, [0x12, 0x01, 0x20]))
        self.assertEqual(ic705.get_swr(), 3.0)


if __name__ == "__main__":
    unittest.main()
