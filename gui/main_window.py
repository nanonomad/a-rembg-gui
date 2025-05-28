"""Main GUI window for the rembg application."""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import tempfile
import atexit
from pathlib import Path
from typing import Optional, Dict, Any
import weakref

try:
    from config.models import MODELS, DEFAULT_MODEL
    MODELS_AVAILABLE = True
except ImportError:
    MODELS_AVAILABLE = False
    MODELS = {"u2net": {"description": "General use (default)", "files": []}}
    DEFAULT_MODEL = "u2net"

try:
    from config.settings import (
        WINDOW_TITLE, WINDOW_SIZE, WINDOW_MIN_SIZE, 
        DEFAULT_FILENAME_FORMAT, DEFAULT_BG_COLOR,
        IMAGE_FILE_TYPES, VIDEO_FILE_TYPES,
        ensure_output_directory, validate_rgb_color, validate_fps,
        MAX_IMAGE_SIZE_MB, MAX_VIDEO_SIZE_MB
    )
    SETTINGS_AVAILABLE = True
except ImportError:
    SETTINGS_AVAILABLE = False
    WINDOW_TITLE = "rembg Background Remover"
    WINDOW_SIZE = "1000x850"
    WINDOW_MIN_SIZE = (800, 700)
    DEFAULT_FILENAME_FORMAT = "{name}_no_bg.png"
    DEFAULT_BG_COLOR = (0, 255, 0)
    IMAGE_FILE_TYPES = [("Image files", "*.png *.jpg *.jpeg"), ("All files", "*.*")]
    VIDEO_FILE_TYPES = [("Video files", "*.mp4 *.avi *.mov"), ("All files", "*.*")]
    MAX_IMAGE_SIZE_MB = 500
    MAX_VIDEO_SIZE_MB = 2000

try:
    from core.processor import ImageProcessor
    from core.session_manager import SessionManager
    from core.video_handler import VideoHandler
    CORE_AVAILABLE = True
except ImportError:
    CORE_AVAILABLE = False

try:
    from gui.components import (
        InputSelectionFrame, ProcessingOptionsFrame, VideoOptionsFrame,
        ControlFrame, LogFrame
    )
    COMPONENTS_AVAILABLE = True
except ImportError:
    COMPONENTS_AVAILABLE = False

try:
    from gui.preview_canvas import PreviewCanvas
    PREVIEW_AVAILABLE = True
except ImportError:
    PREVIEW_AVAILABLE = False

try:
    from utils.logging_utils import Logger
    from utils.system_utils import check_gpu_availability, get_system_info, check_available_memory_for_file
    from utils.file_utils import generate_output_filename, validate_file_size, safe_remove_directory
    UTILS_AVAILABLE = True
except ImportError:
    UTILS_AVAILABLE = False


class ProcessingState:
    """Thread-safe processing state management."""
    
    def __init__(self):
        self._lock = threading.Lock()
        self._processing = False
        self._should_stop = False
    
    def start_processing(self) -> bool:
        """Start processing if not already running."""
        with self._lock:
            if self._processing:
                return False
            self._processing = True
            self._should_stop = False
            return True
    
    def stop_processing(self):
        """Signal that processing should stop."""
        with self._lock:
            self._should_stop = True
    
    def finish_processing(self):
        """Mark processing as finished."""
        with self._lock:
            self._processing = False
            self._should_stop = False
    
    def is_processing(self) -> bool:
        """Check if currently processing."""
        with self._lock:
            return self._processing
    
    def should_stop(self) -> bool:
        """Check if processing should stop."""
        with self._lock:
            return self._should_stop


