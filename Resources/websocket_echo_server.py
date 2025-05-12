#!/usr/bin/env python

import asyncio
import websockets
import json
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger('websocket_echo_server')

# Set of connected clients
connected_clients = set()

async def echo(websocket, path):
    """Echo server handler"""
    # Register client
    connected_clients.add(websocket)
    client_id = f"client-{id(websocket)}"
    logger.info(f"🟢 Client connected: {client_id}")
    
    try:
        async for message in websocket:
            logger.info(f"Received message from {client_id}: {message}")
            
            # Try to parse as JSON
            try:
                data = json.loads(message)
                
                # Handle handshake
                if data.get("type") == "handshake":
                    response = {
                        "success": True,
                        "message": f"Echo server handshake received: {data.get('message', '')}",
                        "connection_info": {
                            "status": "Connected to Echo Server",
                            "server_type": "Echo Server",
                            "timestamp": import_time(),
                            "session_id": f"ECHO-{int(import_time())}"
                        }
                    }
                    await websocket.send(json.dumps(response) + '\n')
                # Echo other messages
                else:
                    # Add echo field
                    data["echo"] = True
                    data["echo_message"] = "This is an echo from the server"
                    await websocket.send(json.dumps(data) + '\n')
            except json.JSONDecodeError:
                # Not JSON, just echo back
                await websocket.send(message)
    except websockets.exceptions.ConnectionClosed:
        logger.info(f"Connection closed for {client_id}")
    finally:
        # Unregister client
        connected_clients.discard(websocket)
        logger.info(f"🔴 Client disconnected: {client_id}")

def import_time():
    """Import time module and return current time"""
    import time
    return time.time()

async def main():
    """Main function"""
    host = "localhost"
    port = 9877
    
    logger.info(f"Starting WebSocket echo server on {host}:{port}")
    
    # Start the server
    async with websockets.serve(echo, host, port):
        logger.info(f"WebSocket echo server running at ws://{host}:{port}")
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        logger.error(traceback.format_exc())
