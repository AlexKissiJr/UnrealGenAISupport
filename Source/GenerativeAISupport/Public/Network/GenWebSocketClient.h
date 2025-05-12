#pragma once

#include "CoreMinimal.h"
#include "WebSocketsModule.h"
#include "IWebSocket.h"
#include "Tickable.h"
#include "GenWebSocketClient.generated.h"

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnWebSocketConnected, bool, bSuccess);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnWebSocketMessage, const FString&, Message);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FOnWebSocketClosed, int32, StatusCode, const FString&, Reason);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnWebSocketError, const FString&, Error);

/**
 * WebSocket client for communicating with the Python WebSocket server
 */
UCLASS(BlueprintType, Blueprintable)
class GENERATIVEAISUPPORT_API UGenWebSocketClient : public UObject, public FTickableGameObject
{
    GENERATED_BODY()

public:
    UGenWebSocketClient();
    virtual ~UGenWebSocketClient();

    // Begin FTickableGameObject interface
    virtual void Tick(float DeltaTime) override;
    virtual bool IsTickable() const override;
    virtual TStatId GetStatId() const override;
    // End FTickableGameObject interface

    /**
     * Connect to the WebSocket server
     * @param ServerURL The URL of the server (e.g., "ws://localhost:9877")
     * @param Protocol The WebSocket protocol to use (default: "ws")
     * @return True if the connection attempt was started
     */
    UFUNCTION(BlueprintCallable, Category = "WebSocket")
    bool Connect(const FString& ServerURL = TEXT("ws://localhost:9877"), const FString& Protocol = TEXT("ws"));

    /**
     * Disconnect from the WebSocket server
     */
    UFUNCTION(BlueprintCallable, Category = "WebSocket")
    void Disconnect();

    /**
     * Send a message to the WebSocket server
     * @param Message The message to send
     * @return True if the message was sent
     */
    UFUNCTION(BlueprintCallable, Category = "WebSocket")
    bool SendMessage(const FString& Message);

    /**
     * Send a JSON message to the WebSocket server
     * @param Command The command type
     * @param Params The parameters as a JSON string
     * @return True if the message was sent
     */
    UFUNCTION(BlueprintCallable, Category = "WebSocket")
    bool SendJsonCommand(const FString& Command, const FString& Params);

    /**
     * Check if the client is connected to the server
     * @return True if connected
     */
    UFUNCTION(BlueprintPure, Category = "WebSocket")
    bool IsConnected() const;

    /**
     * Get the last error message
     * @return The last error message
     */
    UFUNCTION(BlueprintPure, Category = "WebSocket")
    FString GetLastError() const;

    // Delegates for events
    UPROPERTY(BlueprintAssignable, Category = "WebSocket|Events")
    FOnWebSocketConnected OnConnected;

    UPROPERTY(BlueprintAssignable, Category = "WebSocket|Events")
    FOnWebSocketMessage OnMessage;

    UPROPERTY(BlueprintAssignable, Category = "WebSocket|Events")
    FOnWebSocketClosed OnClosed;

    UPROPERTY(BlueprintAssignable, Category = "WebSocket|Events")
    FOnWebSocketError OnError;

private:
    // The WebSocket instance
    TSharedPtr<IWebSocket> Socket;

    // Connection state
    bool bIsConnected;

    // Last error message
    FString LastError;

    // Queue for messages to be processed on the game thread
    TQueue<FString> MessageQueue;

    // Setup WebSocket event handlers
    void SetupWebSocketHandlers();

    // Process messages on the game thread
    void ProcessMessages();
};
