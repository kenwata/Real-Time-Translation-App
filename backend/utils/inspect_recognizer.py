import sherpa_onnx
import inspect

print("OfflineRecognizer signature:")
try:
    print(inspect.signature(sherpa_onnx.OfflineRecognizer))
except ValueError:
    print("Could not get signature (extensions often don't support it).")
    print("Docstring:")
    print(sherpa_onnx.OfflineRecognizer.__doc__)
    print("Init docstring:")
    print(sherpa_onnx.OfflineRecognizer.__init__.__doc__)
