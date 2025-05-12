#!/usr/bin/env python3
"""
MCP Server with WebSocket support for Unreal Engine.
This script starts a WebSocket server on port 9877 and dispatches incoming JSON messages
to a FastMCP instance with tool handlers defined in mcp_tools.py.
"""

import socket
import json
import sys
import os
import threading
import time
import traceback
import struct
import hashlib
import base64
import re
import signal
from pathlib import Path

# Import logging and authentication modules
import websocket_logging as log
import websocket_auth as auth

# Import tools
import mcp_tools  # This imports all the tool functions and registers them with the FastMCP instance

# Get the MCP instance from mcp_tools
mcp = mcp_tools.mcp

# Global variables
clients = set()
server_socket = None
server_thread = None
is_running = False
server_instance = None

# Create a PID file to let the Unreal plugin know this process is running
def write_pid_file():
    """Write a PID file to let the Unreal plugin know this process is running"""
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
        log.log_error(f"Failed to write PID file: {e}", include_traceback=True)
        return None

# WebSocket handshake
def handshake(client_socket):
    """Perform WebSocket handshake"""
    try:
        data = client_socket.recv(1024).decode('utf-8')
        if not data:
            return False

        # Extract the WebSocket key
        key = re.search(r'Sec-WebSocket-Key: (.*)\r\n', data)
        if not key:
            log.log_error("No WebSocket key found in handshake")
            return False

        # Extract the auth token
        auth_header = re.search(r'Authorization: Bearer (.*)\r\n', data)
        if auth_header:
            token = auth_header.group(1)
            if not auth.validate_token(token):
                log.log_error("Invalid auth token")
                return False
        else:
            # Check if authentication is required
            if len(auth.get_auth_tokens()) > 0:
                log.log_error("No auth token provided")
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

        log.log_info("WebSocket handshake successful")
        return True
    except Exception as e:
        log.log_error(f"Error during WebSocket handshake: {str(e)}", include_traceback=True)
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
        log.log_error(f"Error decoding WebSocket frame: {str(e)}", include_traceback=True)
        return None


# WebSocket frame encoding
def encode_websocket_frame(payload, opcode=1):
    """Encode a WebSocket frame"""
    try:
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
        log.log_error(f"Error encoding WebSocket frame: {str(e)}", include_traceback=True)
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
        log.log_info(f"🟢 Client connected: {client_id} from {client_address}")

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
                        log.log_info(f"Close frame received from {client_id}")
                        client_socket.close()
                        break
                    elif frame['opcode'] == 0x9:  # Ping
                        log.log_debug(f"Ping received from {client_id}")
                        # Send pong
                        pong_frame = encode_websocket_frame(frame['payload'], opcode=0xA)
                        client_socket.send(pong_frame)
                    elif frame['opcode'] == 0xA:  # Pong
                        log.log_debug(f"Pong received from {client_id}")
                    elif frame['opcode'] == 0x1:  # Text
                        # Process text message
                        message = frame['payload'].decode('utf-8')
                        log.log_info(f"Message received from {client_id}: {message}")

                        # Handle the message
                        if message.endswith('\n'):
                            message = message[:-1]  # Remove trailing newline

                        try:
                            # Parse JSON
                            command = json.loads(message)

                            # Handle handshake test
                            if command.get("name") == "handshake_test":
                                # Create a handshake command
                                handshake_command = {
                                    "type": "handshake",
                                    "message": command.get("args", {}).get("message", "Hello from client")
                                }

                                # Dispatch to FastMCP
                                response = mcp.dispatch(handshake_command)
                            else:
                                # Dispatch to FastMCP
                                response = mcp.dispatch(command)

                            # Send response
                            response_json = json.dumps(response) + '\n'
                            response_frame = encode_websocket_frame(response_json.encode('utf-8'))
                            client_socket.send(response_frame)

                        except json.JSONDecodeError as e:
                            log.log_error(f"Invalid JSON from {client_id}: {str(e)}")
                            error_response = {
                                "success": False,
                                "error": f"Invalid JSON: {str(e)}"
                            }
                            response_json = json.dumps(error_response) + '\n'
                            response_frame = encode_websocket_frame(response_json.encode('utf-8'))
                            client_socket.send(response_frame)
                        except Exception as e:
                            log.log_error(f"Error handling message from {client_id}: {str(e)}", include_traceback=True)
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
                log.log_error(f"Error handling client {client_id}: {str(e)}", include_traceback=True)
                break

        # Remove client from list
        clients.discard(client_socket)
        log.log_info(f"🔴 Client disconnected: {client_id}")
    except Exception as e:
        log.log_error(f"Error in handle_client: {str(e)}", include_traceback=True)
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
        host = "0.0.0.0"  # Listen on all interfaces
        port = 9877

        # Try to bind to the port
        try:
            server_socket.bind((host, port))
        except OSError as e:
            if e.errno == 10048:  # Address already in use
                log.log_warning(f"Port {port} is already in use. Trying to close existing connections...")

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

        log.log_info(f"🟢 WebSocket server started on {host}:{port}")
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
                    log.log_error(f"Error accepting connection: {str(e)}", include_traceback=True)
    except Exception as e:
        log.log_error(f"Error in server thread: {str(e)}", include_traceback=True)
    finally:
        # Close server socket
        if server_socket:
            server_socket.close()
            server_socket = None

        is_running = False
        log.log_info("WebSocket server stopped")


# Start the server
def start_server():
    """Start the WebSocket server"""
    global server_thread, is_running

    try:
        log.log_info("🟢 Starting WebSocket server...")

        # Start the server thread
        server_thread = threading.Thread(
            target=server_thread_function,
            daemon=True
        )
        server_thread.start()

        # Wait a moment for the server to start
        time.sleep(0.5)

        if is_running:
            log.log_info("✅ WebSocket server started successfully")
            return True
        else:
            log.log_error("❌ WebSocket server failed to start")
            return False
    except Exception as e:
        log.log_error(f"Error starting WebSocket server: {str(e)}", include_traceback=True)
        return False


# Stop the server
def stop_server():
    """Stop the WebSocket server"""
    global server_socket, server_thread, is_running

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

        log.log_info("WebSocket server stopped")
        return True
    except Exception as e:
        log.log_error(f"Error stopping WebSocket server: {str(e)}", include_traceback=True)
        return False


# Handle signals for clean shutdown
def signal_handler(sig, frame):  # pylint: disable=unused-argument
    """Handle signals for clean shutdown"""
    log.log_info("Received signal, shutting down...")
    stop_server()
    sys.exit(0)


# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


# No-op function for compatibility
def process_commands():
    """No-op function for compatibility"""
    pass


# Main function
def main():
    """Main function"""
    try:
        # Write PID file
        pid_file = write_pid_file()
        if pid_file:
            log.log_info(f"MCP Server started with PID file at: {pid_file}")

        # Start the server
        start_server()

        # Keep the script running
        try:
            while is_running:
                # Process commands on the main thread
                process_commands()

                # Sleep to avoid high CPU usage
                time.sleep(0.1)
        except KeyboardInterrupt:
            log.log_info("Stopping WebSocket server...")
            stop_server()
    except Exception as e:
        log.log_error(f"Error in main function: {str(e)}", include_traceback=True)
        return 1

    return 0


# Write PID file on startup
pid_file = write_pid_file()
if pid_file:
    log.log_info(f"MCP Server started with PID file at: {pid_file}")


# Start the server when this script is run
if __name__ == "__main__":
    sys.exit(main())