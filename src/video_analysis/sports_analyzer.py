import cv2
import numpy as np
from typing import List, Dict, Tuple, Optional, Any, Callable
import logging
from dataclasses import dataclass
from pathlib import Path
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# Import our custom modules
from ..video_analysis.video_processor import VideoProcessor, VideoMetadata
from ..models.detection_engine import DetectionEngine, FrameDetections
from ..tracking.multi_object_tracker import MultiObjectTracker, TrackingResult
from ..annotations.annotation_engine import AnnotationEngine
from ..export.video_exporter import VideoExporter, ExportSettings

@dataclass
class AnalysisSettings:
    """Settings for sports video analysis."""
    # Detection settings
    detection_confidence: float = 0.5
    detection_model: str = 'yolov8n.pt'
    
    # Tracking settings
    tracking_max_disappeared: int = 30
    tracking_min_hits: int = 3
    iou_threshold: float = 0.3
    
    # Processing settings
    frame_skip: int = 1  # Process every nth frame
    batch_size: int = 8
    use_gpu: bool = True
    
    # Analysis settings
    enable_event_detection: bool = True
    enable_heatmap_generation: bool = True
    enable_trajectory_analysis: bool = True
    enable_metrics_calculation: bool = True
    
    # Export settings
    export_annotated_video: bool = True
    export_data_files: bool = True
    export_highlight_reel: bool = False

@dataclass
class SportsEvent:
    """Represents a sports event detected in the video."""
    event_type: str  # 'pass', 'shot', 'tackle', 'dribble', etc.
    timestamp: float
    frame_id: int
    player_id: int
    position: Tuple[int, int]
    success: bool
    confidence: float
    metadata: Dict[str, Any]

