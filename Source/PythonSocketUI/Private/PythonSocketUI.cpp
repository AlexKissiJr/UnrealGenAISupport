// Copyright Epic Games, Inc. All Rights Reserved.

#include "PythonSocketUI.h"
#include "LevelEditor.h"
#include "Framework/MultiBox/MultiBoxBuilder.h"
#include "Styling/SlateStyleRegistry.h"
#include "Interfaces/IPluginManager.h"
#include "Styling/SlateStyle.h"
#include "Styling/SlateStyleMacros.h"
#include "Styling/SlateTypes.h"
#include "Styling/CoreStyle.h"
#include "ToolMenus.h"
#include "ToolMenuSection.h"
#include "Widgets/Images/SImage.h"
#include "Widgets/SWindow.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/Layout/SScrollBox.h"
#include "Widgets/Text/STextBlock.h"
#include "Widgets/Input/SButton.h"
#include "Widgets/Layout/SGridPanel.h"
#include "Widgets/Layout/SUniformGridPanel.h"
#include "Framework/Docking/TabManager.h"
#include "Framework/Application/SlateApplication.h"
#include "EditorStyleSet.h"
#include "IPythonScriptPlugin.h"
#include "Editor.h"
#include "Misc/MessageDialog.h"
#include "Editor/EditorEngine.h"

// Log category
DEFINE_LOG_CATEGORY(LogPythonSocket);

// Macro for logging
#define PYSOCKET_LOG_INFO(Format, ...) UE_LOG(LogPythonSocket, Display, TEXT(Format), ##__VA_ARGS__)
#define PYSOCKET_LOG_WARNING(Format, ...) UE_LOG(LogPythonSocket, Warning, TEXT(Format), ##__VA_ARGS__)
#define PYSOCKET_LOG_ERROR(Format, ...) UE_LOG(LogPythonSocket, Error, TEXT(Format), ##__VA_ARGS__)

#define LOCTEXT_NAMESPACE "FPythonSocketUIModule"

// Define path constants
class FPythonSocketConstants
{
public:
    static FString PluginResourcesPath;
    static FString PluginContentPath;
    
    static void InitializePathConstants()
    {
        // First try to find our plugin directly
        TSharedPtr<IPlugin> Plugin = IPluginManager::Get().FindPlugin("UnrealGenAISupport");
        if (Plugin.IsValid())
        {
            PluginResourcesPath = Plugin->GetBaseDir() / TEXT("Resources");
            PluginContentPath = Plugin->GetContentDir();
            
            UE_LOG(LogPythonSocket, Display, TEXT("Plugin found directly: %s"), *Plugin->GetName());
            UE_LOG(LogPythonSocket, Display, TEXT("Resources path: %s"), *PluginResourcesPath);
            UE_LOG(LogPythonSocket, Display, TEXT("Content path: %s"), *PluginContentPath);
            return;
        }
        
        // If not found, try to find it by iterating through all plugins
        UE_LOG(LogPythonSocket, Warning, TEXT("Plugin not found directly, searching all plugins..."));
        for (TSharedRef<IPlugin> LoadedPlugin : IPluginManager::Get().GetDiscoveredPlugins())
        {
            UE_LOG(LogPythonSocket, Display, TEXT("Checking plugin: %s"), *LoadedPlugin.Get().GetName());
            
            // Check if this is our plugin
            if (LoadedPlugin.Get().GetName().Contains(TEXT("GenAI")) || 
                LoadedPlugin.Get().GetName().Contains(TEXT("GenerativeAI")))
            {
                UE_LOG(LogPythonSocket, Display, TEXT("Found plugin by partial name: %s"), *LoadedPlugin.Get().GetName());
                Plugin = LoadedPlugin.Get().AsShared();
                break;
            }
        }
        
        // If found via the alternative method
        if (Plugin.IsValid())
        {
            PluginResourcesPath = Plugin->GetBaseDir() / TEXT("Resources");
            PluginContentPath = Plugin->GetContentDir();
            
            UE_LOG(LogPythonSocket, Display, TEXT("Plugin found by iterating: %s"), *Plugin->GetName());
            UE_LOG(LogPythonSocket, Display, TEXT("Resources path: %s"), *PluginResourcesPath);
            UE_LOG(LogPythonSocket, Display, TEXT("Content path: %s"), *PluginContentPath);
            return;
        }
        
        // Fallback to a hardcoded path if all else fails
        FString ProjectDir = FPaths::ProjectDir();
        PluginResourcesPath = FPaths::Combine(ProjectDir, TEXT("Plugins/UnrealGenAISupport/Resources"));
        PluginContentPath = FPaths::Combine(ProjectDir, TEXT("Plugins/UnrealGenAISupport/Content"));
        
        UE_LOG(LogPythonSocket, Warning, TEXT("Could not find plugin! Using hardcoded fallback paths:"));
        UE_LOG(LogPythonSocket, Warning, TEXT("Resources path: %s"), *PluginResourcesPath);
        UE_LOG(LogPythonSocket, Warning, TEXT("Content path: %s"), *PluginContentPath);
    }
};

