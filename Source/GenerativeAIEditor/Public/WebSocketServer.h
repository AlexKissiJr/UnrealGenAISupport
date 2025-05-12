// Copyright Alex Kissi Jr 2024. All rights Reserved. https://createlex.com/terms

#pragma once

#include "CoreMinimal.h"

/**
 * WebSocket server config structure
 */
struct FWebSocketServerConfig
{
    // Port to listen on
    int32 Port = 8081;

    // Server name
    FString ServerName = TEXT("GenerativeAI WebSocket Server");
};

/**
 * Simplified WebSocket server implementation for GenerativeAI
 * This is a placeholder class that delegates the actual WebSocket functionality to Python
 */
class GENERATIVEAIEDITOR_API FWebSocketServer
{
public:
    FWebSocketServer(const FWebSocketServerConfig& InConfig = FWebSocketServerConfig())
        : Config(InConfig)
        , bIsRunning(false)
    {
    }

    virtual ~FWebSocketServer()
    {
        Stop();
    }

    // Start the server (implemented in Python)
    bool Start()
    {
        bIsRunning = true;
        return true;
    }

    // Stop the server (implemented in Python)
    void Stop()
    {
        bIsRunning = false;
    }

    // Check if the server is running
    bool IsRunning() const
    {
        return bIsRunning;
    }

    // Get the server config
    const FWebSocketServerConfig& GetConfig() const { return Config; }

private:
    // Server configuration
    FWebSocketServerConfig Config;

    // Running state
    bool bIsRunning;
};
