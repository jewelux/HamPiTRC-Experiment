# HamPiTRC built-in radio profiles.
#
# What a radio is: CI-V address, baud rate, serial port and what it can do.
# Modelled on the profile table of the Talking Remote Controller LX1WJ
# (firmware/radio_profile_table.cpp on its development branch). No SD card,
# no profile files: the table is part of the program.
#
# To add a radio: copy a profile below, set its link defaults, switch on only
# the capabilities its CI-V reference guide and Hamlib both list, add a row to
# docs/radio-support-matrix.md and a page under docs/radios/. See
# builder-guide.md, "Add a radio".

from dataclasses import dataclass, field, fields, replace


@dataclass(frozen=True)
class Capabilities:
    """One flag per feature group. Everything is off unless a profile sets it.

    A key whose feature is off says "<feature> not available on <radio>" and
    sends nothing to the radio.
    """
    # Bank 1: status
    freq: bool = False            # 03 / 05
    mode: bool = False            # 04 / 06
    smeter: bool = False          # 15 02
    power_meter: bool = False     # 15 11
    rf_power: bool = False        # 14 0A
    swr: bool = False             # 15 12
    tx_status: bool = False       # 1C 00
    tx_freq: bool = False         # 1C 03
    lock: bool = False            # 16 50
    # Bank 2: filter and receive DSP
    nr: bool = False              # 16 40
    nr_level: bool = False        # 14 06
    nb: bool = False              # 16 22
    nb_level: bool = False        # 14 12
    notch: bool = False           # 16 48
    notch_width: bool = False     # 16 57
    pbt: bool = False             # 14 07 / 14 08
    filter_shape: bool = False    # 16 56
    filter_width: bool = False    # filter number in 04 / 06
    preamp: bool = False          # 16 02
    att: bool = False             # 11
    agc: bool = False             # 16 12
    # Bank 3: VFO
    vfo: bool = False             # 07 00 / 01 / B0
    split: bool = False           # 0F 00 / 01
    vfo_b_direct: bool = False    # 25 / 26 (read and set the unselected VFO)
    # Bank 4: monitor, tuner, transceive
    monitor: bool = False         # 16 45
    monitor_level: bool = False   # 14 15
    transceive: bool = False      # 1A 05 <transceive_menu_item>
    tuner: bool = False           # 1C 01
    xfc: bool = False             # 1C 02
    # Bank 5: RIT
    rit: bool = False             # 21 00 / 21 01
    # Bank 6: repeater and tones
    duplex: bool = False          # 0F 10 / 11 / 12
    repeater_tone: bool = False   # 16 42
    tsql: bool = False            # 16 43
    dtcs: bool = False            # 16 4B
    tone_squelch_mode: bool = False  # 16 5D
    dsql_csql: bool = False       # 16 5B (D-STAR)
    # Bank 7: memory, scan, D-STAR, GPS
    memory: bool = False          # 08 / 09 / 0A
    memory_clear: bool = False    # 0B
    scan: bool = False            # 0E
    dv_data: bool = False         # 22 02 / 22 03
    gps: bool = False             # 23 01 / 16 5C
    # Extra meters (not on a key yet)
    alc_meter: bool = False       # 15 13
    comp_meter: bool = False      # 15 14
    vd_meter: bool = False        # 15 15
    id_meter: bool = False        # 15 16


