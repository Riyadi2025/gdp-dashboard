from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBearer
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import tempfile
import os
import json
import logging
import asyncio
from pathlib import Path
import uuid
from datetime import datetime

# Import our analysis components
try:
    from ..video_analysis.sports_analyzer import SportsAnalyzer, AnalysisSettings, AnalysisResult
    from ..export.video_exporter import ExportSettings
    ANALYSIS_AVAILABLE = True
except ImportError:
    ANALYSIS_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Sports Video Analysis API",
    description="REST API for comprehensive sports video analysis with AI-powered player tracking and event detection",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Global storage for analysis tasks and results
analysis_tasks: Dict[str, Dict[str, Any]] = {}
analysis_results: Dict[str, AnalysisResult] = {}

# Pydantic models for API
class AnalysisSettingsRequest(BaseModel):
    detection_confidence: float = 0.5
    detection_model: str = "yolov8n.pt"
    tracking_max_disappeared: int = 30
    tracking_min_hits: int = 3
    frame_skip: int = 1
    enable_event_detection: bool = True
    enable_heatmap_generation: bool = True
    enable_trajectory_analysis: bool = True
    enable_metrics_calculation: bool = True
    export_annotated_video: bool = True
    export_data_files: bool = True
    export_highlight_reel: bool = False

class ExportSettingsRequest(BaseModel):
    quality: str = "high"
    include_audio: bool = True
    output_format: str = "mp4"
    resolution: Optional[List[int]] = None

class AnalysisTaskResponse(BaseModel):
    task_id: str
    status: str
    message: str
    created_at: str

class AnalysisProgressResponse(BaseModel):
    task_id: str
    progress: float
    status: str
    message: str
    estimated_remaining: Optional[float] = None

class AnalysisResultResponse(BaseModel):
    task_id: str
    status: str
    processing_time: float
    video_metadata: Dict[str, Any]
    events: List[Dict[str, Any]]
    metrics: Dict[str, Any]
    available_exports: List[str]

# Utility functions
def create_analysis_settings(request: AnalysisSettingsRequest) -> AnalysisSettings:
    """Convert API request to AnalysisSettings."""
    return AnalysisSettings(
        detection_confidence=request.detection_confidence,
        detection_model=request.detection_model,
        tracking_max_disappeared=request.tracking_max_disappeared,
        tracking_min_hits=request.tracking_min_hits,
        frame_skip=request.frame_skip,
        enable_event_detection=request.enable_event_detection,
        enable_heatmap_generation=request.enable_heatmap_generation,
        enable_trajectory_analysis=request.enable_trajectory_analysis,
        enable_metrics_calculation=request.enable_metrics_calculation,
        export_annotated_video=request.export_annotated_video,
        export_data_files=request.export_data_files,
        export_highlight_reel=request.export_highlight_reel
    )

def create_export_settings(request: ExportSettingsRequest) -> ExportSettings:
    """Convert API request to ExportSettings."""
    return ExportSettings(
        quality=request.quality,
        include_audio=request.include_audio,
        output_format=request.output_format,
        resolution=tuple(request.resolution) if request.resolution else None
    )

async def analyze_video_task(task_id: str, video_path: str, settings: AnalysisSettings):
    """Background task for video analysis."""
    try:
        analysis_tasks[task_id]["status"] = "processing"
        analysis_tasks[task_id]["message"] = "Starting analysis..."
        
        def progress_callback(progress: float):
            analysis_tasks[task_id]["progress"] = progress
            analysis_tasks[task_id]["message"] = f"Analysis progress: {progress*100:.1f}%"
        
        # Initialize analyzer
        analyzer = SportsAnalyzer(settings)
        
        # Run analysis
        result = analyzer.analyze_video(
            video_path=video_path,
            progress_callback=progress_callback
        )
        
        # Store result
        analysis_results[task_id] = result
        analysis_tasks[task_id]["status"] = "completed"
        analysis_tasks[task_id]["message"] = "Analysis completed successfully"
        analysis_tasks[task_id]["progress"] = 1.0
        
        # Clean up
        analyzer.cleanup()
        
        logger.info(f"Analysis {task_id} completed successfully")
        
    except Exception as e:
        analysis_tasks[task_id]["status"] = "failed"
        analysis_tasks[task_id]["message"] = f"Analysis failed: {str(e)}"
        logger.error(f"Analysis {task_id} failed: {str(e)}")

