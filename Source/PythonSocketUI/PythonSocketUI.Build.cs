// Copyright Epic Games, Inc. All Rights Reserved.

using System.IO;
using UnrealBuildTool;

public class PythonSocketUI : ModuleRules
{
	public PythonSocketUI(ReadOnlyTargetRules Target) : base(Target)
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
                Path.Combine(EngineDirectory, "Plugins/Experimental/PythonScriptPlugin/Source/PythonScriptPlugin/Private"),
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
                "PythonScriptPlugin",
                "Settings",
                "ApplicationCore"
			}
		);
		
		if (Target.bBuildEditor == true)
        {
            // Detect and use Python if available
            string PythonPath = "";
            if (Target.Platform == UnrealTargetPlatform.Win64)
            {
                PythonPath = Path.Combine(EngineDirectory, "Binaries/ThirdParty/Python3/Win64");
            }
            else if (Target.Platform == UnrealTargetPlatform.Mac)
            {
                PythonPath = Path.Combine(EngineDirectory, "Binaries/ThirdParty/Python3/Mac");
            }
            else if (Target.Platform == UnrealTargetPlatform.Linux)
            {
                PythonPath = Path.Combine(EngineDirectory, "Binaries/ThirdParty/Python3/Linux");
            }

            if (Directory.Exists(PythonPath))
            {
                PrivateDefinitions.Add("WITH_PYTHON=1");
                System.Console.WriteLine("Python support enabled for PythonSocketUI module");
            }
            else
            {
                PrivateDefinitions.Add("WITH_PYTHON=0");
                System.Console.WriteLine("Python support disabled for PythonSocketUI module - Python not found at: " + PythonPath);
            }
        }
        else
        {
            PrivateDefinitions.Add("WITH_PYTHON=0");
        }
	}
} 