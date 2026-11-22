import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.dirname(__file__))
import fakes  # noqa: F401
import civ
import radio
import radio_profiles
from radio_profiles import get_profile


class ProfileTableTests(unittest.TestCase):
    def test_table_is_consistent(self):
        self.assertEqual(radio_profiles.validate(), [])

    def test_factory_addresses(self):
        # CI-V reference guides and Hamlib (ic705.c, ic7300.c, ic7100.c).
        self.assertEqual(get_profile('ic705').civ_addr, 0xA4)
        self.assertEqual(get_profile('ic7300').civ_addr, 0x94)
        self.assertEqual(get_profile('ic7100').civ_addr, 0x88)

    def test_ic7100_baud_limit(self):
        self.assertLessEqual(max(get_profile('ic7100').bauds), 19200)

    def test_transceive_menu_items(self):
        self.assertEqual(get_profile('ic705').transceive_menu_item, 0x0131)
        self.assertEqual(get_profile('ic7300').transceive_menu_item, 0x0071)

    def test_ic705_keeps_everything_of_0_7_0(self):
        caps = get_profile('ic705').caps
        yaesu_only = {'keyer', 'cw_speed', 'cw_delay', 'power_switch', 'radio_id'}
        for name in radio_profiles.capability_names():
            if name not in yaesu_only:
                self.assertTrue(getattr(caps, name), name)

    def test_hf_radio_has_no_dstar(self):
        caps = get_profile('ic7300').caps
        self.assertFalse(caps.dsql_csql)
        self.assertFalse(caps.dv_data)
        self.assertFalse(caps.gps)
        self.assertNotIn('DV', get_profile('ic7300').modes)

    def test_every_gated_function_exists_somewhere(self):
        import yaesu_cat
        for name, feature in radio.FEATURE_OF.items():
            self.assertTrue(hasattr(civ, name) or hasattr(yaesu_cat, name), name)
            self.assertIn(feature, radio_profiles.capability_names(), name)

    def test_every_yaesu_capability_has_its_functions(self):
        import yaesu_cat
        for fn in ('get_freq', 'get_mode', 'get_nr', 'get_nr_level', 'get_agc', 'get_att',
                   'get_ctcss_tenths', 'get_keyer', 'get_cw_speed', 'get_power_state'):
            self.assertTrue(hasattr(yaesu_cat, fn), fn)


if __name__ == '__main__':
    unittest.main()
