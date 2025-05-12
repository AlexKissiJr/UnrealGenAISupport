// Copyright Alex Kissi Jr 2024. All rights Reserved. https://createlex.com/terms

#pragma once

#include "CoreMinimal.h"
#include "IWebSocket.h"
#include "IWebSocketServer.h"

/**
 * WebSocket server config structure
 */
struct FWebSocketServerConfig
{
    // Port to listen on
    int32 Port = 8080;
    
    // Max connections
    int32 MaxConnections = 10;
    
    // Whether to use secure WebSocket (wss://)
    bool bUseSecureWebSocket = false;
    
    // Server name
    FString ServerName = TEXT("GenerativeAI WebSocket Server");
};

/**
 * Delegate for WebSocket message events
 */
DECLARE_MULTICAST_DELEGATE_TwoParams(FOnWebSocketMessageReceived, const FString& /* ClientId */, const FString& /* Message */);
DECLARE_MULTICAST_DELEGATE_OneParam(FOnWebSocketClientConnected, const FString& /* ClientId */);
DECLARE_MULTICAST_DELEGATE_OneParam(FOnWebSocketClientDisconnected, const FString& /* ClientId */);

/**
 * WebSocket server implementation for GenerativeAI
 */
class GENERATIVEAIEDITOR_API FWebSocketServer
{
public:
    FWebSocketServer(const FWebSocketServerConfig& InConfig = FWebSocketServerConfig());
    virtual ~FWebSocketServer();
    
    // Start the server
    bool Start();
    
    // Stop the server
    void Stop();
    
    // Check if the server is running
    bool IsRunning() const;
    
    // Get the server config
    const FWebSocketServerConfig& GetConfig() const { return Config; }
    
    // Send a message to a specific client
    bool SendMessage(const FString& ClientId, const FString& Message);
    
    // Send a message to all connected clients
    void BroadcastMessage(const FString& Message);
    
    // Event delegates
    FOnWebSocketMessageReceived OnMessageReceived;
    FOnWebSocketClientConnected OnClientConnected;
    FOnWebSocketClientDisconnected OnClientDisconnected;
    
private:
    // WebSocket server instance
    TSharedPtr<IWebSocketServer> WebSocketServer;
    
    // Connected clients
    TMap<FString, TSharedPtr<IWebSocket>> ConnectedClients;
    
    // Server configuration
    FWebSocketServerConfig Config;
    
    // Running state
    bool bIsRunning;
    
    // Mutex for thread safety
    FCriticalSection ClientsLock;
    
    // WebSocket callbacks
    void OnConnectionAccepted(const FString& ClientId, TSharedPtr<IWebSocket> WebSocket);
    void OnConnectionClosed(const FString& ClientId);
    void OnMessageReceived(const FString& ClientId, const FString& Message);
};
