import socket
import subprocess
import time
import os
import sys

def is_port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def start_server():
    print("Starting backend server...")
    # Assume script is run from project root or handle relative paths
    # Best guess for project root is 2 levels up if run as python backend/utils/check_server.py
    # But usually we run from root.
    
    cmd = ["backend/.venv/bin/uvicorn", "backend.app.server:app", "--reload", "--host", "0.0.0.0", "--port", "8000"]
    
    # Check if .venv exists in expected location relative to CWD
    if not os.path.exists("backend/.venv"):
        print("Warning: backend/.venv not found in current directory. Trying to find python...")
        cmd[0] = sys.executable # Fallback to current python interpreter
        
    try:
        # Start in background (detached)? Or just Popen and let it run?
        # If we want to keep it running after this script exits, we subprocess.Popen
        subprocess.Popen(cmd)
        print("Server start command issued.")
    except Exception as e:
        print(f"Failed to start server: {e}")

def main():
    port = 8000
    if is_port_in_use(port):
        print(f"✅ Port {port} is active. Server appears to be running.")
    else:
        print(f"❌ Port {port} is closed. Server is DOWN.")
        start_server()
        
        # Wait a bit to check if it comes up
        print("Waiting for startup...")
        time.sleep(5)
        if is_port_in_use(port):
             print("✅ Server started successfully.")
        else:
             print("⚠️ Server might still be starting or failed. Check logs.")

if __name__ == "__main__":
    main()
