"""
Direct test script for Unreal Engine.
This script tests subprocess creation without relying on the WebSocket server.
"""

import unreal
import sys
import os
import subprocess
import time
import traceback

def test_subprocess():
    """Test subprocess creation"""
    try:
        unreal.log("Testing subprocess creation...")
        
        # Get the Python executable
        python_executable = sys.executable
        unreal.log(f"Python executable: {python_executable}")
        
        # Create a simple Python script
        script_content = """
import sys
import time
print("Hello from subprocess!")
print(f"Python version: {sys.version}")
print(f"Python executable: {sys.executable}")
print(f"Arguments: {sys.argv}")
time.sleep(1)
print("Subprocess completed successfully")
sys.exit(0)
"""
        
        # Write the script to a temporary file
        script_dir = os.path.dirname(os.path.abspath(__file__))
        script_path = os.path.join(script_dir, "temp_subprocess_test.py")
        
        with open(script_path, "w") as f:
            f.write(script_content)
            
        unreal.log(f"Created temporary script at: {script_path}")
        
        # Start the subprocess
        unreal.log(f"Starting subprocess: {python_executable} {script_path}")
        
        if sys.platform == "win32":
            # Windows
            process = subprocess.Popen(
                [python_executable, script_path, "arg1", "arg2"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
        else:
            # Unix
            process = subprocess.Popen(
                [python_executable, script_path, "arg1", "arg2"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
        unreal.log(f"Subprocess created with PID: {process.pid}")
        
        # Wait for the process to complete
        unreal.log("Waiting for subprocess to complete...")
        stdout, stderr = process.communicate(timeout=5)
        
        # Check the result
        unreal.log(f"Subprocess exited with code: {process.returncode}")
        
        if stdout:
            unreal.log(f"Subprocess stdout: {stdout.decode('utf-8')}")
        if stderr:
            unreal.log_error(f"Subprocess stderr: {stderr.decode('utf-8')}")
            
        # Clean up
        try:
            os.remove(script_path)
            unreal.log(f"Removed temporary script: {script_path}")
        except Exception as e:
            unreal.log_warning(f"Failed to remove temporary script: {str(e)}")
            
        return process.returncode == 0
    except Exception as e:
        unreal.log_error(f"Error testing subprocess: {str(e)}")
        unreal.log_error(traceback.format_exc())
        return False

def test_file_operations():
    """Test file operations"""
    try:
        unreal.log("Testing file operations...")
        
        # Get the script directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        unreal.log(f"Script directory: {script_dir}")
        
        # List files in the directory
        files = os.listdir(script_dir)
        unreal.log(f"Files in directory: {files}")
        
        # Check if mcp_server_refactored.py exists
        server_script_path = os.path.join(script_dir, "mcp_server_refactored.py")
        if os.path.exists(server_script_path):
            unreal.log(f"mcp_server_refactored.py exists at: {server_script_path}")
            
            # Get file size
            file_size = os.path.getsize(server_script_path)
            unreal.log(f"File size: {file_size} bytes")
            
            # Read the first few lines
            with open(server_script_path, "r") as f:
                first_lines = [f.readline() for _ in range(5)]
                unreal.log(f"First few lines: {first_lines}")
        else:
            unreal.log_error(f"mcp_server_refactored.py not found at: {server_script_path}")
            
        return True
    except Exception as e:
        unreal.log_error(f"Error testing file operations: {str(e)}")
        unreal.log_error(traceback.format_exc())
        return False

def main():
    """Main function"""
    try:
        unreal.log("Starting direct test...")
        
        # Test file operations
        unreal.log("Testing file operations...")
        file_ops_result = test_file_operations()
        unreal.log(f"File operations test result: {file_ops_result}")
        
        # Test subprocess creation
        unreal.log("Testing subprocess creation...")
        subprocess_result = test_subprocess()
        unreal.log(f"Subprocess test result: {subprocess_result}")
        
        # Overall result
        if file_ops_result and subprocess_result:
            unreal.log("✅ All tests passed")
            return True
        else:
            unreal.log_error("❌ Some tests failed")
            return False
    except Exception as e:
        unreal.log_error(f"Error in main function: {str(e)}")
        unreal.log_error(traceback.format_exc())
        return False

# Run the main function
if __name__ == "__main__":
    main()
