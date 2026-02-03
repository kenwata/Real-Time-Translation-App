from huggingface_hub import snapshot_download
import os

def download_model():
    repo_id = "csukuangfj/sherpa-onnx-streaming-zipformer-en-2023-06-26"
    print(f"Downloading {repo_id}...")
    
    # Download to backend directory
    local_dir = os.path.join("backend", "sherpa-onnx-streaming-zipformer-en-2023-06-26")
    
    snapshot_download(repo_id=repo_id, local_dir=local_dir)
    print(f"Downloaded to {local_dir}")

if __name__ == "__main__":
    download_model()
