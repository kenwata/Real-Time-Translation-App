import asyncio
import json
import logging
import os
from logging.handlers import TimedRotatingFileHandler
from typing import List

import numpy as np
import sherpa_onnx
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import uvicorn

# Configure logging
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)

logger = logging.getLogger("server")
logger.setLevel(logging.INFO)

# File handler with rotation (1 week retention)
file_handler = TimedRotatingFileHandler(
    filename=os.path.join(log_dir, "server.log"),
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

SAMPLE_RATE = 16000
VAD_WINDOW_SIZE = 512  # Samples

class TranscriptionService:
    def __init__(self, language: str = "", model_type: str = "sensevoice", mode: str = "offline"):
        self.language = language
        self.model_type = model_type
        self.mode = mode
        
        # Silero VAD (only needed for offline mode or VAD-based segmentation)
        # Even for online, we might want VAD to reset streams, but standard streaming is continuous.
        vad_config = sherpa_onnx.VadModelConfig()
        vad_config.silero_vad.model = "./silero_vad.onnx"
        vad_config.silero_vad.threshold = 0.5  # Slightly less sensitive to noise
        vad_config.silero_vad.min_silence_duration = 1.0 # Increase to 1.0s to avoid cutting sentences too early
        vad_config.silero_vad.min_speech_duration = 0.25
        vad_config.sample_rate = SAMPLE_RATE
        
        self.vad = sherpa_onnx.VoiceActivityDetector(
            config=vad_config,
            buffer_size_in_seconds=60
        )

        # Initialize Recognizer based on type
        logger.info(f"Initializing {model_type} ({mode}) for language: '{language}'")
        
        self.output_buffer = [] # Buffer for partial results if needed

        if mode == "streaming":
            if model_type == "zipformer" and language == "en":
                logger.info("Loading Streaming English Zipformer model")
                tokens = "./sherpa-onnx-streaming-zipformer-en-2023-06-26/tokens.txt"
                # Check absolute path if needed, but relative should work since we moved it
                self.recognizer = sherpa_onnx.OnlineRecognizer.from_transducer(
                    encoder="./sherpa-onnx-streaming-zipformer-en-2023-06-26/encoder-epoch-99-avg-1-chunk-16-left-128.onnx",
                    decoder="./sherpa-onnx-streaming-zipformer-en-2023-06-26/decoder-epoch-99-avg-1-chunk-16-left-128.onnx",
                    joiner="./sherpa-onnx-streaming-zipformer-en-2023-06-26/joiner-epoch-99-avg-1-chunk-16-left-128.onnx",
                    tokens=tokens,
                    num_threads=1,
                    sample_rate=16000,
                    feature_dim=80,
                    decoding_method="greedy_search", # Streaming usually uses greedy for speed
                )
            else:
                logger.error(f"Streaming not supported for {model_type}/{language}")
                raise ValueError("Streaming not supported for this configuration")
        else:
            # Offline Initialization
            if model_type == "zipformer":
                if language == 'en':
                    # Use English-specific model (Gigaspeech)
                    # Use absolute path or ensure backend is CWD
                    logger.info("Loading English Zipformer (Gigaspeech) model")
                    self.recognizer = sherpa_onnx.OfflineRecognizer.from_transducer(
                        encoder="./sherpa-onnx-zipformer-gigaspeech-2023-12-12/encoder-epoch-30-avg-1.onnx",
                        decoder="./sherpa-onnx-zipformer-gigaspeech-2023-12-12/decoder-epoch-30-avg-1.onnx",
                        joiner="./sherpa-onnx-zipformer-gigaspeech-2023-12-12/joiner-epoch-30-avg-1.onnx",
                        tokens="./sherpa-onnx-zipformer-gigaspeech-2023-12-12/tokens.txt",
                        num_threads=1,
                        sample_rate=16000,
                        feature_dim=80,
                        decoding_method="modified_beam_search",
                    )
                else:
                    # multiple languages (mainly Chinese/English mixed)
                    logger.info("Loading Multi-lingual Zipformer model")
                    self.recognizer = sherpa_onnx.OfflineRecognizer.from_transducer(
                        encoder="./sherpa-onnx-zipformer-multi-zh-hans-2023-9-2/encoder-epoch-20-avg-1.int8.onnx",
                        decoder="./sherpa-onnx-zipformer-multi-zh-hans-2023-9-2/decoder-epoch-20-avg-1.int8.onnx",
                        joiner="./sherpa-onnx-zipformer-multi-zh-hans-2023-9-2/joiner-epoch-20-avg-1.int8.onnx",
                        tokens="./sherpa-onnx-zipformer-multi-zh-hans-2023-9-2/tokens.txt",
                        decoding_method="modified_beam_search",
                    )
            else:
                # Default to SenseVoice
                self.recognizer = sherpa_onnx.OfflineRecognizer.from_sense_voice(
                    model="./sherpa-onnx-sense-voice-zh-en-ja-ko-yue-int8-2024-07-17/model.int8.onnx",
                    tokens="./sherpa-onnx-sense-voice-zh-en-ja-ko-yue-int8-2024-07-17/tokens.txt",
                    language=language,
                    use_itn=True,
                )

        # Initialize Punctuation
        punct_config = sherpa_onnx.OfflinePunctuationConfig()
        punct_config.model.ct_transformer = "./sherpa-onnx-punct-ct-transformer-zh-en-vocab272727-2024-04-12/model.onnx"
        punct_config.model.num_threads = 1
        punct_config.model.debug = True
        # For this specific model (vocab272727), it contains metadata, so we might not need vocab file.
        # But if needed, we can try leaving it empty or pointing to tokens.json if supported.
        # Official docs say pass model path.

        try:
            self.punctuation = sherpa_onnx.OfflinePunctuation(punct_config)
            logger.info("Initialized Punctuation model")
        except Exception as e:
            logger.error(f"Failed to initialize punctuation: {e}")
            self.punctuation = None

    def normalize_punctuation(self, text: str) -> str:
        """
        Convert Chinese punctuation to English if language is English.
        """
        if self.language == 'en':
            return text.replace("。", ".").replace("，", ",").replace("？", "?").replace("！", "!").replace("、", ",")
        return text

    def create_stream(self):
        if self.mode == "streaming":
            return self.recognizer.create_stream()
        else:
            return None 

    def process_audio(self, samples: np.ndarray, stream=None) -> List[dict]:
        """
        Feed audio to recognizer.
        For Offline: uses internal VAD and returns list of texts (final).
        For Streaming: feeds persistent 'stream' and returns partial/final results.
        params:
            stream: OnlineStream object (required for streaming mode)
        returns:
            List of dicts: {"text": str, "is_final": bool}
        """
        results = []
        
        if self.mode == "streaming":
            if stream is None:
                logger.error("No stream provided for streaming mode")
                return []
            
            # Feed audio to Recognizer
            stream.accept_waveform(SAMPLE_RATE, samples)
            while self.recognizer.is_ready(stream):
                self.recognizer.decode_stream(stream)
            
            # Feed audio to VAD for endpoint detection
            self.vad.accept_waveform(samples)
            
            # Check if VAD detected a completed segment (Endpoint)
            is_endpoint = not self.vad.empty()
            
            if is_endpoint:
                # Clear VAD segments (we just use it for trigger)
                while not self.vad.empty():
                    self.vad.pop()
                
                text = self.recognizer.get_result(stream)
                if text:
                    # Finalize
                    if self.punctuation:
                        text = self.punctuation.add_punctuation(text)
                        text = self.normalize_punctuation(text)
                    
                    logger.info(f"Stream Endpoint (VAD): {text}")
                    results.append({"text": text, "is_final": True})
                    self.recognizer.reset(stream)
            else:
                # Partial result
                text = self.recognizer.get_result(stream)
                if text:
                    # Partial punctuation (optional, unstable)
                    if self.punctuation:
                        try:
                            p_text = self.punctuation.add_punctuation(text)
                            text = self.normalize_punctuation(p_text)
                        except:
                            pass
                    results.append({"text": text, "is_final": False})
                
            return results

        else:
            # OFFLINE MODE (Internal VAD)
            try:
                self.vad.accept_waveform(samples)
                
                # Check for completed speech segments
                while not self.vad.empty():
                    segment = self.vad.front
                    segment_samples = segment.samples
                    self.vad.pop()
                    
                    duration = len(segment_samples) / SAMPLE_RATE
                    logger.info(f"Speech detected! Duration: {duration:.2f}s")
                    
                    if duration < 0.1:
                        continue

                    # transcribe this segment
                    s = self.recognizer.create_stream()
                    s.accept_waveform(SAMPLE_RATE, segment_samples)
                    self.recognizer.decode_stream(s)
                    text = s.result.text
                    if text:
                        # Apply Punctuation
                        if self.punctuation:
                            text = self.punctuation.add_punctuation(text)
                            text = self.normalize_punctuation(text)
                            
                        logger.info(f"Transcribed: {text}")
                        results.append({"text": text, "is_final": True})
                
                return results
            except Exception as e:
                logger.error(f"Error in process_audio: {e}", exc_info=True)
                return []

# Service Manager to cache models by language
class ServiceManager:
    def __init__(self):
        self.services = {}

    def get_service(self, language: str, model_type: str = "sensevoice", mode: str = "offline") -> TranscriptionService:
        # Map "auto" to empty string for Sherpa-ONNX
        lang_code = "" if language == "auto" else language
        
        key = f"{model_type}_{lang_code}_{mode}"
        
        if key not in self.services:
            logger.info(f"Creating new service for key: {key}")
            self.services[key] = TranscriptionService(language=lang_code, model_type=model_type, mode=mode)
        return self.services[key]

manager = ServiceManager()

@app.on_event("startup")
async def startup_event():
    # Pre-load default language (English)
    pass
    # logger.info("Pre-loading default model (en, sensevoice)...")
    # try:
    #     manager.get_service("en", "sensevoice")
    #     logger.info("Default model loaded.")
    # except Exception as e:
    #     logger.error(f"Failed to load default model: {e}")
        # Don't raise here, allow retry connection

@app.websocket("/ws/transcribe")
async def websocket_endpoint(websocket: WebSocket, language: str = "en", model_type: str = "sensevoice", mode: str = "offline"):
    await websocket.accept()
    logger.info(f"Client connected with language: {language}, model: {model_type}, mode: {mode}")
    
    try:
        service = manager.get_service(language, model_type, mode)
    except Exception as e:
        logger.error(f"Failed to get service for {language}/{model_type}/{mode}: {e}")
        await websocket.close(code=1011)
        return

    # specific stream for this connection (only used for streaming mode)
    stream = service.create_stream()

    try:
        while True:
            data = await websocket.receive_bytes()
            # Convert bytes to float32 numpy array
            samples = np.frombuffer(data, dtype=np.float32)
            
            # logger.debug(f"Received {len(samples)} samples") 
            
            if service:
                # Pass the persistent stream if streaming mode
                results = service.process_audio(samples, stream=stream)
                for res in results:
                    text = res["text"]
                    is_final = res["is_final"]
                    logger.info(f"Sending text: {text} (Final: {is_final})")
                    await websocket.send_json({"text": text, "is_final": is_final})

                    
    except WebSocketDisconnect:
        logger.info("Client disconnected")
    except Exception as e:
        logger.error(f"Error in websocket loop: {e}", exc_info=True)
        await websocket.close()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
