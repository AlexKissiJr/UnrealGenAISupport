# WebSocket Implementation for UnrealGenAISupport

This document describes the WebSocket implementation for the UnrealGenAISupport plugin.

## Overview

The WebSocket implementation provides a robust, thread-safe communication channel between Unreal Engine and external applications. It uses the Python `websockets` library and implements a proper protocol with JSON messages terminated by newlines.

## Key Features

- **Thread-safe command queue**: Uses `queue.Queue()` for safe communication between threads
- **Slate tick callback**: Processes commands on the game thread via `unreal.register_slate_post_tick_callback()`
- **Fixed port**: Listens on `ws://localhost:9877`
- **JSON protocol**: All messages are JSON strings terminated with a newline character (`\n`)
- **Robust error handling**: Comprehensive error handling and logging

## Files

- `Content/Python/websocket_server.py`: Main WebSocket server implementation
- `Content/Python/start_websocket_server.py`: Helper script to start the server
- `Resources/WebSocketTest.html`: Test client for the WebSocket server

## How to Use

### Starting the Server

1. **From the UI**:
   - Open the Python Socket Control Panel from the toolbar
   - Make sure "Use WebSocket" is checked
   - Click "Start Server"

2. **From Python**:
   ```python
   import websocket_server
   websocket_server.initialize_server()
   ```

3. **From an Editor Utility Widget**:
   - Create an Editor Utility Widget
   - Add a "Run Python Command" node with the following code:
   ```python
   import start_websocket_server
   ```

### Testing the Server

1. Open `Resources/WebSocketTest.html` in a web browser
2. Click "Connect" to connect to the WebSocket server
3. Send a handshake message: `{"type": "handshake", "message": "Hello from WebSocket client"}`
4. Check the response in the log

### Protocol

- All messages are JSON objects serialized to strings
- Each message is terminated with a newline character (`\n`)
- Basic message format:
  ```json
  {
    "type": "command_type",
    "message": "Optional message",
    "other_parameters": "..."
  }
  ```

### Command Types

- `handshake`: Initial connection handshake
- Other command types are handled by the existing command dispatcher

## Implementation Details

### Thread Safety

- Commands from clients are placed in a thread-safe queue
- A Slate tick callback processes commands on the game thread
- Responses are protected with a threading lock

### Error Handling

- Comprehensive error handling for all operations
- Detailed logging with clear status indicators
- Automatic timeout for command processing

## Troubleshooting

- If the server doesn't start, check the Output Log for error messages
- Make sure the `websockets` Python package is installed
- Verify that port 9877 is not in use by another application

## Future Improvements

- Add secure WebSocket support (WSS)
- Implement authentication mechanism
- Add support for binary messages
- Create a C++ WebSocket client for better integration