FString FPythonSocketConstants::PluginResourcesPath;
FString FPythonSocketConstants::PluginContentPath;

// Define a style set for our plugin
class FPythonSocketStyle : public FSlateStyleSet
{
public:
    FPythonSocketStyle() : FSlateStyleSet("PythonSocketStyle")
    {
        const FVector2D Icon16x16(16.0f, 16.0f);
        const FVector2D StatusSize(6.0f, 6.0f);

        // Use path constants
        SetContentRoot(FPythonSocketConstants::PluginResourcesPath);

        // Register icon
        FSlateImageBrush* IconBrush = new FSlateImageBrush(
            RootToContentDir(TEXT("Icon128.png")), 
            Icon16x16,
            FLinearColor::White,
            ESlateBrushTileType::NoTile
        );
        Set("PythonSocket.ServerIcon", IconBrush);

        // Create status indicator brushes
        const FLinearColor RunningColor(0.0f, 0.8f, 0.0f);  // Green
        const FLinearColor StoppedColor(0.8f, 0.0f, 0.0f);  // Red
        
        Set("PythonSocket.StatusRunning", new FSlateRoundedBoxBrush(RunningColor, 3.0f, FVector2f(StatusSize)));
        Set("PythonSocket.StatusStopped", new FSlateRoundedBoxBrush(StoppedColor, 3.0f, FVector2f(StatusSize)));

        // Define a custom button style with hover feedback
        FButtonStyle ToolbarButtonStyle = FAppStyle::Get().GetWidgetStyle<FButtonStyle>("LevelEditor.ToolBar.Button");
        
        // Normal state
        ToolbarButtonStyle.SetNormal(FSlateColorBrush(FLinearColor(0, 0, 0, 0))); // Transparent
        
        // Hovered state
        ToolbarButtonStyle.SetHovered(FSlateColorBrush(FLinearColor(0.2f, 0.2f, 0.2f, 0.3f)));
        
        // Pressed state
        ToolbarButtonStyle.SetPressed(FSlateColorBrush(FLinearColor(0.1f, 0.1f, 0.1f, 0.5f)));
        
        // Register the custom style
        Set("PythonSocket.TransparentToolbarButton", ToolbarButtonStyle);
    }

    static void Initialize()
    {
        if (!Instance.IsValid())
        {
            Instance = MakeShareable(new FPythonSocketStyle());
        }
    }

    static void Shutdown()
    {
        if (Instance.IsValid())
        {
            FSlateStyleRegistry::UnRegisterSlateStyle(*Instance);
            Instance.Reset();
        }
    }

    static TSharedPtr<FPythonSocketStyle> Get()
    {
        return Instance;
    }

private:
    static TSharedPtr<FPythonSocketStyle> Instance;
};

TSharedPtr<FPythonSocketStyle> FPythonSocketStyle::Instance = nullptr;

