import unreal
import sys
import os
import time

def log_info(message):
    """Log info message"""
    unreal.log(f"[WebSocket Manager Test] {message}")

def log_warning(message):
    """Log warning message"""
    unreal.log_warning(f"[WebSocket Manager Test] {message}")

def log_error(message):
    """Log error message"""
    unreal.log_error(f"[WebSocket Manager Test] {message}")

def test_websocket_manager():
    """Test the WebSocket manager"""
    try:
        # Import the WebSocket manager
        try:
            import websocket_manager
        except ImportError:
            log_error("Failed to import websocket_manager module")
            return False
        
        log_info("Successfully imported websocket_manager module")
        
        # Check if the server is already running
        if websocket_manager.is_server_running():
            log_info("WebSocket server is already running")
            return True
        
        # Start the server
        log_info("Starting WebSocket server...")
        success = websocket_manager.start_server()
        
        if success:
            log_info("✅ WebSocket server started successfully")
            
            # Wait a moment for the server to start
            time.sleep(2)
            
            # Check if the server is running
            if websocket_manager.is_server_running():
                log_info("✅ WebSocket server is running")
                
                # Test with a WebSocket client
                log_info("Testing WebSocket client...")
                
                # Create a WebSocket client
                websocket_client = unreal.GenWebSocketManager()
                
                if not websocket_client:
                    log_error("Failed to create WebSocket client")
                    return False
                
                # Initialize the client
                server_url = websocket_manager.get_server_url()
                log_info(f"Connecting to WebSocket server at {server_url}...")
                
                # Initialize the client
                success = websocket_client.initialize(server_url)
                
                if success:
                    log_info("✅ WebSocket client initialized successfully")
                    
                    # Wait for connection
                    time.sleep(2)
                    
                    # Check if connected
                    if websocket_client.is_connected():
                        log_info("✅ WebSocket client connected successfully")
                        
                        # Send a handshake
                        log_info("Sending handshake...")
                        websocket_client.send_handshake("Hello from WebSocket client test")
                        
                        # Wait for response
                        time.sleep(2)
                        
                        # Disconnect
                        log_info("Disconnecting WebSocket client...")
                        websocket_client.shutdown()
                        
                        # Stop the server
                        log_info("Stopping WebSocket server...")
                        websocket_manager.stop_server()
                        
                        log_info("✅ WebSocket test completed successfully")
                        return True
                    else:
                        log_error("❌ WebSocket client failed to connect")
                        return False
                else:
                    log_error("❌ WebSocket client initialization failed")
                    return False
            else:
                log_error("❌ WebSocket server is not running")
                return False
        else:
            log_error("❌ WebSocket server failed to start")
            return False
    except Exception as e:
        log_error(f"Error testing WebSocket manager: {str(e)}")
        import traceback
        log_error(traceback.format_exc())
        return False

# Run the test
if __name__ == "__main__":
    log_info("Starting WebSocket manager test...")
    success = test_websocket_manager()
    
    if success:
        log_info("✅ WebSocket manager test passed")
    else:
        log_error("❌ WebSocket manager test failed")

# Function to run from Unreal Engine
def run_test():
    """Run the WebSocket manager test"""
    return test_websocket_manager()
