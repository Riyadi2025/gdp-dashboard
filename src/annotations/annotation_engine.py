import cv2
import numpy as np
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle, FancyBboxPatch
import matplotlib.patches as mpatches
from PIL import Image, ImageDraw, ImageFont
import logging
import json
from pathlib import Path
import seaborn as sns

@dataclass
class Annotation:
    """Base class for all annotations."""
    type: str
    position: Tuple[int, int]
    timestamp: float
    frame_id: int
    duration: float = 0.0  # How long to show annotation
    color: Tuple[int, int, int] = (255, 255, 255)
    thickness: int = 2
    font_scale: float = 0.7
    alpha: float = 1.0

@dataclass
class TextAnnotation(Annotation):
    """Text annotation with customizable styling."""
    text: str
    background_color: Optional[Tuple[int, int, int]] = None
    font_type: int = cv2.FONT_HERSHEY_SIMPLEX

@dataclass
class LineAnnotation(Annotation):
    """Line annotation for trajectories and arrows."""
    start_point: Tuple[int, int]
    end_point: Tuple[int, int]
    arrow: bool = False

@dataclass
class CircleAnnotation(Annotation):
    """Circle annotation for highlighting areas."""
    radius: int
    filled: bool = False

@dataclass
class RectangleAnnotation(Annotation):
    """Rectangle annotation for bounding boxes."""
    width: int
    height: int
    filled: bool = False

@dataclass
class HeatmapAnnotation(Annotation):
    """Heatmap annotation for player positioning."""
    data: np.ndarray
    colormap: str = 'hot'
    overlay_alpha: float = 0.6

@dataclass
class EventAnnotation(Annotation):
    """Event annotation for sports events."""
    event_type: str  # 'pass', 'shot', 'tackle', 'dribble', etc.
    player_id: int
    success: bool
    metadata: Dict[str, Any] = None

