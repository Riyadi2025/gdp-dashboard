import streamlit as st
import pandas as pd
import numpy as np
import cv2
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional
import logging
import tempfile
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Set page config
st.set_page_config(
    page_title="Sports Video Analysis Platform",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Import our analysis components
try:
    from src.video_analysis.sports_analyzer import SportsAnalyzer, AnalysisSettings
    from src.video_analysis.video_processor import VideoProcessor
    from src.models.detection_engine import DetectionEngine
    from src.export.video_exporter import ExportSettings
    ANALYSIS_AVAILABLE = True
except ImportError as e:
    ANALYSIS_AVAILABLE = False
    st.error(f"Analysis components not available: {e}")

# Initialize session state
if 'analysis_result' not in st.session_state:
    st.session_state.analysis_result = None
if 'analysis_progress' not in st.session_state:
    st.session_state.analysis_progress = 0.0
if 'is_analyzing' not in st.session_state:
    st.session_state.is_analyzing = False
if 'uploaded_video' not in st.session_state:
    st.session_state.uploaded_video = None

def main():
    """Main application function."""
    st.title("⚽ Sports Video Analysis Platform")
    st.markdown("Upload a sports video and get comprehensive AI-powered analysis with player tracking, event detection, and detailed metrics.")
    
    # Sidebar for configuration
    setup_sidebar()
    
    # Main content area
    if not ANALYSIS_AVAILABLE:
        show_setup_instructions()
        return
    
    # Show different views based on analysis state
    if st.session_state.analysis_result is None:
        show_upload_interface()
    else:
        show_analysis_results()

def setup_sidebar():
    """Setup the sidebar with analysis settings."""
    st.sidebar.title("Analysis Settings")
    
    # Detection settings
    st.sidebar.subheader("🔍 Detection Settings")
    detection_confidence = st.sidebar.slider(
        "Detection Confidence", 0.1, 1.0, 0.5, 0.1,
        help="Minimum confidence threshold for object detection"
    )
    detection_model = st.sidebar.selectbox(
        "Detection Model", 
        ["yolov8n.pt", "yolov8s.pt", "yolov8m.pt", "yolov8l.pt", "yolov8x.pt"],
        help="YOLOv8 model size (n=nano, s=small, m=medium, l=large, x=extra large)"
    )
    
    # Tracking settings
    st.sidebar.subheader("🎯 Tracking Settings")
    tracking_max_disappeared = st.sidebar.slider(
        "Max Disappeared Frames", 10, 100, 30, 5,
        help="Maximum frames before a track is considered lost"
    )
    tracking_min_hits = st.sidebar.slider(
        "Min Hits for Confirmation", 1, 10, 3, 1,
        help="Minimum detections before confirming a track"
    )
    
    # Processing settings
    st.sidebar.subheader("⚙️ Processing Settings")
    frame_skip = st.sidebar.slider(
        "Frame Skip", 1, 10, 1, 1,
        help="Process every nth frame (higher = faster but less accurate)"
    )
    
    # Analysis features
    st.sidebar.subheader("📊 Analysis Features")
    enable_event_detection = st.sidebar.checkbox("Event Detection", True)
    enable_heatmap_generation = st.sidebar.checkbox("Heatmap Generation", True)
    enable_trajectory_analysis = st.sidebar.checkbox("Trajectory Analysis", True)
    enable_metrics_calculation = st.sidebar.checkbox("Metrics Calculation", True)
    
    # Export settings
    st.sidebar.subheader("📤 Export Settings")
    export_annotated_video = st.sidebar.checkbox("Export Annotated Video", True)
    export_data_files = st.sidebar.checkbox("Export Data Files", True)
    export_highlight_reel = st.sidebar.checkbox("Export Highlight Reel", False)
    
    # Store settings in session state
    st.session_state.analysis_settings = AnalysisSettings(
        detection_confidence=detection_confidence,
        detection_model=detection_model,
        tracking_max_disappeared=tracking_max_disappeared,
        tracking_min_hits=tracking_min_hits,
        frame_skip=frame_skip,
        enable_event_detection=enable_event_detection,
        enable_heatmap_generation=enable_heatmap_generation,
        enable_trajectory_analysis=enable_trajectory_analysis,
        enable_metrics_calculation=enable_metrics_calculation,
        export_annotated_video=export_annotated_video,
        export_data_files=export_data_files,
        export_highlight_reel=export_highlight_reel
    )

def show_setup_instructions():
    """Show setup instructions if analysis components are not available."""
    st.warning("⚠️ Analysis components not available. Please install required dependencies.")
    
    with st.expander("📋 Setup Instructions"):
        st.markdown("""
        To use the sports video analysis platform, please install the required dependencies:
        
        ```bash
        pip install -r requirements.txt
        ```
        
        Make sure you have the following installed:
        - OpenCV (cv2)
        - YOLOv8 (ultralytics)
        - FFmpeg
        - PyTorch
        - All other requirements from requirements.txt
        """)

def show_upload_interface():
    """Show the video upload interface."""
    st.header("📁 Upload Sports Video")
    
    # File uploader
    uploaded_file = st.file_uploader(
        "Choose a video file",
        type=['mp4', 'avi', 'mov', 'mkv', 'wmv'],
        help="Upload a sports video file for analysis"
    )
    
    if uploaded_file is not None:
        # Save uploaded file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp_file:
            tmp_file.write(uploaded_file.read())
            video_path = tmp_file.name
        
        st.session_state.uploaded_video = video_path
        
        # Show video preview
        st.subheader("📹 Video Preview")
        st.video(uploaded_file)
        
        # Show video info
        show_video_info(video_path)
        
        # Analysis button
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🚀 Start Analysis", type="primary", use_container_width=True):
                start_analysis(video_path)
    
    # Show demo section
    show_demo_section()

def show_video_info(video_path: str):
    """Show basic video information."""
    try:
        if ANALYSIS_AVAILABLE:
            with VideoProcessor(video_path) as processor:
                metadata = processor.load_video()
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Duration", f"{metadata.duration:.2f}s")
                
                with col2:
                    st.metric("Resolution", f"{metadata.width}x{metadata.height}")
                
                with col3:
                    st.metric("FPS", f"{metadata.fps:.2f}")
                
                with col4:
                    st.metric("Total Frames", metadata.total_frames)
    except Exception as e:
        st.error(f"Error reading video: {e}")

def show_demo_section():
    """Show demo section with sample analysis."""
    st.header("🎬 Demo & Examples")
    
    with st.expander("🔍 What can this platform do?"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🎯 Object Detection & Tracking")
            st.markdown("""
            - **Player Detection**: Identify and track all players
            - **Ball Tracking**: Continuous ball position tracking
            - **Multi-Object Tracking**: Maintain consistent IDs across frames
            - **Real-time Processing**: Fast analysis with GPU acceleration
            """)
            
            st.subheader("🏃 Event Detection")
            st.markdown("""
            - **Pass Detection**: Identify successful and failed passes
            - **Shot Analysis**: Detect shots and analyze trajectory
            - **Dribble Recognition**: Track ball control and dribbling
            - **Tackle Detection**: Identify defensive actions
            """)
        
        with col2:
            st.subheader("📊 Advanced Analytics")
            st.markdown("""
            - **Heatmaps**: Player positioning and movement patterns
            - **Trajectory Analysis**: Path analysis and speed calculation
            - **Performance Metrics**: Success rates, distance covered
            - **Statistical Reports**: Comprehensive game statistics
            """)
            
            st.subheader("🎥 Video Export")
            st.markdown("""
            - **Annotated Videos**: Export with all visualizations
            - **Highlight Reels**: Automatic key moments compilation
            - **Data Export**: JSON/CSV files with all metrics
            - **Custom Overlays**: Scoreboards, timers, and more
            """)

def start_analysis(video_path: str):
    """Start the video analysis process."""
    if not ANALYSIS_AVAILABLE:
        st.error("Analysis components not available")
        return
    
    st.session_state.is_analyzing = True
    st.session_state.analysis_progress = 0.0
    
    # Create progress display
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    def progress_callback(progress: float):
        st.session_state.analysis_progress = progress
        progress_bar.progress(progress)
        status_text.text(f"Analysis Progress: {progress*100:.1f}%")
    
    try:
        # Initialize analyzer
        analyzer = SportsAnalyzer(st.session_state.analysis_settings)
        
        # Run analysis
        status_text.text("Starting analysis...")
        result = analyzer.analyze_video(
            video_path=video_path,
            progress_callback=progress_callback
        )
        
        # Store result
        st.session_state.analysis_result = result
        st.session_state.is_analyzing = False
        
        # Clean up
        analyzer.cleanup()
        
        # Show success message
        st.success(f"Analysis completed! Processed {len(result.frame_detections)} frames in {result.processing_time:.2f} seconds")
        
        # Rerun to show results
        st.rerun()
        
    except Exception as e:
        st.error(f"Analysis failed: {str(e)}")
        st.session_state.is_analyzing = False
        logging.error(f"Analysis error: {e}")

def show_analysis_results():
    """Show the analysis results interface."""
    result = st.session_state.analysis_result
    
    if result is None:
        st.error("No analysis results available")
        return
    
    # Header with key metrics
    st.header("📊 Analysis Results")
    
    # Key metrics row
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            "Total Events", 
            len(result.events),
            help="Total number of detected events"
        )
    
    with col2:
        total_players = len(set(
            track.track_id for tr in result.tracking_results 
            for track in tr.active_tracks if track.class_name == 'person'
        ))
        st.metric(
            "Players Detected", 
            total_players,
            help="Unique players identified"
        )
    
    with col3:
        st.metric(
            "Processing Time", 
            f"{result.processing_time:.2f}s",
            help="Total analysis time"
        )
    
    with col4:
        st.metric(
            "Frames Analyzed", 
            len(result.frame_detections),
            help="Total frames processed"
        )
    
    with col5:
        avg_fps = len(result.frame_detections) / result.processing_time if result.processing_time > 0 else 0
        st.metric(
            "Avg FPS", 
            f"{avg_fps:.1f}",
            help="Average processing speed"
        )
    
    # Navigation tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📈 Overview", 
        "🎯 Events", 
        "📊 Metrics", 
        "🗺️ Visualizations", 
        "📤 Export"
    ])
    
    with tab1:
        show_overview_tab(result)
    
    with tab2:
        show_events_tab(result)
    
    with tab3:
        show_metrics_tab(result)
    
    with tab4:
        show_visualizations_tab(result)
    
    with tab5:
        show_export_tab(result)
    
    # Reset button
    if st.button("🔄 Analyze New Video"):
        st.session_state.analysis_result = None
        st.session_state.uploaded_video = None
        st.rerun()

