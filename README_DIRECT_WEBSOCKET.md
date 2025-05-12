# Direct WebSocket Server Guide

This guide provides instructions for using the direct WebSocket server in the UnrealGenAISupport plugin.

## Overview

The direct WebSocket server provides a simple and reliable WebSocket implementation that:

1. Does not require any external Python modules
2. Works directly with the built-in Python libraries
3. Can be used directly from Python code
4. Works seamlessly with the C++ WebSocket client

## Using the Direct WebSocket Server

### Method 1: Through the Python Console

The simplest way to use the direct WebSocket server is through the Python Console:

1. Open the Python Console in Unreal Engine (Window > Developer Tools > Python Console)
2. Run the following code:

```python
import direct_websocket_start
direct_websocket_start.start()
```

3. To stop the server:

```python
import direct_websocket_start
direct_websocket_start.stop()
```

### Method 2: Force the WebSocket Server to Use the Basic Implementation

If you prefer to use the Python Socket UI, you can force it to use the basic WebSocket server:

1. Open the Python Console in Unreal Engine
2. Run the following code:

```python
import force_basic_websocket
force_basic_websocket.force_basic()
```

3. Then use the Python Socket UI as normal

### Method 3: Through C++ Code

You can use the direct WebSocket server with the C++ WebSocket client:

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

The direct WebSocket server:

1. Uses only built-in Python libraries
2. Handles WebSocket connections according to the protocol
3. Processes messages in a thread-safe manner
4. Provides proper error handling

### Supported Commands

The direct WebSocket server supports the following commands:

1. **Handshake**: Establishes a connection with the server
2. **Ping**: Tests the connection with the server
3. **Echo**: Echoes back any other messages with additional information

## Testing the Direct WebSocket Server

You can test the direct WebSocket server using the provided HTML test page:

1. Start the direct WebSocket server using one of the methods above
2. Open `Resources/WebSocketTest.html` in a web browser
3. Click "Connect" to connect to the WebSocket server
4. Click "Send Handshake" to send a handshake message
5. Check the logs for the response

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

The direct WebSocket server works seamlessly with the C++ WebSocket client:

1. The direct WebSocket server handles the server-side
2. The C++ WebSocket client connects to the server
3. They communicate using the same protocol

This provides a robust and reliable WebSocket implementation for your plugin.
