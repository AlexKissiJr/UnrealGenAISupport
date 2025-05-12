# WebSocket Setup Guide

This guide provides instructions for setting up and testing the WebSocket functionality in the UnrealGenAISupport plugin.

## Prerequisites

The WebSocket functionality requires the Python `websockets` module to be installed in your Unreal Engine's Python environment. Follow these steps to install it:

### Step 1: Install the WebSockets Module

1. Open your Unreal Engine project
2. Open the Python Console (Window > Developer Tools > Python Console)
3. Run the following command:
   ```python
   import install_websockets
   install_websockets.install_websockets()
   ```
4. If the installation is successful, you'll see a message saying "✅ websockets module is ready to use."
5. If the installation fails, you'll need to install it manually:
   - Open a command prompt or terminal
   - Navigate to your Unreal Engine Python directory
   - Run: `python -m pip install websockets`
   - Restart Unreal Engine

### Step 2: Check WebSocket Server

1. After installing the `websockets` module, check if the WebSocket server can start:
   ```python
   import check_websocket_server
   check_websocket_server.check_server()
   ```
2. If the check is successful, you'll see a message saying "✅ WebSocket server is ready to use."
3. If the check fails, review the error messages for troubleshooting.

## Testing the WebSocket Functionality

### Method 1: Using the Python Socket Control Panel

1. Open your Unreal Engine project
2. Open the Python Socket Control Panel from the toolbar
3. Make sure "Use WebSocket" is checked
4. Click "Start Server"
5. Check the Output Log for any error messages

### Method 2: Using the Basic WebSocket Test HTML

1. Start the WebSocket server using Method 1
2. Open `Resources/BasicWebSocketTest.html` in a web browser
3. Click "Connect" to connect to the WebSocket server
4. If the connection is successful, the status will change to "Connected"
5. Click "Send Handshake" to test the handshake functionality
6. Check the log for the responses

## Troubleshooting

### Common Issues

#### "No module named 'websockets'"

This error means the `websockets` module is not installed. Follow the installation steps above.

#### "Address already in use"

This error means the port (9877) is already in use. Make sure you don't have another instance of the WebSocket server running.

#### "Connection refused"

This error means the WebSocket server is not running or is not accessible. Make sure the server is started and the port is not blocked by a firewall.

### Checking WebSocket Server Status

You can check if the WebSocket server is running by:

1. Opening the Python Console
2. Running:
   ```python
   import websocket_server
   print(websocket_server.is_running)
   ```
3. If it returns `True`, the server is running.

### Restarting the WebSocket Server

If you need to restart the WebSocket server:

1. Open the Python Console
2. Run:
   ```python
   import websocket_server
   websocket_server.stop_server()
   websocket_server.initialize_server()
   ```

## Integration with C++ WebSocket Client

The WebSocket server communicates with the C++ WebSocket client in your plugin. The client is implemented in:

- `GenWebSocketClient.h`
- `GenWebSocketClient.cpp`
- `GenWebSocketManager.h`
- `GenWebSocketManager.cpp`

These files handle the C++ side of the WebSocket communication.

## Next Steps

After verifying that the WebSocket server works:

1. Test the integration with your AI models
2. Test the Blueprint and actor operations
3. Create a custom UI for controlling the WebSocket functionality
4. Develop external applications that use the WebSocket API
