// Copyright Epic Games, Inc. All Rights Reserved.

#include "GenerativeAIEditor.h"
#include "TCPServer.h"
#include "LevelEditor.h"
#include "Framework/MultiBox/MultiBoxBuilder.h"
#include "Styling/SlateStyleRegistry.h"
#include "Interfaces/IPluginManager.h"
#include "Styling/SlateStyle.h"
#include "Styling/SlateStyleMacros.h"
#include "ISettingsModule.h"
#include "ToolMenus.h"
#include "ToolMenuSection.h"
#include "Widgets/SWindow.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/Layout/SScrollBox.h"
#include "Widgets/Text/STextBlock.h"
#include "Widgets/Input/SButton.h"
#include "Widgets/Layout/SGridPanel.h"
#include "Widgets/Layout/SUniformGridPanel.h"
#include "Framework/Application/SlateApplication.h"
#include "EditorStyleSet.h"

// Define the log category
DEFINE_LOG_CATEGORY(LogGenAI);

#define LOCTEXT_NAMESPACE "FGenerativeAIEditorModule"

// Define path constants
class FGenAIConstants
{
public:
    static FString PluginResourcesPath;
    static FString PluginLogsPath;
    
    static void InitializePathConstants()
    {
        TSharedPtr<IPlugin> Plugin = IPluginManager::Get().FindPlugin("UnrealGenAISupport");
        if (Plugin.IsValid())
        {
            PluginResourcesPath = Plugin->GetBaseDir() / TEXT("Resources");
            PluginLogsPath = Plugin->GetBaseDir() / TEXT("Logs");
            
            // Create logs directory if it doesn't exist
            IPlatformFile& PlatformFile = FPlatformFileManager::Get().GetPlatformFile();
            if (!PlatformFile.DirectoryExists(*PluginLogsPath))
            {
                PlatformFile.CreateDirectory(*PluginLogsPath);
            }
        }
    }
};

FString FGenAIConstants::PluginResourcesPath;
FString FGenAIConstants::PluginLogsPath;

// Macro for logging
#define GENAI_LOG_INFO(Format, ...) UE_LOG(LogGenAI, Display, TEXT(Format), ##__VA_ARGS__)
#define GENAI_LOG_WARNING(Format, ...) UE_LOG(LogGenAI, Warning, TEXT(Format), ##__VA_ARGS__)
#define GENAI_LOG_ERROR(Format, ...) UE_LOG(LogGenAI, Error, TEXT(Format), ##__VA_ARGS__)

// Define a style set for our plugin
class FGenAIPluginStyle : public FSlateStyleSet
{
public:
    FGenAIPluginStyle() : FSlateStyleSet("GenAIPluginStyle")
    {
        const FVector2D Icon16x16(16.0f, 16.0f);
        const FVector2D StatusSize(6.0f, 6.0f);

        // Use path constants
        SetContentRoot(FGenAIConstants::PluginResourcesPath);

        // Register icon - you'll need to create this icon
        FSlateImageBrush* IconBrush = new FSlateImageBrush(
            RootToContentDir(TEXT("Icon128.png")), 
            Icon16x16,
            FLinearColor::White,
            ESlateBrushTileType::NoTile
        );
        Set("GenAIPlugin.ServerIcon", IconBrush);

        // Create status indicator brushes
        const FLinearColor RunningColor(0.0f, 0.8f, 0.0f);  // Green
        const FLinearColor StoppedColor(0.8f, 0.0f, 0.0f);  // Red
        
        Set("GenAIPlugin.StatusRunning", new FSlateRoundedBoxBrush(RunningColor, 3.0f, FVector2f(StatusSize)));
        Set("GenAIPlugin.StatusStopped", new FSlateRoundedBoxBrush(StoppedColor, 3.0f, FVector2f(StatusSize)));

        // Define a custom button style with hover feedback
        FButtonStyle ToolbarButtonStyle = FAppStyle::Get().GetWidgetStyle<FButtonStyle>("LevelEditor.ToolBar.Button");
        
        // Normal state: fully transparent background
        ToolbarButtonStyle.SetNormal(FSlateColorBrush(FLinearColor(0, 0, 0, 0))); // Transparent
        
        // Hovered state: subtle overlay
        ToolbarButtonStyle.SetHovered(FSlateColorBrush(FLinearColor(0.2f, 0.2f, 0.2f, 0.3f)));
        
        // Pressed state: slightly darker overlay
        ToolbarButtonStyle.SetPressed(FSlateColorBrush(FLinearColor(0.1f, 0.1f, 0.1f, 0.5f)));
        
        // Register the custom style
        Set("GenAIPlugin.TransparentToolbarButton", ToolbarButtonStyle);
    }

