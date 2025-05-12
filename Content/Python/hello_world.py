"""
Hello World script for Unreal Engine.
This script simply prints "Hello, World!" to the Unreal Engine log.
"""

import unreal

def main():
    """Main function"""
    try:
        unreal.log("Hello, World!")
        unreal.log("This is a simple test script to verify that Python is working in Unreal Engine.")
        unreal.log("✅ Test completed successfully")
        return True
    except Exception as e:
        unreal.log_error(f"❌ Error: {str(e)}")
        import traceback
        unreal.log_error(traceback.format_exc())
        return False

# Run the main function
if __name__ == "__main__":
    main()
