# WebSocket MCP Server Guide

This guide provides instructions for using the WebSocket version of the MCP server in the UnrealGenAISupport plugin.

## Overview

The WebSocket MCP server is a drop-in replacement for the standard MCP server that:

1. Uses WebSocket protocol instead of TCP
2. Works with the Python Socket UI in Unreal Engine
3. Doesn't require any external Python modules
4. Provides the same functionality as the standard MCP server

## Using the WebSocket MCP Server

### Method 1: Replace the Standard MCP Server

The simplest way to use the WebSocket MCP server is to replace the standard MCP server:

1. Open the Python Console in Unreal Engine (Window > Developer Tools > Python Console)
2. Run the following code:

```python
import replace_mcp_server
replace_mcp_server.replace()
```

3. Then use the Python Socket UI as normal (make sure "Use WebSocket" is checked)

4. To restore the original MCP server:

```python
import replace_mcp_server
replace_mcp_server.restore()
```

### Method 2: Use the Direct WebSocket Start Script

If you don't want to replace the standard MCP server, you can use the direct WebSocket start script:

1. Open the Python Console in Unreal Engine
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

## Features

### Simple and Reliable

The WebSocket MCP server:

1. Uses only built-in Python libraries
2. Handles WebSocket connections according to the protocol
3. Processes messages in a thread-safe manner
4. Provides proper error handling

### Supported Commands

The WebSocket MCP server supports the same commands as the standard MCP server:

1. **Handshake**: Establishes a connection with the server
2. **Execute Python Script**: Executes a Python script in Unreal Engine
3. **Execute Unreal Command**: Executes an Unreal Engine command
4. **Spawn Object**: Spawns an object in the Unreal Engine level
5. **Edit Component Property**: Edits a property of a component
6. **Create Material**: Creates a new material
7. **Create Blueprint**: Creates a new Blueprint
8. **Add Component to Blueprint**: Adds a component to a Blueprint
9. **Add Variable to Blueprint**: Adds a variable to a Blueprint
10. **Add Function to Blueprint**: Adds a function to a Blueprint
11. **Add Node to Blueprint**: Adds a node to a Blueprint graph

## Testing the WebSocket MCP Server

You can test the WebSocket MCP server using the provided HTML test page:

1. Replace the standard MCP server with the WebSocket version
2. Start the server from the Python Socket UI
3. Open `Resources/WebSocketTest.html` in a web browser
4. Click "Connect" to connect to the WebSocket server
5. Click "Send Handshake" to send a handshake message
6. Check the logs for the response

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

The WebSocket MCP server works seamlessly with the C++ WebSocket client:

1. The WebSocket MCP server handles the server-side
2. The C++ WebSocket client connects to the server
3. They communicate using the same protocol

This provides a robust and reliable WebSocket implementation for your plugin.
