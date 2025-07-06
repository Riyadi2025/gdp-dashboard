import cv2
import numpy as np
from typing import List, Dict, Tuple, Optional, Any, Callable
import ffmpeg
import logging
from pathlib import Path
from dataclasses import dataclass
import json
import tempfile
import shutil
from moviepy.editor import VideoFileClip, CompositeVideoClip
import subprocess

@dataclass
class ExportSettings:
    """Settings for video export."""
    output_format: str = 'mp4'
    codec: str = 'libx264'
    bitrate: str = '5000k'
    fps: float = 30.0
    resolution: Tuple[int, int] = None  # (width, height), None to keep original
    quality: str = 'high'  # 'low', 'medium', 'high', 'lossless'
    audio_codec: str = 'aac'
    audio_bitrate: str = '128k'
    include_audio: bool = True
    
    def get_quality_settings(self) -> Dict[str, Any]:
        """Get quality-specific settings."""
        quality_presets = {
            'low': {'crf': 28, 'preset': 'fast'},
            'medium': {'crf': 23, 'preset': 'medium'},
            'high': {'crf': 18, 'preset': 'slow'},
            'lossless': {'crf': 0, 'preset': 'veryslow'}
        }
        return quality_presets.get(self.quality, quality_presets['medium'])

@dataclass
class ExportProgress:
    """Progress information for export operations."""
    current_frame: int
    total_frames: int
    elapsed_time: float
    estimated_remaining: float
    current_stage: str
    
    @property
    def progress_percent(self) -> float:
        """Get progress as percentage."""
        if self.total_frames == 0:
            return 0.0
        return (self.current_frame / self.total_frames) * 100.0

