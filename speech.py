# HamPiTRC speech output: Piper text-to-speech, played through ALSA (aplay).
#
# Sentences are synthesised in the caller and queued; a player thread plays
# them one after the other. stop() (a new key press) silences the current
# sentence at once and drops the queue, as on HamTRC. Volume 1..9 scales the
# samples; speed slow/normal/fast sets Piper's length scale.

import array
import io
import math
import queue
import subprocess
import threading
import time
import wave

from config import AUDIO_DEVICE as CONFIG_AUDIO_DEVICE, AUDIO_NAME, HDMI_NAME, PIPER_MODEL

AUDIO_DEVICE = CONFIG_AUDIO_DEVICE

# Piper length scale per speed: above 1 is slower.
SPEED_SCALE = {'slow': 1.3, 'normal': 1.0, 'fast': 0.75}

_voice = None
_volume = 5
_speed = 'normal'
_queue = queue.Queue()
_current = None            # running aplay process
_lock = threading.Lock()
_generation = 0            # bumped by stop(): queued items of older generations are dropped
_player = None
_last_audio_busy_print = 0


def _get_audio_device():
    try:
        with open('/proc/asound/cards', 'r', encoding='utf-8') as f:
            for line in f:
                if AUDIO_NAME in line and '[' in line:
                    card_num = line.split('[', 1)[0].strip()
                    if card_num.isdigit():
                        return f"plughw:{card_num},0"
    except OSError:
        pass
    try:
        result = subprocess.run(["aplay", "-l"], capture_output=True, text=True)
    except OSError:
        return AUDIO_DEVICE
    for name in (AUDIO_NAME, HDMI_NAME):
        for line in result.stdout.splitlines():
            if name in line and line.startswith("card"):
                card_num = line.split()[1].rstrip(":")
                return f"plughw:{card_num},0"
    return AUDIO_DEVICE


def load_voice():
    """Load the Piper model once; say() calls this on first use."""
    global _voice
    if _voice is None:
        from piper import PiperVoice
        print("Loading voice model...")
        _voice = PiperVoice.load(PIPER_MODEL)
        print("Voice model ready.")
    return _voice


def set_volume(level):
    global _volume
    _volume = max(1, min(9, int(level)))


def set_speed(speed):
    global _speed
    if speed in SPEED_SCALE:
        _speed = speed


def _gain():
    # Level 9 is full scale; each step down is about 3 dB.
    return 10 ** (-(9 - _volume) * 3 / 20)


def _scaled(frames, sample_width):
    if sample_width != 2:
        return frames
    gain = _gain()
    if gain >= 0.999:
        return frames
    samples = array.array('h')
    samples.frombytes(frames)
    for i, v in enumerate(samples):
        samples[i] = int(v * gain)
    return samples.tobytes()


def _synthesize(text):
    voice = load_voice()
    kwargs = {}
    scale = SPEED_SCALE.get(_speed, 1.0)
    if scale != 1.0:
        try:
            from piper import SynthesisConfig
            kwargs['syn_config'] = SynthesisConfig(length_scale=scale)
        except ImportError:
            pass
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as wav_file:
        for chunk in voice.synthesize(text, **kwargs):
            if wav_file.getnframes() == 0:
                wav_file.setnchannels(chunk.sample_channels)
                wav_file.setsampwidth(chunk.sample_width)
                wav_file.setframerate(chunk.sample_rate)
            wav_file.writeframes(_scaled(chunk.audio_int16_bytes, chunk.sample_width))
    return buf.getvalue()


def _beep_wav(freq=880, ms=120, rate=22050):
    n = int(rate * ms / 1000)
    amp = 12000 * _gain()
    samples = array.array('h', (int(amp * math.sin(2 * math.pi * freq * i / rate)) for i in range(n)))
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(samples.tobytes())
    return buf.getvalue()


def _play(audio):
    global _current, _last_audio_busy_print
    device = _get_audio_device()
    for attempt in range(5):
        with _lock:
            proc = subprocess.Popen(['aplay', '-D', device, '-q'], stdin=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
            _current = proc
        try:
            _out, err = proc.communicate(audio)
        except (BrokenPipeError, OSError):
            err = b''
        with _lock:
            _current = None
        if proc.returncode == 0 or proc.returncode < 0:   # done, or stopped
            return
        if err and b'Device or resource busy' in err:
            if attempt == 4:
                now = time.time()
                if now - _last_audio_busy_print > 10:
                    print('Audio device busy')
                    _last_audio_busy_print = now
                return
            time.sleep(0.3)
            continue
        if err:
            print(err.decode(errors='replace').strip())
        return


def _player_loop():
    while True:
        gen, audio = _queue.get()
        if gen == _generation:
            _play(audio)


def _enqueue(audio):
    global _player
    if _player is None:
        _player = threading.Thread(target=_player_loop, daemon=True)
        _player.start()
    _queue.put((_generation, audio))


def say(text):
    print(f"Say: {text}")
    gen = _generation
    audio = _synthesize(text)
    if gen == _generation:     # not interrupted while synthesising
        _enqueue(audio)


def beep():
    print("Beep")
    _enqueue(_beep_wav())


def stop():
    """Silence now: drop queued speech and end the running sentence."""
    global _generation
    _generation += 1
    with _lock:
        proc = _current
    if proc is not None and proc.poll() is None:
        try:
            proc.terminate()
        except OSError:
            pass


def wait_idle(timeout=10.0):
    """Block until the queue has been played (startup and shutdown)."""
    end = time.time() + timeout
    while time.time() < end:
        with _lock:
            busy = _current is not None
        if _queue.empty() and not busy:
            return
        time.sleep(0.05)


# Spoken abbreviations: written forms that Piper would otherwise read as a word.
SPEAK_MAP = {
    'HamPiTRC': 'Ham Pi T R C',
    'PiHAMTRC': 'Pi Ham T R C',
    'HAMTRC':   'Ham T R C',
    'VFO':      'V F O',
    'USB':      'U S B',
    'LSB':      'L S B',
    'CW-R':     'C W reverse',
    'RTTY':     'R T T Y',
    'RTTY-R':   'R T T Y reverse',
    'NR':       'N R',
    'NB':       'N B',
    'RIT':      'R I T',
    'PTT':      'P T T',
    'RF':       'R F',
    'AF':       'A F',
    'DV':       'D V',
    'WFM':      'wide F M',
    'DTCS':     'D T C S',
    'TSQL':     'T S Q L',
    'DSQL':     'D S Q L',
    'CSQL':     'C S Q L',
    'XFC':      'X F C',
}


def nice_text(text):
    # Longest first, so RTTY-R is not read as RTTY plus "-R".
    for abbr in sorted(SPEAK_MAP, key=len, reverse=True):
        text = text.replace(abbr, SPEAK_MAP[abbr])
    return text


def say_nice(text):
    say(nice_text(text))


def spell(text):
    return ' '.join(list(text))


class Speech:
    """The speech interface the ui uses (a fake replaces it in tests)."""

    def say(self, text):
        say_nice(text)

    def beep(self):
        beep()

    def stop(self):
        stop()

    def set_volume(self, level):
        set_volume(level)

    def set_speed(self, speed):
        set_speed(speed)