def show_overview_tab(result):
    """Show the overview tab."""
    st.subheader("📋 Analysis Summary")
    
    # Video information
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🎬 Video Information")
        video_info = {
            "Filename": result.video_metadata.filename,
            "Duration": f"{result.video_metadata.duration:.2f} seconds",
            "Resolution": f"{result.video_metadata.width}x{result.video_metadata.height}",
            "FPS": f"{result.video_metadata.fps:.2f}",
            "Total Frames": result.video_metadata.total_frames
        }
        
        for key, value in video_info.items():
            st.write(f"**{key}:** {value}")
    
    with col2:
        st.subheader("🔍 Detection Summary")
        detection_stats = result.metrics.get('detection_statistics', {})
        
        detection_info = {
            "Total Detections": detection_stats.get('total_detections', 0),
            "Avg Players/Frame": f"{detection_stats.get('avg_players_per_frame', 0):.2f}",
            "Avg Balls/Frame": f"{detection_stats.get('avg_balls_per_frame', 0):.2f}",
            "Confidence Range": f"{detection_stats.get('confidence_stats', {}).get('min', 0):.2f} - {detection_stats.get('confidence_stats', {}).get('max', 0):.2f}"
        }
        
        for key, value in detection_info.items():
            st.write(f"**{key}:** {value}")
    
    # Event timeline
    if result.events:
        st.subheader("📅 Event Timeline")
        create_event_timeline(result.events)
    
    # Player activity chart
    if result.events:
        st.subheader("👥 Player Activity")
        create_player_activity_chart(result.events)

