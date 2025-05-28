"""Application settings and configuration constants."""

import os
from pathlib import Path

# GUI Settings
WINDOW_TITLE = "rembg Background Remover"
WINDOW_SIZE = "1000x850"
WINDOW_MIN_SIZE = (800, 700)

# File extensions
IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.webp'}
VIDEO_EXTENSIONS = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv'}

# Canvas settings
CANVAS_WIDTH = 400
CANVAS_HEIGHT = 300

# Default values
DEFAULT_FPS = 30
DEFAULT_BG_COLOR = (0, 255, 0)  # Green
DEFAULT_FILENAME_FORMAT = "{name}_no_bg.png"

# File size limits (in MB)
MAX_IMAGE_SIZE_MB = 100  # 100MB limit for single images
MAX_VIDEO_SIZE_MB = 1000  # 1GB limit for videos

# Memory limits
MIN_AVAILABLE_MEMORY_GB = 1.0  # Minimum required available memory

# File type filters
IMAGE_FILE_TYPES = [
    ("Image files", "*.png *.jpg *.jpeg *.bmp *.tiff *.webp"),
    ("All files", "*.*")
]

VIDEO_FILE_TYPES = [
    ("Video files", "*.mp4 *.avi *.mov *.mkv *.wmv *.flv"),
    ("All files", "*.*")
]

# Model directory - fixed to use correct rembg path
def get_model_directory():
    """Get the rembg model directory."""
    # Check environment variable first (allows override)
    env_path = os.environ.get('REMBG_MODELS_PATH')
    if env_path:
        return Path(env_path)
    
    # Use rembg's actual model directory
    return Path.home() / ".u2net"


def ensure_output_directory(output_path: str) -> bool:
    """Ensure output directory exists and is writable.
    
    Returns:
        True if directory is ready, False if there are permission issues
    """
    try:
        output_dir = Path(output_path)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Test write permissions by creating a temporary file
        test_file = output_dir / ".write_test"
        try:
            test_file.touch()
            test_file.unlink()
            return True
        except (PermissionError, OSError):
            return False
            
    except (PermissionError, OSError, FileExistsError):
        return False


def safe_path_join(*args) -> str:
    """Safely join path components for cross-platform compatibility."""
    return str(Path(*args))


def validate_rgb_color(r: str, g: str, b: str) -> tuple:
    """Validate and clamp RGB color values.
    
    Returns:
        Tuple of (r, g, b) values clamped to 0-255 range
    """
    def clamp_color_value(value_str: str, default: int = 0) -> int:
        try:
            value = int(float(value_str))  # Handle decimal inputs
            return max(0, min(255, value))  # Clamp to 0-255
        except (ValueError, TypeError):
            return default
    
    return (
        clamp_color_value(r, 0),
        clamp_color_value(g, 255),
        clamp_color_value(b, 0)
    )


def validate_fps(fps_str: str) -> tuple[bool, float]:
    """Validate FPS input.
    
    Returns:
        Tuple of (is_valid, fps_value). fps_value is None for native framerate.
    """
    fps_str = fps_str.strip()
    
    if not fps_str:
        return True, None  # Empty = use native framerate
    
    try:
        fps = float(fps_str)
        if fps <= 0:
            return False, None
        if fps > 120:  # Reasonable upper limit
            return False, None
        return True, fps
    except (ValueError, TypeError):
        return False, None


# GPU memory settings
GPU_MEMORY_LIMIT = 2 * 1024 * 1024 * 1024  # 2GB limit

# CUDA options
CUDA_OPTIONS = {
    'device_id': 0,
    'arena_extend_strategy': 'kSameAsRequested',
    'gpu_mem_limit': GPU_MEMORY_LIMIT,
    'cudnn_conv_algo_search': 'EXHAUSTIVE'
}
