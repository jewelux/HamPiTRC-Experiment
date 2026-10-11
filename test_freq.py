import subprocess

freq_raw = subprocess.check_output(['rigctl', '-m', '3085', '-r', '/dev/ttyACM0', '-s', '115200', 'f']).decode().strip()
freq_mhz = int(freq_raw) * 100 / 1_000_000
text = f"Frequency {freq_mhz:.3f} megahertz"
print(text)

# Generate WAV first
subprocess.run(['python3', '-m', 'piper', '--model', '/home/pi/piper-voices/de_DE-thorsten-high.onnx', '--output_file', '/tmp/ansage.wav'], input=text.encode())

# Play the WAV
subprocess.run(['aplay', '-D', 'plughw:0,0', '/tmp/ansage.wav'])
