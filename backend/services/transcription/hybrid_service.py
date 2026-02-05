import logging
import sherpa_onnx
import numpy as np
import os
import sys

# Ensure backend modules can be found
try:
    from .mlx_whisper_service import MlxWhisperService
    from backend.core.config import MODEL_DIR
    from backend.utils.text_processing import beautify_text
except ImportError:
    # Fallback or strict import
    from mlx_whisper_service import MlxWhisperService
    from backend.core.config import MODEL_DIR
    from backend.utils.text_processing import beautify_text
    # MODEL_DIR = "models" 

logger = logging.getLogger("server")

class HybridService:
    def __init__(self):
        logger.info("Initializing Hybrid Service (Zipformer + MLX Whisper)...")
        
        # 1. Initialize MLX Whisper (for Final determination)
        self.mlx_whisper_service = MlxWhisperService()
        
        # 2. Initialize Zipformer (for Real-time Preview)
        model_dir = os.path.join(MODEL_DIR, "asr", "sherpa-onnx-streaming-zipformer-en-2023-06-26")
        tokens_path = os.path.join(model_dir, "tokens.txt")
        encoder_path = os.path.join(model_dir, "encoder-epoch-99-avg-1-chunk-16-left-128.int8.onnx")
        decoder_path = os.path.join(model_dir, "decoder-epoch-99-avg-1-chunk-16-left-128.int8.onnx")
        joiner_path = os.path.join(model_dir, "joiner-epoch-99-avg-1-chunk-16-left-128.int8.onnx")
        
        logger.info(f"Loading Zipformer model from {model_dir}")
        self.online_recognizer = sherpa_onnx.OnlineRecognizer.from_transducer(
            tokens=tokens_path,
            encoder=encoder_path,
            decoder=decoder_path,
            joiner=joiner_path,
            num_threads=1,
            sample_rate=16000,
            feature_dim=80,
            decoding_method="greedy_search",
            provider="cpu"
        )
        
        # 3. Initialize Punctuation
        punct_model_dir = os.path.join(MODEL_DIR, "punctuation", "sherpa-onnx-punct-ct-transformer-zh-en-vocab272727-2024-04-12")
        punct_model_path = os.path.join(punct_model_dir, "model.onnx")
        if not os.path.exists(punct_model_path):
             # Fallback if tar extraction didn't create a subdir or structure is different
             # Common fallback: maybe it's directly in punctuation dir or just name difference
             punct_model_path = os.path.join(MODEL_DIR, "punctuation", "model.onnx")

        logger.info(f"Loading Punctuation model from {punct_model_dir}")
        try:
            punct_config = sherpa_onnx.OfflinePunctuationConfig()
            punct_config.model.ct_transformer = punct_model_path
            self.punct_model = sherpa_onnx.OfflinePunctuation(punct_config)
            logger.info("Punctuation model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load punctuation model: {e}")
            self.punct_model = None
            
        logger.info("Hybrid Service initialized.")

    def create_stream(self):
        return HybridStream(self.mlx_whisper_service, self.online_recognizer, self.punct_model)

    def process_audio(self, samples: np.ndarray, stream=None) -> list:
        if stream is None:
            return []
        
        return stream.accept_waveform(samples)

class HybridStream:
    def __init__(self, mlx_whisper_service, online_recognizer, punct_model):
        # Stream for MLX Whisper (Buffered)
        self.mlx_stream = mlx_whisper_service.create_stream()
        
        # Stream for Zipformer (Real-time)
        self.online_stream = online_recognizer.create_stream()
        
        self.mlx_whisper_service = mlx_whisper_service
        self.online_recognizer = online_recognizer
        self.punct_model = punct_model
        
        self.last_zipformer_text = ""

    def accept_waveform(self, samples: np.ndarray) -> list:
        results = []
        
        # --- 1. Feed MLX Whisper (Buffered) ---
        # This returns results ONLY if Final (VAD/Timeout)
        
        mlx_results = self.mlx_stream.accept_waveform(samples)
        
        final_mlx_result = None
        for res in mlx_results:
            if res.get("is_final"):
                final_mlx_result = res
                results.append(res) # Add Final result to output
        
        if final_mlx_result:
            # Re-create the online stream to clear context
            self.online_stream = self.online_recognizer.create_stream()
            self.last_zipformer_text = ""
            # We don't need to add anything else, the Final result replaces everything.
            return results

        # --- 2. Feed Zipformer (Real-time) ---
        self.online_stream.accept_waveform(16000, samples)
        
        if self.online_recognizer.is_ready(self.online_stream):
            self.online_recognizer.decode_stream(self.online_stream)
                 
        # Regular Result Check
        result = self.online_recognizer.get_result(self.online_stream)
        if isinstance(result, str):
             zipformer_text = result.strip()
        else:
             zipformer_text = result.text.strip()
        
        # Only emit if text changed and it's not empty
        if zipformer_text and zipformer_text != self.last_zipformer_text:
            
            # Apply Punctuation if available
            display_text = zipformer_text
            if self.punct_model:
                # Add punctuation to the text
                try:
                    # Step 1: Lowercase input to help punctuation model
                    input_to_punct = zipformer_text.lower()
                    
                    # Step 2: Apply punctuation
                    punctuated_text = self.punct_model.add_punctuation(input_to_punct)
                    
                    # Step 3: Verify & Beautify (Normalization + Casing)
                    display_text = beautify_text(punctuated_text)
                    
                except Exception as e:
                    logger.error(f"Punctuation/Beautify failed: {e}")
                    # Fallback to original text (maybe just beautify original)
                    display_text = beautify_text(zipformer_text)
                    pass
            else:
                 # Even if no punctuation model, still beautify
                 display_text = beautify_text(zipformer_text)
                
            logger.info(f"Zipformer emitting: {display_text}")
            results.append({
                "text": display_text, 
                "is_final": False # Always interim
            })
            self.last_zipformer_text = zipformer_text
            
        return results
