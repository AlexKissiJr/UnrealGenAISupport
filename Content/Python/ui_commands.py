import unreal
import sys
import os
import importlib.util

# Try to import the websocket_server module
try:
    import websocket_server
    has_websocket_server = True
except ImportError:
    has_websocket_server = False

# Try to import the standalone_websocket_server module
try:
    import standalone_websocket_server
    has_standalone_server = True
except ImportError:
    has_standalone_server = False

# Try to import the simple_websocket_server module
try:
    import simple_websocket_server
    has_simple_server = True
except ImportError:
    has_simple_server = False

# Try to import the websocket_manager module
try:
    import websocket_manager
    has_websocket_manager = True
except ImportError:
    has_websocket_manager = False

def start_socket_server(use_websocket=False):
    """Start the Python socket server"""
    try:
        if use_websocket:
            # Try to use the simple WebSocket server first
            if has_simple_server:
                unreal.log("Starting simple WebSocket server...")
                return simple_websocket_server.initialize_server()
            # Try to use the standalone WebSocket server next
            elif has_standalone_server:
                unreal.log("Starting standalone WebSocket server...")
                return standalone_websocket_server.initialize_server()
            # Try to use the WebSocket manager if available
            elif has_websocket_manager:
                unreal.log("Starting WebSocket server using websocket_manager...")
                return websocket_manager.start_server()
            # Fall back to the old WebSocket server if available
            elif has_websocket_server:
                unreal.log("Starting WebSocket server using websocket_server...")
                return websocket_server.initialize_server()
            else:
                unreal.log_error("WebSocket server modules not available")
                return False
        else:
            # Start TCP socket server
            import mcp_server
            return mcp_server.start_server()
    except Exception as e:
        unreal.log_error(f"Error starting Python socket server: {str(e)}")
        import traceback
        unreal.log_error(traceback.format_exc())
        return False

def stop_socket_server(use_websocket=False):
    """Stop the Python socket server"""
    try:
        if use_websocket:
            # Try to use the simple WebSocket server first
            if has_simple_server:
                unreal.log("Stopping simple WebSocket server...")
                return simple_websocket_server.stop_server()
            # Try to use the standalone WebSocket server next
            elif has_standalone_server:
                unreal.log("Stopping standalone WebSocket server...")
                return standalone_websocket_server.stop_server()
            # Try to use the WebSocket manager if available
            elif has_websocket_manager:
                unreal.log("Stopping WebSocket server using websocket_manager...")
                return websocket_manager.stop_server()
            # Fall back to the old WebSocket server if available
            elif has_websocket_server:
                unreal.log("Stopping WebSocket server using websocket_server...")
                return websocket_server.stop_server()
            else:
                unreal.log_error("WebSocket server modules not available")
                return False
        else:
            # Stop TCP socket server
            import mcp_server
            return mcp_server.stop_server()
    except Exception as e:
        unreal.log_error(f"Error stopping Python socket server: {str(e)}")
        import traceback
        unreal.log_error(traceback.format_exc())
        return False

def is_socket_server_running(use_websocket=False):
    """Check if the Python socket server is running"""
    try:
        if use_websocket:
            # Try to use the simple WebSocket server first
            if has_simple_server:
                return hasattr(simple_websocket_server, 'is_running') and simple_websocket_server.is_running
            # Try to use the standalone WebSocket server next
            elif has_standalone_server:
                return hasattr(standalone_websocket_server, 'is_running') and standalone_websocket_server.is_running
            # Try to use the WebSocket manager if available
            elif has_websocket_manager:
                return websocket_manager.is_server_running()
            # Fall back to the old WebSocket server if available
            elif has_websocket_server:
                return hasattr(websocket_server, 'server_instance') and websocket_server.server_instance is not None
            else:
                return False
        else:
            # Check TCP socket server
            import mcp_server
            return mcp_server.is_server_running()
    except Exception as e:
        unreal.log_error(f"Error checking if Python socket server is running: {str(e)}")
        return False