void FPythonSocketUIModule::StartupModule()
{
    PYSOCKET_LOG_INFO("Python Socket UI Plugin is starting up");
    
    // Initialize constants
    FPythonSocketConstants::InitializePathConstants();
    
    // Initialize styling for the plugin
    FPythonSocketStyle::Initialize();
    FSlateStyleRegistry::RegisterSlateStyle(*FPythonSocketStyle::Get());
    
    // Set initial state
    bIsSocketServerRunning = false;
    
    // Log whether Python is available
    if (IsPythonAvailable())
    {
        PYSOCKET_LOG_INFO("Python is available for this module");
    }
    else
    {
        PYSOCKET_LOG_WARNING("Python is NOT available for this module");
    }
    
    // More debug logging
    PYSOCKET_LOG_INFO("Python Socket Style registered");
    
    // Ensure tool menus are initiated
    if (!UToolMenus::IsToolMenuUIEnabled())
    {
        UToolMenus::Get()->RegisterMenu("LevelEditor.MainMenu", "MainFrame.MainMenu");
        PYSOCKET_LOG_INFO("Registered UToolMenus");
    }
    
    // Try to extend toolbar immediately if possible
    if (UToolMenus::IsToolMenuUIEnabled() && FSlateApplication::IsInitialized())
    {
        PYSOCKET_LOG_INFO("Extending toolbar directly");
        ExtendLevelEditorToolbar();
    }
    
    // Also register for post engine init as a fallback
    FCoreDelegates::OnPostEngineInit.RemoveAll(this);
    PYSOCKET_LOG_INFO("Registering OnPostEngineInit delegate");
    FCoreDelegates::OnPostEngineInit.AddRaw(this, &FPythonSocketUIModule::ExtendLevelEditorToolbar);
}

void FPythonSocketUIModule::ShutdownModule()
{
    PYSOCKET_LOG_INFO("Python Socket UI Plugin is shutting down");
    
    // Unregister style set
    FPythonSocketStyle::Shutdown();
    
    // Stop server if running
    if (bIsSocketServerRunning)
    {
        StopSocketServer();
    }
    
    // Close control panel if open
    CloseControlPanel();
    
    // Clean up delegates
    FCoreDelegates::OnPostEngineInit.RemoveAll(this);
}

void FPythonSocketUIModule::ExtendLevelEditorToolbar()
{
    static bool bToolbarExtended = false;
    
    if (bToolbarExtended)
    {
        PYSOCKET_LOG_WARNING("ExtendLevelEditorToolbar called but toolbar already extended, skipping");
        return;
    }
    
    // Make sure UToolMenus is initialized
    if (!UToolMenus::IsToolMenuUIEnabled())
    {
        PYSOCKET_LOG_WARNING("UToolMenus not initialized yet, cannot extend toolbar");
        return;
    }
    
    PYSOCKET_LOG_INFO("ExtendLevelEditorToolbar called - first time");
    
    // Check if our style is registered
    if (!FPythonSocketStyle::Get().IsValid())
    {
        PYSOCKET_LOG_ERROR("PythonSocketStyle is not valid! Reinitializing...");
        FPythonSocketStyle::Initialize();
        FSlateStyleRegistry::RegisterSlateStyle(*FPythonSocketStyle::Get());
    }
    
    // Ensure the main menu is registered
    UToolMenus::Get()->RegisterMenu("LevelEditor.MainMenu", "MainFrame.MainMenu");
    
    // Add button to toolbar
    UToolMenu* ToolbarMenu = UToolMenus::Get()->ExtendMenu("LevelEditor.LevelEditorToolBar.User");
    if (ToolbarMenu)
    {
        FToolMenuSection& Section = ToolbarMenu->FindOrAddSection("PythonSocket");
        
        // Add a custom widget instead of a static toolbar button
        Section.AddEntry(FToolMenuEntry::InitWidget(
            "PythonSocketControl",
            SNew(SButton)
            .ButtonStyle(FPythonSocketStyle::Get().ToSharedRef(), "PythonSocket.TransparentToolbarButton")
            .OnClicked(FOnClicked::CreateRaw(this, &FPythonSocketUIModule::OpenControlPanel_OnClicked))
            .ToolTipText(LOCTEXT("PythonSocketButtonTooltip", "Open Python Socket Control Panel"))
            .Content()
            [
                SNew(SOverlay)
                + SOverlay::Slot()
                [
                    SNew(SImage)
                    .Image(FPythonSocketStyle::Get()->GetBrush("PythonSocket.ServerIcon"))
                    .ColorAndOpacity(FLinearColor::White)
                ]
                + SOverlay::Slot()
                .HAlign(HAlign_Right)
                .VAlign(VAlign_Bottom)
                [
                    SNew(SImage)
                    .Image_Lambda([this]() -> const FSlateBrush* {
                        return bIsSocketServerRunning 
                            ? FPythonSocketStyle::Get()->GetBrush("PythonSocket.StatusRunning") 
                            : FPythonSocketStyle::Get()->GetBrush("PythonSocket.StatusStopped");
                    })
                ]
            ],
            FText::GetEmpty(),
            true,
            false,
            false
        ));
        
        PYSOCKET_LOG_INFO("Python Socket button added to main toolbar with dynamic icon");
    }
    else
    {
        PYSOCKET_LOG_ERROR("Failed to extend LevelEditor toolbar - toolbar menu is null");
        return;
    }
    
    // Window menu 
    UToolMenu* WindowMenu = UToolMenus::Get()->ExtendMenu("LevelEditor.MainMenu.Window");
    if (WindowMenu)
    {
        FToolMenuSection& Section = WindowMenu->FindOrAddSection("WindowLayout");
        Section.AddMenuEntry(
            "PythonSocketWindow",
            LOCTEXT("PythonSocketWindowMenuLabel", "Python Socket Control Panel"),
            LOCTEXT("PythonSocketWindowMenuTooltip", "Open Python Socket Control Panel"),
            FSlateIcon(FPythonSocketStyle::Get()->GetStyleSetName(), "PythonSocket.ServerIcon"),
            FUIAction(
                FExecuteAction::CreateRaw(this, &FPythonSocketUIModule::OpenControlPanel),
                FCanExecuteAction()
            )
        );
        PYSOCKET_LOG_INFO("Python Socket entry added to Window menu");
    }
    else
    {
        PYSOCKET_LOG_ERROR("Failed to extend Window menu - menu is null");
    }
    
    bToolbarExtended = true;
    
    // Force refresh all tool menus to make sure our changes take effect
    UToolMenus::Get()->RefreshAllWidgets();
}

