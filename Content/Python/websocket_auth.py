"""
Authentication module for WebSocket server.
This module provides authentication functions for the WebSocket server.
"""

import os
import json
import hashlib
import time
import threading
import uuid
from pathlib import Path
import websocket_logging as log

# Global variables
auth_tokens = {}
auth_lock = threading.Lock()
auth_config_path = None

# Initialize authentication
def init_auth(config_path=None):
    """Initialize authentication"""
    global auth_config_path
    
    try:
        # Set config path
        if config_path:
            auth_config_path = config_path
        else:
            # Use default config path
            auth_dir = os.path.join(os.path.expanduser("~"), ".unrealgenai")
            os.makedirs(auth_dir, exist_ok=True)
            auth_config_path = os.path.join(auth_dir, "websocket_auth.json")
            
        # Load auth tokens
        load_auth_tokens()
        
        log.log_info(f"Authentication initialized with config path: {auth_config_path}")
        return True
    except Exception as e:
        log.log_error(f"Failed to initialize authentication: {str(e)}", include_traceback=True)
        return False

# Load auth tokens from file
def load_auth_tokens():
    """Load auth tokens from file"""
    global auth_tokens, auth_config_path, auth_lock
    
    try:
        with auth_lock:
            if os.path.exists(auth_config_path):
                with open(auth_config_path, "r") as f:
                    auth_tokens = json.load(f)
                log.log_info(f"Loaded {len(auth_tokens)} auth tokens from {auth_config_path}")
            else:
                # Create default auth token
                token = generate_token()
                auth_tokens = {
                    "default": {
                        "token": token,
                        "created": time.time(),
                        "expires": time.time() + 86400 * 30  # 30 days
                    }
                }
                save_auth_tokens()
                log.log_info(f"Created default auth token: {token}")
    except Exception as e:
        log.log_error(f"Failed to load auth tokens: {str(e)}", include_traceback=True)

# Save auth tokens to file
def save_auth_tokens():
    """Save auth tokens to file"""
    global auth_tokens, auth_config_path, auth_lock
    
    try:
        with auth_lock:
            with open(auth_config_path, "w") as f:
                json.dump(auth_tokens, f, indent=2)
            log.log_info(f"Saved {len(auth_tokens)} auth tokens to {auth_config_path}")
    except Exception as e:
        log.log_error(f"Failed to save auth tokens: {str(e)}", include_traceback=True)

# Generate a new token
def generate_token():
    """Generate a new token"""
    return str(uuid.uuid4())

# Create a new auth token
def create_auth_token(name, expires=None):
    """Create a new auth token"""
    global auth_tokens, auth_lock
    
    try:
        with auth_lock:
            token = generate_token()
            auth_tokens[name] = {
                "token": token,
                "created": time.time(),
                "expires": time.time() + 86400 * 30 if expires is None else expires  # 30 days
            }
            save_auth_tokens()
            log.log_info(f"Created auth token '{name}': {token}")
            return token
    except Exception as e:
        log.log_error(f"Failed to create auth token: {str(e)}", include_traceback=True)
        return None

# Validate an auth token
def validate_token(token):
    """Validate an auth token"""
    global auth_tokens, auth_lock
    
    try:
        with auth_lock:
            # Check if token exists
            for name, auth in auth_tokens.items():
                if auth["token"] == token:
                    # Check if token has expired
                    if auth["expires"] > time.time():
                        log.log_debug(f"Auth token '{name}' is valid")
                        return True
                    else:
                        log.log_warning(f"Auth token '{name}' has expired")
                        return False
            
            log.log_warning(f"Auth token not found")
            return False
    except Exception as e:
        log.log_error(f"Failed to validate auth token: {str(e)}", include_traceback=True)
        return False

# Delete an auth token
def delete_auth_token(name):
    """Delete an auth token"""
    global auth_tokens, auth_lock
    
    try:
        with auth_lock:
            if name in auth_tokens:
                del auth_tokens[name]
                save_auth_tokens()
                log.log_info(f"Deleted auth token '{name}'")
                return True
            else:
                log.log_warning(f"Auth token '{name}' not found")
                return False
    except Exception as e:
        log.log_error(f"Failed to delete auth token: {str(e)}", include_traceback=True)
        return False

# Get all auth tokens
def get_auth_tokens():
    """Get all auth tokens"""
    global auth_tokens, auth_lock
    
    try:
        with auth_lock:
            return auth_tokens
    except Exception as e:
        log.log_error(f"Failed to get auth tokens: {str(e)}", include_traceback=True)
        return {}

# Initialize authentication with default settings
init_auth()
