"""
Sports Video Analysis Platform

A comprehensive AI-powered sports video analysis platform that provides:
- Player tracking and object detection
- Event detection and analysis
- Performance metrics and statistics
- Annotated video export capabilities
- Real-time processing with web interface

Main Components:
- VideoProcessor: Video loading and frame extraction
- DetectionEngine: AI-powered object detection using YOLOv8
- MultiObjectTracker: Player tracking with DeepSORT
- AnnotationEngine: Visual overlays and annotations
- SportsAnalyzer: Main analysis pipeline orchestrator
- VideoExporter: Video export with FFmpeg integration
"""

__version__ = "1.0.0"
__author__ = "Sports Analysis Team"
__email__ = "support@sportsanalysis.com"

# Import main classes for easy access
try:
    from .video_analysis.sports_analyzer import SportsAnalyzer, AnalysisSettings, AnalysisResult
    from .video_analysis.video_processor import VideoProcessor, VideoMetadata
    from .models.detection_engine import DetectionEngine, Detection, FrameDetections
    from .tracking.multi_object_tracker import MultiObjectTracker, Track, TrackingResult
    from .annotations.annotation_engine import AnnotationEngine
    from .export.video_exporter import VideoExporter, ExportSettings
    
    __all__ = [
        'SportsAnalyzer',
        'AnalysisSettings', 
        'AnalysisResult',
        'VideoProcessor',
        'VideoMetadata',
        'DetectionEngine',
        'Detection',
        'FrameDetections',
        'MultiObjectTracker',
        'Track',
        'TrackingResult',
        'AnnotationEngine',
        'VideoExporter',
        'ExportSettings'
    ]
    
except ImportError as e:
    # Handle missing dependencies gracefully
    import warnings
    warnings.warn(f"Some components could not be imported: {e}")
    __all__ = []

def get_version():
    """Get the current version of the platform."""
    return __version__

def check_dependencies():
    """Check if all required dependencies are available."""
    missing_deps = []
    
    try:
        import cv2
    except ImportError:
        missing_deps.append("opencv-python")
    
    try:
        import ultralytics
    except ImportError:
        missing_deps.append("ultralytics")
    
    try:
        import torch
    except ImportError:
        missing_deps.append("torch")
    
    try:
        import filterpy
    except ImportError:
        missing_deps.append("filterpy")
    
    try:
        import ffmpeg
    except ImportError:
        missing_deps.append("ffmpeg-python")
    
    try:
        import streamlit
    except ImportError:
        missing_deps.append("streamlit")
    
    try:
        import fastapi
    except ImportError:
        missing_deps.append("fastapi")
    
    if missing_deps:
        return False, missing_deps
    return True, []

def get_system_info():
    """Get system information for debugging."""
    import platform
    import sys
    
    info = {
        'platform': platform.platform(),
        'python_version': sys.version,
        'architecture': platform.architecture()[0],
        'processor': platform.processor(),
        'version': __version__
    }
    
    # Check for GPU availability
    try:
        import torch
        info['cuda_available'] = torch.cuda.is_available()
        if torch.cuda.is_available():
            info['cuda_version'] = torch.version.cuda
            info['gpu_count'] = torch.cuda.device_count()
            info['gpu_name'] = torch.cuda.get_device_name(0) if torch.cuda.device_count() > 0 else None
    except ImportError:
        info['cuda_available'] = False
    
    return info