import sys
import os

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

print("Attempting to import HybridService...")
from backend.services.transcription.hybrid_service import HybridService
print("Successfully imported HybridService.")

