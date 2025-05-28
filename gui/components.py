"""Reusable GUI components."""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from typing import Dict, Any, Callable, Optional

try:
    from config.models import MODELS, ADVANCED_PARAMETERS
    MODELS_AVAILABLE = True
except ImportError:
    MODELS_AVAILABLE = False
    MODELS = {}
    ADVANCED_PARAMETERS = {}

try:
    from config.settings import DEFAULT_BG_COLOR, DEFAULT_FILENAME_FORMAT, validate_rgb_color, validate_fps
    SETTINGS_AVAILABLE = True
except ImportError:
    SETTINGS_AVAILABLE = False
    DEFAULT_BG_COLOR = (0, 255, 0)
    DEFAULT_FILENAME_FORMAT = "{name}_no_bg.png"
    
    def validate_rgb_color(r, g, b):
        return (0, 255, 0)
    
    def validate_fps(fps_str):
        return True, None


class ToolTip:
    """Tooltip functionality for widgets."""
    
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        self.widget.bind("<Enter>", self.on_enter)
        self.widget.bind("<Leave>", self.on_leave)
    
    def on_enter(self, event=None):
        """Show tooltip on mouse enter."""
        try:
            x, y, _, _ = self.widget.bbox("insert")
            x += self.widget.winfo_rootx() + 20
            y += self.widget.winfo_rooty() + 20
        except (tk.TclError, ValueError):
            x = self.widget.winfo_rootx() + 20
            y = self.widget.winfo_rooty() + 20
        
        self.tooltip_window = tk.Toplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.wm_geometry(f"+{x}+{y}")
        
        label = tk.Label(
            self.tooltip_window,
            text=self.text,
            background="lightyellow",
            relief="solid",
            borderwidth=1,
            font=("Arial", 9, "normal"),
            wraplength=300,
            justify="left"
        )
        label.pack()
    
    def on_leave(self, event=None):
        """Hide tooltip on mouse leave."""
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None


class InputSelectionFrame:
    """Frame for input selection options."""
    
    def __init__(self, parent, input_type_var: tk.StringVar, input_path_var: tk.StringVar, 
                 output_path_var: tk.StringVar, filename_format_var: tk.StringVar,
                 browse_input_callback: Callable, browse_output_callback: Callable,
                 input_type_change_callback: Callable):
        self.input_type_var = input_type_var
        self.filename_format_var = filename_format_var
        self.setup_ui(parent, input_path_var, output_path_var, browse_input_callback, 
                     browse_output_callback, input_type_change_callback)
    
    def setup_ui(self, parent, input_path_var, output_path_var, browse_input_callback, 
                browse_output_callback, input_type_change_callback):
        """Setup the input selection UI."""
        try:
            self.frame = ttk.LabelFrame(parent, text="Input Selection", padding="8")
            self.frame.columnconfigure(1, weight=1)
            
            # Input type selection
            ttk.Radiobutton(self.frame, text="Single Image", variable=self.input_type_var, 
                           value="image", command=input_type_change_callback).grid(row=0, column=0, sticky=tk.W)
            ttk.Radiobutton(self.frame, text="Image Directory", variable=self.input_type_var, 
                           value="directory", command=input_type_change_callback).grid(row=0, column=1, sticky=tk.W)
            ttk.Radiobutton(self.frame, text="Video File", variable=self.input_type_var, 
                           value="video", command=input_type_change_callback).grid(row=0, column=2, sticky=tk.W)
            
            # Input path
            ttk.Label(self.frame, text="Input:").grid(row=1, column=0, sticky=tk.W, pady=(8, 0))
            self.input_entry = ttk.Entry(self.frame, textvariable=input_path_var, state="readonly")
            self.input_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(5, 5), pady=(8, 0))
            ttk.Button(self.frame, text="Browse", command=browse_input_callback).grid(row=1, column=2, pady=(8, 0))
            
            # Output path
            ttk.Label(self.frame, text="Output Dir:").grid(row=2, column=0, sticky=tk.W, pady=(5, 0))
            ttk.Entry(self.frame, textvariable=output_path_var).grid(row=2, column=1, sticky=(tk.W, tk.E), padx=(5, 5), pady=(5, 0))
            ttk.Button(self.frame, text="Browse", command=browse_output_callback).grid(row=2, column=2, pady=(5, 0))
            
            # Filename format (only for single images)
            self.format_frame = ttk.Frame(self.frame)
            ttk.Label(self.format_frame, text="Filename:").grid(row=0, column=0, sticky=tk.W, pady=(5, 0))
            format_entry = ttk.Entry(self.format_frame, textvariable=self.filename_format_var, width=25)
            format_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(5, 0), pady=(5, 0))
            ttk.Label(self.format_frame, text="({name}=filename, {ext}=extension)", 
                     foreground="gray", font=("Arial", 8)).grid(row=0, column=2, sticky=tk.W, padx=(5, 0))
            self.format_frame.columnconfigure(1, weight=1)
        except tk.TclError as e:
            print(f"Error creating InputSelectionFrame: {e}")
    
    def show_format_frame(self):
        """Show the filename format frame."""
        try:
            if hasattr(self, 'format_frame'):
                self.format_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(5, 0))
        except tk.TclError:
            pass
    
    def hide_format_frame(self):
        """Hide the filename format frame."""
        try:
            if hasattr(self, 'format_frame'):
                self.format_frame.grid_remove()
        except tk.TclError:
            pass
    
    def grid(self, **kwargs):
        """Grid the frame."""
        try:
            if hasattr(self, 'frame'):
                self.frame.grid(**kwargs)
        except tk.TclError:
            pass


