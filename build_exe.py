import subprocess
import os
import sys

def build():
    # Application Name
    APP_NAME = "Polaris"
    
    # Path to main script
    MAIN_SCRIPT = "main.py"
    
    # Path to icon
    ICON_FILE = os.path.join("assets", "icon.ico")
    
    # Base command
    cmd = [
        "pyinstaller",
        "--noconfirm",
        "--onefile",
        "--windowed", # Same as --noconsole
        f"--name={APP_NAME}",
        f"--icon={ICON_FILE}",
        # Add assets folder. Format: Source;Destination (on Windows)
       "--add-data=assets;assets",
        # CustomTKinter needs specific handling for its theme files
        "--collect-all=customtkinter",
        "--collect-all=PIL",
        MAIN_SCRIPT
    ]
    
    print(f"Starting build process for {APP_NAME}...")
    print("Command:", " ".join(cmd))
    
    try:
        subprocess.check_call(cmd)
        print("\nBuild Successful!")
        print(f"Executable can be found in the 'dist' folder.")
    except subprocess.CalledProcessError as e:
        print(f"\nBuild Failed: {e}")
    except Exception as e:
        print(f"\nAn error occurred: {e}")

if __name__ == "__main__":
    build()
