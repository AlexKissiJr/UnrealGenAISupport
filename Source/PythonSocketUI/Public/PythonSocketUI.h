// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Modules/ModuleManager.h"
#include "Modules/ModuleInterface.h"
#include "Sockets.h"
#include "SocketSubsystem.h"
#include "Interfaces/IPv4/IPv4Address.h"
#include "HAL/RunnableThread.h"
#include "HAL/Runnable.h"
#include "TimerManager.h"

// Forward declarations
class SWindow;
class IPythonScriptPlugin;

// Declare custom log category
DECLARE_LOG_CATEGORY_EXTERN(LogPythonSocket, Log, All);

// Forward declaration of connection checker class
class FSocketConnectionChecker;

class PYTHONSOCKETUI_API FPythonSocketUIModule : public IModuleInterface, public TSharedFromThis<FPythonSocketUIModule>
{
public:
	/** IModuleInterface implementation */
	virtual void StartupModule() override;
	virtual void ShutdownModule() override;

	/** Get whether socket server is running */
	bool IsSocketServerRunning() const { return bIsSocketServerRunning; }

	/** Get whether to use WebSocket instead of TCP */
	bool UseWebSocket() const { return bUseWebSocket; }

	/** Set whether to use WebSocket instead of TCP */
	void SetUseWebSocket(bool bUseWS) { bUseWebSocket = bUseWS; }

	/** Helper function to run Python commands and get results */
	bool RunPythonCommand(const FString& Command, FString& Result);

	/** Update the connection status */
	void UpdateConnectionStatus(bool bConnected);

	/** Start the connection checker */
	void StartConnectionChecker();

	/** Stop the connection checker */
	void StopConnectionChecker();

	/** Test the connection to the socket server */
	bool TestSocketConnection();

	/** Auto-restart the socket server if it's not responding */
	void AutoRestartSocketServer();

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
	FReply OnTestConnectionClicked();

	TSharedPtr<SWindow> ControlPanelWindow;
	bool bIsSocketServerRunning;
	bool bIsSocketConnected;
	bool bUseWebSocket = true; // Default to using WebSocket
	TSharedPtr<FSocketConnectionChecker> ConnectionChecker;
};

// Connection checker class that runs in a separate thread
class FSocketConnectionChecker : public FRunnable
{
public:
	FSocketConnectionChecker(FPythonSocketUIModule* InOwner, float InCheckInterval = 5.0f);
	virtual ~FSocketConnectionChecker();

	// FRunnable interface
	virtual bool Init() override;
	virtual uint32 Run() override;
	virtual void Stop() override;
	virtual void Exit() override;

	// Start/stop the thread
	void StartThread();
	void StopThread();

	// Test the connection
	bool TestConnection();

private:
	FPythonSocketUIModule* Owner;
	float CheckInterval;
	bool bRunning;
	FRunnableThread* Thread;
	FCriticalSection CriticalSection;
	int32 FailedConnectionCount;
	const int32 MaxFailedConnections;
};