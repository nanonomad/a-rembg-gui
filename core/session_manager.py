"""Session management for rembg processing."""

import time
import threading
from typing import Optional, List, Dict, Any

try:
    from rembg import new_session
    REMBG_AVAILABLE = True
except ImportError:
    REMBG_AVAILABLE = False

try:
    from config.settings import CUDA_OPTIONS
    SETTINGS_AVAILABLE = True
except ImportError:
    SETTINGS_AVAILABLE = False
    CUDA_OPTIONS = {
        'device_id': 0,
        'arena_extend_strategy': 'kSameAsRequested',
        'gpu_mem_limit': 2 * 1024 * 1024 * 1024,
        'cudnn_conv_algo_search': 'EXHAUSTIVE'
    }

try:
    from utils.logging_utils import Logger
    from utils.system_utils import get_memory_usage
    UTILS_AVAILABLE = True
except ImportError:
    UTILS_AVAILABLE = False


class SessionManager:
    """Manages rembg processing sessions with thread safety."""
    
    def __init__(self, logger=None):
        self.logger = logger
        self._lock = threading.Lock()
        self._session = None
        self._current_model = None
        self._use_gpu = False
    
    def create_session(self, model_name: str, use_gpu: bool = False) -> bool:
        """Create a new rembg session with thread safety."""
        with self._lock:
            return self._create_session_internal(model_name, use_gpu)
    
    def _create_session_internal(self, model_name: str, use_gpu: bool = False) -> bool:
        """Internal session creation method."""
        if not REMBG_AVAILABLE:
            if self.logger:
                self.logger.error("rembg not available")
            return False
        
        try:
            if self.logger:
                self.logger.debug("Creating new rembg session...")
            
            # Check memory before session creation
            if UTILS_AVAILABLE:
                memory_pre = get_memory_usage()
                if self.logger:
                    self.logger.debug(f"Memory before session: {memory_pre['available_gb']:.2f} GB available")
            
            # Determine providers
            providers = self._get_providers(use_gpu)
            
            # Create session
            start_time = time.time()
            
            try:
                self._session = new_session(model_name, providers=providers)
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Failed to create session with model {model_name}", e)
                
                # Try CPU fallback if GPU failed
                if use_gpu:
                    if self.logger:
                        self.logger.info("Attempting CPU fallback...")
                    return self._create_session_internal(model_name, use_gpu=False)
                
                return False
            
            session_time = time.time() - start_time
            
            self._current_model = model_name
            self._use_gpu = use_gpu and self._is_gpu_session(providers)
            
            # Log success
            acceleration = "GPU" if self._use_gpu else "CPU"
            if self.logger:
                self.logger.debug(f"{acceleration} session created in {session_time:.2f} seconds")
            
            # Check memory after session
            if UTILS_AVAILABLE:
                memory_post = get_memory_usage()
                memory_used = memory_pre['available_gb'] - memory_post['available_gb']
                if self.logger:
                    self.logger.debug(f"Session memory usage: {memory_used:.2f} GB")
            
            return True
            
        except Exception as e:
            if self.logger:
                self.logger.error("Session creation failed", e)
            
            # Try CPU fallback if GPU failed
            if use_gpu:
                if self.logger:
                    self.logger.info("Attempting CPU fallback...")
                return self._create_session_internal(model_name, use_gpu=False)
            
            return False
    
    def _get_providers(self, use_gpu: bool) -> List:
        """Get ONNX providers based on GPU preference."""
        if use_gpu and SETTINGS_AVAILABLE:
            providers = [
                ('CUDAExecutionProvider', CUDA_OPTIONS),
                'CPUExecutionProvider'
            ]
            if self.logger:
                self.logger.debug(f"GPU providers config: {providers}")
        else:
            providers = ['CPUExecutionProvider']
            if self.logger:
                self.logger.debug("Using CPU provider")
        
        return providers
    
    def _is_gpu_session(self, providers: List) -> bool:
        """Check if the session is actually using GPU."""
        try:
            # Check if GPU providers are in the list and available
            if isinstance(providers, list):
                for provider in providers:
                    if isinstance(provider, tuple):
                        provider_name = provider[0]
                    else:
                        provider_name = provider
                    
                    if 'CUDA' in provider_name or 'ROCM' in provider_name:
                        # Additional check to see if GPU is actually being used
                        try:
                            import onnxruntime as ort
                            available_providers = ort.get_available_providers()
                            return provider_name in available_providers
                        except ImportError:
                            return False
            return False
        except Exception:
            return False
    
    def get_session(self):
        """Get the current session with thread safety."""
        with self._lock:
            return self._session
    
    def destroy_session(self) -> None:
        """Destroy the current session with thread safety."""
        with self._lock:
            if self._session:
                if self.logger:
                    self.logger.debug("Destroying rembg session")
                
                try:
                    # Attempt to properly cleanup the session
                    # Note: rembg sessions don't have an explicit cleanup method,
                    # but we can still null the reference
                    self._session = None
                    self._current_model = None
                    self._use_gpu = False
                except Exception as e:
                    if self.logger:
                        self.logger.debug(f"Error during session cleanup: {e}")
                    # Force null the session even if cleanup fails
                    self._session = None
                    self._current_model = None
                    self._use_gpu = False
    
    def is_session_ready(self) -> bool:
        """Check if session is ready for processing with thread safety."""
        with self._lock:
            return self._session is not None
    
    def get_session_info(self) -> Dict[str, Any]:
        """Get information about the current session with thread safety."""
        with self._lock:
            return {
                'model': self._current_model,
                'use_gpu': self._use_gpu,
                'ready': self._session is not None,
                'rembg_available': REMBG_AVAILABLE
            }
    
    def recreate_session_if_needed(self, model_name: str, use_gpu: bool = False) -> bool:
        """Recreate session if model or GPU setting changed."""
        with self._lock:
            # Check if we need to recreate
            if (self._session is None or 
                self._current_model != model_name or 
                self._use_gpu != use_gpu):
                
                # Destroy existing session
                if self._session:
                    if self.logger:
                        self.logger.debug("Recreating session due to changed parameters")
                    self._session = None
                
                # Create new session
                return self._create_session_internal(model_name, use_gpu)
            
            return True  # Session is already correct
    
    def __del__(self):
        """Cleanup on object destruction."""
        try:
            self.destroy_session()
        except Exception:
            # Silent cleanup on destruction
            pass
