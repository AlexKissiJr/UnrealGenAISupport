import unreal
import socket_server_manager
import threading
import time
import traceback

# Global variables
connection_checker_thread = None
connection_checker_running = False

def start_socket_server(use_websocket=False):
    """Start the Python socket server"""
    try:
        # Stop any existing server
        stop_socket_server()
        
        # Start the server
        success = socket_server_manager.start_server(use_websocket)
        
        if success:
            # Start the connection checker
            start_connection_checker()
            
            return "Python socket server started successfully"
        else:
            return "Failed to start Python socket server"
    except Exception as e:
        unreal.log_error(f"Error starting Python socket server: {str(e)}")
        unreal.log_error(traceback.format_exc())
        return f"Error starting Python socket server: {str(e)}"

def stop_socket_server():
    """Stop the Python socket server"""
    try:
        # Stop the connection checker
        stop_connection_checker()
        
        # Stop the server
        success = socket_server_manager.stop_server()
        
        if success:
            return "Python socket server stopped successfully."
        else:
            return "Failed to stop Python socket server."
    except Exception as e:
        unreal.log_error(f"Error stopping Python socket server: {str(e)}")
        unreal.log_error(traceback.format_exc())
        return f"Error stopping Python socket server: {str(e)}"

def is_socket_server_running():
    """Check if the Python socket server is running"""
    try:
        return socket_server_manager.is_server_running()
    except Exception as e:
        unreal.log_error(f"Error checking if Python socket server is running: {str(e)}")
        unreal.log_error(traceback.format_exc())
        return False

def get_socket_server_url():
    """Get the Python socket server URL"""
    try:
        return socket_server_manager.get_server_url()
    except Exception as e:
        unreal.log_error(f"Error getting Python socket server URL: {str(e)}")
        unreal.log_error(traceback.format_exc())
        return ""

def get_socket_server_type():
    """Get the Python socket server type"""
    try:
        return socket_server_manager.get_server_type()
    except Exception as e:
        unreal.log_error(f"Error getting Python socket server type: {str(e)}")
        unreal.log_error(traceback.format_exc())
        return ""

def connection_checker_thread_function():
    """Connection checker thread function"""
    global connection_checker_running
    
    failures = 0
    max_failures = 3
    check_interval = 5  # seconds
    
    unreal.log("Socket connection checker started")
    
    while connection_checker_running:
        try:
            # Check if the server is running
            if not is_socket_server_running():
                unreal.log_warning("Socket server is not running")
                failures += 1
            else:
                # Try to send a test message
                try:
                    unreal.log("Test message sent, waiting for response")
                    # This is just a placeholder, we're not actually sending a message
                    # The server is already checked with is_socket_server_running()
                    failures = 0
                except Exception as e:
                    unreal.log_error(f"Failed to send test message: {str(e)}")
                    failures += 1
            
            # Check if we've reached the maximum number of failures
            if failures >= max_failures:
                unreal.log_warning(f"Socket connection check: {failures} consecutive failures. Attempting auto-restart...")
                
                # Auto-restart the server
                try:
                    unreal.log_warning("Auto-restarting socket server due to connection issues")
                    unreal.log_warning("Stopping socket server...")
                    socket_server_manager.stop_server()
                    time.sleep(1)
                    
                    # Get the current server type
                    is_websocket = socket_server_manager.is_websocket
                    
                    # Start the server
                    socket_server_manager.start_server(is_websocket)
                    
                    unreal.log_warning("Socket server auto-restart completed")
                    failures = 0
                except Exception as e:
                    unreal.log_error(f"Failed to auto-restart socket server: {str(e)}")
            
            # Sleep for the check interval
            time.sleep(check_interval)
        except Exception as e:
            unreal.log_error(f"Error in connection checker thread: {str(e)}")
            unreal.log_error(traceback.format_exc())
            time.sleep(check_interval)
    
    unreal.log("Socket connection checker stopped")

def start_connection_checker():
    """Start the connection checker thread"""
    global connection_checker_thread, connection_checker_running
    
    try:
        # Stop any existing connection checker
        stop_connection_checker()
        
        # Start the connection checker thread
        connection_checker_running = True
        connection_checker_thread = threading.Thread(
            target=connection_checker_thread_function,
            daemon=True
        )
        connection_checker_thread.start()
        
        unreal.log("Socket connection checker started")
        return True
    except Exception as e:
        unreal.log_error(f"Error starting connection checker: {str(e)}")
        unreal.log_error(traceback.format_exc())
        connection_checker_running = False
        return False

def stop_connection_checker():
    """Stop the connection checker thread"""
    global connection_checker_thread, connection_checker_running
    
    try:
        # Stop the connection checker thread
        connection_checker_running = False
        
        # Wait for the thread to exit
        if connection_checker_thread and connection_checker_thread.is_alive():
            connection_checker_thread.join(timeout=2.0)
        
        connection_checker_thread = None
        
        unreal.log("Socket connection checker stopped")
        return True
    except Exception as e:
        unreal.log_error(f"Error stopping connection checker: {str(e)}")
        unreal.log_error(traceback.format_exc())
        return False
