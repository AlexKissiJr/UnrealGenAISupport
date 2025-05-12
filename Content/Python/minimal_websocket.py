"""
Minimal WebSocket server implementation for Unreal Engine.
This script starts a WebSocket server in a separate process to avoid freezing Unreal Engine.
"""

import unreal
import sys
import os
import subprocess
import time
import traceback

# Enable verbose logging
VERBOSE = True

def verbose_log(message):
    """Log a verbose message"""
    if VERBOSE:
        unreal.log(f"[VERBOSE] {message}")

# Print system information
unreal.log(f"Python version: {sys.version}")
unreal.log(f"Python executable: {sys.executable}")
unreal.log(f"Current working directory: {os.getcwd()}")
unreal.log(f"Script directory: {os.path.dirname(os.path.abspath(__file__))}")
unreal.log(f"Platform: {sys.platform}")
unreal.log(f"Unreal Engine version: {unreal.SystemLibrary.get_engine_version()}")

# Global variables
server_process = None

# Start the server as a separate process
def start_server():
    """Start the WebSocket server as a separate process"""
    global server_process

    try:
        unreal.log("Starting minimal WebSocket server...")
        verbose_log("Entering start_server function")

        # Get the directory of this script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        verbose_log(f"Script directory: {script_dir}")

        # Get the path to the WebSocket server script
        server_script_path = os.path.join(script_dir, "mcp_server_refactored.py")
        verbose_log(f"Server script path: {server_script_path}")

        # Check if the script exists
        if not os.path.exists(server_script_path):
            unreal.log_error(f"WebSocket server script not found at: {server_script_path}")
            # Try to list files in the directory
            try:
                files = os.listdir(script_dir)
                unreal.log(f"Files in directory: {files}")
            except Exception as e:
                unreal.log_error(f"Error listing files: {str(e)}")
            return False

        # Get the Python executable
        python_executable = sys.executable
        verbose_log(f"Python executable: {python_executable}")

        # Start the server process
        unreal.log(f"Starting WebSocket server process: {python_executable} {server_script_path}")

        # Create a new process with output capture
        try:
            verbose_log("Creating subprocess...")
            if sys.platform == "win32":
                # Windows
                verbose_log("Using Windows subprocess creation")
                server_process = subprocess.Popen(
                    [python_executable, server_script_path],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    creationflags=subprocess.CREATE_NEW_CONSOLE
                )
            else:
                # Unix
                verbose_log("Using Unix subprocess creation")
                server_process = subprocess.Popen(
                    [python_executable, server_script_path],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )

            verbose_log(f"Subprocess created with PID: {server_process.pid}")
        except Exception as e:
            unreal.log_error(f"Error creating subprocess: {str(e)}")
            unreal.log_error(traceback.format_exc())
            return False

        # Wait briefly to allow the server to start
        verbose_log("Waiting for server to start...")
        time.sleep(1)

        # Try to read any output
        try:
            stdout_data, stderr_data = server_process.communicate(timeout=0.1)
            if stdout_data:
                verbose_log(f"Server stdout: {stdout_data.decode('utf-8')}")
            if stderr_data:
                verbose_log(f"Server stderr: {stderr_data.decode('utf-8')}")
        except subprocess.TimeoutExpired:
            verbose_log("No output from server yet (timeout)")
        except Exception as e:
            verbose_log(f"Error reading server output: {str(e)}")

        # Check if the process is still running
        poll_result = server_process.poll()
        verbose_log(f"Process poll result: {poll_result}")

        if poll_result is None:
            unreal.log("✅ WebSocket server started successfully")
            return True
        else:
            unreal.log_error(f"❌ WebSocket server process exited with code: {poll_result}")

            # Try to read any output
            try:
                stdout_data, stderr_data = server_process.communicate(timeout=0.1)
                if stdout_data:
                    unreal.log(f"Server stdout: {stdout_data.decode('utf-8')}")
                if stderr_data:
                    unreal.log_error(f"Server stderr: {stderr_data.decode('utf-8')}")
            except Exception as e:
                unreal.log_error(f"Error reading server output: {str(e)}")

            server_process = None
            return False
    except Exception as e:
        unreal.log_error(f"Error starting WebSocket server: {str(e)}")
        unreal.log_error(traceback.format_exc())
        return False

# Stop the server
def stop_server():
    """Stop the WebSocket server"""
    global server_process

    try:
        # Check if the process is running
        if server_process is None:
            unreal.log_warning("WebSocket server is not running")
            return True

        # Check if the process has already exited
        if server_process.poll() is not None:
            unreal.log(f"WebSocket server process already exited with code: {server_process.returncode}")
            server_process = None
            return True

        # Terminate the process
        unreal.log("Stopping WebSocket server process...")

        server_process.terminate()

        # Wait for the process to exit
        try:
            server_process.wait(timeout=5)
            unreal.log(f"WebSocket server process exited with code: {server_process.returncode}")
        except subprocess.TimeoutExpired:
            unreal.log_warning("WebSocket server process did not exit within timeout, forcing termination")
            server_process.kill()

        server_process = None
        unreal.log("WebSocket server stopped")
        return True
    except Exception as e:
        unreal.log_error(f"Error stopping WebSocket server: {str(e)}")
        import traceback
        unreal.log_error(traceback.format_exc())
        return False

# Check if the server is running
def is_server_running():
    """Check if the WebSocket server is running"""
    global server_process

    try:
        if server_process is None:
            return False

        return server_process.poll() is None
    except Exception as e:
        unreal.log_error(f"Error checking if WebSocket server is running: {str(e)}")
        import traceback
        unreal.log_error(traceback.format_exc())
        return False

# Get the server status
def get_server_status():
    """Get the status of the WebSocket server"""
    global server_process

    try:
        if is_server_running():
            return "running"
        else:
            return "stopped"
    except Exception as e:
        unreal.log_error(f"Error getting WebSocket server status: {str(e)}")
        import traceback
        unreal.log_error(traceback.format_exc())
        return "error"

# Functions to run from Unreal Engine
def start():
    """Start the WebSocket server"""
    return start_server()

def stop():
    """Stop the WebSocket server"""
    return stop_server()

def status():
    """Get the status of the WebSocket server"""
    return get_server_status()

# Test function
def test():
    """Test the WebSocket server"""
    try:
        unreal.log("Testing minimal WebSocket server...")
        verbose_log("Entering test function")

        # Start the server
        unreal.log("Calling start_server()...")
        start_result = start_server()
        unreal.log(f"start_server() returned: {start_result}")

        if start_result:
            unreal.log("Server started successfully")

            # Wait briefly
            verbose_log("Waiting for 2 seconds...")
            time.sleep(2)

            # Check status
            verbose_log("Checking server status...")
            status = get_server_status()
            unreal.log(f"Server status: {status}")

            # Stop the server
            verbose_log("Calling stop_server()...")
            stop_result = stop_server()
            unreal.log(f"stop_server() returned: {stop_result}")

            if stop_result:
                unreal.log("Server stopped successfully")
                return True
            else:
                unreal.log_error("Failed to stop server")
                return False
        else:
            unreal.log_error("Failed to start server")
            return False
    except Exception as e:
        unreal.log_error(f"Error testing WebSocket server: {str(e)}")
        unreal.log_error(traceback.format_exc())
        return False
