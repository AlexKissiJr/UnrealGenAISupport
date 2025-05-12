# C++ WebSocket Client Testing Guide

This guide provides instructions for testing the C++ WebSocket client implementation in the UnrealGenAISupport plugin.

## Overview

The plugin includes a C++ WebSocket client implementation that uses Unreal Engine's built-in WebSocket module. This implementation is based on the approach described in the [Unreal Community Wiki](https://unrealcommunity.wiki/websocket-client-cpp-5vk7hp9e).

## Testing the C++ WebSocket Client

### Method 1: Using the Echo Server

1. **Start the Echo Server**:
   - Open a command prompt or terminal
   - Navigate to the `Resources` directory
   - Run: `python websocket_echo_server.py`
   - You should see a message saying "WebSocket echo server running at ws://localhost:9877"

2. **Create the Test Blueprint**:
   - Open your Unreal Engine project
   - Open the Python Console (Window > Developer Tools > Python Console)
   - Run:
     ```python
     import create_websocket_test_bp
     create_websocket_test_bp.create_blueprint()
     ```
   - This will create and open a Blueprint named `BP_WebSocketTest`

3. **Set Up the Blueprint**:
   - In the Blueprint editor, go to the Event Graph
   - Add the following nodes:
     - **Event Begin Play**
     - **Create Object** (Class: GenWebSocketClient)
     - **Set WebSocketClient** (connect to the variable)
     - **Connect** (on the WebSocketClient reference, use the ServerURL variable)
   - Add event handlers for the WebSocket events:
     - **OnConnected**
     - **OnMessage**
     - **OnClosed**
     - **OnError**
   - Add a custom event called **SendHandshake** with the following logic:
     ```
     If WebSocketClient Is Connected
        Call SendJsonCommand on WebSocketClient with "handshake" and "Hello from Unreal Engine"
     ```

4. **Test the Blueprint**:
   - Place the Blueprint in your level
   - Start the game
   - The WebSocket client should connect to the echo server
   - Call the SendHandshake event (e.g., through the console or a UI button)
   - Check the Output Log for the response from the server

### Method 2: Using the Python WebSocket Server

If you have the `websockets` module installed, you can also test with the Python WebSocket server:

1. **Start the Python WebSocket Server**:
   - Open the Python Socket Control Panel from the toolbar
   - Make sure "Use WebSocket" is checked
   - Click "Start Server"

2. **Test with the Blueprint** as described in Method 1.

## Troubleshooting

### Common Issues

#### "WebSocket connection error"

This error can occur if:
- The WebSocket server is not running
- The server URL is incorrect
- There's a firewall blocking the connection

#### "WebSocket not connected"

This error occurs when trying to send a message before the connection is established. Make sure to:
- Check if the connection is successful before sending messages
- Use the OnConnected event to trigger actions after the connection is established

#### "Failed to create WebSocket"

This error can occur if:
- The WebSocketsModule is not properly initialized
- The URL format is invalid

## C++ WebSocket Client Implementation

The C++ WebSocket client is implemented in:

- `GenWebSocketClient.h`
- `GenWebSocketClient.cpp`

Key features of the implementation:

1. **Thread Safety**: Messages are queued and processed on the game thread
2. **Event Handling**: Events for connection, messages, errors, and disconnection
3. **JSON Support**: Helper methods for sending JSON commands
4. **Blueprint Support**: Full Blueprint integration

## Next Steps

After verifying that the C++ WebSocket client works:

1. Test the integration with your AI models
2. Test the Blueprint and actor operations
3. Create a custom UI for controlling the WebSocket functionality
4. Develop external applications that use the WebSocket API
