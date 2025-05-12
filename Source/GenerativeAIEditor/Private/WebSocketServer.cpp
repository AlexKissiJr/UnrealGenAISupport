// Copyright Alex Kissi Jr 2024. All rights Reserved. https://createlex.com/terms

#include "WebSocketServer.h"
#include "GenerativeAIEditor.h"
#include "WebSocketsModule.h"
#include "IWebSocketNetworkingModule.h"

// Define log macros for cleaner code
#define GENAI_LOG_INFO(Format, ...) UE_LOG(LogGenAI, Display, TEXT(Format), ##__VA_ARGS__)
#define GENAI_LOG_WARNING(Format, ...) UE_LOG(LogGenAI, Warning, TEXT(Format), ##__VA_ARGS__)
#define GENAI_LOG_ERROR(Format, ...) UE_LOG(LogGenAI, Error, TEXT(Format), ##__VA_ARGS__)

FWebSocketServer::FWebSocketServer(const FWebSocketServerConfig& InConfig)
    : Config(InConfig)
    , bIsRunning(false)
{
}

FWebSocketServer::~FWebSocketServer()
{
    Stop();
}

bool FWebSocketServer::Start()
{
    if (bIsRunning)
    {
        GENAI_LOG_WARNING("WebSocket Server is already running");
        return true;
    }
    
    GENAI_LOG_INFO("Starting WebSocket Server on port %d", Config.Port);
    
    // Initialize WebSockets module
    if (!FModuleManager::Get().IsModuleLoaded("WebSockets"))
    {
        FModuleManager::Get().LoadModule("WebSockets");
    }
    
    // Create WebSocket server
    WebSocketServer = FWebSocketsModule::Get().CreateServer();
    
    if (!WebSocketServer.IsValid())
    {
        GENAI_LOG_ERROR("Failed to create WebSocket server");
        return false;
    }
    
    // Configure the server
    WebSocketServer->OnConnectionAccepted().AddRaw(this, &FWebSocketServer::OnConnectionAccepted);
    
    // Start listening
    if (!WebSocketServer->Init(Config.Port, Config.bUseSecureWebSocket))
    {
        GENAI_LOG_ERROR("Failed to initialize WebSocket server on port %d", Config.Port);
        return false;
    }
    
    bIsRunning = true;
    GENAI_LOG_INFO("WebSocket Server started successfully on port %d", Config.Port);
    return true;
}

void FWebSocketServer::Stop()
{
    if (!bIsRunning)
    {
        return;
    }
    
    GENAI_LOG_INFO("Stopping WebSocket Server");
    
    // Close all connections
    {
        FScopeLock Lock(&ClientsLock);
        for (auto& Client : ConnectedClients)
        {
            if (Client.Value.IsValid() && Client.Value->IsConnected())
            {
                Client.Value->Close();
            }
        }
        ConnectedClients.Empty();
    }
    
    // Stop the server
    if (WebSocketServer.IsValid())
    {
        WebSocketServer->Stop();
        WebSocketServer.Reset();
    }
    
    bIsRunning = false;
    GENAI_LOG_INFO("WebSocket Server stopped");
}

bool FWebSocketServer::IsRunning() const
{
    return bIsRunning;
}

bool FWebSocketServer::SendMessage(const FString& ClientId, const FString& Message)
{
    FScopeLock Lock(&ClientsLock);
    
    TSharedPtr<IWebSocket>* ClientPtr = ConnectedClients.Find(ClientId);
    if (ClientPtr && ClientPtr->IsValid() && (*ClientPtr)->IsConnected())
    {
        (*ClientPtr)->Send(Message);
        return true;
    }
    
    return false;
}

void FWebSocketServer::BroadcastMessage(const FString& Message)
{
    FScopeLock Lock(&ClientsLock);
    
    for (auto& Client : ConnectedClients)
    {
        if (Client.Value.IsValid() && Client.Value->IsConnected())
        {
            Client.Value->Send(Message);
        }
    }
}

void FWebSocketServer::OnConnectionAccepted(const FString& InClientId, TSharedPtr<IWebSocket> WebSocket)
{
    FString ClientId = InClientId;
    
    // Register callbacks for this connection
    WebSocket->OnMessage().AddLambda([this, ClientId](const FString& Message)
    {
        this->OnMessageReceived(ClientId, Message);
    });
    
    WebSocket->OnClosed().AddLambda([this, ClientId](int32 StatusCode, const FString& Reason, bool bWasClean)
    {
        this->OnConnectionClosed(ClientId);
    });
    
    // Add to connected clients
    {
        FScopeLock Lock(&ClientsLock);
        ConnectedClients.Add(ClientId, WebSocket);
    }
    
    GENAI_LOG_INFO("WebSocket client connected: %s", *ClientId);
    
    // Broadcast the connection event
    OnClientConnected.Broadcast(ClientId);
}

void FWebSocketServer::OnConnectionClosed(const FString& ClientId)
{
    // Remove from connected clients
    {
        FScopeLock Lock(&ClientsLock);
        ConnectedClients.Remove(ClientId);
    }
    
    GENAI_LOG_INFO("WebSocket client disconnected: %s", *ClientId);
    
    // Broadcast the disconnection event
    OnClientDisconnected.Broadcast(ClientId);
}

void FWebSocketServer::OnMessageReceived(const FString& ClientId, const FString& Message)
{
    GENAI_LOG_INFO("WebSocket message received from %s: %s", *ClientId, *Message);
    
    // Broadcast the message event
    OnMessageReceived.Broadcast(ClientId, Message);
}
