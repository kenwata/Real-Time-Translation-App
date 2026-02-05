import numpy as np

# Read raw int16 PCM (16kHz, 1 channel)
with open("debug_parakeet_raw.pcm", "rb") as f:
    raw_data = f.read()

data = np.frombuffer(raw_data, dtype=np.int16)
float_data = data.astype(np.float32) / 32768.0

print(f"Total samples: {len(data)}")
print(f"Duration: {len(data)/16000:.2f} seconds")
print(f"Max Amplitude (Int16): {np.max(np.abs(data))}")
print(f"Max Amplitude (Float): {np.max(np.abs(float_data)):.4f}")
print(f"Mean Amplitude: {np.mean(np.abs(float_data)):.4f}")
print(f"RMS: {np.sqrt(np.mean(float_data**2)):.4f}")
