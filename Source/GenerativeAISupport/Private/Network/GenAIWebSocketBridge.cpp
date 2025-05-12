#include "Network/GenAIWebSocketBridge.h"
#include "Network/GenWebSocketManager.h"
#include "Models/OpenAI/GenOAIChat.h"
#include "Models/Anthropic/GenClaudeChat.h"
#include "Models/DeepSeek/GenDSeekChat.h"
#include "Json.h"
#include "JsonUtilities.h"

UGenAIWebSocketBridge::UGenAIWebSocketBridge()
    : WebSocketManager(nullptr)
    , OAIChat(nullptr)
    , ClaudeChat(nullptr)
    , DSeekChat(nullptr)
{
}

UGenAIWebSocketBridge::~UGenAIWebSocketBridge()
{
}

bool UGenAIWebSocketBridge::Initialize(UGenWebSocketManager* InWebSocketManager)
{
    if (!InWebSocketManager)
    {
        UE_LOG(LogTemp, Error, TEXT("WebSocket manager is null"));
        return false;
    }

    WebSocketManager = InWebSocketManager;

    // Bind to WebSocket messages
    if (WebSocketManager->GetWebSocketClient())
    {
        WebSocketManager->GetWebSocketClient()->OnMessage.AddDynamic(this, &UGenAIWebSocketBridge::OnWebSocketMessage);
    }
    else
    {
        UE_LOG(LogTemp, Error, TEXT("WebSocket client is null"));
        return false;
    }

    return true;
}

void UGenAIWebSocketBridge::SetOpenAIChat(UGenOAIChat* InOAIChat)
{
    OAIChat = InOAIChat;
}

void UGenAIWebSocketBridge::SetClaudeChat(UGenClaudeChat* InClaudeChat)
{
    ClaudeChat = InClaudeChat;
}

void UGenAIWebSocketBridge::SetDeepSeekChat(UGenDSeekChat* InDSeekChat)
{
    DSeekChat = InDSeekChat;
}

bool UGenAIWebSocketBridge::SendAIRequest(const FString& ModelType, const FString& Prompt, const FString& SystemPrompt)
{
    if (!WebSocketManager || !WebSocketManager->IsConnected())
    {
        UE_LOG(LogTemp, Warning, TEXT("WebSocket not connected"));
        return false;
    }

    // Create a JSON object for the request
    TSharedPtr<FJsonObject> JsonObject = MakeShareable(new FJsonObject);
    JsonObject->SetStringField(TEXT("type"), TEXT("ai_request"));
    JsonObject->SetStringField(TEXT("model_type"), ModelType);
    JsonObject->SetStringField(TEXT("prompt"), Prompt);

    if (!SystemPrompt.IsEmpty())
    {
        JsonObject->SetStringField(TEXT("system_prompt"), SystemPrompt);
    }

    // Convert to string
    FString JsonString;
    TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&JsonString);
    FJsonSerializer::Serialize(JsonObject.ToSharedRef(), Writer);

    // Send the message
    return WebSocketManager->GetWebSocketClient()->SendMessage(JsonString);
}

void UGenAIWebSocketBridge::OnWebSocketMessage(const FString& Message)
{
    // Parse the JSON message
    TSharedPtr<FJsonObject> JsonObject;
    TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(Message);

    if (FJsonSerializer::Deserialize(Reader, JsonObject))
    {
        // Check if this is an AI request
        FString Type;
        if (JsonObject->TryGetStringField(TEXT("type"), Type) && Type == TEXT("ai_request"))
        {
            // Process the AI request
            FString Response = ProcessAIRequest(Message);

            // Send the response
            if (WebSocketManager && WebSocketManager->IsConnected())
            {
                WebSocketManager->GetWebSocketClient()->SendMessage(Response);
            }
        }
    }
}