    static void Initialize()
    {
        if (!Instance.IsValid())
        {
            Instance = MakeShareable(new FGenAIPluginStyle());
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

    static TSharedPtr<FGenAIPluginStyle> Get()
    {
        return Instance;
    }

private:
    static TSharedPtr<FGenAIPluginStyle> Instance;
};

TSharedPtr<FGenAIPluginStyle> FGenAIPluginStyle::Instance = nullptr;

void FGenerativeAIEditorModule::StartupModule()
{
    // Initialize path constants first
    FGenAIConstants::InitializePathConstants();
    
    // Initialize our custom log category
    GENAI_LOG_INFO("GenerativeAI Editor Plugin is starting up");
    
    // Register style set
    FGenAIPluginStyle::Initialize();
    FSlateStyleRegistry::RegisterSlateStyle(*FGenAIPluginStyle::Get());
    
    // More debug logging
    GENAI_LOG_INFO("GenerativeAI Style registered");

    // Register settings if needed
    // TODO: Add settings registration if needed
    
    // Register for post engine init to add toolbar button
    FCoreDelegates::OnPostEngineInit.RemoveAll(this);
    
    GENAI_LOG_INFO("Registering OnPostEngineInit delegate");
    FCoreDelegates::OnPostEngineInit.AddRaw(this, &FGenerativeAIEditorModule::ExtendLevelEditorToolbar);
}

void FGenerativeAIEditorModule::ShutdownModule()
{
    // Unregister style set
    FGenAIPluginStyle::Shutdown();

    // Unregister settings if needed
    
    // Stop server if running
    if (Server)
    {
        StopServer();
    }
    
    // Close control panel if open
    CloseControlPanel();
    
    // Clean up delegates
    FCoreDelegates::OnPostEngineInit.RemoveAll(this);
}

void FGenerativeAIEditorModule::ExtendLevelEditorToolbar()
{
    static bool bToolbarExtended = false;
    
    if (bToolbarExtended)
    {
        GENAI_LOG_WARNING("ExtendLevelEditorToolbar called but toolbar already extended, skipping");
        return;
    }
    
    GENAI_LOG_INFO("ExtendLevelEditorToolbar called - first time");
    
    UToolMenus::Get()->RegisterMenu("LevelEditor.MainMenu", "MainFrame.MainMenu");
    
    UToolMenu* ToolbarMenu = UToolMenus::Get()->ExtendMenu("LevelEditor.LevelEditorToolBar.User");
    if (ToolbarMenu)
    {
        FToolMenuSection& Section = ToolbarMenu->FindOrAddSection("GenerativeAI");
        
        // Add a custom widget instead of a static toolbar button
        Section.AddEntry(FToolMenuEntry::InitWidget(
            "GenerativeAIControl",
            SNew(SButton)
            .ButtonStyle(FGenAIPluginStyle::Get().ToSharedRef(), "GenAIPlugin.TransparentToolbarButton")
            .OnClicked(FOnClicked::CreateRaw(this, &FGenerativeAIEditorModule::OpenControlPanel_OnClicked))
            .ToolTipText(LOCTEXT("GenAIButtonTooltip", "Open Generative AI Control Panel"))
            .Content()
            [
                SNew(SOverlay)
                + SOverlay::Slot()
                [
                    SNew(SImage)
                    .Image(FGenAIPluginStyle::Get()->GetBrush("GenAIPlugin.ServerIcon"))
                    .ColorAndOpacity(FLinearColor::White)
                ]
                + SOverlay::Slot()
                .HAlign(HAlign_Right)
                .VAlign(VAlign_Bottom)
                [
                    SNew(SImage)
                    .Image_Lambda([this]() -> const FSlateBrush* {
                        return IsServerRunning() 
                            ? FGenAIPluginStyle::Get()->GetBrush("GenAIPlugin.StatusRunning") 
                            : FGenAIPluginStyle::Get()->GetBrush("GenAIPlugin.StatusStopped");
                    })
                ]
            ],
            FText::GetEmpty(),
            true,
            false,
            false
        ));
        
        GENAI_LOG_INFO("Generative AI button added to main toolbar with dynamic icon");
    }
    
    // Window menu 
    UToolMenu* WindowMenu = UToolMenus::Get()->ExtendMenu("LevelEditor.MainMenu.Window");
    if (WindowMenu)
    {
        FToolMenuSection& Section = WindowMenu->FindOrAddSection("WindowLayout");
        Section.AddMenuEntry(
            "GenerativeAIControlWindow",
            LOCTEXT("GenAIWindowMenuLabel", "Generative AI Control Panel"),
            LOCTEXT("GenAIWindowMenuTooltip", "Open Generative AI Control Panel"),
            FSlateIcon(FGenAIPluginStyle::Get()->GetStyleSetName(), "GenAIPlugin.ServerIcon"),
            FUIAction(
                FExecuteAction::CreateRaw(this, &FGenerativeAIEditorModule::OpenControlPanel),
                FCanExecuteAction()
            )
        );
        GENAI_LOG_INFO("Generative AI entry added to Window menu");
    }
    
    bToolbarExtended = true;
}

void FGenerativeAIEditorModule::OpenControlPanel()
{
    // If the window already exists, just focus it
    if (ControlPanelWindow.IsValid())
    {
        ControlPanelWindow->BringToFront();
        return;
    }

    // Create a new window
    ControlPanelWindow = SNew(SWindow)
        .Title(LOCTEXT("GenAIControlPanelTitle", "Generative AI Control Panel"))
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
    ControlPanelWindow->GetOnWindowClosedEvent().AddRaw(this, &FGenerativeAIEditorModule::OnControlPanelClosed);

    // Show the window
    FSlateApplication::Get().AddWindow(ControlPanelWindow.ToSharedRef());

    GENAI_LOG_INFO("Generative AI Control Panel opened");
}

FReply FGenerativeAIEditorModule::OpenControlPanel_OnClicked()
{
    OpenControlPanel();
    return FReply::Handled();
}

void FGenerativeAIEditorModule::OnControlPanelClosed(const TSharedRef<SWindow>& Window)
{
    ControlPanelWindow.Reset();
    GENAI_LOG_INFO("Generative AI Control Panel closed");
}

void FGenerativeAIEditorModule::CloseControlPanel()
{
    if (ControlPanelWindow.IsValid())
    {
        ControlPanelWindow->RequestDestroyWindow();
        ControlPanelWindow.Reset();
        GENAI_LOG_INFO("Generative AI Control Panel closed");
    }
}

TSharedRef<SWidget> FGenerativeAIEditorModule::CreateControlPanelContent()
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
                    .Text(LOCTEXT("ServerStatusLabel", "Server Status:"))
                    .Font(FAppStyle::GetFontStyle("NormalText"))
                ]
                
