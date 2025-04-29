#!/usr/bin/env python3
"""
Build script for creating a standalone Windows executable.
"""

import sys
import logging
from teamschatgrab.exe_builder import build_exe

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

if __name__ == "__main__":
    try:
        # Default configuration
        name = "TeamsChatGrabber"
        onefile = True
        console = False
        
        # Parse command-line arguments if provided
        if len(sys.argv) > 1:
            if "--console" in sys.argv:
                console = True
            if "--multifile" in sys.argv:
                onefile = False
        
        # Build the executable
        exe_path = build_exe(name=name, onefile=onefile, console=console)
        print(f"Successfully built executable: {exe_path}")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        print("Build failed!")
        sys.exit(1)