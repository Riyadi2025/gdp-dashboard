"""
Models Module

AI models and computer vision components including:
- Object detection using YOLOv8
- Player and ball detection
- Detection result management
"""

from .detection_engine import DetectionEngine, Detection, FrameDetections

__all__ = [
    'DetectionEngine',
    'Detection',
    'FrameDetections'
]