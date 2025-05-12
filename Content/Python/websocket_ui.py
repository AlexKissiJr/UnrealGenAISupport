"""
WebSocket server UI for Unreal Engine.
This module provides a UI to control the WebSocket server from Unreal Engine.
"""

import unreal
import unreal_websocket_nonblocking as websocket
import threading
import time
import json

# Global variables
status_check_thread = None
is_checking_status = False
last_status = None

# Start the WebSocket server
def start_server():
    """Start the WebSocket server"""
    try:
        # Start the server
        success = websocket.start()
        
        if success:
            unreal.log("✅ WebSocket server started successfully")
            
            # Start status checking
            start_status_checking()
            
            return True
        else:
            unreal.log_error("❌ Failed to start WebSocket server")
            return False
    except Exception as e:
        unreal.log_error(f"Error starting WebSocket server: {str(e)}")
        import traceback
        unreal.log_error(traceback.format_exc())
        return False

# Stop the WebSocket server
def stop_server():
    """Stop the WebSocket server"""
    try:
        # Stop status checking
        stop_status_checking()
        
        # Stop the server
        success = websocket.stop()
        
        if success:
            unreal.log("✅ WebSocket server stopped successfully")
            return True
        else:
            unreal.log_error("❌ Failed to stop WebSocket server")
            return False
    except Exception as e:
        unreal.log_error(f"Error stopping WebSocket server: {str(e)}")
        import traceback
        unreal.log_error(traceback.format_exc())
        return False

# Get the WebSocket server status
def get_server_status():
    """Get the WebSocket server status"""
    try:
        status_json = websocket.status()
        status = json.loads(status_json)
        
        return status
    except Exception as e:
        unreal.log_error(f"Error getting WebSocket server status: {str(e)}")
        import traceback
        unreal.log_error(traceback.format_exc())
        return {"status": "error", "error": str(e)}

# Status check thread function
def status_check_thread_function():
    """Status check thread function"""
    global is_checking_status, last_status
    
    try:
        unreal.log("Starting WebSocket server status check thread...")
        
        while is_checking_status:
            try:
                # Get the server status
                status = get_server_status()
                
                # Check if status has changed
                if status != last_status:
                    unreal.log(f"WebSocket server status: {status['status']}")
                    last_status = status
                    
                # Sleep briefly
                time.sleep(1)
            except Exception as e:
                unreal.log_error(f"Error checking WebSocket server status: {str(e)}")
                time.sleep(5)  # Sleep longer on error
                
        unreal.log("WebSocket server status check thread stopped")
    except Exception as e:
        unreal.log_error(f"Error in WebSocket server status check thread: {str(e)}")
        import traceback
        unreal.log_error(traceback.format_exc())
    finally:
        is_checking_status = False

# Start status checking
def start_status_checking():
    """Start status checking"""
    global status_check_thread, is_checking_status
    
    try:
        # Check if already checking
        if is_checking_status and status_check_thread and status_check_thread.is_alive():
            unreal.log("WebSocket server status check thread is already running")
            return True
            
        # Start the status check thread
        is_checking_status = True
        status_check_thread = threading.Thread(
            target=status_check_thread_function,
            daemon=True,
            name="WebSocketStatusCheckThread"
        )
        status_check_thread.start()
        
        return True
    except Exception as e:
        unreal.log_error(f"Error starting WebSocket server status check thread: {str(e)}")
        import traceback
        unreal.log_error(traceback.format_exc())
        is_checking_status = False
        return False

# Stop status checking
def stop_status_checking():
    """Stop status checking"""
    global status_check_thread, is_checking_status
    
    try:
        # Check if already stopped
        if not is_checking_status:
            unreal.log("WebSocket server status check thread is already stopped")
            return True
            
        # Stop the status check thread
        is_checking_status = False
        
        # Wait for the thread to exit
        if status_check_thread and status_check_thread.is_alive():
            unreal.log("Waiting for WebSocket server status check thread to exit...")
            status_check_thread.join(timeout=5)
            
            if status_check_thread.is_alive():
                unreal.log_warning("WebSocket server status check thread did not exit within timeout")
            else:
                unreal.log("WebSocket server status check thread exited")
                
        status_check_thread = None
        
        return True
    except Exception as e:
        unreal.log_error(f"Error stopping WebSocket server status check thread: {str(e)}")
        import traceback
        unreal.log_error(traceback.format_exc())
        return False

# Create the UI
def create_ui():
    """Create the UI"""
    try:
        # Create a new editor utility widget
        widget_class = unreal.EditorUtilityWidgetBlueprint.get_editor_utility_widget_blueprint_class('/Game/Python/WebSocketUI.WebSocketUI')
        widget = unreal.EditorUtilitySubsystem.get_subsystem().spawn_and_register_tab(widget_class)
        
        # Set up the widget
        widget.set_python_module('websocket_ui')
        
        return widget
    except Exception as e:
        unreal.log_error(f"Error creating WebSocket server UI: {str(e)}")
        import traceback
        unreal.log_error(traceback.format_exc())
        return None

# Show the UI
def show_ui():
    """Show the UI"""
    try:
        # Create the UI
        widget = create_ui()
        
        if widget:
            unreal.log("WebSocket server UI created successfully")
            return True
        else:
            unreal.log_error("Failed to create WebSocket server UI")
            return False
    except Exception as e:
        unreal.log_error(f"Error showing WebSocket server UI: {str(e)}")
        import traceback
        unreal.log_error(traceback.format_exc())
        return False

# Functions to be called from the UI
def start():
    """Start the WebSocket server"""
    return start_server()

def stop():
    """Stop the WebSocket server"""
    return stop_server()

def status():
    """Get the WebSocket server status"""
    status = get_server_status()
    return status['status']

# Run when this script is executed
if __name__ == "__main__":
    show_ui()
