import unreal
import asyncio
import websockets
import json
import threading
import time
import socket
import sys
import os
from typing import Dict, Any, Optional, List, Set, Tuple

# Import handlers from existing socket server
from handlers import basic_commands, actor_commands, blueprint_commands, python_commands
from handlers import ui_commands
from utils import logging as log

# Global queues and state
command_queue = []
response_dict = {}
connected_clients = set()

# Global server state
server_instance = None
server_task = None
server_loop = None
server_thread = None

# Create a command dispatcher (reusing from socket server)
class CommandDispatcher:
    """
    Dispatches commands to appropriate handlers based on command type
    """
    def __init__(self):
        # Register command handlers
        self.handlers = {
            "handshake": self._handle_handshake,

            # Basic object commands
            "spawn": basic_commands.handle_spawn,
            "create_material": basic_commands.handle_create_material,
            "modify_object": actor_commands.handle_modify_object,

            # Blueprint commands
            "create_blueprint": blueprint_commands.handle_create_blueprint,
            "add_component": blueprint_commands.handle_add_component,
            "add_variable": blueprint_commands.handle_add_variable,
            "add_function": blueprint_commands.handle_add_function,
            "add_node": blueprint_commands.handle_add_node,
            "connect_nodes": blueprint_commands.handle_connect_nodes,
            "compile_blueprint": blueprint_commands.handle_compile_blueprint,
            "spawn_blueprint": blueprint_commands.handle_spawn_blueprint,
            "delete_node": blueprint_commands.handle_delete_node,

            # Getters
            "get_node_guid": blueprint_commands.handle_get_node_guid,
            "get_all_nodes": blueprint_commands.handle_get_all_nodes,
            "get_node_suggestions": blueprint_commands.handle_get_node_suggestions,

            # Bulk commands
            "add_nodes_bulk": blueprint_commands.handle_add_nodes_bulk,
            "connect_nodes_bulk": blueprint_commands.handle_connect_nodes_bulk,

            # Python and console
            "execute_python": python_commands.handle_execute_python,
            "execute_unreal_command": python_commands.handle_execute_unreal_command,

            # New
            "edit_component_property": actor_commands.handle_edit_component_property,
            "add_component_with_events": actor_commands.handle_add_component_with_events,

            # Scene
            "get_all_scene_objects": basic_commands.handle_get_all_scene_objects,
            "create_project_folder": basic_commands.handle_create_project_folder,
            "get_files_in_folder": basic_commands.handle_get_files_in_folder,

            # Input
            "add_input_binding": basic_commands.handle_add_input_binding,

            # UI commands
            "add_widget_to_user_widget": ui_commands.handle_add_widget_to_user_widget,
            "edit_widget_property": ui_commands.handle_edit_widget_property,
        }

    def dispatch(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Dispatch command to appropriate handler"""
        command_type = command.get("type")
        if command_type not in self.handlers:
            return {"success": False, "error": f"Unknown command type: {command_type}"}

        try:
            handler = self.handlers[command_type]
            return handler(command)
        except Exception as e:
            log.log_error(f"Error processing command: {str(e)}")
            return {"success": False, "error": str(e)}

    def _handle_handshake(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Built-in handler for handshake command"""
        message = command.get("message", "")
        log.log_info(f"WebSocket handshake received: {message}")

        # Get Unreal Engine version
        engine_version = unreal.SystemLibrary.get_engine_version()

        # Add connection and session information
        connection_info = {
            "status": "Connected via WebSocket",
            "engine_version": engine_version,
            "timestamp": time.time(),
            "session_id": f"WS-UE-{int(time.time())}"
        }

        return {
            "success": True,
            "message": f"WebSocket handshake received: {message}",
            "connection_info": connection_info
        }

# Create global dispatcher instance
dispatcher = CommandDispatcher()

# Process commands on the main thread
def process_commands(delta_time=None):
    """Process commands on the main thread"""
    if not command_queue:
        return

    command_id, command, websocket = command_queue.pop(0)
    log.log_info(f"Processing WebSocket command on main thread: {command}")

    try:
        response = dispatcher.dispatch(command)
        response_dict[command_id] = (response, websocket)
    except Exception as e:
        log.log_error(f"Error processing WebSocket command: {str(e)}", include_traceback=True)
        response_dict[command_id] = ({"success": False, "error": str(e)}, websocket)

# WebSocket handler
async def handle_websocket(websocket, path):
    """Handle WebSocket connections

    Args:
        websocket: The WebSocket connection
        path: The request path (required by websockets library)
    """
    client_id = f"client-{id(websocket)}"
    connected_clients.add(websocket)
    log.log_info(f"WebSocket client connected: {client_id} (path: {path})")

    try:
        async for message in websocket:
            try:
                # Parse the JSON message
                command = json.loads(message)
                log.log_info(f"WebSocket message received from {client_id}: {command}")

                # For handshake, we can respond directly
                if command.get("type") == "handshake":
                    response = dispatcher.dispatch(command)
                    await websocket.send(json.dumps(response))
                else:
                    # For other commands, queue them for main thread execution
                    command_id = f"{client_id}-{time.time()}"
                    command_queue.append((command_id, command, websocket))

                    # Wait for the response with a timeout
                    timeout = 10  # seconds
                    start_time = time.time()
                    while command_id not in response_dict and time.time() - start_time < timeout:
                        await asyncio.sleep(0.1)

                    # Send the response if available
                    if command_id in response_dict:
                        response, _ = response_dict.pop(command_id)
                        await websocket.send(json.dumps(response))
                    else:
                        # Timeout occurred
                        error_response = {"success": False, "error": "Command processing timeout"}
                        await websocket.send(json.dumps(error_response))

            except json.JSONDecodeError as e:
                log.log_error(f"Invalid JSON received: {str(e)}")
                error_response = {"success": False, "error": f"Invalid JSON: {str(e)}"}
                await websocket.send(json.dumps(error_response))
            except Exception as e:
                log.log_error(f"Error processing WebSocket message: {str(e)}", include_traceback=True)
                error_response = {"success": False, "error": str(e)}
                await websocket.send(json.dumps(error_response))
    except websockets.exceptions.ConnectionClosed:
        log.log_info(f"WebSocket client disconnected: {client_id}")
    finally:
        connected_clients.remove(websocket)

# Function to find an available port
def find_available_port(start_port=8081, max_attempts=5):
    """Find an available port starting from start_port"""
    for port in range(start_port, start_port + max_attempts):
        try:
            # Try to create a socket and bind to the port
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(('localhost', port))
            sock.close()
            return port
        except OSError:
            continue
    return None

# WebSocket server
async def start_websocket_server(host='localhost', port=8081):
    """Start the WebSocket server"""
    global server_instance

    try:
        # Find an available port
        available_port = find_available_port(port)
        if available_port is None:
            log.log_error(f"Could not find an available port after trying {port} through {port+4}")
            return None

        if available_port != port:
            log.log_warning(f"Port {port} is not available, using port {available_port} instead")

        # Create a server instance with the handler function
        # The handler function must accept websocket and path parameters
        server_instance = await websockets.serve(
            ws_handler=handle_websocket,  # Explicitly name the parameter
            host=host,
            port=available_port
        )

        log.log_info(f"WebSocket server started on ws://{host}:{available_port}")

        # Return the server instance and port
        return server_instance, available_port
    except Exception as e:
        log.log_error(f"Failed to start WebSocket server: {str(e)}", include_traceback=True)
        return None

# Thread function to run the WebSocket server
def websocket_server_thread():
    """Run the WebSocket server in a separate thread"""
    global server_loop, server_task, server_instance

    try:
        # Create a new event loop for this thread
        server_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(server_loop)

        # Start the server
        server_task = server_loop.create_task(start_websocket_server())

        # Run the event loop
        server_loop.run_forever()
    except Exception as e:
        log.log_error(f"Error in WebSocket server thread: {str(e)}", include_traceback=True)
    finally:
        log.log_info("WebSocket server thread exiting")

# Register tick function to process commands on main thread
def register_command_processor():
    """Register the command processor with Unreal's tick system"""
    unreal.register_slate_post_tick_callback(process_commands)
    log.log_info("WebSocket command processor registered")

# Initialize the server
def initialize_server():
    """Initialize and start the WebSocket server"""
    global server_thread

    # Make sure any previous server is stopped
    stop_server()

    # Start the server thread
    server_thread = threading.Thread(target=websocket_server_thread, name="websocket_server_thread")
    server_thread.daemon = True
    server_thread.start()
    log.log_info("WebSocket server thread started")

    # Register the command processor on the main thread
    register_command_processor()

    log.log_info("Unreal Engine WebSocket AI command server initialized successfully")
    return True

# Function to stop the server
def stop_server():
    """Stop the WebSocket server"""
    global server_loop, server_task, server_instance, server_thread

    # Unregister the command processor
    try:
        unreal.unregister_slate_post_tick_callback(process_commands)
        log.log_info("WebSocket command processor unregistered")
    except Exception as e:
        log.log_error(f"Error unregistering WebSocket command processor: {str(e)}")

    # Clear any pending commands and responses
    command_queue.clear()
    response_dict.clear()

    # Stop the server
    if server_loop is not None:
        try:
            # Close the server
            if server_instance is not None:
                # Create a coroutine to close the server
                async def close_server():
                    server_instance.close()
                    await server_instance.wait_closed()

                # Run the coroutine in the server's event loop
                future = asyncio.run_coroutine_threadsafe(close_server(), server_loop)

                # Wait for the coroutine to complete with a timeout
                try:
                    future.result(timeout=2.0)
                except Exception as e:
                    log.log_warning(f"Error waiting for server to close: {str(e)}")

                server_instance = None

            # Stop the event loop
            server_loop.call_soon_threadsafe(server_loop.stop)
            server_loop = None
            server_task = None
        except Exception as e:
            log.log_error(f"Error stopping WebSocket server: {str(e)}")

    # Wait for the thread to exit
    if server_thread is not None and server_thread.is_alive():
        try:
            # Give the thread a short time to exit gracefully
            server_thread.join(timeout=1.0)
        except Exception as e:
            log.log_error(f"Error joining WebSocket server thread: {str(e)}")
        finally:
            server_thread = None

    log.log_info("WebSocket server stopped")
    return True

# Auto-start is disabled - the server will be started explicitly when needed
# To start the server manually, call initialize_server()
# initialize_server()