FString UGenAIWebSocketBridge::ProcessAIRequest(const FString& RequestJson)
{
    // Parse the JSON request
    TSharedPtr<FJsonObject> JsonObject;
    TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(RequestJson);

    if (FJsonSerializer::Deserialize(Reader, JsonObject))
    {
        // Get the model type
        FString ModelType;
        if (JsonObject->TryGetStringField(TEXT("model_type"), ModelType))
        {
            if (ModelType.Equals(TEXT("openai"), ESearchCase::IgnoreCase))
            {
                return ProcessOpenAIRequest(JsonObject);
            }
            else if (ModelType.Equals(TEXT("claude"), ESearchCase::IgnoreCase))
            {
                return ProcessClaudeRequest(JsonObject);
            }
            else if (ModelType.Equals(TEXT("deepseek"), ESearchCase::IgnoreCase))
            {
                return ProcessDeepSeekRequest(JsonObject);
            }
            else
            {
                // Unknown model type
                TSharedPtr<FJsonObject> ResponseObject = MakeShareable(new FJsonObject);
                ResponseObject->SetStringField(TEXT("type"), TEXT("ai_response"));
                ResponseObject->SetBoolField(TEXT("success"), false);
                ResponseObject->SetStringField(TEXT("error"), FString::Printf(TEXT("Unknown model type: %s"), *ModelType));

                FString ResponseJson;
                TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&ResponseJson);
                FJsonSerializer::Serialize(ResponseObject.ToSharedRef(), Writer);

                return ResponseJson;
            }
        }
    }

    // Invalid request
    TSharedPtr<FJsonObject> ResponseObject = MakeShareable(new FJsonObject);
    ResponseObject->SetStringField(TEXT("type"), TEXT("ai_response"));
    ResponseObject->SetBoolField(TEXT("success"), false);
    ResponseObject->SetStringField(TEXT("error"), TEXT("Invalid AI request"));

    FString ResponseJson;
    TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&ResponseJson);
    FJsonSerializer::Serialize(ResponseObject.ToSharedRef(), Writer);

    return ResponseJson;
}

FString UGenAIWebSocketBridge::ProcessOpenAIRequest(const TSharedPtr<FJsonObject>& JsonObject)
{
    if (!OAIChat)
    {
        // OpenAI chat model not set
        TSharedPtr<FJsonObject> ResponseObject = MakeShareable(new FJsonObject);
        ResponseObject->SetStringField(TEXT("type"), TEXT("ai_response"));
        ResponseObject->SetBoolField(TEXT("success"), false);
        ResponseObject->SetStringField(TEXT("error"), TEXT("OpenAI chat model not set"));

        FString ResponseJson;
        TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&ResponseJson);
        FJsonSerializer::Serialize(ResponseObject.ToSharedRef(), Writer);

        return ResponseJson;
    }

    // Get the prompt and system prompt
    FString Prompt;
    FString SystemPrompt;
    JsonObject->TryGetStringField(TEXT("prompt"), Prompt);
    JsonObject->TryGetStringField(TEXT("system_prompt"), SystemPrompt);

    // TODO: Implement actual OpenAI request processing
    // This would involve calling OAIChat methods and handling the response

    // For now, return a placeholder response
    TSharedPtr<FJsonObject> ResponseObject = MakeShareable(new FJsonObject);
    ResponseObject->SetStringField(TEXT("type"), TEXT("ai_response"));
    ResponseObject->SetBoolField(TEXT("success"), true);
    ResponseObject->SetStringField(TEXT("model_type"), TEXT("openai"));
    ResponseObject->SetStringField(TEXT("response"), TEXT("This is a placeholder response from OpenAI"));

    FString ResponseJson;
    TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&ResponseJson);
    FJsonSerializer::Serialize(ResponseObject.ToSharedRef(), Writer);

    return ResponseJson;
}

FString UGenAIWebSocketBridge::ProcessClaudeRequest(const TSharedPtr<FJsonObject>& JsonObject)
{
    // Similar implementation to ProcessOpenAIRequest but for Claude
    // Placeholder for now
    TSharedPtr<FJsonObject> ResponseObject = MakeShareable(new FJsonObject);
    ResponseObject->SetStringField(TEXT("type"), TEXT("ai_response"));
    ResponseObject->SetBoolField(TEXT("success"), true);
    ResponseObject->SetStringField(TEXT("model_type"), TEXT("claude"));
    ResponseObject->SetStringField(TEXT("response"), TEXT("This is a placeholder response from Claude"));

    FString ResponseJson;
    TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&ResponseJson);
    FJsonSerializer::Serialize(ResponseObject.ToSharedRef(), Writer);

    return ResponseJson;
}

FString UGenAIWebSocketBridge::ProcessDeepSeekRequest(const TSharedPtr<FJsonObject>& JsonObject)
{
    // Similar implementation to ProcessOpenAIRequest but for DeepSeek
    // Placeholder for now
    TSharedPtr<FJsonObject> ResponseObject = MakeShareable(new FJsonObject);
    ResponseObject->SetStringField(TEXT("type"), TEXT("ai_response"));
    ResponseObject->SetBoolField(TEXT("success"), true);
    ResponseObject->SetStringField(TEXT("model_type"), TEXT("deepseek"));
    ResponseObject->SetStringField(TEXT("response"), TEXT("This is a placeholder response from DeepSeek"));

    FString ResponseJson;
    TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&ResponseJson);
    FJsonSerializer::Serialize(ResponseObject.ToSharedRef(), Writer);

    return ResponseJson;
}
