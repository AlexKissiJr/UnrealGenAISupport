// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Modules/ModuleManager.h"
#include "Modules/ModuleInterface.h"

// Forward declarations
class SWindow;
class IPythonScriptPlugin;

// Declare custom log category
DECLARE_LOG_CATEGORY_EXTERN(LogPythonSocket, Log, All);

class PYTHONSOCKETUI_API FPythonSocketUIModule : public IModuleInterface, public TSharedFromThis<FPythonSocketUIModule>
{
public:
	/** IModuleInterface implementation */
	virtual void StartupModule() override;
	virtual void ShutdownModule() override;

	/** Get whether socket server is running */
	bool IsSocketServerRunning() const { return bIsSocketServerRunning; }
	
	/** Helper function to run Python commands and get results */
	bool RunPythonCommand(const FString& Command, FString& Result);

private:
	void ExtendLevelEditorToolbar();
	void ToggleSocketServer();
	void StartSocketServer();
	void StopSocketServer();
	
	// Helper function to check Python availability
	bool IsPythonAvailable() const;
	
	// Control Panel functions
	void OpenControlPanel();
	FReply OpenControlPanel_OnClicked();
	void CloseControlPanel();
	void OnControlPanelClosed(const TSharedRef<SWindow>& Window);
	TSharedRef<class SWidget> CreateControlPanelContent();
	FReply OnStartServerClicked();
	FReply OnStopServerClicked();
	
	TSharedPtr<SWindow> ControlPanelWindow;
	bool bIsSocketServerRunning;
}; 