class VideoExporter:
    """Advanced video exporter with FFmpeg integration."""
    
    def __init__(self, temp_dir: Optional[str] = None):
        """Initialize the video exporter."""
        self.temp_dir = Path(temp_dir) if temp_dir else Path(tempfile.mkdtemp())
        self.temp_dir.mkdir(exist_ok=True)
        self.logger = logging.getLogger(__name__)
        
        # Check if FFmpeg is available
        self._check_ffmpeg_availability()
    
    def _check_ffmpeg_availability(self):
        """Check if FFmpeg is available in the system."""
        try:
            subprocess.run(['ffmpeg', '-version'], 
                          capture_output=True, check=True)
            self.logger.info("FFmpeg found and ready")
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.logger.warning("FFmpeg not found. Some export features may not work.")
    
    def export_annotated_video(self, 
                              input_video_path: str,
                              output_path: str,
                              frame_processor: Callable[[np.ndarray, int, float], np.ndarray],
                              settings: ExportSettings = None,
                              progress_callback: Optional[Callable[[ExportProgress], None]] = None) -> bool:
        """
        Export video with annotations applied by frame processor.
        
        Args:
            input_video_path: Path to input video
            output_path: Path for output video
            frame_processor: Function that processes each frame
            settings: Export settings
            progress_callback: Optional callback for progress updates
        
        Returns:
            True if export successful, False otherwise
        """
        if settings is None:
            settings = ExportSettings()
        
        try:
            # Load input video
            cap = cv2.VideoCapture(input_video_path)
            
            if not cap.isOpened():
                self.logger.error(f"Cannot open input video: {input_video_path}")
                return False
            
            # Get video properties
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            # Override resolution if specified
            if settings.resolution:
                width, height = settings.resolution
            
            # Setup output video writer
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            temp_output = self.temp_dir / f"temp_output.mp4"
            
            out = cv2.VideoWriter(str(temp_output), fourcc, fps, (width, height))
            
            if not out.isOpened():
                self.logger.error("Cannot create output video writer")
                return False
            
            # Process frames
            frame_idx = 0
            start_time = cv2.getTickCount()
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Resize frame if needed
                if settings.resolution and (frame.shape[1] != width or frame.shape[0] != height):
                    frame = cv2.resize(frame, (width, height))
                
                # Apply frame processing (annotations, etc.)
                timestamp = frame_idx / fps
                processed_frame = frame_processor(frame, frame_idx, timestamp)
                
                # Write frame
                out.write(processed_frame)
                
                # Update progress
                frame_idx += 1
                if progress_callback and frame_idx % 10 == 0:  # Update every 10 frames
                    elapsed = (cv2.getTickCount() - start_time) / cv2.getTickFrequency()
                    fps_processed = frame_idx / elapsed if elapsed > 0 else 0
                    remaining_frames = frame_count - frame_idx
                    estimated_remaining = remaining_frames / fps_processed if fps_processed > 0 else 0
                    
                    progress = ExportProgress(
                        current_frame=frame_idx,
                        total_frames=frame_count,
                        elapsed_time=elapsed,
                        estimated_remaining=estimated_remaining,
                        current_stage="Processing frames"
                    )
                    progress_callback(progress)
            
            # Clean up
            cap.release()
            out.release()
            
            # Post-process with FFmpeg for better quality and audio
            if settings.include_audio:
                self._add_audio_and_finalize(input_video_path, str(temp_output), output_path, settings)
            else:
                self._finalize_without_audio(str(temp_output), output_path, settings)
            
            # Clean up temp file
            temp_output.unlink()
            
            self.logger.info(f"Video exported successfully to: {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error exporting video: {str(e)}")
            return False
    
    def _add_audio_and_finalize(self, original_path: str, processed_path: str, 
                               output_path: str, settings: ExportSettings):
        """Add audio from original video and finalize with FFmpeg."""
        try:
            quality_settings = settings.get_quality_settings()
            
            # Build FFmpeg command
            input_video = ffmpeg.input(processed_path)
            input_audio = ffmpeg.input(original_path)
            
            # Configure video stream
            video_stream = ffmpeg.filter(input_video, 'scale', 
                                        width=-1 if not settings.resolution else settings.resolution[0],
                                        height=-1 if not settings.resolution else settings.resolution[1])
            
            # Configure audio stream
            audio_stream = ffmpeg.filter(input_audio['a'], 'aresample', 44100)
            
            # Combine streams
            output = ffmpeg.output(
                video_stream, 
                audio_stream,
                output_path,
                vcodec=settings.codec,
                acodec=settings.audio_codec,
                video_bitrate=settings.bitrate,
                audio_bitrate=settings.audio_bitrate,
                crf=quality_settings['crf'],
                preset=quality_settings['preset'],
                r=settings.fps
            )
            
            # Run FFmpeg
            ffmpeg.run(output, overwrite_output=True, quiet=True)
            
        except Exception as e:
            self.logger.error(f"Error in FFmpeg processing: {str(e)}")
            # Fallback: just copy the processed video
            shutil.copy2(processed_path, output_path)
    
    def _finalize_without_audio(self, processed_path: str, output_path: str, settings: ExportSettings):
        """Finalize video without audio using FFmpeg."""
        try:
            quality_settings = settings.get_quality_settings()
            
            input_stream = ffmpeg.input(processed_path)
            
            # Configure video stream
            video_stream = ffmpeg.filter(input_stream, 'scale',
                                        width=-1 if not settings.resolution else settings.resolution[0],
                                        height=-1 if not settings.resolution else settings.resolution[1])
            
            # Output configuration
            output = ffmpeg.output(
                video_stream,
                output_path,
                vcodec=settings.codec,
                video_bitrate=settings.bitrate,
                crf=quality_settings['crf'],
                preset=quality_settings['preset'],
                r=settings.fps
            )
            
            # Run FFmpeg
            ffmpeg.run(output, overwrite_output=True, quiet=True)
            
        except Exception as e:
            self.logger.error(f"Error in FFmpeg processing: {str(e)}")
            # Fallback: just copy the processed video
            shutil.copy2(processed_path, output_path)
    
    def create_highlight_reel(self, 
                             input_video_path: str,
                             output_path: str,
                             highlight_segments: List[Tuple[float, float]], # (start_time, end_time)
                             settings: ExportSettings = None) -> bool:
        """
        Create a highlight reel from specified segments.
        
        Args:
            input_video_path: Path to input video
            output_path: Path for output highlight reel
            highlight_segments: List of (start_time, end_time) tuples in seconds
            settings: Export settings
        
        Returns:
            True if successful, False otherwise
        """
        if settings is None:
            settings = ExportSettings()
        
        try:
            # Load video
            video = VideoFileClip(input_video_path)
            
            # Extract highlight clips
            highlight_clips = []
            for start_time, end_time in highlight_segments:
                # Ensure times are within video bounds
                start_time = max(0, min(start_time, video.duration))
                end_time = max(start_time, min(end_time, video.duration))
                
                if end_time > start_time:
                    clip = video.subclip(start_time, end_time)
                    highlight_clips.append(clip)
            
            if not highlight_clips:
                self.logger.warning("No valid highlight segments found")
                return False
            
            # Concatenate clips
            final_clip = CompositeVideoClip(highlight_clips)
            
            # Write output
            final_clip.write_videofile(
                output_path,
                codec=settings.codec,
                fps=settings.fps,
                bitrate=settings.bitrate,
                audio_codec=settings.audio_codec if settings.include_audio else None
            )
            
            # Clean up
            video.close()
            final_clip.close()
            for clip in highlight_clips:
                clip.close()
            
            self.logger.info(f"Highlight reel created: {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error creating highlight reel: {str(e)}")
            return False
    
    def export_frame_sequence(self, 
                             frames: List[np.ndarray],
                             output_path: str,
                             fps: float = 30.0,
                             settings: ExportSettings = None) -> bool:
        """
        Export a sequence of frames as a video.
        
        Args:
            frames: List of frame arrays
            output_path: Output video path
            fps: Frames per second
            settings: Export settings
        
        Returns:
            True if successful, False otherwise
        """
        if not frames:
            self.logger.error("No frames to export")
            return False
        
        if settings is None:
            settings = ExportSettings()
        
        try:
            # Get frame dimensions
            height, width = frames[0].shape[:2]
            
            if settings.resolution:
                width, height = settings.resolution
            
            # Create video writer
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            temp_output = self.temp_dir / f"temp_sequence.mp4"
            
            out = cv2.VideoWriter(str(temp_output), fourcc, fps, (width, height))
            
            if not out.isOpened():
                self.logger.error("Cannot create video writer")
                return False
            
            # Write frames
            for i, frame in enumerate(frames):
                # Resize if needed
                if settings.resolution and (frame.shape[1] != width or frame.shape[0] != height):
                    frame = cv2.resize(frame, (width, height))
                
                out.write(frame)
            
            out.release()
            
            # Finalize with FFmpeg
            self._finalize_without_audio(str(temp_output), output_path, settings)
            
            # Clean up
            temp_output.unlink()
            
            self.logger.info(f"Frame sequence exported: {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error exporting frame sequence: {str(e)}")
            return False
    
    def export_with_custom_overlays(self,
                                   input_video_path: str,
                                   output_path: str,
                                   overlay_data: Dict[str, Any],
                                   settings: ExportSettings = None) -> bool:
        """
        Export video with custom overlays like scoreboards, timers, etc.
        
        Args:
            input_video_path: Path to input video
            output_path: Path for output video
            overlay_data: Dictionary containing overlay configuration
            settings: Export settings
        
        Returns:
            True if successful, False otherwise
        """
        if settings is None:
            settings = ExportSettings()
        
        def frame_processor(frame: np.ndarray, frame_idx: int, timestamp: float) -> np.ndarray:
            """Process frame with custom overlays."""
            processed_frame = frame.copy()
            
            # Add scoreboard overlay
            if 'scoreboard' in overlay_data:
                scoreboard = overlay_data['scoreboard']
                processed_frame = self._add_scoreboard_overlay(
                    processed_frame, scoreboard, timestamp
                )
            
            # Add timer overlay
            if 'timer' in overlay_data:
                timer = overlay_data['timer']
                processed_frame = self._add_timer_overlay(
                    processed_frame, timer, timestamp
                )
            
            # Add custom text overlays
            if 'text_overlays' in overlay_data:
                for text_overlay in overlay_data['text_overlays']:
                    if self._should_show_overlay(text_overlay, timestamp):
                        processed_frame = self._add_text_overlay(
                            processed_frame, text_overlay
                        )
            
            return processed_frame
        
        return self.export_annotated_video(
            input_video_path, output_path, frame_processor, settings
        )
    
    def _add_scoreboard_overlay(self, frame: np.ndarray, scoreboard_config: Dict, 
                               timestamp: float) -> np.ndarray:
        """Add scoreboard overlay to frame."""
        # Get scoreboard data for current timestamp
        current_score = self._get_score_at_timestamp(scoreboard_config, timestamp)
        
        # Position and styling
        x, y = scoreboard_config.get('position', (10, 10))
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = scoreboard_config.get('font_scale', 1.0)
        color = scoreboard_config.get('color', (255, 255, 255))
        thickness = scoreboard_config.get('thickness', 2)
        
        # Create scoreboard text
        score_text = f"{current_score.get('home', 0)} - {current_score.get('away', 0)}"
        
        # Add background
        text_size = cv2.getTextSize(score_text, font, font_scale, thickness)[0]
        cv2.rectangle(frame, (x - 5, y - text_size[1] - 10), 
                     (x + text_size[0] + 5, y + 5), (0, 0, 0), -1)
        
        # Add text
        cv2.putText(frame, score_text, (x, y), font, font_scale, color, thickness)
        
        return frame
    
    def _add_timer_overlay(self, frame: np.ndarray, timer_config: Dict, 
                          timestamp: float) -> np.ndarray:
        """Add timer overlay to frame."""
        # Position and styling
        x, y = timer_config.get('position', (frame.shape[1] - 150, 30))
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = timer_config.get('font_scale', 0.8)
        color = timer_config.get('color', (255, 255, 255))
        thickness = timer_config.get('thickness', 2)
        
        # Format time
        minutes = int(timestamp // 60)
        seconds = int(timestamp % 60)
        time_text = f"{minutes:02d}:{seconds:02d}"
        
        # Add background
        text_size = cv2.getTextSize(time_text, font, font_scale, thickness)[0]
        cv2.rectangle(frame, (x - 5, y - text_size[1] - 10), 
                     (x + text_size[0] + 5, y + 5), (0, 0, 0), -1)
        
        # Add text
        cv2.putText(frame, time_text, (x, y), font, font_scale, color, thickness)
        
        return frame
    
    def _add_text_overlay(self, frame: np.ndarray, text_config: Dict) -> np.ndarray:
        """Add custom text overlay to frame."""
        text = text_config.get('text', '')
        position = text_config.get('position', (10, 50))
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = text_config.get('font_scale', 0.7)
        color = text_config.get('color', (255, 255, 255))
        thickness = text_config.get('thickness', 2)
        background_color = text_config.get('background_color')
        
        # Add background if specified
        if background_color:
            text_size = cv2.getTextSize(text, font, font_scale, thickness)[0]
            x, y = position
            cv2.rectangle(frame, (x - 5, y - text_size[1] - 10), 
                         (x + text_size[0] + 5, y + 5), background_color, -1)
        
        # Add text
        cv2.putText(frame, text, position, font, font_scale, color, thickness)
        
        return frame
    
    def _get_score_at_timestamp(self, scoreboard_config: Dict, timestamp: float) -> Dict:
        """Get score data for specific timestamp."""
        score_events = scoreboard_config.get('score_events', [])
        current_score = {'home': 0, 'away': 0}
        
        for event in score_events:
            if event['timestamp'] <= timestamp:
                current_score[event['team']] += event.get('points', 1)
        
        return current_score
    
    def _should_show_overlay(self, overlay_config: Dict, timestamp: float) -> bool:
        """Check if overlay should be shown at current timestamp."""
        start_time = overlay_config.get('start_time', 0)
        end_time = overlay_config.get('end_time', float('inf'))
        
        return start_time <= timestamp <= end_time
    
    def cleanup(self):
        """Clean up temporary files."""
        try:
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
            self.logger.info("Temporary files cleaned up")
        except Exception as e:
            self.logger.warning(f"Error cleaning up temp files: {str(e)}")
    
    def __del__(self):
        """Cleanup on deletion."""
        self.cleanup()