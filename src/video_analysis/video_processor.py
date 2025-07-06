import cv2
import numpy as np
from pathlib import Path
from typing import Generator, Tuple, Optional, List
import logging
from dataclasses import dataclass
from moviepy.editor import VideoFileClip
import json

@dataclass
class VideoMetadata:
    """Metadata for uploaded video."""
    filename: str
    duration: float
    fps: float
    width: int
    height: int
    total_frames: int
    format: str

class VideoProcessor:
    """Core video processing engine for sports analysis."""
    
    def __init__(self, video_path: str):
        self.video_path = Path(video_path)
        self.cap = None
        self.metadata = None
        self.current_frame = 0
        self.logger = logging.getLogger(__name__)
        
    def load_video(self) -> VideoMetadata:
        """Load video and extract metadata."""
        try:
            self.cap = cv2.VideoCapture(str(self.video_path))
            
            if not self.cap.isOpened():
                raise ValueError(f"Cannot open video: {self.video_path}")
            
            # Extract video metadata
            fps = self.cap.get(cv2.CAP_PROP_FPS)
            width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = total_frames / fps if fps > 0 else 0
            
            self.metadata = VideoMetadata(
                filename=self.video_path.name,
                duration=duration,
                fps=fps,
                width=width,
                height=height,
                total_frames=total_frames,
                format=self.video_path.suffix.lower()
            )
            
            self.logger.info(f"Loaded video: {self.metadata.filename} - {width}x{height} @ {fps:.2f}fps")
            return self.metadata
            
        except Exception as e:
            self.logger.error(f"Error loading video: {str(e)}")
            raise
    
    def get_frame_generator(self, skip_frames: int = 1) -> Generator[Tuple[int, np.ndarray], None, None]:
        """Generate frames from video with optional frame skipping."""
        if not self.cap:
            raise ValueError("Video not loaded. Call load_video() first.")
        
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        frame_count = 0
        
        while True:
            ret, frame = self.cap.read()
            if not ret:
                break
                
            if frame_count % skip_frames == 0:
                yield frame_count, frame
            
            frame_count += 1
    
    def get_frame_at_timestamp(self, timestamp: float) -> Optional[np.ndarray]:
        """Get frame at specific timestamp (in seconds)."""
        if not self.cap or not self.metadata:
            raise ValueError("Video not loaded. Call load_video() first.")
        
        frame_number = int(timestamp * self.metadata.fps)
        return self.get_frame_at_index(frame_number)
    
    def get_frame_at_index(self, frame_index: int) -> Optional[np.ndarray]:
        """Get frame at specific index."""
        if not self.cap:
            raise ValueError("Video not loaded. Call load_video() first.")
        
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
        ret, frame = self.cap.read()
        
        if ret:
            return frame
        return None
    
    def extract_frames_batch(self, start_frame: int, end_frame: int) -> List[np.ndarray]:
        """Extract a batch of frames between start and end indices."""
        frames = []
        
        for i in range(start_frame, min(end_frame, self.metadata.total_frames)):
            frame = self.get_frame_at_index(i)
            if frame is not None:
                frames.append(frame)
        
        return frames
    
    def preprocess_frame(self, frame: np.ndarray, target_size: Optional[Tuple[int, int]] = None) -> np.ndarray:
        """Preprocess frame for analysis (resize, normalize, etc.)."""
        processed = frame.copy()
        
        # Resize if target size specified
        if target_size:
            processed = cv2.resize(processed, target_size)
        
        # Convert to RGB (OpenCV uses BGR by default)
        processed = cv2.cvtColor(processed, cv2.COLOR_BGR2RGB)
        
        return processed
    
    def get_video_info(self) -> dict:
        """Get comprehensive video information."""
        if not self.metadata:
            raise ValueError("Video not loaded. Call load_video() first.")
        
        return {
            'filename': self.metadata.filename,
            'duration': self.metadata.duration,
            'fps': self.metadata.fps,
            'resolution': f"{self.metadata.width}x{self.metadata.height}",
            'total_frames': self.metadata.total_frames,
            'format': self.metadata.format,
            'duration_formatted': self._format_duration(self.metadata.duration)
        }
    
    def _format_duration(self, seconds: float) -> str:
        """Format duration in human-readable format."""
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes:02d}:{seconds:02d}"
    
    def save_frame(self, frame: np.ndarray, output_path: str, timestamp: float = None):
        """Save a frame to disk with optional timestamp in filename."""
        if timestamp is not None:
            base_path = Path(output_path)
            stem = base_path.stem
            suffix = base_path.suffix
            output_path = base_path.parent / f"{stem}_{timestamp:.2f}s{suffix}"
        
        # Convert from RGB back to BGR for saving
        if len(frame.shape) == 3 and frame.shape[2] == 3:
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        
        cv2.imwrite(str(output_path), frame)
        self.logger.info(f"Saved frame to: {output_path}")
    
    def close(self):
        """Clean up resources."""
        if self.cap:
            self.cap.release()
            self.cap = None
        self.logger.info("Video processor closed")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()