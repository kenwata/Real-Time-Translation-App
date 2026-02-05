import logging
import time
import sherpa_onnx
import numpy as np
import os
import mlx_whisper

try:
    from backend.core.config import MODEL_DIR
except ImportError:
    MODEL_DIR = "models"

logger = logging.getLogger("server")

class MlxWhisperService:
    def __init__(self):
        logger.info("Initializing MLX Whisper Service...")
        
        # 1. Model Configuration
        # We don't explicitly "load" the model object in __init__ for mlx_whisper 
        # as it typically handles caching internally or we pass the path to transcribe.
        # However, to ensure it's ready or to trigger download immediately as requested,
        # we can do a dummy transcription or just rely on the first call.
        # The prompt requested: "Automatic download on first run".
        self.model_path = "mlx-community/whisper-large-v3-turbo-q4"
        self.initial_prompt = "Technical terms: LLM, RAG, Transformer, PyTorch, Kubernetes, quantization, latency, Sherpa-ONNX, Zipformer, MLX."
        
        logger.info(f"Target Model: {self.model_path}")
        logger.info("MLX Whisper Service will download the model on first use if not present.")

        
        # 2. Buffer State (VAD is now RMS-based, no external model loaded)
        self.sample_rate = 16000
        self.max_buffer_duration = 10.0 
        
    def create_stream(self):
        # Create explicit stream with clean state
        return MlxWhisperStream(self.model_path, self.initial_prompt, self.max_buffer_duration)

    def process_audio(self, samples: np.ndarray, stream=None) -> list:
        if stream is None:
            return []
        
        results = stream.accept_waveform(samples)
        return results

class MlxWhisperStream:
    def __init__(self, model_path, initial_prompt, max_buffer_duration):
        self.model_path = model_path
        self.initial_prompt = initial_prompt
        self.max_buffer_duration = max_buffer_duration
        
        self.buffer = np.array([], dtype=np.float32)
        self.buffer_duration = 0.0
        
        # Manual VAD State (RMS Based)
        self.silence_counter = 0.0
        self.is_speech_active = False
        self.speech_threshold = 0.01

        # Overlap State
        self.prev_chunk_tail = np.array([], dtype=np.float32)
        
    def accept_waveform(self, samples: np.ndarray) -> list:
        results = []
        
        # 1. Append to buffer
        self.buffer = np.concatenate((self.buffer, samples))
        chunk_duration = len(samples) / 16000.0
        self.buffer_duration += chunk_duration
        
        # 2. RMS Calculation
        if len(samples) > 0:
            rms = np.sqrt(np.mean(samples**2))
        else:
            rms = 0.0
            
        is_speech = rms > self.speech_threshold
        
        # 3. Trigger Logic
        should_decode = False
        
        # State Machine
        if is_speech:
            if not self.is_speech_active:
                logger.info("Speech Start Detected (RMS)")
            self.is_speech_active = True
            self.silence_counter = 0.0
        else:
            if self.is_speech_active:
                self.silence_counter += chunk_duration
            
        # Debug Log periodically (every ~1 second)
        if len(self.buffer) % 16000 == 0: 
             logger.info(f"Buf: {self.buffer_duration:.2f}s, RMS: {rms:.4f}, Active: {self.is_speech_active}, Sil: {self.silence_counter:.2f}s")

        # Trigger Rule: We had speech recently, and now we have >0.6s silence
        if self.is_speech_active and self.silence_counter > 0.6:
             logger.info(f"VAD Silence Triggered (RMS). Buffer: {self.buffer_duration:.2f}s")
             should_decode = True
             self.is_speech_active = False # Reset state
             self.silence_counter = 0.0

        # Priority 2: Max Duration Timeout
        if self.buffer_duration >= self.max_buffer_duration:
            logger.info(f"Max Duration Triggered. Buffer: {self.buffer_duration:.2f}s")
            should_decode = True
            
        if should_decode and len(self.buffer) > 0:
            results.extend(self._finalize())
            
        return results

    def finalize(self) -> list:
        """Force finalize (transcribe) current buffer if meaningful."""
        if len(self.buffer) / 16000.0 > 0.5: # Only transcribe if buffer > 0.5s
            logger.info(f"External Finalize Triggered. Buffer: {self.buffer_duration:.2f}s")
            return self._finalize()
        return []

    def _finalize(self) -> list:
        results = []
        
        # Prepare audio with overlap
        # Prepend the tail of the previous chunk to the current chunk
        if len(self.prev_chunk_tail) > 0:
            audio_to_transcribe = np.concatenate((self.prev_chunk_tail, self.buffer))
            logger.info(f"Pre-padding added: {len(self.prev_chunk_tail)/16000.0:.2f}s")
        else:
            audio_to_transcribe = self.buffer

        # Transcribe
        text = self._transcribe(audio_to_transcribe)
        if text.strip():
            results.append({"text": text, "is_final": True})
        
        # Save Tail for Next Chunk (Lookback)
        # Keep last 1.0s (16000 samples)
        lookback_samples = 16000
        if len(self.buffer) > lookback_samples:
            self.prev_chunk_tail = self.buffer[-lookback_samples:]
        else:
            # If buffer is smaller than 1.0s, keep all of it
            self.prev_chunk_tail = self.buffer
            
        # Log the saved lookback tail for verification
        logger.info(f"Saved lookback tail: {len(self.prev_chunk_tail)/16000.0:.2f}s")

        # Clear buffer
        self.buffer = np.array([], dtype=np.float32)
        self.buffer_duration = 0.0
        # Reset state
        self.is_speech_active = False
        self.silence_counter = 0.0
        return results

    def _transcribe(self, audio_data: np.ndarray) -> str:
        try:
            logger.info(f"MLX Whisper Transcribing {len(audio_data)/16000.0:.2f}s of audio...")
            
            result = mlx_whisper.transcribe(
                audio_data,
                path_or_hf_repo=self.model_path,
                language="en", 
                initial_prompt=self.initial_prompt,
                # Hallucination Suppression Parameters
                condition_on_previous_text=False,
                no_speech_threshold=0.6,
                logprob_threshold=-1.0,
                # Stricter Loop Prevention
                compression_ratio_threshold=2.0, # Stricter than default 2.4
                temperature=(0.0, 0.2, 0.4, 0.6, 0.8, 1.0) # Fallback temperatures
            )
            
            text = result.get("text", "").strip()
            logger.info(f"MLX Whisper Result: {text}")
            return text
            
        except Exception as e:
            logger.error(f"MLX Whisper Transcription Failed: {e}")
            return ""
