import numpy as np
import cv2
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import logging
from filterpy.kalman import KalmanFilter
from scipy.optimize import linear_sum_assignment
import math

@dataclass
class Track:
    """Represents a tracked object with trajectory and metadata."""
    track_id: int
    bbox: Tuple[int, int, int, int]  # x1, y1, x2, y2
    center: Tuple[int, int]
    confidence: float
    class_name: str
    age: int  # Number of frames since first detection
    hits: int  # Number of times detected
    time_since_update: int  # Frames since last update
    velocity: Tuple[float, float]  # dx, dy per frame
    trajectory: List[Tuple[int, int]]  # Historical center positions
    is_active: bool
    
    def __post_init__(self):
        if not self.trajectory:
            self.trajectory = [self.center]

@dataclass
class TrackingResult:
    """Results from tracking for a single frame."""
    frame_id: int
    timestamp: float
    tracks: List[Track]
    active_tracks: List[Track]
    lost_tracks: List[Track]

class KalmanTracker:
    """Individual Kalman filter for tracking a single object."""
    
    def __init__(self, bbox: Tuple[int, int, int, int]):
        """Initialize Kalman filter for object tracking."""
        self.kf = KalmanFilter(dim_x=7, dim_z=4)
        
        # State transition matrix (constant velocity model)
        self.kf.F = np.array([
            [1, 0, 0, 0, 1, 0, 0],
            [0, 1, 0, 0, 0, 1, 0],
            [0, 0, 1, 0, 0, 0, 1],
            [0, 0, 0, 1, 0, 0, 0],
            [0, 0, 0, 0, 1, 0, 0],
            [0, 0, 0, 0, 0, 1, 0],
            [0, 0, 0, 0, 0, 0, 1]
        ])
        
        # Measurement function
        self.kf.H = np.array([
            [1, 0, 0, 0, 0, 0, 0],
            [0, 1, 0, 0, 0, 0, 0],
            [0, 0, 1, 0, 0, 0, 0],
            [0, 0, 0, 1, 0, 0, 0]
        ])
        
        # Measurement noise
        self.kf.R[2:, 2:] *= 10.0
        
        # Process noise
        self.kf.P[4:, 4:] *= 1000.0
        self.kf.P *= 10.0
        
        # Initialize state
        self.kf.Q[-1, -1] *= 0.01
        self.kf.Q[4:, 4:] *= 0.01
        
        # Convert bbox to [cx, cy, s, r] format
        cx, cy, s, r = self._bbox_to_z(bbox)
        self.kf.x[:4] = [cx, cy, s, r]
        
        self.time_since_update = 0
        self.history = []
        self.hits = 0
        self.hit_streak = 0
        self.age = 0
    
    def _bbox_to_z(self, bbox: Tuple[int, int, int, int]) -> Tuple[float, float, float, float]:
        """Convert bounding box to z format for Kalman filter."""
        x1, y1, x2, y2 = bbox
        w = x2 - x1
        h = y2 - y1
        cx = x1 + w / 2.0
        cy = y1 + h / 2.0
        s = w * h    # scale is just area
        r = w / float(h)  # aspect ratio
        return cx, cy, s, r
    
    def _z_to_bbox(self, z: np.ndarray) -> Tuple[int, int, int, int]:
        """Convert z format back to bounding box."""
        cx, cy, s, r = z
        w = np.sqrt(s * r)
        h = s / w
        x1 = cx - w / 2.0
        y1 = cy - h / 2.0
        x2 = cx + w / 2.0
        y2 = cy + h / 2.0
        return int(x1), int(y1), int(x2), int(y2)
    
    def update(self, bbox: Tuple[int, int, int, int]):
        """Update the tracker with a new detection."""
        self.time_since_update = 0
        self.history = []
        self.hits += 1
        self.hit_streak += 1
        
        z = self._bbox_to_z(bbox)
        self.kf.update(z)
    
    def predict(self):
        """Predict next state and return estimated bounding box."""
        if self.kf.x[6] + self.kf.x[2] <= 0:
            self.kf.x[6] *= 0.0
        
        self.kf.predict()
        self.age += 1
        
        if self.time_since_update > 0:
            self.hit_streak = 0
        
        self.time_since_update += 1
        self.history.append(self._z_to_bbox(self.kf.x))
        
        return self.history[-1]
    
    def get_state(self) -> Tuple[int, int, int, int]:
        """Get current state as bounding box."""
        return self._z_to_bbox(self.kf.x)

