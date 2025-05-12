import unreal

def log_info(message):
    """Log info message"""
    unreal.log(f"[WebSocket Test BP] {message}")

def log_warning(message):
    """Log warning message"""
    unreal.log_warning(f"[WebSocket Test BP] {message}")

def log_error(message):
    """Log error message"""
    unreal.log_error(f"[WebSocket Test BP] {message}")

def create_websocket_test_blueprint():
    """Create a Blueprint for testing the WebSocket client"""
    try:
        # Get asset tools
        asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
        
        # Create Blueprint factory
        factory = unreal.BlueprintFactory()
        factory.set_editor_property('ParentClass', unreal.Actor)
        
        # Create the Blueprint
        asset_path = "/Game/WebSocketTest"
        asset_name = "BP_WebSocketTest"
        package_path = f"{asset_path}/{asset_name}"
        
        # Check if the asset already exists
        if unreal.EditorAssetLibrary.does_asset_exist(package_path):
            log_warning(f"Blueprint {package_path} already exists. Loading existing asset.")
            blueprint = unreal.EditorAssetLibrary.load_asset(package_path)
        else:
            # Create the asset
            blueprint = asset_tools.create_asset(asset_name, asset_path, unreal.Blueprint, factory)
            
            # Get the Blueprint object
            blueprint_obj = unreal.EditorAssetLibrary.load_blueprint_class(package_path)
            
            # Add components and variables
            blueprint_utils = unreal.EditorUtilityLibrary.get_blueprint_asset_editor_for_asset(blueprint)
            
            if blueprint_utils:
                # Add WebSocket client variable
                websocket_client_var = unreal.EditorUtilityLibrary.add_variable(
                    blueprint,
                    "WebSocketClient",
                    unreal.EditorUtilityLibrary.get_object_class_from_path("/Script/GenerativeAISupport.GenWebSocketClient")
                )
                
                # Set variable properties
                if websocket_client_var:
                    websocket_client_var.set_meta_data("Category", "WebSocket")
                    websocket_client_var.set_editor_property("BlueprintReadWrite", True)
                    websocket_client_var.set_editor_property("ExposeOnSpawn", False)
                
                # Add server URL variable
                server_url_var = unreal.EditorUtilityLibrary.add_variable(
                    blueprint,
                    "ServerURL",
                    unreal.EditorUtilityLibrary.get_object_class_from_path("/Script/CoreUObject.String")
                )
                
                # Set variable properties
                if server_url_var:
                    server_url_var.set_meta_data("Category", "WebSocket")
                    server_url_var.set_editor_property("BlueprintReadWrite", True)
                    server_url_var.set_editor_property("ExposeOnSpawn", True)
                    
                    # Set default value
                    default_value = unreal.EditorUtilityLibrary.get_default_object(blueprint_obj)
                    default_value.set_editor_property("ServerURL", "ws://localhost:9877")
            
            # Save the Blueprint
            unreal.EditorAssetLibrary.save_asset(package_path)
            
            log_info(f"Created WebSocket test Blueprint at {package_path}")
        
        # Open the Blueprint in the editor
        unreal.AssetEditorSubsystem.get_instance().open_editor_for_assets([blueprint])
        
        return blueprint
    except Exception as e:
        log_error(f"Error creating WebSocket test Blueprint: {str(e)}")
        import traceback
        log_error(traceback.format_exc())
        return None

# Create the Blueprint
if __name__ == "__main__":
    create_websocket_test_blueprint()

# Function to run from Unreal Engine
def create_blueprint():
    """Create a Blueprint for testing the WebSocket client"""
    return create_websocket_test_blueprint()
