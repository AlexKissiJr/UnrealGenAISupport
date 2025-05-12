import unreal
import sys
import os
import importlib.util
import threading
import time
import json
import subprocess
import atexit

# Get the plugin's Content/Python path
plugin_content_path = unreal.Paths.project_plugins_dir() + "/UnrealGenAISupport/Content"
python_path = os.path.join(plugin_content_path, "Python")
resources_path = os.path.join(plugin_content_path, "..", "Resources")
sys.path.append(python_path)

# Global variables
server_process = None
server_thread = None
is_running = False
auto_restart = True
use_external_server = False
external_server_url = "ws://localhost:9877"

# Simple logging functions
def log_info(message):
    """Log info message"""
    unreal.log(f"[WebSocket Manager] {message}")

def log_warning(message):
    """Log warning message"""
    unreal.log_warning(f"[WebSocket Manager] {message}")

def log_error(message):
    """Log error message"""
    unreal.log_error(f"[WebSocket Manager] {message}")

def check_module_installed(module_name):
    """Check if a Python module is installed"""
    try:
        spec = importlib.util.find_spec(module_name)
        return spec is not None
    except ModuleNotFoundError:
        return False

def install_websockets():
    """Install the websockets module"""
    try:
        # Check if already installed
        if check_module_installed("websockets"):
            log_info("websockets module is already installed.")
            return True
            
        # Get Python executable
        python_exe = sys.executable
        log_info(f"Using Python executable: {python_exe}")
        
        # Install websockets
        log_info("Installing websockets module...")
        result = subprocess.call([python_exe, "-m", "pip", "install", "websockets"])
        
        if result == 0:
            log_info("websockets module installed successfully.")
            return True
        else:
            log_error("Failed to install websockets module.")
            return False
    except Exception as e:
        log_error(f"Error installing websockets module: {str(e)}")
        return False

def start_server_process():
    """Start the WebSocket server as a separate process"""
    global server_process
    
    try:
        # Check if websockets module is installed
        if not check_module_installed("websockets"):
            log_warning("websockets module not found. Attempting to install...")
            if not install_websockets():
                log_error("Failed to install websockets module. Cannot start server.")
                return False
        
        # Get the path to the echo server script
        echo_server_path = os.path.join(resources_path, "websocket_echo_server.py")
        
        # Check if the script exists
        if not os.path.exists(echo_server_path):
            log_error(f"WebSocket echo server script not found at: {echo_server_path}")
            return False
        
        # Start the server process
        log_info(f"Starting WebSocket server process: {echo_server_path}")
        
        # Get Python executable
        python_exe = sys.executable
        
        # Start the process
        server_process = subprocess.Popen(
            [python_exe, echo_server_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait a moment for the server to start
        time.sleep(1)
        
        # Check if the process is running
        if server_process.poll() is None:
            log_info("WebSocket server process started successfully.")
            return True
        else:
            stdout, stderr = server_process.communicate()
            log_error(f"WebSocket server process failed to start.")
            log_error(f"STDOUT: {stdout}")
            log_error(f"STDERR: {stderr}")
            return False
    except Exception as e:
        log_error(f"Error starting WebSocket server process: {str(e)}")
        return False

def stop_server_process():
    """Stop the WebSocket server process"""
    global server_process
    
    try:
        if server_process:
            log_info("Stopping WebSocket server process...")
            
            # Terminate the process
            server_process.terminate()
            
            # Wait for the process to terminate
            try:
                server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # Force kill if it doesn't terminate
                server_process.kill()
                server_process.wait()
            
            server_process = None
            log_info("WebSocket server process stopped.")
            return True
        else:
            log_info("No WebSocket server process to stop.")
            return True
    except Exception as e:
        log_error(f"Error stopping WebSocket server process: {str(e)}")
        return False

def monitor_server_thread():
    """Thread function to monitor the server process"""
    global server_process, is_running, auto_restart
    
    log_info("Server monitor thread started.")
    
    while is_running:
        try:
            # Check if the process is still running
            if server_process and server_process.poll() is not None:
                log_warning("WebSocket server process has stopped.")
                
                # Restart if auto-restart is enabled
                if auto_restart:
                    log_info("Auto-restarting WebSocket server...")
                    stop_server_process()
                    start_server_process()
            
            # Sleep for a while
            time.sleep(5)
        except Exception as e:
            log_error(f"Error in server monitor thread: {str(e)}")
            time.sleep(5)
    
    log_info("Server monitor thread stopped.")

def start_server():
    """Start the WebSocket server"""
    global server_thread, is_running
    
    try:
        # Don't start if already running
        if is_running:
            log_info("WebSocket server is already running.")
            return True
        
        # Set running flag
        is_running = True
        
        # Start the server process
        if not start_server_process():
            is_running = False
            return False
        
        # Start the monitor thread
        server_thread = threading.Thread(
            target=monitor_server_thread,
            daemon=True
        )
        server_thread.start()
        
        # Register cleanup function
        atexit.register(stop_server)
        
        log_info("WebSocket server started successfully.")
        return True
    except Exception as e:
        log_error(f"Error starting WebSocket server: {str(e)}")
        is_running = False
        return False

def stop_server():
    """Stop the WebSocket server"""
    global server_thread, is_running
    
    try:
        # Don't stop if not running
        if not is_running:
            log_info("WebSocket server is not running.")
            return True
        
        # Set running flag
        is_running = False
        
        # Stop the server process
        stop_server_process()
        
        # Wait for the monitor thread to exit
        if server_thread and server_thread.is_alive():
            server_thread.join(timeout=2.0)
        
        server_thread = None
        
        # Unregister cleanup function
        try:
            atexit.unregister(stop_server)
        except:
            pass
        
        log_info("WebSocket server stopped successfully.")
        return True
    except Exception as e:
        log_error(f"Error stopping WebSocket server: {str(e)}")
        return False

def is_server_running():
    """Check if the WebSocket server is running"""
    global is_running, server_process
    
    if is_running and server_process and server_process.poll() is None:
        return True
    else:
        return False

def set_auto_restart(enabled):
    """Set whether to automatically restart the server if it stops"""
    global auto_restart
    
    auto_restart = enabled
    log_info(f"Auto-restart {'enabled' if enabled else 'disabled'}.")

def set_use_external_server(enabled, url=None):
    """Set whether to use an external WebSocket server"""
    global use_external_server, external_server_url
    
    use_external_server = enabled
    
    if url:
        external_server_url = url
    
    log_info(f"External server {'enabled' if enabled else 'disabled'}.")
    if enabled:
        log_info(f"External server URL: {external_server_url}")

def get_server_url():
    """Get the WebSocket server URL"""
    global use_external_server, external_server_url
    
    if use_external_server:
        return external_server_url
    else:
        return "ws://localhost:9877"

# Initialize the module
def initialize():
    """Initialize the WebSocket manager"""
    log_info("Initializing WebSocket manager...")
    
    # Check if websockets module is installed
    if not check_module_installed("websockets"):
        log_warning("websockets module not found. Server will be started when needed.")
    
    log_info("WebSocket manager initialized.")
    return True

# Clean up on module unload
def cleanup():
    """Clean up on module unload"""
    log_info("Cleaning up WebSocket manager...")
    stop_server()
    log_info("WebSocket manager cleaned up.")

# Register cleanup function
atexit.register(cleanup)

# Initialize the module
initialize()
