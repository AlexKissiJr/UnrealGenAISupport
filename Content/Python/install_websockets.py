import unreal
import sys
import subprocess
import os
import importlib.util

def log_info(message):
    """Log info message"""
    unreal.log(f"[WebSocket Installer] {message}")

def log_warning(message):
    """Log warning message"""
    unreal.log_warning(f"[WebSocket Installer] {message}")

def log_error(message):
    """Log error message"""
    unreal.log_error(f"[WebSocket Installer] {message}")

def check_module_installed(module_name):
    """Check if a Python module is installed"""
    try:
        spec = importlib.util.find_spec(module_name)
        return spec is not None
    except ModuleNotFoundError:
        return False

def get_python_executable():
    """Get the path to the Python executable"""
    return sys.executable

def install_module(module_name):
    """Install a Python module using pip"""
    try:
        python_exe = get_python_executable()
        log_info(f"Using Python executable: {python_exe}")
        
        # Check if pip is available
        try:
            subprocess.check_call([python_exe, "-m", "pip", "--version"])
        except subprocess.CalledProcessError:
            log_error("pip is not available. Please install pip first.")
            return False
        
        # Install the module
        log_info(f"Installing {module_name}...")
        result = subprocess.check_call([python_exe, "-m", "pip", "install", module_name])
        
        if result == 0:
            log_info(f"{module_name} installed successfully.")
            return True
        else:
            log_error(f"Failed to install {module_name}.")
            return False
    except Exception as e:
        log_error(f"Error installing {module_name}: {str(e)}")
        return False

def main():
    """Main function"""
    log_info("Checking for websockets module...")
    
    if check_module_installed("websockets"):
        log_info("websockets module is already installed.")
        return True
    
    log_warning("websockets module is not installed. Attempting to install...")
    
    if install_module("websockets"):
        log_info("websockets module installed successfully.")
        
        # Verify installation
        if check_module_installed("websockets"):
            log_info("Verified websockets module installation.")
            return True
        else:
            log_error("Failed to verify websockets module installation.")
            return False
    else:
        log_error("Failed to install websockets module.")
        
        # Provide manual installation instructions
        log_info("Please install the websockets module manually:")
        log_info("1. Open a command prompt or terminal")
        log_info(f"2. Run: {get_python_executable()} -m pip install websockets")
        log_info("3. Restart Unreal Engine")
        
        return False

# Run the main function
if __name__ == "__main__":
    success = main()
    
    if success:
        log_info("✅ websockets module is ready to use.")
    else:
        log_error("❌ websockets module is not available.")

# Function to run from Unreal Engine
def install_websockets():
    """Install the websockets module"""
    return main()
