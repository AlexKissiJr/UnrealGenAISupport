"""
Node.js adapter for communicating with the Unreal Engine socket server
This file should be run outside of Unreal Engine
"""
import socket
import json
import sys
import os
import time
import threading
from typing import Dict, Any, Callable, Optional

# Configuration
DEFAULT_CONFIG = {
    "unreal_host": os.environ.get('UNREAL_HOST', 'localhost'),
    "unreal_port": int(os.environ.get('UNREAL_PORT', 9877)),
    "bridge_port": int(os.environ.get('BRIDGE_PORT', 9878)),
    "api_key": os.environ.get('UNREAL_API_KEY', 'your_default_api_key')
}

class UnrealSocketAdapter:
    """Adapter for communicating with the Unreal Engine socket server"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the adapter with configuration"""
        self.config = DEFAULT_CONFIG.copy()
        if config:
            self.config.update(config)
        
        self.connected = False
        self.event_handlers = {}
        self.bridge_socket = None
        self.bridge_thread = None
    
    def connect(self) -> bool:
        """Test the connection to the Unreal Engine socket server"""
        try:
            # Try a handshake message
            response = self.send_command({
                "type": "handshake",
                "message": "Connection test from Node.js adapter"
            })
            
            if response.get("success"):
                print(f"Successfully connected to Unreal Engine at {self.config['unreal_host']}:{self.config['unreal_port']}")
                self.connected = True
                return True
            else:
                print(f"Failed to connect: {response.get('error', 'Unknown error')}")
                return False
        except Exception as e:
            print(f"Connection error: {str(e)}")
            return False
    
    def send_command(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Send a command to the Unreal Engine socket server"""
        # Add API key if needed
        if "type" in command and command["type"] not in ["handshake", "auth"]:
            command["api_key"] = self.config["api_key"]
        
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((self.config["unreal_host"], self.config["unreal_port"]))
                s.sendall(json.dumps(command).encode())
                response = s.recv(4096)
                return json.loads(response.decode())
        except Exception as e:
            print(f"Error sending command: {str(e)}")
            self.connected = False
            return {"success": False, "error": str(e)}
    
    def start_event_listener(self) -> bool:
        """Start listening for events from the Unreal Engine bridge"""
        if self.bridge_thread and self.bridge_thread.is_alive():
            return True  # Already running
        
        try:
            # Create socket for bridge connection (long-running)
            self.bridge_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.bridge_socket.connect((self.config["unreal_host"], self.config["bridge_port"]))
            
            # Start thread to listen for events
            self.bridge_thread = threading.Thread(target=self._event_listener_thread)
            self.bridge_thread.daemon = True
            self.bridge_thread.start()
            
            print(f"Started event listener on {self.config['unreal_host']}:{self.config['bridge_port']}")
            return True
        except Exception as e:
            print(f"Failed to start event listener: {str(e)}")
            return False
    
    def _event_listener_thread(self):
        """Thread function for listening to events"""
        if not self.bridge_socket:
            return
        
        buffer = ""
        
        try:
            while True:
                data = self.bridge_socket.recv(4096)
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
                        
                        # Handle the event
                        self._handle_event(message)
                    except json.JSONDecodeError:
                        # Invalid JSON - discard until the next {
                        next_start = buffer.find("{")
                        if next_start == -1:
                            buffer = ""
                        else:
                            buffer = buffer[next_start:]
                        break
                    except Exception as e:
                        print(f"Error handling event: {str(e)}")
                        break
        except Exception as e:
            print(f"Event listener thread error: {str(e)}")
        finally:
            try:
                self.bridge_socket.close()
            except:
                pass
            self.bridge_socket = None
    
    def _handle_event(self, message: Dict[str, Any]):
        """Handle an event from the Unreal Engine bridge"""
        if message.get("type") != "event":
            return
        
        event_type = message.get("event_type")
        if not event_type or event_type not in self.event_handlers:
            return
        
        # Call registered handlers for this event type
        data = message.get("data", {})
        for handler in self.event_handlers.get(event_type, []):
            try:
                handler(data)
            except Exception as e:
                print(f"Error in event handler: {str(e)}")
    
    def register_event(self, event_type: str, handler: Callable[[Dict[str, Any]], None]) -> bool:
        """Register an event handler for a specific event type"""
        # First make sure we're listening for events
        if not self.bridge_socket and not self.start_event_listener():
            return False
        
        # Register handler locally
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)
        
        # Register with the Unreal Engine bridge
        response = self.send_command({
            "type": "register_event",
            "event_type": event_type
        })
        
        return response.get("success", False)
    
    def unregister_event(self, event_type: str, handler: Optional[Callable] = None) -> bool:
        """Unregister an event handler for a specific event type"""
        if event_type not in self.event_handlers:
            return True  # Nothing to unregister
        
        # Unregister handler locally
        if handler:
            self.event_handlers[event_type] = [h for h in self.event_handlers[event_type] if h != handler]
        else:
            self.event_handlers[event_type] = []
        
        # If no more handlers for this event type, unregister with the Unreal Engine bridge
        if not self.event_handlers[event_type]:
            response = self.send_command({
                "type": "unregister_event",
                "event_type": event_type
            })
            return response.get("success", False)
        
        return True
    
    def close(self):
        """Close the connection to the Unreal Engine bridge"""
        if self.bridge_socket:
            try:
                self.bridge_socket.close()
            except:
                pass
            self.bridge_socket = None
        
        self.connected = False
        print("Closed connection to Unreal Engine")


# Example usage
if __name__ == "__main__":
    adapter = UnrealSocketAdapter()
    if adapter.connect():
        # Register for events
        def on_object_spawned(data):
            print(f"Object spawned: {data}")
        
        adapter.register_event("object_spawned", on_object_spawned)
        
        # Example commands
        print("\nSending test commands:")
        
        # Spawn a cube
        response = adapter.send_command({
            "type": "spawn",
            "actor_class": "Cube",
            "location": [0, 0, 100],
            "rotation": [0, 0, 0],
            "scale": [1, 1, 1],
            "actor_label": "TestCube"
        })
        print(f"Spawn cube response: {response}")
        
        # Keep the script running to receive events
        try:
            print("\nListening for events (press Ctrl+C to exit)...")
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("Exiting...")
        finally:
            adapter.close() 