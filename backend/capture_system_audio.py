import sounddevice as sd
import wave
import numpy as np
import time
DEVICE =25
SAMPLE_RATE = 48000
CHANNELS = 2
DURATION =10
OUTPUT_FILE = "output.wav"
print("Recording audio...")
print(f"Using device: {DEVICE}")
audio= sd.rec(int(DURATION * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=CHANNELS, device=DEVICE,dtype='int16')
sd.wait()   
print("Recording finished. Saving to file...")
with wave.open(OUTPUT_FILE, 'wb') as wf:
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(2)  # 2 bytes for 'int16'
    wf.setframerate(SAMPLE_RATE)
    wf.writeframes(audio.tobytes())
print(f"Audio saved to {OUTPUT_FILE}")