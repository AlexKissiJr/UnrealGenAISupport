// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Modules/ModuleManager.h"
#include "Modules/ModuleInterface.h"

// Declare custom log category
DECLARE_LOG_CATEGORY_EXTERN(LogGenAI, Log, All);

class FTCPServer;
class FWebSocketServer;
class SWindow;

class GENERATIVEAIEDITOR_API FGenerativeAIEditorModule : public IModuleInterface, public TSharedFromThis<FGenerativeAIEditorModule>
{
public:
	/** IModuleInterface implementation */
	virtual void StartupModule() override;
	virtual void ShutdownModule() override;

	/**
	 * Get the TCP server instance
	 * External modules can use this to register custom handlers
	 * @return The server instance, or nullptr if not available
	 */
	FTCPServer* GetServer() const { return Server.Get(); }

	/**
	 * Get the WebSocket server instance
	 * External modules can use this to register custom handlers
	 * @return The WebSocket server instance, or nullptr if not available
	 */
	FWebSocketServer* GetWebSocketServer() const { return WebSocketServer.Get(); }

	/**
	 * Check if WebSocket server is enabled
	 * @return True if WebSocket server is enabled
	 */
	bool IsWebSocketEnabled() const { return bUseWebSocket; }

private:
	// UI and toolbar
	void ExtendLevelEditorToolbar();

	// Server control
	void ToggleServer();
	void StartServer();
	void StopServer();
	bool IsServerRunning() const;

	// WebSocket specific methods
	void StartWebSocketServer();
	void StopWebSocketServer();
	bool IsWebSocketServerRunning() const;
	void HandleWebSocketMessage(const FString& ClientId, const FString& Message);

	// Control Panel functions
	void OpenControlPanel();
	FReply OpenControlPanel_OnClicked();
	void CloseControlPanel();
	void OnControlPanelClosed(const TSharedRef<SWindow>& Window);
	TSharedRef<class SWidget> CreateControlPanelContent();
	FReply OnStartServerClicked();
	FReply OnStopServerClicked();

	// Server instances
	TUniquePtr<FTCPServer> Server;
	TUniquePtr<FWebSocketServer> WebSocketServer;

	// UI elements
	TSharedPtr<SWindow> ControlPanelWindow;

	// Configuration
	bool bUseWebSocket = true; // Default to using WebSocket
};