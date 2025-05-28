"""System utilities for hardware detection and monitoring."""

import sys
import psutil
from typing import List, Dict, Any, Optional

try:
    import onnxruntime as ort
    ONNX_AVAILABLE = True
except ImportError:
    ONNX_AVAILABLE = False


def get_system_info() -> Dict[str, Any]:
    """Get basic system information."""
    return {
        'python_version': sys.version,
        'platform': sys.platform,
        'available_memory_gb': psutil.virtual_memory().available / (1024**3)
    }


def check_gpu_availability() -> Dict[str, Any]:
    """Check if GPU acceleration is available."""
    gpu_info = {
        'cuda_available': False,
        'rocm_available': False,
        'providers': []
    }
    
    if not ONNX_AVAILABLE:
        return gpu_info
    
    try:
        providers = ort.get_available_providers()
        gpu_info['providers'] = providers
        
        # CUDA check
        cuda_available = 'CUDAExecutionProvider' in providers
        gpu_info['cuda_available'] = cuda_available
        
        # ROCM check
        rocm_available = 'ROCMExecutionProvider' in providers
        gpu_info['rocm_available'] = rocm_available
        
    except Exception as e:
        print(f"Error checking GPU availability: {e}")
    
    return gpu_info


def get_memory_usage() -> Dict[str, float]:
    """Get current memory usage in GB."""
    memory = psutil.virtual_memory()
    return {
        'total_gb': memory.total / (1024**3),
        'available_gb': memory.available / (1024**3),
        'used_gb': memory.used / (1024**3),
        'percent': memory.percent
    }


def check_available_memory_for_file(file_path: str, multiplier: float = 3.0) -> bool:
    """Check if there's enough memory to process a file.
    
    Args:
        file_path: Path to the file to check
        multiplier: Memory multiplier (image processing typically needs 2-4x file size)
    
    Returns:
        True if enough memory is available
    """
    try:
        import os
        file_size_gb = os.path.getsize(file_path) / (1024**3)
        required_memory_gb = file_size_gb * multiplier
        available_memory_gb = psutil.virtual_memory().available / (1024**3)
        
        return available_memory_gb >= required_memory_gb
    except Exception:
        # If we can't check, assume it's okay to proceed
        return True


def get_safe_temp_directory() -> str:
    """Get a safe temporary directory with proper cleanup handling."""
    import tempfile
    import atexit
    import shutil
    from pathlib import Path
    
    # Create temp directory with cleanup registration
    temp_dir = tempfile.mkdtemp(prefix="rembg_")
    
    def cleanup_temp_dir():
        """Cleanup function registered with atexit."""
        try:
            if Path(temp_dir).exists():
                shutil.rmtree(temp_dir, ignore_errors=True)
        except Exception:
            pass  # Silent cleanup on exit
    
    atexit.register(cleanup_temp_dir)
    return temp_dir
