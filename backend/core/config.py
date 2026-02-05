import os

# Base directory of the backend project (parent of 'core')
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Directories
MODEL_DIR = os.path.join(BASE_DIR, "models")
LOG_DIR = os.path.join(BASE_DIR, "logs")
RECORDINGS_DIR = os.path.join(BASE_DIR, "recordings")

# Ensure directories exist
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(RECORDINGS_DIR, exist_ok=True)
os.makedirs(MODEL_DIR, exist_ok=True)

# Logging
LOG_LEVEL = "INFO"
LOG_FILE = os.path.join(LOG_DIR, "server.log")
