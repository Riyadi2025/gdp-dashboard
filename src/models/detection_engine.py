import cv2
import numpy as np
from ultralytics import YOLO
from typing import List, Dict, Tuple, Optional
import logging
from dataclasses import dataclass
from pathlib import Path
import torch

@dataclass
class Detection:
    """Represents a single detection with all relevant information."""
    bbox: Tuple[int, int, int, int]  # x1, y1, x2, y2
    confidence: float
    class_id: int
    class_name: str
    center: Tuple[int, int]
    area: float

@dataclass
class FrameDetections:
    """All detections for a single frame."""
    frame_id: int
    timestamp: float
    detections: List[Detection]
    players: List[Detection]
    balls: List[Detection]
    other_objects: List[Detection]

class DetectionEngine:
    """Advanced computer vision engine for sports object detection."""
    
    # Sports-specific class mappings
    SPORTS_CLASSES = {
        'person': 0,
        'sports ball': 32,
        'soccer ball': 32,
        'basketball': 32,
        'tennis ball': 32,
        'football': 32,
        'baseball': 32,
        'volleyball': 32
    }
    
    def __init__(self, model_path: str = 'yolov8n.pt', confidence_threshold: float = 0.5):
        """Initialize the detection engine with YOLOv8 model."""
        self.model_path = model_path
        self.confidence_threshold = confidence_threshold
        self.model = None
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.logger = logging.getLogger(__name__)
        
        # Load model
        self.load_model()
    
    def load_model(self):
        """Load the YOLOv8 model."""
        try:
            self.model = YOLO(self.model_path)
            self.model.to(self.device)
            self.logger.info(f"Loaded YOLO model: {self.model_path} on {self.device}")
            
            # Print available classes
            class_names = self.model.names
            self.logger.info(f"Available classes: {len(class_names)}")
            
        except Exception as e:
            self.logger.error(f"Error loading model: {str(e)}")
            raise
    
    def detect_frame(self, frame: np.ndarray, frame_id: int, timestamp: float) -> FrameDetections:
        """Detect objects in a single frame."""
        if self.model is None:
            raise ValueError("Model not loaded. Call load_model() first.")
        
        # Run inference
        results = self.model(frame, conf=self.confidence_threshold, verbose=False)
        
        detections = []
        players = []
        balls = []
        other_objects = []
        
        # Process results
        for result in results:
            boxes = result.boxes
            
            if boxes is not None:
                for box in boxes:
                    # Extract detection information
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    confidence = box.conf[0].cpu().numpy()
                    class_id = int(box.cls[0].cpu().numpy())
                    class_name = self.model.names[class_id]
                    
                    # Calculate center and area
                    center_x = int((x1 + x2) / 2)
                    center_y = int((y1 + y2) / 2)
                    area = (x2 - x1) * (y2 - y1)
                    
                    detection = Detection(
                        bbox=(int(x1), int(y1), int(x2), int(y2)),
                        confidence=float(confidence),
                        class_id=class_id,
                        class_name=class_name,
                        center=(center_x, center_y),
                        area=area
                    )
                    
                    detections.append(detection)
                    
                    # Categorize detections
                    if class_name == 'person':
                        players.append(detection)
                    elif 'ball' in class_name.lower() or class_name in ['sports ball']:
                        balls.append(detection)
                    else:
                        other_objects.append(detection)
        
        return FrameDetections(
            frame_id=frame_id,
            timestamp=timestamp,
            detections=detections,
            players=players,
            balls=balls,
            other_objects=other_objects
        )
    
    def detect_batch(self, frames: List[np.ndarray], start_frame_id: int = 0, fps: float = 30.0) -> List[FrameDetections]:
        """Detect objects in a batch of frames."""
        batch_detections = []
        
        for i, frame in enumerate(frames):
            frame_id = start_frame_id + i
            timestamp = frame_id / fps
            
            frame_detections = self.detect_frame(frame, frame_id, timestamp)
            batch_detections.append(frame_detections)
        
        return batch_detections
    
    def get_player_detections(self, frame_detections: FrameDetections) -> List[Detection]:
        """Get only player detections from frame detections."""
        return frame_detections.players
    
    def get_ball_detections(self, frame_detections: FrameDetections) -> List[Detection]:
        """Get only ball detections from frame detections."""
        return frame_detections.balls
    
    def filter_detections_by_confidence(self, detections: List[Detection], min_confidence: float) -> List[Detection]:
        """Filter detections by minimum confidence threshold."""
        return [det for det in detections if det.confidence >= min_confidence]
    
    def filter_detections_by_area(self, detections: List[Detection], min_area: float = 100.0, max_area: float = 50000.0) -> List[Detection]:
        """Filter detections by bounding box area."""
        return [det for det in detections if min_area <= det.area <= max_area]
    
    def get_detection_statistics(self, frame_detections: List[FrameDetections]) -> Dict:
        """Get statistics about detections across frames."""
        total_detections = sum(len(fd.detections) for fd in frame_detections)
        total_players = sum(len(fd.players) for fd in frame_detections)
        total_balls = sum(len(fd.balls) for fd in frame_detections)
        
        avg_detections_per_frame = total_detections / len(frame_detections) if frame_detections else 0
        avg_players_per_frame = total_players / len(frame_detections) if frame_detections else 0
        avg_balls_per_frame = total_balls / len(frame_detections) if frame_detections else 0
        
        # Get confidence statistics
        all_confidences = []
        for fd in frame_detections:
            all_confidences.extend([det.confidence for det in fd.detections])
        
        stats = {
            'total_frames': len(frame_detections),
            'total_detections': total_detections,
            'total_players': total_players,
            'total_balls': total_balls,
            'avg_detections_per_frame': avg_detections_per_frame,
            'avg_players_per_frame': avg_players_per_frame,
            'avg_balls_per_frame': avg_balls_per_frame,
            'confidence_stats': {
                'min': min(all_confidences) if all_confidences else 0,
                'max': max(all_confidences) if all_confidences else 0,
                'mean': np.mean(all_confidences) if all_confidences else 0,
                'std': np.std(all_confidences) if all_confidences else 0
            }
        }
        
        return stats
    
    def visualize_detections(self, frame: np.ndarray, frame_detections: FrameDetections, 
                           draw_confidence: bool = True, draw_class_names: bool = True) -> np.ndarray:
        """Visualize detections on a frame."""
        vis_frame = frame.copy()
        
        # Color scheme for different object types
        colors = {
            'person': (0, 255, 0),      # Green for players
            'ball': (0, 0, 255),        # Red for balls
            'sports ball': (0, 0, 255), # Red for sports balls
            'other': (255, 0, 0)        # Blue for other objects
        }
        
        for detection in frame_detections.detections:
            x1, y1, x2, y2 = detection.bbox
            
            # Choose color based on class
            color = colors.get(detection.class_name, colors['other'])
            
            # Draw bounding box
            cv2.rectangle(vis_frame, (x1, y1), (x2, y2), color, 2)
            
            # Draw center point
            cv2.circle(vis_frame, detection.center, 5, color, -1)
            
            # Draw label
            if draw_class_names or draw_confidence:
                label_parts = []
                if draw_class_names:
                    label_parts.append(detection.class_name)
                if draw_confidence:
                    label_parts.append(f"{detection.confidence:.2f}")
                
                label = " ".join(label_parts)
                
                # Calculate text size and position
                (text_width, text_height), baseline = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
                cv2.rectangle(vis_frame, (x1, y1 - text_height - 10), (x1 + text_width, y1), color, -1)
                cv2.putText(vis_frame, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
        
        return vis_frame
    
    def save_detections_to_json(self, frame_detections: List[FrameDetections], output_path: str):
        """Save detections to JSON file."""
        import json
        
        data = []
        for fd in frame_detections:
            frame_data = {
                'frame_id': fd.frame_id,
                'timestamp': fd.timestamp,
                'detections': []
            }
            
            for detection in fd.detections:
                det_data = {
                    'bbox': detection.bbox,
                    'confidence': detection.confidence,
                    'class_id': detection.class_id,
                    'class_name': detection.class_name,
                    'center': detection.center,
                    'area': detection.area
                }
                frame_data['detections'].append(det_data)
            
            data.append(frame_data)
        
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        self.logger.info(f"Saved detections to: {output_path}")
    
    def load_detections_from_json(self, input_path: str) -> List[FrameDetections]:
        """Load detections from JSON file."""
        import json
        
        with open(input_path, 'r') as f:
            data = json.load(f)
        
        frame_detections = []
        for frame_data in data:
            detections = []
            players = []
            balls = []
            other_objects = []
            
            for det_data in frame_data['detections']:
                detection = Detection(
                    bbox=tuple(det_data['bbox']),
                    confidence=det_data['confidence'],
                    class_id=det_data['class_id'],
                    class_name=det_data['class_name'],
                    center=tuple(det_data['center']),
                    area=det_data['area']
                )
                
                detections.append(detection)
                
                if detection.class_name == 'person':
                    players.append(detection)
                elif 'ball' in detection.class_name.lower():
                    balls.append(detection)
                else:
                    other_objects.append(detection)
            
            frame_detections.append(FrameDetections(
                frame_id=frame_data['frame_id'],
                timestamp=frame_data['timestamp'],
                detections=detections,
                players=players,
                balls=balls,
                other_objects=other_objects
            ))
        
        return frame_detections