class ProcessingOptionsFrame:
    """Frame for processing options with enhanced model information."""
    
    def __init__(self, parent, selected_model_var: tk.StringVar, model_desc_var: tk.StringVar,
                 model_status_var: tk.StringVar, gpu_status_var: tk.StringVar,
                 only_mask_var: tk.BooleanVar, alpha_matting_var: tk.BooleanVar,
                 extra_params_var: tk.StringVar, model_change_callback: Callable):
        self.selected_model_var = selected_model_var
        self.setup_ui(parent, selected_model_var, model_desc_var, model_status_var, 
                     gpu_status_var, only_mask_var, alpha_matting_var, extra_params_var,
                     model_change_callback)
    
    def setup_ui(self, parent, selected_model_var, model_desc_var, model_status_var, 
                gpu_status_var, only_mask_var, alpha_matting_var, extra_params_var,
                model_change_callback):
        """Setup the processing options UI."""
        try:
            self.frame = ttk.LabelFrame(parent, text="Processing Options", padding="8")
            self.frame.columnconfigure(1, weight=1)
            
            # Model selection row
            model_row = ttk.Frame(self.frame)
            model_row.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 5))
            model_row.columnconfigure(2, weight=1)
            
            ttk.Label(model_row, text="Model:").grid(row=0, column=0, sticky=tk.W)
            model_values = list(MODELS.keys()) if MODELS_AVAILABLE else ["u2net"]
            model_combo = ttk.Combobox(model_row, textvariable=selected_model_var, 
                                      values=model_values, state="readonly", width=20)
            model_combo.grid(row=0, column=1, sticky=tk.W, padx=(5, 10))
            model_combo.bind('<<ComboboxSelected>>', model_change_callback)
            
            # GPU/CPU status
            ttk.Label(model_row, textvariable=gpu_status_var, foreground="green").grid(row=0, column=2, sticky=tk.E)
            
            # Model information area
            info_frame = ttk.Frame(self.frame)
            info_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(5, 10))
            info_frame.columnconfigure(0, weight=1)
            info_frame.columnconfigure(1, weight=1)
            
            # Model details (left side)
            details_frame = ttk.LabelFrame(info_frame, text="Model Information", padding="5")
            details_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))
            details_frame.columnconfigure(0, weight=1)
            details_frame.rowconfigure(0, weight=1)
            
            self.model_info_text = scrolledtext.ScrolledText(
                details_frame, 
                height=6, 
                width=50,
                wrap=tk.WORD,
                state="disabled",
                font=("Arial", 9)
            )
            self.model_info_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
            
            # Advanced parameters (right side)
            params_frame = ttk.LabelFrame(info_frame, text="Advanced Parameters (JSON)", padding="5")
            params_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(5, 0))
            params_frame.columnconfigure(0, weight=1)
            params_frame.rowconfigure(0, weight=1)
            
            self.params_info_text = scrolledtext.ScrolledText(
                params_frame, 
                height=6, 
                width=50,
                wrap=tk.WORD,
                state="disabled",
                font=("Consolas", 8)
            )
            self.params_info_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
            
            # Processing options row
            options_frame = ttk.Frame(self.frame)
            options_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(5, 0))
            
            # Only mask checkbox with tooltip
            only_mask_cb = ttk.Checkbutton(options_frame, text="Output only mask", variable=only_mask_var)
            only_mask_cb.grid(row=0, column=0, sticky=tk.W, padx=(0, 20))
            ToolTip(only_mask_cb, 
                   "Output only the segmentation mask instead of the transparent image.\n"
                   "Useful for creating custom compositions or manual editing.\n"
                   "Produces a black/white mask where white = foreground.")
            
            # Alpha matting checkbox with tooltip
            alpha_matting_cb = ttk.Checkbutton(options_frame, text="Apply alpha matting", variable=alpha_matting_var)
            alpha_matting_cb.grid(row=0, column=1, sticky=tk.W)
            ToolTip(alpha_matting_cb,
                   "Refine edges using alpha matting for better transparency.\n"
                   "Particularly effective for hair, fur, and fine details.\n"
                   "Increases processing time but improves edge quality.")
            
            # Extra parameters
            ttk.Label(self.frame, text="Extra parameters (JSON):").grid(row=3, column=0, sticky=tk.W, pady=(8, 0))
            self.extra_params_entry = ttk.Entry(self.frame, textvariable=extra_params_var)
            self.extra_params_entry.grid(row=3, column=1, sticky=(tk.W, tk.E), padx=(5, 0), pady=(8, 0))
            ToolTip(self.extra_params_entry,
                   "Advanced JSON parameters for fine-tuning.\n"
                   "See the Advanced Parameters panel for available options.\n"
                   "Example: {\"alpha_matting_foreground_threshold\": 240}")
            
            # Update model info initially
            self.update_model_info(selected_model_var.get())
            
        except tk.TclError as e:
            print(f"Error creating ProcessingOptionsFrame: {e}")
    
    def update_model_info(self, model_name: str):
        """Update the model information display."""
        try:
            # Update model details
            self.model_info_text.configure(state="normal")
            self.model_info_text.delete(1.0, tk.END)
            
            if MODELS_AVAILABLE and model_name in MODELS:
                model_info = MODELS[model_name]
                detailed_info = model_info.get("detailed_info", "No detailed information available.")
                self.model_info_text.insert(tk.END, detailed_info)
            else:
                self.model_info_text.insert(tk.END, "Model information not available.")
            
            self.model_info_text.configure(state="disabled")
            
            # Update advanced parameters info
            self.params_info_text.configure(state="normal")
            self.params_info_text.delete(1.0, tk.END)
            
            if MODELS_AVAILABLE and ADVANCED_PARAMETERS:
                params_text = "Available Parameters:\n\n"
                
                # Alpha matting parameters
                if "alpha_matting" in ADVANCED_PARAMETERS:
                    am_info = ADVANCED_PARAMETERS["alpha_matting"]
                    params_text += "ALPHA MATTING:\n"
                    params_text += f"{am_info['description']}\n\n"
                    
                    for param, details in am_info["parameters"].items():
                        params_text += f"• {param}:\n"
                        params_text += f"  {details['description']}\n"
                        params_text += f"  Default: {details['default']}\n"
                        if 'range' in details:
                            params_text += f"  Range: {details['range']}\n"
                        params_text += "\n"
                    
                    params_text += "Example JSON:\n"
                    params_text += am_info["example_json"] + "\n\n"
                
                # SAM-specific parameters
                if model_name == "sam" and "sam_specific" in ADVANCED_PARAMETERS:
                    sam_info = ADVANCED_PARAMETERS["sam_specific"]
                    params_text += "SAM SPECIFIC:\n"
                    params_text += f"{sam_info['description']}\n\n"
                    
                    for param, details in sam_info["parameters"].items():
                        params_text += f"• {param}:\n"
                        params_text += f"  {details['description']}\n"
                        params_text += "\n"
                    
                    params_text += "Example JSON:\n"
                    params_text += sam_info["example_json"] + "\n\n"
                
                # Background replacement
                if "background_replacement" in ADVANCED_PARAMETERS:
                    bg_info = ADVANCED_PARAMETERS["background_replacement"]
                    params_text += "BACKGROUND REPLACEMENT:\n"
                    params_text += f"{bg_info['description']}\n\n"
                    
                    for param, details in bg_info["parameters"].items():
                        params_text += f"• {param}:\n"
                        params_text += f"  {details['description']}\n"
                        params_text += f"  Default: {details['default']}\n"
                        params_text += "\n"
                    
                    params_text += "Example JSON:\n"
                    params_text += bg_info["example_json"] + "\n\n"
                
                # Post processing
                if "post_processing" in ADVANCED_PARAMETERS:
                    pp_info = ADVANCED_PARAMETERS["post_processing"]
                    params_text += "POST PROCESSING:\n"
                    params_text += f"{pp_info['description']}\n\n"
                    
                    for param, details in pp_info["parameters"].items():
                        params_text += f"• {param}:\n"
                        params_text += f"  {details['description']}\n"
                        params_text += f"  Default: {details['default']}\n"
                        params_text += "\n"
                    
                    params_text += "Example JSON:\n"
                    params_text += pp_info["example_json"]
                
                self.params_info_text.insert(tk.END, params_text)
            else:
                self.params_info_text.insert(tk.END, "Advanced parameter information not available.")
            
            self.params_info_text.configure(state="disabled")
            
        except tk.TclError:
            pass
    
    def grid(self, **kwargs):
        """Grid the frame."""
        try:
            if hasattr(self, 'frame'):
                self.frame.grid(**kwargs)
        except tk.TclError:
            pass