# API Endpoints

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Sports Video Analysis API",
        "version": "1.0.0",
        "status": "running",
        "analysis_available": ANALYSIS_AVAILABLE,
        "endpoints": {
            "upload": "/api/v1/upload",
            "analyze": "/api/v1/analyze",
            "status": "/api/v1/status/{task_id}",
            "result": "/api/v1/result/{task_id}",
            "export": "/api/v1/export/{task_id}",
            "docs": "/docs"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "analysis_available": ANALYSIS_AVAILABLE,
        "active_tasks": len([t for t in analysis_tasks.values() if t["status"] == "processing"])
    }

@app.post("/api/v1/upload", response_model=Dict[str, str])
async def upload_video(file: UploadFile = File(...)):
    """Upload a video file for analysis."""
    if not ANALYSIS_AVAILABLE:
        raise HTTPException(status_code=503, detail="Analysis components not available")
    
    # Validate file type
    allowed_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.wmv']
    file_extension = Path(file.filename).suffix.lower()
    
    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}"
        )
    
    # Save uploaded file
    try:
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=file_extension)
        content = await file.read()
        temp_file.write(content)
        temp_file.close()
        
        file_id = str(uuid.uuid4())
        
        return {
            "file_id": file_id,
            "filename": file.filename,
            "file_path": temp_file.name,
            "size": len(content),
            "message": "File uploaded successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.post("/api/v1/analyze", response_model=AnalysisTaskResponse)
async def start_analysis(
    background_tasks: BackgroundTasks,
    video_path: str,
    settings: AnalysisSettingsRequest = AnalysisSettingsRequest()
):
    """Start video analysis with specified settings."""
    if not ANALYSIS_AVAILABLE:
        raise HTTPException(status_code=503, detail="Analysis components not available")
    
    # Validate video file exists
    if not os.path.exists(video_path):
        raise HTTPException(status_code=404, detail="Video file not found")
    
    # Create task
    task_id = str(uuid.uuid4())
    analysis_settings = create_analysis_settings(settings)
    
    # Initialize task tracking
    analysis_tasks[task_id] = {
        "task_id": task_id,
        "status": "queued",
        "message": "Analysis queued",
        "progress": 0.0,
        "created_at": datetime.now().isoformat(),
        "video_path": video_path,
        "settings": settings.dict()
    }
    
    # Start background analysis
    background_tasks.add_task(analyze_video_task, task_id, video_path, analysis_settings)
    
    return AnalysisTaskResponse(
        task_id=task_id,
        status="queued",
        message="Analysis started",
        created_at=analysis_tasks[task_id]["created_at"]
    )

@app.get("/api/v1/status/{task_id}", response_model=AnalysisProgressResponse)
async def get_analysis_status(task_id: str):
    """Get the status and progress of an analysis task."""
    if task_id not in analysis_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = analysis_tasks[task_id]
    
    return AnalysisProgressResponse(
        task_id=task_id,
        progress=task.get("progress", 0.0),
        status=task["status"],
        message=task["message"],
        estimated_remaining=task.get("estimated_remaining")
    )

@app.get("/api/v1/result/{task_id}", response_model=AnalysisResultResponse)
async def get_analysis_result(task_id: str):
    """Get the result of a completed analysis."""
    if task_id not in analysis_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = analysis_tasks[task_id]
    
    if task["status"] != "completed":
        raise HTTPException(
            status_code=400, 
            detail=f"Analysis not completed. Current status: {task['status']}"
        )
    
    if task_id not in analysis_results:
        raise HTTPException(status_code=404, detail="Analysis result not found")
    
    result = analysis_results[task_id]
    
    # Prepare response
    return AnalysisResultResponse(
        task_id=task_id,
        status=task["status"],
        processing_time=result.processing_time,
        video_metadata={
            "filename": result.video_metadata.filename,
            "duration": result.video_metadata.duration,
            "fps": result.video_metadata.fps,
            "width": result.video_metadata.width,
            "height": result.video_metadata.height,
            "total_frames": result.video_metadata.total_frames,
            "format": result.video_metadata.format
        },
        events=[
            {
                "event_type": event.event_type,
                "timestamp": event.timestamp,
                "frame_id": event.frame_id,
                "player_id": event.player_id,
                "position": event.position,
                "success": event.success,
                "confidence": event.confidence,
                "metadata": event.metadata
            }
            for event in result.events
        ],
        metrics=result.metrics,
        available_exports=["json", "csv", "video"] if task["settings"]["export_annotated_video"] else ["json", "csv"]
    )

@app.get("/api/v1/events/{task_id}")
async def get_events(task_id: str, event_type: Optional[str] = None, player_id: Optional[int] = None):
    """Get filtered events from analysis result."""
    if task_id not in analysis_results:
        raise HTTPException(status_code=404, detail="Analysis result not found")
    
    result = analysis_results[task_id]
    events = result.events
    
    # Apply filters
    if event_type:
        events = [e for e in events if e.event_type == event_type]
    
    if player_id is not None:
        events = [e for e in events if e.player_id == player_id]
    
    return {
        "task_id": task_id,
        "total_events": len(events),
        "events": [
            {
                "event_type": event.event_type,
                "timestamp": event.timestamp,
                "frame_id": event.frame_id,
                "player_id": event.player_id,
                "position": event.position,
                "success": event.success,
                "confidence": event.confidence,
                "metadata": event.metadata
            }
            for event in events
        ]
    }

@app.get("/api/v1/metrics/{task_id}")
async def get_metrics(task_id: str):
    """Get detailed metrics from analysis result."""
    if task_id not in analysis_results:
        raise HTTPException(status_code=404, detail="Analysis result not found")
    
    result = analysis_results[task_id]
    
    return {
        "task_id": task_id,
        "metrics": result.metrics
    }

@app.get("/api/v1/tracking/{task_id}")
async def get_tracking_data(task_id: str, player_id: Optional[int] = None):
    """Get player tracking data."""
    if task_id not in analysis_results:
        raise HTTPException(status_code=404, detail="Analysis result not found")
    
    result = analysis_results[task_id]
    
    # Extract tracking data
    tracking_data = {}
    
    for tracking_result in result.tracking_results:
        for track in tracking_result.active_tracks:
            if track.class_name == 'person':
                if player_id is None or track.track_id == player_id:
                    if track.track_id not in tracking_data:
                        tracking_data[track.track_id] = []
                    
                    tracking_data[track.track_id].append({
                        "timestamp": tracking_result.timestamp,
                        "frame_id": tracking_result.frame_id,
                        "position": track.center,
                        "bbox": track.bbox,
                        "velocity": track.velocity,
                        "confidence": track.confidence
                    })
    
    return {
        "task_id": task_id,
        "tracking_data": tracking_data
    }

@app.post("/api/v1/export/{task_id}")
async def export_data(
    task_id: str,
    export_type: str,
    export_settings: Optional[ExportSettingsRequest] = None
):
    """Export analysis data in various formats."""
    if task_id not in analysis_results:
        raise HTTPException(status_code=404, detail="Analysis result not found")
    
    result = analysis_results[task_id]
    
    if export_type == "json":
        # Export complete analysis data as JSON
        data = result.to_dict()
        filename = f"analysis_{task_id}.json"
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            json.dump(data, f, indent=2)
            temp_path = f.name
        
        return FileResponse(
            temp_path,
            media_type="application/json",
            filename=filename
        )
    
    elif export_type == "csv":
        # Export events as CSV
        import pandas as pd
        
        events_data = []
        for event in result.events:
            events_data.append({
                'timestamp': event.timestamp,
                'event_type': event.event_type,
                'player_id': event.player_id,
                'success': event.success,
                'confidence': event.confidence,
                'position_x': event.position[0],
                'position_y': event.position[1]
            })
        
        df = pd.DataFrame(events_data)
        filename = f"events_{task_id}.csv"
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            df.to_csv(f.name, index=False)
            temp_path = f.name
        
        return FileResponse(
            temp_path,
            media_type="text/csv",
            filename=filename
        )
    
    elif export_type == "video":
        # Export annotated video (if available)
        task = analysis_tasks[task_id]
        
        if not task["settings"]["export_annotated_video"]:
            raise HTTPException(
                status_code=400, 
                detail="Video export not enabled for this analysis"
            )
        
        # This would require implementing video export functionality
        # For now, return information about how to access the video
        return {
            "message": "Video export functionality requires additional implementation",
            "task_id": task_id,
            "export_type": export_type
        }
    
    else:
        raise HTTPException(status_code=400, detail="Unsupported export type")

@app.delete("/api/v1/task/{task_id}")
async def delete_task(task_id: str):
    """Delete a task and its results."""
    if task_id not in analysis_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Clean up task data
    if task_id in analysis_tasks:
        del analysis_tasks[task_id]
    
    if task_id in analysis_results:
        del analysis_results[task_id]
    
    return {"message": f"Task {task_id} deleted successfully"}

@app.get("/api/v1/tasks")
async def list_tasks():
    """List all analysis tasks."""
    return {
        "tasks": [
            {
                "task_id": task_id,
                "status": task["status"],
                "progress": task.get("progress", 0.0),
                "created_at": task["created_at"],
                "message": task["message"]
            }
            for task_id, task in analysis_tasks.items()
        ]
    }

@app.get("/api/v1/models")
async def list_available_models():
    """List available detection models."""
    return {
        "available_models": [
            {
                "name": "yolov8n.pt",
                "description": "YOLOv8 Nano - Fastest, lowest accuracy",
                "size": "6.2 MB"
            },
            {
                "name": "yolov8s.pt", 
                "description": "YOLOv8 Small - Good balance of speed and accuracy",
                "size": "21.5 MB"
            },
            {
                "name": "yolov8m.pt",
                "description": "YOLOv8 Medium - Higher accuracy, slower",
                "size": "49.7 MB"
            },
            {
                "name": "yolov8l.pt",
                "description": "YOLOv8 Large - High accuracy",
                "size": "83.7 MB"
            },
            {
                "name": "yolov8x.pt",
                "description": "YOLOv8 Extra Large - Highest accuracy, slowest",
                "size": "130.5 MB"
            }
        ]
    }

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"detail": "Resource not found"}
    )

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    logger.error(f"Internal server error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize the application."""
    logger.info("Sports Video Analysis API starting up...")
    
    if not ANALYSIS_AVAILABLE:
        logger.warning("Analysis components not available")
    else:
        logger.info("Analysis components loaded successfully")
    
    # Create necessary directories
    os.makedirs("temp", exist_ok=True)
    os.makedirs("exports", exist_ok=True)

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on shutdown."""
    logger.info("Sports Video Analysis API shutting down...")
    
    # Clean up any running tasks
    for task_id in list(analysis_tasks.keys()):
        if analysis_tasks[task_id]["status"] == "processing":
            analysis_tasks[task_id]["status"] = "cancelled"
            analysis_tasks[task_id]["message"] = "Task cancelled due to server shutdown"

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")