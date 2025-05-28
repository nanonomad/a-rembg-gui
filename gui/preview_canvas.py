"""Image preview canvas component."""

import tkinter as tk
import weakref
from typing import Optional

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

from config.settings import CANVAS_WIDTH, CANVAS_HEIGHT

try:
    from utils.logging_utils import Logger
    LOGGING_AVAILABLE = True
except ImportError:
    LOGGING_AVAILABLE = False


class PreviewCanvas:
    """Handles image preview display in a canvas."""
    
    def __init__(self, parent, title: str, logger=None):
        self.logger = logger
        self._image_references = []  # Track image references for cleanup
        self._container_ref = None
        self._canvas_ref = None
        self.setup_ui(parent, title)
        
    def setup_ui(self, parent, title: str):
        """Setup the preview canvas UI."""
        # Container
        self.container = tk.Frame(parent)
        self._container_ref = weakref.ref(self.container)
        self.container.columnconfigure(0, weight=1)
        self.container.rowconfigure(1, weight=1)
        
        # Title
        try:
            title_label = tk.Label(self.container, text=title, font=("Arial", 12, "bold"))
            title_label.grid(row=0, column=0, pady=(0, 10))
        except tk.TclError:
            # Handle case where widget creation fails
            if self.logger and LOGGING_AVAILABLE:
                self.logger.debug("Failed to create title label")
        
        # Canvas
        try:
            self.canvas = tk.Canvas(
                self.container, 
                width=CANVAS_WIDTH, 
                height=CANVAS_HEIGHT,
                bg="lightgray", 
                relief="sunken", 
                bd=2
            )
            self._canvas_ref = weakref.ref(self.canvas)
            self.canvas.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
            
            # Default message
            self.set_default_message("No image selected")
        except tk.TclError:
            if self.logger and LOGGING_AVAILABLE:
                self.logger.debug("Failed to create canvas")
        
    def _safe_canvas_operation(self, operation):
        """Safely perform canvas operations with error handling."""
        try:
            canvas = self._canvas_ref() if self._canvas_ref else None
            if canvas and canvas.winfo_exists():
                return operation(canvas)
        except (tk.TclError, AttributeError):
            # Canvas no longer exists or is not accessible
            pass
        return None
        
    def cleanup_image_references(self):
        """Clean up stored image references to prevent memory leaks."""
        self._image_references.clear()
        
        def clear_canvas_image(canvas):
            if hasattr(canvas, 'image'):
                canvas.image = None
        
        self._safe_canvas_operation(clear_canvas_image)
    
    def resize_image_for_canvas(self, image_path: str) -> Optional[ImageTk.PhotoImage]:
        """Resize image to fit in canvas while maintaining aspect ratio."""
        if not PIL_AVAILABLE:
            if self.logger and LOGGING_AVAILABLE:
                self.logger.debug("PIL not available for image preview")
            return None
            
        try:
            with Image.open(image_path) as img:
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'LA'):
                    # Create white background for transparency
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'RGBA':
                        background.paste(img, mask=img.split()[-1])
                    else:
                        background.paste(img, mask=img.split()[-1])
                    img = background
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Calculate resize dimensions maintaining aspect ratio
                img_width, img_height = img.size
                aspect_ratio = img_width / img_height
                
                # Calculate new dimensions to fit in canvas
                canvas_width = CANVAS_WIDTH - 20  # Leave margin
                canvas_height = CANVAS_HEIGHT - 20
                
                if aspect_ratio > canvas_width / canvas_height:
                    # Image is wider, fit to width
                    new_width = canvas_width
                    new_height = int(new_width / aspect_ratio)
                else:
                    # Image is taller, fit to height
                    new_height = canvas_height
                    new_width = int(new_height * aspect_ratio)
                
                # Resize the image
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # Create PhotoImage and track reference
                photo = ImageTk.PhotoImage(img)
                self._image_references.append(photo)
                
                # Clean up old references if too many
                if len(self._image_references) > 5:
                    self._image_references = self._image_references[-3:]
                
                return photo
                
        except Exception as e:
            if self.logger and LOGGING_AVAILABLE:
                self.logger.debug(f"Error loading preview image: {e}")
            return None
    
    def update_image(self, image_path: str):
        """Update the canvas with a new image."""
        def update_operation(canvas):
            try:
                # Clear canvas
                canvas.delete("all")
                
                # Load and resize image
                photo = self.resize_image_for_canvas(image_path)
                if photo:
                    # Calculate center position
                    canvas_width = canvas.winfo_width()
                    canvas_height = canvas.winfo_height()
                    if canvas_width <= 1:  # Canvas not yet rendered
                        canvas_width = CANVAS_WIDTH
                        canvas_height = CANVAS_HEIGHT
                    
                    center_x = canvas_width // 2
                    center_y = canvas_height // 2
                    
                    # Display image centered
                    canvas.create_image(center_x, center_y, image=photo, anchor=tk.CENTER)
                    canvas.image = photo  # Keep a reference
                else:
                    self._set_canvas_message(canvas, "Error loading image", "red")
                    
            except Exception as e:
                if self.logger and LOGGING_AVAILABLE:
                    self.logger.debug(f"Error updating preview: {e}")
                self._set_canvas_message(canvas, "Error loading preview", "red")
        
        self._safe_canvas_operation(update_operation)
    
    def _set_canvas_message(self, canvas, message: str, color: str = "darkgray"):
        """Set a message on the canvas."""
        try:
            canvas.delete("all")
            canvas.create_text(
                CANVAS_WIDTH // 2, 
                CANVAS_HEIGHT // 2, 
                text=message,
                font=("Arial", 12), 
                fill=color
            )
            canvas.image = None
        except tk.TclError:
            pass
    
    def set_default_message(self, message: str):
        """Set a default message on the canvas."""
        def message_operation(canvas):
            self._set_canvas_message(canvas, message, "darkgray")
        
        self._safe_canvas_operation(message_operation)
    
    def set_error_message(self, message: str):
        """Set an error message on the canvas."""
        def error_operation(canvas):
            self._set_canvas_message(canvas, message, "red")
        
        self._safe_canvas_operation(error_operation)
    
    def clear(self):
        """Clear the canvas."""
        self.cleanup_image_references()
        self.set_default_message("No image selected")
    
    def grid(self, **kwargs):
        """Grid the container."""
        try:
            container = self._container_ref() if self._container_ref else None
            if container:
                container.grid(**kwargs)
        except (tk.TclError, AttributeError):
            pass
    
    def grid_remove(self):
        """Remove the container from grid."""
        try:
            container = self._container_ref() if self._container_ref else None
            if container:
                container.grid_remove()
        except (tk.TclError, AttributeError):
            pass
    
    def destroy(self):
        """Clean up resources when destroying the widget."""
        self.cleanup_image_references()
        try:
            container = self._container_ref() if self._container_ref else None
            if container:
                container.destroy()
        except (tk.TclError, AttributeError):
            pass
