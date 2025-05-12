import unreal
import sys
import os
import importlib.util

def log_info(message):
    """Log info message"""
    unreal.log(f"[WebSocket Check] {message}")

def log_warning(message):
    """Log warning message"""
    unreal.log_warning(f"[WebSocket Check] {message}")

def log_error(message):
    """Log error message"""
    unreal.log_error(f"[WebSocket Check] {message}")

def check_module_installed(module_name):
    """Check if a Python module is installed"""
    try:
        spec = importlib.util.find_spec(module_name)
        return spec is not None
    except ModuleNotFoundError:
        return False

def check_websocket_server():
    """Check if the WebSocket server can start"""
    log_info("Checking WebSocket server prerequisites...")
    
    # Check if websockets module is installed
    if not check_module_installed("websockets"):
        log_error("websockets module is not installed.")
        log_info("Please run the install_websockets.py script to install it.")
        return False
    
    # Try to import the websocket_server module
    try:
        import websocket_server
        log_info("Successfully imported websocket_server module.")
        
        # Check if the server is already running
        if hasattr(websocket_server, 'server_instance') and websocket_server.server_instance:
            log_info("WebSocket server is already running.")
            return True
        
        # Try to initialize the server
        log_info("Attempting to initialize WebSocket server...")
        
        try:
            success = websocket_server.initialize_server()
            
            if success:
                log_info("✅ WebSocket server initialized successfully.")
                return True
            else:
                log_error("❌ WebSocket server initialization failed.")
                return False
        except Exception as e:
            log_error(f"Error initializing WebSocket server: {str(e)}")
            import traceback
            log_error(traceback.format_exc())
            return False
    except ImportError as e:
        log_error(f"Failed to import websocket_server module: {str(e)}")
        return False
    except Exception as e:
        log_error(f"Error checking WebSocket server: {str(e)}")
        import traceback
        log_error(traceback.format_exc())
        return False

# Run the check
if __name__ == "__main__":
    success = check_websocket_server()
    
    if success:
        log_info("✅ WebSocket server is ready to use.")
    else:
        log_error("❌ WebSocket server is not available.")

# Function to run from Unreal Engine
def check_server():
    """Check if the WebSocket server can start"""
    return check_websocket_server()
