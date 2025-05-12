// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Modules/ModuleManager.h"
#include "Modules/ModuleInterface.h"
#include "TCPServer.h"

// Declare custom log category
DECLARE_LOG_CATEGORY_EXTERN(LogGenAI, Log, All);

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

	// WebSocket functionality is handled in Python

	// Control Panel functions
	void OpenControlPanel();
	FReply OpenControlPanel_OnClicked();
	void CloseControlPanel();
	void OnControlPanelClosed(const TSharedRef<SWindow>& Window);
	TSharedRef<class SWidget> CreateControlPanelContent();
	FReply OnStartServerClicked();
	FReply OnStopServerClicked();

	// Server instance
	TUniquePtr<FTCPServer> Server;

	// UI elements
	TSharedPtr<SWindow> ControlPanelWindow;

	// Configuration
	bool bUseWebSocket = true; // Default to using WebSocket
};