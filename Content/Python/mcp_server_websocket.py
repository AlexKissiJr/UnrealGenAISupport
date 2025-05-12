import socket
import json
import sys
import os
import threading
import time
import traceback
from pathlib import Path

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

# WebSocket handshake
def handshake(client_socket):
    """Perform WebSocket handshake"""
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
            print("No WebSocket key found in handshake", file=sys.stderr)
            return False
            
        # Create the WebSocket accept key
        websocket_key = key.group(1)
        websocket_accept = base64.b64encode(
            hashlib.sha1((websocket_key + '258EAFA5-E914-47DA-95CA-C5AB0DC85B11').encode()).digest()
        ).decode('utf-8')
        
        # Send the handshake response
        response = (
            'HTTP/1.1 101 Switching Protocols\r\n'
            'Upgrade: websocket\r\n'
            'Connection: Upgrade\r\n'
            f'Sec-WebSocket-Accept: {websocket_accept}\r\n\r\n'
        )
        client_socket.send(response.encode())
        
        print("WebSocket handshake successful", file=sys.stderr)
        return True
    except Exception as e:
        print(f"Error during WebSocket handshake: {str(e)}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
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
        print(f"Error decoding WebSocket frame: {str(e)}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
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
        print(f"Error encoding WebSocket frame: {str(e)}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
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
        print(f"🟢 Client connected: {client_id} from {client_address}", file=sys.stderr)
        
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
                        print(f"Close frame received from {client_id}", file=sys.stderr)
                        client_socket.close()
                        break
                    elif frame['opcode'] == 0x9:  # Ping
                        print(f"Ping received from {client_id}", file=sys.stderr)
                        # Send pong
                        pong_frame = encode_websocket_frame(frame['payload'], opcode=0xA)
                        client_socket.send(pong_frame)
                    elif frame['opcode'] == 0xA:  # Pong
                        print(f"Pong received from {client_id}", file=sys.stderr)
                    elif frame['opcode'] == 0x1:  # Text
                        # Process text message
                        message = frame['payload'].decode('utf-8')
                        print(f"Message received from {client_id}: {message}", file=sys.stderr)
                        
                        # Handle the message
                        if message.endswith('\n'):
                            message = message[:-1]  # Remove trailing newline
                            
                        try:
                            # Parse JSON
                            command = json.loads(message)
                            
                            # Handle handshake directly
                            if command.get("type") == "handshake":
                                response = {
                                    "success": True,
                                    "message": f"Handshake received: {command.get('message', '')}",
                                    "connection_info": {
                                        "status": "Connected via WebSocket",
                                        "timestamp": time.time(),
                                        "session_id": f"WS-UE-{int(time.time())}"
                                    }
                                }
                                response_json = json.dumps(response) + '\n'
                                response_frame = encode_websocket_frame(response_json.encode('utf-8'))
                                client_socket.send(response_frame)
                            # Handle ping directly
                            elif command.get("type") == "ping":
                                response = {
                                    "type": "pong",
                                    "timestamp": command.get("timestamp", 0),
                                    "server_time": time.time(),
                                    "message": "Pong from WebSocket server"
                                }
                                response_json = json.dumps(response) + '\n'
                                response_frame = encode_websocket_frame(response_json.encode('utf-8'))
                                client_socket.send(response_frame)
                            else:
                                # Echo other messages
                                command["echo"] = True
                                command["echo_message"] = "This is an echo from the server"
                                response_json = json.dumps(command) + '\n'
                                response_frame = encode_websocket_frame(response_json.encode('utf-8'))
                                client_socket.send(response_frame)
                        except json.JSONDecodeError as e:
                            print(f"Invalid JSON from {client_id}: {str(e)}", file=sys.stderr)
                            error_response = {
                                "success": False,
                                "error": f"Invalid JSON: {str(e)}"
                            }
                            response_json = json.dumps(error_response) + '\n'
                            response_frame = encode_websocket_frame(response_json.encode('utf-8'))
                            client_socket.send(response_frame)
                        except Exception as e:
                            print(f"Error handling message from {client_id}: {str(e)}", file=sys.stderr)
                            traceback.print_exc(file=sys.stderr)
                            error_response = {
                                "success": False,
                                "error": str(e)
                            }
                            response_json = json.dumps(error_response) + '\n'
                            response_frame = encode_websocket_frame(response_json.encode('utf-8'))
                            client_socket.send(response_frame)
            except socket.timeout:
                continue
            except Exception as e:
                print(f"Error handling client {client_id}: {str(e)}", file=sys.stderr)
                traceback.print_exc(file=sys.stderr)
                break
                
        # Remove client from list
        clients.discard(client_socket)
        print(f"🔴 Client disconnected: {client_id}", file=sys.stderr)
    except Exception as e:
        print(f"Error in handle_client: {str(e)}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
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
        host = "localhost"
        port = 9877
        
        # Try to bind to the port
        try:
            server_socket.bind((host, port))
        except OSError as e:
            if e.errno == 10048:  # Address already in use
                print(f"Port {port} is already in use. Trying to close existing connections...", file=sys.stderr)
                
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
        
        print(f"🟢 WebSocket server started on {host}:{port}", file=sys.stderr)
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
                continue
            except Exception as e:
                if is_running:
                    print(f"Error accepting connection: {str(e)}", file=sys.stderr)
                    traceback.print_exc(file=sys.stderr)
    except Exception as e:
        print(f"Error in server thread: {str(e)}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
    finally:
        # Close server socket
        if server_socket:
            server_socket.close()
            server_socket = None
        
        is_running = False
        print("WebSocket server stopped", file=sys.stderr)

# Start the server
def start_server():
    """Start the WebSocket server"""
    global server_thread, is_running, server_instance
    
    try:
        print("🟢 Starting WebSocket server...", file=sys.stderr)
        
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
            print("✅ WebSocket server started successfully", file=sys.stderr)
            return True
        else:
            print("❌ WebSocket server failed to start", file=sys.stderr)
            return False
    except Exception as e:
        print(f"Error starting WebSocket server: {str(e)}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
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
        
        print("WebSocket server stopped", file=sys.stderr)
        return True
    except Exception as e:
        print(f"Error stopping WebSocket server: {str(e)}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
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
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping WebSocket server...", file=sys.stderr)
        stop_server()
