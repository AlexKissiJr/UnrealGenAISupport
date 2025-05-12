import unreal

# Create an Editor Utility Widget for testing the WebSocket server
def create_websocket_test_widget():
    # Create the asset
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    
    # Create the factory
    factory = unreal.EditorUtilityWidgetBlueprint()
    
    # Create the asset
    asset_path = "/Game/WebSocketTest"
    asset_name = "WebSocketTestWidget"
    package_path = f"{asset_path}/{asset_name}"
    
    # Check if the asset already exists
    if unreal.EditorAssetLibrary.does_asset_exist(package_path):
        unreal.log_warning(f"Asset {package_path} already exists. Skipping creation.")
        return unreal.EditorAssetLibrary.load_asset(package_path)
    
    # Create the asset
    asset = asset_tools.create_asset(asset_name, asset_path, unreal.EditorUtilityWidgetBlueprint, factory)
    
    # Save the asset
    unreal.EditorAssetLibrary.save_asset(package_path)
    
    unreal.log_info(f"Created WebSocket Test Widget at {package_path}")
    return asset

# Create the widget
widget = create_websocket_test_widget()

# Open the widget in the editor
if widget:
    unreal.log_info("Opening WebSocket Test Widget in the editor...")
    unreal.AssetEditorSubsystem.get_instance().open_editor_for_assets([widget])
