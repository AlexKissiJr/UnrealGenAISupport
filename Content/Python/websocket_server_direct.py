import unreal
import sys
import os
import importlib.util
import traceback

# Try to import the basic_websocket_server module
try:
    import basic_websocket_server
    has_basic_server = True
except ImportError:
    has_basic_server = False
    unreal.log_error("Failed to import basic_websocket_server module")

# Global variables
server_instance = None

def initialize_server():
    """Initialize the WebSocket server"""
    global server_instance
    
    try:
        unreal.log("🟢 Initializing direct WebSocket server...")
        
        # Stop any existing server
        stop_server()
        
        if has_basic_server:
            # Start the basic WebSocket server
            success = basic_websocket_server.initialize_server()
            
            if success:
                server_instance = True
                unreal.log("✅ Direct WebSocket server initialized successfully")
                return True
            else:
                unreal.log_error("❌ Direct WebSocket server failed to start")
                return False
        else:
            unreal.log_error("❌ basic_websocket_server module not available")
            return False
    except Exception as e:
        unreal.log_error(f"Error initializing direct WebSocket server: {str(e)}")
        unreal.log_error(traceback.format_exc())
        return False

def stop_server():
    """Stop the WebSocket server"""
    global server_instance
    
    try:
        if has_basic_server and basic_websocket_server.is_running:
            unreal.log("Stopping direct WebSocket server...")
            success = basic_websocket_server.stop_server()
            
            if success:
                server_instance = None
                unreal.log("✅ Direct WebSocket server stopped successfully")
                return True
            else:
                unreal.log_error("❌ Direct WebSocket server failed to stop")
                return False
        else:
            unreal.log("No direct WebSocket server to stop")
            server_instance = None
            return True
    except Exception as e:
        unreal.log_error(f"Error stopping direct WebSocket server: {str(e)}")
        unreal.log_error(traceback.format_exc())
        server_instance = None
        return False

def is_server_running():
    """Check if the WebSocket server is running"""
    try:
        if has_basic_server:
            return basic_websocket_server.is_running
        else:
            return False
    except Exception as e:
        unreal.log_error(f"Error checking if direct WebSocket server is running: {str(e)}")
        unreal.log_error(traceback.format_exc())
        return False