void FPythonSocketUIModule::OpenControlPanel()
{
    // If the window already exists, just focus it
    if (ControlPanelWindow.IsValid())
    {
        ControlPanelWindow->BringToFront();
        return;
    }

    // Create a new window
    ControlPanelWindow = SNew(SWindow)
        .Title(LOCTEXT("PythonSocketControlPanelTitle", "Python Socket Control Panel"))
        .SizingRule(ESizingRule::Autosized)
        .SupportsMaximize(false)
        .SupportsMinimize(false)
        .HasCloseButton(true)
        .CreateTitleBar(true)
        .IsTopmostWindow(true)
        .MinWidth(300)
        .MinHeight(150);

    // Set the content of the window
    ControlPanelWindow->SetContent(CreateControlPanelContent());

    // Register a callback for when the window is closed
    ControlPanelWindow->GetOnWindowClosedEvent().AddRaw(this, &FPythonSocketUIModule::OnControlPanelClosed);

    // Show the window
    FSlateApplication::Get().AddWindow(ControlPanelWindow.ToSharedRef());

    PYSOCKET_LOG_INFO("Python Socket Control Panel opened");
}

FReply FPythonSocketUIModule::OpenControlPanel_OnClicked()
{
    OpenControlPanel();
    return FReply::Handled();
}

void FPythonSocketUIModule::OnControlPanelClosed(const TSharedRef<SWindow>& Window)
{
    ControlPanelWindow.Reset();
    PYSOCKET_LOG_INFO("Python Socket Control Panel closed");
}

void FPythonSocketUIModule::CloseControlPanel()
{
    if (ControlPanelWindow.IsValid())
    {
        ControlPanelWindow->RequestDestroyWindow();
        ControlPanelWindow.Reset();
        PYSOCKET_LOG_INFO("Python Socket Control Panel closed");
    }
}

