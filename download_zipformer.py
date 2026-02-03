import os
import urllib.request
import tarfile

def download_and_extract(url, extract_to='.'):
    filename = url.split('/')[-1]
    if os.path.exists(extract_to + "/" + filename.replace(".tar.bz2", "")):
        print(f"{filename} already exists, skipping.")
        return

    print(f"Downloading {filename}...")
    urllib.request.urlretrieve(url, filename)
    
    print(f"Extracting {filename}...")
    with tarfile.open(filename, "r:bz2") as tar:
        tar.extractall(path=extract_to)
    
    os.remove(filename)
    print("Done.")

if __name__ == "__main__":
    urls = [
        "https://github.com/k2-fsa/sherpa-onnx/releases/download/v1.9.10/sherpa-onnx-zipformer-multi-zh-hans-2023-9-2.tar.bz2",
        "https://github.com/k2-fsa/sherpa-onnx/releases/download/v1.9.23/sherpa-onnx-zipformer-multi-zh-hans-2023-9-2.tar.bz2",
        "https://github.com/k2-fsa/sherpa-onnx/releases/download/v1.9.23/sherpa-onnx-zipformer-en-2023-06-26.tar.bz2" # Fallback to English
    ]
    
    for url in urls:
        try:
            download_and_extract(url, extract_to="backend")
            print(f"Successfully downloaded {url}")
            break
        except Exception as e:
            print(f"Failed {url}: {e}")
            continue
