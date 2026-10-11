import subprocess
import io
import wave
import time
import threading
from piper import PiperVoice
from config import AUDIO_DEVICE as CONFIG_AUDIO_DEVICE, AUDIO_NAME, HDMI_NAME, PIPER_MODEL
AUDIO_DEVICE = CONFIG_AUDIO_DEVICE
_audio_lock = threading.Lock()

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

    import subprocess as sp
    result = sp.run(["aplay", "-l"], capture_output=True, text=True)
    for name in (AUDIO_NAME, HDMI_NAME):
        for line in result.stdout.splitlines():
            if name in line and line.startswith("card"):
                card_num = line.split()[1].rstrip(":")
                return f"plughw:{card_num},0"
    return AUDIO_DEVICE

print("Loading voice model...")
_voice = PiperVoice.load(PIPER_MODEL)
print("Voice model ready.")
_last_audio_busy_print = 0

def say(text):
    global _last_audio_busy_print
    print(f"Say: {text}")
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as wav_file:
        for chunk in _voice.synthesize(text):
            if wav_file.getnframes() == 0:
                wav_file.setnchannels(chunk.sample_channels)
                wav_file.setsampwidth(chunk.sample_width)
                wav_file.setframerate(chunk.sample_rate)
            wav_file.writeframes(chunk.audio_int16_bytes)
    buf.seek(0)
    audio = buf.read()
    with _audio_lock:
        for attempt in range(5):
            result = subprocess.run(
                ['aplay', '-D', _get_audio_device(), '-q'],
                input=audio,
                capture_output=True,
            )
            if result.returncode == 0:
                return
            if b'Device or resource busy' in result.stderr:
                if attempt == 4:
                    now = time.time()
                    if now - _last_audio_busy_print > 10:
                        print('Audio device busy')
                        _last_audio_busy_print = now
                    return
                time.sleep(0.3)
                continue
            else:
                if result.stderr:
                    print(result.stderr.decode(errors='replace').strip())
                return

def spell(text):
    return ' '.join(list(text))

# Spoken abbreviations
SPEAK_MAP = {
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
}

def say_nice(text):
    for abbr, spoken in SPEAK_MAP.items():
        text = text.replace(abbr, spoken)
    say(text)