                + SHorizontalBox::Slot()
                .FillWidth(1.0f)
                .VAlign(VAlign_Center)
                [
                    SNew(STextBlock)
                    .Text_Lambda([this]() -> FText {
                        return IsServerRunning() 
                            ? LOCTEXT("ServerRunningStatus", "Running") 
                            : LOCTEXT("ServerStoppedStatus", "Stopped");
                    })
                    .ColorAndOpacity_Lambda([this]() -> FSlateColor {
                        return IsServerRunning() 
                            ? FSlateColor(FLinearColor(0.0f, 0.8f, 0.0f)) 
                            : FSlateColor(FLinearColor(0.8f, 0.0f, 0.0f));
                    })
                    .Font(FAppStyle::GetFontStyle("NormalText"))
                ]
            ]
            
            // Port information (if server is properly configured)
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
                    .Text_Lambda([this]() -> FText {
                        if (Server)
                        {
                            return FText::AsNumber(Server->GetConfig().Port);
                        }
                        return FText::AsNumber(8080); // Default port
                    })
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
                    .IsEnabled_Lambda([this]() -> bool { return !IsServerRunning(); })
                    .OnClicked(FOnClicked::CreateRaw(this, &FGenerativeAIEditorModule::OnStartServerClicked))
                ]
                
                // Stop button
                + SUniformGridPanel::Slot(1, 0)
                [
                    SNew(SButton)
                    .HAlign(HAlign_Center)
                    .VAlign(VAlign_Center)
                    .Text(LOCTEXT("StopServerButton", "Stop Server"))
                    .IsEnabled_Lambda([this]() -> bool { return IsServerRunning(); })
                    .OnClicked(FOnClicked::CreateRaw(this, &FGenerativeAIEditorModule::OnStopServerClicked))
                ]
            ]
            
            // Generate content button
            + SVerticalBox::Slot()
            .AutoHeight()
            .Padding(0, 16, 0, 0)
            .HAlign(HAlign_Center)
            [
                SNew(SButton)
                .HAlign(HAlign_Center)
                .VAlign(VAlign_Center)
                .Text(LOCTEXT("GenerateContentButton", "Generate Content"))
                .OnClicked_Lambda([]() -> FReply {
                    // TODO: Implement content generation
                    return FReply::Handled();
                })
            ]
        ];
}

