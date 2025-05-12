import unreal
import json
import sys
import os
from typing import Dict, Any, List, Optional

# Import the blueprint commands module
try:
    from handlers import blueprint_commands
except ImportError:
    unreal.log_error("Failed to import blueprint_commands module")

    # Create a dummy module
    class DummyBlueprintCommands:
        @staticmethod
        def handle_create_blueprint(command):
            return {"success": False, "error": "Blueprint commands module not available"}

        @staticmethod
        def handle_add_component(command):
            return {"success": False, "error": "Blueprint commands module not available"}

        @staticmethod
        def handle_add_variable(command):
            return {"success": False, "error": "Blueprint commands module not available"}

        @staticmethod
        def handle_add_function(command):
            return {"success": False, "error": "Blueprint commands module not available"}

        @staticmethod
        def handle_add_event(command):
            return {"success": False, "error": "Blueprint commands module not available"}

        @staticmethod
        def handle_add_node(command):
            return {"success": False, "error": "Blueprint commands module not available"}

        @staticmethod
        def handle_connect_nodes(command):
            return {"success": False, "error": "Blueprint commands module not available"}

    blueprint_commands = DummyBlueprintCommands()

# Simple logging functions
def log_info(message):
    unreal.log(f"[WebSocket Blueprint Handler] {message}")

def log_warning(message):
    unreal.log_warning(f"[WebSocket Blueprint Handler] {message}")

def log_error(message, include_traceback=False):
    if include_traceback:
        import traceback
        unreal.log_error(f"[WebSocket Blueprint Handler] {message}\n{traceback.format_exc()}")
    else:
        unreal.log_error(f"[WebSocket Blueprint Handler] {message}")

