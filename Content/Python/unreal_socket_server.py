import socket
import json
import unreal
import threading
import time
import uuid
import os
from typing import Dict, Any, Tuple, List, Optional, Callable

# Import handlers
from handlers import basic_commands, actor_commands, blueprint_commands
from utils import logging as log

# Global queues and state
command_queue = []
response_dict = {}
api_keys = {}  # Dictionary to store valid API keys

# Event tracking for web frontend
active_connections = {}
event_listeners = {}

# Default configuration
DEFAULT_API_KEYS = ["your_default_api_key"]

# Server ports
PRIMARY_PORT = int(os.environ.get('UNREAL_PORT', 9877))  # Main socket server port
WEB_BRIDGE_PORT = int(os.environ.get('BRIDGE_PORT', 9878))  # Web frontend bridge port

class CommandDispatcher:
    """
    Dispatches commands to appropriate handlers based on command type
    """
    def __init__(self):
        # Register command handlers
        self.handlers = {
            "handshake": self._handle_handshake,
            "auth": self._handle_auth,

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
            "get_node_guid": blueprint_commands.handle_get_node_guid,
            
            # Bulk commands
            "add_nodes_bulk": blueprint_commands.handle_add_nodes_bulk,
            "connect_nodes_bulk": blueprint_commands.handle_connect_nodes_bulk,
            
            # Web frontend commands
            "register_event": self._handle_register_event,
            "unregister_event": self._handle_unregister_event,
            "send_event": self._handle_send_event,
            "check_connection": self._handle_check_connection
        }
        
        # Initialize API keys
        for key in DEFAULT_API_KEYS:
            api_keys[key] = {"valid": True, "created_at": time.time()}

    def dispatch(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Dispatch command to appropriate handler"""
        # First check authentication
        api_key = command.get("api_key")
        command_type = command.get("type")
        
        # Skip auth check for handshake and auth commands
        if command_type not in ["handshake", "auth", "check_connection"] and not self._validate_api_key(api_key):
            return {"success": False, "error": "Unauthorized: Invalid or missing API key"}
            
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
        log.log_info(f"Handshake received: {message}")
        return {"success": True, "message": f"Received: {message}"}
        
    def _handle_auth(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Handle authentication requests"""
        key = command.get("key")
        if key in api_keys and api_keys[key]["valid"]:
            return {"success": True, "message": "Authentication successful"}
        else:
            # In a real production system, you'd want to implement proper authentication
            # This is just a placeholder
            return {"success": False, "error": "Invalid authentication key"}
    
    def _handle_check_connection(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Handle connection check requests from web frontend"""
        return {"success": True, "message": "Connected to Unreal Engine"}
            
    def _validate_api_key(self, key: str) -> bool:
        """Validate if API key is valid"""
        if not key:
            return False
        return key in api_keys and api_keys[key]["valid"]
        
    def _handle_register_event(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Handle event registration from web frontend"""
        client_id = command.get("client_id")
        event_type = command.get("event_type")
        
        if not event_type:
            return {"success": False, "error": "No event_type specified"}
            
        if event_type not in event_listeners:
            event_listeners[event_type] = set()
            
        event_listeners[event_type].add(client_id)
        return {"success": True, "message": f"Registered for {event_type} events"}
        
    def _handle_unregister_event(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Handle event unregistration from web frontend"""
        client_id = command.get("client_id")
        event_type = command.get("event_type")
        
        if not event_type or event_type not in event_listeners or client_id not in event_listeners[event_type]:
            return {"success": False, "error": "Not registered for this event"}
            
        event_listeners[event_type].remove(client_id)
        return {"success": True, "message": f"Unregistered from {event_type} events"}
        
    def _handle_send_event(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Handle sending events to web frontend"""
        event_type = command.get("event_type")
        data = command.get("data", {})
        
        if not event_type:
            return {"success": False, "error": "No event_type specified"}
            
        # Broadcast the event to all registered clients
        broadcast_event(event_type, data)
        return {"success": True, "message": f"Event {event_type} broadcasted"}


# Create global dispatcher instance
dispatcher = CommandDispatcher()


def process_commands(delta_time=None):
    """Process commands on the main thread"""
    if not command_queue:
        return

    command_id, command = command_queue.pop(0)
    log.log_info(f"Processing command on main thread: {command}")

    try:
        response = dispatcher.dispatch(command)
        response_dict[command_id] = response
    except Exception as e:
        log.log_error(f"Error processing command: {str(e)}", include_traceback=True)
        response_dict[command_id] = {"success": False, "error": str(e)}


def socket_server_thread():
    """Socket server running in a separate thread"""
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    # Listen on all interfaces for external connections
    server_socket.bind(('0.0.0.0', PRIMARY_PORT))
    server_socket.listen(5)
    log.log_info(f"Unreal Engine socket server started on port {PRIMARY_PORT} (all interfaces)")

    command_counter = 0

    while True:
        try:
            conn, addr = server_socket.accept()
            log.log_info(f"Connection from {addr}")
            data = conn.recv(4096)
            if data:
                try:
                    command = json.loads(data.decode())
                    log.log_info(f"Received command: {command}")

                    # For handshake, auth, and check_connection we can respond directly from the thread
                    if command.get("type") in ["handshake", "auth", "check_connection"]:
                        response = dispatcher.dispatch(command)
                        conn.sendall(json.dumps(response).encode())
                    else:
                        # For other commands, queue them for main thread execution
                        command_id = command_counter
                        command_counter += 1
                        command_queue.append((command_id, command))

                        # Wait for the response with a timeout
                        timeout = 10  # seconds
                        start_time = time.time()
                        while command_id not in response_dict and time.time() - start_time < timeout:
                            time.sleep(0.1)

                        if command_id in response_dict:
                            response = response_dict.pop(command_id)
                            conn.sendall(json.dumps(response).encode())
                        else:
                            error_response = {"success": False, "error": "Command timed out"}
                            conn.sendall(json.dumps(error_response).encode())
                except json.JSONDecodeError:
                    error_response = {"success": False, "error": "Invalid JSON format"}
                    conn.sendall(json.dumps(error_response).encode())
            conn.close()
        except Exception as e:
            log.log_error(f"Error in socket server: {str(e)}", include_traceback=True)


def web_bridge_thread():
    """Web bridge server running in a separate thread"""
    bridge_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    bridge_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    # Listen on all interfaces for web connections
    bridge_socket.bind(('0.0.0.0', WEB_BRIDGE_PORT))
    bridge_socket.listen(10)
    log.log_info(f"Web bridge server started on port {WEB_BRIDGE_PORT} (all interfaces)")

    while True:
        try:
            client_socket, addr = bridge_socket.accept()
            client_id = f"{addr[0]}:{addr[1]}"
            log.log_info(f"Web client connection from {client_id}")
            
            # Start a thread to handle this client
            client_thread = threading.Thread(
                target=handle_web_client,
                args=(client_socket, client_id)
            )
            client_thread.daemon = True
            client_thread.start()
        except Exception as e:
            log.log_error(f"Error in web bridge server: {str(e)}")
            time.sleep(1)  # Prevent tight loop if accept() keeps failing


def handle_web_client(client_socket, client_id):
    """Handle web client connection"""
    active_connections[client_id] = client_socket
    
    try:
        # Keep connection open for bidirectional communication
        buffer = ""
        while True:
            data = client_socket.recv(4096)
            if not data:
                break  # Connection closed
                
            buffer += data.decode()
            
            # Process complete JSON messages
            while True:
                try:
                    # Find a complete JSON object
                    obj_end = buffer.find("}")
                    if obj_end == -1:
                        break  # No complete object yet
                        
                    # Parse the message
                    message = json.loads(buffer[:obj_end+1])
                    buffer = buffer[obj_end+1:].lstrip()
                    
                    # Add client ID for tracking
                    message["client_id"] = client_id
                    
                    # Handle the message via the dispatcher
                    response = dispatcher.dispatch(message)
                    client_socket.sendall(json.dumps(response).encode())
                except json.JSONDecodeError:
                    # Invalid JSON - discard until the next {
                    next_start = buffer.find("{")
                    if next_start == -1:
                        buffer = ""
                    else:
                        buffer = buffer[next_start:]
                    break
                except Exception as e:
                    log.log_error(f"Error handling web client message: {str(e)}")
                    break
    except Exception as e:
        log.log_error(f"Error with web client {client_id}: {str(e)}")
    finally:
        # Clean up
        client_socket.close()
        if client_id in active_connections:
            del active_connections[client_id]
            
        # Remove from event listeners
        for event_type, listeners in event_listeners.items():
            if client_id in listeners:
                listeners.remove(client_id)


def broadcast_event(event_type: str, data: Dict[str, Any]):
    """Broadcast an event to all registered web clients"""
    if event_type not in event_listeners:
        return
        
    message = {
        "type": "event",
        "event_type": event_type,
        "data": data
    }
    
    message_json = json.dumps(message)
    
    # Send to all registered clients
    for client_id in list(event_listeners[event_type]):
        if client_id in active_connections:
            try:
                active_connections[client_id].sendall(message_json.encode())
            except Exception as e:
                log.log_error(f"Error sending to client {client_id}: {str(e)}")
                # Remove client if we can't send to it
                event_listeners[event_type].remove(client_id)
                if client_id in active_connections:
                    try:
                        active_connections[client_id].close()
                    except:
                        pass
                    del active_connections[client_id]


# Register tick function to process commands on main thread
def register_command_processor():
    """Register the command processor with Unreal's tick system"""
    unreal.register_slate_post_tick_callback(process_commands)
    log.log_info("Command processor registered")


# Initialize the server
def initialize_server():
    """Initialize and start the socket server"""
    # Start the main server thread
    thread = threading.Thread(target=socket_server_thread)
    thread.daemon = True
    thread.start()
    log.log_info("Main socket server thread started")
    
    # Start the web bridge thread
    bridge_thread = threading.Thread(target=web_bridge_thread)
    bridge_thread.daemon = True
    bridge_thread.start()
    log.log_info("Web bridge server thread started")

    # Register the command processor on the main thread
    register_command_processor()

    log.log_info("Unreal Engine AI command server initialized successfully")
    log.log_info("Available interfaces:")
    log.log_info(f"  - MCP/Python API: Port {PRIMARY_PORT}")
    log.log_info(f"  - Web Frontend Bridge: Port {WEB_BRIDGE_PORT}")
    log.log_info("Available commands:")
    log.log_info("  - Authentication: handshake, auth")
    log.log_info("  - Basic: spawn, create_material, modify_object")
    log.log_info("  - Blueprint: create_blueprint, add_component, add_variable, add_function, add_node, connect_nodes, compile_blueprint, spawn_blueprint, add_nodes_bulk, connect_nodes_bulk")
    log.log_info("  - Web frontend: register_event, unregister_event, send_event, check_connection")

# Auto-start the server when this module is imported
initialize_server()