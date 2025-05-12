# WebSocket Testing Guide

This guide provides instructions for testing the WebSocket functionality in the UnrealGenAISupport plugin.

## Quick Test

The quickest way to test if the WebSocket server is working:

1. Open your Unreal Engine project
2. Open the Python Socket Control Panel from the toolbar
3. Make sure "Use WebSocket" is checked
4. Click "Start Server"
5. Run the test script:
   ```python
   # In the Unreal Engine Python console
   import test_websocket_server
   test_websocket_server.run_test()
   ```
6. Check the Output Log for the test results

## Test with HTML Client

To test with the HTML client:

1. Start the WebSocket server as described above
2. Open `Resources/SimpleWebSocketTest.html` in a web browser
3. Click "Connect to WebSocket Server"
4. If the connection is successful, the status will change to "Connected"
5. Click "Send Handshake" to test the handshake functionality
6. Click "Send Ping" to test the ping functionality
7. Check the log for the responses

## Test with Editor Utility Widget

To create and use an Editor Utility Widget for testing:

1. Run the following script to create the widget:
   ```python
   # In the Unreal Engine Python console
   import create_websocket_test_widget
   ```
2. The widget will open in the editor
3. Add the following components to the widget:
   - A button for starting the WebSocket server
   - A button for testing the WebSocket server
   - A text block for displaying the test results
4. Add the following code to the "Start Server" button click event:
   ```python
   import websocket_server
   websocket_server.initialize_server()
   ```
5. Add the following code to the "Test Server" button click event:
   ```python
   import test_websocket_server
   test_websocket_server.run_test()
   ```

## Test with Blueprint

To create and use a Blueprint for testing:

1. Run the following script to create the Blueprint:
   ```python
   # In the Unreal Engine Python console
   import create_websocket_test_blueprint
   ```
2. The Blueprint will open in the editor
3. Add the following components to the Blueprint:
   - A `GenWebSocketManager` variable
   - A `GenWebSocketClient` variable
4. In the `BeginPlay` event:
   ```
   Create Object (Class: GenWebSocketManager) → Set as WebSocketManager
   Call Initialize on WebSocketManager
   ```
5. Add a custom event called `SendHandshake` with the following logic:
   ```
   If WebSocketManager Is Connected
      Call SendHandshake on WebSocketManager with message "Test from Blueprint"
   ```
6. In the `EndPlay` event:
   ```
   Call Shutdown on WebSocketManager
   ```

## Troubleshooting

If you encounter issues with the WebSocket server:

1. Check the Output Log for error messages
2. Make sure the WebSocket server is running
3. Verify that port 9877 is not blocked by a firewall
4. Check if the WebSocket server is already running in another instance
5. Try restarting the Unreal Engine editor

### Common Issues

#### "WebSocket server failed to start"

This could be due to:
- Port 9877 is already in use
- Missing Python dependencies
- Errors in the WebSocket server code

#### "WebSocket connection failed"

This could be due to:
- WebSocket server not running
- Firewall blocking the connection
- Incorrect WebSocket URL

#### "Handler not implemented"

This means the command handler is not available. Check if the handler is properly implemented in the corresponding module.

## Advanced Testing

For more advanced testing:

1. Use the `websocket` Python module to create a custom client
2. Test different command types (blueprint_operation, actor_operation, etc.)
3. Test error handling by sending invalid commands
4. Test performance with multiple concurrent connections
5. Test long-running connections

## Next Steps

After verifying that the WebSocket server works:

1. Test the integration with your AI models
2. Test the Blueprint and actor operations
3. Create a custom UI for controlling the WebSocket functionality
4. Develop external applications that use the WebSocket API
