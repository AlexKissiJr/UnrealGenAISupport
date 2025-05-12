"""
Standalone WebSocket server for Unreal Engine.
This script creates a simple WebSocket server directly without using subprocess.
"""

import unreal
import socket
import threading
import time
import traceback
import json
import struct
import hashlib
import base64
import re

# Global variables
clients = set()
server_socket = None
server_thread = None
is_running = False

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
            unreal.log_error("No WebSocket key found in handshake")
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

        unreal.log("WebSocket handshake successful")
        return True
    except Exception as e:
        unreal.log_error(f"Error during WebSocket handshake: {str(e)}")
        unreal.log_error(traceback.format_exc())
        return False

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
        unreal.log_error(f"Error encoding WebSocket frame: {str(e)}")
        unreal.log_error(traceback.format_exc())
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
        unreal.log(f"🟢 Client connected: {client_id} from {client_address}")

        # Send a welcome message
        welcome_message = {
            "type": "welcome",
            "message": "Welcome to the Unreal Engine WebSocket server!",
            "server_time": time.time()
        }
        welcome_json = json.dumps(welcome_message)
        welcome_frame = encode_websocket_frame(welcome_json.encode('utf-8'))
        client_socket.send(welcome_frame)

        # Keep the connection open
        while is_running:
            try:
                # Sleep briefly
                time.sleep(0.1)
            except Exception as e:
                unreal.log_error(f"Error in client loop: {str(e)}")
                break

        # Remove client from list
        clients.discard(client_socket)
        unreal.log(f"🔴 Client disconnected: {client_id}")
    except Exception as e:
        unreal.log_error(f"Error in handle_client: {str(e)}")
        unreal.log_error(traceback.format_exc())
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
        server_socket.bind((host, port))

        # Listen for connections
        server_socket.listen(5)
        server_socket.settimeout(1.0)  # 1 second timeout for accept

        unreal.log(f"🟢 WebSocket server started on {host}:{port}")
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
                    unreal.log_error(f"Error accepting connection: {str(e)}")
                    unreal.log_error(traceback.format_exc())
    except Exception as e:
        unreal.log_error(f"Error in server thread: {str(e)}")
        unreal.log_error(traceback.format_exc())
    finally:
        # Close server socket
        if server_socket:
            server_socket.close()
            server_socket = None

        is_running = False
        unreal.log("WebSocket server stopped")

# Start the server
def start_server():
    """Start the WebSocket server"""
    global server_thread, is_running

    try:
        unreal.log("Starting standalone WebSocket server...")

        # Check if server is already running
        if is_running and server_thread and server_thread.is_alive():
            unreal.log("WebSocket server is already running")
            return True

        # Start the server thread
        server_thread = threading.Thread(
            target=server_thread_function,
            daemon=True
        )
        server_thread.start()

        # Wait for the server to start
        time.sleep(0.5)

        if is_running:
            unreal.log("✅ WebSocket server started successfully")
            return True
        else:
            unreal.log_error("❌ WebSocket server failed to start")
            return False
    except Exception as e:
        unreal.log_error(f"Error starting WebSocket server: {str(e)}")
        unreal.log_error(traceback.format_exc())
        return False

# Stop the server
def stop_server():
    """Stop the WebSocket server"""
    global server_socket, server_thread, is_running

    try:
        # Check if server is already stopped
        if not is_running:
            unreal.log("WebSocket server is already stopped")
            return True

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

        unreal.log("WebSocket server stopped")
        return True
    except Exception as e:
        unreal.log_error(f"Error stopping WebSocket server: {str(e)}")
        unreal.log_error(traceback.format_exc())
        return False

# Test the server
def test():
    """Test the WebSocket server"""
    try:
        unreal.log("Testing standalone WebSocket server...")

        # Start the server
        if start_server():
            unreal.log("Server started successfully")

            # Wait briefly
            time.sleep(5)

            # Stop the server
            if stop_server():
                unreal.log("Server stopped successfully")
                return True
            else:
                unreal.log_error("Failed to stop server")
                return False
        else:
            unreal.log_error("Failed to start server")
            return False
    except Exception as e:
        unreal.log_error(f"Error testing WebSocket server: {str(e)}")
        unreal.log_error(traceback.format_exc())
        return False

# Run the test function
if __name__ == "__main__":
    test()