class MainWindow:
    """Main application window."""
    
    def __init__(self):
        self.setup_core_components()
        self.setup_window()
        self.setup_variables()
        self.setup_ui()
        self.initialize_application()
        self.setup_cleanup()
    
    def setup_core_components(self):
        """Initialize core components."""
        if UTILS_AVAILABLE:
            self.logger = Logger(debug_mode=True)
        else:
            self.logger = None
        
        self.processing_state = ProcessingState()
        self.temp_directories = []  # Track temp directories for cleanup
        
        if CORE_AVAILABLE and UTILS_AVAILABLE:
            self.session_manager = SessionManager(self.logger)
            self.image_processor = ImageProcessor(self.session_manager, self.logger)
            self.video_handler = VideoHandler(self.image_processor, self.logger)
        else:
            self.session_manager = None
            self.image_processor = None
            self.video_handler = None
        
        # State variables
        self.gpu_available = False
        self.use_gpu = False
    
    def setup_window(self):
        """Setup the main window."""
        self.root = tk.Tk()
        self.root.title(WINDOW_TITLE)
        self.root.geometry(WINDOW_SIZE)
        self.root.minsize(*WINDOW_MIN_SIZE)
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_window_close)
    
    def setup_variables(self):
        """Setup tkinter variables."""
        # Input/Output variables
        self.input_type = tk.StringVar(value="image")
        self.input_path = tk.StringVar()
        self.output_path = tk.StringVar()
        self.filename_format = tk.StringVar(value=DEFAULT_FILENAME_FORMAT)
        
        # Model variables
        self.selected_model = tk.StringVar(value=DEFAULT_MODEL)
        if MODELS_AVAILABLE and DEFAULT_MODEL in MODELS:
            self.model_desc = tk.StringVar(value=MODELS[DEFAULT_MODEL]["description"])
        else:
            self.model_desc = tk.StringVar(value="General use (default)")
        self.gpu_status = tk.StringVar(value="Checking GPU...")
        
        # Processing options
        self.only_mask = tk.BooleanVar()
        self.alpha_matting = tk.BooleanVar()
        self.extra_params = tk.StringVar()
        
        # Video options
        self.fps_var = tk.StringVar(value="")
        self.reassemble_video = tk.BooleanVar(value=True)
        self.bg_color_vars = {
            'r': tk.StringVar(value=str(DEFAULT_BG_COLOR[0])),
            'g': tk.StringVar(value=str(DEFAULT_BG_COLOR[1])),
            'b': tk.StringVar(value=str(DEFAULT_BG_COLOR[2]))
        }
    
    def setup_ui(self):
        """Setup the user interface."""
        try:
            # Main container
            main_frame = ttk.Frame(self.root, padding="10")
            main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
            main_frame.columnconfigure(1, weight=1)
            main_frame.rowconfigure(5, weight=4)  # Image preview gets most space
            main_frame.rowconfigure(9, weight=1)  # Log gets minimal space
            
            # Title
            title_label = ttk.Label(main_frame, text=WINDOW_TITLE, font=("Arial", 16, "bold"))
            title_label.grid(row=0, column=0, columnspan=3, pady=(0, 15))
            
            # Input selection frame
            if COMPONENTS_AVAILABLE:
                self.input_frame = InputSelectionFrame(
                    main_frame, self.input_type, self.input_path, self.output_path, 
                    self.filename_format, self.browse_input, self.browse_output,
                    self.on_input_type_change
                )
                self.input_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 8))
            
            # Processing options frame
            if COMPONENTS_AVAILABLE:
                self.options_frame = ProcessingOptionsFrame(
                    main_frame, self.selected_model, self.model_desc, None,
                    self.gpu_status, self.only_mask, self.alpha_matting, self.extra_params,
                    self.on_model_change
                )
                self.options_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 8))
            
            # Video options frame (initially hidden)
            if COMPONENTS_AVAILABLE:
                self.video_frame = VideoOptionsFrame(
                    main_frame, self.fps_var, self.reassemble_video, self.bg_color_vars,
                    self.set_bg_color
                )
            
            # Control frame (moved above preview images)
            control_container = ttk.Frame(main_frame)
            control_container.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 8))
            control_container.columnconfigure(0, weight=1)
            
            if COMPONENTS_AVAILABLE:
                self.control_frame = ControlFrame(
                    control_container, self.start_processing, self.stop_processing, self.clear_log
                )
            
            # Image preview frame
            preview_frame = ttk.LabelFrame(main_frame, text="Image Preview", padding="10")
            preview_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(8, 8))
            preview_frame.columnconfigure(0, weight=1)
            preview_frame.columnconfigure(1, weight=1)
            preview_frame.rowconfigure(0, weight=1)
            
            # Input and output preview canvases
            if PREVIEW_AVAILABLE:
                self.input_preview = PreviewCanvas(preview_frame, "Input Image", self.logger)
                self.input_preview.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
                
                self.output_preview = PreviewCanvas(preview_frame, "Output Result", self.logger)
                self.output_preview.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(10, 0))
                self.output_preview.set_default_message("Processing not started")
            else:
                self.input_preview = None
                self.output_preview = None
            
            # Log frame
            if COMPONENTS_AVAILABLE:
                self.log_frame = LogFrame(main_frame, height=5)
                self.log_frame.grid(row=9, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
                
                # Set up logger GUI callback
                if self.logger and hasattr(self.logger, 'set_gui_callback'):
                    self.logger.set_gui_callback(self.safe_log_output)
            else:
                self.log_frame = None
                
        except Exception as e:
            print(f"Error setting up UI: {e}")
            messagebox.showerror("UI Error", f"Failed to create user interface: {e}")
    
    def setup_cleanup(self):
        """Setup cleanup procedures."""
        def cleanup():
            """Cleanup function for application exit."""
            try:
                # Stop any ongoing processing
                if hasattr(self, 'processing_state'):
                    self.processing_state.stop_processing()
                
                # Cleanup temp directories
                for temp_dir in getattr(self, 'temp_directories', []):
                    if UTILS_AVAILABLE:
                        safe_remove_directory(temp_dir)
                
                # Cleanup session
                if hasattr(self, 'session_manager') and self.session_manager:
                    self.session_manager.destroy_session()
                
                # Cleanup preview canvases
                if hasattr(self, 'input_preview') and self.input_preview:
                    self.input_preview.cleanup_image_references()
                if hasattr(self, 'output_preview') and self.output_preview:
                    self.output_preview.cleanup_image_references()
                    
            except Exception as e:
                print(f"Error during cleanup: {e}")
        
        atexit.register(cleanup)
    
    def initialize_application(self):
        """Initialize the application."""
        if self.logger:
            self.logger.info("=== rembg GUI Debug Mode ===")
            
            # Log system info
            if UTILS_AVAILABLE:
                system_info = get_system_info()
                self.logger.debug(f"Python version: {system_info['python_version']}")
                self.logger.debug(f"Platform: {system_info['platform']}")
                self.logger.debug(f"Available memory: {system_info['available_memory_gb']:.2f} GB")
        
        # Check dependencies and GPU
        self.check_dependencies()
        self.check_gpu_availability()
    
    def check_dependencies(self):
        """Check if required dependencies are available."""
        try:
            missing_deps = []
            
            if not CORE_AVAILABLE:
                missing_deps.append("Core processing modules")
            if not COMPONENTS_AVAILABLE:
                missing_deps.append("GUI components")
            if not UTILS_AVAILABLE:
                missing_deps.append("Utility modules")
            
            # Check individual dependencies
            try:
                import rembg
                if self.logger:
                    self.logger.debug(f"rembg version: {rembg.__version__}")
            except ImportError:
                missing_deps.append("rembg")
            
            try:
                import PIL
                if self.logger:
                    self.logger.debug(f"PIL version: {PIL.__version__}")
            except ImportError:
                missing_deps.append("Pillow")
            
            try:
                import cv2
                if self.logger:
                    self.logger.debug(f"OpenCV version: {cv2.__version__}")
            except ImportError:
                missing_deps.append("opencv-python")
            
            try:
                import onnxruntime as ort
                if self.logger:
                    self.logger.debug(f"onnxruntime version: {ort.__version__}")
            except ImportError:
                missing_deps.append("onnxruntime")
            
            if missing_deps:
                error_msg = f"Missing dependencies:\n" + "\n".join(f"- {dep}" for dep in missing_deps)
                error_msg += "\n\nPlease install with:\npip install \"rembg[gpu,cli]\" pillow opencv-python"
                messagebox.showerror("Missing Dependencies", error_msg)
                
        except Exception as e:
            if self.logger:
                self.logger.error("Error checking dependencies", e)
    
    def check_gpu_availability(self):
        """Check if GPU acceleration is available."""
        if self.logger:
            self.logger.debug("=== GPU Availability Check ===")
        
        if not UTILS_AVAILABLE:
            self.gpu_status.set("💻 CPU Only")
            return
        
        try:
            gpu_info = check_gpu_availability()
            if self.logger:
                self.logger.debug(f"Available ONNX providers: {gpu_info['providers']}")
            
            if gpu_info['cuda_available']:
                self.use_gpu = True
                self.gpu_available = True
                self.gpu_status.set("🚀 GPU (CUDA)")
                if self.logger:
                    self.logger.info("✓ GPU (CUDA) acceleration available and enabled")
            elif gpu_info['rocm_available']:
                self.use_gpu = True
                self.gpu_available = True
                self.gpu_status.set("🚀 GPU (ROCM)")
                if self.logger:
                    self.logger.info("✓ ROCM GPU acceleration available")
            else:
                self.use_gpu = False
                self.gpu_available = False
                self.gpu_status.set("💻 CPU Only")
                if self.logger:
                    self.logger.info("! GPU acceleration not available, using CPU")
        except Exception as e:
            self.use_gpu = False
            self.gpu_available = False
            self.gpu_status.set("💻 CPU Only")
            if self.logger:
                self.logger.error("Error checking GPU availability", e)
    
    def on_input_type_change(self):
        """Handle input type radio button changes."""
        try:
            if self.input_type.get() == "video" and hasattr(self, 'video_frame'):
                self.video_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 8))
            elif hasattr(self, 'video_frame'):
                self.video_frame.grid_remove()
            
            # Show/hide filename format for single images
            if self.input_type.get() == "image" and hasattr(self, 'input_frame'):
                self.input_frame.show_format_frame()
            elif hasattr(self, 'input_frame'):
                self.input_frame.hide_format_frame()
            
            # Clear current paths and previews
            self.input_path.set("")
            self.output_path.set("")
            self.clear_previews()
        except Exception as e:
            if self.logger:
                self.logger.debug(f"Error in input type change: {e}")
    
    def on_model_change(self, event=None):
        """Update model description and information when model is changed."""
        try:
            model = self.selected_model.get()
            if MODELS_AVAILABLE and model in MODELS:
                model_info = MODELS.get(model, {})
                self.model_desc.set(model_info.get("description", ""))
                
                # Update the detailed model information in the options frame
                if hasattr(self, 'options_frame') and hasattr(self.options_frame, 'update_model_info'):
                    self.options_frame.update_model_info(model)
        except Exception as e:
            if self.logger:
                self.logger.debug(f"Error in model change: {e}")
    
    def set_bg_color(self, r: int, g: int, b: int):
        """Set background color preset."""
        try:
            self.bg_color_vars['r'].set(str(r))
            self.bg_color_vars['g'].set(str(g))
            self.bg_color_vars['b'].set(str(b))
        except Exception as e:
            if self.logger:
                self.logger.debug(f"Error setting background color: {e}")
    
    def validate_file_before_processing(self, file_path: str) -> tuple[bool, str]:
        """Validate file before processing."""
        if not UTILS_AVAILABLE:
            return True, ""
        
        try:
            # Check file size
            is_video = self.input_type.get() == "video"
            size_valid, size_msg = validate_file_size(file_path, is_video)
            if not size_valid:
                return False, size_msg
            
            # Check available memory
            if not check_available_memory_for_file(file_path):
                file_size_mb = Path(file_path).stat().st_size / (1024**2)
                return False, f"Insufficient memory for file ({file_size_mb:.1f}MB). Close other applications and try again."
            
            return True, ""
            
        except Exception as e:
            return False, f"Error validating file: {e}"
    
    def browse_input(self):
        """Browse for input file or directory."""
        try:
            input_type = self.input_type.get()
            
            if input_type == "image":
                filename = filedialog.askopenfilename(
                    title="Select Image File",
                    filetypes=IMAGE_FILE_TYPES
                )
                if filename:
                    # Validate file before setting
                    is_valid, error_msg = self.validate_file_before_processing(filename)
                    if not is_valid:
                        messagebox.showerror("File Validation Error", error_msg)
                        return
                    
                    self.input_path.set(filename)
                    path = Path(filename)
                    self.output_path.set(str(path.parent))
                    if self.input_preview:
                        self.input_preview.update_image(filename)
                    if self.output_preview:
                        self.output_preview.set_default_message("Processing not started")
            
            elif input_type == "directory":
                dirname = filedialog.askdirectory(title="Select Image Directory")
                if dirname:
                    self.input_path.set(dirname)
                    path = Path(dirname)
                    output_dir = f"{path.name}_no_bg"
                    self.output_path.set(str(path.parent / output_dir))
                    self.clear_previews()
            
            elif input_type == "video":
                filename = filedialog.askopenfilename(
                    title="Select Video File",
                    filetypes=VIDEO_FILE_TYPES
                )
                if filename:
                    # Validate file before setting
                    is_valid, error_msg = self.validate_file_before_processing(filename)
                    if not is_valid:
                        messagebox.showerror("File Validation Error", error_msg)
                        return
                    
                    self.input_path.set(filename)
                    path = Path(filename)
                    output_dir = f"{path.stem}_frames_no_bg"
                    self.output_path.set(str(path.parent / output_dir))
                    self.clear_previews()
                    
        except Exception as e:
            if self.logger:
                self.logger.error("Error browsing input", e)
            messagebox.showerror("Browse Error", f"Error selecting input: {e}")
    
    def browse_output(self):
        """Browse for output location."""
        try:
            dirname = filedialog.askdirectory(title="Select Output Directory")
            if dirname:
                # Check if directory is writable
                if SETTINGS_AVAILABLE and not ensure_output_directory(dirname):
                    messagebox.showerror("Permission Error", 
                                       f"Cannot write to directory: {dirname}\nPlease select a different location.")
                    return
                
                self.output_path.set(dirname)
        except Exception as e:
            if self.logger:
                self.logger.error("Error browsing output", e)
            messagebox.showerror("Browse Error", f"Error selecting output directory: {e}")
    
    def clear_previews(self):
        """Clear both image previews."""
        try:
            if self.input_preview:
                self.input_preview.clear()
            if self.output_preview:
                self.output_preview.set_default_message("Processing not started")
        except Exception as e:
            if self.logger:
                self.logger.debug(f"Error clearing previews: {e}")
    
    def safe_log_output(self, message: str):
        """Thread-safe log output."""
        def log_message():
            try:
                if hasattr(self, 'log_frame') and self.log_frame:
                    self.log_frame.add_message(message)
            except Exception as e:
                print(f"Error logging message: {e}")
        
        try:
            self.root.after(0, log_message)
        except tk.TclError:
            # GUI might be closing
            print(message)
    
    def clear_log(self):
        """Clear the log output."""
        try:
            if hasattr(self, 'log_frame') and self.log_frame:
                self.log_frame.clear()
        except Exception as e:
            if self.logger:
                self.logger.debug(f"Error clearing log: {e}")
    
    def safe_update_progress(self, current: int, total: int, status: str = ""):
        """Thread-safe progress update."""
        def update_gui():
            try:
                if hasattr(self, 'control_frame') and self.control_frame:
                    if total > 0:
                        progress_value = (current / total) * 100
                        self.control_frame.update_progress(progress_value)
                    
                    if status:
                        self.control_frame.update_status(status)
                    else:
                        self.control_frame.update_status(f"Processing {current}/{total}")
            except Exception as e:
                if self.logger:
                    self.logger.debug(f"Error updating progress: {e}")
        
        try:
            self.root.after(0, update_gui)
        except tk.TclError:
            pass
    
    def safe_update_progress_with_preview(self, current: int, total: int, status: str = "", 
                                         input_file: str = None, output_file: str = None):
        """Thread-safe progress update with preview support for directory processing."""
        def update_gui():
            try:
                # Update progress bar and status
                if hasattr(self, 'control_frame') and self.control_frame:
                    if total > 0:
                        progress_value = (current / total) * 100
                        self.control_frame.update_progress(progress_value)
                    
                    if status:
                        self.control_frame.update_status(status)
                    else:
                        self.control_frame.update_status(f"Processing {current}/{total}")
                
                # Update input preview if file is provided
                if input_file and self.input_preview:
                    self.input_preview.update_image(input_file)
                
                # Update output preview based on output file availability
                if self.output_preview:
                    if output_file and Path(output_file).exists():
                        self.output_preview.update_image(output_file)
                    elif "Failed" in status:
                        self.output_preview.set_error_message("Processing failed")
                    elif "Processing" in status:
                        self.output_preview.set_default_message("Processing...")
                    elif "Completed" in status and not output_file:
                        self.output_preview.set_error_message("Output file not found")
                        
            except Exception as e:
                if self.logger:
                    self.logger.debug(f"Error updating progress with preview: {e}")
        
        try:
            self.root.after(0, update_gui)
        except tk.TclError:
            pass
    
    def safe_update_preview(self, input_file: str, output_file: str = None):
        """Thread-safe preview update."""
        def update_gui():
            try:
                # Update input preview
                if self.input_preview:
                    self.input_preview.update_image(input_file)
                
                # Update output preview if available
                if self.output_preview:
                    if output_file and Path(output_file).exists():
                        self.output_preview.update_image(output_file)
                    else:
                        self.output_preview.set_default_message("Processing...")
            except Exception as e:
                if self.logger:
                    self.logger.debug(f"Error updating preview: {e}")
        
        try:
            self.root.after(0, update_gui)
        except tk.TclError:
            pass
    
    def get_validated_inputs(self) -> tuple[bool, str, dict]:
        """Get and validate all user inputs.
        
        Returns:
            Tuple of (is_valid, error_message, validated_inputs)
        """
        try:
            # Basic path validation
            input_path = self.input_path.get()
            output_path = self.output_path.get()
            
            if not input_path or not output_path:
                return False, "Please select input and output paths", {}
            
            # Video options validation
            if self.input_type.get() == "video" and hasattr(self, 'video_frame'):
                is_valid, error_msg = self.video_frame.validate_all_inputs()
                if not is_valid:
                    return False, error_msg, {}
            
            # Get validated FPS
            fps = None
            if SETTINGS_AVAILABLE:
                is_valid, fps = validate_fps(self.fps_var.get())
                if not is_valid and self.fps_var.get().strip():
                    return False, "Invalid FPS value", {}
            
            # Get validated RGB colors
            bg_color = DEFAULT_BG_COLOR
            if SETTINGS_AVAILABLE:
                bg_color = validate_rgb_color(
                    self.bg_color_vars['r'].get(),
                    self.bg_color_vars['g'].get(),
                    self.bg_color_vars['b'].get()
                )
            
            return True, "", {
                'input_path': input_path,
                'output_path': output_path,
                'fps': fps,
                'bg_color': bg_color,
                'model': self.selected_model.get(),
                'only_mask': self.only_mask.get(),
                'alpha_matting': self.alpha_matting.get(),
                'extra_params': self.extra_params.get(),
                'reassemble_video': self.reassemble_video.get(),
                'filename_format': self.filename_format.get()
            }
            
        except Exception as e:
            return False, f"Error validating inputs: {e}", {}
    
    def create_temp_directory(self) -> str:
        """Create and track a temporary directory."""
        try:
            temp_dir = tempfile.mkdtemp(prefix="rembg_video_")
            self.temp_directories.append(temp_dir)
            return temp_dir
        except Exception as e:
            if self.logger:
                self.logger.error("Error creating temp directory", e)
            raise
    
    def processing_thread(self):
        """Main processing thread with comprehensive error handling."""
        temp_dir = None
        
        try:
            if self.logger:
                self.logger.debug("=== Processing Thread Started ===")
            
            # Get validated inputs
            is_valid, error_msg, inputs = self.get_validated_inputs()
            if not is_valid:
                self.root.after(0, lambda: messagebox.showerror("Input Error", error_msg))
                return
            
            # Create session
            if not self.session_manager or not self.session_manager.create_session(inputs['model'], self.use_gpu):
                self.root.after(0, lambda: messagebox.showerror("Error", "Failed to create processing session"))
                return
            
            if self.logger:
                self.logger.info(f"Starting processing with model: {inputs['model']}")
                acceleration = "GPU" if self.use_gpu else "CPU"
                self.logger.info(f"Using {acceleration} acceleration")
            
            input_type = self.input_type.get()
            
            if input_type == "image":
                self.safe_update_progress(0, 1, "Processing image...")
                output_file = generate_output_filename(
                    inputs['input_path'], inputs['output_path'], inputs['filename_format']
                ) if UTILS_AVAILABLE else str(Path(inputs['output_path']) / "output.png")
                
                success = self.image_processor.process_single_image(
                    inputs['input_path'], output_file,
                    inputs['only_mask'], inputs['alpha_matting'],
                    inputs['extra_params'], self.safe_update_progress
                )
                
                if success and self.output_preview:
                    self.root.after(100, lambda: self.safe_update_preview(inputs['input_path'], output_file))
                
                self.safe_update_progress(1, 1, "Complete" if success else "Failed")
            
            elif input_type == "directory":
                # Create a custom progress callback that handles the enhanced parameters
                def directory_progress_callback(current, total, status, input_file=None, output_file=None):
                    if not self.processing_state.should_stop():
                        # Use the enhanced progress callback for directory processing
                        self.safe_update_progress_with_preview(current, total, status, input_file, output_file)
                
                result = self.image_processor.process_directory(
                    inputs['input_path'], inputs['output_path'],
                    inputs['only_mask'], inputs['alpha_matting'],
                    inputs['extra_params'], directory_progress_callback
                )
                
                if self.logger:
                    self.logger.info(f"Directory processing complete: {result['successful']}/{result['total']} files")
            
            elif input_type == "video":
                temp_dir = self.create_temp_directory()
                if self.logger:
                    self.logger.info(f"Extracting video frames to: {temp_dir}")
                
                # Extract frames
                frame_files = self.video_handler.extract_video_frames(
                    inputs['input_path'], temp_dir, inputs['fps'], self.safe_update_progress
                )
                
                if frame_files and self.processing_state.is_processing():
                    processed_frames_dir = Path(inputs['output_path']) / "processed_frames"
                    processed_frames_dir.mkdir(parents=True, exist_ok=True)
                    
                    # Process frames with preview updates
                    def progress_callback_with_preview(current, total, status):
                        if not self.processing_state.should_stop():
                            self.safe_update_progress(current, total, status)
                            
                            # Update previews during processing
                            if current > 0 and current <= len(frame_files):
                                input_frame = frame_files[current - 1]
                                frame_name = Path(input_frame).name
                                output_frame_name = frame_name.replace('.png', '_no_bg.png')
                                output_frame = processed_frames_dir / output_frame_name
                                
                                self.safe_update_preview(
                                    input_frame, 
                                    str(output_frame) if output_frame.exists() else None
                                )
                    
                    # Set the image processor to use our processing state
                    if self.image_processor:
                        original_is_processing = self.image_processor.is_processing
                        self.image_processor.is_processing = lambda: self.processing_state.is_processing() and not self.processing_state.should_stop()
                    
                    result = self.image_processor.process_directory(
                        temp_dir, str(processed_frames_dir),
                        inputs['only_mask'], inputs['alpha_matting'],
                        inputs['extra_params'], progress_callback_with_preview
                    )
                    
                    # Restore original is_processing method
                    if self.image_processor:
                        self.image_processor.is_processing = original_is_processing
                    
                    # Reassemble video if requested
                    if (inputs['reassemble_video'] and result.get("processed_frames") and 
                        self.processing_state.is_processing() and not self.processing_state.should_stop()):
                        
                        output_video_path = self.video_handler.generate_video_output_filename(
                            inputs['input_path'], inputs['output_path']
                        )
                        
                        if self.video_handler.reassemble_video_from_frames(
                            str(processed_frames_dir), output_video_path, 
                            inputs['bg_color'], inputs['fps'], 
                            progress_callback=self.safe_update_progress
                        ):
                            if self.logger:
                                self.logger.info("✓ Video processing complete!")
        
        except Exception as e:
            if self.logger:
                self.logger.error("Processing thread error", e)
            self.root.after(0, lambda: messagebox.showerror("Processing Error", str(e)))
        
        finally:
            # Cleanup
            try:
                if self.session_manager:
                    self.session_manager.destroy_session()
                
                if temp_dir and UTILS_AVAILABLE:
                    safe_remove_directory(temp_dir)
                    if temp_dir in self.temp_directories:
                        self.temp_directories.remove(temp_dir)
                
            except Exception as e:
                if self.logger:
                    self.logger.debug(f"Error in cleanup: {e}")
            
            # Reset GUI state
            self.processing_state.finish_processing()
            
            def reset_gui():
                try:
                    if hasattr(self, 'control_frame') and self.control_frame:
                        self.control_frame.set_processing_state(False)
                        self.control_frame.update_progress(0)
                        self.control_frame.update_status("Ready")
                except Exception as e:
                    if self.logger:
                        self.logger.debug(f"Error resetting GUI: {e}")
            
            try:
                self.root.after(0, reset_gui)
            except tk.TclError:
                pass
    
    def start_processing(self):
        """Start the processing in a separate thread."""
        if not self.processing_state.start_processing():
            return  # Already processing
        
        if not CORE_AVAILABLE:
            messagebox.showerror("Error", "Core processing modules not available")
            self.processing_state.finish_processing()
            return
        
        try:
            if hasattr(self, 'control_frame') and self.control_frame:
                self.control_frame.set_processing_state(True)
            
            # Set image processor processing state
            if self.image_processor:
                self.image_processor.set_processing(True)
            
            thread = threading.Thread(target=self.processing_thread, daemon=True)
            thread.start()
            
        except Exception as e:
            if self.logger:
                self.logger.error("Error starting processing", e)
            messagebox.showerror("Error", f"Failed to start processing: {e}")
            self.processing_state.finish_processing()
    
    def stop_processing(self):
        """Stop the current processing."""
        self.processing_state.stop_processing()
        
        if self.image_processor:
            self.image_processor.set_processing(False)
        
        if self.logger:
            self.logger.info("Stopping processing...")
    
    def on_window_close(self):
        """Handle window close event."""
        try:
            # Stop processing
            self.processing_state.stop_processing()
            
            # Cleanup
            for temp_dir in self.temp_directories:
                if UTILS_AVAILABLE:
                    safe_remove_directory(temp_dir)
            
            # Destroy window
            self.root.destroy()
            
        except Exception as e:
            print(f"Error during window close: {e}")
            self.root.destroy()
    
    def run(self):
        """Start the GUI application."""
        try:
            self.root.mainloop()
        except Exception as e:
            print(f"Error running application: {e}")
            raise