TSharedRef<SWidget> FPythonSocketUIModule::CreateControlPanelContent()
{
    return SNew(SBorder)
        .BorderImage(FAppStyle::GetBrush("ToolPanel.GroupBorder"))
        .Padding(8.0f)
        [
            SNew(SVerticalBox)
            
            // Status section
            + SVerticalBox::Slot()
            .AutoHeight()
            .Padding(0, 0, 0, 8)
            [
                SNew(SHorizontalBox)
                
                + SHorizontalBox::Slot()
                .AutoWidth()
                .VAlign(VAlign_Center)
                .Padding(0, 0, 8, 0)
                [
                    SNew(STextBlock)
                    .Text(LOCTEXT("ServerStatusLabel", "Socket Server Status:"))
                    .Font(FAppStyle::GetFontStyle("NormalText"))
                ]
                
                + SHorizontalBox::Slot()
                .FillWidth(1.0f)
                .VAlign(VAlign_Center)
                [
                    SNew(STextBlock)
                    .Text_Lambda([this]() -> FText {
                        return bIsSocketServerRunning 
                            ? LOCTEXT("ServerRunningStatus", "Running") 
                            : LOCTEXT("ServerStoppedStatus", "Stopped");
                    })
                    .ColorAndOpacity_Lambda([this]() -> FSlateColor {
                        return bIsSocketServerRunning 
                            ? FSlateColor(FLinearColor(0.0f, 0.8f, 0.0f)) 
                            : FSlateColor(FLinearColor(0.8f, 0.0f, 0.0f));
                    })
                    .Font(FAppStyle::GetFontStyle("NormalText"))
                ]
            ]
            
            // Port information
            + SVerticalBox::Slot()
            .AutoHeight()
            .Padding(0, 0, 0, 8)
            [
                SNew(SHorizontalBox)
                
                + SHorizontalBox::Slot()
                .AutoWidth()
                .VAlign(VAlign_Center)
                .Padding(0, 0, 8, 0)
                [
                    SNew(STextBlock)
                    .Text(LOCTEXT("ServerPortLabel", "Port:"))
                    .Font(FAppStyle::GetFontStyle("NormalText"))
                ]
                
                + SHorizontalBox::Slot()
                .FillWidth(1.0f)
                .VAlign(VAlign_Center)
                [
                    SNew(STextBlock)
                    .Text(FText::AsNumber(9877)) // Hardcoded port from unreal_socket_server.py
                    .Font(FAppStyle::GetFontStyle("NormalText"))
                ]
            ]
            
            // Buttons
            + SVerticalBox::Slot()
            .AutoHeight()
            .Padding(0, 8, 0, 0)
            .HAlign(HAlign_Center)
            [
                SNew(SUniformGridPanel)
                .SlotPadding(FMargin(5.0f))
                .MinDesiredSlotWidth(100.0f)
                
                // Start button
                + SUniformGridPanel::Slot(0, 0)
                [
                    SNew(SButton)
                    .HAlign(HAlign_Center)
                    .VAlign(VAlign_Center)
                    .Text(LOCTEXT("StartServerButton", "Start Server"))
                    .IsEnabled_Lambda([this]() -> bool { return !bIsSocketServerRunning; })
                    .OnClicked(FOnClicked::CreateRaw(this, &FPythonSocketUIModule::OnStartServerClicked))
                ]
                
                // Stop button
                + SUniformGridPanel::Slot(1, 0)
                [
                    SNew(SButton)
                    .HAlign(HAlign_Center)
                    .VAlign(VAlign_Center)
                    .Text(LOCTEXT("StopServerButton", "Stop Server"))
                    .IsEnabled_Lambda([this]() -> bool { return bIsSocketServerRunning; })
                    .OnClicked(FOnClicked::CreateRaw(this, &FPythonSocketUIModule::OnStopServerClicked))
                ]
            ]
        ];
}

FReply FPythonSocketUIModule::OnStartServerClicked()
{
    StartSocketServer();
    return FReply::Handled();
}

FReply FPythonSocketUIModule::OnStopServerClicked()
{
    StopSocketServer();
    return FReply::Handled();
}

void FPythonSocketUIModule::ToggleSocketServer()
{
    PYSOCKET_LOG_WARNING("ToggleSocketServer called - Server state: %s", bIsSocketServerRunning ? TEXT("Running") : TEXT("Not Running"));
    
    if (bIsSocketServerRunning)
    {
        PYSOCKET_LOG_WARNING("Stopping socket server...");
        StopSocketServer();
    }
    else
    {
        PYSOCKET_LOG_WARNING("Starting socket server...");
        StartSocketServer();
    }
    
    PYSOCKET_LOG_WARNING("ToggleSocketServer completed - Server state: %s", bIsSocketServerRunning ? TEXT("Running") : TEXT("Not Running"));
}

