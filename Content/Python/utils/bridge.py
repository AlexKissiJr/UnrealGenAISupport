"""
Bridge module to handle communication between the Unreal Engine plugin and Node.js backend
"""
import json
import socket
import threading
import time
import os
from typing import Dict, Any, Optional, Callable

# Default configuration - override with environment variables
DEFAULT_CONFIG = {
    "listen_host": "0.0.0.0",
    "listen_port": 9878,  # Different port from the primary socket server
    "api_keys": ["your_default_api_key"],  # Should match the key in your backend
    "max_connections": 10
}

# Global state
active_connections = {}
event_listeners = {}


class BridgeServer:
    """
    Bridge server that listens for connections from the Node.js backend
    """
    def __init__(self, config: Dict[str, Any] = None):
        self.config = DEFAULT_CONFIG.copy()
        if config:
            self.config.update(config)
            
        # Load from environment if available
        if os.environ.get("BRIDGE_HOST"):
            self.config["listen_host"] = os.environ.get("BRIDGE_HOST")
        if os.environ.get("BRIDGE_PORT"):
            self.config["listen_port"] = int(os.environ.get("BRIDGE_PORT"))
            
        self.server_socket = None
        self.running = False
        self.server_thread = None
        
    def start(self):
        """Start the bridge server"""
        if self.running:
            return
            
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.config["listen_host"], self.config["listen_port"]))
        self.server_socket.listen(self.config["max_connections"])
        
        self.running = True
        self.server_thread = threading.Thread(target=self._run_server)
        self.server_thread.daemon = True
        self.server_thread.start()
        
        print(f"Bridge server started on {self.config['listen_host']}:{self.config['listen_port']}")
        
    def stop(self):
        """Stop the bridge server"""
        self.running = False
        if self.server_socket:
            self.server_socket.close()
        
    def _run_server(self):
        """Server thread function"""
        while self.running:
            try:
                client_socket, addr = self.server_socket.accept()
                client_id = f"{addr[0]}:{addr[1]}"
                print(f"Bridge connection from {client_id}")
                
                # Start a thread to handle this client
                client_thread = threading.Thread(
                    target=self._handle_client,
                    args=(client_socket, client_id)
                )
                client_thread.daemon = True
                client_thread.start()
                
            except Exception as e:
                if self.running:  # Only log errors if we're still supposed to be running
                    print(f"Bridge server error: {str(e)}")
                    time.sleep(1)  # Prevent tight loop if accept() keeps failing
                
    def _handle_client(self, client_socket, client_id):
        """Handle client connection"""
        active_connections[client_id] = client_socket
        
        try:
            # Keep connection open for bidirectional communication
            buffer = ""
            while self.running:
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
                        
                        # Validate API key
                        api_key = message.get("api_key")
                        if api_key not in self.config["api_keys"]:
                            response = {"success": False, "error": "Invalid API key"}
                            client_socket.sendall(json.dumps(response).encode())
                            continue
                            
                        # Handle the message
                        self._handle_message(message, client_socket, client_id)
                    except json.JSONDecodeError:
                        # Invalid JSON - discard until the next {
                        next_start = buffer.find("{")
                        if next_start == -1:
                            buffer = ""
                        else:
                            buffer = buffer[next_start:]
                        break
                    except Exception as e:
                        print(f"Error handling message: {str(e)}")
                        break
        except Exception as e:
            print(f"Error with client {client_id}: {str(e)}")
        finally:
            # Clean up
            client_socket.close()
            if client_id in active_connections:
                del active_connections[client_id]
                
    def _handle_message(self, message, client_socket, client_id):
        """Handle a message from the client"""
        message_type = message.get("type")
        
        if message_type == "register_event":
            # Client wants to register for Unreal Engine events
            event_type = message.get("event_type")
            if event_type:
                if event_type not in event_listeners:
                    event_listeners[event_type] = set()
                event_listeners[event_type].add(client_id)
                response = {"success": True, "message": f"Registered for {event_type} events"}
            else:
                response = {"success": False, "error": "No event_type specified"}
                
        elif message_type == "unregister_event":
            # Client wants to unregister from events
            event_type = message.get("event_type")
            if event_type and event_type in event_listeners and client_id in event_listeners[event_type]:
                event_listeners[event_type].remove(client_id)
                response = {"success": True, "message": f"Unregistered from {event_type} events"}
            else:
                response = {"success": False, "error": "Not registered for this event"}
                
        else:
            # Unknown message type
            response = {"success": False, "error": f"Unknown message type: {message_type}"}
            
        # Send response
        client_socket.sendall(json.dumps(response).encode())


# Global bridge server instance
bridge_server = None


def initialize_bridge(config: Dict[str, Any] = None):
    """Initialize the bridge server"""
    global bridge_server
    if bridge_server is None:
        bridge_server = BridgeServer(config)
        bridge_server.start()
    return bridge_server


def broadcast_event(event_type: str, data: Dict[str, Any]):
    """Broadcast an event to all registered clients"""
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
                print(f"Error sending to client {client_id}: {str(e)}")
                # Remove client if we can't send to it
                event_listeners[event_type].remove(client_id)
                if client_id in active_connections:
                    active_connections[client_id].close()
                    del active_connections[client_id]


def register_event_handler(event_type: str, handler: Callable):
    """Register a handler for an event type (used internally)"""
    # Implement internal event handling if needed
    pass


# Shutdown function
def shutdown_bridge():
    """Shut down the bridge server"""
    global bridge_server
    if bridge_server:
        bridge_server.stop()
        bridge_server = None 