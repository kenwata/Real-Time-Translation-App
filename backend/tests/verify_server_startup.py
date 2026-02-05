import sys
import os
import logging
from fastapi import FastAPI

# Add project root to sys.path explicitly to mimic what happens in server.py fallback
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# Mimic server.py imports
try:
    from backend.app.server import app, manager
    print("PASS: Imported app and manager.")
except ImportError as e:
    print(f"FATAL: Failed to import server: {e}")
    sys.exit(1)
except Exception as e:
    print(f"FATAL: Failed to init server module: {e}")
    sys.exit(1)

# Try initializing service
print("Initializing Service via Manager...")
try:
    service = manager.get_service("en")
    print("PASS: Service initialized.")
except Exception as e:
    print(f"FATAL: Failed to get service: {e}")
    sys.exit(1)

print("Server startup simulation passed.")