# Spoken name of each feature, used in "<feature> not available on <radio>".
FEATURE_NAMES = {
    'freq': 'Frequency', 'mode': 'Mode', 'smeter': 'S meter',
    'power_meter': 'Power meter', 'rf_power': 'RF power', 'swr': 'SWR',
    'tx_status': 'TX status', 'tx_freq': 'TX frequency', 'lock': 'Lock',
    'nr': 'Noise reduction', 'nr_level': 'NR level', 'nb': 'Noise blanker',
    'nb_level': 'NB level', 'notch': 'Notch', 'notch_width': 'Notch width',
    'pbt': 'PBT', 'filter_shape': 'Filter shape', 'filter_width': 'Filter width',
    'preamp': 'Preamp', 'att': 'Attenuator', 'agc': 'AGC', 'vfo': 'VFO',
    'split': 'Split', 'vfo_b_direct': 'Direct VFO access',
    'monitor': 'Monitor', 'monitor_level': 'Monitor level',
    'transceive': 'Transceive', 'tuner': 'Tuner', 'xfc': 'XFC', 'rit': 'RIT',
    'duplex': 'Duplex', 'repeater_tone': 'Repeater tone', 'tsql': 'TSQL',
    'dtcs': 'DTCS', 'tone_squelch_mode': 'Tone mode',
    'dsql_csql': 'Digital squelch', 'memory': 'Memory',
    'memory_clear': 'Memory clear', 'scan': 'Scan', 'dv_data': 'DV data',
    'gps': 'GPS', 'alc_meter': 'ALC meter', 'comp_meter': 'Compression meter',
    'vd_meter': 'Voltage meter', 'id_meter': 'Current meter',
}

# CI-V mode codes (04 / 06). A profile lists the ones its radio has.
MODE_CODES = {
    'LSB': 0x00, 'USB': 0x01, 'AM': 0x02, 'CW': 0x03, 'RTTY': 0x04,
    'FM': 0x05, 'WFM': 0x06, 'CW-R': 0x07, 'RTTY-R': 0x08, 'DV': 0x17,
}

CIV_BAUDS = (4800, 9600, 19200, 38400, 57600, 115200)


@dataclass(frozen=True)
class RadioProfile:
    key: str                  # short id, used in config.py and the prefs file
    name: str                 # written name, e.g. "Icom IC-705"
    spoken: str               # how speech says it
    civ_addr: int             # factory CI-V address
    baud: int                 # default baud on the USB port
    bauds: tuple              # baud rates the radio offers
    serial_port: str          # default serial device (override in config.py)
    caps: Capabilities
    modes: tuple              # mode names it can select, see MODE_CODES
    transceive_menu_item: int = 0  # 1A 05 menu number of "CI-V Transceive"
    status: str = 'not tested'     # hardware status, as in the support matrix
    notes: str = ''


# --- IC-705 ------------------------------------------------------------------
# Everything HamPiTRC 0.7.0 did. Tested on a real IC-705 (Raspberry Pi 5,
# USB numeric keypad, PC speakers). Address A4h (CI-V guide, Hamlib).
IC705_CAPS = Capabilities(
    freq=True, mode=True, smeter=True, power_meter=True, rf_power=True,
    swr=True, tx_status=True, tx_freq=True, lock=True,
    nr=True, nr_level=True, nb=True, nb_level=True, notch=True,
    notch_width=True, pbt=True, filter_shape=True, filter_width=True,
    preamp=True, att=True, agc=True,
    vfo=True, split=True, vfo_b_direct=True,
    monitor=True, monitor_level=True, transceive=True, tuner=True, xfc=True,
    rit=True,
    duplex=True, repeater_tone=True, tsql=True, dtcs=True,
    tone_squelch_mode=True, dsql_csql=True,
    memory=True, memory_clear=True, scan=True, dv_data=True, gps=True,
    alc_meter=True, comp_meter=True, vd_meter=True, id_meter=True,
)

# --- IC-7300 -----------------------------------------------------------------
# HF/50 MHz, no D-STAR, no GPS, no repeater shift over CI-V (Hamlib has no
# rptr_shift for it), no DTCS. 25/26 and 1C 03 are always present (Hamlib
# x25x26_always, x1cx03_always). Transceive is menu 0071 (HamTRC, Hamlib).
# XFC (1C 02) left off until checked against the CI-V guide.
IC7300_CAPS = replace(
    IC705_CAPS,
    xfc=False, duplex=False, dtcs=False, tone_squelch_mode=False,
    dsql_csql=False, dv_data=False, gps=False,
)

