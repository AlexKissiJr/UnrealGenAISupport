#!/usr/bin/env python3
"""
Comprehensive test script for the WebSocket server.
This script tests all the tool functions available in the WebSocket server.
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
import traceback

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
            print("WebSocket handshake successful")
            return True
        else:
            print(f"WebSocket handshake failed: {response}")
            return False
    except Exception as e:
        print(f"Error during WebSocket handshake: {str(e)}")
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

# Send a message to the server
def send_message(sock, message):
    """Send a message to the server"""
    try:
        # Encode the message
        frame = encode_websocket_frame(message.encode())
        
        # Send the frame
        sock.send(frame)
        
        # Receive the response
        response_data = sock.recv(8192)
        
        # Decode the response
        frame = decode_websocket_frame(response_data)
        if frame:
            return frame['payload'].decode()
        else:
            return None
    except Exception as e:
        print(f"Error sending message: {str(e)}")
        traceback.print_exc()
        return None

# Test a tool function
def test_tool(sock, name, args=None):
    """Test a tool function"""
    try:
        # Create the message
        message = {
            "name": name,
            "args": args or {}
        }
        
        # Send the message
        print(f"\n🧪 Testing tool: {name}")
        print(f"Request: {json.dumps(message, indent=2)}")
        
        response = send_message(sock, json.dumps(message))
        
        # Parse the response
        if response:
            try:
                response_json = json.loads(response)
                print(f"Response: {json.dumps(response_json, indent=2)}")
                return response_json
            except json.JSONDecodeError:
                print(f"Invalid JSON response: {response}")
                return None
        else:
            print("No response received")
            return None
    except Exception as e:
        print(f"Error testing tool {name}: {str(e)}")
        traceback.print_exc()
        return None

# Main function
def main():
    """Main function"""
    try:
        # Connect to the server
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(('localhost', 9877))
        
        # Perform handshake
        if not perform_handshake(sock):
            sock.close()
            return 1
            
        # Test handshake_test
        test_tool(sock, "handshake_test", {"message": "Hello from WebSocket client"})
        
        # Test execute_python_script
        test_tool(sock, "execute_python_script", {"script": "import unreal\nprint('Hello from Python script')\nreturn 'Success'"})
        
        # Test execute_unreal_command
        test_tool(sock, "execute_unreal_command", {"command": "stat fps"})
        
        # Test spawn_object
        test_tool(sock, "spawn_object", {
            "actor_class": "Cube",
            "location": [0, 0, 100],
            "rotation": [0, 0, 0],
            "scale": [1, 1, 1],
            "actor_label": "TestCube"
        })
        
        # Test create_material
        test_tool(sock, "create_material", {
            "material_name": "TestMaterial",
            "color": [1, 0, 0]
        })
        
        # Test create_blueprint
        test_tool(sock, "create_blueprint", {
            "blueprint_name": "BP_Test",
            "parent_class": "Actor",
            "save_path": "/Game/Blueprints"
        })
        
        # Close the connection
        sock.close()
        
        print("\n✅ All tests completed")
        return 0
    except Exception as e:
        print(f"Error in main function: {str(e)}")
        traceback.print_exc()
        return 1

# Run the main function
if __name__ == "__main__":
    sys.exit(main())