def create_event_timeline(events):
    """Create an event timeline visualization."""
    if not events:
        st.info("No events detected")
        return
    
    # Prepare data
    event_data = []
    for event in events:
        event_data.append({
            'Timestamp': event.timestamp,
            'Event Type': event.event_type,
            'Player ID': event.player_id,
            'Success': event.success,
            'Confidence': event.confidence
        })
    
    df = pd.DataFrame(event_data)
    
    # Create timeline plot
    fig = px.scatter(
        df, 
        x='Timestamp', 
        y='Event Type',
        color='Success',
        size='Confidence',
        hover_data=['Player ID', 'Confidence'],
        title="Event Timeline"
    )
    
    fig.update_layout(
        xaxis_title="Time (seconds)",
        yaxis_title="Event Type",
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)

def create_player_activity_chart(events):
    """Create a player activity chart."""
    if not events:
        st.info("No events detected")
        return
    
    # Count events by player
    player_counts = {}
    for event in events:
        player_id = event.player_id
        if player_id not in player_counts:
            player_counts[player_id] = {'total': 0, 'successful': 0}
        player_counts[player_id]['total'] += 1
        if event.success:
            player_counts[player_id]['successful'] += 1
    
    # Prepare data
    players = list(player_counts.keys())
    total_events = [player_counts[p]['total'] for p in players]
    successful_events = [player_counts[p]['successful'] for p in players]
    
    # Create chart
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        name='Total Events',
        x=[f'Player {p}' for p in players],
        y=total_events,
        marker_color='lightblue'
    ))
    
    fig.add_trace(go.Bar(
        name='Successful Events',
        x=[f'Player {p}' for p in players],
        y=successful_events,
        marker_color='darkblue'
    ))
    
    fig.update_layout(
        title='Player Activity Summary',
        xaxis_title='Player',
        yaxis_title='Number of Events',
        barmode='group',
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)

