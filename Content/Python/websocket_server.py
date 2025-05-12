import unreal
import asyncio
import json
import threading
import queue
import time
import sys
import os
import importlib
from typing import Dict, Any, Optional, List, Set, Tuple

# Import websockets with error handling
try:
    import websockets
except ImportError:
    unreal.log_error("[AI Plugin] ERROR: websockets module not found. Please install it using pip install websockets")
    raise

# Set up logging first
import logging

# Create a custom logger
log = logging.getLogger("WebSocketServer")
log.setLevel(logging.INFO)

# Create console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)

# Add handler to logger
log.addHandler(console_handler)

# Helper functions for logging
def log_info(message):
    """Log info message"""
    log.info(message)
    unreal.log_info(f"[WebSocket] {message}")

def log_warning(message):
    """Log warning message"""
    log.warning(message)
    unreal.log_warning(f"[WebSocket] {message}")

def log_error(message, include_traceback=False):
    """Log error message"""
    if include_traceback:
        import traceback
        log.error(f"{message}\n{traceback.format_exc()}")
        unreal.log_error(f"[WebSocket] {message}\n{traceback.format_exc()}")
    else:
        log.error(message)
        unreal.log_error(f"[WebSocket] {message}")

# Try to import handlers, but provide fallbacks if they don't exist
try:
    from handlers import basic_commands, actor_commands, blueprint_commands, python_commands
    from handlers import ui_commands
    from utils import logging as external_log
    # If external logging exists, use it instead
    log_info = getattr(external_log, 'log_info', log_info)
    log_warning = getattr(external_log, 'log_warning', log_warning)
    log_error = getattr(external_log, 'log_error', log_error)
    log_info("Successfully imported handler modules")
except ImportError as e:
    log_warning(f"Could not import some handler modules: {str(e)}")
    # Create dummy modules with placeholder functions
    class DummyModule:
        @staticmethod
        def dummy_handler(command):
            return {"success": False, "error": "Handler not implemented"}

    # Create fallback modules if they don't exist
    basic_commands = getattr(sys.modules, 'basic_commands', DummyModule())
    actor_commands = getattr(sys.modules, 'actor_commands', DummyModule())
    blueprint_commands = getattr(sys.modules, 'blueprint_commands', DummyModule())
    python_commands = getattr(sys.modules, 'python_commands', DummyModule())
    ui_commands = getattr(sys.modules, 'ui_commands', DummyModule())