@dataclass
class AnalysisResult:
    """Complete analysis result for a sports video."""
    video_metadata: VideoMetadata
    frame_detections: List[FrameDetections]
    tracking_results: List[TrackingResult]
    events: List[SportsEvent]
    metrics: Dict[str, Any]
    processing_time: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for JSON serialization."""
        return {
            'video_metadata': {
                'filename': self.video_metadata.filename,
                'duration': self.video_metadata.duration,
                'fps': self.video_metadata.fps,
                'width': self.video_metadata.width,
                'height': self.video_metadata.height,
                'total_frames': self.video_metadata.total_frames,
                'format': self.video_metadata.format
            },
            'events': [
                {
                    'event_type': event.event_type,
                    'timestamp': event.timestamp,
                    'frame_id': event.frame_id,
                    'player_id': event.player_id,
                    'position': event.position,
                    'success': event.success,
                    'confidence': event.confidence,
                    'metadata': event.metadata
                }
                for event in self.events
            ],
            'metrics': self.metrics,
            'processing_time': self.processing_time
        }

class SportsAnalyzer:
    """Comprehensive sports video analysis pipeline."""
    
    def __init__(self, settings: AnalysisSettings = None):
        """Initialize the sports analyzer."""
        self.settings = settings or AnalysisSettings()
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.video_processor = None
        self.detection_engine = None
        self.tracker = None
        self.annotation_engine = None
        self.video_exporter = None
        
        # Analysis state
        self.current_analysis = None
        self.analysis_progress = 0.0
        self.is_analyzing = False
        self.analysis_thread = None
        
        # Setup logging
        self._setup_logging()
    
    def _setup_logging(self):
        """Setup logging configuration."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('sports_analysis.log'),
                logging.StreamHandler()
            ]
        )
    
    def initialize_components(self):
        """Initialize all analysis components."""
        try:
            # Initialize detection engine
            self.detection_engine = DetectionEngine(
                model_path=self.settings.detection_model,
                confidence_threshold=self.settings.detection_confidence
            )
            
            # Initialize tracker
            self.tracker = MultiObjectTracker(
                max_disappeared=self.settings.tracking_max_disappeared,
                min_hits=self.settings.tracking_min_hits
            )
            
            # Initialize annotation engine
            self.annotation_engine = AnnotationEngine()
            
            # Initialize video exporter
            self.video_exporter = VideoExporter()
            
            self.logger.info("All components initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Error initializing components: {str(e)}")
            raise
    
    def analyze_video(self, video_path: str, output_dir: str = None, 
                     progress_callback: Optional[Callable[[float], None]] = None) -> AnalysisResult:
        """
        Perform comprehensive analysis of a sports video.
        
        Args:
            video_path: Path to the video file
            output_dir: Directory to save outputs (optional)
            progress_callback: Callback function for progress updates
        
        Returns:
            Complete analysis result
        """
        if self.is_analyzing:
            raise RuntimeError("Analysis already in progress")
        
        self.is_analyzing = True
        start_time = time.time()
        
        try:
            # Initialize components if not already done
            if self.detection_engine is None:
                self.initialize_components()
            
            # Create output directory
            if output_dir:
                output_path = Path(output_dir)
                output_path.mkdir(parents=True, exist_ok=True)
            else:
                output_path = Path(video_path).parent / "analysis_output"
                output_path.mkdir(parents=True, exist_ok=True)
            
            # Initialize video processor
            self.video_processor = VideoProcessor(video_path)
            video_metadata = self.video_processor.load_video()
            
            self.logger.info(f"Starting analysis of {video_metadata.filename}")
            
            # Step 1: Detection and tracking
            self._update_progress(0.1, "Detecting objects...", progress_callback)
            frame_detections, tracking_results = self._detect_and_track()
            
            # Step 2: Event detection
            self._update_progress(0.6, "Detecting events...", progress_callback)
            events = self._detect_events(frame_detections, tracking_results)
            
            # Step 3: Metrics calculation
            self._update_progress(0.8, "Calculating metrics...", progress_callback)
            metrics = self._calculate_metrics(frame_detections, tracking_results, events)
            
            # Step 4: Generate annotations
            self._update_progress(0.9, "Generating annotations...", progress_callback)
            self._generate_annotations(frame_detections, tracking_results, events)
            
            # Step 5: Export results
            self._update_progress(0.95, "Exporting results...", progress_callback)
            self._export_results(video_path, str(output_path), frame_detections, tracking_results, events, metrics)
            
            # Create final result
            processing_time = time.time() - start_time
            result = AnalysisResult(
                video_metadata=video_metadata,
                frame_detections=frame_detections,
                tracking_results=tracking_results,
                events=events,
                metrics=metrics,
                processing_time=processing_time
            )
            
            self._update_progress(1.0, "Analysis complete!", progress_callback)
            self.logger.info(f"Analysis completed in {processing_time:.2f} seconds")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error during analysis: {str(e)}")
            raise
        finally:
            self.is_analyzing = False
            if self.video_processor:
                self.video_processor.close()
    
    def _detect_and_track(self) -> Tuple[List[FrameDetections], List[TrackingResult]]:
        """Perform object detection and tracking on video frames."""
        frame_detections = []
        tracking_results = []
        
        # Process frames
        frame_generator = self.video_processor.get_frame_generator(skip_frames=self.settings.frame_skip)
        
        for frame_id, frame in frame_generator:
            # Detect objects
            timestamp = frame_id / self.video_processor.metadata.fps
            detections = self.detection_engine.detect_frame(frame, frame_id, timestamp)
            frame_detections.append(detections)
            
            # Update tracker
            detection_list = []
            for detection in detections.detections:
                detection_list.append({
                    'bbox': detection.bbox,
                    'confidence': detection.confidence,
                    'class_name': detection.class_name,
                    'center': detection.center
                })
            
            tracking_result = self.tracker.update(detection_list, frame_id, timestamp)
            tracking_results.append(tracking_result)
            
            # Log progress occasionally
            if frame_id % 100 == 0:
                self.logger.info(f"Processed frame {frame_id}")
        
        return frame_detections, tracking_results
    
    def _detect_events(self, frame_detections: List[FrameDetections], 
                      tracking_results: List[TrackingResult]) -> List[SportsEvent]:
        """Detect sports events based on detections and tracking."""
        events = []
        
        if not self.settings.enable_event_detection:
            return events
        
        # Simple event detection based on player and ball interactions
        for i, (detections, tracking) in enumerate(zip(frame_detections, tracking_results)):
            timestamp = detections.timestamp
            
            # Detect pass events (ball movement between players)
            pass_events = self._detect_pass_events(detections, tracking, i)
            events.extend(pass_events)
            
            # Detect shot events (ball moving towards goal area)
            shot_events = self._detect_shot_events(detections, tracking, i)
            events.extend(shot_events)
            
            # Detect dribble events (player controlling ball)
            dribble_events = self._detect_dribble_events(detections, tracking, i)
            events.extend(dribble_events)
        
        return events
    
    def _detect_pass_events(self, detections: FrameDetections, tracking: TrackingResult, 
                           frame_idx: int) -> List[SportsEvent]:
        """Detect pass events in the frame."""
        events = []
        
        # Simple pass detection: ball near player then moving away
        if detections.balls and len(tracking.active_tracks) >= 2:
            ball = detections.balls[0]
            
            # Find closest player to ball
            closest_player = None
            min_distance = float('inf')
            
            for track in tracking.active_tracks:
                if track.class_name == 'person':
                    distance = np.sqrt((ball.center[0] - track.center[0])**2 + 
                                     (ball.center[1] - track.center[1])**2)
                    if distance < min_distance:
                        min_distance = distance
                        closest_player = track
            
            # If ball is close to player and player is moving, it might be a pass
            if closest_player and min_distance < 100:
                velocity_magnitude = np.sqrt(closest_player.velocity[0]**2 + closest_player.velocity[1]**2)
                if velocity_magnitude > 5:  # Arbitrary threshold
                    event = SportsEvent(
                        event_type='pass',
                        timestamp=detections.timestamp,
                        frame_id=frame_idx,
                        player_id=closest_player.track_id,
                        position=closest_player.center,
                        success=True,  # Would need more sophisticated logic
                        confidence=0.7,
                        metadata={'distance_to_ball': min_distance}
                    )
                    events.append(event)
        
        return events
    
    def _detect_shot_events(self, detections: FrameDetections, tracking: TrackingResult, 
                           frame_idx: int) -> List[SportsEvent]:
        """Detect shot events in the frame."""
        events = []
        
        # Simple shot detection: ball moving fast towards goal area
        if detections.balls:
            ball = detections.balls[0]
            
            # Find closest player to ball
            closest_player = None
            min_distance = float('inf')
            
            for track in tracking.active_tracks:
                if track.class_name == 'person':
                    distance = np.sqrt((ball.center[0] - track.center[0])**2 + 
                                     (ball.center[1] - track.center[1])**2)
                    if distance < min_distance:
                        min_distance = distance
                        closest_player = track
            
            # Check if ball is moving towards goal area (simple heuristic)
            if closest_player and min_distance < 80:
                # Assume goal is at the edges of the frame
                frame_width = self.video_processor.metadata.width
                is_towards_goal = (ball.center[0] < frame_width * 0.1 or 
                                 ball.center[0] > frame_width * 0.9)
                
                if is_towards_goal:
                    event = SportsEvent(
                        event_type='shot',
                        timestamp=detections.timestamp,
                        frame_id=frame_idx,
                        player_id=closest_player.track_id,
                        position=closest_player.center,
                        success=True,  # Would need goal detection
                        confidence=0.6,
                        metadata={'ball_position': ball.center}
                    )
                    events.append(event)
        
        return events
    
    def _detect_dribble_events(self, detections: FrameDetections, tracking: TrackingResult, 
                              frame_idx: int) -> List[SportsEvent]:
        """Detect dribble events in the frame."""
        events = []
        
        # Simple dribble detection: player moving with ball nearby
        if detections.balls:
            ball = detections.balls[0]
            
            for track in tracking.active_tracks:
                if track.class_name == 'person':
                    distance = np.sqrt((ball.center[0] - track.center[0])**2 + 
                                     (ball.center[1] - track.center[1])**2)
                    velocity_magnitude = np.sqrt(track.velocity[0]**2 + track.velocity[1]**2)
                    
                    # If player is moving with ball close by
                    if distance < 60 and velocity_magnitude > 3:
                        event = SportsEvent(
                            event_type='dribble',
                            timestamp=detections.timestamp,
                            frame_id=frame_idx,
                            player_id=track.track_id,
                            position=track.center,
                            success=True,
                            confidence=0.8,
                            metadata={'ball_distance': distance, 'velocity': velocity_magnitude}
                        )
                        events.append(event)
        
        return events
    
    def _calculate_metrics(self, frame_detections: List[FrameDetections], 
                          tracking_results: List[TrackingResult], 
                          events: List[SportsEvent]) -> Dict[str, Any]:
        """Calculate comprehensive metrics from analysis results."""
        metrics = {}
        
        if not self.settings.enable_metrics_calculation:
            return metrics
        
        # Basic counts
        total_players = len(set(track.track_id for result in tracking_results for track in result.active_tracks if track.class_name == 'person'))
        total_events = len(events)
        
        # Event statistics
        event_counts = {}
        for event in events:
            event_counts[event.event_type] = event_counts.get(event.event_type, 0) + 1
        
        # Player statistics
        player_stats = {}
        for event in events:
            if event.player_id not in player_stats:
                player_stats[event.player_id] = {
                    'total_events': 0,
                    'successful_events': 0,
                    'event_types': {}
                }
            
            player_stats[event.player_id]['total_events'] += 1
            if event.success:
                player_stats[event.player_id]['successful_events'] += 1
            
            event_type = event.event_type
            if event_type not in player_stats[event.player_id]['event_types']:
                player_stats[event.player_id]['event_types'][event_type] = 0
            player_stats[event.player_id]['event_types'][event_type] += 1
        
        # Detection statistics
        detection_stats = self.detection_engine.get_detection_statistics(frame_detections)
        
        # Tracking statistics
        tracking_stats = self.tracker.get_track_statistics(tracking_results)
        
        metrics = {
            'video_duration': self.video_processor.metadata.duration,
            'total_frames_analyzed': len(frame_detections),
            'total_players_detected': total_players,
            'total_events_detected': total_events,
            'event_counts': event_counts,
            'player_statistics': player_stats,
            'detection_statistics': detection_stats,
            'tracking_statistics': tracking_stats,
            'success_rates': {
                event_type: len([e for e in events if e.event_type == event_type and e.success]) / len([e for e in events if e.event_type == event_type])
                for event_type in event_counts.keys()
                if len([e for e in events if e.event_type == event_type]) > 0
            }
        }
        
        return metrics
    
    def _generate_annotations(self, frame_detections: List[FrameDetections], 
                             tracking_results: List[TrackingResult], 
                             events: List[SportsEvent]):
        """Generate annotations for visualization."""
        self.annotation_engine.clear_annotations()
        
        # Add event annotations
        for event in events:
            self.annotation_engine.add_event_annotation(
                event_type=event.event_type,
                player_id=event.player_id,
                position=event.position,
                timestamp=event.timestamp,
                frame_id=event.frame_id,
                success=event.success,
                metadata=event.metadata
            )
        
        # Add trajectory annotations for tracked players
        if self.settings.enable_trajectory_analysis:
            player_trajectories = {}
            for result in tracking_results:
                for track in result.active_tracks:
                    if track.class_name == 'person':
                        if track.track_id not in player_trajectories:
                            player_trajectories[track.track_id] = []
                        player_trajectories[track.track_id].append(track.center)
            
            # Add trajectory annotations
            for player_id, trajectory in player_trajectories.items():
                if len(trajectory) > 1:
                    self.annotation_engine.add_trajectory_annotation(
                        points=trajectory,
                        timestamp=0,  # Will be visible throughout
                        frame_id=0
                    )
        
        # Generate heatmaps if enabled
        if self.settings.enable_heatmap_generation:
            self._generate_heatmaps(tracking_results)
    
    def _generate_heatmaps(self, tracking_results: List[TrackingResult]):
        """Generate heatmaps for player positioning."""
        player_positions = {}
        
        for result in tracking_results:
            for track in result.active_tracks:
                if track.class_name == 'person':
                    if track.track_id not in player_positions:
                        player_positions[track.track_id] = []
                    player_positions[track.track_id].append(track.center)
        
        # Create heatmaps for each player
        for player_id, positions in player_positions.items():
            if len(positions) > 10:  # Only create heatmap if enough data
                heatmap_data = self.annotation_engine.create_player_heatmap(
                    trajectory_points=positions,
                    frame_width=self.video_processor.metadata.width,
                    frame_height=self.video_processor.metadata.height
                )
                
                self.annotation_engine.add_heatmap_annotation(
                    heatmap_data=heatmap_data,
                    position=(0, 0),
                    timestamp=0,
                    frame_id=0
                )
    
    def _export_results(self, input_video_path: str, output_dir: str, 
                       frame_detections: List[FrameDetections], 
                       tracking_results: List[TrackingResult], 
                       events: List[SportsEvent], 
                       metrics: Dict[str, Any]):
        """Export all analysis results."""
        output_path = Path(output_dir)
        
        # Export data files
        if self.settings.export_data_files:
            # Export detections
            self.detection_engine.save_detections_to_json(
                frame_detections, str(output_path / 'detections.json')
            )
            
            # Export annotations
            self.annotation_engine.export_annotations(
                str(output_path / 'annotations.json')
            )
            
            # Export events
            events_data = [
                {
                    'event_type': event.event_type,
                    'timestamp': event.timestamp,
                    'frame_id': event.frame_id,
                    'player_id': event.player_id,
                    'position': event.position,
                    'success': event.success,
                    'confidence': event.confidence,
                    'metadata': event.metadata
                }
                for event in events
            ]
            
            with open(output_path / 'events.json', 'w') as f:
                json.dump(events_data, f, indent=2)
            
            # Export metrics
            with open(output_path / 'metrics.json', 'w') as f:
                json.dump(metrics, f, indent=2)
        
        # Export annotated video
        if self.settings.export_annotated_video:
            self._export_annotated_video(input_video_path, str(output_path / 'annotated_video.mp4'))
        
        # Export highlight reel
        if self.settings.export_highlight_reel:
            self._export_highlight_reel(input_video_path, str(output_path / 'highlights.mp4'), events)
    
    def _export_annotated_video(self, input_video_path: str, output_path: str):
        """Export video with all annotations."""
        def frame_processor(frame: np.ndarray, frame_idx: int, timestamp: float) -> np.ndarray:
            """Process frame with annotations."""
            # Apply all annotations
            annotated_frame = self.annotation_engine.apply_annotations(frame, timestamp, frame_idx)
            
            # Add metrics overlay
            current_metrics = {
                'Frame': frame_idx,
                'Time': f"{timestamp:.2f}s",
                'Players': len([t for t in self.tracker.trackers if t.hits >= 3])
            }
            annotated_frame = self.annotation_engine.create_metrics_overlay(annotated_frame, current_metrics)
            
            return annotated_frame
        
        export_settings = ExportSettings(quality='high', include_audio=True)
        success = self.video_exporter.export_annotated_video(
            input_video_path, output_path, frame_processor, export_settings
        )
        
        if success:
            self.logger.info(f"Annotated video exported to: {output_path}")
        else:
            self.logger.error("Failed to export annotated video")
    
    def _export_highlight_reel(self, input_video_path: str, output_path: str, events: List[SportsEvent]):
        """Export highlight reel with important events."""
        # Create highlight segments around events
        highlight_segments = []
        
        for event in events:
            if event.event_type in ['shot', 'pass']:  # Only include important events
                start_time = max(0, event.timestamp - 2)  # 2 seconds before
                end_time = event.timestamp + 3  # 3 seconds after
                highlight_segments.append((start_time, end_time))
        
        if highlight_segments:
            success = self.video_exporter.create_highlight_reel(
                input_video_path, output_path, highlight_segments
            )
            
            if success:
                self.logger.info(f"Highlight reel exported to: {output_path}")
            else:
                self.logger.error("Failed to export highlight reel")
    
    def _update_progress(self, progress: float, message: str, callback: Optional[Callable]):
        """Update analysis progress."""
        self.analysis_progress = progress
        self.logger.info(f"Progress: {progress*100:.1f}% - {message}")
        
        if callback:
            callback(progress)
    
    def get_analysis_summary(self, result: AnalysisResult) -> Dict[str, Any]:
        """Get a summary of the analysis results."""
        return {
            'video_info': {
                'filename': result.video_metadata.filename,
                'duration': f"{result.video_metadata.duration:.2f}s",
                'resolution': f"{result.video_metadata.width}x{result.video_metadata.height}",
                'fps': result.video_metadata.fps
            },
            'detection_summary': {
                'total_detections': sum(len(fd.detections) for fd in result.frame_detections),
                'avg_players_per_frame': result.metrics.get('detection_statistics', {}).get('avg_players_per_frame', 0),
                'avg_balls_per_frame': result.metrics.get('detection_statistics', {}).get('avg_balls_per_frame', 0)
            },
            'event_summary': {
                'total_events': len(result.events),
                'event_types': result.metrics.get('event_counts', {}),
                'success_rates': result.metrics.get('success_rates', {})
            },
            'processing_info': {
                'processing_time': f"{result.processing_time:.2f}s",
                'frames_processed': len(result.frame_detections)
            }
        }
    
    def cleanup(self):
        """Clean up resources."""
        if self.video_processor:
            self.video_processor.close()
        if self.video_exporter:
            self.video_exporter.cleanup()
        if self.tracker:
            self.tracker.reset()
        if self.annotation_engine:
            self.annotation_engine.clear_annotations()
        
        self.logger.info("Sports analyzer cleaned up")