class MultiObjectTracker:
    """Advanced multi-object tracker using DeepSORT-inspired approach."""
    
    def __init__(self, max_disappeared: int = 30, min_hits: int = 3):
        """Initialize the multi-object tracker."""
        self.max_disappeared = max_disappeared  # Max frames before deleting track
        self.min_hits = min_hits  # Min detections before confirming track
        self.trackers = []
        self.next_id = 0
        self.frame_count = 0
        self.logger = logging.getLogger(__name__)
    
    def calculate_iou(self, box1: Tuple[int, int, int, int], box2: Tuple[int, int, int, int]) -> float:
        """Calculate Intersection over Union (IoU) of two bounding boxes."""
        x1_max = max(box1[0], box2[0])
        y1_max = max(box1[1], box2[1])
        x2_min = min(box1[2], box2[2])
        y2_min = min(box1[3], box2[3])
        
        if x2_min <= x1_max or y2_min <= y1_max:
            return 0.0
        
        intersection = (x2_min - x1_max) * (y2_min - y1_max)
        area1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
        area2 = (box2[2] - box2[0]) * (box2[3] - box2[1])
        union = area1 + area2 - intersection
        
        return intersection / union if union > 0 else 0.0
    
    def calculate_distance(self, center1: Tuple[int, int], center2: Tuple[int, int]) -> float:
        """Calculate Euclidean distance between two centers."""
        return math.sqrt((center1[0] - center2[0])**2 + (center1[1] - center2[1])**2)
    
    def associate_detections_to_trackers(self, detections: List[Dict], trackers: List[KalmanTracker], 
                                       iou_threshold: float = 0.3) -> Tuple[List[Tuple[int, int]], List[int], List[int]]:
        """Associate detections to existing trackers using Hungarian algorithm."""
        if len(trackers) == 0:
            return [], list(range(len(detections))), []
        
        # Create cost matrix
        cost_matrix = np.zeros((len(detections), len(trackers)), dtype=np.float32)
        
        for d, detection in enumerate(detections):
            for t, tracker in enumerate(trackers):
                # Calculate IoU
                iou = self.calculate_iou(detection['bbox'], tracker.get_state())
                cost_matrix[d, t] = 1.0 - iou  # Convert to cost (lower is better)
        
        # Solve assignment problem
        if min(cost_matrix.shape) > 0:
            row_indices, col_indices = linear_sum_assignment(cost_matrix)
            
            # Filter out matches with low IoU
            matches = []
            unmatched_detections = []
            unmatched_trackers = []
            
            for d, t in zip(row_indices, col_indices):
                if cost_matrix[d, t] > (1.0 - iou_threshold):
                    unmatched_detections.append(d)
                    unmatched_trackers.append(t)
                else:
                    matches.append((d, t))
            
            # Add unmatched detections and trackers
            for d in range(len(detections)):
                if d not in [m[0] for m in matches]:
                    unmatched_detections.append(d)
            
            for t in range(len(trackers)):
                if t not in [m[1] for m in matches]:
                    unmatched_trackers.append(t)
            
            return matches, unmatched_detections, unmatched_trackers
        else:
            return [], list(range(len(detections))), []
    
    def update(self, detections: List[Dict], frame_id: int, timestamp: float) -> TrackingResult:
        """Update tracker with new detections."""
        self.frame_count += 1
        
        # Convert detections to the format expected by the tracker
        detection_list = []
        for det in detections:
            detection_list.append({
                'bbox': det['bbox'],
                'confidence': det['confidence'],
                'class_name': det['class_name'],
                'center': det['center']
            })
        
        # Predict new locations of existing trackers
        for tracker in self.trackers:
            tracker.predict()
        
        # Associate detections to trackers
        matches, unmatched_detections, unmatched_trackers = self.associate_detections_to_trackers(
            detection_list, self.trackers
        )
        
        # Update matched trackers
        for detection_idx, tracker_idx in matches:
            self.trackers[tracker_idx].update(detection_list[detection_idx]['bbox'])
        
        # Create new trackers for unmatched detections
        for detection_idx in unmatched_detections:
            tracker = KalmanTracker(detection_list[detection_idx]['bbox'])
            self.trackers.append(tracker)
        
        # Create tracks for output
        tracks = []
        active_tracks = []
        lost_tracks = []
        
        i = len(self.trackers)
        for tracker in reversed(self.trackers):
            i -= 1
            
            # Get current state
            bbox = tracker.get_state()
            center = (int((bbox[0] + bbox[2]) / 2), int((bbox[1] + bbox[3]) / 2))
            
            # Calculate velocity
            velocity = (0.0, 0.0)
            if len(tracker.history) > 1:
                prev_bbox = tracker.history[-2]
                prev_center = (int((prev_bbox[0] + prev_bbox[2]) / 2), int((prev_bbox[1] + prev_bbox[3]) / 2))
                velocity = (center[0] - prev_center[0], center[1] - prev_center[1])
            
            # Determine class name and confidence
            class_name = 'unknown'
            confidence = 0.0
            
            # Find matching detection for this tracker
            for detection_idx, tracker_idx in matches:
                if tracker_idx == i:
                    class_name = detection_list[detection_idx]['class_name']
                    confidence = detection_list[detection_idx]['confidence']
                    break
            
            # Create track
            track = Track(
                track_id=self.next_id if tracker.hits == 1 else getattr(tracker, 'track_id', self.next_id),
                bbox=bbox,
                center=center,
                confidence=confidence,
                class_name=class_name,
                age=tracker.age,
                hits=tracker.hits,
                time_since_update=tracker.time_since_update,
                velocity=velocity,
                trajectory=[center],  # Will be updated with full trajectory
                is_active=tracker.time_since_update <= 1
            )
            
            # Assign track ID if this is a new tracker
            if not hasattr(tracker, 'track_id'):
                tracker.track_id = self.next_id
                track.track_id = self.next_id
                self.next_id += 1
            else:
                track.track_id = tracker.track_id
            
            tracks.append(track)
            
            # Categorize tracks
            if tracker.time_since_update <= 1 and tracker.hits >= self.min_hits:
                active_tracks.append(track)
            elif tracker.time_since_update > 1:
                lost_tracks.append(track)
        
        # Remove dead trackers
        self.trackers = [t for t in self.trackers if t.time_since_update <= self.max_disappeared]
        
        return TrackingResult(
            frame_id=frame_id,
            timestamp=timestamp,
            tracks=tracks,
            active_tracks=active_tracks,
            lost_tracks=lost_tracks
        )
    
    def get_track_statistics(self, tracking_results: List[TrackingResult]) -> Dict:
        """Get statistics about tracking performance."""
        total_tracks = set()
        total_active_frames = 0
        total_lost_frames = 0
        
        for result in tracking_results:
            total_tracks.update([t.track_id for t in result.tracks])
            total_active_frames += len(result.active_tracks)
            total_lost_frames += len(result.lost_tracks)
        
        avg_tracks_per_frame = len(total_tracks) / len(tracking_results) if tracking_results else 0
        avg_active_per_frame = total_active_frames / len(tracking_results) if tracking_results else 0
        avg_lost_per_frame = total_lost_frames / len(tracking_results) if tracking_results else 0
        
        return {
            'total_unique_tracks': len(total_tracks),
            'total_frames': len(tracking_results),
            'avg_tracks_per_frame': avg_tracks_per_frame,
            'avg_active_per_frame': avg_active_per_frame,
            'avg_lost_per_frame': avg_lost_per_frame,
            'track_retention_rate': total_active_frames / (total_active_frames + total_lost_frames) if (total_active_frames + total_lost_frames) > 0 else 0
        }
    
    def visualize_tracks(self, frame: np.ndarray, tracking_result: TrackingResult, 
                        show_trajectory: bool = True, show_velocity: bool = True) -> np.ndarray:
        """Visualize tracking results on a frame."""
        vis_frame = frame.copy()
        
        # Colors for different track states
        colors = {
            'active': (0, 255, 0),     # Green for active tracks
            'lost': (0, 0, 255),       # Red for lost tracks
            'trajectory': (255, 255, 0), # Yellow for trajectory
            'velocity': (255, 0, 255)   # Magenta for velocity
        }
        
        for track in tracking_result.tracks:
            x1, y1, x2, y2 = track.bbox
            color = colors['active'] if track.is_active else colors['lost']
            
            # Draw bounding box
            cv2.rectangle(vis_frame, (x1, y1), (x2, y2), color, 2)
            
            # Draw track ID
            label = f"ID:{track.track_id}"
            if track.class_name != 'unknown':
                label += f" {track.class_name}"
            if track.confidence > 0:
                label += f" {track.confidence:.2f}"
            
            cv2.putText(vis_frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
            
            # Draw center point
            cv2.circle(vis_frame, track.center, 5, color, -1)
            
            # Draw trajectory
            if show_trajectory and len(track.trajectory) > 1:
                for i in range(1, len(track.trajectory)):
                    cv2.line(vis_frame, track.trajectory[i-1], track.trajectory[i], colors['trajectory'], 2)
            
            # Draw velocity vector
            if show_velocity and track.velocity != (0.0, 0.0):
                end_point = (
                    int(track.center[0] + track.velocity[0] * 3),
                    int(track.center[1] + track.velocity[1] * 3)
                )
                cv2.arrowedLine(vis_frame, track.center, end_point, colors['velocity'], 2)
        
        return vis_frame
    
    def reset(self):
        """Reset the tracker."""
        self.trackers = []
        self.next_id = 0
        self.frame_count = 0
        self.logger.info("Tracker reset")