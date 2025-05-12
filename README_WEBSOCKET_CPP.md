# C++ WebSocket Client for UnrealGenAISupport

This document describes the C++ WebSocket client implementation for the UnrealGenAISupport plugin.

## Overview

The C++ WebSocket client provides a native way to communicate with the Python WebSocket server from C++ code or Blueprints. It uses Unreal Engine's built-in WebSockets module to establish a connection to the server and send/receive messages.

## Key Features

- **Blueprint-friendly**: All functionality is exposed to Blueprints
- **Thread-safe**: Messages are processed on the game thread
- **JSON support**: Helper functions for sending JSON commands
- **Event-based**: Uses delegates for event handling
- **Tickable**: Processes messages on the game thread

## Classes

### UGenWebSocketClient

The main WebSocket client class that handles the connection to the server.

```cpp
UCLASS(BlueprintType, Blueprintable)
class GENERATIVEAISUPPORT_API UGenWebSocketClient : public UObject, public FTickableGameObject
```

#### Key Methods

- `bool Connect(const FString& ServerURL, const FString& Protocol)`: Connect to the WebSocket server
- `void Disconnect()`: Disconnect from the WebSocket server
- `bool SendMessage(const FString& Message)`: Send a raw message to the server
- `bool SendJsonCommand(const FString& Command, const FString& Params)`: Send a JSON command to the server
- `bool IsConnected() const`: Check if the client is connected

#### Events

- `FOnWebSocketConnected OnConnected`: Called when the connection is established or fails
- `FOnWebSocketMessage OnMessage`: Called when a message is received
- `FOnWebSocketClosed OnClosed`: Called when the connection is closed
- `FOnWebSocketError OnError`: Called when an error occurs

### UGenWebSocketManager

A higher-level manager class that provides a simpler interface for common operations.

```cpp
UCLASS(BlueprintType, Blueprintable)
class GENERATIVEAISUPPORT_API UGenWebSocketManager : public UObject
```

#### Key Methods

- `bool Initialize(const FString& ServerURL)`: Initialize the WebSocket manager
- `void Shutdown()`: Shutdown the WebSocket manager
- `bool SendHandshake(const FString& Message)`: Send a handshake message
- `bool ExecutePython(const FString& PythonCode)`: Execute Python code on the server
- `bool IsConnected() const`: Check if the client is connected

## How to Use

### In C++

```cpp
// Create a WebSocket manager
UGenWebSocketManager* WebSocketManager = NewObject<UGenWebSocketManager>();

// Initialize the manager
WebSocketManager->Initialize("ws://localhost:9877");

// Send a handshake message
WebSocketManager->SendHandshake("Hello from C++");

// Execute Python code
WebSocketManager->ExecutePython("print('Hello from Unreal Engine')");

// Shutdown when done
WebSocketManager->Shutdown();
```

### In Blueprints

1. Create a variable of type `GenWebSocketManager`
2. Call `Initialize` to connect to the server
3. Use `SendHandshake` or `ExecutePython` to send commands
4. Call `Shutdown` when done

## Example Blueprint

Here's an example of how to use the WebSocket client in a Blueprint:

1. Create a new Blueprint Actor
2. Add a `GenWebSocketManager` variable
3. In the `BeginPlay` event:
   - Create a new `GenWebSocketManager` object
   - Call `Initialize` to connect to the server
   - Call `SendHandshake` to send a handshake message
4. Add a custom event for sending Python code:
   - Call `ExecutePython` with the Python code to execute
5. In the `EndPlay` event:
   - Call `Shutdown` to disconnect from the server

## Protocol

The WebSocket client follows the same protocol as the Python WebSocket server:

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

## Integration with Python WebSocket Server

The C++ WebSocket client is designed to work seamlessly with the Python WebSocket server:

1. The server listens on `ws://localhost:9877`
2. The client connects to this address
3. They exchange JSON messages with newline terminators
4. The server processes commands on the game thread
5. The client processes responses on the game thread

## Troubleshooting

- If the connection fails, check that the Python WebSocket server is running
- Make sure the port (9877) is not blocked by a firewall
- Check the Output Log for error messages
- Verify that the WebSockets module is properly included in the Build.cs file
