import sherpa_onnx
import numpy as np
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("vad_test")

def main():
    try:
        vad_config = sherpa_onnx.VadModelConfig()
        vad_config.silero_vad.model = "./silero_vad.onnx"
        vad_config.sample_rate = 16000
        
        # Lower threshold to see if it helps (default is usually around 0.5)
        vad_config.silero_vad.threshold = 0.1 
        vad_config.silero_vad.min_silence_duration = 0.1
        vad_config.silero_vad.min_speech_duration = 0.1 
        
        logger.info(f"Loading VAD from {vad_config.silero_vad.model}")
        vad = sherpa_onnx.VoiceActivityDetector(
            config=vad_config,
            buffer_size_in_seconds=60
        )
        
        logger.info("Generating audio...")
        duration = 3.0
        sample_rate = 16000
        t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
        audio = 1.0 * np.sin(2 * np.pi * 440 * t) # 440Hz sine wave (Max volume)
        audio = audio.astype(np.float32)
        
        logger.info("Feeding audio in chunks...")
        chunk_size = 512
        for i in range(0, len(audio), chunk_size):
            chunk = audio[i:i+chunk_size]
            vad.accept_waveform(chunk)
            if vad.is_speech_detected():
                 logger.info(f"Speech detected at {i/sample_rate:.2f}s")
            
        logger.info("Feeding silence...")
        silence = np.zeros(sample_rate * 2, dtype=np.float32)
        vad.accept_waveform(silence)
        
        while not vad.empty():
            segment = vad.front
            vad.pop()
            logger.info(f"Segment duration: {len(segment.samples) / sample_rate}s")

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)

if __name__ == "__main__":
    main()
