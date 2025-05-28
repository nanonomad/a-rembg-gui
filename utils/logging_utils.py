"""Logging utilities for the rembg GUI application."""

import time
import traceback
from typing import Optional, Callable


class Logger:
    """Simple logger that can output to console and GUI."""
    
    def __init__(self, gui_callback: Optional[Callable] = None, debug_mode: bool = True):
        self.gui_callback = gui_callback
        self.debug_mode = debug_mode
    
    def debug(self, message: str) -> None:
        """Log debug message."""
        if self.debug_mode:
            timestamp = time.strftime("%H:%M:%S")
            debug_msg = f"[{timestamp}] DEBUG: {message}"
            print(debug_msg)
            
            if self.gui_callback:
                try:
                    self.gui_callback(debug_msg)
                except Exception:
                    # GUI might not be available
                    pass
    
    def info(self, message: str) -> None:
        """Log info message."""
        print(message)
        if self.gui_callback:
            try:
                self.gui_callback(message)
            except Exception:
                pass
    
    def error(self, message: str, exc: Optional[Exception] = None) -> None:
        """Log error message with optional exception."""
        error_msg = f"ERROR: {message}"
        if exc:
            error_msg += f" - {str(exc)}"
        
        print(error_msg)
        
        if self.debug_mode and exc:
            print(f"Traceback: {traceback.format_exc()}")
        
        if self.gui_callback:
            try:
                self.gui_callback(error_msg)
            except Exception:
                pass
    
    def set_gui_callback(self, callback: Callable) -> None:
        """Set the GUI callback for logging."""
        self.gui_callback = callback
