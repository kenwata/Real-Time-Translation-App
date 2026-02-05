import logging
import asyncio
import numpy as np
import mlx.core as mx
from parakeet_mlx import from_pretrained
from parakeet_mlx.audio import load_audio
import os

try:
    from backend.core.config import MODEL_DIR
except ImportError:
    MODEL_DIR = "."

logger = logging.getLogger("server")

class ParakeetService:
    def __init__(self, model_name: str = "mlx-community/parakeet-tdt-0.6b-v3"):
        self.model_name = model_name
        logger.info(f"Loading Parakeet model: {model_name}")
        self.model = from_pretrained(model_name)
        logger.info(f"Parakeet model loaded successfully. Expected SR: {self.model.preprocessor_config.sample_rate}")
        self.context_manager = None
        self.stream = None
        
        # Initialize VAD for streaming endpoints
        import sherpa_onnx
        vad_config = sherpa_onnx.VadModelConfig()
        vad_config.silero_vad.model = os.path.join(MODEL_DIR, "vad", "silero_vad.onnx") # Updated path
        vad_config.silero_vad.threshold = 0.5
        vad_config.silero_vad.min_silence_duration = 0.35 # Reduced from 1.0 for faster endpointing
        vad_config.silero_vad.min_speech_duration = 0.25
        vad_config.sample_rate = 16000
        self.vad = sherpa_onnx.VoiceActivityDetector(
            config=vad_config,
            buffer_size_in_seconds=60
        )
        self.punctuation = None # Todo: Add punctuation support if compatible
        self.current_segment_duration = 0.0

    def normalize_punctuation(self, text: str) -> str:
        # Simple normalizer
        return text.replace("。", ".").replace("，", ",").replace("？", "?").replace("！", "!").replace("、", ",")
        
    def create_stream(self):
        """
        Returns a streaming transcriber object.
        """
        if self.context_manager is None:
            self.context_manager = self.model.transcribe_stream(context_size=(256, 256))
            self.stream = self.context_manager.__enter__()
            self.current_segment_duration = 0.0 # Reset duration on new stream
        return self.stream

    def close_stream(self):
        if self.context_manager:
            self.context_manager.__exit__(None, None, None)
            self.context_manager = None
            self.stream = None

    def process_audio(self, samples: np.ndarray, stream=None) -> list:
        """
        Feed audio to recognizer.
        params:
            stream: The transcriber object returned by create_stream
        """
        results = []
        
        # Ignore result of passed stream argument, use internal self.stream management
        # because we reset it on endpoint and server.py holds a stale reference.
        stream = self.stream
        
        if stream:
            # DEBUG: Capture raw audio to verify what the model hears
            import wave
            try:
                # Append to raw PCM
                with open("debug_capture.pcm", "ab") as f:
                    # Convert float32 samples to int16 bytes
                     f.write((samples * 32767).clip(-32768, 32767).astype(np.int16).tobytes())
            except Exception:
                pass 

            # Apply gain reduction (0.1) just in case input is too hot for Parakeet
            # Many MLX models are sensitive to scale.
            scaled_samples = samples * 0.1 
            
            # 1. Update Transcription
            # Convert numpy to mlx array for compatibility with parakeet's internal mx.concat
            stream.add_audio(mx.array(scaled_samples))
            res = stream.result
            text = res.text
            
            # 2. Check VAD for endpoint
            self.vad.accept_waveform(samples)
            is_vad_endpoint = not self.vad.empty()
            
            # 3. Analyze Punctuation
            # Normalize to check for standard sentence endings
            norm_text = self.normalize_punctuation(text).strip()
            has_punctuation = norm_text.endswith(('.', '?', '!'))
            
            # 4. Check for Forced Timeout (Max Duration)
            chunk_duration = len(samples) / 16000.0
            self.current_segment_duration += chunk_duration
            
            should_commit = False
            
            # Logic: 
            # - If Timeout (>15s): Force commit
            # - If VAD Endpoint + Punctuation: Commit
            # - If VAD Endpoint + No Punctuation: Ignore (wait for more context)
            
            if self.current_segment_duration > 15.0:
                logger.info(f"Forcing endpoint due to max duration ({self.current_segment_duration:.2f}s)")
                should_commit = True
            elif is_vad_endpoint:
                if has_punctuation:
                    logger.info(f"Natural Endpoint (VAD + Punctuation): {text}")
                    should_commit = True
                else:
                    logger.info(f"Ignoring VAD endpoint (No Punctuation): {text}")
                    # Clear VAD queue to "consume" this silence and continue listening
                    while not self.vad.empty():
                        self.vad.pop()
                    should_commit = False
            
            if should_commit:
                # Clear VAD just in case
                while not self.vad.empty():
                    self.vad.pop()
                
                # Reset stream on endpoint to segment text
                self.close_stream()
                self.create_stream() # Re-create immediately
                
                logger.info(f"Parakeet Commit: {text}")
                results.append({"text": text, "is_final": True})
            else:
                results.append({"text": text, "is_final": False})
            
        return results
