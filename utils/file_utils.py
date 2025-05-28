"""File handling utilities."""

import os
import shutil
import time
from pathlib import Path
from typing import List, Callable, Optional, Tuple

try:
    import urllib.request
    import urllib.error
    URL_AVAILABLE = True
except ImportError:
    URL_AVAILABLE = False

from config.settings import IMAGE_EXTENSIONS, MAX_IMAGE_SIZE_MB, MAX_VIDEO_SIZE_MB


def find_image_files(directory: str) -> List[Path]:
    """Find all image files in a directory recursively."""
    image_files = []
    try:
        for file_path in Path(directory).rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in IMAGE_EXTENSIONS:
                image_files.append(file_path)
    except (PermissionError, OSError) as e:
        print(f"Error accessing directory {directory}: {e}")
    
    return image_files


def generate_output_filename(input_path: str, output_dir: str, format_template: str) -> str:
    """Generate output filename using the format template."""
    input_path_obj = Path(input_path)
    output_dir_obj = Path(output_dir)
    
    # Replace template variables
    output_name = format_template.format(
        name=input_path_obj.stem,
        ext=input_path_obj.suffix
    )
    
    return str(output_dir_obj / output_name)


def download_file(url: str, filepath: Path, progress_callback: Optional[Callable] = None) -> bool:
    """Download a file with optional progress reporting.
    
    Returns:
        True if download was successful, False otherwise
    """
    if not URL_AVAILABLE:
        print("URL download not available - missing urllib")
        return False
    
    def progress_hook(block_num, block_size, total_size):
        if progress_callback and total_size > 0:
            downloaded = block_num * block_size
            percentage = min(100, (downloaded / total_size) * 100)
            progress_callback(downloaded, total_size, percentage)
    
    try:
        filepath.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(url, filepath, reporthook=progress_hook)
        return True
    except (urllib.error.URLError, OSError, PermissionError) as e:
        print(f"Error downloading {url}: {e}")
        return False


def get_file_size_mb(filepath: str) -> float:
    """Get file size in megabytes."""
    try:
        return os.path.getsize(filepath) / (1024**2)
    except (OSError, FileNotFoundError):
        return 0.0


def ensure_directory_exists(directory: str) -> bool:
    """Create directory if it doesn't exist.
    
    Returns:
        True if directory exists/was created successfully, False otherwise
    """
    try:
        Path(directory).mkdir(parents=True, exist_ok=True)
        return True
    except (PermissionError, OSError) as e:
        print(f"Error creating directory {directory}: {e}")
        return False


def safe_remove_directory(directory: str, max_retries: int = 3) -> bool:
    """Safely remove a directory with retries.
    
    Args:
        directory: Directory path to remove
        max_retries: Maximum number of retry attempts
        
    Returns:
        True if removal was successful, False otherwise
    """
    if not Path(directory).exists():
        return True
    
    for attempt in range(max_retries):
        try:
            shutil.rmtree(directory, ignore_errors=False)
            return True
        except (PermissionError, OSError) as e:
            if attempt < max_retries - 1:
                time.sleep(0.5)  # Wait before retry
                continue
            else:
                print(f"Failed to remove directory {directory} after {max_retries} attempts: {e}")
                # Try with ignore_errors as last resort
                try:
                    shutil.rmtree(directory, ignore_errors=True)
                    return True
                except Exception:
                    return False
    
    return False


def validate_file_size(filepath: str, is_video: bool = False) -> Tuple[bool, str]:
    """Validate if file size is within acceptable limits.
    
    Args:
        filepath: Path to the file to check
        is_video: True if this is a video file
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        size_mb = get_file_size_mb(filepath)
        max_size = MAX_VIDEO_SIZE_MB if is_video else MAX_IMAGE_SIZE_MB
        file_type = "Video" if is_video else "Image"
        
        if size_mb > max_size:
            return False, f"{file_type} file too large: {size_mb:.1f}MB (max: {max_size}MB)"
        
        return True, ""
        
    except Exception as e:
        return False, f"Error checking file size: {e}"


def get_safe_filename(filename: str) -> str:
    """Get a safe filename by removing/replacing problematic characters."""
    # Remove or replace characters that are problematic on Windows/Unix
    unsafe_chars = '<>:"/\\|?*'
    safe_name = filename
    
    for char in unsafe_chars:
        safe_name = safe_name.replace(char, '_')
    
    # Remove any control characters
    safe_name = ''.join(char for char in safe_name if ord(char) >= 32)
    
    # Ensure it's not empty and doesn't start/end with spaces or dots
    safe_name = safe_name.strip(' .')
    if not safe_name:
        safe_name = "untitled"
    
    return safe_name


def check_disk_space(directory: str, required_mb: float) -> bool:
    """Check if there's enough disk space in the target directory.
    
    Args:
        directory: Directory to check
        required_mb: Required space in megabytes
        
    Returns:
        True if enough space is available
    """
    try:
        if os.name == 'nt':  # Windows
            free_bytes = shutil.disk_usage(directory).free
        else:  # Unix-like
            statvfs = os.statvfs(directory)
            free_bytes = statvfs.f_frsize * statvfs.f_bavail
        
        free_mb = free_bytes / (1024**2)
        return free_mb >= required_mb
        
    except (OSError, AttributeError):
        # If we can't check, assume it's okay
        return True
