"""Video processing functionality."""

import os
import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional, Callable

try:
    import cv2
    VIDEO_AVAILABLE = True
except ImportError:
    VIDEO_AVAILABLE = False

from core.processor import ImageProcessor
from utils.logging_utils import Logger
from utils.file_utils import ensure_directory_exists


class VideoHandler:
    """Handles video processing operations."""
    
    def __init__(self, image_processor: ImageProcessor, logger: Logger):
        self.image_processor = image_processor
        self.logger = logger
        self.original_video_info = {}
    
    def get_video_info(self, video_path: str) -> Dict[str, Any]:
        """Get video information including fps, duration, and codec."""
        if not VIDEO_AVAILABLE:
            raise Exception("OpenCV not available for video processing")
        
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise Exception(f"Could not open video file: {video_path}")
        
        try:
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            duration = frame_count / fps if fps > 0 else 0
            
            # Try to get codec information
            fourcc = int(cap.get(cv2.CAP_PROP_FOURCC))
            codec = "".join([chr((fourcc >> 8 * i) & 0xFF) for i in range(4)])
            
            video_info = {
                'fps': fps,
                'frame_count': frame_count,
                'width': width,
                'height': height,
                'duration': duration,
                'codec': codec
            }
            
            self.logger.debug(f"Video info: {video_info}")
            return video_info
            
        finally:
            cap.release()
    
    def extract_video_frames(
        self, 
        video_path: str, 
        output_dir: str, 
        fps: Optional[float] = None,
        progress_callback: Optional[Callable] = None
    ) -> List[str]:
        """Extract frames from video file.
        
        Args:
            video_path: Path to the input video file
            output_dir: Directory to save extracted frames
            fps: Target FPS for extraction. If None, uses native video framerate (extracts all frames)
            progress_callback: Optional callback for progress updates
        """
        if not VIDEO_AVAILABLE:
            raise Exception("OpenCV not available for video processing")
        
        ensure_directory_exists(output_dir)
        
        # Get original video information
        self.original_video_info = self.get_video_info(video_path)
        video_fps = self.original_video_info['fps']
        total_frames = self.original_video_info['frame_count']
        
        self.logger.info(f"Original video: {self.original_video_info['width']}x{self.original_video_info['height']} @ {video_fps:.2f} FPS")
        self.logger.info(f"Duration: {self.original_video_info['duration']:.2f} seconds, {total_frames} frames")
        
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise Exception(f"Could not open video file: {video_path}")
        
        # Determine frame extraction strategy
        if fps is None:
            # Extract all frames at native framerate
            frame_skip = 1
            self.logger.info("Extracting ALL frames at native framerate")
        else:
            # Calculate frame skip to match desired FPS
            frame_skip = max(1, int(video_fps / fps))
            self.logger.info(f"Video FPS: {video_fps:.2f}, Target FPS: {fps:.2f}, Extracting every {frame_skip} frames")
        
        frame_files = []
        frame_count = 0
        saved_count = 0
        
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                if frame_count % frame_skip == 0:
                    frame_filename = os.path.join(output_dir, f"frame_{saved_count:06d}.png")
                    cv2.imwrite(frame_filename, frame)
                    frame_files.append(frame_filename)
                    saved_count += 1
                    
                    if saved_count % 10 == 0 and progress_callback:  # Update every 10 frames
                        progress_callback(frame_count, total_frames, f"Extracting frames: {saved_count}")
                
                frame_count += 1
        
        finally:
            cap.release()
        
        self.logger.info(f"Extracted {len(frame_files)} frames from video")
        return frame_files
    
    def reassemble_video_from_frames(
        self,
        frames_dir: str,
        output_video_path: str,
        bg_color: tuple = (0, 255, 0),
        fps: Optional[float] = None,
        progress_callback: Optional[Callable] = None
    ) -> bool:
        """Reassemble video from processed frames with greenscreen background.
        
        Args:
            frames_dir: Directory containing processed frames
            output_video_path: Path for the output video
            bg_color: Background color RGB tuple
            fps: Output video FPS. If None, uses original video FPS
            progress_callback: Optional callback for progress updates
        """
        if not VIDEO_AVAILABLE:
            self.logger.error("OpenCV not available for video processing")
            return False
        
        try:
            self.logger.info(f"Using background color RGB: {bg_color}")
            
            # Use original video FPS if not specified
            if fps is None:
                fps = self.original_video_info.get('fps', 30.0)
            
            self.logger.info(f"Output video FPS: {fps:.2f}")
            
            # Find all processed frame files
            frame_files = []
            for file in sorted(os.listdir(frames_dir)):
                if file.startswith('frame_') and file.endswith(('.png', '.jpg', '.jpeg')):
                    frame_files.append(os.path.join(frames_dir, file))
            
            if not frame_files:
                raise Exception("No processed frames found for video reassembly")
            
            self.logger.info(f"Reassembling {len(frame_files)} frames into video at {fps:.2f} FPS")
            
            # Create temporary directory for greenscreen frames
            greenscreen_dir = os.path.join(os.path.dirname(frames_dir), "greenscreen_frames")
            ensure_directory_exists(greenscreen_dir)
            
            # Apply greenscreen background to all frames
            self.logger.info("Applying greenscreen background to frames...")
            for i, frame_file in enumerate(frame_files):
                if not self.image_processor.is_processing():  # Check if stopped
                    break
                
                frame_name = os.path.basename(frame_file)
                greenscreen_frame_path = os.path.join(greenscreen_dir, frame_name)
                
                if self.image_processor.apply_greenscreen_background(frame_file, greenscreen_frame_path, bg_color):
                    if progress_callback:
                        progress_callback(i, len(frame_files), f"Applying background: {i+1}/{len(frame_files)}")
                else:
                    self.logger.info(f"Failed to apply background to frame {i+1}")
            
            if not self.image_processor.is_processing():
                return False
            
            self.logger.info("Creating video from greenscreen frames...")
            
            # Get frame dimensions from first frame
            first_frame = cv2.imread(os.path.join(greenscreen_dir, os.listdir(greenscreen_dir)[0]))
            height, width, layers = first_frame.shape
            
            # Use original video dimensions if available
            if 'width' in self.original_video_info and 'height' in self.original_video_info:
                width = self.original_video_info['width']
                height = self.original_video_info['height']
            
            # Define codec and create VideoWriter
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))
            
            # Write frames to video
            greenscreen_files = sorted([f for f in os.listdir(greenscreen_dir) if f.endswith('.png')])
            
            for i, frame_file in enumerate(greenscreen_files):
                if not self.image_processor.is_processing():  # Check if stopped
                    break
                
                frame_path = os.path.join(greenscreen_dir, frame_file)
                frame = cv2.imread(frame_path)
                
                if frame is not None:
                    # Resize frame if necessary
                    if frame.shape[:2] != (height, width):
                        frame = cv2.resize(frame, (width, height))
                    
                    out.write(frame)
                    
                    if i % 30 == 0 and progress_callback:  # Update every 30 frames
                        progress_callback(i, len(greenscreen_files), f"Writing video: {i+1}/{len(greenscreen_files)}")
            
            out.release()
            
            # Clean up temporary greenscreen frames
            try:
                shutil.rmtree(greenscreen_dir)
                self.logger.debug(f"Cleaned up greenscreen frames directory: {greenscreen_dir}")
            except Exception as e:
                self.logger.debug(f"Could not clean up greenscreen frames: {e}")
            
            if self.image_processor.is_processing():
                self.logger.info(f"✓ Video reassembled successfully: {output_video_path}")
                return True
            else:
                self.logger.info("Video reassembly stopped")
                return False
                
        except Exception as e:
            self.logger.error("Error in video reassembly", e)
            return False
    
    def generate_video_output_filename(self, input_video_path: str, output_dir: str) -> str:
        """Generate output video filename with timestamp."""
        input_path = Path(input_video_path)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create filename with _no_bg suffix and timestamp
        output_name = f"{input_path.stem}_no_bg_{timestamp}.mp4"
        return str(Path(output_dir) / output_name)
