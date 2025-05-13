import json
import inspect
import sys
import os
import traceback
from typing import Any, Callable, Dict, List, Optional, Union, get_type_hints

class FastMCP:
    """
    A simple MCP (Model-Controller-Presenter) server for Unreal Engine.
    This is a lightweight implementation to support the existing mcp_server.py.
    """
    
    def __init__(self, name: str):
        """
        Initialize the FastMCP server.
        
        Args:
            name: The name of the server
        """
        self.name = name
        self.tools = {}
        self.tool_descriptions = {}
        
    def tool(self, description: str = None):
        """
        Decorator to register a function as a tool.
        
        Args:
            description: Optional description of the tool
        """
        def decorator(func):
            tool_name = func.__name__
            self.tools[tool_name] = func
            
            # Get the function's docstring as the description if not provided
            if description is None and func.__doc__:
                self.tool_descriptions[tool_name] = func.__doc__.strip()
            else:
                self.tool_descriptions[tool_name] = description or ""
                
            return func
        
        # Handle case where decorator is used without parentheses
        if callable(description):
            func = description
            description = None
            return decorator(func)
            
        return decorator
        
    def get_tools(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all registered tools with their descriptions and parameters.
        
        Returns:
            A dictionary of tool names to tool information
        """
        tools_info = {}
        
        for tool_name, func in self.tools.items():
            # Get parameter information
            sig = inspect.signature(func)
            params = []
            
            for param_name, param in sig.parameters.items():
                param_info = {
                    "name": param_name,
                    "required": param.default == inspect.Parameter.empty
                }
                
                # Try to get type hints
                try:
                    type_hints = get_type_hints(func)
                    if param_name in type_hints:
                        param_info["type"] = str(type_hints[param_name])
                except:
                    pass
                    
                params.append(param_info)
                
            # Add tool information
            tools_info[tool_name] = {
                "description": self.tool_descriptions.get(tool_name, ""),
                "parameters": params
            }
            
        return tools_info
        
    def call_tool(self, tool_name: str, **kwargs) -> Any:
        """
        Call a registered tool by name.
        
        Args:
            tool_name: The name of the tool to call
            **kwargs: Arguments to pass to the tool
            
        Returns:
            The result of the tool call
        """
        if tool_name not in self.tools:
            raise ValueError(f"Tool '{tool_name}' not found")
            
        tool = self.tools[tool_name]
        
        try:
            return tool(**kwargs)
        except Exception as e:
            traceback.print_exc()
            return f"Error calling tool '{tool_name}': {str(e)}"