# --- IC-7100 -----------------------------------------------------------------
# HF/VHF/UHF with D-STAR. Address 88h, max 19200 baud (Hamlib ic7100.c).
# Hamlib lists no monitor switch, no RIT command, no transceive menu item, no
# filter shape and no notch width for it, and only "possibly" 25/26 and
# 1C 03, so those stay off until tested on a radio. Repeater shift (0F 1x),
# tone and TSQL are in Hamlib. D-STAR squelch, DV data and GPS stay off
# until checked against the IC-7100 CI-V guide.
IC7100_CAPS = Capabilities(
    freq=True, mode=True, smeter=True, power_meter=True, rf_power=True,
    swr=True, tx_status=True, lock=True,
    nr=True, nr_level=True, nb=True, nb_level=True, notch=True,
    pbt=True, filter_width=True, preamp=True, att=True, agc=True,
    vfo=True, split=True,
    monitor_level=True, tuner=True,
    duplex=True, repeater_tone=True, tsql=True,
    memory=True, memory_clear=True, scan=True,
    alc_meter=True, comp_meter=True, vd_meter=True, id_meter=True,
)

HF_MODES = ('LSB', 'USB', 'CW', 'FM', 'AM', 'RTTY', 'CW-R', 'RTTY-R')

PROFILES = (
    RadioProfile(
        key='ic705', name='Icom IC-705', spoken='I C seven oh five',
        civ_addr=0xA4, baud=115200, bauds=CIV_BAUDS,
        serial_port='/dev/ttyACM0', caps=IC705_CAPS,
        modes=HF_MODES + ('DV',), transceive_menu_item=0x0131,
        status='tested on hardware',
        notes='Raspberry Pi 5, USB numeric keypad, PC speakers.',
    ),
    RadioProfile(
        key='ic7300', name='Icom IC-7300', spoken='I C seventy-three hundred',
        civ_addr=0x94, baud=115200, bauds=CIV_BAUDS,
        serial_port='/dev/ttyUSB0', caps=IC7300_CAPS,
        modes=HF_MODES, transceive_menu_item=0x0071,
        notes='Command set from the IC-705 profile minus D-STAR, GPS and repeater.',
    ),
    RadioProfile(
        key='ic7100', name='Icom IC-7100', spoken='I C seventy-one hundred',
        civ_addr=0x88, baud=19200, bauds=CIV_BAUDS[:3],
        serial_port='/dev/ttyUSB0', caps=IC7100_CAPS,
        modes=HF_MODES + ('WFM', 'DV'),
        notes='Conservative first block from Hamlib ic7100.c.',
    ),
)

DEFAULT_PROFILE = 'ic705'


def profile_keys():
    return [p.key for p in PROFILES]


def get_profile(key):
    for p in PROFILES:
        if p.key == key:
            return p
    raise KeyError('Unknown radio profile: ' + str(key))


def capability_names():
    return [f.name for f in fields(Capabilities)]


def validate():
    """Return a list of problems in the table (empty when it is consistent)."""
    problems = []
    seen = set()
    for p in PROFILES:
        if p.key in seen:
            problems.append(p.key + ': duplicate key')
        seen.add(p.key)
        if not 0 < p.civ_addr < 0xE0:
            problems.append(p.key + ': CI-V address out of range')
        if p.baud not in p.bauds:
            problems.append(p.key + ': default baud not in bauds')
        for m in p.modes:
            if m not in MODE_CODES:
                problems.append(p.key + ': unknown mode ' + m)
        if p.caps.transceive and not p.transceive_menu_item:
            problems.append(p.key + ': transceive without menu item')
        if p.caps.memory_clear and not p.caps.memory:
            problems.append(p.key + ': memory_clear without memory')
    for name in capability_names():
        if name not in FEATURE_NAMES:
            problems.append('no spoken name for capability ' + name)
    return problems
