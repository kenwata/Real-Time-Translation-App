# Real-time Transcription App
[English](./README.md) | [日本語]

---

## 概要
本アプリは **Next.js** (フロントエンド) と **FastAPI** (バックエンド) で構築された、高性能な **リアルタイム音声文字起こしアプリケーション** です。**MLX** (Apple Silicon) と **Sherpa-ONNX** を活用することで、用途に応じて柔軟な音声認識オプションを提供します。

ニーズに合わせて以下の2つのモデルを選択可能です：

*   **Parakeet TDT (MLX)**:
    *   **高精度**: 長文の口述や精度を重視する場合に最適です。
    *   **スマートバッファリング**: VAD (音声区間検出) と句読点判定を用いて、文の区切りでインテリジェントにテキストを確定させます。文脈を考慮した自然な文字起こしが可能です。
    *   **最適化**: Apple Silicon上で効率的に動作します。
*   **Zipformer (Sherpa-ONNX)**:
    *   **低遅延**: 話しているそばから即座に文字が表示されます。
    *   **ストリーミング**: 即時性が求められるシーンに最適です。

### 主な機能
*   **Apple Silicon 最適化**: **MLX** を採用し、Mac上で極めて効率的に動作します。
*   **ローカル推論**: 全てのAIモデルはローカルマシン上で動作するため、プライバシーが保護されます。
*   **モデル選択**: 精度重視 (Parakeet) と速度重視 (Zipformer) を瞬時に切り替え可能です。
*   **スマートチャンキング**: 句読点やポーズに基づいた自然な区切りで文字起こしを行います (Parakeet)。
*   **英語・中国語対応**: 英語および中国語の音声認識に最適化されています。
*   **モダンなUI**: Material UI (MUI) を採用した、使いやすくレスポンシブなデザインです。

## 技術スタック
*   **フロントエンド**: Next.js, React, Material UI (MUI)
*   **バックエンド**: Python, FastAPI, WebSocket
*   **AIエンジン**:
    *   **MLX**: Parakeet TDT (Apple Silicon 最適化)
    *   [Sherpa-ONNX](https://github.com/k2-fsa/sherpa-onnx): Zipformer および VAD
*   **使用モデル**: 
    *   **Parakeet TDT** (0.6B) - via MLX
    *   **Zipformer** (Streaming) - via Sherpa-ONNX
    *   **Silero VAD** - 音声区間検出

## セットアップと使用方法

### システム要件 (macOS)
**1. Homebrew のインストール** (未インストールの場合):
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

**2. ツールのインストール**:
**ffmpeg** (音声処理用) と **mise** (バージョン管理用) のインストールが必要です。

```bash
# ffmpeg と mise のインストール
brew install ffmpeg mise
```

### 前提条件
*   **Node.js & Python**: 本プロジェクトには `mise.toml` が含まれています。
    *   プロジェクトルートで `mise install` を実行すると、適切なバージョン (Python 3.11, Node.js latest) が自動的にインストールされます。
*   **uv**: 高速なPythonパッケージマネージャ (推奨)。別途インストールするか、miseで設定してください。

### 1. バックエンドのセットアップ
```bash
cd backend
# 依存関係のインストール (.venv フォルダが自動作成されます)
uv sync

# モデルのダウンロード
uv run download_models.py
```

### 2. フロントエンドのセットアップ
```bash
cd frontend
npm install
```

### 3. アプリケーションの起動
**バックエンド:**
```bash
cd backend
uv run server.py
# サーバーは http://localhost:8000 で起動します
```

**フロントエンド:**
```bash
cd frontend
npm run dev
# アプリは http://localhost:3000 で起動します
```

## ライセンス
MIT