class VideoOptionsFrame:
    """Frame for video processing options with enhanced tooltips."""
    
    def __init__(self, parent, fps_var: tk.StringVar, reassemble_var: tk.BooleanVar,
                 bg_color_vars: Dict[str, tk.StringVar], set_bg_color_callback: Callable):
        self.fps_var = fps_var
        self.bg_color_vars = bg_color_vars
        self.setup_ui(parent, fps_var, reassemble_var, bg_color_vars, set_bg_color_callback)
    
    def setup_ui(self, parent, fps_var, reassemble_var, bg_color_vars, set_bg_color_callback):
        """Setup the video options UI."""
        try:
            self.frame = ttk.LabelFrame(parent, text="Video Options", padding="8")
            self.frame.columnconfigure(4, weight=1)
            
            # FPS setting with validation and tooltip
            ttk.Label(self.frame, text="Extract FPS:").grid(row=0, column=0, sticky=tk.W)
            self.fps_entry = ttk.Entry(self.frame, textvariable=fps_var, width=10)
            self.fps_entry.grid(row=0, column=1, sticky=tk.W, padx=(5, 0))
            self.fps_entry.bind('<FocusOut>', self._validate_fps)
            self.fps_entry.bind('<KeyRelease>', self._validate_fps_realtime)
            
            ToolTip(self.fps_entry,
                   "Frame extraction rate for video processing.\n\n"
                   "• Empty = Extract all frames (native framerate)\n"
                   "• Lower FPS = Faster processing, fewer frames\n"
                   "• Higher FPS = More frames, smoother video\n"
                   "• Range: 0.1 - 120 FPS\n\n"
                   "Example: 30 FPS extracts 30 frames per second")
            
            ttk.Label(self.frame, text="(empty = native framerate)", 
                     foreground="gray", font=("Arial", 8)).grid(row=0, column=2, sticky=tk.W, padx=(5, 0))
            
            # FPS validation label
            self.fps_validation_label = ttk.Label(self.frame, text="", foreground="red", font=("Arial", 8))
            
            # Video reassembly option
            reassemble_cb = ttk.Checkbutton(self.frame, text="Reassemble video with greenscreen background", 
                           variable=reassemble_var)
            reassemble_cb.grid(row=0, column=3, sticky=tk.W, padx=(20, 0))
            ToolTip(reassemble_cb,
                   "Automatically reassemble processed frames into a video file.\n\n"
                   "• Creates MP4 video with greenscreen background\n"
                   "• Uses processed frames from background removal\n"
                   "• Maintains original video timing and dimensions\n"
                   "• Disable to only process individual frames")
            
            # Background color selection with validation
            ttk.Label(self.frame, text="Background color (RGB):").grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
            
            color_frame = ttk.Frame(self.frame)
            color_frame.grid(row=1, column=1, columnspan=2, sticky=tk.W, padx=(5, 0), pady=(5, 0))
            
            # RGB input fields with validation and tooltips
            ttk.Label(color_frame, text="R:").grid(row=0, column=0, sticky=tk.W)
            self.r_entry = ttk.Entry(color_frame, textvariable=bg_color_vars['r'], width=5)
            self.r_entry.grid(row=0, column=1, padx=(2, 5))
            self.r_entry.bind('<FocusOut>', lambda e: self._validate_color_component('r'))
            ToolTip(self.r_entry, "Red component (0-255)")
            
            ttk.Label(color_frame, text="G:").grid(row=0, column=2, sticky=tk.W)
            self.g_entry = ttk.Entry(color_frame, textvariable=bg_color_vars['g'], width=5)
            self.g_entry.grid(row=0, column=3, padx=(2, 5))
            self.g_entry.bind('<FocusOut>', lambda e: self._validate_color_component('g'))
            ToolTip(self.g_entry, "Green component (0-255)")
            
            ttk.Label(color_frame, text="B:").grid(row=0, column=4, sticky=tk.W)
            self.b_entry = ttk.Entry(color_frame, textvariable=bg_color_vars['b'], width=5)
            self.b_entry.grid(row=0, column=5, padx=(2, 0))
            self.b_entry.bind('<FocusOut>', lambda e: self._validate_color_component('b'))
            ToolTip(self.b_entry, "Blue component (0-255)")
            
            # Color validation label
            self.color_validation_label = ttk.Label(color_frame, text="", foreground="red", font=("Arial", 8))
            self.color_validation_label.grid(row=1, column=0, columnspan=6, pady=(2, 0))
            
            # Preset color buttons with tooltips
            preset_frame = ttk.Frame(self.frame)
            preset_frame.grid(row=1, column=3, sticky=tk.W, padx=(10, 0), pady=(5, 0))
            
            green_btn = ttk.Button(preset_frame, text="Green", width=8, 
                      command=lambda: self._set_preset_color(set_bg_color_callback, 0, 255, 0))
            green_btn.grid(row=0, column=0, padx=(0, 2))
            ToolTip(green_btn, "Standard chroma key green (0, 255, 0)")
            
            blue_btn = ttk.Button(preset_frame, text="Blue", width=8, 
                      command=lambda: self._set_preset_color(set_bg_color_callback, 0, 0, 255))
            blue_btn.grid(row=0, column=1, padx=(0, 2))
            ToolTip(blue_btn, "Blue screen background (0, 0, 255)")
            
            white_btn = ttk.Button(preset_frame, text="White", width=8, 
                      command=lambda: self._set_preset_color(set_bg_color_callback, 255, 255, 255))
            white_btn.grid(row=0, column=2)
            ToolTip(white_btn, "White background (255, 255, 255)")
            
        except tk.TclError as e:
            print(f"Error creating VideoOptionsFrame: {e}")
    
    def _validate_fps(self, event=None):
        """Validate FPS input on focus out."""
        if SETTINGS_AVAILABLE:
            is_valid, fps_value = validate_fps(self.fps_var.get())
            if not is_valid and self.fps_var.get().strip():
                self.fps_validation_label.config(text="Invalid FPS (must be > 0 and ≤ 120)")
                self.fps_validation_label.grid(row=0, column=2, sticky=tk.W, padx=(5, 0))
            else:
                self.fps_validation_label.grid_remove()
    
    def _validate_fps_realtime(self, event=None):
        """Real-time FPS validation while typing."""
        fps_str = self.fps_var.get().strip()
        if fps_str and SETTINGS_AVAILABLE:
            is_valid, _ = validate_fps(fps_str)
            if not is_valid:
                self.fps_entry.config(foreground="red")
            else:
                self.fps_entry.config(foreground="black")
        else:
            self.fps_entry.config(foreground="black")
    
    def _validate_color_component(self, component: str):
        """Validate individual color component."""
        try:
            value = int(self.bg_color_vars[component].get())
            if 0 <= value <= 255:
                self.color_validation_label.grid_remove()
                getattr(self, f'{component}_entry').config(foreground="black")
            else:
                self._show_color_error("RGB values must be 0-255")
                getattr(self, f'{component}_entry').config(foreground="red")
        except ValueError:
            if self.bg_color_vars[component].get().strip():  # Only show error if not empty
                self._show_color_error("RGB values must be numbers")
                getattr(self, f'{component}_entry').config(foreground="red")
            else:
                getattr(self, f'{component}_entry').config(foreground="black")
    
    def _show_color_error(self, message: str):
        """Show color validation error."""
        self.color_validation_label.config(text=message)
        self.color_validation_label.grid(row=1, column=0, columnspan=6, pady=(2, 0))
    
    def _set_preset_color(self, callback, r, g, b):
        """Set preset color and validate."""
        callback(r, g, b)
        # Clear any validation errors
        self.color_validation_label.grid_remove()
        for component in ['r', 'g', 'b']:
            getattr(self, f'{component}_entry').config(foreground="black")
    
    def validate_all_inputs(self) -> tuple[bool, str]:
        """Validate all inputs in the video options frame.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Validate FPS
        if SETTINGS_AVAILABLE:
            is_valid, _ = validate_fps(self.fps_var.get())
            if not is_valid and self.fps_var.get().strip():
                return False, "Invalid FPS value"
        
        # Validate RGB colors
        if SETTINGS_AVAILABLE:
            try:
                r, g, b = validate_rgb_color(
                    self.bg_color_vars['r'].get(),
                    self.bg_color_vars['g'].get(),
                    self.bg_color_vars['b'].get()
                )
                # Update with validated values
                self.bg_color_vars['r'].set(str(r))
                self.bg_color_vars['g'].set(str(g))
                self.bg_color_vars['b'].set(str(b))
            except Exception:
                return False, "Invalid RGB color values"
        
        return True, ""
    
    def grid(self, **kwargs):
        """Grid the frame."""
        try:
            if hasattr(self, 'frame'):
                self.frame.grid(**kwargs)
        except tk.TclError:
            pass
    
    def grid_remove(self):
        """Remove the frame from grid."""
        try:
            if hasattr(self, 'frame'):
                self.frame.grid_remove()
        except tk.TclError:
            pass


class ControlFrame:
    """Frame for control buttons and progress."""
    
    def __init__(self, parent, process_callback: Callable, stop_callback: Callable, 
                 clear_log_callback: Callable):
        self._processing_state = False
        self.setup_ui(parent, process_callback, stop_callback, clear_log_callback)
    
    def setup_ui(self, parent, process_callback, stop_callback, clear_log_callback):
        """Setup the control UI."""
        try:
            self.parent = parent
            
            # Control buttons
            button_frame = ttk.Frame(parent)
            button_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
            
            self.process_btn = ttk.Button(button_frame, text="Process", command=process_callback)
            self.process_btn.pack(side=tk.LEFT, padx=(0, 10))
            
            self.stop_btn = ttk.Button(button_frame, text="Stop", command=stop_callback, state="disabled")
            self.stop_btn.pack(side=tk.LEFT, padx=(0, 10))
            
            ttk.Button(button_frame, text="Clear Log", command=clear_log_callback).pack(side=tk.LEFT)
            
            # Progress bar
            self.progress = ttk.Progressbar(parent, mode='determinate')
            self.progress.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
            
            # Status label
            self.status_var = tk.StringVar(value="Ready")
            self.status_label = ttk.Label(parent, textvariable=self.status_var)
            self.status_label.grid(row=2, column=0, pady=(0, 5))
        except tk.TclError as e:
            print(f"Error creating ControlFrame: {e}")
    
    def grid(self, **kwargs):
        """Grid the control frame."""
        # The control frame components are already gridded within their parent
        pass
    
    def set_processing_state(self, processing: bool):
        """Set the processing state of buttons with thread safety."""
        self._processing_state = processing
        
        def update_buttons():
            try:
                if hasattr(self, 'process_btn') and self.process_btn.winfo_exists():
                    if processing:
                        self.process_btn.configure(state="disabled")
                    else:
                        self.process_btn.configure(state="normal")
                
                if hasattr(self, 'stop_btn') and self.stop_btn.winfo_exists():
                    if processing:
                        self.stop_btn.configure(state="normal")
                    else:
                        self.stop_btn.configure(state="disabled")
            except tk.TclError:
                pass
        
        # Ensure this runs on the main thread
        if hasattr(self, 'parent'):
            try:
                self.parent.after(0, update_buttons)
            except tk.TclError:
                # Fallback to direct call if after() fails
                update_buttons()
    
    def update_progress(self, value: float):
        """Update progress bar value with thread safety."""
        def update_progress_bar():
            try:
                if hasattr(self, 'progress') and self.progress.winfo_exists():
                    self.progress['value'] = max(0, min(100, value))
            except tk.TclError:
                pass
        
        if hasattr(self, 'parent'):
            try:
                self.parent.after(0, update_progress_bar)
            except tk.TclError:
                update_progress_bar()
    
    def update_status(self, status: str):
        """Update status text with thread safety."""
        def update_status_label():
            try:
                if hasattr(self, 'status_var'):
                    self.status_var.set(status)
            except tk.TclError:
                pass
        
        if hasattr(self, 'parent'):
            try:
                self.parent.after(0, update_status_label)
            except tk.TclError:
                update_status_label()
    
    def get_processing_state(self) -> bool:
        """Get current processing state."""
        return self._processing_state


class LogFrame:
    """Frame for logging output."""
    
    def __init__(self, parent, height: int = 5):
        self.setup_ui(parent, height)
    
    def setup_ui(self, parent, height):
        """Setup the log UI."""
        try:
            self.frame = ttk.LabelFrame(parent, text="Processing Log", padding="5")
            self.frame.columnconfigure(0, weight=1)
            self.frame.rowconfigure(0, weight=1)
            
            self.log_text = scrolledtext.ScrolledText(self.frame, height=height, state="disabled")
            self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        except tk.TclError as e:
            print(f"Error creating LogFrame: {e}")
    
    def add_message(self, message: str):
        """Add a message to the log with thread safety."""
        def add_log_message():
            try:
                if hasattr(self, 'log_text') and self.log_text.winfo_exists():
                    self.log_text.configure(state="normal")
                    self.log_text.insert(tk.END, f"{message}\n")
                    self.log_text.configure(state="disabled")
                    self.log_text.see(tk.END)
            except tk.TclError:
                # Widget might be destroyed
                pass
        
        # Try to schedule on main thread, fallback to direct call
        try:
            if hasattr(self, 'frame'):
                self.frame.after(0, add_log_message)
            else:
                add_log_message()
        except tk.TclError:
            add_log_message()
    
    def clear(self):
        """Clear the log with thread safety."""
        def clear_log():
            try:
                if hasattr(self, 'log_text') and self.log_text.winfo_exists():
                    self.log_text.configure(state="normal")
                    self.log_text.delete(1.0, tk.END)
                    self.log_text.configure(state="disabled")
            except tk.TclError:
                pass
        
        try:
            if hasattr(self, 'frame'):
                self.frame.after(0, clear_log)
            else:
                clear_log()
        except tk.TclError:
            clear_log()
    
    def grid(self, **kwargs):
        """Grid the frame."""
        try:
            if hasattr(self, 'frame'):
                self.frame.grid(**kwargs)
        except tk.TclError:
            pass
