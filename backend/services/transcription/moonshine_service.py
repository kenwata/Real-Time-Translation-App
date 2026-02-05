import logging
import time
import sherpa_onnx
import numpy as np
import os

try:
    from backend.core.config import MODEL_DIR
except ImportError:
    MODEL_DIR = "models"

logger = logging.getLogger("server")

class MoonshineService:
    def __init__(self, model_dir: str = None):
        if model_dir is None:
            model_dir = os.path.join(MODEL_DIR, "asr", "sherpa-onnx-moonshine-base-en-int8")
        logger.info("Initializing Moonshine Service...")
        
        # 1. Load Moonshine Offline Recognizer
        logger.info(f"Loading Moonshine model from {model_dir}")
        try:
             self.recognizer = sherpa_onnx.OfflineRecognizer.from_moonshine(
                preprocessor=f"{model_dir}/preprocess.onnx",
                encoder=f"{model_dir}/encode.int8.onnx",
                uncached_decoder=f"{model_dir}/uncached_decode.int8.onnx",
                cached_decoder=f"{model_dir}/cached_decode.int8.onnx",
                tokens=f"{model_dir}/tokens.txt",
                num_threads=2,
                debug=False
             )
        except Exception as e:
             logger.error(f"Failed to load Moonshine model: {e}")
             raise
        logger.info("Moonshine OfflineRecognizer loaded.")

        # 2. VAD Setup (Reusing Silero VAD)
        vad_config = sherpa_onnx.VadModelConfig()
        vad_config.silero_vad.model = os.path.join(MODEL_DIR, "vad", "silero_vad.onnx")
        vad_config.silero_vad.threshold = 0.5
        vad_config.silero_vad.min_silence_duration = 0.5
        vad_config.silero_vad.min_speech_duration = 0.25
        vad_config.sample_rate = 16000
        self.vad = sherpa_onnx.VoiceActivityDetector(
            config=vad_config,
            buffer_size_in_seconds=60
        )
        
        # 3. Buffer State
        self.sample_rate = 16000
        self.max_buffer_duration = 7.0  # Force trigger after 7 seconds (Fail-safe)
        
    def create_stream(self, enable_interim_results: bool = True):
        return MoonshineStream(self.recognizer, self.vad, self.max_buffer_duration, enable_interim_results)

    def process_audio(self, samples: np.ndarray, stream=None) -> list:
        if stream is None:
            return []
        
        results = stream.accept_waveform(samples)
        return results

class MoonshineStream:
    def __init__(self, recognizer, vad, max_buffer_duration, enable_interim_results=True):
        self.recognizer = recognizer
        self.vad = vad
        self.max_buffer_duration = max_buffer_duration
        self.enable_interim_results = enable_interim_results
        self.buffer = np.array([], dtype=np.float32)
        self.buffer_duration = 0.0
        self.last_interim_duration = 0.0
        self.interim_interval = 0.5 # 0.5s

    def accept_waveform(self, samples: np.ndarray) -> list:
        results = []
        
        # 1. Append to buffer
        self.buffer = np.concatenate((self.buffer, samples))
        self.buffer_duration += len(samples) / 16000.0
        
        # 2. Check VAD
        self.vad.accept_waveform(samples)
        
        # 3. Trigger Logic
        should_decode = False
        
        # Priority 1: VAD Silence (Natural Pause)
        # If VAD detects end of speech (silence), trigger immediately.
        if not self.vad.empty():
             # We assume VAD events generally imply a transition or notable event.
             # If we are currently detecting silence BUT we have buffered speech, process it.
             # Ideally we check specifically for "Speech End" event but simply checking
             # "not is_speech_detected" on the current frame is a decent proxy if queue is empty
             # or just trusting the VAD internal buffer.
             
             # Simpler approach: If VAD says "Silence" and we have valid buffer > 0.5s, decode.
             # (Avoid decoding very short non-speech clicks)
             if not self.vad.is_speech_detected():
                 if self.buffer_duration > 0.5:
                     should_decode = True

        # Priority 2: Fail-safe Timeout (Long Continuous Speech)
        if self.buffer_duration >= self.max_buffer_duration:
             should_decode = True
        
        # Priority 3: Interim Results (Real-time Feedback)
        # Only if NOT committing and we have new data since last interim
        if self.enable_interim_results and not should_decode and self.buffer_duration - self.last_interim_duration >= self.interim_interval:
            if self.buffer_duration > 0.2: # Minimum buffer to avoid garbage
                 stream = self.recognizer.create_stream()
                 stream.accept_waveform(16000, self.buffer)
                 self.recognizer.decode_stream(stream)
                 text = stream.result.text
                 if text.strip():
                     results.append({"text": text, "is_final": False})
                     self.last_interim_duration = self.buffer_duration

        if should_decode and len(self.buffer) > 0:
            # Decode the buffer (Final)
            stream = self.recognizer.create_stream()
            stream.accept_waveform(16000, self.buffer)
            self.recognizer.decode_stream(stream)
            text = stream.result.text
            
            if text.strip():
                results.append({"text": text, "is_final": True})
            
            # Clear buffer
            self.buffer = np.array([], dtype=np.float32)
            self.buffer_duration = 0.0
            self.last_interim_duration = 0.0 # Reset interim tracker
            
            # Reset VAD to avoid carry-over state issues
            self.vad.reset()

        return results
