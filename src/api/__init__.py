"""
API Module

FastAPI-based REST API for sports video analysis including:
- Video upload and management
- Asynchronous analysis tasks
- Result retrieval and export
- Progress monitoring
"""

from .main import app

__all__ = [
    'app'
]