// Copyright Epic Games, Inc. All Rights Reserved.

#include "TCPServer.h"
#include "GenerativeAIEditor.h"

FTCPServer::FTCPServer(const FTCPServerConfig& InConfig)
    : Config(InConfig)
    , bIsRunning(false)
{
}

FTCPServer::~FTCPServer()
{
    Stop();
}

bool FTCPServer::Start()
{
    if (bIsRunning)
    {
        UE_LOG(LogGenAI, Warning, TEXT("TCP Server is already running"));
        return true;
    }
    
    // TODO: Implement actual server startup
    UE_LOG(LogGenAI, Display, TEXT("Starting TCP Server on port %d"), Config.Port);
    
    // Placeholder for actual TCP server implementation
    bIsRunning = true;
    
    UE_LOG(LogGenAI, Display, TEXT("TCP Server started successfully"));
    return true;
}

void FTCPServer::Stop()
{
    if (!bIsRunning)
    {
        return;
    }
    
    // TODO: Implement actual server shutdown
    UE_LOG(LogGenAI, Display, TEXT("Stopping TCP Server"));
    
    // Placeholder for actual TCP server shutdown
    bIsRunning = false;
    
    UE_LOG(LogGenAI, Display, TEXT("TCP Server stopped"));
}

bool FTCPServer::IsRunning() const
{
    return bIsRunning;
} 