def show_events_tab(result):
    """Show the events tab."""
    st.subheader("🎯 Detected Events")
    
    if not result.events:
        st.info("No events detected in this video")
        return
    
    # Event filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        event_types = list(set(event.event_type for event in result.events))
        selected_types = st.multiselect(
            "Filter by Event Type",
            event_types,
            default=event_types
        )
    
    with col2:
        player_ids = list(set(event.player_id for event in result.events))
        selected_players = st.multiselect(
            "Filter by Player",
            [f"Player {pid}" for pid in player_ids],
            default=[f"Player {pid}" for pid in player_ids]
        )
        selected_player_ids = [int(p.split()[1]) for p in selected_players]
    
    with col3:
        success_filter = st.selectbox(
            "Filter by Success",
            ["All", "Successful Only", "Failed Only"]
        )
    
    # Filter events
    filtered_events = []
    for event in result.events:
        if event.event_type in selected_types and event.player_id in selected_player_ids:
            if success_filter == "All" or \
               (success_filter == "Successful Only" and event.success) or \
               (success_filter == "Failed Only" and not event.success):
                filtered_events.append(event)
    
    # Show events table
    if filtered_events:
        events_data = []
        for event in filtered_events:
            events_data.append({
                'Timestamp': f"{event.timestamp:.2f}s",
                'Event Type': event.event_type,
                'Player ID': event.player_id,
                'Success': "✅" if event.success else "❌",
                'Confidence': f"{event.confidence:.2f}",
                'Position': f"({event.position[0]}, {event.position[1]})"
            })
        
        df = pd.DataFrame(events_data)
        st.dataframe(df, use_container_width=True)
        
        # Event statistics
        st.subheader("📊 Event Statistics")
        show_event_statistics(filtered_events)
    else:
        st.info("No events match the selected filters")

