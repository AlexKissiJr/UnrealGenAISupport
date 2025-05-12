"""
Simple test script to verify that Python is working correctly in Unreal Engine.
"""

import unreal
import sys
import os

def main():
    """Main function"""
    try:
        # Log basic information
        unreal.log("Simple test script running...")
        unreal.log(f"Python version: {sys.version}")
        unreal.log(f"Python executable: {sys.executable}")
        unreal.log(f"Current working directory: {os.getcwd()}")
        
        # Log Unreal Engine information
        unreal.log(f"Unreal Engine version: {unreal.SystemLibrary.get_engine_version()}")
        unreal.log(f"Project directory: {unreal.Paths.project_dir()}")
        unreal.log(f"Project content directory: {unreal.Paths.project_content_dir()}")
        
        # Log success message
        unreal.log("✅ Simple test script completed successfully")
        return True
    except Exception as e:
        unreal.log_error(f"❌ Error in simple test script: {str(e)}")
        import traceback
        unreal.log_error(traceback.format_exc())
        return False

# Run the main function
if __name__ == "__main__":
    main()
