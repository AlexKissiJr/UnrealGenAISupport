"""
Logging module for WebSocket server.
This module provides logging functions for the WebSocket server.
"""

import sys
import os
import traceback
import time
import threading
from pathlib import Path
from enum import Enum

# Log levels
class LogLevel(Enum):
    DEBUG = 0
    INFO = 1
    WARNING = 2
    ERROR = 3
    CRITICAL = 4

# Global variables
log_level = LogLevel.INFO
log_file = None
log_lock = threading.Lock()

# Initialize logging
def init_logging(level=LogLevel.INFO, log_to_file=False, log_file_path=None):
    """Initialize logging"""
    global log_level, log_file
    
    # Set log level
    log_level = level
    
    # Set log file
    if log_to_file:
        try:
            if log_file_path:
                # Use specified log file path
                log_file_dir = os.path.dirname(log_file_path)
                if log_file_dir:
                    os.makedirs(log_file_dir, exist_ok=True)
                log_file = open(log_file_path, "a", encoding="utf-8")
            else:
                # Use default log file path
                log_dir = os.path.join(os.path.expanduser("~"), ".unrealgenai", "logs")
                os.makedirs(log_dir, exist_ok=True)
                log_file_path = os.path.join(log_dir, f"websocket_server_{time.strftime('%Y%m%d_%H%M%S')}.log")
                log_file = open(log_file_path, "a", encoding="utf-8")
                
            # Register to close the log file on exit
            import atexit
            def close_log_file():
                if log_file:
                    log_file.close()
            atexit.register(close_log_file)
            
            log_info(f"Logging to file: {log_file_path}")
        except Exception as e:
            log_error(f"Failed to open log file: {str(e)}")
            log_file = None

# Log a message
def log_message(level, message, include_traceback=False):
    """Log a message"""
    global log_level, log_file, log_lock
    
    # Check log level
    if level.value < log_level.value:
        return
    
    # Format message
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    level_str = level.name
    formatted_message = f"[{timestamp}] [{level_str}] {message}"
    
    # Add traceback if requested
    if include_traceback:
        tb = traceback.format_exc()
        if tb != "NoneType: None\n":
            formatted_message += f"\n{tb}"
    
    # Log to console
    with log_lock:
        print(formatted_message, file=sys.stderr)
        
        # Log to file
        if log_file:
            try:
                log_file.write(formatted_message + "\n")
                log_file.flush()
            except Exception as e:
                print(f"Error writing to log file: {str(e)}", file=sys.stderr)

# Log debug message
def log_debug(message, include_traceback=False):
    """Log a debug message"""
    log_message(LogLevel.DEBUG, message, include_traceback)

# Log info message
def log_info(message, include_traceback=False):
    """Log an info message"""
    log_message(LogLevel.INFO, message, include_traceback)

# Log warning message
def log_warning(message, include_traceback=False):
    """Log a warning message"""
    log_message(LogLevel.WARNING, message, include_traceback)

# Log error message
def log_error(message, include_traceback=False):
    """Log an error message"""
    log_message(LogLevel.ERROR, message, include_traceback)

# Log critical message
def log_critical(message, include_traceback=False):
    """Log a critical message"""
    log_message(LogLevel.CRITICAL, message, include_traceback)

# Set log level
def set_log_level(level):
    """Set log level"""
    global log_level
    log_level = level
    log_info(f"Log level set to {level.name}")

# Get log level
def get_log_level():
    """Get log level"""
    global log_level
    return log_level

# Initialize logging with default settings
init_logging()
