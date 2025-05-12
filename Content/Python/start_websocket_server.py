import unreal
import sys
import os
from importlib import reload

# Get the plugin's Content/Python path
plugin_content_path = unreal.Paths.project_plugins_dir() + "/UnrealGenAISupport/Content"
python_path = os.path.join(plugin_content_path, "Python")
sys.path.append(python_path)

try:
    # Try to import websockets
    try:
        import websockets
    except ImportError:
        print("WebSockets module not found. Installing...")
        import pip
        pip.main(['install', 'websockets'])
        import websockets
        print("WebSockets module installed successfully")
    
    # Import and reload our WebSocket server module
    import websocket_server
    reload(websocket_server)
    
    # Initialize the WebSocket server
    websocket_server.initialize_server()
    print("WebSocket server started successfully on port 9877")
    
except Exception as e:
    print(f"Error starting WebSocket server: {str(e)}")
    raise