class AnnotationEngine:
    """Advanced annotation engine for sports video analysis."""
    
    # Predefined colors for different annotation types
    COLORS = {
        'player': (0, 255, 0),      # Green
        'ball': (0, 0, 255),        # Red
        'pass': (255, 255, 0),      # Yellow
        'shot': (255, 0, 0),        # Blue
        'tackle': (0, 255, 255),    # Cyan
        'dribble': (255, 0, 255),   # Magenta
        'success': (0, 255, 0),     # Green
        'failure': (0, 0, 255),     # Red
        'neutral': (255, 255, 255), # White
        'trajectory': (255, 255, 0), # Yellow
        'heatmap': (255, 0, 0),     # Red base for heatmap
    }
    
    def __init__(self, font_path: Optional[str] = None):
        """Initialize the annotation engine."""
        self.annotations = []
        self.font_path = font_path
        self.logger = logging.getLogger(__name__)
        
        # Load custom font if provided
        try:
            if font_path and Path(font_path).exists():
                self.pil_font = ImageFont.truetype(font_path, 20)
            else:
                self.pil_font = ImageFont.load_default()
        except Exception as e:
            self.logger.warning(f"Could not load custom font: {e}")
            self.pil_font = ImageFont.load_default()
    
    def add_text_annotation(self, text: str, position: Tuple[int, int], timestamp: float, 
                           frame_id: int, color: Tuple[int, int, int] = None, 
                           background_color: Tuple[int, int, int] = None, 
                           duration: float = 1.0) -> TextAnnotation:
        """Add a text annotation."""
        if color is None:
            color = self.COLORS['neutral']
        
        annotation = TextAnnotation(
            type='text',
            position=position,
            timestamp=timestamp,
            frame_id=frame_id,
            duration=duration,
            color=color,
            text=text,
            background_color=background_color
        )
        
        self.annotations.append(annotation)
        return annotation
    
    def add_event_annotation(self, event_type: str, player_id: int, position: Tuple[int, int],
                            timestamp: float, frame_id: int, success: bool, 
                            metadata: Dict[str, Any] = None) -> EventAnnotation:
        """Add a sports event annotation."""
        color = self.COLORS.get(event_type, self.COLORS['neutral'])
        if not success:
            color = self.COLORS['failure']
        
        annotation = EventAnnotation(
            type='event',
            position=position,
            timestamp=timestamp,
            frame_id=frame_id,
            color=color,
            event_type=event_type,
            player_id=player_id,
            success=success,
            metadata=metadata or {}
        )
        
        self.annotations.append(annotation)
        return annotation
    
    def add_trajectory_annotation(self, points: List[Tuple[int, int]], timestamp: float, 
                                 frame_id: int, color: Tuple[int, int, int] = None) -> List[LineAnnotation]:
        """Add a trajectory annotation connecting multiple points."""
        if color is None:
            color = self.COLORS['trajectory']
        
        trajectory_annotations = []
        for i in range(len(points) - 1):
            annotation = LineAnnotation(
                type='trajectory',
                position=points[i],
                timestamp=timestamp,
                frame_id=frame_id,
                color=color,
                start_point=points[i],
                end_point=points[i + 1]
            )
            trajectory_annotations.append(annotation)
            self.annotations.append(annotation)
        
        return trajectory_annotations
    
    def add_arrow_annotation(self, start_point: Tuple[int, int], end_point: Tuple[int, int],
                            timestamp: float, frame_id: int, 
                            color: Tuple[int, int, int] = None) -> LineAnnotation:
        """Add an arrow annotation."""
        if color is None:
            color = self.COLORS['neutral']
        
        annotation = LineAnnotation(
            type='arrow',
            position=start_point,
            timestamp=timestamp,
            frame_id=frame_id,
            color=color,
            start_point=start_point,
            end_point=end_point,
            arrow=True
        )
        
        self.annotations.append(annotation)
        return annotation
    
    def add_circle_annotation(self, center: Tuple[int, int], radius: int, timestamp: float,
                             frame_id: int, color: Tuple[int, int, int] = None, 
                             filled: bool = False) -> CircleAnnotation:
        """Add a circle annotation."""
        if color is None:
            color = self.COLORS['neutral']
        
        annotation = CircleAnnotation(
            type='circle',
            position=center,
            timestamp=timestamp,
            frame_id=frame_id,
            color=color,
            radius=radius,
            filled=filled
        )
        
        self.annotations.append(annotation)
        return annotation
    
    def add_heatmap_annotation(self, heatmap_data: np.ndarray, position: Tuple[int, int],
                              timestamp: float, frame_id: int, 
                              colormap: str = 'hot', alpha: float = 0.6) -> HeatmapAnnotation:
        """Add a heatmap annotation."""
        annotation = HeatmapAnnotation(
            type='heatmap',
            position=position,
            timestamp=timestamp,
            frame_id=frame_id,
            data=heatmap_data,
            colormap=colormap,
            overlay_alpha=alpha
        )
        
        self.annotations.append(annotation)
        return annotation
    
    def create_player_heatmap(self, trajectory_points: List[Tuple[int, int]], 
                             frame_width: int, frame_height: int, 
                             grid_size: int = 50) -> np.ndarray:
        """Create a heatmap from player trajectory points."""
        # Create a grid for the heatmap
        grid_x = frame_width // grid_size
        grid_y = frame_height // grid_size
        heatmap = np.zeros((grid_y, grid_x))
        
        # Count occurrences in each grid cell
        for x, y in trajectory_points:
            grid_i = min(int(y // grid_size), grid_y - 1)
            grid_j = min(int(x // grid_size), grid_x - 1)
            heatmap[grid_i, grid_j] += 1
        
        # Apply Gaussian blur for smoothing
        from scipy.ndimage import gaussian_filter
        heatmap = gaussian_filter(heatmap, sigma=1.0)
        
        # Normalize
        if heatmap.max() > 0:
            heatmap = heatmap / heatmap.max()
        
        return heatmap
    
    def apply_annotations(self, frame: np.ndarray, current_timestamp: float, 
                         current_frame_id: int) -> np.ndarray:
        """Apply all relevant annotations to a frame."""
        annotated_frame = frame.copy()
        
        # Filter annotations for current frame/timestamp
        active_annotations = []
        for ann in self.annotations:
            if ann.frame_id == current_frame_id or \
               (ann.timestamp <= current_timestamp <= ann.timestamp + ann.duration):
                active_annotations.append(ann)
        
        # Apply annotations by type
        for ann in active_annotations:
            if isinstance(ann, TextAnnotation):
                annotated_frame = self._draw_text(annotated_frame, ann)
            elif isinstance(ann, LineAnnotation):
                annotated_frame = self._draw_line(annotated_frame, ann)
            elif isinstance(ann, CircleAnnotation):
                annotated_frame = self._draw_circle(annotated_frame, ann)
            elif isinstance(ann, RectangleAnnotation):
                annotated_frame = self._draw_rectangle(annotated_frame, ann)
            elif isinstance(ann, HeatmapAnnotation):
                annotated_frame = self._draw_heatmap(annotated_frame, ann)
            elif isinstance(ann, EventAnnotation):
                annotated_frame = self._draw_event(annotated_frame, ann)
        
        return annotated_frame
    
    def _draw_text(self, frame: np.ndarray, annotation: TextAnnotation) -> np.ndarray:
        """Draw text annotation on frame."""
        x, y = annotation.position
        
        # Draw background if specified
        if annotation.background_color:
            text_size = cv2.getTextSize(annotation.text, annotation.font_type, 
                                      annotation.font_scale, annotation.thickness)[0]
            cv2.rectangle(frame, (x, y - text_size[1] - 10), 
                         (x + text_size[0], y), annotation.background_color, -1)
        
        # Draw text
        cv2.putText(frame, annotation.text, (x, y), annotation.font_type, 
                   annotation.font_scale, annotation.color, annotation.thickness)
        
        return frame
    
    def _draw_line(self, frame: np.ndarray, annotation: LineAnnotation) -> np.ndarray:
        """Draw line or arrow annotation on frame."""
        if annotation.arrow:
            # Draw arrow
            cv2.arrowedLine(frame, annotation.start_point, annotation.end_point, 
                           annotation.color, annotation.thickness)
        else:
            # Draw line
            cv2.line(frame, annotation.start_point, annotation.end_point, 
                    annotation.color, annotation.thickness)
        
        return frame
    
    def _draw_circle(self, frame: np.ndarray, annotation: CircleAnnotation) -> np.ndarray:
        """Draw circle annotation on frame."""
        thickness = -1 if annotation.filled else annotation.thickness
        cv2.circle(frame, annotation.position, annotation.radius, 
                  annotation.color, thickness)
        
        return frame
    
    def _draw_rectangle(self, frame: np.ndarray, annotation: RectangleAnnotation) -> np.ndarray:
        """Draw rectangle annotation on frame."""
        x, y = annotation.position
        x2 = x + annotation.width
        y2 = y + annotation.height
        
        thickness = -1 if annotation.filled else annotation.thickness
        cv2.rectangle(frame, (x, y), (x2, y2), annotation.color, thickness)
        
        return frame
    
    def _draw_heatmap(self, frame: np.ndarray, annotation: HeatmapAnnotation) -> np.ndarray:
        """Draw heatmap annotation on frame."""
        # Convert heatmap to color image
        colormap = plt.cm.get_cmap(annotation.colormap)
        colored_heatmap = colormap(annotation.data)
        colored_heatmap = (colored_heatmap * 255).astype(np.uint8)
        
        # Resize heatmap to match frame size
        h, w = frame.shape[:2]
        heatmap_resized = cv2.resize(colored_heatmap, (w, h))
        
        # Apply alpha blending
        alpha = annotation.overlay_alpha
        blended = cv2.addWeighted(frame, 1 - alpha, heatmap_resized[:, :, :3], alpha, 0)
        
        return blended
    
    def _draw_event(self, frame: np.ndarray, annotation: EventAnnotation) -> np.ndarray:
        """Draw event annotation on frame."""
        x, y = annotation.position
        
        # Create event label
        success_text = "✓" if annotation.success else "✗"
        event_text = f"P{annotation.player_id} {annotation.event_type} {success_text}"
        
        # Draw background
        text_size = cv2.getTextSize(event_text, cv2.FONT_HERSHEY_SIMPLEX, 
                                   annotation.font_scale, annotation.thickness)[0]
        
        # Choose background color based on success
        bg_color = (0, 100, 0) if annotation.success else (0, 0, 100)
        cv2.rectangle(frame, (x, y - text_size[1] - 10), 
                     (x + text_size[0] + 10, y), bg_color, -1)
        
        # Draw text
        cv2.putText(frame, event_text, (x + 5, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 
                   annotation.font_scale, annotation.color, annotation.thickness)
        
        return frame
    
    def create_metrics_overlay(self, frame: np.ndarray, metrics: Dict[str, Any], 
                              position: Tuple[int, int] = (10, 30)) -> np.ndarray:
        """Create a metrics overlay panel on the frame."""
        overlay_frame = frame.copy()
        x, y = position
        
        # Create semi-transparent background
        overlay = overlay_frame.copy()
        cv2.rectangle(overlay, (x - 5, y - 25), (x + 300, y + len(metrics) * 25), 
                     (0, 0, 0), -1)
        alpha = 0.7
        overlay_frame = cv2.addWeighted(overlay_frame, alpha, overlay, 1 - alpha, 0)
        
        # Add metrics text
        for i, (key, value) in enumerate(metrics.items()):
            text = f"{key}: {value}"
            cv2.putText(overlay_frame, text, (x, y + i * 25), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        return overlay_frame
    
    def create_timeline_overlay(self, frame: np.ndarray, events: List[Dict], 
                               current_time: float, total_time: float) -> np.ndarray:
        """Create a timeline overlay showing events."""
        overlay_frame = frame.copy()
        
        # Timeline dimensions
        timeline_height = 40
        timeline_width = frame.shape[1] - 100
        timeline_x = 50
        timeline_y = frame.shape[0] - 60
        
        # Draw timeline background
        cv2.rectangle(overlay_frame, (timeline_x, timeline_y), 
                     (timeline_x + timeline_width, timeline_y + timeline_height), 
                     (50, 50, 50), -1)
        
        # Draw timeline border
        cv2.rectangle(overlay_frame, (timeline_x, timeline_y), 
                     (timeline_x + timeline_width, timeline_y + timeline_height), 
                     (255, 255, 255), 2)
        
        # Draw current time marker
        current_x = int(timeline_x + (current_time / total_time) * timeline_width)
        cv2.line(overlay_frame, (current_x, timeline_y), 
                (current_x, timeline_y + timeline_height), (0, 255, 0), 3)
        
        # Draw events on timeline
        for event in events:
            event_time = event.get('timestamp', 0)
            event_x = int(timeline_x + (event_time / total_time) * timeline_width)
            
            # Choose color based on event type
            event_color = self.COLORS.get(event.get('type', 'neutral'), (255, 255, 255))
            
            # Draw event marker
            cv2.circle(overlay_frame, (event_x, timeline_y + timeline_height // 2), 
                      5, event_color, -1)
        
        return overlay_frame
    
    def export_annotations(self, output_path: str):
        """Export annotations to JSON file."""
        data = []
        for ann in self.annotations:
            ann_data = {
                'type': ann.type,
                'position': ann.position,
                'timestamp': ann.timestamp,
                'frame_id': ann.frame_id,
                'duration': ann.duration,
                'color': ann.color,
                'thickness': ann.thickness,
                'font_scale': ann.font_scale,
                'alpha': ann.alpha
            }
            
            # Add type-specific data
            if isinstance(ann, TextAnnotation):
                ann_data['text'] = ann.text
                ann_data['background_color'] = ann.background_color
            elif isinstance(ann, LineAnnotation):
                ann_data['start_point'] = ann.start_point
                ann_data['end_point'] = ann.end_point
                ann_data['arrow'] = ann.arrow
            elif isinstance(ann, CircleAnnotation):
                ann_data['radius'] = ann.radius
                ann_data['filled'] = ann.filled
            elif isinstance(ann, EventAnnotation):
                ann_data['event_type'] = ann.event_type
                ann_data['player_id'] = ann.player_id
                ann_data['success'] = ann.success
                ann_data['metadata'] = ann.metadata
            
            data.append(ann_data)
        
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        self.logger.info(f"Exported {len(data)} annotations to {output_path}")
    
    def clear_annotations(self):
        """Clear all annotations."""
        self.annotations = []
        self.logger.info("Cleared all annotations")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about annotations."""
        stats = {
            'total_annotations': len(self.annotations),
            'annotation_types': {},
            'events': {},
            'duration_range': (0, 0),
            'frame_range': (0, 0)
        }
        
        if self.annotations:
            # Count by type
            for ann in self.annotations:
                stats['annotation_types'][ann.type] = stats['annotation_types'].get(ann.type, 0) + 1
            
            # Count events
            for ann in self.annotations:
                if isinstance(ann, EventAnnotation):
                    stats['events'][ann.event_type] = stats['events'].get(ann.event_type, 0) + 1
            
            # Duration and frame ranges
            timestamps = [ann.timestamp for ann in self.annotations]
            frame_ids = [ann.frame_id for ann in self.annotations]
            stats['duration_range'] = (min(timestamps), max(timestamps))
            stats['frame_range'] = (min(frame_ids), max(frame_ids))
        
        return stats