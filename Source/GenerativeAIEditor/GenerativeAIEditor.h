// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Modules/ModuleManager.h"
#include "Modules/ModuleInterface.h"

// Declare custom log category
DECLARE_LOG_CATEGORY_EXTERN(LogGenAI, Log, All);

class FTCPServer;
class SWindow;

class GENERATIVEAIEDITOR_API FGenerativeAIEditorModule : public IModuleInterface, public TSharedFromThis<FGenerativeAIEditorModule>
{
public:
	/** IModuleInterface implementation */
	virtual void StartupModule() override;
	virtual void ShutdownModule() override;

	/**
	 * Get the server instance
	 * External modules can use this to register custom handlers
	 * @return The server instance, or nullptr if not available
	 */
	FTCPServer* GetServer() const { return Server.Get(); }

private:
	void ExtendLevelEditorToolbar();
	void ToggleServer();
	void StartServer();
	void StopServer();
	bool IsServerRunning() const;
	
	// Control Panel functions
	void OpenControlPanel();
	FReply OpenControlPanel_OnClicked();
	void CloseControlPanel();
	void OnControlPanelClosed(const TSharedRef<SWindow>& Window);
	TSharedRef<class SWidget> CreateControlPanelContent();
	FReply OnStartServerClicked();
	FReply OnStopServerClicked();
	
	TUniquePtr<FTCPServer> Server;
	TSharedPtr<SWindow> ControlPanelWindow;
}; 