void FPythonSocketUIModule::StartSocketServer()
{
    if (bIsSocketServerRunning)
    {
        PYSOCKET_LOG_WARNING("Socket server is already running, ignoring start request");
        return;
    }

    PYSOCKET_LOG_INFO("Starting Python socket server");
    
    IPythonScriptPlugin* PythonPlugin = IPythonScriptPlugin::Get();
    
    if (!PythonPlugin)
    {
        PYSOCKET_LOG_ERROR("Python plugin not available");
        FText ErrorTitle = LOCTEXT("StartServerErrorTitle", "Socket Server Error");
        FMessageDialog::Open(
            EAppMsgType::Ok, 
            LOCTEXT("PythonPluginMissingError", "Python plugin is not available. Make sure Python Script Plugin is enabled."),
            ErrorTitle
        );
        return;
    }
    
    // Use Python script plugin to start the socket server
    FString PythonCommand = TEXT("import unreal\n"
                                "import sys\n"
                                "from importlib import reload\n"
                                "import importlib.util\n"
                                "import os\n"
                                "\n"
                                "# Get the Content/Python path from plugin\n");
    
    PythonCommand += TEXT("plugin_content_path = r\"");
    PythonCommand += FPythonSocketConstants::PluginContentPath;
    PythonCommand += TEXT("\"\n");
    
    PythonCommand += TEXT("python_path = os.path.join(plugin_content_path, \"Python\")\n"
                         "sys.path.append(python_path)\n"
                         "\n"
                         "try:\n"
                         "    import unreal_socket_server\n"
                         "    reload(unreal_socket_server)\n"
                         "    print(\"Python socket server started successfully\")\n"
                         "    success = True\n"
                         "except Exception as e:\n"
                         "    print(f\"Error starting Python socket server: {str(e)}\")\n"
                         "    success = False\n"
                         "\n"
                         "success");

    bool bSuccess = false;
    
    FPythonCommandEx PythonCommandEx;
    PythonCommandEx.Command = PythonCommand;
    if (PythonPlugin->ExecPythonCommandEx(PythonCommandEx))
    {
        // Get the result from the CommandResult field
        FString Result = PythonCommandEx.CommandResult;
        
        // Log the complete result for debugging
        PYSOCKET_LOG_INFO("Python command result: %s", *Result);
        
        // Check multiple indications of success - the server might output multiple messages
        if (Result.Contains(TEXT("Socket server listening")) || 
            Result.Contains(TEXT("Socket server started")) || 
            Result.Contains(TEXT("Python socket server started successfully")) ||
            !Result.Contains(TEXT("Error")))  // If no error message is present, consider it successful
        {
            PYSOCKET_LOG_INFO("Python socket server started successfully");
            bIsSocketServerRunning = true;
            bSuccess = true;
        }
        else if (Result.Contains(TEXT("True"))) 
        {
            // Fallback to the original check
            PYSOCKET_LOG_INFO("Python socket server started successfully (detected via True)");
            bIsSocketServerRunning = true;
            bSuccess = true;
        }
        else if (Result.IsEmpty())
        {
            // If the result is empty, consider it a success - sometimes Python doesn't return proper output
            PYSOCKET_LOG_INFO("Python socket server potentially started (empty result)");
            bIsSocketServerRunning = true;
            bSuccess = true;
        }
        else
        {
            PYSOCKET_LOG_ERROR("Failed to start Python socket server: %s", *Result);
        }
    }
    else
    {
        PYSOCKET_LOG_ERROR("Failed to execute Python command");
    }
    
    // Refresh the toolbar to update the status indicator
    if (UToolMenus* ToolMenus = UToolMenus::Get())
    {
        ToolMenus->RefreshAllWidgets();
    }
    
    if (!bSuccess)
    {
        // Show an error message
        FText ErrorTitle = LOCTEXT("StartServerErrorTitle", "Socket Server Error");
        FMessageDialog::Open(
            EAppMsgType::Ok, 
            LOCTEXT("StartServerErrorMessage", "Failed to start Python socket server. Check Output Log for details."),
            ErrorTitle
        );
    }
}

