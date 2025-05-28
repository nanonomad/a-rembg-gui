"""Core image processing functionality."""

import json
import time
import threading
from pathlib import Path
from typing import Dict, Any, Optional, Callable

try:
    from rembg import remove
    from PIL import Image
    PROCESSING_AVAILABLE = True
except ImportError:
    PROCESSING_AVAILABLE = False

try:
    from core.session_manager import SessionManager
    SESSION_AVAILABLE = True
except ImportError:
    SESSION_AVAILABLE = False

try:
    from utils.logging_utils import Logger
    from utils.file_utils import ensure_directory_exists, get_file_size_mb
    from utils.system_utils import get_memory_usage, check_available_memory_for_file
    UTILS_AVAILABLE = True
except ImportError:
    UTILS_AVAILABLE = False


class ProcessingState:
    """Thread-safe processing state management for the image processor."""
    
    def __init__(self):
        self._lock = threading.Lock()
        self._processing = False
        self._should_stop = False
    
    def set_processing(self, processing: bool):
        """Set processing state."""
        with self._lock:
            self._processing = processing
            if not processing:
                self._should_stop = False
    
    def is_processing(self) -> bool:
        """Check if currently processing."""
        with self._lock:
            return self._processing and not self._should_stop
    
    def stop_processing(self):
        """Signal that processing should stop."""
        with self._lock:
            self._should_stop = True
    
    def should_stop(self) -> bool:
        """Check if processing should stop."""
        with self._lock:
            return self._should_stop


