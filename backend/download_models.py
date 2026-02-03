import os
import urllib.request
import tarfile
import zipfile
try:
    from huggingface_hub import snapshot_download
except ImportError:
    snapshot_download = None

def download_file(url, filename):
    if not os.path.exists(filename):
        print(f"Downloading {filename} from {url}...")
        urllib.request.urlretrieve(url, filename)
        print("Download complete.")
    else:
        print(f"{filename} already exists. Skipping download.")

def extract_tar(filename):
    print(f"Extracting {filename}...")
    with tarfile.open(filename, "r:bz2") as tar:
        tar.extractall()
    print("Extraction complete.")

def extract_zip(filename):
    print(f"Extracting {filename}...")
    with zipfile.ZipFile(filename, 'r') as zip_ref:
        zip_ref.extractall()
    print("Extraction complete.")

def main():
    # SenseVoiceSmall (Multilingual including English) - int8 version
    sense_voice_url = "https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-sense-voice-zh-en-ja-ko-yue-int8-2024-07-17.tar.bz2"
    sense_voice_file = "sherpa-onnx-sense-voice-zh-en-ja-ko-yue-int8-2024-07-17.tar.bz2"
    
    download_file(sense_voice_url, sense_voice_file)
    extract_tar(sense_voice_file)

    # Silero VAD
    vad_url = "https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/silero_vad.onnx"
    vad_file = "silero_vad.onnx"

    download_file(vad_url, vad_file)
    # No extraction needed for single file

    # Zipformer (Multi-En-Zh)
    zipformer_url = "https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-zipformer-multi-zh-hans-2023-9-2.tar.bz2"
    zipformer_file = "sherpa-onnx-zipformer-multi-zh-hans-2023-9-2.tar.bz2"
    
    download_file(zipformer_url, zipformer_file)
    extract_tar(zipformer_file)

    # Zipformer (English - Gigaspeech)
    zipformer_en_urls = [
        "https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-zipformer-gigaspeech-2023-12-12.tar.bz2",
        # "https://huggingface.co/csukuangfj/sherpa-onnx-streaming-zipformer-en-2023-06-26/resolve/main/sherpa-onnx-streaming-zipformer-en-2023-06-26.tar.bz2",
        "https://github.com/k2-fsa/sherpa-onnx/releases/download/punctuation-models/sherpa-onnx-punct-ct-transformer-zh-en-vocab272727-2024-04-12.tar.bz2",
    ]
    zipformer_en_files = [
        "sherpa-onnx-zipformer-gigaspeech-2023-12-12.tar.bz2",
        # "sherpa-onnx-streaming-zipformer-en-2023-06-26.tar.bz2",
        "sherpa-onnx-punct-ct-transformer-zh-en-vocab272727-2024-04-12.tar.bz2",
    ]
    
    for url, filename in zip(zipformer_en_urls, zipformer_en_files):
        download_file(url, filename)
        extract_tar(filename)

    # Streaming Zipformer (English) - via Hugging Face
    print("Downloading Streaming Zipformer (English)...")
    if snapshot_download:
        repo_id = "csukuangfj/sherpa-onnx-streaming-zipformer-en-2023-06-26"
        local_dir = "sherpa-onnx-streaming-zipformer-en-2023-06-26"
        if not os.path.exists(local_dir):
            snapshot_download(repo_id=repo_id, local_dir=local_dir)
            print(f"Downloaded to {local_dir}")
        else:
            print(f"{local_dir} already exists. Skipping.")
    else:
        print("Warning: 'huggingface_hub' not installed. Skipping streaming model download.")
        print("Run 'pip install huggingface_hub' to enable this.")

if __name__ == "__main__":
    main()
