# WebSocket Server for Unreal Engine GenAI Support

This implementation provides a WebSocket server for the Unreal Engine GenAI Support plugin. It allows clients to connect to the server and send commands to Unreal Engine using the FastMCP protocol.

## Files

- `mcp_server_refactored.py`: The main WebSocket server implementation
- `mcp_tools.py`: The tool functions and FastMCP implementation
- `websocket_client_test.py`: A simple WebSocket client for testing

## How to Use

### Starting the Server

The server can be started in two ways:

1. From the command line:
   ```bash
   cd /path/to/UnrealGenAISupport/Content/Python
   python3 mcp_server_refactored.py
   ```

2. From Unreal Engine:
   ```python
   import mcp_server_refactored
   mcp_server_refactored.main()
   ```

### Connecting to the Server

Clients can connect to the server using the WebSocket protocol on port 9877. The server accepts JSON messages with the following format:

```json
{
  "name": "tool_name",
  "args": {
    "arg1": "value1",
    "arg2": "value2"
  }
}
```

Where:
- `name`: The name of the tool to call
- `args`: The arguments to pass to the tool

### Available Tools

The following tools are available:

- `handshake_test`: Test the connection to the server
- `execute_python_script`: Execute a Python script in Unreal Engine
- `execute_unreal_command`: Execute an Unreal Engine command
- `spawn_object`: Spawn an object in the Unreal Engine level
- `edit_component_property`: Edit a property of a component in a Blueprint or scene actor
- `create_material`: Create a new material with the specified color
- `create_blueprint`: Create a new Blueprint class
- `add_component_to_blueprint`: Add a component to a Blueprint
- `add_variable_to_blueprint`: Add a variable to a Blueprint
- `add_function_to_blueprint`: Add a function to a Blueprint
- `add_node_to_blueprint`: Add a node to a Blueprint graph
- `get_node_suggestions`: Get suggestions for a node type in Unreal Blueprints
- `delete_node_from_blueprint`: Delete a node from a Blueprint graph
- `get_all_nodes_in_graph`: Get all nodes in a Blueprint graph with their positions and types
- `connect_blueprint_nodes`: Connect two nodes in a Blueprint graph
- `compile_blueprint`: Compile a Blueprint
- `spawn_blueprint_actor`: Spawn a Blueprint actor in the level
- `add_component_with_events`: Add a component to a Blueprint with overlap events if applicable
- `connect_blueprint_nodes_bulk`: Connect multiple pairs of nodes in a Blueprint graph
- `get_blueprint_node_guid`: Retrieve the GUID of a pre-existing node in a Blueprint graph
- `get_all_scene_objects`: Retrieve all actors in the current Unreal Engine level
- `create_project_folder`: Create a new folder in the Unreal project content directory
- `get_files_in_folder`: List all files in a specified project folder
- `create_game_mode`: Create a game mode Blueprint, set its default pawn, and assign it as the current scene's default game mode
- `add_widget_to_user_widget`: Add a widget to a User Widget Blueprint
- `edit_widget_property`: Edit a property of a widget in a User Widget Blueprint
- `add_input_binding`: Add an input action binding to Project Settings

### Example

Here's an example of how to call the `handshake_test` tool:

```json
{
  "name": "handshake_test",
  "args": {
    "message": "Hello from WebSocket client"
  }
}
```

The server will respond with:

```json
{
  "success": true,
  "message": "Handshake successful with key: UnrealHandshake"
}
```

## Implementation Details

The implementation consists of three main components:

1. **WebSocket Server**: Handles WebSocket connections, handshakes, and message encoding/decoding
2. **FastMCP**: Dispatches commands to the appropriate tool functions
3. **Tool Functions**: Implement the functionality for each tool

### WebSocket Protocol

The WebSocket protocol is implemented according to RFC 6455. It includes:

- Handshake with Sec-WebSocket-Key and Sec-WebSocket-Accept
- Frame encoding and decoding
- Support for text messages (opcode 0x1)
- Support for close frames (opcode 0x8)
- Support for ping/pong frames (opcodes 0x9/0xA)

### FastMCP Protocol

The FastMCP protocol is a simple JSON-based protocol for calling tool functions. It includes:

- Tool registration with the `@mcp.tool()` decorator
- Tool dispatch based on the `name` field in the JSON message
- Tool arguments passed as the `args` field in the JSON message
- Tool results returned as the `result` field in the JSON response

## Troubleshooting

If you encounter issues with the WebSocket server, check the following:

1. Make sure the server is running and listening on port 9877
2. Make sure the client is sending valid JSON messages
3. Make sure the tool name is correct and the tool exists
4. Make sure the tool arguments are correct

## License

This implementation is part of the Unreal Engine GenAI Support plugin and is subject to the same license terms.
