import unreal
from typing import Dict, Any, List, Tuple

from utils import unreal_conversions as uc
from utils import logging as log


def handle_spawn(command: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle a spawn command
    
    Args:
        command: The command dictionary containing:
            - actor_class: Actor class name or path
            - location: [X, Y, Z] coordinates (optional)
            - rotation: [Pitch, Yaw, Roll] in degrees (optional)
            - scale: [X, Y, Z] scale factors (optional)
            - actor_label: Optional custom name for the actor
            
    Returns:
        Response dictionary with success/failure status and additional info
    """
    try:
        # Extract parameters
        actor_class_name = command.get("actor_class", "Cube")
        location = command.get("location", (0, 0, 0))
        rotation = command.get("rotation", (0, 0, 0))
        scale = command.get("scale", (1, 1, 1))
        actor_label = command.get("actor_label")

        log.log_command("spawn", f"Class: {actor_class_name}, Label: {actor_label}")

        # Import the C++ utility class
        gen_actor_utils = unreal.GenActorUtils

        # First handle specific cases for basic shapes
        actor_class_lower = actor_class_name.lower()

        # Map to properly capitalized names for finding assets
        shape_map = {
            "cube": "Cube",
            "sphere": "Sphere",
            "cylinder": "Cylinder",
            "cone": "Cone"
        }

        # Convert parameters to Unreal types
        loc = uc.to_unreal_vector(location)
        rot = uc.to_unreal_rotator(rotation)
        scale_vector = uc.to_unreal_vector(scale)

        actor = None

        # Use the right C++ function based on the actor type
        if actor_class_lower in shape_map:
            proper_name = shape_map[actor_class_lower]
            actor = gen_actor_utils.spawn_basic_shape(proper_name, loc, rot, scale_vector, actor_label or "")
        else:
            actor = gen_actor_utils.spawn_actor_from_class(actor_class_name, loc, rot, scale_vector, actor_label or "")

        if not actor:
            log.log_error(f"Failed to spawn actor of type {actor_class_name}")
            return {"success": False, "error": f"Failed to spawn actor of type {actor_class_name}"}

        actor_name = actor.get_actor_label()
        log.log_result("spawn", True, f"Actor: {actor_name} at {loc}")
        return {"success": True, "actor_name": actor_name}

    except Exception as e:
        log.log_error(f"Error spawning actor: {str(e)}", include_traceback=True)

        # Add hint for Claude to understand what went wrong
        error_msg = str(e)
        if "not found" in error_msg:
            hint = "\nHint: For basic shapes, use 'Cube', 'Sphere', 'Cylinder', or 'Cone'. For other actors, try using '/Script/Engine.PointLight' format."
            error_msg += hint

        return {"success": False, "error": error_msg}


def handle_create_material(command: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle a create_material command
    
    Args:
        command: The command dictionary containing:
            - material_name: Name for the new material
            - color: [R, G, B] color values (0-1)
            
    Returns:
        Response dictionary with success/failure status and material path if successful
    """
    try:
        # Extract parameters
        material_name = command.get("material_name", "NewMaterial")
        color = command.get("color", (1, 0, 0))

        log.log_command("create_material", f"Name: {material_name}, Color: {color}")

        # Use the C++ utility class
        gen_actor_utils = unreal.GenActorUtils
        color_linear = uc.to_unreal_color(color)

        material = gen_actor_utils.create_material(material_name, color_linear)

        if not material:
            log.log_error("Failed to create material")
            return {"success": False, "error": "Failed to create material"}

        material_path = f"/Game/Materials/{material_name}"
        log.log_result("create_material", True, f"Path: {material_path}")
        return {"success": True, "material_path": material_path}

    except Exception as e:
        log.log_error(f"Error creating material: {str(e)}", include_traceback=True)
        return {"success": False, "error": str(e)}


def handle_get_all_scene_objects(command: Dict[str, Any]) -> Dict[str, Any]:
    try:
        level = unreal.EditorLevelLibrary.get_level(unreal.EditorLevelLibrary.get_editor_world())
        actors = unreal.GameplayStatics.get_all_actors_of_class(level, unreal.Actor)
        result = [
            {"name": actor.get_name(), "class": actor.get_class().get_name(), "location": [actor.get_actor_location().x, actor.get_actor_location().y, actor.get_actor_location().z]}
            for actor in actors
        ]
        return {"success": True, "actors": result}
    except Exception as e:
        return {"success": False, "error": str(e)}

def handle_create_project_folder(command: Dict[str, Any]) -> Dict[str, Any]:
    try:
        folder_path = command.get("folder_path")
        full_path = f"/Game/{folder_path}"
        unreal.EditorAssetLibrary.make_directory(full_path)
        return {"success": True, "message": f"Created folder at {full_path}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def handle_get_files_in_folder(command: Dict[str, Any]) -> Dict[str, Any]:
    try:
        folder_path = f"/Game/{command.get('folder_path')}"
        files = unreal.EditorAssetLibrary.list_assets(folder_path, recursive=False)
        return {"success": True, "files": [str(f) for f in files]}
    except Exception as e:
        return {"success": False, "error": str(e)}

def handle_add_input_binding(command: Dict[str, Any]) -> Dict[str, Any]:
    try:
        action_name = command.get("action_name")
        key = command.get("key")
        input_settings = unreal.get_editor_subsystem(unreal.InputSettings)
        action_mapping = unreal.InputActionKeyMapping(action_name=action_name, key=unreal.InputCoreTypes.get_key(key))
        input_settings.add_action_mapping(action_mapping)
        input_settings.save_config()
        return {"success": True, "message": f"Added input binding {action_name} -> {key}"}
    except Exception as e:
        return {"success": False, "error": str(e)}