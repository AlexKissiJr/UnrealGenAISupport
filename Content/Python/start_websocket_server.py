import unreal
import sys
import os
import traceback
from importlib import reload

# Get the plugin's Content/Python path
plugin_content_path = unreal.Paths.project_plugins_dir() + "/UnrealGenAISupport/Content"
python_path = os.path.join(plugin_content_path, "Python")
sys.path.append(python_path)

def start_server():
    """Start the WebSocket server with error handling"""
    try:
        # Try to import websockets
        try:
            import websockets
        except ImportError:
            print("WebSockets module not found. Installing...")
            try:
                import pip
                pip.main(['install', 'websockets'])
                import websockets
                print("WebSockets module installed successfully")
            except Exception as pip_error:
                print(f"Failed to install websockets: {str(pip_error)}")
                print("Please install manually with: pip install websockets")
                return False

        # Import and reload our WebSocket server module
        import websocket_server
        reload(websocket_server)

        # Initialize the WebSocket server
        success = websocket_server.initialize_server()
        if success:
            print("WebSocket server started successfully on port 9877")
            return True
        else:
            print("WebSocket server failed to start")
            return False

    except Exception as e:
        print(f"Error starting WebSocket server: {str(e)}")
        print(traceback.format_exc())
        return False

# Start the server when this script is run
if __name__ == "__main__" or True:  # Always execute when imported in Unreal
    start_server()
