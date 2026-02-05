import asyncio
import websockets
import numpy as np
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("client")

async def test_transcription():
    uri = "ws://localhost:8000/ws/transcribe"
    logger.info(f"Connecting to {uri}")
    try:
        async with websockets.connect(uri) as websocket:
            logger.info("Connected!")
            
            # Generate 5 seconds of silence (zeros)
            # Sample rate 16000, float32
            duration = 5
            sample_rate = 16000
            
            # Send synthetic audio (sine wave)
            logger.info("Sending synthetic audio...")
            duration = 3.0
            t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
            audio = 0.5 * np.sin(2 * np.pi * 440 * t) # 440Hz sine wave
            audio = audio.astype(np.float32)
            
            # Send in chunks to simulate streaming
            chunk_size = 4096
            for i in range(0, len(audio), chunk_size):
                chunk = audio[i:i+chunk_size]
                await websocket.send(chunk.tobytes())
                await asyncio.sleep(chunk_size / sample_rate)
            
            # Send silence after to allow VAD to detect end of speech
            logger.info("Sending silence...")
            silence = np.zeros(sample_rate * 2, dtype=np.float32)
            await websocket.send(silence.tobytes())
            
            # Wait for response
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                logger.info(f"Received: {response}")
            except asyncio.TimeoutError:
                logger.info("No response received (expected for silence)")
            
            logger.info("Closing connection")
            
    except Exception as e:
        logger.error(f"Connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_transcription())
