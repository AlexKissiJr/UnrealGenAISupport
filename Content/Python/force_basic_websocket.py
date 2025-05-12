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

def force_basic_websocket():
    """Force the use of the basic WebSocket server"""
    try:
        # Check if the basic WebSocket server is available
        if not has_basic_server:
            unreal.log_error("Basic WebSocket server not available")
            return False
        
        # Check if the websocket_server module is loaded
        if 'websocket_server' in sys.modules:
            # Get the websocket_server module
            websocket_server = sys.modules['websocket_server']
            
            # Override the initialize_server function
            original_initialize = websocket_server.initialize_server
            
            def new_initialize_server():
                unreal.log("🔄 Redirecting to basic WebSocket server...")
                return basic_websocket_server.initialize_server()
            
            # Replace the function
            websocket_server.initialize_server = new_initialize_server
            
            # Override the stop_server function
            original_stop = websocket_server.stop_server
            
            def new_stop_server():
                unreal.log("🔄 Redirecting to basic WebSocket server...")
                return basic_websocket_server.stop_server()
            
            # Replace the function
            websocket_server.stop_server = new_stop_server
            
            unreal.log("✅ Successfully forced the use of the basic WebSocket server")
            return True
        else:
            unreal.log_warning("WebSocket server module not loaded")
            return False
    except Exception as e:
        unreal.log_error(f"Error forcing basic WebSocket server: {str(e)}")
        unreal.log_error(traceback.format_exc())
        return False

# Run the script
if __name__ == "__main__":
    unreal.log("Forcing the use of the basic WebSocket server...")
    success = force_basic_websocket()
    
    if success:
        unreal.log("✅ Successfully forced the use of the basic WebSocket server")
    else:
        unreal.log_error("❌ Failed to force the use of the basic WebSocket server")

# Function to run from Unreal Engine
def force_basic():
    """Force the use of the basic WebSocket server"""
    return force_basic_websocket()
