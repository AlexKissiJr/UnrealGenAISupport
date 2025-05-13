import socket
import json
import sys
import os
import threading
import time
import traceback
from pathlib import Path

# Try to import unreal module, but don't fail if we're running outside of Unreal
try:
    import unreal
    IN_UNREAL = True
except ImportError:
    IN_UNREAL = False
    print("Running outside of Unreal Engine environment", file=sys.stderr)

# We don't need the MCP module for the WebSocket server

# Import handlers
try:
    from handlers import basic_commands, actor_commands, blueprint_commands, python_commands
    from handlers import ui_commands
    HANDLERS_AVAILABLE = True
except ImportError:
    HANDLERS_AVAILABLE = False
    print("Handler modules not available", file=sys.stderr)

# Create a PID file to let the Unreal plugin know this process is running
def write_pid_file():
    try:
        pid = os.getpid()
        pid_dir = os.path.join(os.path.expanduser("~"), ".unrealgenai")
        os.makedirs(pid_dir, exist_ok=True)
        pid_path = os.path.join(pid_dir, "mcp_server.pid")

        with open(pid_path, "w") as f:
            f.write(f"{pid}\n9877")  # Store PID and port

        # Register to delete the PID file on exit
        import atexit
        def cleanup_pid_file():
            try:
                if os.path.exists(pid_path):
                    os.remove(pid_path)
            except:
                pass

        atexit.register(cleanup_pid_file)

        return pid_path
    except Exception as e:
        print(f"Failed to write PID file: {e}", file=sys.stderr)
        return None

# Write PID file on startup
pid_file = write_pid_file()
if pid_file:
    print(f"WebSocket Server started with PID file at: {pid_file}", file=sys.stderr)

# Global variables
clients = set()
server_socket = None
server_thread = None
is_running = False
server_instance = None
command_queue = []
response_dict = {}

# Logging functions that work both in and outside of Unreal
def log_info(message):
    print(f"[INFO] {message}", file=sys.stderr)
    if IN_UNREAL:
        try:
            unreal.log(f"[WebSocket] {message}")
        except:
            pass

def log_warning(message):
    print(f"[WARNING] {message}", file=sys.stderr)
    if IN_UNREAL:
        try:
            unreal.log_warning(f"[WebSocket] {message}")
        except:
            pass

def log_error(message, include_traceback=False):
    if include_traceback:
        print(f"[ERROR] {message}\n{traceback.format_exc()}", file=sys.stderr)
        if IN_UNREAL:
            try:
                unreal.log_error(f"[WebSocket] {message}\n{traceback.format_exc()}")
            except:
                pass
    else:
        print(f"[ERROR] {message}", file=sys.stderr)
        if IN_UNREAL:
            try:
                unreal.log_error(f"[WebSocket] {message}")
            except:
                pass

# Command dispatcher class
class CommandDispatcher:
    """
    Dispatches commands to appropriate handlers based on command type
    """
    def __init__(self):
        # Register command handlers
        self.handlers = {
            "handshake": self._handle_handshake,
            "ping": self._handle_ping,
        }

        if HANDLERS_AVAILABLE:
            # Basic object commands
            self.handlers.update({
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

                # Bulk commands
                "add_nodes_bulk": blueprint_commands.handle_add_nodes_bulk,
                "connect_nodes_bulk": blueprint_commands.handle_connect_nodes_bulk,

                # Python and console
                "execute_python": python_commands.handle_execute_python,
                "execute_unreal_command": python_commands.handle_execute_unreal_command,

                # Component and property editing
                "edit_component_property": actor_commands.handle_edit_component_property,
                "add_component_with_events": actor_commands.handle_add_component_with_events,

                # UI commands
                "add_widget_to_user_widget": ui_commands.handle_add_widget_to_user_widget,
                "edit_widget_property": ui_commands.handle_edit_widget_property,
            })

    def dispatch(self, command):
        """Dispatch command to appropriate handler"""
        command_type = command.get("type")
        if command_type not in self.handlers:
            return {"success": False, "error": f"Unknown command type: {command_type}"}

        try:
            handler = self.handlers[command_type]
            return handler(command)
        except Exception as e:
            log_error(f"Error processing command: {str(e)}")
            return {"success": False, "error": str(e)}

    def _handle_handshake(self, command):
        """Built-in handler for handshake command"""
        message = command.get("message", "")
        log_info(f"Handshake received: {message}")

        # Get Unreal Engine version if available
        engine_version = "Unknown"
        if IN_UNREAL:
            try:
                engine_version = unreal.SystemLibrary.get_engine_version()
            except:
                pass

        # Add connection and session information
        connection_info = {
            "status": "Connected via WebSocket",
            "engine_version": engine_version,
            "timestamp": time.time(),
            "session_id": f"WS-UE-{int(time.time())}"
        }

        return {
            "success": True,
            "message": f"Received: {message}",
            "connection_info": connection_info
        }

    def _handle_ping(self, command):
        """Built-in handler for ping command"""
        timestamp = command.get("timestamp", time.time())
        log_info(f"Ping received with timestamp: {timestamp}")

        return {
            "success": True,
            "type": "pong",
            "timestamp": timestamp,
            "server_time": time.time(),
            "message": "Pong from WebSocket server"
        }

