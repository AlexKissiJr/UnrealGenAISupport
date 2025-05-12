#include "Network/GenWebSocketManager.h"
#include "Network/GenWebSocketClient.h"
#include "Json.h"
#include "JsonUtilities.h"

UGenWebSocketManager::UGenWebSocketManager()
    : WebSocketClient(nullptr)
{
}

UGenWebSocketManager::~UGenWebSocketManager()
{
    Shutdown();
}

bool UGenWebSocketManager::Initialize(const FString& ServerURL)
{
    // Create the WebSocket client if it doesn't exist
    if (!WebSocketClient)
    {
        WebSocketClient = NewObject<UGenWebSocketClient>(this);
        
        if (!WebSocketClient)
        {
            UE_LOG(LogTemp, Error, TEXT("Failed to create WebSocket client"));
            return false;
        }
        
        // Bind to WebSocket events
        WebSocketClient->OnConnected.AddDynamic(this, &UGenWebSocketManager::OnWebSocketConnected);
        WebSocketClient->OnMessage.AddDynamic(this, &UGenWebSocketManager::OnWebSocketMessage);
        WebSocketClient->OnClosed.AddDynamic(this, &UGenWebSocketManager::OnWebSocketClosed);
        WebSocketClient->OnError.AddDynamic(this, &UGenWebSocketManager::OnWebSocketError);
    }
    
    // Connect to the server
    return WebSocketClient->Connect(ServerURL);
}

void UGenWebSocketManager::Shutdown()
{
    if (WebSocketClient)
    {
        WebSocketClient->Disconnect();
        WebSocketClient = nullptr;
    }
}

bool UGenWebSocketManager::SendHandshake(const FString& Message)
{
    if (!WebSocketClient || !WebSocketClient->IsConnected())
    {
        UE_LOG(LogTemp, Warning, TEXT("WebSocket not connected"));
        return false;
    }
    
    // Create a handshake message
    return WebSocketClient->SendJsonCommand(TEXT("handshake"), FString::Printf(TEXT("{\"message\": \"%s\"}"), *Message));
}

bool UGenWebSocketManager::ExecutePython(const FString& PythonCode)
{
    if (!WebSocketClient || !WebSocketClient->IsConnected())
    {
        UE_LOG(LogTemp, Warning, TEXT("WebSocket not connected"));
        return false;
    }
    
    // Create a Python execution command
    return WebSocketClient->SendJsonCommand(TEXT("execute_python"), FString::Printf(TEXT("{\"code\": \"%s\"}"), *PythonCode));
}

bool UGenWebSocketManager::IsConnected() const
{
    return WebSocketClient && WebSocketClient->IsConnected();
}

void UGenWebSocketManager::OnWebSocketConnected(bool bSuccess)
{
    if (bSuccess)
    {
        UE_LOG(LogTemp, Log, TEXT("WebSocket connected successfully"));
        
        // Send a handshake message
        SendHandshake();
    }
    else
    {
        UE_LOG(LogTemp, Error, TEXT("WebSocket connection failed"));
    }
}

void UGenWebSocketManager::OnWebSocketMessage(const FString& Message)
{
    UE_LOG(LogTemp, Log, TEXT("WebSocket message received: %s"), *Message);
    
    // Store the last response
    LastResponse = Message;
    
    // Parse the JSON response
    TSharedPtr<FJsonObject> JsonObject;
    TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(Message);
    
    if (FJsonSerializer::Deserialize(Reader, JsonObject))
    {
        // Check if the response was successful
        bool bSuccess = false;
        if (JsonObject->TryGetBoolField(TEXT("success"), bSuccess))
        {
            if (bSuccess)
            {
                UE_LOG(LogTemp, Log, TEXT("WebSocket command succeeded"));
            }
            else
            {
                FString Error;
                if (JsonObject->TryGetStringField(TEXT("error"), Error))
                {
                    UE_LOG(LogTemp, Warning, TEXT("WebSocket command failed: %s"), *Error);
                }
                else
                {
                    UE_LOG(LogTemp, Warning, TEXT("WebSocket command failed with unknown error"));
                }
            }
        }
    }
    else
    {
        UE_LOG(LogTemp, Warning, TEXT("Failed to parse WebSocket response as JSON"));
    }
}

void UGenWebSocketManager::OnWebSocketClosed(int32 StatusCode, const FString& Reason)
{
    UE_LOG(LogTemp, Log, TEXT("WebSocket closed: %s (Code: %d)"), *Reason, StatusCode);
}

void UGenWebSocketManager::OnWebSocketError(const FString& Error)
{
    UE_LOG(LogTemp, Error, TEXT("WebSocket error: %s"), *Error);
}
