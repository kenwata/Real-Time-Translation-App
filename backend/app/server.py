import asyncio
import json
import logging
import os
from logging.handlers import TimedRotatingFileHandler
from typing import List

import numpy as np
import sherpa_onnx
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from pydantic import BaseModel
import uvicorn
import wave

# Updated Imports
try:
    from backend.core.config import LOG_DIR, LOG_FILE, RECORDINGS_DIR
    from backend.services.transcription.hybrid_service import HybridService
except ImportError:
    # Allow running server.py directly if PYTHONPATH is set or from root
    import sys
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
    from backend.core.config import LOG_DIR, LOG_FILE, RECORDINGS_DIR
    from backend.services.transcription.hybrid_service import HybridService


logger = logging.getLogger("server")
logger.setLevel(logging.INFO)

# File handler with rotation (1 week retention)
file_handler = TimedRotatingFileHandler(
    filename=LOG_FILE,
    when="midnight",
    interval=1,
    backupCount=7,
    encoding="utf-8"
)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

# Console handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

logger.addHandler(file_handler)
logger.addHandler(console_handler)

app = FastAPI()

# Buffer to store audio data for each session: {session_id: bytearray}
session_buffers = {}

class SaveRequest(BaseModel):
    session_id: str

@app.post("/api/save_recording")
async def save_recording(request: SaveRequest):
    session_id = request.session_id
    if session_id not in session_buffers or len(session_buffers[session_id]) == 0:
        return {"message": "No audio to save", "filename": None}

    audio_data = session_buffers.pop(session_id)
    filename = f"{session_id}.wav"
    filepath = os.path.join(RECORDINGS_DIR, filename)

    try:
        with wave.open(filepath, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)  # 16-bit PCM (2 bytes)
            wf.setframerate(SAMPLE_RATE)
            wf.writeframes(audio_data)
        
        logger.info(f"Saved recording: {filepath}")
        return {"message": "Saved successfully", "filename": filename, "path": filepath}
    except Exception as e:
        logger.error(f"Failed to save WAV: {e}")
        # Put data back in case of error? Or just raise? 
        # For now, simplistic error handling.
        raise HTTPException(status_code=500, detail=str(e))


SAMPLE_RATE = 16000

# Service Manager to cache models by language
class ServiceManager:
    def __init__(self):
        self.services = {}

    def get_service(self, language: str):
        # We only support hybrid mode basically. logic simplified.
        key = "hybrid_en_streaming" # Single instance for now for simplicity
        
        if key not in self.services:
            logger.info(f"Creating new service for key: {key}")
            self.services[key] = HybridService() # Language hardcoded to EN in HybridService currently
        return self.services[key]

manager = ServiceManager()

@app.on_event("startup")
async def startup_event():
    logger.info(f"Server starting... default model hybrid")


@app.websocket("/ws/transcribe")
async def websocket_endpoint(websocket: WebSocket, language: str = "en", session_id: str = None):
    await websocket.accept()
    
    logger.info(f"WebSocket connected. Lang: {language}, Session: {session_id}")
    
    try:
        service = manager.get_service(language)
        
        # Create stream for this connection
        stream = service.create_stream()
        
        if session_id:
             session_buffers[session_id] = bytearray()
        
        while True:
            data = await websocket.receive_bytes()
            # logger.info(f"Received audio chunk: {len(data)} bytes") # Debug log
            
            # Convert bytes to numpy float32
            # WebAudio sends float32 usually, but here likely 16-bit PCM or Float32 depending on client.
            # Client sends Float32Array.buffer
            samples = np.frombuffer(data, dtype=np.float32)


            if session_id:
                if session_id not in session_buffers:
                    session_buffers[session_id] = bytearray()
                
                # Convert float32 (-1.0 to 1.0) to int16 PCM
                pcm_data = (samples * 32767).clip(-32768, 32767).astype(np.int16).tobytes()
                session_buffers[session_id].extend(pcm_data)
            
            # logger.debug(f"Received {len(samples)} samples") 
            
            if service:
                try:
                    # Pass the persistent stream if streaming mode
        
                    # Run blocking processing in a separate thread to keep the event loop responsive
                    # This is critical for heavy ML/transcription tasks (like MLX Whisper download or inference)
                    results = await asyncio.to_thread(service.process_audio, samples, stream=stream)
                    for res in results:
                        text = res["text"]
                        is_final = res["is_final"]
                        logger.info(f"Sending text: {text} (Final: {is_final})")
                        await websocket.send_json({"text": text, "is_final": is_final})
                except Exception as e:
                    logger.error(f"Error processing audio chunk: {e}", exc_info=True)
                    # We continue the loop, hoping the service recovered
                    continue

                    
                except WebSocketDisconnect:
                    logger.info("Client disconnected during send")
                    break
                except Exception as e:
                    logger.error(f"Error processing audio chunk: {e}", exc_info=True)
                    continue

                    
    except WebSocketDisconnect:
        logger.info("Client disconnected")
    except RuntimeError as e:
        if "WebSocket is not connected" in str(e):
             logger.info("WebSocket disconnected cleanly")
        else:
             logger.error(f"RuntimeError in websocket loop: {e}", exc_info=True)
    except Exception as e:
        logger.error(f"Error in websocket loop: {e}", exc_info=True)
        try:
            await websocket.close()
        except:
            pass

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
