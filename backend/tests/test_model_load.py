import sherpa_onnx
import logging
import os
import sys

# Try to find config
try:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
    from backend.core.config import MODEL_DIR
except ImportError:
    MODEL_DIR = "../models"

logging.basicConfig(level=logging.INFO)

def test_load():
    model_dir = os.path.join(MODEL_DIR, "asr", "sherpa-onnx-streaming-zipformer-en-2023-06-26")
    logging.info(f"Loading Streaming Zipformer from {model_dir}")
    
    tokens = os.path.join(model_dir, "tokens.txt")
    encoder = os.path.join(model_dir, "encoder-epoch-99-avg-1-chunk-16-left-128.int8.onnx")
    decoder = os.path.join(model_dir, "decoder-epoch-99-avg-1-chunk-16-left-128.int8.onnx")
    joiner = os.path.join(model_dir, "joiner-epoch-99-avg-1-chunk-16-left-128.int8.onnx")

    if not os.path.exists(encoder):
        logging.error(f"Model file not found: {encoder}")
        return

    try:
        recognizer = sherpa_onnx.OnlineRecognizer.from_transducer(
            tokens=tokens,
            encoder=encoder,
            decoder=decoder,
            joiner=joiner,
            num_threads=1,
            sample_rate=16000,
            feature_dim=80,
            decoding_method="greedy_search",
        )
        logging.info("Successfully loaded OnlineRecognizer model!")
    except Exception as e:
        logging.error(f"Failed to load model: {e}")

if __name__ == "__main__":
    test_load()