# Create global dispatcher instance
dispatcher = CommandDispatcher()

# Process commands on the main thread
def process_commands():
    """Process commands on the main thread"""
    if not command_queue:
        return

    command_id, command = command_queue.pop(0)
    log_info(f"Processing command on main thread: {command}")

    try:
        response = dispatcher.dispatch(command)
        response_dict[command_id] = response
    except Exception as e:
        log_error(f"Error processing command: {str(e)}", include_traceback=True)
        response_dict[command_id] = {"success": False, "error": str(e)}

# WebSocket handshake
def handshake(client_socket):
    """Perform WebSocket handshake with CORS support"""
    try:
        data = client_socket.recv(1024).decode('utf-8')
        if not data:
            return False

        # Extract the WebSocket key
        import re
        import hashlib
        import base64

        key = re.search(r'Sec-WebSocket-Key: (.*)\r\n', data)
        if not key:
            log_error("No WebSocket key found in handshake")
            return False

        # Create the WebSocket accept key
        websocket_key = key.group(1)
        websocket_accept = base64.b64encode(
            hashlib.sha1((websocket_key + '258EAFA5-E914-47DA-95CA-C5AB0DC85B11').encode()).digest()
        ).decode('utf-8')

        # Check for Origin header to implement CORS
        origin = re.search(r'Origin: (.*)\r\n', data)
        origin_value = origin.group(1) if origin else "*"

        # Send the handshake response with CORS headers
        response = (
            'HTTP/1.1 101 Switching Protocols\r\n'
            'Upgrade: websocket\r\n'
            'Connection: Upgrade\r\n'
            f'Sec-WebSocket-Accept: {websocket_accept}\r\n'
            f'Access-Control-Allow-Origin: {origin_value}\r\n'
            'Access-Control-Allow-Credentials: true\r\n'
            'Access-Control-Allow-Headers: content-type\r\n\r\n'
        )
        client_socket.send(response.encode())

        log_info("WebSocket handshake successful")
        return True
    except Exception as e:
        log_error(f"Error during WebSocket handshake: {str(e)}", include_traceback=True)
        return False

# WebSocket frame decoding
def decode_websocket_frame(data):
    """Decode a WebSocket frame"""
    try:
        if len(data) < 2:
            return None

        # Get the first byte
        first_byte = data[0]
        fin = (first_byte & 0x80) != 0
        opcode = first_byte & 0x0F

        # Get the second byte
        second_byte = data[1]
        mask = (second_byte & 0x80) != 0
        payload_length = second_byte & 0x7F

        # Determine the payload length
        import struct

        data_index = 2
        if payload_length == 126:
            if len(data) < 4:
                return None
            payload_length = struct.unpack('>H', data[2:4])[0]
            data_index = 4
        elif payload_length == 127:
            if len(data) < 10:
                return None
            payload_length = struct.unpack('>Q', data[2:10])[0]
            data_index = 10

        # Get the masking key
        if mask:
            if len(data) < data_index + 4:
                return None
            masking_key = data[data_index:data_index+4]
            data_index += 4
        else:
            masking_key = None

        # Get the payload
        if len(data) < data_index + payload_length:
            return None
        payload = data[data_index:data_index+payload_length]

        # Unmask the payload
        if mask:
            unmasked = bytearray(payload_length)
            for i in range(payload_length):
                unmasked[i] = payload[i] ^ masking_key[i % 4]
            payload = bytes(unmasked)

        # Return the decoded frame
        return {
            'fin': fin,
            'opcode': opcode,
            'mask': mask,
            'payload_length': payload_length,
            'masking_key': masking_key,
            'payload': payload,
            'bytes_read': data_index + payload_length
        }
    except Exception as e:
        log_error(f"Error decoding WebSocket frame: {str(e)}", include_traceback=True)
        return None

