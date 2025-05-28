"""
rembg GUI - A frontend for the rembg background removal tool.
Supports single images, batch processing, and video frame extraction with reassembly.
"""

import sys
import traceback

def check_dependencies():
    """Check if all required dependencies are available."""
    missing_deps = []
    
    try:
        import tkinter
    except ImportError:
        missing_deps.append("tkinter")
    
    try:
        import rembg
    except ImportError:
        missing_deps.append("rembg")
    
    try:
        import PIL
    except ImportError:
        missing_deps.append("Pillow")
    
    try:
        import cv2
    except ImportError:
        missing_deps.append("opencv-python")
    
    try:
        import onnxruntime
    except ImportError:
        missing_deps.append("onnxruntime")
    
    try:
        import psutil
    except ImportError:
        missing_deps.append("psutil")
    
    try:
        import numpy
    except ImportError:
        missing_deps.append("numpy")
    
    if missing_deps:
        print("ERROR: Missing required dependencies:")
        for dep in missing_deps:
            print(f"  - {dep}")
        print("\nPlease install with:")
        print("pip install \"rembg[gpu,cli]\" pillow opencv-python psutil numpy")
        return False
    
    return True


def main():
    """Main entry point for the application."""
    print("Starting rembg GUI...")
    
    # Check for debug flag
    debug_mode = "--debug" in sys.argv
    if debug_mode:
        print("Extended debug mode enabled")
    
    # Check dependencies
    if not check_dependencies():
        input("Press Enter to exit...")
        sys.exit(1)
    
    try:
        # Import and run the GUI
        from gui.main_window import MainWindow
        
        print("Initializing GUI...")
        app = MainWindow()
        print("GUI initialized successfully")
        
        # Run the application
        app.run()
        
    except Exception as e:
        print(f"FATAL ERROR: Failed to start GUI: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        input("Press Enter to exit...")
        sys.exit(1)


if __name__ == "__main__":
    main()
