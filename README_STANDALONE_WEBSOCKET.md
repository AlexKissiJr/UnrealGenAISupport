# Standalone WebSocket Server Guide

This guide provides instructions for using the standalone WebSocket server in the UnrealGenAISupport plugin.

## Overview

The standalone WebSocket server provides a simple and reliable WebSocket implementation that:

1. Does not require any external Python modules
2. Works directly with the built-in Python libraries
3. Integrates with the Python Socket UI
4. Works seamlessly with the C++ WebSocket client

## Using the Standalone WebSocket Server

### Method 1: Through the Python Socket UI

The standalone WebSocket server is integrated with the Python Socket UI:

1. Open the Python Socket Control Panel from the toolbar
2. Make sure "Use WebSocket" is checked
3. Click "Start Server"
4. The standalone WebSocket server will automatically start

### Method 2: Through Python Code

You can also use the standalone WebSocket server directly in your Python code:

```python
import standalone_websocket_server

# Start the WebSocket server
standalone_websocket_server.initialize_server()

# Check if the server is running
is_running = standalone_websocket_server.is_running

# Stop the server
standalone_websocket_server.stop_server()
```

### Method 3: Through C++ Code

You can use the standalone WebSocket server with the C++ WebSocket client:

```cpp
// Create a WebSocket manager
UGenWebSocketManager* WebSocketManager = NewObject<UGenWebSocketManager>();

// Initialize the manager (it will connect to the WebSocket server)
WebSocketManager->Initialize("ws://localhost:9877");

// Send a handshake
WebSocketManager->SendHandshake("Hello from C++");

// Shutdown when done
WebSocketManager->Shutdown();
```

## Features

### Simple and Reliable

The standalone WebSocket server:

1. Uses only built-in Python libraries
2. Handles WebSocket connections according to the protocol
3. Processes messages in a thread-safe manner
4. Provides proper error handling

### Supported Commands

The standalone WebSocket server supports the following commands:

1. **Handshake**: Establishes a connection with the server
2. **Ping**: Tests the connection with the server
3. **Echo**: Echoes back any other messages with additional information

## Testing the Standalone WebSocket Server

You can test the standalone WebSocket server using the provided test script:

```python
import test_standalone_websocket
test_standalone_websocket.run_test()
```

This will:

1. Start the standalone WebSocket server
2. Create a WebSocket client
3. Connect to the server
4. Send a handshake
5. Disconnect
6. Stop the server

## Troubleshooting

### Common Issues

#### "Error in server thread"

This error can occur if:
- The port (9877) is already in use
- There's a permission issue with the socket

#### "WebSocket client failed to connect"

This error occurs when the client cannot connect to the server. Make sure:
- The server is running
- The port is not blocked by a firewall
- The URL is correct

#### "Error handling client"

This error occurs when there's an issue processing a client message. Check:
- The message format
- The WebSocket protocol implementation

## Integration with C++ WebSocket Client

The standalone WebSocket server works seamlessly with the C++ WebSocket client:

1. The standalone WebSocket server handles the server-side
2. The C++ WebSocket client connects to the server
3. They communicate using the same protocol

This provides a robust and reliable WebSocket implementation for your plugin.
