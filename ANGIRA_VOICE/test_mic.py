"""Test microphone input levels."""
import pyaudio
import struct
import numpy as np

p = pyaudio.PyAudio()

print("=" * 50)
print("MICROPHONE TEST")
print("=" * 50)

# Show available input devices
print("\nAvailable input devices:")
for i in range(p.get_device_count()):
    info = p.get_device_info_by_index(i)
    if info['maxInputChannels'] > 0:
        print(f"  [{i}] {info['name']}")

default = p.get_default_input_device_info()
print(f"\nUsing: {default['name']} (index {default['index']})")
print("=" * 50)

s = p.open(
    format=pyaudio.paInt16, 
    channels=1, 
    rate=16000, 
    input=True, 
    frames_per_buffer=1024
)

print("\n🎤 SPEAK NOW for 3 seconds!")
print("-" * 50)

max_level = 0
for i in range(30):
    data = s.read(1024, exception_on_overflow=False)
    samples = struct.unpack(f"{len(data)//2}h", data)
    rms = np.sqrt(np.mean(np.square(np.array(samples, dtype=np.float32)))) / 32768
    max_level = max(max_level, rms)
    bar = "█" * int(rms * 500)
    print(f"Level: {rms:.6f} {bar}")

s.close()
p.terminate()

print("-" * 50)
print(f"MAX LEVEL: {max_level:.6f}")
if max_level < 0.001:
    print("❌ NO AUDIO DETECTED - Microphone is not working!")
    print("\nTry these fixes:")
    print("1. Windows Settings > Privacy > Microphone - Enable access")
    print("2. Right-click speaker icon > Sound settings > Input - Check volume")
    print("3. Check if mic has a physical mute button (often F4 key)")
elif max_level < 0.01:
    print("⚠️  VERY LOW AUDIO - Speak louder or check mic volume")
else:
    print("✅ MICROPHONE IS WORKING!")
