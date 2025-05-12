import unreal
import json
import sys
import os
from typing import Dict, Any, List, Optional

# Import the actor commands module
try:
    from handlers import actor_commands
except ImportError:
    unreal.log_error("Failed to import actor_commands module")
    
    # Create a dummy module
    class DummyActorCommands:
        @staticmethod
        def handle_modify_object(command):
            return {"success": False, "error": "Actor commands module not available"}
            
        @staticmethod
        def handle_edit_component_property(command):
            return {"success": False, "error": "Actor commands module not available"}
            
        @staticmethod
        def handle_add_component_with_events(command):
            return {"success": False, "error": "Actor commands module not available"}
    
    actor_commands = DummyActorCommands()

# Simple logging functions
def log_info(message):
    unreal.log_info(f"[WebSocket Actor Handler] {message}")
    
def log_warning(message):
    unreal.log_warning(f"[WebSocket Actor Handler] {message}")
    
def log_error(message, include_traceback=False):
    if include_traceback:
        import traceback
        unreal.log_error(f"[WebSocket Actor Handler] {message}\n{traceback.format_exc()}")
    else:
        unreal.log_error(f"[WebSocket Actor Handler] {message}")

# WebSocket handler for actor operations
class WebSocketActorHandler:
    """Handler for actor operations over WebSocket"""
    
    def __init__(self):
        """Initialize the handler"""
        log_info("Initializing WebSocket Actor Handler")
        
    def handle_actor_request(self, request_json: str) -> str:
        """
        Handle an actor request received over WebSocket
        
        Args:
            request_json: The JSON request string
            
        Returns:
            The JSON response string
        """
        try:
            # Parse the JSON request
            request = json.loads(request_json)
            
            # Get the operation type
            operation = request.get("operation", "")
            
            if not operation:
                return json.dumps({
                    "success": False,
                    "error": "Missing operation field in actor request"
                })
                
            # Dispatch to the appropriate handler
            if operation == "modify_object":
                return self._handle_modify_object(request)
            elif operation == "edit_component_property":
                return self._handle_edit_component_property(request)
            elif operation == "add_component_with_events":
                return self._handle_add_component_with_events(request)
            elif operation == "get_actor_properties":
                return self._handle_get_actor_properties(request)
            elif operation == "set_actor_properties":
                return self._handle_set_actor_properties(request)
            else:
                return json.dumps({
                    "success": False,
                    "error": f"Unknown actor operation: {operation}"
                })
                
        except Exception as e:
            log_error(f"Error handling actor request: {str(e)}", include_traceback=True)
            return json.dumps({
                "success": False,
                "error": f"Error handling actor request: {str(e)}"
            })
            
    def _handle_modify_object(self, request: Dict[str, Any]) -> str:
        """Handle modify_object operation"""
        try:
            # Convert the request to the format expected by actor_commands
            command = {
                "type": "modify_object",
                "object_path": request.get("object_path", ""),
                "property_name": request.get("property_name", ""),
                "property_value": request.get("property_value", "")
            }
            
            # Call the actor command handler
            result = actor_commands.handle_modify_object(command)
            
            # Return the result as JSON
            return json.dumps(result)
            
        except Exception as e:
            log_error(f"Error modifying object: {str(e)}", include_traceback=True)
            return json.dumps({
                "success": False,
                "error": f"Error modifying object: {str(e)}"
            })
            
    def _handle_edit_component_property(self, request: Dict[str, Any]) -> str:
        """Handle edit_component_property operation"""
        try:
            # Convert the request to the format expected by actor_commands
            command = {
                "type": "edit_component_property",
                "actor_path": request.get("actor_path", ""),
                "component_name": request.get("component_name", ""),
                "property_name": request.get("property_name", ""),
                "property_value": request.get("property_value", "")
            }
            
            # Call the actor command handler
            result = actor_commands.handle_edit_component_property(command)
            
            # Return the result as JSON
            return json.dumps(result)
            
        except Exception as e:
            log_error(f"Error editing component property: {str(e)}", include_traceback=True)
            return json.dumps({
                "success": False,
                "error": f"Error editing component property: {str(e)}"
            })
            
    def _handle_add_component_with_events(self, request: Dict[str, Any]) -> str:
        """Handle add_component_with_events operation"""
        try:
            # Convert the request to the format expected by actor_commands
            command = {
                "type": "add_component_with_events",
                "actor_path": request.get("actor_path", ""),
                "component_class": request.get("component_class", ""),
                "component_name": request.get("component_name", ""),
                "events": request.get("events", [])
            }
            
            # Call the actor command handler
            result = actor_commands.handle_add_component_with_events(command)
            
            # Return the result as JSON
            return json.dumps(result)
            
        except Exception as e:
            log_error(f"Error adding component with events: {str(e)}", include_traceback=True)
            return json.dumps({
                "success": False,
                "error": f"Error adding component with events: {str(e)}"
            })
            
    def _handle_get_actor_properties(self, request: Dict[str, Any]) -> str:
        """Handle get_actor_properties operation"""
        try:
            # Get the actor path
            actor_path = request.get("actor_path", "")
            
            if not actor_path:
                return json.dumps({
                    "success": False,
                    "error": "Missing actor_path field in get_actor_properties request"
                })
                
            # Get the actor
            actor = unreal.EditorAssetLibrary.load_asset(actor_path)
            
            if not actor:
                return json.dumps({
                    "success": False,
                    "error": f"Actor not found: {actor_path}"
                })
                
            # Get the properties
            properties = {}
            
            # Get transform properties
            if hasattr(actor, "get_actor_location"):
                location = actor.get_actor_location()
                properties["location"] = {
                    "x": location.x,
                    "y": location.y,
                    "z": location.z
                }
                
            if hasattr(actor, "get_actor_rotation"):
                rotation = actor.get_actor_rotation()
                properties["rotation"] = {
                    "pitch": rotation.pitch,
                    "yaw": rotation.yaw,
                    "roll": rotation.roll
                }
                
            if hasattr(actor, "get_actor_scale"):
                scale = actor.get_actor_scale()
                properties["scale"] = {
                    "x": scale.x,
                    "y": scale.y,
                    "z": scale.z
                }
                
            # Get components
            components = []
            
            if hasattr(actor, "get_components_by_class"):
                for component in actor.get_components_by_class(unreal.ActorComponent):
                    components.append({
                        "name": component.get_name(),
                        "class": component.get_class().get_name()
                    })
                    
            properties["components"] = components
            
            # Return the properties
            return json.dumps({
                "success": True,
                "actor_path": actor_path,
                "properties": properties
            })
            
        except Exception as e:
            log_error(f"Error getting actor properties: {str(e)}", include_traceback=True)
            return json.dumps({
                "success": False,
                "error": f"Error getting actor properties: {str(e)}"
            })
            
    def _handle_set_actor_properties(self, request: Dict[str, Any]) -> str:
        """Handle set_actor_properties operation"""
        try:
            # Get the actor path and properties
            actor_path = request.get("actor_path", "")
            properties = request.get("properties", {})
            
            if not actor_path:
                return json.dumps({
                    "success": False,
                    "error": "Missing actor_path field in set_actor_properties request"
                })
                
            if not properties:
                return json.dumps({
                    "success": False,
                    "error": "Missing properties field in set_actor_properties request"
                })
                
            # Get the actor
            actor = unreal.EditorAssetLibrary.load_asset(actor_path)
            
            if not actor:
                return json.dumps({
                    "success": False,
                    "error": f"Actor not found: {actor_path}"
                })
                
            # Set the properties
            if "location" in properties and hasattr(actor, "set_actor_location"):
                location = properties["location"]
                actor.set_actor_location(
                    unreal.Vector(
                        location.get("x", 0),
                        location.get("y", 0),
                        location.get("z", 0)
                    ),
                    False,  # sweep
                    True    # teleport
                )
                
            if "rotation" in properties and hasattr(actor, "set_actor_rotation"):
                rotation = properties["rotation"]
                actor.set_actor_rotation(
                    unreal.Rotator(
                        rotation.get("pitch", 0),
                        rotation.get("yaw", 0),
                        rotation.get("roll", 0)
                    ),
                    True    # teleport
                )
                
            if "scale" in properties and hasattr(actor, "set_actor_scale"):
                scale = properties["scale"]
                actor.set_actor_scale(
                    unreal.Vector(
                        scale.get("x", 1),
                        scale.get("y", 1),
                        scale.get("z", 1)
                    )
                )
                
            # Return success
            return json.dumps({
                "success": True,
                "message": f"Actor properties set successfully: {actor_path}",
                "actor_path": actor_path
            })
            
        except Exception as e:
            log_error(f"Error setting actor properties: {str(e)}", include_traceback=True)
            return json.dumps({
                "success": False,
                "error": f"Error setting actor properties: {str(e)}"
            })

# Create a singleton instance
actor_handler = WebSocketActorHandler()

# Function to handle actor requests
def handle_actor_request(request_json: str) -> str:
    """
    Handle an actor request received over WebSocket
    
    Args:
        request_json: The JSON request string
        
    Returns:
        The JSON response string
    """
    return actor_handler.handle_actor_request(request_json)
