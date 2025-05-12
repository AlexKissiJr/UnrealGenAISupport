import unreal

# Create a Blueprint for testing the WebSocket functionality
def create_websocket_test_blueprint():
    # Create the asset
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    
    # Create the factory
    factory = unreal.BlueprintFactory()
    factory.set_editor_property('ParentClass', unreal.Actor)
    
    # Create the asset
    asset_path = "/Game/WebSocketTest"
    asset_name = "BP_WebSocketTest"
    package_path = f"{asset_path}/{asset_name}"
    
    # Check if the asset already exists
    if unreal.EditorAssetLibrary.does_asset_exist(package_path):
        unreal.log_warning(f"Asset {package_path} already exists. Skipping creation.")
        return unreal.EditorAssetLibrary.load_asset(package_path)
    
    # Create the asset
    asset = asset_tools.create_asset(asset_name, asset_path, unreal.Blueprint, factory)
    
    # Save the asset
    unreal.EditorAssetLibrary.save_asset(package_path)
    
    unreal.log_info(f"Created WebSocket Test Blueprint at {package_path}")
    return asset

# Create the Blueprint
blueprint = create_websocket_test_blueprint()

# Open the Blueprint in the editor
if blueprint:
    unreal.log_info("Opening WebSocket Test Blueprint in the editor...")
    unreal.AssetEditorSubsystem.get_instance().open_editor_for_assets([blueprint])
