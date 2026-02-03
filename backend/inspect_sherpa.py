import sherpa_onnx

print("Sherpa-ONNX version:", sherpa_onnx.__version__)
print("\n--- OfflineRecognizer ---")
try:
    help(sherpa_onnx.OfflineRecognizer)
except Exception as e:
    print(e)

print("\n--- OfflineRecognizerConfig ---")
try:
    help(sherpa_onnx.OfflineRecognizerConfig)
except Exception as e:
    print(e)
