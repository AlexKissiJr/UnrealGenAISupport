import unreal
import sys
import os
import traceback

def start_direct_websocket():
    """Start the basic WebSocket server directly"""
    try:
        # Import the basic WebSocket server
        try:
            import basic_websocket_server
        except ImportError:
            unreal.log_error("Failed to import basic_websocket_server module")
            return False
        
        unreal.log("Successfully imported basic_websocket_server module")
        
        # Check if the server is already running
        if basic_websocket_server.is_running:
            unreal.log("Basic WebSocket server is already running")
            return True
        
        # Stop any existing server
        try:
            basic_websocket_server.stop_server()
        except:
            pass
        
        # Start the server
        unreal.log("Starting basic WebSocket server directly...")
        success = basic_websocket_server.initialize_server()
        
        if success:
            unreal.log("✅ Basic WebSocket server started successfully")
            return True
        else:
            unreal.log_error("❌ Basic WebSocket server failed to start")
            return False
    except Exception as e:
        unreal.log_error(f"Error starting basic WebSocket server: {str(e)}")
        unreal.log_error(traceback.format_exc())
        return False

def stop_direct_websocket():
    """Stop the basic WebSocket server directly"""
    try:
        # Import the basic WebSocket server
        try:
            import basic_websocket_server
        except ImportError:
            unreal.log_error("Failed to import basic_websocket_server module")
            return False
        
        # Check if the server is running
        if not basic_websocket_server.is_running:
            unreal.log("Basic WebSocket server is not running")
            return True
        
        # Stop the server
        unreal.log("Stopping basic WebSocket server directly...")
        success = basic_websocket_server.stop_server()
        
        if success:
            unreal.log("✅ Basic WebSocket server stopped successfully")
            return True
        else:
            unreal.log_error("❌ Basic WebSocket server failed to stop")
            return False
    except Exception as e:
        unreal.log_error(f"Error stopping basic WebSocket server: {str(e)}")
        unreal.log_error(traceback.format_exc())
        return False

# Run the script
if __name__ == "__main__":
    unreal.log("Starting basic WebSocket server directly...")
    success = start_direct_websocket()
    
    if success:
        unreal.log("✅ Basic WebSocket server started successfully")
    else:
        unreal.log_error("❌ Basic WebSocket server failed to start")

# Functions to run from Unreal Engine
def start():
    """Start the basic WebSocket server directly"""
    return start_direct_websocket()

def stop():
    """Stop the basic WebSocket server directly"""
    return stop_direct_websocket()