def show_event_statistics(events):
    """Show statistics for filtered events."""
    if not events:
        return
    
    # Count by type
    type_counts = {}
    success_counts = {}
    
    for event in events:
        event_type = event.event_type
        type_counts[event_type] = type_counts.get(event_type, 0) + 1
        
        if event_type not in success_counts:
            success_counts[event_type] = {'total': 0, 'successful': 0}
        success_counts[event_type]['total'] += 1
        if event.success:
            success_counts[event_type]['successful'] += 1
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Event type distribution
        fig = px.pie(
            values=list(type_counts.values()),
            names=list(type_counts.keys()),
            title="Event Type Distribution"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Success rates
        success_rates = []
        event_types = []
        for event_type, counts in success_counts.items():
            if counts['total'] > 0:
                success_rate = counts['successful'] / counts['total'] * 100
                success_rates.append(success_rate)
                event_types.append(event_type)
        
        fig = px.bar(
            x=event_types,
            y=success_rates,
            title="Success Rate by Event Type (%)",
            labels={'x': 'Event Type', 'y': 'Success Rate (%)'}
        )
        st.plotly_chart(fig, use_container_width=True)

def show_metrics_tab(result):
    """Show the metrics tab."""
    st.subheader("📊 Detailed Metrics")
    
    metrics = result.metrics
    
    # Overall statistics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("🎬 Video Metrics")
        st.metric("Video Duration", f"{metrics.get('video_duration', 0):.2f}s")
        st.metric("Frames Analyzed", metrics.get('total_frames_analyzed', 0))
        st.metric("Analysis Speed", f"{metrics.get('total_frames_analyzed', 0) / result.processing_time:.1f} FPS")
    
    with col2:
        st.subheader("🔍 Detection Metrics")
        detection_stats = metrics.get('detection_statistics', {})
        st.metric("Total Detections", detection_stats.get('total_detections', 0))
        st.metric("Avg Players/Frame", f"{detection_stats.get('avg_players_per_frame', 0):.2f}")
        st.metric("Avg Balls/Frame", f"{detection_stats.get('avg_balls_per_frame', 0):.2f}")
    
    with col3:
        st.subheader("🎯 Tracking Metrics")
        tracking_stats = metrics.get('tracking_statistics', {})
        st.metric("Unique Tracks", tracking_stats.get('total_unique_tracks', 0))
        st.metric("Track Retention", f"{tracking_stats.get('track_retention_rate', 0)*100:.1f}%")
        st.metric("Avg Active Tracks", f"{tracking_stats.get('avg_active_per_frame', 0):.2f}")
    
    # Player statistics
    if 'player_statistics' in metrics:
        st.subheader("👥 Player Statistics")
        player_stats = metrics['player_statistics']
        
        if player_stats:
            # Create player stats table
            player_data = []
            for player_id, stats in player_stats.items():
                success_rate = (stats['successful_events'] / stats['total_events'] * 100) if stats['total_events'] > 0 else 0
                player_data.append({
                    'Player ID': player_id,
                    'Total Events': stats['total_events'],
                    'Successful Events': stats['successful_events'],
                    'Success Rate': f"{success_rate:.1f}%",
                    'Event Types': ', '.join(stats['event_types'].keys())
                })
            
            df = pd.DataFrame(player_data)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No player statistics available")
    
    # Success rates by event type
    if 'success_rates' in metrics:
        st.subheader("📈 Success Rates by Event Type")
        success_rates = metrics['success_rates']
        
        if success_rates:
            fig = px.bar(
                x=list(success_rates.keys()),
                y=[rate * 100 for rate in success_rates.values()],
                title="Success Rate by Event Type",
                labels={'x': 'Event Type', 'y': 'Success Rate (%)'}
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No success rate data available")

def show_visualizations_tab(result):
    """Show the visualizations tab."""
    st.subheader("🗺️ Visualizations")
    
    if not result.tracking_results:
        st.info("No tracking data available for visualization")
        return
    
    # Heatmap visualization
    st.subheader("🔥 Player Heatmaps")
    
    # Extract player positions
    player_positions = {}
    for tracking_result in result.tracking_results:
        for track in tracking_result.active_tracks:
            if track.class_name == 'person':
                if track.track_id not in player_positions:
                    player_positions[track.track_id] = []
                player_positions[track.track_id].append(track.center)
    
    if player_positions:
        # Player selection
        selected_player = st.selectbox(
            "Select Player for Heatmap",
            list(player_positions.keys()),
            format_func=lambda x: f"Player {x}"
        )
        
        if selected_player in player_positions:
            positions = player_positions[selected_player]
            
            # Create heatmap
            if len(positions) > 1:
                x_coords = [pos[0] for pos in positions]
                y_coords = [pos[1] for pos in positions]
                
                fig = px.density_heatmap(
                    x=x_coords,
                    y=y_coords,
                    title=f"Player {selected_player} Position Heatmap",
                    labels={'x': 'X Position', 'y': 'Y Position'}
                )
                
                # Invert y-axis to match video coordinates
                fig.update_yaxis(autorange="reversed")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info(f"Not enough position data for Player {selected_player}")
    else:
        st.info("No player position data available")
    
    # Trajectory visualization
    st.subheader("🏃 Player Trajectories")
    
    if player_positions:
        # Multi-select for players
        selected_players = st.multiselect(
            "Select Players for Trajectory",
            list(player_positions.keys()),
            default=list(player_positions.keys())[:3],  # Show first 3 by default
            format_func=lambda x: f"Player {x}"
        )
        
        if selected_players:
            fig = go.Figure()
            
            for player_id in selected_players:
                if player_id in player_positions:
                    positions = player_positions[player_id]
                    x_coords = [pos[0] for pos in positions]
                    y_coords = [pos[1] for pos in positions]
                    
                    fig.add_trace(go.Scatter(
                        x=x_coords,
                        y=y_coords,
                        mode='lines+markers',
                        name=f'Player {player_id}',
                        line=dict(width=2),
                        marker=dict(size=4)
                    ))
            
            fig.update_layout(
                title="Player Trajectories",
                xaxis_title="X Position",
                yaxis_title="Y Position",
                yaxis=dict(autorange="reversed"),
                height=600
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Please select at least one player")

def show_export_tab(result):
    """Show the export tab."""
    st.subheader("📤 Export Results")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📄 Data Export")
        
        # Export analysis results as JSON
        if st.button("📊 Export Analysis Data (JSON)"):
            analysis_data = result.to_dict()
            st.download_button(
                label="Download Analysis Data",
                data=json.dumps(analysis_data, indent=2),
                file_name=f"analysis_results_{int(time.time())}.json",
                mime="application/json"
            )
        
        # Export events as CSV
        if st.button("📋 Export Events (CSV)"):
            if result.events:
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
                csv = df.to_csv(index=False)
                st.download_button(
                    label="Download Events CSV",
                    data=csv,
                    file_name=f"events_{int(time.time())}.csv",
                    mime="text/csv"
                )
            else:
                st.info("No events to export")
    
    with col2:
        st.subheader("🎥 Video Export")
        
        st.info("Video export functionality requires the full analysis pipeline with video processing capabilities.")
        
        # Export settings
        st.subheader("Export Settings")
        video_quality = st.selectbox(
            "Video Quality",
            ["high", "medium", "low"],
            index=0
        )
        
        include_audio = st.checkbox("Include Audio", True)
        export_format = st.selectbox("Export Format", ["mp4", "avi", "mov"])
        
        if st.button("🎬 Generate Export Instructions"):
            st.code(f"""
# Video Export Instructions
# Use the following settings for video export:

export_settings = ExportSettings(
    quality='{video_quality}',
    include_audio={include_audio},
    output_format='{export_format}'
)

# Export annotated video
analyzer.export_annotated_video(
    input_video_path='your_video.mp4',
    output_path='annotated_video.{export_format}',
    settings=export_settings
)
            """)

if __name__ == "__main__":
    main()
