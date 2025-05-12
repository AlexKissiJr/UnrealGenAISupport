#!/usr/bin/env python

import asyncio
import websockets
import json
import logging
import sys
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger('websocket_test')

async def test_websocket_connection():
    """Test WebSocket connection to the server"""
    uri = "ws://localhost:9877"
    logger.info(f"Connecting to {uri}...")
    
    try:
        async with websockets.connect(uri) as websocket:
            logger.info("Connected to WebSocket server")
            
            # Send a handshake message
            handshake_message = {
                "type": "handshake",
                "message": "Hello from test script"
            }
            
            logger.info(f"Sending handshake message: {handshake_message}")
            await websocket.send(json.dumps(handshake_message) + '\n')
            
            # Wait for the response
            logger.info("Waiting for response...")
            response = await websocket.recv()
            
            # Parse the response
            if response.endswith('\n'):
                response = response[:-1]  # Remove trailing newline
                
            response_json = json.loads(response)
            logger.info(f"Received response: {response_json}")
            
            # Send a ping message
            ping_message = {
                "type": "ping",
                "timestamp": time.time()
            }
            
            logger.info(f"Sending ping message: {ping_message}")
            await websocket.send(json.dumps(ping_message) + '\n')
            
            # Wait for the response
            logger.info("Waiting for response...")
            response = await websocket.recv()
            
            # Parse the response
            if response.endswith('\n'):
                response = response[:-1]  # Remove trailing newline
                
            response_json = json.loads(response)
            logger.info(f"Received response: {response_json}")
            
            # Close the connection
            logger.info("Test completed successfully")
            return True
    except Exception as e:
        logger.error(f"Error testing WebSocket connection: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

async def main():
    """Main function"""
    logger.info("Starting WebSocket connection test")
    
    # Test the connection
    success = await test_websocket_connection()
    
    if success:
        logger.info("✅ WebSocket connection test passed")
    else:
        logger.error("❌ WebSocket connection test failed")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Test stopped by user")
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        logger.error(traceback.format_exc())