# WebSocket frame encoding
def encode_websocket_frame(payload, opcode=1):
    """Encode a WebSocket frame"""
    try:
        import struct

        # First byte: FIN bit (1) + opcode (4 bits)
        first_byte = 0x80 | opcode

        # Second byte: MASK bit (0) + payload length (7 bits)
        payload_length = len(payload)
        if payload_length <= 125:
            second_byte = payload_length
            header = bytes([first_byte, second_byte])
        elif payload_length <= 65535:
            second_byte = 126
            header = bytes([first_byte, second_byte]) + struct.pack('>H', payload_length)
        else:
            second_byte = 127
            header = bytes([first_byte, second_byte]) + struct.pack('>Q', payload_length)

        # Return the encoded frame
        return header + payload
    except Exception as e:
        log_error(f"Error encoding WebSocket frame: {str(e)}", include_traceback=True)
        return None

# Handle client connection
def handle_client(client_socket, client_address):
    """Handle a client connection"""
    try:
        # Perform WebSocket handshake
        if not handshake(client_socket):
            client_socket.close()
            return

        # Add the client to the list of connected clients
        clients.add(client_socket)
        client_id = f"client-{id(client_socket)}"
        log_info(f"🟢 Client connected: {client_id} from {client_address}")

        # Handle client messages
        buffer = bytearray()
        while True:
            try:
                # Receive data
                data = client_socket.recv(1024)
                if not data:
                    break

                # Add data to buffer
                buffer.extend(data)

                # Process frames in buffer
                while len(buffer) > 0:
                    frame = decode_websocket_frame(buffer)
                    if not frame:
                        break

                    # Remove processed data from buffer
                    buffer = buffer[frame['bytes_read']:]

                    # Handle different opcodes
                    if frame['opcode'] == 0x8:  # Close
                        log_info(f"Close frame received from {client_id}")
                        client_socket.close()
                        break
                    elif frame['opcode'] == 0x9:  # Ping
                        log_info(f"Ping received from {client_id}")
                        # Send pong
                        pong_frame = encode_websocket_frame(frame['payload'], opcode=0xA)
                        client_socket.send(pong_frame)
                    elif frame['opcode'] == 0xA:  # Pong
                        log_info(f"Pong received from {client_id}")
                    elif frame['opcode'] == 0x1:  # Text
                        # Process text message
                        message = frame['payload'].decode('utf-8')
                        log_info(f"Message received from {client_id}: {message}")

                        # Handle the message
                        if message.endswith('\n'):
                            message = message[:-1]  # Remove trailing newline

                        try:
                            # Parse JSON
                            command = json.loads(message)

                            # Handle handshake directly
                            if command.get("type") == "handshake":
                                response = dispatcher.dispatch(command)
                                response_json = json.dumps(response) + '\n'
                                response_frame = encode_websocket_frame(response_json.encode('utf-8'))
                                client_socket.send(response_frame)
                            # Handle ping directly
                            elif command.get("type") == "ping":
                                response = dispatcher.dispatch(command)
                                response_json = json.dumps(response) + '\n'
                                response_frame = encode_websocket_frame(response_json.encode('utf-8'))
                                client_socket.send(response_frame)
                            else:
                                # Queue other commands for processing
                                command_id = f"{client_id}-{time.time()}"
                                command_queue.append((command_id, command))

                                # Wait for the response with a timeout
                                timeout = 10  # seconds
                                start_time = time.time()

                                while time.time() - start_time < timeout:
                                    if command_id in response_dict:
                                        response = response_dict.pop(command_id)
                                        response_json = json.dumps(response) + '\n'
                                        response_frame = encode_websocket_frame(response_json.encode('utf-8'))
                                        client_socket.send(response_frame)
                                        break

                                    # Process commands while waiting
                                    process_commands()
                                    time.sleep(0.1)
                                else:
                                    # Timeout occurred
                                    error_response = {
                                        "success": False,
                                        "error": f"Command processing timeout after {timeout} seconds"
                                    }
                                    response_json = json.dumps(error_response) + '\n'
                                    response_frame = encode_websocket_frame(response_json.encode('utf-8'))
                                    client_socket.send(response_frame)
                        except json.JSONDecodeError as e:
                            log_error(f"Invalid JSON from {client_id}: {str(e)}")
                            error_response = {
                                "success": False,
                                "error": f"Invalid JSON: {str(e)}"
                            }
                            response_json = json.dumps(error_response) + '\n'
                            response_frame = encode_websocket_frame(response_json.encode('utf-8'))
                            client_socket.send(response_frame)
                        except Exception as e:
                            log_error(f"Error handling message from {client_id}: {str(e)}", include_traceback=True)
                            error_response = {
                                "success": False,
                                "error": str(e)
                            }
                            response_json = json.dumps(error_response) + '\n'
                            response_frame = encode_websocket_frame(response_json.encode('utf-8'))
                            client_socket.send(response_frame)
            except socket.timeout:
                # Process any pending commands
                process_commands()
                continue
            except Exception as e:
                log_error(f"Error handling client {client_id}: {str(e)}", include_traceback=True)
                break

        # Remove client from list
        clients.discard(client_socket)
        log_info(f"🔴 Client disconnected: {client_id}")
    except Exception as e:
        log_error(f"Error in handle_client: {str(e)}", include_traceback=True)
        clients.discard(client_socket)