void FPythonSocketUIModule::StopSocketServer()
{
	PYSOCKET_LOG_WARNING("Stopping socket server...");
	if (!bIsSocketServerRunning)
	{
		PYSOCKET_LOG_WARNING("Socket server not running.");
		bIsSocketServerRunning = false;
		return;
	}

	FString Result;

	FString PyCmd = TEXT(
		"import sys\n"
		"import unreal\n"
		"success = False\n"
		"try:\n"
		"    if 'unreal_socket_server' in sys.modules:\n"
		"        unreal_socket_server = sys.modules['unreal_socket_server']\n"
		"        unreal_socket_server.stop_server()\n"
		"        sys.modules.pop('unreal_socket_server', None)\n"
		"        print('Python socket server module removed')\n"
		"        print('Python socket server stopped')\n"
		"        success = True\n"
		"    else:\n"
		"        print('Error: unreal_socket_server module not found')\n"
		"    import threading\n"
		"    print('Running threads: ' + str([t.name for t in threading.enumerate()]))\n"
		"except Exception as e:\n"
		"    print('Error stopping socket server: ' + str(e))\n"
		"print(success)\n"
	);

	const bool bCommandSuccessful = RunPythonCommand(PyCmd, Result);
	PYSOCKET_LOG_INFO("Stop server command result: %s", *Result);

	// Check if the result contains success indicators
	bool bServerStopped = false;
	
	// Check for explicit success messages
	if (Result.Contains(TEXT("Python socket server module removed")) || 
	    Result.Contains(TEXT("Python socket server stopped")))
	{
		bServerStopped = true;
	}
	// Check for the literal string "True"
	else if (Result.Contains(TEXT("True")))
	{
		bServerStopped = true;
	}
	// If the result is empty, assume success
	else if (Result.IsEmpty() || Result.Len() == 0)
	{
		bServerStopped = true;
	}
	// Fallback - if no error message is found, consider it a success
	else if (!Result.Contains(TEXT("Error")))
	{
		bServerStopped = true;
	}

	if (bCommandSuccessful && bServerStopped)
	{
		PYSOCKET_LOG_INFO("Python socket server stopped successfully.");
		bIsSocketServerRunning = false;
	}
	else
	{
		PYSOCKET_LOG_ERROR("Failed to stop Python socket server: %s", *Result);
		// Even if there was an error, we'll assume the server is no longer running
		// This helps recover from inconsistent states
		bIsSocketServerRunning = false;
	}

	// Refresh the toolbar to update the status
	if (UToolMenus* ToolMenus = UToolMenus::Get())
	{
		ToolMenus->RefreshAllWidgets();
	}
}

// Function to check if Python is available and debug issues
bool FPythonSocketUIModule::IsPythonAvailable() const
{
    IPythonScriptPlugin* PythonPlugin = IPythonScriptPlugin::Get();
    if (!PythonPlugin)
    {
        PYSOCKET_LOG_ERROR("Python script plugin is not available");
        return false;
    }
    
    // Check if we can run a simple Python command
    FPythonCommandEx PythonCommandEx;
    PythonCommandEx.Command = TEXT("print('Python is available')");
    bool bSuccess = PythonPlugin->ExecPythonCommandEx(PythonCommandEx);
    
    if (!bSuccess)
    {
        PYSOCKET_LOG_ERROR("Python script plugin is available but failed to execute a simple Python command");
        return false;
    }
    
    // Get the result from the CommandResult field
    FString Result = PythonCommandEx.CommandResult;
    
    PYSOCKET_LOG_INFO("Python test result: %s", *Result);
    return true;
}

bool FPythonSocketUIModule::RunPythonCommand(const FString& Command, FString& Result)
{
    if (IPythonScriptPlugin* PythonPlugin = IPythonScriptPlugin::Get())
    {
        FPythonCommandEx PythonCommandEx;
        PythonCommandEx.Command = Command;
        
        if (PythonPlugin->ExecPythonCommandEx(PythonCommandEx))
        {
            Result = PythonCommandEx.CommandResult;
            return true;
        }
    }
    return false;
}

#undef LOCTEXT_NAMESPACE 