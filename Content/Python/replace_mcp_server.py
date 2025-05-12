import unreal
import sys
import os
import shutil
import traceback

def replace_mcp_server():
    """Replace the standard mcp_server.py with our WebSocket version"""
    try:
        # Get the plugin's Content/Python path
        plugin_content_path = unreal.Paths.project_plugins_dir() + "/UnrealGenAISupport/Content"
        python_path = os.path.join(plugin_content_path, "Python")
        
        # Check if the files exist
        mcp_server_path = os.path.join(python_path, "mcp_server.py")
        mcp_server_websocket_path = os.path.join(python_path, "mcp_server_websocket.py")
        mcp_server_backup_path = os.path.join(python_path, "mcp_server_original.py")
        
        if not os.path.exists(mcp_server_websocket_path):
            unreal.log_error(f"WebSocket version of mcp_server.py not found at: {mcp_server_websocket_path}")
            return False
        
        # Create a backup of the original mcp_server.py if it exists
        if os.path.exists(mcp_server_path) and not os.path.exists(mcp_server_backup_path):
            unreal.log(f"Creating backup of original mcp_server.py at: {mcp_server_backup_path}")
            shutil.copy2(mcp_server_path, mcp_server_backup_path)
        
        # Replace mcp_server.py with our WebSocket version
        unreal.log(f"Replacing mcp_server.py with WebSocket version")
        shutil.copy2(mcp_server_websocket_path, mcp_server_path)
        
        unreal.log("✅ Successfully replaced mcp_server.py with WebSocket version")
        return True
    except Exception as e:
        unreal.log_error(f"Error replacing mcp_server.py: {str(e)}")
        unreal.log_error(traceback.format_exc())
        return False

def restore_mcp_server():
    """Restore the original mcp_server.py"""
    try:
        # Get the plugin's Content/Python path
        plugin_content_path = unreal.Paths.project_plugins_dir() + "/UnrealGenAISupport/Content"
        python_path = os.path.join(plugin_content_path, "Python")
        
        # Check if the backup file exists
        mcp_server_path = os.path.join(python_path, "mcp_server.py")
        mcp_server_backup_path = os.path.join(python_path, "mcp_server_original.py")
        
        if not os.path.exists(mcp_server_backup_path):
            unreal.log_error(f"Backup of original mcp_server.py not found at: {mcp_server_backup_path}")
            return False
        
        # Restore the original mcp_server.py
        unreal.log(f"Restoring original mcp_server.py")
        shutil.copy2(mcp_server_backup_path, mcp_server_path)
        
        unreal.log("✅ Successfully restored original mcp_server.py")
        return True
    except Exception as e:
        unreal.log_error(f"Error restoring mcp_server.py: {str(e)}")
        unreal.log_error(traceback.format_exc())
        return False

# Run the script
if __name__ == "__main__":
    unreal.log("Replacing mcp_server.py with WebSocket version...")
    success = replace_mcp_server()
    
    if success:
        unreal.log("✅ Successfully replaced mcp_server.py with WebSocket version")
    else:
        unreal.log_error("❌ Failed to replace mcp_server.py with WebSocket version")

# Functions to run from Unreal Engine
def replace():
    """Replace the standard mcp_server.py with our WebSocket version"""
    return replace_mcp_server()

def restore():
    """Restore the original mcp_server.py"""
    return restore_mcp_server()
