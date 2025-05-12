"""
Non-blocking WebSocket server integration for Unreal Engine.
This module provides a non-blocking WebSocket server that won't freeze Unreal Engine.
"""

import sys
import os
import time
import threading
import traceback
import subprocess
import signal
import atexit
import json
from pathlib import Path

# Try to import Unreal Engine module
try:
    import unreal
    has_unreal = True
except ImportError:
    has_unreal = False

# Global variables
server_process = None
is_running = False
pid_file_path = None

# Log functions that work both in Unreal Engine and standalone
def log_info(message):
    """Log an info message"""
    if has_unreal:
        unreal.log(message)
    else:
        print(f"[INFO] {message}", file=sys.stderr)

def log_warning(message):
    """Log a warning message"""
    if has_unreal:
        unreal.log_warning(message)
    else:
        print(f"[WARNING] {message}", file=sys.stderr)

def log_error(message, include_traceback=False):
    """Log an error message"""
    if has_unreal:
        unreal.log_error(message)
        if include_traceback:
            unreal.log_error(traceback.format_exc())
    else:
        print(f"[ERROR] {message}", file=sys.stderr)
        if include_traceback:
            traceback.print_exc(file=sys.stderr)

# Get the path to the WebSocket server script
def get_server_script_path():
    """Get the path to the WebSocket server script"""
    try:
        # Get the directory of this script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Get the path to the WebSocket server script
        server_script_path = os.path.join(script_dir, "mcp_server_refactored.py")
        
        # Check if the script exists
        if not os.path.exists(server_script_path):
            log_error(f"WebSocket server script not found at: {server_script_path}")
            return None
            
        return server_script_path
    except Exception as e:
        log_error(f"Error getting WebSocket server script path: {str(e)}", include_traceback=True)
        return None

# Get the PID file path
def get_pid_file_path():
    """Get the PID file path"""
    try:
        pid_dir = os.path.join(os.path.expanduser("~"), ".unrealgenai")
        return os.path.join(pid_dir, "mcp_server.pid")
    except Exception as e:
        log_error(f"Error getting PID file path: {str(e)}", include_traceback=True)
        return None

# Check if the server is running
def is_server_running():
    """Check if the WebSocket server is running"""
    global server_process, is_running, pid_file_path
    
    try:
        # Check if we have a server process
        if server_process is not None:
            # Check if the process is still running
            if server_process.poll() is None:
                return True
            else:
                # Process has exited
                log_warning(f"WebSocket server process exited with code: {server_process.returncode}")
                server_process = None
                is_running = False
                return False
                
        # Check if we have a PID file
        if pid_file_path is None:
            pid_file_path = get_pid_file_path()
            
        if pid_file_path and os.path.exists(pid_file_path):
            try:
                # Read the PID file
                with open(pid_file_path, "r") as f:
                    pid_data = f.read().strip().split("\n")
                    
                if len(pid_data) >= 1:
                    pid = int(pid_data[0])
                    
                    # Check if the process is running
                    if sys.platform == "win32":
                        # Windows
                        import ctypes
                        kernel32 = ctypes.windll.kernel32
                        SYNCHRONIZE = 0x00100000
                        process = kernel32.OpenProcess(SYNCHRONIZE, False, pid)
                        if process != 0:
                            kernel32.CloseHandle(process)
                            return True
                    else:
                        # Unix
                        try:
                            os.kill(pid, 0)
                            return True
                        except OSError:
                            pass
            except Exception as e:
                log_error(f"Error checking PID file: {str(e)}")
                
        return False
    except Exception as e:
        log_error(f"Error checking if WebSocket server is running: {str(e)}", include_traceback=True)
        return False

