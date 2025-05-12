# WebSocket Integration with GenerativeAI Support

This document describes how to integrate the WebSocket functionality with the GenerativeAI Support plugin features.

## Overview

The WebSocket implementation provides a robust communication channel between Unreal Engine and external applications. This integration allows you to:

1. Send AI requests and receive responses over WebSocket
2. Create and modify Blueprints through WebSocket commands
3. Manipulate actors and their properties via WebSocket
4. Control the AI models (OpenAI, Claude, DeepSeek) remotely

## Components

The integration consists of several key components:

1. **WebSocket Server**: The Python-based WebSocket server that handles connections and commands
2. **WebSocket Client**: The C++ WebSocket client for communicating with the server
3. **AI WebSocket Bridge**: Connects AI models with WebSocket functionality
4. **Blueprint Handler**: Processes Blueprint-related commands
5. **Actor Handler**: Processes actor-related commands

## Setup Instructions

### 1. Start the WebSocket Server

```python
# In Python
import websocket_server
websocket_server.initialize_server()
```

### 2. Create an AI WebSocket Bridge

```cpp
// In C++
UGenWebSocketManager* WebSocketManager = NewObject<UGenWebSocketManager>();
WebSocketManager->Initialize("ws://localhost:9877");

UGenAIWebSocketBridge* AIBridge = NewObject<UGenAIWebSocketBridge>();
AIBridge->Initialize(WebSocketManager);

// Set up AI models
UGenOAIChat* OAIChat = NewObject<UGenOAIChat>();
OAIChat->Initialize("your-api-key");
AIBridge->SetOpenAIChat(OAIChat);

UGenClaudeChat* ClaudeChat = NewObject<UGenClaudeChat>();
ClaudeChat->Initialize("your-api-key");
AIBridge->SetClaudeChat(ClaudeChat);
```

### 3. Blueprint Setup

Create a Blueprint actor with the following components:

1. Add a `GenWebSocketManager` variable
2. Add a `GenAIWebSocketBridge` variable
3. In `BeginPlay`:
   - Create and initialize the WebSocket manager
   - Create and initialize the AI bridge
   - Set up the AI models

## Usage Examples

### 1. AI Requests via WebSocket

#### From External Client to Unreal Engine

```json
{
  "type": "ai_request",
  "model_type": "openai",
  "prompt": "Generate a description for a fantasy character",
  "system_prompt": "You are a creative writing assistant"
}
```

#### From Unreal Engine to External Client

```json
{
  "type": "ai_response",
  "success": true,
  "model_type": "openai",
  "response": "Elyndra is a half-elven sorceress with silver hair..."
}
```

### 2. Blueprint Operations via WebSocket

#### Create a Blueprint

```json
{
  "type": "blueprint_operation",
  "operation": "create_blueprint",
  "blueprint_path": "/Game/Blueprints/MyCharacter",
  "parent_class": "Character"
}
```

#### Add a Component

```json
{
  "type": "blueprint_operation",
  "operation": "add_component",
  "blueprint_path": "/Game/Blueprints/MyCharacter",
  "component_class": "SkeletalMeshComponent",
  "component_name": "CharacterMesh"
}
```

#### Generate a Complete Blueprint

```json
{
  "type": "blueprint_operation",
  "operation": "generate_blueprint",
  "blueprint_spec": {
    "blueprint_path": "/Game/Blueprints/MyCharacter",
    "parent_class": "Character",
    "components": [
      {
        "component_class": "SkeletalMeshComponent",
        "component_name": "CharacterMesh"
      },
      {
        "component_class": "CameraComponent",
        "component_name": "FollowCamera"
      }
    ],
    "variables": [
      {
        "name": "Health",
        "type": "float",
        "default_value": 100.0
      }
    ],
    "functions": [
      {
        "name": "TakeDamage",
        "parameters": [
          {
            "name": "DamageAmount",
            "type": "float"
          }
        ]
      }
    ]
  }
}
```

### 3. Actor Operations via WebSocket

#### Modify an Actor Property

```json
{
  "type": "actor_operation",
  "operation": "modify_object",
  "object_path": "/Game/Level/MyActor",
  "property_name": "Health",
  "property_value": 50.0
}
```

#### Get Actor Properties

```json
{
  "type": "actor_operation",
  "operation": "get_actor_properties",
  "actor_path": "/Game/Level/MyActor"
}
```

#### Set Actor Properties

```json
{
  "type": "actor_operation",
  "operation": "set_actor_properties",
  "actor_path": "/Game/Level/MyActor",
  "properties": {
    "location": {
      "x": 100.0,
      "y": 200.0,
      "z": 0.0
    },
    "rotation": {
      "pitch": 0.0,
      "yaw": 90.0,
      "roll": 0.0
    }
  }
}
```

## Blueprint Example: AI-Controlled Character

Here's an example of how to create a character that uses AI via WebSocket:

1. Create a new Blueprint based on Character
2. Add the following components:
   - `GenWebSocketManager`
   - `GenAIWebSocketBridge`
3. In the `BeginPlay` event:
   - Initialize the WebSocket manager
   - Initialize the AI bridge
   - Set up the AI models
4. Create a custom event `AskAI` with a string parameter `Question`
5. In the `AskAI` event:
   - Call `SendAIRequest` on the AI bridge with the question
6. Create a custom event `OnAIResponse` with a string parameter `Response`
7. Bind this event to the `OnMessage` delegate of the WebSocket client

## Integration with External Applications

You can integrate this WebSocket functionality with various external applications:

1. **Web Applications**: Create a web interface for controlling AI and Blueprints
2. **Mobile Apps**: Build a companion app for your Unreal Engine project
3. **Python Scripts**: Write scripts to automate tasks in Unreal Engine
4. **Other Game Engines**: Connect Unity or Godot to your Unreal Engine project

## Troubleshooting

If you encounter issues with the WebSocket integration:

1. Check that the WebSocket server is running
2. Verify that the port (9877) is not blocked by a firewall
3. Make sure the message format is correct (JSON with newline terminator)
4. Check the Unreal Engine Output Log for error messages
5. Verify that the AI models are properly initialized

## Next Steps

1. **Implement Authentication**: Add security to your WebSocket connections
2. **Add Binary Message Support**: For more efficient data transfer
3. **Create a Visual Editor**: Build a web-based visual editor for Blueprints
4. **Implement Real-time Collaboration**: Allow multiple users to work together
