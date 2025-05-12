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

# Try to import the simple_websocket_server module
try:
    import simple_websocket_server
    has_simple_server = True
except ImportError:
    has_simple_server = False

# Try to import the standalone_websocket_server module
try:
    import standalone_websocket_server
    has_standalone_server = True
except ImportError:
    has_standalone_server = False

# Try to import the websocket_server module
try:
    import websocket_server
    has_websocket_server = True
except ImportError:
    has_websocket_server = False

# Try to import the websocket_manager module
try:
    import websocket_manager
    has_websocket_manager = True
except ImportError:
    has_websocket_manager = False

# Global variables
current_server_type = None
is_websocket = False

def start_server(use_websocket=False):
    """Start the server"""
    global current_server_type, is_websocket
    
    try:
        is_websocket = use_websocket
        
        if use_websocket:
            # Try to use the basic WebSocket server first (most reliable)
            if has_basic_server:
                unreal.log("Starting basic WebSocket server...")
                success = basic_websocket_server.initialize_server()
                if success:
                    current_server_type = "basic"
                    return True
                else:
                    unreal.log_warning("Failed to start basic WebSocket server, trying alternatives...")
            
            # Try to use the simple WebSocket server next
            if has_simple_server:
                unreal.log("Starting simple WebSocket server...")
                success = simple_websocket_server.initialize_server()
                if success:
                    current_server_type = "simple"
                    return True
                else:
                    unreal.log_warning("Failed to start simple WebSocket server, trying alternatives...")
            
            # Try to use the standalone WebSocket server next
            if has_standalone_server:
                unreal.log("Starting standalone WebSocket server...")
                success = standalone_websocket_server.initialize_server()
                if success:
                    current_server_type = "standalone"
                    return True
                else:
                    unreal.log_warning("Failed to start standalone WebSocket server, trying alternatives...")
            
            # Try to use the WebSocket manager if available
            if has_websocket_manager:
                unreal.log("Starting WebSocket server using websocket_manager...")
                success = websocket_manager.start_server()
                if success:
                    current_server_type = "manager"
                    return True
                else:
                    unreal.log_warning("Failed to start WebSocket manager, trying alternatives...")
            
            # Fall back to the old WebSocket server if available
            if has_websocket_server:
                unreal.log("Starting WebSocket server using websocket_server...")
                success = websocket_server.initialize_server()
                if success:
                    current_server_type = "websocket"
                    return True
                else:
                    unreal.log_warning("Failed to start WebSocket server")
            
            unreal.log_error("All WebSocket server implementations failed to start")
            current_server_type = None
            return False
        else:
            # Start TCP socket server
            import mcp_server
            success = mcp_server.start_server()
            if success:
                current_server_type = "mcp"
                return True
            else:
                unreal.log_warning("Failed to start MCP server")
                current_server_type = None
                return False
    except Exception as e:
        unreal.log_error(f"Error starting server: {str(e)}")
        unreal.log_error(traceback.format_exc())
        current_server_type = None
        return False

def stop_server():
    """Stop the server"""
    global current_server_type, is_websocket
    
    try:
        if current_server_type == "basic":
            unreal.log("Stopping basic WebSocket server...")
            return basic_websocket_server.stop_server()
        elif current_server_type == "simple":
            unreal.log("Stopping simple WebSocket server...")
            return simple_websocket_server.stop_server()
        elif current_server_type == "standalone":
            unreal.log("Stopping standalone WebSocket server...")
            return standalone_websocket_server.stop_server()
        elif current_server_type == "manager":
            unreal.log("Stopping WebSocket server using websocket_manager...")
            return websocket_manager.stop_server()
        elif current_server_type == "websocket":
            unreal.log("Stopping WebSocket server using websocket_server...")
            return websocket_server.stop_server()
        elif current_server_type == "mcp":
            unreal.log("Stopping MCP server...")
            import mcp_server
            return mcp_server.stop_server()
        else:
            unreal.log_warning("No server to stop")
            return True
    except Exception as e:
        unreal.log_error(f"Error stopping server: {str(e)}")
        unreal.log_error(traceback.format_exc())
        return False
    finally:
        current_server_type = None

def is_server_running():
    """Check if the server is running"""
    global current_server_type, is_websocket
    
    try:
        if current_server_type == "basic":
            return hasattr(basic_websocket_server, 'is_running') and basic_websocket_server.is_running
        elif current_server_type == "simple":
            return hasattr(simple_websocket_server, 'is_running') and simple_websocket_server.is_running
        elif current_server_type == "standalone":
            return hasattr(standalone_websocket_server, 'is_running') and standalone_websocket_server.is_running
        elif current_server_type == "manager":
            return websocket_manager.is_server_running()
        elif current_server_type == "websocket":
            return hasattr(websocket_server, 'server_instance') and websocket_server.server_instance is not None
        elif current_server_type == "mcp":
            import mcp_server
            return mcp_server.is_server_running()
        else:
            return False
    except Exception as e:
        unreal.log_error(f"Error checking if server is running: {str(e)}")
        unreal.log_error(traceback.format_exc())
        return False

def get_server_url():
    """Get the server URL"""
    global current_server_type, is_websocket
    
    if is_websocket:
        return "ws://localhost:9877"
    else:
        return "localhost:8888"

def get_server_type():
    """Get the current server type"""
    global current_server_type
    return current_server_type
