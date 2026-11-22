# HamPiTRC keypad: USB numeric keypad keycodes -> HamTRC logical keys.
#
# HamTRC has a 4x4 keypad (1 2 3 A / 4 5 6 B / 7 8 9 C / * 0 # D). On a PC
# numeric keypad the digits sit upside down (7 8 9 on top); the logical keys
# and every bank function are the same.
KEY_MAP = {
    'KEY_KP1':       '1',
    'KEY_KP2':       '2',
    'KEY_KP3':       '3',
    'KEY_KP4':       '4',
    'KEY_KP5':       '5',
    'KEY_KP6':       '6',
    'KEY_KP7':       '7',
    'KEY_KP8':       '8',
    'KEY_KP9':       '9',
    'KEY_KP0':       '0',
    'KEY_SPACE':     '*',
    'KEY_KPDOT':     '#',
    'KEY_KPENTER':   'D',
    'KEY_BACKSPACE': 'A',
    'KEY_KPMINUS':   'B',
    'KEY_KPPLUS':    'C',
}
