# WebSocket Manager Guide

This guide provides instructions for using the integrated WebSocket Manager in the UnrealGenAISupport plugin.

## Overview

The WebSocket Manager provides a simplified way to use WebSocket functionality in your Unreal Engine project. It:

1. Automatically handles the WebSocket server setup and management
2. Provides a simple interface for starting and stopping the server
3. Integrates with the Python Socket UI
4. Works seamlessly with the C++ WebSocket client

## Using the WebSocket Manager

### Method 1: Through the Python Socket UI

The WebSocket Manager is integrated with the Python Socket UI:

1. Open the Python Socket Control Panel from the toolbar
2. Make sure "Use WebSocket" is checked
3. Click "Start Server"
4. The WebSocket Manager will automatically start the WebSocket server

### Method 2: Through Python Code

You can also use the WebSocket Manager directly in your Python code:

```python
import websocket_manager

# Start the WebSocket server
websocket_manager.start_server()

# Check if the server is running
is_running = websocket_manager.is_server_running()

# Get the server URL
server_url = websocket_manager.get_server_url()

# Stop the server
websocket_manager.stop_server()
```

### Method 3: Through C++ Code

You can use the WebSocket Manager with the C++ WebSocket client:

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

### Automatic Server Management

The WebSocket Manager automatically:

1. Starts the WebSocket server when needed
2. Monitors the server process
3. Restarts the server if it crashes
4. Cleans up the server when Unreal Engine exits

### External Server Support

You can also use an external WebSocket server:

```python
import websocket_manager

# Use an external server
websocket_manager.set_use_external_server(True, "ws://example.com:8080")
```

### Auto-Restart

By default, the WebSocket Manager will automatically restart the server if it crashes. You can disable this:

```python
import websocket_manager

# Disable auto-restart
websocket_manager.set_auto_restart(False)
```

## Testing the WebSocket Manager

You can test the WebSocket Manager using the provided test script:

```python
import test_websocket_manager
test_websocket_manager.run_test()
```

This will:

1. Start the WebSocket server
2. Create a WebSocket client
3. Connect to the server
4. Send a handshake
5. Disconnect
6. Stop the server

## Troubleshooting

### Common Issues

#### "Error starting WebSocket server process"

This error can occur if:
- The WebSocket server script is not found
- The Python executable is not accessible
- There's a permission issue

#### "WebSocket server process has stopped"

This error occurs when the server process crashes. The WebSocket Manager will automatically restart it if auto-restart is enabled.

#### "websockets module not found"

This error occurs when the `websockets` module is not installed. The WebSocket Manager will attempt to install it automatically.

## Integration with C++ WebSocket Client

The WebSocket Manager works seamlessly with the C++ WebSocket client:

1. The WebSocket Manager starts and manages the server
2. The C++ WebSocket client connects to the server
3. They communicate using the same protocol

This provides a robust and reliable WebSocket implementation for your plugin.
