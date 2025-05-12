#pragma once

#include "CoreMinimal.h"
#include "UObject/NoExportTypes.h"
#include "Network/GenWebSocketManager.h"
#include "GenAIWebSocketBridge.generated.h"

// Forward declarations
class UGenOAIChat;
class UGenClaudeChat;
class UGenDSeekChat;

/**
 * Bridge class that connects AI models with WebSocket functionality
 * This allows AI responses to be sent over WebSocket and AI requests to be received
 */
UCLASS(BlueprintType, Blueprintable)
class GENERATIVEAISUPPORT_API UGenAIWebSocketBridge : public UObject
{
    GENERATED_BODY()

public:
    UGenAIWebSocketBridge();
    virtual ~UGenAIWebSocketBridge();

    /**
     * Initialize the bridge with a WebSocket manager
     * @param InWebSocketManager The WebSocket manager to use
     * @return True if initialization was successful
     */
    UFUNCTION(BlueprintCallable, Category = "AI|WebSocket")
    bool Initialize(UGenWebSocketManager* InWebSocketManager);

    /**
     * Set the OpenAI chat model to use
     * @param InOAIChat The OpenAI chat model
     */
    UFUNCTION(BlueprintCallable, Category = "AI|WebSocket")
    void SetOpenAIChat(UGenOAIChat* InOAIChat);

    /**
     * Set the Claude chat model to use
     * @param InClaudeChat The Claude chat model
     */
    UFUNCTION(BlueprintCallable, Category = "AI|WebSocket")
    void SetClaudeChat(UGenClaudeChat* InClaudeChat);

    /**
     * Set the DeepSeek chat model to use
     * @param InDSeekChat The DeepSeek chat model
     */
    UFUNCTION(BlueprintCallable, Category = "AI|WebSocket")
    void SetDeepSeekChat(UGenDSeekChat* InDSeekChat);

    /**
     * Send an AI request over WebSocket
     * @param ModelType The type of AI model to use ("openai", "claude", "deepseek")
     * @param Prompt The prompt to send to the AI model
     * @param SystemPrompt Optional system prompt
     * @return True if the request was sent successfully
     */
    UFUNCTION(BlueprintCallable, Category = "AI|WebSocket")
    bool SendAIRequest(const FString& ModelType, const FString& Prompt, const FString& SystemPrompt = "");

    /**
     * Process an AI request received over WebSocket
     * @param RequestJson The JSON request received over WebSocket
     * @return The response JSON to send back
     */
    UFUNCTION(BlueprintCallable, Category = "AI|WebSocket")
    FString ProcessAIRequest(const FString& RequestJson);

private:
    // The WebSocket manager
    UPROPERTY()
    UGenWebSocketManager* WebSocketManager;

    // AI models
    UPROPERTY()
    UGenOAIChat* OAIChat;

    UPROPERTY()
    UGenClaudeChat* ClaudeChat;

    UPROPERTY()
    UGenDSeekChat* DSeekChat;

    // Handle WebSocket messages
    UFUNCTION()
    void OnWebSocketMessage(const FString& Message);

    // Process OpenAI request
    FString ProcessOpenAIRequest(const TSharedPtr<FJsonObject>& JsonObject);

    // Process Claude request
    FString ProcessClaudeRequest(const TSharedPtr<FJsonObject>& JsonObject);

    // Process DeepSeek request
    FString ProcessDeepSeekRequest(const TSharedPtr<FJsonObject>& JsonObject);
};
