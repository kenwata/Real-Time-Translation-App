import numpy as np

with open("debug_parakeet_raw.pcm", "rb") as f:
    raw_data = f.read()

data = np.frombuffer(raw_data, dtype=np.int16)
float_data = data.astype(np.float32) / 32768.0

print(f"Max Amp: {np.max(np.abs(float_data)):.4f}")
print(f"Mean (Signed): {np.mean(float_data):.4f}")
print(f"Std Dev: {np.std(float_data):.4f}")
