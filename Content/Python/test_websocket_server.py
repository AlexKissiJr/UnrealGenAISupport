import unreal
import sys
import os
import json
import time

# Get the plugin's Content/Python path
plugin_content_path = unreal.Paths.project_plugins_dir() + "/UnrealGenAISupport/Content"
python_path = os.path.join(plugin_content_path, "Python")
sys.path.append(python_path)

def log_info(message):
    """Log info message"""
    unreal.log(f"[WebSocket Test] {message}")

def log_error(message):
    """Log error message"""
    unreal.log_error(f"[WebSocket Test] {message}")

def test_websocket_server():
    """Test if the WebSocket server is working properly"""
    try:
        # Import the websocket_server module
        import websocket_server
        log_info("Successfully imported websocket_server module")

        # Check if the server is already running
        if hasattr(websocket_server, 'server_instance') and websocket_server.server_instance:
            log_info("WebSocket server is already running")
            return True

        # Initialize the server
        log_info("Initializing WebSocket server...")
        success = websocket_server.initialize_server()

        if success:
            log_info("✅ WebSocket server initialized successfully")

            # Wait a moment for the server to start
            time.sleep(1)

            # Check if the server is running
            if hasattr(websocket_server, 'server_instance') and websocket_server.server_instance:
                log_info("✅ WebSocket server is running")
                return True
            else:
                log_error("❌ WebSocket server failed to start")
                return False
        else:
            log_error("❌ WebSocket server initialization failed")
            return False

    except ImportError as e:
        log_error(f"Failed to import websocket_server module: {str(e)}")
        return False
    except Exception as e:
        log_error(f"Error testing WebSocket server: {str(e)}")
        import traceback
        log_error(traceback.format_exc())
        return False

def test_websocket_handshake():
    """Test the WebSocket handshake functionality"""
    try:
        # Import the websockets module
        try:
            import websockets
        except ImportError:
            log_error("websockets module not found. Cannot test handshake.")
            return False

        import asyncio

        # Define the handshake test
        async def test_handshake():
            try:
                # Connect to the WebSocket server
                uri = "ws://localhost:9877"
                log_info(f"Connecting to {uri}...")

                async with websockets.connect(uri) as websocket:
                    # Send a handshake message
                    handshake_message = {
                        "type": "handshake",
                        "message": "Hello from test script"
                    }

                    log_info(f"Sending handshake message: {handshake_message}")
                    await websocket.send(json.dumps(handshake_message) + '\n')

                    # Wait for the response
                    log_info("Waiting for response...")
                    response = await websocket.recv()

                    # Parse the response
                    if response.endswith('\n'):
                        response = response[:-1]  # Remove trailing newline

                    response_json = json.loads(response)
                    log_info(f"Received response: {response_json}")

                    # Check if the handshake was successful
                    if response_json.get("success", False):
                        log_info("✅ Handshake successful")
                        return True
                    else:
                        log_error(f"❌ Handshake failed: {response_json.get('error', 'Unknown error')}")
                        return False

            except Exception as e:
                log_error(f"Error during handshake test: {str(e)}")
                import traceback
                log_error(traceback.format_exc())
                return False

        # Run the handshake test
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(test_handshake())
        loop.close()

        return result

    except Exception as e:
        log_error(f"Error testing WebSocket handshake: {str(e)}")
        import traceback
        log_error(traceback.format_exc())
        return False

# Run the tests
if __name__ == "__main__":
    log_info("Starting WebSocket server test...")

    # Test the WebSocket server
    server_result = test_websocket_server()

    if server_result:
        # Test the WebSocket handshake
        handshake_result = test_websocket_handshake()

        if handshake_result:
            log_info("✅ All tests passed! WebSocket server is working properly.")
        else:
            log_error("❌ Handshake test failed. WebSocket server may not be working properly.")
    else:
        log_error("❌ Server test failed. Cannot proceed with handshake test.")

# Function to run from Unreal Engine
def run_test():
    """Run the WebSocket server test"""
    log_info("Starting WebSocket server test...")

    # Test the WebSocket server
    server_result = test_websocket_server()

    if server_result:
        log_info("✅ WebSocket server is running properly.")
        return True
    else:
        log_error("❌ WebSocket server test failed.")
        return False
