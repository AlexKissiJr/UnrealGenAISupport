#!/usr/bin/env python3
"""
Test script for non-blocking WebSocket server.
This script tests the non-blocking WebSocket server to ensure it doesn't freeze Unreal Engine.
"""

import sys
import time
import threading
import traceback
import json

# Import the non-blocking WebSocket server
import unreal_websocket_nonblocking as websocket

# Global variables
is_running = True
test_thread = None

# Test thread function
def test_thread_function():
    """Test thread function"""
    global is_running
    
    try:
        print("Starting WebSocket server test thread...")
        
        # Start the server
        print("Starting WebSocket server...")
        success = websocket.start()
        
        if success:
            print("✅ WebSocket server started successfully")
        else:
            print("❌ Failed to start WebSocket server")
            return
            
        # Get the server status
        print("Getting WebSocket server status...")
        status_json = websocket.status()
        status = json.loads(status_json)
        print(f"WebSocket server status: {status}")
        
        # Wait for a while
        print("Waiting for 10 seconds...")
        for i in range(10):
            if not is_running:
                break
                
            print(f"Waiting... {i+1}/10")
            time.sleep(1)
            
        # Stop the server
        print("Stopping WebSocket server...")
        success = websocket.stop()
        
        if success:
            print("✅ WebSocket server stopped successfully")
        else:
            print("❌ Failed to stop WebSocket server")
            
        print("WebSocket server test thread completed")
    except Exception as e:
        print(f"Error in WebSocket server test thread: {str(e)}")
        traceback.print_exc()
    finally:
        is_running = False

# Main function
def main():
    """Main function"""
    global test_thread, is_running
    
    try:
        # Start the test thread
        is_running = True
        test_thread = threading.Thread(
            target=test_thread_function,
            daemon=True,
            name="WebSocketTestThread"
        )
        test_thread.start()
        
        # Wait for the test thread to complete
        print("Waiting for test thread to complete...")
        while is_running:
            # This is the main thread, which simulates Unreal Engine's main thread
            # It should not be blocked by the WebSocket server
            print("Main thread is still running (this simulates Unreal Engine's main thread)")
            time.sleep(1)
            
        print("Test completed successfully")
        return 0
    except KeyboardInterrupt:
        print("Test interrupted by user")
        is_running = False
        return 1
    except Exception as e:
        print(f"Error in main function: {str(e)}")
        traceback.print_exc()
        is_running = False
        return 1

# Run the main function
if __name__ == "__main__":
    sys.exit(main())
