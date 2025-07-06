"""
Export Module

Video and data export functionality including:
- Annotated video export with FFmpeg
- Highlight reel generation
- Data export in various formats (JSON, CSV)
- Custom overlay integration
"""

from .video_exporter import VideoExporter, ExportSettings, ExportProgress

__all__ = [
    'VideoExporter',
    'ExportSettings',
    'ExportProgress'
]