FReply FGenerativeAIEditorModule::OnStartServerClicked()
{
    StartServer();
    return FReply::Handled();
}

FReply FGenerativeAIEditorModule::OnStopServerClicked()
{
    StopServer();
    return FReply::Handled();
}

void FGenerativeAIEditorModule::ToggleServer()
{
    GENAI_LOG_WARNING("ToggleServer called - Server state: %s", (Server && Server->IsRunning()) ? TEXT("Running") : TEXT("Not Running"));
    
    if (Server && Server->IsRunning())
    {
        GENAI_LOG_WARNING("Stopping server...");
        StopServer();
    }
    else
    {
        GENAI_LOG_WARNING("Starting server...");
        StartServer();
    }
    
    GENAI_LOG_WARNING("ToggleServer completed - Server state: %s", (Server && Server->IsRunning()) ? TEXT("Running") : TEXT("Not Running"));
}

void FGenerativeAIEditorModule::StartServer()
{
    // Check if server is already running
    if (Server && Server->IsRunning())
    {
        GENAI_LOG_WARNING("Server is already running, ignoring start request");
        return;
    }

    GENAI_LOG_INFO("Creating new server instance");
    
    // Create a config object
    FTCPServerConfig Config;
    Config.Port = 8080; // Default port, can be customized
    
    // Create the server with the config
    Server = MakeUnique<FTCPServer>(Config);
    
    if (Server->Start())
    {
        // Refresh the toolbar to update the status indicator
        if (UToolMenus* ToolMenus = UToolMenus::Get())
        {
            ToolMenus->RefreshAllWidgets();
        }
    }
    else
    {
        GENAI_LOG_ERROR("Failed to start GenerativeAI Server");
    }
}

void FGenerativeAIEditorModule::StopServer()
{
    if (Server)
    {
        Server->Stop();
        Server.Reset();
        GENAI_LOG_INFO("GenerativeAI Server stopped");
        
        // Refresh the toolbar to update the status indicator
        if (UToolMenus* ToolMenus = UToolMenus::Get())
        {
            ToolMenus->RefreshAllWidgets();
        }
    }
}

bool FGenerativeAIEditorModule::IsServerRunning() const
{
    return Server && Server->IsRunning();
}

#undef LOCTEXT_NAMESPACE

IMPLEMENT_MODULE(FGenerativeAIEditorModule, GenerativeAIEditor) 