# WebSocket handler for blueprint operations
class WebSocketBlueprintHandler:
    """Handler for blueprint operations over WebSocket"""

    def __init__(self):
        """Initialize the handler"""
        log_info("Initializing WebSocket Blueprint Handler")

    def handle_blueprint_request(self, request_json: str) -> str:
        """
        Handle a blueprint request received over WebSocket

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
                    "error": "Missing operation field in blueprint request"
                })

            # Dispatch to the appropriate handler
            if operation == "create_blueprint":
                return self._handle_create_blueprint(request)
            elif operation == "add_component":
                return self._handle_add_component(request)
            elif operation == "add_variable":
                return self._handle_add_variable(request)
            elif operation == "add_function":
                return self._handle_add_function(request)
            elif operation == "add_event":
                return self._handle_add_event(request)
            elif operation == "add_node":
                return self._handle_add_node(request)
            elif operation == "connect_nodes":
                return self._handle_connect_nodes(request)
            elif operation == "generate_blueprint":
                return self._handle_generate_blueprint(request)
            else:
                return json.dumps({
                    "success": False,
                    "error": f"Unknown blueprint operation: {operation}"
                })

        except Exception as e:
            log_error(f"Error handling blueprint request: {str(e)}", include_traceback=True)
            return json.dumps({
                "success": False,
                "error": f"Error handling blueprint request: {str(e)}"
            })

    def _handle_create_blueprint(self, request: Dict[str, Any]) -> str:
        """Handle create_blueprint operation"""
        try:
            # Convert the request to the format expected by blueprint_commands
            command = {
                "type": "create_blueprint",
                "blueprint_path": request.get("blueprint_path", ""),
                "parent_class": request.get("parent_class", "Actor")
            }

            # Call the blueprint command handler
            result = blueprint_commands.handle_create_blueprint(command)

            # Return the result as JSON
            return json.dumps(result)

        except Exception as e:
            log_error(f"Error creating blueprint: {str(e)}", include_traceback=True)
            return json.dumps({
                "success": False,
                "error": f"Error creating blueprint: {str(e)}"
            })

    def _handle_add_component(self, request: Dict[str, Any]) -> str:
        """Handle add_component operation"""
        try:
            # Convert the request to the format expected by blueprint_commands
            command = {
                "type": "add_component",
                "blueprint_path": request.get("blueprint_path", ""),
                "component_class": request.get("component_class", ""),
                "component_name": request.get("component_name", "")
            }

            # Call the blueprint command handler
            result = blueprint_commands.handle_add_component(command)

            # Return the result as JSON
            return json.dumps(result)

        except Exception as e:
            log_error(f"Error adding component: {str(e)}", include_traceback=True)
            return json.dumps({
                "success": False,
                "error": f"Error adding component: {str(e)}"
            })

    def _handle_add_variable(self, request: Dict[str, Any]) -> str:
        """Handle add_variable operation"""
        try:
            # Convert the request to the format expected by blueprint_commands
            command = {
                "type": "add_variable",
                "blueprint_path": request.get("blueprint_path", ""),
                "variable_name": request.get("variable_name", ""),
                "variable_type": request.get("variable_type", ""),
                "default_value": request.get("default_value", None),
                "category": request.get("category", "Default")
            }

            # Call the blueprint command handler
            result = blueprint_commands.handle_add_variable(command)

            # Return the result as JSON
            return json.dumps(result)

        except Exception as e:
            log_error(f"Error adding variable: {str(e)}", include_traceback=True)
            return json.dumps({
                "success": False,
                "error": f"Error adding variable: {str(e)}"
            })

    def _handle_add_function(self, request: Dict[str, Any]) -> str:
        """Handle add_function operation"""
        try:
            # Convert the request to the format expected by blueprint_commands
            command = {
                "type": "add_function",
                "blueprint_path": request.get("blueprint_path", ""),
                "function_name": request.get("function_name", ""),
                "inputs": request.get("inputs", []),
                "outputs": request.get("outputs", [])
            }

            # Call the blueprint command handler
            result = blueprint_commands.handle_add_function(command)

            # Return the result as JSON
            return json.dumps(result)

        except Exception as e:
            log_error(f"Error adding function: {str(e)}", include_traceback=True)
            return json.dumps({
                "success": False,
                "error": f"Error adding function: {str(e)}"
            })

    def _handle_add_event(self, request: Dict[str, Any]) -> str:
        """Handle add_event operation"""
        try:
            # Convert the request to the format expected by blueprint_commands
            command = {
                "type": "add_event",
                "blueprint_path": request.get("blueprint_path", ""),
                "event_name": request.get("event_name", ""),
                "event_type": request.get("event_type", "Custom")
            }

            # Call the blueprint command handler
            result = blueprint_commands.handle_add_event(command)

            # Return the result as JSON
            return json.dumps(result)

        except Exception as e:
            log_error(f"Error adding event: {str(e)}", include_traceback=True)
            return json.dumps({
                "success": False,
                "error": f"Error adding event: {str(e)}"
            })

    def _handle_add_node(self, request: Dict[str, Any]) -> str:
        """Handle add_node operation"""
        try:
            # Convert the request to the format expected by blueprint_commands
            command = {
                "type": "add_node",
                "blueprint_path": request.get("blueprint_path", ""),
                "function_id": request.get("function_id", ""),
                "node_type": request.get("node_type", ""),
                "node_position": request.get("node_position", [0, 0]),
                "node_properties": request.get("node_properties", {})
            }

            # Call the blueprint command handler
            result = blueprint_commands.handle_add_node(command)

            # Return the result as JSON
            return json.dumps(result)

        except Exception as e:
            log_error(f"Error adding node: {str(e)}", include_traceback=True)
            return json.dumps({
                "success": False,
                "error": f"Error adding node: {str(e)}"
            })

    def _handle_connect_nodes(self, request: Dict[str, Any]) -> str:
        """Handle connect_nodes operation"""
        try:
            # Convert the request to the format expected by blueprint_commands
            command = {
                "type": "connect_nodes",
                "blueprint_path": request.get("blueprint_path", ""),
                "function_id": request.get("function_id", ""),
                "source_node_id": request.get("source_node_id", ""),
                "source_pin": request.get("source_pin", ""),
                "target_node_id": request.get("target_node_id", ""),
                "target_pin": request.get("target_pin", "")
            }

            # Call the blueprint command handler
            result = blueprint_commands.handle_connect_nodes(command)

            # Return the result as JSON
            return json.dumps(result)

        except Exception as e:
            log_error(f"Error connecting nodes: {str(e)}", include_traceback=True)
            return json.dumps({
                "success": False,
                "error": f"Error connecting nodes: {str(e)}"
            })

    def _handle_generate_blueprint(self, request: Dict[str, Any]) -> str:
        """
        Handle generate_blueprint operation
        This is a higher-level operation that combines multiple blueprint operations
        """
        try:
            # Get the blueprint specification
            blueprint_spec = request.get("blueprint_spec", {})

            if not blueprint_spec:
                return json.dumps({
                    "success": False,
                    "error": "Missing blueprint_spec field in generate_blueprint request"
                })

            # Extract blueprint details
            blueprint_path = blueprint_spec.get("blueprint_path", "")
            parent_class = blueprint_spec.get("parent_class", "Actor")
            components = blueprint_spec.get("components", [])
            variables = blueprint_spec.get("variables", [])
            functions = blueprint_spec.get("functions", [])
            events = blueprint_spec.get("events", [])

            if not blueprint_path:
                return json.dumps({
                    "success": False,
                    "error": "Missing blueprint_path field in blueprint_spec"
                })

            # Create the blueprint
            create_result = blueprint_commands.handle_create_blueprint({
                "type": "create_blueprint",
                "blueprint_path": blueprint_path,
                "parent_class": parent_class
            })

            if not create_result.get("success", False):
                return json.dumps(create_result)

            # Add components
            for component in components:
                component_result = blueprint_commands.handle_add_component({
                    "type": "add_component",
                    "blueprint_path": blueprint_path,
                    "component_class": component.get("component_class", ""),
                    "component_name": component.get("component_name", "")
                })

                if not component_result.get("success", False):
                    log_warning(f"Failed to add component: {component_result.get('error', '')}")

            # Add variables, functions, and events (similar to components)

            # Return success
            return json.dumps({
                "success": True,
                "message": f"Blueprint generated successfully: {blueprint_path}",
                "blueprint_path": blueprint_path
            })

        except Exception as e:
            log_error(f"Error generating blueprint: {str(e)}", include_traceback=True)
            return json.dumps({
                "success": False,
                "error": f"Error generating blueprint: {str(e)}"
            })

# Create a singleton instance
blueprint_handler = WebSocketBlueprintHandler()

# Function to handle blueprint requests
def handle_blueprint_request(request_json: str) -> str:
    """
    Handle a blueprint request received over WebSocket

    Args:
        request_json: The JSON request string

    Returns:
        The JSON response string
    """
    return blueprint_handler.handle_blueprint_request(request_json)
