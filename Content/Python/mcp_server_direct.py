import socket
import json
import sys
import os
import time
from pathlib import Path

# Create a PID file to let the Unreal plugin know this process is running
def write_pid_file():
    try:
        pid = os.getpid()
        pid_dir = os.path.join(os.path.expanduser("~"), ".unrealgenai")
        os.makedirs(pid_dir, exist_ok=True)
        pid_path = os.path.join(pid_dir, "mcp_server.pid")

        with open(pid_path, "w") as f:
            f.write(f"{pid}\n9877")  # Store PID and port

        # Register to delete the PID file on exit
        import atexit
        def cleanup_pid_file():
            try:
                if os.path.exists(pid_path):
                    os.remove(pid_path)
            except:
                pass

        atexit.register(cleanup_pid_file)

        return pid_path
    except Exception as e:
        print(f"Failed to write PID file: {e}", file=sys.stderr)
        return None

# Write PID file on startup
pid_file = write_pid_file()
if pid_file:
    print(f"WebSocket Server started with PID file at: {pid_file}", file=sys.stderr)

# Import the basic_websocket_server module from the plugin's Python directory
def import_basic_websocket_server():
    try:
        # Get the current directory (where this script is located)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Add the current directory to the Python path
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)
        
        # Import the basic_websocket_server module
        import basic_websocket_server
        return basic_websocket_server
    except ImportError:
        print("Failed to import basic_websocket_server module", file=sys.stderr)
        return None
    except Exception as e:
        print(f"Error importing basic_websocket_server module: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return None

# Start the server
def start_server():
    """Start the WebSocket server"""
    try:
        print("🟢 Starting WebSocket server...", file=sys.stderr)
        
        # Import the basic_websocket_server module
        basic_websocket_server = import_basic_websocket_server()
        if not basic_websocket_server:
            print("❌ Failed to import basic_websocket_server module", file=sys.stderr)
            return False
        
        # Start the server
        success = basic_websocket_server.initialize_server()
        
        if success:
            print("✅ WebSocket server started successfully", file=sys.stderr)
            return True
        else:
            print("❌ WebSocket server failed to start", file=sys.stderr)
            return False
    except Exception as e:
        print(f"Error starting WebSocket server: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return False

# Stop the server
def stop_server():
    """Stop the WebSocket server"""
    try:
        print("Stopping WebSocket server...", file=sys.stderr)
        
        # Import the basic_websocket_server module
        basic_websocket_server = import_basic_websocket_server()
        if not basic_websocket_server:
            print("❌ Failed to import basic_websocket_server module", file=sys.stderr)
            return False
        
        # Stop the server
        success = basic_websocket_server.stop_server()
        
        if success:
            print("✅ WebSocket server stopped successfully", file=sys.stderr)
            return True
        else:
            print("❌ WebSocket server failed to stop", file=sys.stderr)
            return False
    except Exception as e:
        print(f"Error stopping WebSocket server: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return False

# Check if the server is running
def is_server_running():
    """Check if the WebSocket server is running"""
    try:
        # Import the basic_websocket_server module
        basic_websocket_server = import_basic_websocket_server()
        if not basic_websocket_server:
            print("❌ Failed to import basic_websocket_server module", file=sys.stderr)
            return False
        
        # Check if the server is running
        return basic_websocket_server.is_running
    except Exception as e:
        print(f"Error checking if WebSocket server is running: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return False

# Start the server when this script is run
if __name__ == "__main__":
    start_server()
    
    # Keep the script running
    try:
        while is_server_running():
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping WebSocket server...", file=sys.stderr)
        stop_server()
