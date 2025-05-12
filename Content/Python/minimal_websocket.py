"""
Minimal WebSocket server implementation for Unreal Engine.
This script starts a WebSocket server in a separate process to avoid freezing Unreal Engine.
"""

import unreal
import sys
import os
import subprocess
import time

# Global variables
server_process = None

# Start the server as a separate process
def start_server():
    """Start the WebSocket server as a separate process"""
    global server_process
    
    try:
        unreal.log("Starting minimal WebSocket server...")
        
        # Get the directory of this script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Get the path to the WebSocket server script
        server_script_path = os.path.join(script_dir, "mcp_server_refactored.py")
        
        # Check if the script exists
        if not os.path.exists(server_script_path):
            unreal.log_error(f"WebSocket server script not found at: {server_script_path}")
            return False
            
        # Get the Python executable
        python_executable = sys.executable
        
        # Start the server process
        unreal.log(f"Starting WebSocket server process: {python_executable} {server_script_path}")
        
        # Create a new process
        if sys.platform == "win32":
            # Windows
            server_process = subprocess.Popen(
                [python_executable, server_script_path],
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
        else:
            # Unix
            server_process = subprocess.Popen(
                [python_executable, server_script_path]
            )
            
        # Wait briefly to allow the server to start
        time.sleep(1)
        
        # Check if the process is still running
        if server_process.poll() is None:
            unreal.log("✅ WebSocket server started successfully")
            return True
        else:
            unreal.log_error(f"❌ WebSocket server process exited with code: {server_process.returncode}")
            server_process = None
            return False
    except Exception as e:
        unreal.log_error(f"Error starting WebSocket server: {str(e)}")
        import traceback
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
        
        # Start the server
        if start_server():
            unreal.log("Server started successfully")
            
            # Wait briefly
            time.sleep(2)
            
            # Check status
            status = get_server_status()
            unreal.log(f"Server status: {status}")
            
            # Stop the server
            if stop_server():
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
        import traceback
        unreal.log_error(traceback.format_exc())
        return False
