#!/usr/bin/env python3
"""
Test script for WebSocket server freezing issue.
This script tests the WebSocket server with multiple clients and messages.
"""

import socket
import json
import sys
import os
import time
import struct
import hashlib
import base64
import re
import random
import string
import threading
import traceback

# Global variables
clients = []
is_running = True
message_count = 0
success_count = 0
error_count = 0

# WebSocket handshake
def perform_handshake(sock):
    """Perform WebSocket handshake"""
    try:
        # Generate a random WebSocket key
        websocket_key = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(16))
        websocket_key = base64.b64encode(websocket_key.encode()).decode()
        
        # Send handshake request
        request = (
            f"GET / HTTP/1.1\r\n"
            f"Host: localhost:9877\r\n"
            f"Upgrade: websocket\r\n"
            f"Connection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {websocket_key}\r\n"
            f"Sec-WebSocket-Version: 13\r\n"
            f"\r\n"
        )
        sock.send(request.encode())
        
        # Receive handshake response
        response = sock.recv(1024).decode()
        
        # Check if handshake was successful
        if "101 Switching Protocols" in response:
            print(f"WebSocket handshake successful for client {id(sock)}")
            return True
        else:
            print(f"WebSocket handshake failed for client {id(sock)}: {response}")
            return False
    except Exception as e:
        print(f"Error during WebSocket handshake for client {id(sock)}: {str(e)}")
        traceback.print_exc()
        return False

# WebSocket frame encoding
def encode_websocket_frame(payload, opcode=1):
    """Encode a WebSocket frame"""
    try:
        # First byte: FIN bit (1) + opcode (4 bits)
        first_byte = 0x80 | opcode
        
        # Second byte: MASK bit (1) + payload length (7 bits)
        payload_length = len(payload)
        if payload_length <= 125:
            second_byte = 0x80 | payload_length
            header = bytes([first_byte, second_byte])
        elif payload_length <= 65535:
            second_byte = 0x80 | 126
            header = bytes([first_byte, second_byte]) + struct.pack('>H', payload_length)
        else:
            second_byte = 0x80 | 127
            header = bytes([first_byte, second_byte]) + struct.pack('>Q', payload_length)
            
        # Generate masking key
        masking_key = os.urandom(4)
        
        # Mask the payload
        masked_payload = bytearray(payload_length)
        for i in range(payload_length):
            masked_payload[i] = payload[i] ^ masking_key[i % 4]
            
        # Return the encoded frame
        return header + masking_key + masked_payload
    except Exception as e:
        print(f"Error encoding WebSocket frame: {str(e)}")
        traceback.print_exc()
        return None

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
        print(f"Error decoding WebSocket frame: {str(e)}")
        traceback.print_exc()
        return None

# Client thread function
def client_thread_function(client_id):
    """Client thread function"""
    global is_running, message_count, success_count, error_count
    
    try:
        # Connect to the server
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5.0)  # 5 second timeout
        sock.connect(('localhost', 9877))
        
        # Perform handshake
        if not perform_handshake(sock):
            sock.close()
            error_count += 1
            return
            
        # Add client to list
        clients.append(sock)
        
        # Send messages
        local_message_count = 0
        while is_running and local_message_count < 10:
            try:
                # Create message
                message = {
                    "name": "handshake_test",
                    "args": {
                        "message": f"Hello from client {client_id}, message {local_message_count}"
                    }
                }
                
                # Send message
                message_json = json.dumps(message)
                frame = encode_websocket_frame(message_json.encode())
                sock.send(frame)
                
                # Receive response
                response_data = sock.recv(8192)
                frame = decode_websocket_frame(response_data)
                if frame:
                    response = frame['payload'].decode()
                    response_json = json.loads(response)
                    if response_json.get("success"):
                        success_count += 1
                    else:
                        error_count += 1
                        print(f"Error response from server: {response}")
                else:
                    error_count += 1
                    print(f"Invalid response from server")
                
                # Increment message count
                local_message_count += 1
                message_count += 1
                
                # Sleep briefly
                time.sleep(0.1)
            except Exception as e:
                error_count += 1
                print(f"Error sending message: {str(e)}")
                traceback.print_exc()
                break
                
        # Close connection
        try:
            sock.close()
        except:
            pass
        
        # Remove client from list
        if sock in clients:
            clients.remove(sock)
            
        print(f"Client {client_id} thread exited after {local_message_count} messages")
    except Exception as e:
        error_count += 1
        print(f"Error in client thread {client_id}: {str(e)}")
        traceback.print_exc()

# Main function
def main():
    """Main function"""
    global is_running, message_count, success_count, error_count
    
    try:
        # Start client threads
        client_threads = []
        for i in range(5):  # 5 clients
            client_thread = threading.Thread(
                target=client_thread_function,
                args=(i,),
                daemon=True
            )
            client_thread.start()
            client_threads.append(client_thread)
            time.sleep(0.5)  # Stagger client connections
            
        # Wait for client threads to exit
        start_time = time.time()
        while time.time() - start_time < 30:  # 30 second timeout
            # Print status
            print(f"Status: {len(clients)} active clients, {message_count} messages, {success_count} successes, {error_count} errors")
            
            # Check if all clients have exited
            if all(not t.is_alive() for t in client_threads):
                break
                
            # Sleep briefly
            time.sleep(1)
            
        # Set running flag to False
        is_running = False
        
        # Close any remaining clients
        for client in list(clients):
            try:
                client.close()
            except:
                pass
        clients.clear()
        
        # Print final status
        print(f"Final status: {message_count} messages, {success_count} successes, {error_count} errors")
        
        return 0
    except Exception as e:
        print(f"Error in main function: {str(e)}")
        traceback.print_exc()
        return 1

# Run the main function
if __name__ == "__main__":
    sys.exit(main())