class ImageProcessor:
    """Handles image processing operations."""
    
    def __init__(self, session_manager=None, logger=None):
        self.session_manager = session_manager
        self.logger = logger
        self._state = ProcessingState()
    
    def process_single_image(
        self, 
        input_path: str, 
        output_path: str,
        only_mask: bool = False,
        alpha_matting: bool = False,
        extra_params: str = "",
        progress_callback: Optional[Callable] = None
    ) -> bool:
        """Process a single image."""
        if not PROCESSING_AVAILABLE:
            if self.logger:
                self.logger.error("Processing libraries not available")
            return False
        
        try:
            if self.logger:
                self.logger.debug(f"Starting single image processing: {input_path}")
            
            # Check if we should stop before starting
            if self._state.should_stop():
                return False
            
            # Validate file size and memory if utils available
            if UTILS_AVAILABLE:
                file_size = get_file_size_mb(input_path)
                if self.logger:
                    self.logger.debug(f"Input file size: {file_size:.2f} MB")
                
                # Check if we have enough memory
                if not check_available_memory_for_file(input_path):
                    if self.logger:
                        self.logger.error(f"Insufficient memory for processing {input_path}")
                    return False
                
                # Check memory before loading
                memory_before = get_memory_usage()
                if self.logger:
                    self.logger.debug(f"Memory before loading: {memory_before['available_gb']:.2f} GB available")
            
            # Load input data
            try:
                with open(input_path, 'rb') as f:
                    input_data = f.read()
            except (IOError, PermissionError) as e:
                if self.logger:
                    self.logger.error(f"Error reading input file {input_path}", e)
                return False
            
            if self.logger:
                self.logger.debug(f"Image data loaded, size: {len(input_data) / (1024**2):.2f} MB")
            
            # Check if we should stop after loading
            if self._state.should_stop():
                return False
            
            # Parse extra parameters
            extra_args = self._parse_extra_params(extra_params)
            
            # Ensure session is ready
            if not self.session_manager or not self.session_manager.is_session_ready():
                if self.logger:
                    self.logger.error("Session not ready for processing")
                return False
            
            # Process with rembg
            if self.logger:
                self.logger.debug("Starting image processing...")
            
            if UTILS_AVAILABLE:
                memory_pre_process = get_memory_usage()
            
            start_time = time.time()
            
            try:
                output_data = remove(
                    input_data,
                    session=self.session_manager.get_session(),
                    only_mask=only_mask,
                    alpha_matting=alpha_matting,
                    **extra_args
                )
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Error during image processing", e)
                return False
            
            process_time = time.time() - start_time
            
            if UTILS_AVAILABLE:
                memory_post_process = get_memory_usage()
                process_memory = memory_pre_process['available_gb'] - memory_post_process['available_gb']
                
                if self.logger:
                    self.logger.debug(f"Processing completed in {process_time:.2f} seconds")
                    self.logger.debug(f"Processing memory usage: {process_memory:.2f} GB")
                    self.logger.debug(f"Output data size: {len(output_data) / (1024**2):.2f} MB")
            
            # Check if we should stop before saving
            if self._state.should_stop():
                return False
            
            # Save output
            try:
                if UTILS_AVAILABLE:
                    ensure_directory_exists(str(Path(output_path).parent))
                else:
                    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
                
                with open(output_path, 'wb') as f:
                    f.write(output_data)
                
                if self.logger:
                    self.logger.debug(f"Output saved to: {output_path}")
                
            except (IOError, PermissionError) as e:
                if self.logger:
                    self.logger.error(f"Error saving output to {output_path}", e)
                return False
            
            if progress_callback:
                progress_callback(1, 1, "Complete")
            
            return True
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error processing {input_path}", e)
            return False
    
    def process_directory(
        self,
        input_dir: str,
        output_dir: str,
        only_mask: bool = False,
        alpha_matting: bool = False,
        extra_params: str = "",
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        # Import here to avoid circular imports
        if UTILS_AVAILABLE:
            try:
                from utils.file_utils import find_image_files
                FILE_UTILS_AVAILABLE = True
            except ImportError:
                FILE_UTILS_AVAILABLE = False
        else:
            FILE_UTILS_AVAILABLE = False
        
        # Find all image files
        if FILE_UTILS_AVAILABLE:
            image_files = find_image_files(input_dir)
        else:
            # Fallback file finding
            try:
                from config.settings import IMAGE_EXTENSIONS
            except ImportError:
                IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.webp'}
            
            image_files = []
            try:
                for file_path in Path(input_dir).rglob('*'):
                    if file_path.is_file() and file_path.suffix.lower() in IMAGE_EXTENSIONS:
                        image_files.append(file_path)
            except (PermissionError, OSError) as e:
                if self.logger:
                    self.logger.error(f"Error accessing directory {input_dir}", e)
                return {"total": 0, "successful": 0, "processed_frames": []}
        
        if not image_files:
            if self.logger:
                self.logger.info("No image files found in directory")
            return {"total": 0, "successful": 0, "processed_frames": []}
        
        if self.logger:
            self.logger.info(f"Found {len(image_files)} image files")
        
        # Ensure output directory exists
        if UTILS_AVAILABLE:
            if not ensure_directory_exists(output_dir):
                if self.logger:
                    self.logger.error(f"Cannot create output directory: {output_dir}")
                return {"total": len(image_files), "successful": 0, "processed_frames": []}
        else:
            try:
                Path(output_dir).mkdir(parents=True, exist_ok=True)
            except (PermissionError, OSError) as e:
                if self.logger:
                    self.logger.error(f"Cannot create output directory: {output_dir}", e)
                return {"total": len(image_files), "successful": 0, "processed_frames": []}
        
        successful = 0
        processed_frames = []
        
        for i, input_file in enumerate(image_files):
            if self._state.should_stop():  # Check if stopped
                break
            
            # Maintain directory structure
            try:
                rel_path = input_file.relative_to(input_dir)
                output_file = Path(output_dir) / rel_path
                output_file = output_file.with_stem(f"{output_file.stem}_no_bg")
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Error calculating output path for {input_file}", e)
                continue
            
            # progress callback with preview information - BEFORE processing
            if progress_callback:
                # Check if callback accepts extra parameters for preview
                try:
                    progress_callback(i, len(image_files), f"Processing: {input_file.name}", 
                                    str(input_file), None)
                except TypeError:
                    # Fallback to standard callback if it doesn't accept extra params
                    progress_callback(i, len(image_files), f"Processing: {input_file.name}")
            
            if self.process_single_image(
                str(input_file), 
                str(output_file),
                only_mask=only_mask,
                alpha_matting=alpha_matting,
                extra_params=extra_params
            ):
                successful += 1
                if self.logger:
                    self.logger.info(f"✓ Processed: {input_file.name}")
                processed_frames.append(str(output_file))
                
                # Call progress callback again with the completed output file - AFTER processing
                if progress_callback:
                    try:
                        progress_callback(i + 1, len(image_files), f"Completed: {input_file.name}",
                                        str(input_file), str(output_file))
                    except TypeError:
                        # Fallback to standard callback
                        progress_callback(i + 1, len(image_files), f"Completed: {input_file.name}")
            else:
                if self.logger:
                    self.logger.info(f"✗ Failed: {input_file.name}")
                
                # Still call progress callback for failed items
                if progress_callback:
                    try:
                        progress_callback(i + 1, len(image_files), f"Failed: {input_file.name}",
                                        str(input_file), None)
                    except TypeError:
                        # Fallback to standard callback
                        progress_callback(i + 1, len(image_files), f"Failed: {input_file.name}")
        
        if self.logger:
            self.logger.info(f"Completed: {successful}/{len(image_files)} images processed successfully")
        
        return {
            "total": len(image_files),
            "successful": successful,
            "processed_frames": processed_frames
        }
    
    def _parse_extra_params(self, extra_params: str) -> Dict[str, Any]:
        """Parse extra parameters from JSON string."""
        if not extra_params.strip():
            return {}
        
        try:
            return json.loads(extra_params)
        except json.JSONDecodeError:
            if self.logger:
                self.logger.info("Warning: Invalid JSON in extra parameters, ignoring")
            return {}
    
    def apply_greenscreen_background(
        self, 
        rgba_image_path: str, 
        output_path: str, 
        bg_color: tuple = (0, 255, 0)
    ) -> bool:
        """Apply greenscreen background to RGBA image."""
        if not PROCESSING_AVAILABLE:
            if self.logger:
                self.logger.error("PIL not available for background application")
            return False
        
        try:
            # Load the RGBA image
            with Image.open(rgba_image_path) as img:
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')
                
                # Create background with specified color
                background = Image.new('RGB', img.size, bg_color)
                
                # Composite the image onto the background
                result = Image.alpha_composite(
                    background.convert('RGBA'), 
                    img
                ).convert('RGB')
                
                # Ensure output directory exists
                if UTILS_AVAILABLE:
                    ensure_directory_exists(str(Path(output_path).parent))
                else:
                    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
                
                # Save as PNG to preserve quality
                result.save(output_path, 'PNG')
            
            return True
            
        except Exception as e:
            if self.logger:
                self.logger.debug(f"Error applying greenscreen background: {e}")
            return False
    
    def set_processing(self, processing: bool) -> None:
        """Set processing state."""
        self._state.set_processing(processing)
    
    def is_processing(self) -> bool:
        """Check if currently processing."""
        return self._state.is_processing()
    
    def stop_processing(self) -> None:
        """Stop processing."""
        self._state.stop_processing()
    
    def should_stop(self) -> bool:
        """Check if processing should stop."""
        return self._state.should_stop()
