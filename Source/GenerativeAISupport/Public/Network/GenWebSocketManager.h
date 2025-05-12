#pragma once

#include "CoreMinimal.h"
#include "UObject/NoExportTypes.h"
#include "Network/GenWebSocketClient.h"
#include "GenWebSocketManager.generated.h"

/**
 * Manager class for WebSocket communication with the Python server
 * This class provides a simple interface for sending commands to the Python server
 * and handling responses
 */
UCLASS(BlueprintType, Blueprintable)
class GENERATIVEAISUPPORT_API UGenWebSocketManager : public UObject
{
    GENERATED_BODY()

public:
    UGenWebSocketManager();
    virtual ~UGenWebSocketManager();

    /**
     * Initialize the WebSocket manager
     * @param ServerURL The URL of the server (e.g., "ws://localhost:9877")
     * @return True if initialization was successful
     */
    UFUNCTION(BlueprintCallable, Category = "WebSocket")
    bool Initialize(const FString& ServerURL = TEXT("ws://localhost:9877"));

    /**
     * Shutdown the WebSocket manager
     */
    UFUNCTION(BlueprintCallable, Category = "WebSocket")
    void Shutdown();

    /**
     * Send a handshake message to the server
     * @param Message Optional message to include in the handshake
     * @return True if the message was sent
     */
    UFUNCTION(BlueprintCallable, Category = "WebSocket|Commands")
    bool SendHandshake(const FString& Message = TEXT("Hello from Unreal Engine"));

    /**
     * Execute a Python command on the server
     * @param PythonCode The Python code to execute
     * @return True if the command was sent
     */
    UFUNCTION(BlueprintCallable, Category = "WebSocket|Commands")
    bool ExecutePython(const FString& PythonCode);

    /**
     * Get the WebSocket client instance
     * @return The WebSocket client
     */
    UFUNCTION(BlueprintPure, Category = "WebSocket")
    UGenWebSocketClient* GetWebSocketClient() const { return WebSocketClient; }

    /**
     * Check if the WebSocket client is connected
     * @return True if connected
     */
    UFUNCTION(BlueprintPure, Category = "WebSocket")
    bool IsConnected() const;

    /**
     * Get the last response received from the server
     * @return The last response
     */
    UFUNCTION(BlueprintPure, Category = "WebSocket")
    FString GetLastResponse() const { return LastResponse; }

private:
    // The WebSocket client instance
    UPROPERTY()
    UGenWebSocketClient* WebSocketClient;

    // The last response received from the server
    FString LastResponse;

    // Handle WebSocket events
    UFUNCTION()
    void OnWebSocketConnected(bool bSuccess);

    UFUNCTION()
    void OnWebSocketMessage(const FString& Message);

    UFUNCTION()
    void OnWebSocketClosed(int32 StatusCode, const FString& Reason);

    UFUNCTION()
    void OnWebSocketError(const FString& Error);
};
