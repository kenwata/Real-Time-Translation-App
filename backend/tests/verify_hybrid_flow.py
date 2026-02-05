import sys
import os
import logging
import numpy as np
import asyncio

# Adjust path to find backend modules (Project Root)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test")

from backend.services.transcription.hybrid_service import HybridService

async def test_hybrid_flow():
    print("\n--- Initializing HybridService ---")
    try:
        service = HybridService()
    except Exception as e:
        print(f"FATAL: Failed to initialize HybridService: {e}")
        import traceback
        traceback.print_exc()
        return

    print("\n--- Creating Stream ---")
    try:
        stream = service.create_stream()
    except Exception as e:
        print(f"FATAL: Failed to create stream: {e}")
        return

    print("\n--- Simulating 10 Seconds of Silence (Check for crash) ---")
    # Generate 1 sec of silence (float32)
    silence = np.zeros(16000, dtype=np.float32)
    
    for i in range(5):
        print(f"Processing chunk {i+1}...")
        try:
             # Mimic server.py: run in thread (although here we just call directly for simplicity, but simulating context)
             results = service.process_audio(silence, stream=stream)
             for res in results:
                 print(f"Result: {res}")
        except Exception as e:
            print(f"FATAL: Error processing audio: {e}")
            import traceback
            traceback.print_exc()
            return
            
    print("\n--- Simulating Fake Speech (Random Noise) ---")
    # Random noise (might trigger VAD)
    noise = np.random.uniform(-0.1, 0.1, 16000).astype(np.float32)
    for i in range(5):
        print(f"Processing noise chunk {i+1}...")
        try:
             results = service.process_audio(noise, stream=stream)
             for res in results:
                 print(f"Result: {res}")
        except Exception as e:
             print(f"FATAL: Error processing noise: {e}")
             return

    print("PASS: Flow completed without crash.")

if __name__ == "__main__":
    asyncio.run(test_hybrid_flow())