# Global queues and state with thread safety
command_queue = queue.Queue()
response_lock = threading.Lock()
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
        # Helper function to safely get handler
        def safe_get_handler(module, handler_name):
            try:
                return getattr(module, handler_name, None)
            except (AttributeError, TypeError):
                log_warning(f"Handler {handler_name} not found in module")
                return None

        # Register command handlers with fallbacks
        self.handlers = {
            # Always have handshake available
            "handshake": self._handle_handshake,
        }

        # Basic object commands
        self._add_handler("spawn", safe_get_handler(basic_commands, "handle_spawn"))
        self._add_handler("create_material", safe_get_handler(basic_commands, "handle_create_material"))
        self._add_handler("modify_object", safe_get_handler(actor_commands, "handle_modify_object"))

        # Blueprint commands
        self._add_handler("create_blueprint", safe_get_handler(blueprint_commands, "handle_create_blueprint"))
        self._add_handler("add_component", safe_get_handler(blueprint_commands, "handle_add_component"))
        self._add_handler("add_variable", safe_get_handler(blueprint_commands, "handle_add_variable"))
        self._add_handler("add_function", safe_get_handler(blueprint_commands, "handle_add_function"))
        self._add_handler("add_event", safe_get_handler(blueprint_commands, "handle_add_event"))
        self._add_handler("add_node", safe_get_handler(blueprint_commands, "handle_add_node"))
        self._add_handler("connect_nodes", safe_get_handler(blueprint_commands, "handle_connect_nodes"))

        # Bulk commands
        self._add_handler("add_nodes_bulk", safe_get_handler(blueprint_commands, "handle_add_nodes_bulk"))
        self._add_handler("connect_nodes_bulk", safe_get_handler(blueprint_commands, "handle_connect_nodes_bulk"))

        # Python and console
        self._add_handler("execute_python", safe_get_handler(python_commands, "handle_execute_python"))
        self._add_handler("execute_unreal_command", safe_get_handler(python_commands, "handle_execute_unreal_command"))

        # Component and property editing
        self._add_handler("edit_component_property", safe_get_handler(actor_commands, "handle_edit_component_property"))
        self._add_handler("add_component_with_events", safe_get_handler(actor_commands, "handle_add_component_with_events"))

        # Scene and project management
        self._add_handler("get_all_scene_objects", safe_get_handler(basic_commands, "handle_get_all_scene_objects"))
        self._add_handler("create_project_folder", safe_get_handler(basic_commands, "handle_create_project_folder"))
        self._add_handler("get_files_in_folder", safe_get_handler(basic_commands, "handle_get_files_in_folder"))

        # Input
        self._add_handler("add_input_binding", safe_get_handler(basic_commands, "handle_add_input_binding"))

        log_info(f"Registered {len(self.handlers)} command handlers")

    def _add_handler(self, command_type, handler):
        """Add a handler if it exists, otherwise use a not implemented handler"""
        if handler:
            self.handlers[command_type] = handler
        else:
            # Create a custom not implemented handler for this command type
            def not_implemented_handler(command):
                return {
                    "success": False,
                    "error": f"Handler for command '{command_type}' is not implemented"
                }
            self.handlers[command_type] = not_implemented_handler

    def dispatch(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """
        Dispatch a command to the appropriate handler
        """
        command_type = command.get("type", "")

        if not command_type:
            return {"success": False, "error": "No command type specified"}

        handler = self.handlers.get(command_type)

        if not handler:
            return {"success": False, "error": f"Unknown command type: {command_type}"}

        try:
            return handler(command)
        except Exception as e:
            log.log_error(f"Error handling command {command_type}: {str(e)}", include_traceback=True)
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

# Process commands on the main thread via Slate tick callback
def process_commands_tick():
    """Process commands on the main thread via Slate tick callback"""
    try:
        # Process up to 10 commands per tick to avoid blocking
        for _ in range(10):
            if command_queue.empty():
                break

            try:
                command_id, command, websocket = command_queue.get_nowait()
                log.log_info(f"Processing WebSocket command on game thread: {command}")

                try:
                    response = dispatcher.dispatch(command)

                    # Store response with thread safety
                    with response_lock:
                        response_dict[command_id] = (response, websocket)

                except Exception as e:
                    log.log_error(f"Error processing WebSocket command: {str(e)}", include_traceback=True)

                    # Store error response with thread safety
                    with response_lock:
                        response_dict[command_id] = ({"success": False, "error": str(e)}, websocket)

                finally:
                    # Mark task as done
                    command_queue.task_done()

            except queue.Empty:
                break
    except Exception as e:
        log.log_error(f"Error in process_commands_tick: {str(e)}", include_traceback=True)

    # Return True to keep the callback registered
    return True

# WebSocket handler
async def handle_websocket(websocket, path):
    """Handle WebSocket connections

    Args:
        websocket: The WebSocket connection
        path: The request path (required by websockets library)
    """
    client_id = f"client-{id(websocket)}"
    connected_clients.add(websocket)
    log.log_info(f"🟢 WebSocket client connected: {client_id} (path: {path})")

    try:
        async for message in websocket:
            try:
                # Parse the JSON message (expecting newline-terminated JSON)
                if message.endswith('\n'):
                    message = message[:-1]  # Remove trailing newline

                command = json.loads(message)
                log.log_info(f"WebSocket message received from {client_id}: {command}")

                # For handshake, we can respond directly
                if command.get("type") == "handshake":
                    response = dispatcher.dispatch(command)
                    await websocket.send(json.dumps(response) + '\n')
                else:
                    # For other commands, queue them for main thread execution
                    command_id = f"{client_id}-{time.time()}"
                    command_queue.put((command_id, command, websocket))

                    # Wait for the response with a timeout
                    timeout = 10  # seconds
                    start_time = time.time()
                    response = None

                    while time.time() - start_time < timeout:
                        with response_lock:
                            if command_id in response_dict:
                                response, _ = response_dict.pop(command_id)
                                break
                        await asyncio.sleep(0.1)

                    if response:
                        # Send the response with newline terminator
                        await websocket.send(json.dumps(response) + '\n')
                    else:
                        # Timeout occurred
                        error_response = {
                            "success": False,
                            "error": f"Command processing timeout after {timeout} seconds"
                        }
                        await websocket.send(json.dumps(error_response) + '\n')
            except json.JSONDecodeError as e:
                log.log_error(f"Invalid JSON from {client_id}: {str(e)}")
                await websocket.send(json.dumps({"success": False, "error": f"Invalid JSON: {str(e)}"}) + '\n')
            except Exception as e:
                log.log_error(f"Error handling message from {client_id}: {str(e)}", include_traceback=True)
                await websocket.send(json.dumps({"success": False, "error": str(e)}) + '\n')
    except websockets.exceptions.ConnectionClosed:
        log.log_info(f"WebSocket connection closed for {client_id}")
    except Exception as e:
        log.log_error(f"WebSocket handler error for {client_id}: {str(e)}", include_traceback=True)
    finally:
        connected_clients.discard(websocket)
        log.log_info(f"🔴 WebSocket client disconnected: {client_id}")

# Start the WebSocket server
async def start_websocket_server():
    """Start the WebSocket server"""
    global server_instance

    host = "localhost"
    port = 9877  # Fixed port as specified in requirements

    try:
        log.log_info(f"🟢 Starting WebSocket server on {host}:{port}...")
        server_instance = await websockets.serve(handle_websocket, host, port)
        log.log_info(f"✅ WebSocket server started successfully on ws://{host}:{port}")

        # Keep the server running
        await asyncio.Future()  # Run forever
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

# Register the command processor on the main thread
def register_command_processor():
    """Register the command processor on the main thread"""
    try:
        # Register a no-argument callback for Slate post-tick
        unreal.register_slate_post_tick_callback(process_commands_tick)
        log.log_info("✅ Registered WebSocket command processor on game thread")
    except Exception as e:
        log.log_error(f"Failed to register command processor: {str(e)}", include_traceback=True)

# Initialize the server
def initialize_server():
    """Initialize and start the WebSocket server"""
    global server_thread

    try:
        log.log_info("🟢 Initializing WebSocket server...")

        # Make sure any previous server is stopped
        stop_server()

        # Start the server thread
        server_thread = threading.Thread(target=websocket_server_thread, name="websocket_server_thread")
        server_thread.daemon = True
        server_thread.start()
        log.log_info("✅ WebSocket server thread started")

        # Register the command processor on the main thread
        register_command_processor()

        log.log_info("✅ Unreal Engine WebSocket AI command server initialized successfully")
        return True
    except Exception as e:
        log.log_error(f"Failed to initialize WebSocket server: {str(e)}", include_traceback=True)
        return False

# Stop the server
def stop_server():
    """Stop the WebSocket server"""
    global server_loop, server_task, server_instance, server_thread

    try:
        # Close the server
        if server_instance:
            log.log_info("Stopping WebSocket server...")

            # Close the event loop
            if server_loop and server_loop.is_running():
                server_loop.call_soon_threadsafe(server_loop.stop)

            server_instance = None
            server_task = None

            # Wait for the thread to exit
            if server_thread and server_thread.is_alive():
                server_thread.join(timeout=2.0)

            server_thread = None
            log.log_info("WebSocket server stopped")
    except Exception as e:
        log.log_error(f"Error stopping WebSocket server: {str(e)}", include_traceback=True)

# Example of how to use in an Editor Utility Widget:
"""
# In an Editor Utility Widget with a "Run Python Command" node:

import websocket_server
reload(websocket_server)  # Reload to get latest changes during development
websocket_server.initialize_server()
"""
