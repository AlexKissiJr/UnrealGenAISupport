import unreal
import sys
import os
import time

def log(message):
    """Log info message"""
    unreal.log(f"[WebSocket Test] {message}")

def log_warning(message):
    """Log warning message"""
    unreal.log_warning(f"[WebSocket Test] {message}")

def log_error(message):
    """Log error message"""
    unreal.log_error(f"[WebSocket Test] {message}")

def test_standalone_websocket():
    """Test the standalone WebSocket server"""
    try:
        # Import the standalone WebSocket server
        try:
            import standalone_websocket_server
        except ImportError:
            log_error("Failed to import standalone_websocket_server module")
            return False
        
        log("Successfully imported standalone_websocket_server module")
        
        # Check if the server is already running
        if standalone_websocket_server.is_running:
            log("WebSocket server is already running")
            return True
        
        # Start the server
        log("Starting WebSocket server...")
        success = standalone_websocket_server.initialize_server()
        
        if success:
            log("✅ WebSocket server started successfully")
            
            # Wait a moment for the server to start
            time.sleep(2)
            
            # Check if the server is running
            if standalone_websocket_server.is_running:
                log("✅ WebSocket server is running")
                
                # Test with a WebSocket client
                log("Testing WebSocket client...")
                
                # Create a WebSocket client
                websocket_client = unreal.GenWebSocketManager()
                
                if not websocket_client:
                    log_error("Failed to create WebSocket client")
                    return False
                
                # Initialize the client
                server_url = "ws://localhost:9877"
                log(f"Connecting to WebSocket server at {server_url}...")
                
                # Initialize the client
                success = websocket_client.initialize(server_url)
                
                if success:
                    log("✅ WebSocket client initialized successfully")
                    
                    # Wait for connection
                    time.sleep(2)
                    
                    # Check if connected
                    if websocket_client.is_connected():
                        log("✅ WebSocket client connected successfully")
                        
                        # Send a handshake
                        log("Sending handshake...")
                        websocket_client.send_handshake("Hello from WebSocket client test")
                        
                        # Wait for response
                        time.sleep(2)
                        
                        # Disconnect
                        log("Disconnecting WebSocket client...")
                        websocket_client.shutdown()
                        
                        # Stop the server
                        log("Stopping WebSocket server...")
                        standalone_websocket_server.stop_server()
                        
                        log("✅ WebSocket test completed successfully")
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
        log_error(f"Error testing WebSocket server: {str(e)}")
        import traceback
        log_error(traceback.format_exc())
        return False

# Run the test
if __name__ == "__main__":
    log("Starting standalone WebSocket server test...")
    success = test_standalone_websocket()
    
    if success:
        log("✅ Standalone WebSocket server test passed")
    else:
        log_error("❌ Standalone WebSocket server test failed")

# Function to run from Unreal Engine
def run_test():
    """Run the standalone WebSocket server test"""
    return test_standalone_websocket()
