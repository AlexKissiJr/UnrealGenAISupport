// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"

/**
 * Simple TCP server config structure
 */
struct FTCPServerConfig
{
    // Port to listen on
    int32 Port = 8080;
    
    // Max connections
    int32 MaxConnections = 10;
};

/**
 * Simple TCP server implementation
 */
class GENERATIVEAIEDITOR_API FTCPServer
{
public:
    FTCPServer(const FTCPServerConfig& InConfig = FTCPServerConfig());
    virtual ~FTCPServer();
    
    // Start the server
    bool Start();
    
    // Stop the server
    void Stop();
    
    // Check if the server is running
    bool IsRunning() const;
    
    // Get the server config
    const FTCPServerConfig& GetConfig() const { return Config; }
    
private:
    FTCPServerConfig Config;
    bool bIsRunning;
}; 