# Server thread function
def server_thread_function():
    """Server thread function"""
    global server_socket, is_running

    try:
        # Create server socket
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # Bind to port
        host = "0.0.0.0"  # Listen on all interfaces to allow external connections
        port = 9877

        # Try to bind to the port
        try:
            server_socket.bind((host, port))
        except OSError as e:
            if e.errno == 10048:  # Address already in use
                log_warning(f"Port {port} is already in use. Trying to close existing connections...")

                # Try to close any existing connections
                for client in list(clients):
                    try:
                        client.close()
                    except:
                        pass
                clients.clear()

                # Try to bind again
                server_socket.bind((host, port))
            else:
                raise

        # Listen for connections
        server_socket.listen(5)
        server_socket.settimeout(1.0)  # 1 second timeout for accept

        log_info(f"🟢 WebSocket server started on {host}:{port}")
        is_running = True

        # Accept connections
        while is_running:
            try:
                client_socket, client_address = server_socket.accept()
                client_socket.settimeout(1.0)  # 1 second timeout for recv

                # Start a new thread to handle the client
                client_thread = threading.Thread(
                    target=handle_client,
                    args=(client_socket, client_address),
                    daemon=True
                )
                client_thread.start()
            except socket.timeout:
                # Process any pending commands
                process_commands()
                continue
            except Exception as e:
                if is_running:
                    log_error(f"Error accepting connection: {str(e)}", include_traceback=True)
    except Exception as e:
        log_error(f"Error in server thread: {str(e)}", include_traceback=True)
    finally:
        # Close server socket
        if server_socket:
            server_socket.close()
            server_socket = None

        is_running = False
        log_info("WebSocket server stopped")

# Start the server
def start_server():
    """Start the WebSocket server"""
    global server_thread, is_running, server_instance

    try:
        log_info("🟢 Starting WebSocket server...")

        # Start the server thread
        server_thread = threading.Thread(
            target=server_thread_function,
            daemon=True
        )
        server_thread.start()

        # Set server instance
        server_instance = True

        # Wait a moment for the server to start
        time.sleep(0.5)

        if is_running:
            log_info("✅ WebSocket server started successfully")
            return True
        else:
            log_info("❌ WebSocket server failed to start")
            return False
    except Exception as e:
        log_error(f"Error starting WebSocket server: {str(e)}", include_traceback=True)
        return False

# Stop the server
def stop_server():
    """Stop the WebSocket server"""
    global server_socket, server_thread, is_running, server_instance

    try:
        # Set running flag to False
        is_running = False

        # Close all client connections
        for client in list(clients):
            try:
                client.close()
            except:
                pass
        clients.clear()

        # Wait for server thread to exit
        if server_thread and server_thread.is_alive():
            server_thread.join(timeout=2.0)

        server_thread = None
        server_instance = None

        log_info("WebSocket server stopped")
        return True
    except Exception as e:
        log_error(f"Error stopping WebSocket server: {str(e)}", include_traceback=True)
        return False

# Check if the server is running
def is_server_running():
    """Check if the WebSocket server is running"""
    global is_running
    return is_running

# Start the server when this script is run
if __name__ == "__main__":
    start_server()

    # Keep the script running
    try:
        while is_running:
            # Process any pending commands
            process_commands()
            time.sleep(1)
    except KeyboardInterrupt:
        log_info("Stopping WebSocket server...")
        stop_server()
