"""
Video Analysis Module

Core video processing and analysis functionality including:
- Video loading and frame extraction
- Sports-specific analysis pipeline
- Event detection and metrics calculation
"""

from .video_processor import VideoProcessor, VideoMetadata
from .sports_analyzer import SportsAnalyzer, AnalysisSettings, AnalysisResult, SportsEvent

__all__ = [
    'VideoProcessor',
    'VideoMetadata', 
    'SportsAnalyzer',
    'AnalysisSettings',
    'AnalysisResult',
    'SportsEvent'
]