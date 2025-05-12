#include "Network/GenWebSocketClient.h"
#include "WebSocketsModule.h"
#include "IWebSocket.h"
#include "Json.h"
#include "JsonUtilities.h"

UGenWebSocketClient::UGenWebSocketClient()
    : bIsConnected(false)
{
}

UGenWebSocketClient::~UGenWebSocketClient()
{
    Disconnect();
}

void UGenWebSocketClient::Tick(float DeltaTime)
{
    // Process any messages that have been queued from the WebSocket thread
    ProcessMessages();
}

bool UGenWebSocketClient::IsTickable() const
{
    return !IsTemplate() && !IsBeingDestroyed() && !HasAnyFlags(RF_BeginDestroyed | RF_FinishDestroyed);
}

TStatId UGenWebSocketClient::GetStatId() const
{
    RETURN_QUICK_DECLARE_CYCLE_STAT(UGenWebSocketClient, STATGROUP_Tickables);
}

bool UGenWebSocketClient::Connect(const FString& ServerURL, const FString& Protocol)
{
    // Don't try to connect if already connected
    if (Socket.IsValid() && Socket->IsConnected())
    {
        UE_LOG(LogTemp, Warning, TEXT("WebSocket already connected"));
        return false;
    }

    // Create the WebSocket
    Socket = FWebSocketsModule::Get().CreateWebSocket(ServerURL, Protocol);

    if (!Socket.IsValid())
    {
        LastError = TEXT("Failed to create WebSocket");
        UE_LOG(LogTemp, Error, TEXT("%s"), *LastError);
        OnError.Broadcast(LastError);
        return false;
    }

    // Setup event handlers
    SetupWebSocketHandlers();

    // Connect to the server
    Socket->Connect();

    UE_LOG(LogTemp, Log, TEXT("WebSocket connecting to %s"), *ServerURL);
    return true;
}

void UGenWebSocketClient::Disconnect()
{
    if (Socket.IsValid() && Socket->IsConnected())
    {
        Socket->Close();
        UE_LOG(LogTemp, Log, TEXT("WebSocket disconnected"));
    }

    // Reset state
    Socket.Reset();
    bIsConnected = false;
}

bool UGenWebSocketClient::SendMessage(const FString& Message)
{
    if (!Socket.IsValid() || !Socket->IsConnected())
    {
        LastError = TEXT("WebSocket not connected");
        UE_LOG(LogTemp, Warning, TEXT("%s"), *LastError);
        return false;
    }

    // Add newline terminator as per our protocol
    FString MessageWithNewline = Message;
    if (!MessageWithNewline.EndsWith(TEXT("\n")))
    {
        MessageWithNewline.Append(TEXT("\n"));
    }

    // Send the message
    Socket->Send(MessageWithNewline);

    UE_LOG(LogTemp, Verbose, TEXT("WebSocket sent: %s"), *Message);
    return true;
}

bool UGenWebSocketClient::SendJsonCommand(const FString& Command, const FString& Params)
{
    // Create a JSON object
    TSharedPtr<FJsonObject> JsonObject = MakeShareable(new FJsonObject);
    JsonObject->SetStringField(TEXT("type"), Command);

    // Parse and add the parameters if provided
    if (!Params.IsEmpty())
    {
        TSharedPtr<FJsonObject> ParamsObject;
        TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(Params);

        if (FJsonSerializer::Deserialize(Reader, ParamsObject))
        {
            // Add each parameter to the main JSON object
            for (auto& Pair : ParamsObject->Values)
            {
                JsonObject->SetField(Pair.Key, Pair.Value);
            }
        }
        else
        {
            // If params is not valid JSON, add it as a message field
            JsonObject->SetStringField(TEXT("message"), Params);
        }
    }

    // Convert to string
    FString JsonString;
    TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&JsonString);
    FJsonSerializer::Serialize(JsonObject.ToSharedRef(), Writer);

    // Send the JSON message
    return SendMessage(JsonString);
}

bool UGenWebSocketClient::IsConnected() const
{
    return Socket.IsValid() && Socket->IsConnected();
}

FString UGenWebSocketClient::GetLastError() const
{
    return LastError;
}

void UGenWebSocketClient::SetupWebSocketHandlers()
{
    if (!Socket.IsValid())
    {
        return;
    }

    // Connected event
    Socket->OnConnected().AddLambda([this]() {
        // This code runs on the WebSocket thread, so we need to defer to the game thread
        AsyncTask(ENamedThreads::GameThread, [this]() {
            bIsConnected = true;
            UE_LOG(LogTemp, Log, TEXT("WebSocket connected"));
            OnConnected.Broadcast(true);
        });
    });

    // Connection error event
    Socket->OnConnectionError().AddLambda([this](const FString& Error) {
        // This code runs on the WebSocket thread, so we need to defer to the game thread
        AsyncTask(ENamedThreads::GameThread, [this, Error]() {
            LastError = Error;
            bIsConnected = false;
            UE_LOG(LogTemp, Error, TEXT("WebSocket connection error: %s"), *Error);
            OnConnected.Broadcast(false);
            OnError.Broadcast(Error);
        });
    });

    // Message received event
    Socket->OnMessage().AddLambda([this](const FString& Message) {
        // Queue the message to be processed on the game thread
        MessageQueue.Enqueue(Message);
    });

    // Connection closed event
    Socket->OnClosed().AddLambda([this](int32 StatusCode, const FString& Reason, bool bWasClean) {
        // This code runs on the WebSocket thread, so we need to defer to the game thread
        AsyncTask(ENamedThreads::GameThread, [this, StatusCode, Reason]() {
            bIsConnected = false;
            UE_LOG(LogTemp, Log, TEXT("WebSocket closed: %s (Code: %d)"), *Reason, StatusCode);
            OnClosed.Broadcast(StatusCode, Reason);
        });
    });
}

void UGenWebSocketClient::ProcessMessages()
{
    // Process all queued messages
    FString Message;
    while (MessageQueue.Dequeue(Message))
    {
        // Remove trailing newline if present
        if (Message.EndsWith(TEXT("\n")))
        {
            Message.LeftChopInline(1);
        }

        UE_LOG(LogTemp, Verbose, TEXT("WebSocket received: %s"), *Message);
        OnMessage.Broadcast(Message);
    }
}
