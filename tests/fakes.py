# Test helpers: stand-ins for modules the host tests must not need.
#
# - pyserial: used only when it is not installed (civ.py needs the names).
# - evdev and piper: never installed for tests; pihamtrc.py and speech.py
#   import them at the top.
# Import this module before civ, radio, speech or pihamtrc.

import sys
import types


def _install(name, module):
    if name not in sys.modules:
        sys.modules[name] = module


try:
    import serial  # noqa: F401
except ImportError:
    serial = types.ModuleType('serial')

    class SerialException(Exception):
        pass

    class Serial:
        def __init__(self, *args, **kwargs):
            raise SerialException('no serial port in host tests')

    serial.SerialException = SerialException
    serial.Serial = Serial
    _install('serial', serial)


evdev = types.ModuleType('evdev')
evdev.ecodes = types.SimpleNamespace(EV_KEY=1, KEY_KP0=82, KEY_KP9=73)
evdev.list_devices = lambda: []
evdev.InputDevice = object
_install('evdev', evdev)

piper = types.ModuleType('piper')


class PiperVoice:
    @staticmethod
    def load(path):
        raise RuntimeError('no Piper voice in host tests')


piper.PiperVoice = PiperVoice
_install('piper', piper)


class FakeSerial:
    """Records written frames and replays queued radio replies."""

    def __init__(self, responses=b''):
        self.writes = []
        self.responses = bytearray(responses)

    def write(self, data):
        self.writes.append(bytes(data))

    def read(self, size=1):
        if not self.responses:
            return b''
        data = self.responses[:size]
        del self.responses[:size]
        return bytes(data)

    def reset_input_buffer(self):
        pass

    def close(self):
        pass
