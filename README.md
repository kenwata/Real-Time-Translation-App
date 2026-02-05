# Real-time Transcription App
[English] | [日本語](./README.ja.md)

---

## Description
This is a high-performance **Real-time Transcription App** built with **Next.js** (Frontend) and **FastAPI** (Backend). It leverages the power of **MLX** (Apple Silicon) and **Sherpa-ONNX** to provide flexible speech recognition options.

You can choose between two models depending on your needs:

*   **Parakeet TDT (MLX)**:
    *   **High Accuracy**: Best for dictation and long-form speech.
    *   **Smart Buffering**: Commits text intelligently at sentence boundaries (using VAD & punctuation) for better context.
    *   **Optimized**: Runs efficiently on Apple Silicon.
*   **Zipformer (Sherpa-ONNX)**:
    *   **Low Latency**: Words appear instantly as you speak.
    *   **Streaming**: Best for scenarios where immediate feedback is critical.

### Key Features
*   **Apple Silicon Optimized**: Uses **MLX** for highly efficient local inference on Mac.
*   **Local Inference**: All models run locally on your machine (privacy-focused).
*   **Selectable Models**: Switch between Parakeet (Accuracy) and Zipformer (Speed) on the fly.
*   **Smart Chunking**: Intelligent segmentation based on punctuation and pauses (Parakeet).
*   **English & Chinese Support**: Optimized for English and Chinese speech recognition.
*   **Modern UI**: Built with Material UI (MUI) for a clean and responsive experience.

## Tech Stack
*   **Frontend**: Next.js, React, Material UI (MUI)
*   **Backend**: Python, FastAPI, WebSocket
*   **AI Engines**:
    *   **MLX**: For Parakeet TDT (Apple Silicon optimization).
    *   [Sherpa-ONNX](https://github.com/k2-fsa/sherpa-onnx): For Zipformer and VAD.
*   **Models**: 
    *   **Parakeet TDT** (0.6B) - via MLX
    *   **Zipformer** (Streaming) - via Sherpa-ONNX
    *   **Silero VAD** - Voice Activity Detection

## Setup & Usage

### System Requirements (macOS)
**1. Install Homebrew** (if not already installed):
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

**2. Install Tools**:
Ensure you have **ffmpeg** (for audio processing) and **mise** (version manager) installed.

```bash
# Install ffmpeg and mise
brew install ffmpeg mise
```

### Prerequisites
*   **Node.js & Python**: This project includes a `mise.toml` file.
    *   Run `mise install` in the project root to automatically install the correct versions (Python 3.11, Node.js latest).
*   **uv**: Fast Python package installer (recommended). `mise` can handle this if configured, or install manually.

### 1. Backend Setup
```bash
cd backend
# Install dependencies (creates .venv folder automatically)
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
