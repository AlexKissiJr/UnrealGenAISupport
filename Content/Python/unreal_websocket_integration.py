"""
Unreal Engine integration for WebSocket server.
This module provides functions to start and stop the WebSocket server from Unreal Engine.
"""

import sys
import os
import time
import threading
import traceback

# Try to import Unreal Engine module
try:
    import unreal
    has_unreal = True
except ImportError:
    has_unreal = False

# Global variables
server_thread = None
is_running = False
server_module = None

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

# Server thread function
def server_thread_function():
    """Server thread function"""
    global is_running, server_module
    
    try:
        log_info("Starting WebSocket server in Unreal Engine...")
        
        # Import the server module
        import mcp_server_refactored
        server_module = mcp_server_refactored
        
        # Start the server
        server_module.main()
        
        log_info("WebSocket server thread exited")
    except Exception as e:
        log_error(f"Error in WebSocket server thread: {str(e)}", include_traceback=True)
    finally:
        is_running = False

# Start the server
def start_server():
    """Start the WebSocket server"""
    global server_thread, is_running
    
    try:
        # Check if server is already running
        if is_running and server_thread and server_thread.is_alive():
            log_warning("WebSocket server is already running")
            return True
            
        # Reset running flag
        is_running = True
        
        # Start the server thread
        server_thread = threading.Thread(
            target=server_thread_function,
            daemon=True,
            name="UnrealWebSocketServerThread"
        )
        server_thread.start()
        
        # Wait for the server to start (up to 5 seconds)
        start_time = time.time()
        while server_thread.is_alive() and time.time() - start_time < 5:
            time.sleep(0.1)
        
        if server_thread.is_alive():
            log_info("✅ WebSocket server started successfully")
            return True
        else:
            log_error("❌ WebSocket server failed to start")
            is_running = False
            return False
    except Exception as e:
        log_error(f"Error starting WebSocket server: {str(e)}", include_traceback=True)
        is_running = False
        return False

# Stop the server
def stop_server():
    """Stop the WebSocket server"""
    global server_thread, is_running, server_module
    
    try:
        # Check if server is already stopped
        if not is_running and (server_thread is None or not server_thread.is_alive()):
            log_warning("WebSocket server is already stopped")
            return True
        
        # Set running flag to False
        is_running = False
        
        # Stop the server
        if server_module:
            try:
                server_module.stop_server()
            except Exception as e:
                log_error(f"Error stopping WebSocket server: {str(e)}")
        
        # Wait for server thread to exit
        if server_thread and server_thread.is_alive():
            log_info("Waiting for server thread to exit...")
            start_time = time.time()
            while server_thread.is_alive() and time.time() - start_time < 5:
                time.sleep(0.1)
                
            if server_thread.is_alive():
                log_warning("Server thread did not exit within timeout")
            else:
                log_info("Server thread exited")
            
        server_thread = None
        
        log_info("WebSocket server stopped")
        return True
    except Exception as e:
        log_error(f"Error stopping WebSocket server: {str(e)}", include_traceback=True)
        return False

# Check if server is running
def is_server_running():
    """Check if the WebSocket server is running"""
    global server_thread, is_running
    
    return is_running and server_thread and server_thread.is_alive()

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
    if is_server_running():
        return "WebSocket server is running"
    else:
        return "WebSocket server is not running"
