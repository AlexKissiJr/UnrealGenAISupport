// Copyright Epic Games, Inc. All Rights Reserved.

using UnrealBuildTool;

public class GenerativeAIEditor : ModuleRules
{
	public GenerativeAIEditor(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = ModuleRules.PCHUsageMode.UseExplicitOrSharedPCHs;
		
		PublicIncludePaths.AddRange(
			new string[] {
				// ... add public include paths required here ...
			}
		);
				
		PrivateIncludePaths.AddRange(
			new string[] {
				// ... add other private include paths required here ...
			}
		);
			
		PublicDependencyModuleNames.AddRange(
			new string[] {
				"Core",
				"CoreUObject",
                "Engine",
                "InputCore",
                "UnrealEd",
                "LevelEditor",
                "Slate",
                "SlateCore",
                "EditorStyle"
			}
		);
			
		PrivateDependencyModuleNames.AddRange(
			new string[] {
                "Projects",
                "ToolMenus",
                "ToolWidgets",
                "EditorFramework",
                "EditorWidgets",
                "PropertyEditor",
                "Settings",
                "ApplicationCore",
                "GenerativeAISupport"  // Dependency on the main module
			}
		);
	}
} 