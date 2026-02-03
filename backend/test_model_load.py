import sherpa_onnx
import logging

logging.basicConfig(level=logging.INFO)

def test_load():
    model_dir = "sherpa-onnx-zipformer-gigaspeech-2023-12-12"
    logging.info(f"Loading English Zipformer (Gigaspeech) model from {model_dir}")
    
    try:
        recognizer = sherpa_onnx.OfflineRecognizer.from_transducer(
            encoder=f"./{model_dir}/encoder-epoch-30-avg-1.onnx",
            decoder=f"./{model_dir}/decoder-epoch-30-avg-1.onnx",
            joiner=f"./{model_dir}/joiner-epoch-30-avg-1.onnx",
            tokens=f"./{model_dir}/tokens.txt",
            num_threads=1,
            sample_rate=16000,
            feature_dim=80,
            decoding_method="modified_beam_search",
        )
        logging.info("Successfully loaded model!")
    except Exception as e:
        logging.error(f"Failed to load model: {e}")

if __name__ == "__main__":
    test_load()
