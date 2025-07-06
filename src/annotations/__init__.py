"""
Annotations Module

Visual annotation and overlay functionality including:
- Text, line, and shape annotations
- Event markers and labels
- Heatmap generation and visualization
- Metrics overlays
"""

from .annotation_engine import (
    AnnotationEngine,
    Annotation,
    TextAnnotation,
    LineAnnotation,
    CircleAnnotation,
    RectangleAnnotation,
    HeatmapAnnotation,
    EventAnnotation
)

__all__ = [
    'AnnotationEngine',
    'Annotation',
    'TextAnnotation',
    'LineAnnotation', 
    'CircleAnnotation',
    'RectangleAnnotation',
    'HeatmapAnnotation',
    'EventAnnotation'
]