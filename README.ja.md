# Real-time Transcription App
[English](./README.md) | [日本語]

---

## 概要
**Sherpa-ONNX** を搭載した、高性能なリアルタイム音声文字起こしアプリケーションです。フロントエンドには **Next.js**、バックエンドには **FastAPI** を使用しています。

以下の2つのモードをサポートしています：
1.  **オフラインモード (Offline Mode)**: VAD (音声区間検出) を使用した高精度な文字起こしモードです。話し終わった後に一括で変換します。**SenseVoice** や **Zipformer** モデルに対応しています。
2.  **ストリーミングモード (Streaming Mode)**: 低遅延のリアルタイム文字起こしモードです。話している最中に文字が次々と表示されます。**Streaming Zipformer** モデルを使用します。

### 主な機能
*   **ローカル推論**: 全てのAIモデルはローカルマシン上で動作するため、プライバシーが保護されます。
*   **デュアルモード**: 精度重視の「オフラインモード」と、即時性重視の「ストリーミングモード」を切り替え可能です。
*   **句読点の自動付与**: 文字起こし結果に自動で句読点（カンマ、ピリオド、疑問符など）を付与します。
*   **英語・中国語対応**: 英語および中国語の音声認識に最適化されています。
*   **モダンなUI**: Material UI (MUI) を採用した、使いやすくレスポンシブなデザインです。

## 技術スタック
*   **フロントエンド**: Next.js, React, Material UI (MUI)
*   **バックエンド**: Python, FastAPI, WebSocket
*   **AIエンジンプ**: [Sherpa-ONNX](https://github.com/k2-fsa/sherpa-onnx)
*   **使用モデル**: 
    *   SenseVoice (多言語対応)
    *   Zipformer (英語・中国語)
    *   CT-Transformer (句読点復元)

## セットアップと使用方法

### 前提条件
*   Node.js (フロントエンド用)
*   Python 3.10以上 (バックエンド用)
*   `uv` (高速なPythonパッケージマネージャ) 推奨

### 1. バックエンドのセットアップ
```bash
cd backend
# 依存関係のインストール
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
