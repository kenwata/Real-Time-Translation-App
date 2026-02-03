# Real-time Transcription App
[English] | [日本語](./README.ja.md)

---

## Description
This is a high-performance real-time speech transcription application built with **Next.js** (Frontend) and **FastAPI** (Backend), powered by **Sherpa-ONNX**.

It supports two modes:
1.  **Offline Mode**: High-accuracy transcription using VAD (Voice Activity Detection). Transcribes after a sentence is finished. Supports **SenseVoice** and **Zipformer**.
2.  **Streaming Mode**: Real-time transcription with low latency. Words appear incrementally as you speak. Powered by **Streaming Zipformer**.

### Key Features
*   **Local Inference**: All models run locally on your machine (privacy-focused).
*   **Dual Modes**: Choose between maximum accuracy (Offline) or immediate feedback (Streaming).
*   **Punctuation Restoration**: Automatically adds punctuation (commas, periods, question marks) to transcripts.
*   **English & Chinese Support**: Optimized for English and Chinese speech recognition.
*   **Modern UI**: Built with Material UI (MUI) for a clean and responsive experience.

## Tech Stack
*   **Frontend**: Next.js, React, Material UI (MUI)
*   **Backend**: Python, FastAPI, WebSocket
*   **AI Engine**: [Sherpa-ONNX](https://github.com/k2-fsa/sherpa-onnx) (Next-gen Kaldi)
*   **Models**: 
    *   SenseVoice (Multilingual)
    *   Zipformer (English & Chinese)
    *   CT-Transformer (Punctuation)

## Setup & Usage

### Prerequisites
*   Node.js (for frontend)
*   Python 3.10+ (for backend)
*   `uv` (fast Python package installer) recommended, or standard `pip`.

### 1. Backend Setup
```bash
cd backend
# Install dependencies
uv sync
# Or with pip: pip install -r requirements.txt (if generated)

# Download Models
uv run download_models.py
```

### 2. Frontend Setup
```bash
cd frontend
npm install
```

### 3. Run Application
**Backend:**
```bash
cd backend
uv run server.py
# Server runs at http://localhost:8000
```

**Frontend:**
```bash
cd frontend
npm run dev
# App runs at http://localhost:3000
```

## License
MIT
