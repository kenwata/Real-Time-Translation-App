import asyncio
import websockets
import json
import logging
import numpy as np
import struct

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_client")

async def test_connection():
    uri = "ws://localhost:8000/ws/transcribe?model=hybrid&lang=en"
    try:
        logger.info(f"Connecting to {uri}...")
        async with websockets.connect(uri) as websocket:
            logger.info("Connected!")
            
            # Generate 5 seconds of "speech" (sine wave)
            # 16kHz, mono, float32
            sample_rate = 16000
            duration = 5
            t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
            # A simple 440Hz tone
            audio = 0.5 * np.sin(2 * np.pi * 440 * t)
            audio = audio.astype(np.float32)
            
            # Send in chunks of 0.1s
            chunk_size = int(16000 * 0.1)
            
            logger.info("Sending Speech...")
            for i in range(0, len(audio), chunk_size):
                chunk = audio[i:i+chunk_size]
                await websocket.send(chunk.tobytes())
                await asyncio.sleep(0.1)
                
                # Check for messages
                try:
                    msg = await asyncio.wait_for(websocket.recv(), timeout=0.01)
                    logger.info(f"Received: {msg}")
                except asyncio.TimeoutError:
                    pass

            logger.info("Sending Silence (trigger VAD)...")
            # Send 2 seconds of silence
            silence = np.zeros(int(16000 * 2.0), dtype=np.float32)
            for i in range(0, len(silence), chunk_size):
                chunk = silence[i:i+chunk_size]
                await websocket.send(chunk.tobytes())
                await asyncio.sleep(0.1)
                
                try:
                    msg = await asyncio.wait_for(websocket.recv(), timeout=0.01)
                    logger.info(f"Received: {msg}")
                except asyncio.TimeoutError:
                    pass

            # Wait a bit more for final result
            logger.info("Waiting for final result...")
            try:
                msg = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                logger.info(f"FINAL Received: {msg}")
            except asyncio.TimeoutError:
                logger.info("Timeout waiting for final result.")

    except Exception as e:
        logger.error(f"Connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_connection())