# Start the server as a separate process
def start_server():
    """Start the WebSocket server as a separate process"""
    global server_process, is_running, pid_file_path
    
    try:
        # Check if server is already running
        if is_server_running():
            log_warning("WebSocket server is already running")
            is_running = True
            return True
            
        # Get the server script path
        server_script_path = get_server_script_path()
        if not server_script_path:
            return False
            
        # Get the Python executable
        python_executable = sys.executable
        
        # Start the server process
        log_info(f"Starting WebSocket server process: {python_executable} {server_script_path}")
        
        # Create a new process group so we can kill the process and all its children
        if sys.platform == "win32":
            # Windows
            server_process = subprocess.Popen(
                [python_executable, server_script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
            )
        else:
            # Unix
            server_process = subprocess.Popen(
                [python_executable, server_script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid
            )
            
        # Register to kill the process on exit
        atexit.register(stop_server)
        
        # Wait for the server to start (up to 5 seconds)
        pid_file_path = get_pid_file_path()
        start_time = time.time()
        while time.time() - start_time < 5:
            # Check if the process is still running
            if server_process.poll() is not None:
                log_error(f"WebSocket server process exited with code: {server_process.returncode}")
                server_process = None
                is_running = False
                return False
                
            # Check if the PID file exists
            if pid_file_path and os.path.exists(pid_file_path):
                log_info("✅ WebSocket server started successfully")
                is_running = True
                return True
                
            # Sleep briefly
            time.sleep(0.1)
            
        log_error("❌ WebSocket server failed to start within timeout")
        is_running = False
        return False
    except Exception as e:
        log_error(f"Error starting WebSocket server: {str(e)}", include_traceback=True)
        is_running = False
        return False

# Stop the server
def stop_server():
    """Stop the WebSocket server"""
    global server_process, is_running, pid_file_path
    
    try:
        # Check if server is already stopped
        if not is_server_running():
            log_warning("WebSocket server is already stopped")
            is_running = False
            return True
            
        # Stop the server process
        if server_process is not None:
            log_info("Stopping WebSocket server process...")
            
            # Send SIGTERM to the process
            if sys.platform == "win32":
                # Windows
                import ctypes
                kernel32 = ctypes.windll.kernel32
                CTRL_C_EVENT = 0
                kernel32.GenerateConsoleCtrlEvent(CTRL_C_EVENT, server_process.pid)
            else:
                # Unix
                os.killpg(os.getpgid(server_process.pid), signal.SIGTERM)
                
            # Wait for the process to exit (up to 5 seconds)
            start_time = time.time()
            while time.time() - start_time < 5:
                if server_process.poll() is not None:
                    log_info(f"WebSocket server process exited with code: {server_process.returncode}")
                    server_process = None
                    break
                    
                # Sleep briefly
                time.sleep(0.1)
                
            # If the process is still running, kill it
            if server_process is not None and server_process.poll() is None:
                log_warning("WebSocket server process did not exit, killing it...")
                
                if sys.platform == "win32":
                    # Windows
                    import ctypes
                    kernel32 = ctypes.windll.kernel32
                    PROCESS_TERMINATE = 1
                    handle = kernel32.OpenProcess(PROCESS_TERMINATE, False, server_process.pid)
                    kernel32.TerminateProcess(handle, 1)
                    kernel32.CloseHandle(handle)
                else:
                    # Unix
                    os.killpg(os.getpgid(server_process.pid), signal.SIGKILL)
                    
                server_process = None
        
        # Delete the PID file
        if pid_file_path and os.path.exists(pid_file_path):
            try:
                os.remove(pid_file_path)
                log_info(f"Deleted PID file: {pid_file_path}")
            except Exception as e:
                log_error(f"Error deleting PID file: {str(e)}")
                
        is_running = False
        log_info("WebSocket server stopped")
        return True
    except Exception as e:
        log_error(f"Error stopping WebSocket server: {str(e)}", include_traceback=True)
        is_running = False
        return False

# Get the server status
def get_server_status():
    """Get the status of the WebSocket server"""
    try:
        if is_server_running():
            return {
                "status": "running",
                "pid": server_process.pid if server_process else None,
                "pid_file": pid_file_path
            }
        else:
            return {
                "status": "stopped",
                "pid": None,
                "pid_file": pid_file_path
            }
    except Exception as e:
        log_error(f"Error getting WebSocket server status: {str(e)}", include_traceback=True)
        return {
            "status": "error",
            "error": str(e)
        }

# Start the server when this script is run
if __name__ == "__main__":
    start_server()
    
    # Keep the script running
    try:
        while is_server_running():
            time.sleep(1)
    except KeyboardInterrupt:
        log_info("Stopping WebSocket server...")
        stop_server()

# Functions to run from Unreal Engine
def start():
    """Start the WebSocket server"""
    return start_server()

def stop():
    """Stop the WebSocket server"""
    return stop_server()

def status():
    """Get the status of the WebSocket server"""
    status_data = get_server_status()
    return json.dumps(status_data, indent=2)
