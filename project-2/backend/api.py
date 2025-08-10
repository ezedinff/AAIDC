import os
import json
import threading
from datetime import datetime
from typing import Dict, Any, Generator
from flask import Flask, request, jsonify, Response, stream_template
from flask_cors import CORS
from werkzeug.exceptions import BadRequest, NotFound

from config import get_config
from database import db, Video, VideoProgress, DatabaseManager, init_database
from graph import VideoGeneratorGraph

# Additional imports for validation and health checks
from pydantic import BaseModel, Field, ValidationError
from functools import lru_cache
import os
from sqlalchemy import text
import json as _json

# Local services and utils
from services.moderation import _llm_moderation_flagged
from utils.media import compute_duration_from_file
from utils.sanitize import sanitize_input
from services.video_generation import generate_video_async, VideoGeneratorWithProgress


app = Flask(__name__)
config = get_config()
# Configure CORS based on configured origins
CORS(app, resources={r"/api/*": {"origins": config["cors_origins"]}})

# Configure Flask app
app.config['SQLALCHEMY_DATABASE_URI'] = config['database_url']
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = config['secret_key']

# Initialize database
db.init_app(app)
db_manager = DatabaseManager(db)

# Initialize video generator
video_generator = VideoGeneratorGraph()

# Global dictionary to store SSE connections
sse_connections = {}

# Global dictionary to store real-time progress updates
progress_updates = {}

class CreateVideoPayload(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=1, max_length=2000)
    user_input: str = Field(min_length=1, max_length=4000)


@app.route('/api/videos', methods=['GET'])
def get_videos():
    """Get all videos from the database."""
    try:
        videos = db_manager.get_all_videos()
        for video in videos:
            if not video.duration or video.duration == 0:
                if video.file_path and os.path.exists(video.file_path):
                    video.duration = compute_duration_from_file(video.file_path)
                    db.session.commit()
        return jsonify({
            'success': True,
            'videos': [video.to_dict() for video in videos]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/videos/<video_id>', methods=['GET'])
def get_video(video_id: str):
    """Get specific video by ID."""
    try:
        video = db_manager.get_video(video_id)
        if not video:
            return jsonify({
                'success': False,
                'error': 'Video not found'
            }), 404
        
        return jsonify({
            'success': True,
            'video': video.to_dict()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/videos', methods=['POST'])
def create_video():
    """Create a new video generation request."""
    try:
        if not request.is_json:
            return jsonify({'success': False, 'error': 'Content-Type must be application/json'}), 400
        data = request.get_json(silent=True) or {}
        try:
            payload = CreateVideoPayload(**data)
        except ValidationError as ve:
            return jsonify({'success': False, 'error': ve.errors()}), 400
        
        user_input = payload.user_input.strip()
        title = payload.title.strip() or f'Video - {datetime.now().strftime("%Y-%m-%d %H:%M")}'
        description = payload.description.strip()

        # Sanitize inputs
        title = sanitize_input(title, 255)
        description = sanitize_input(description, 2000)
        user_input = sanitize_input(user_input, 4000)

        # Moderation pre-filter (disabled in mock mode)
        if _llm_moderation_flagged(f"{title} {description} {user_input}"):
            return jsonify({'success': False, 'error': 'Content violates policy'}), 422
        
        # Create video record
        video = db_manager.create_video(title, description, user_input)
        
        # Start video generation in background
        thread = threading.Thread(
            target=generate_video_async,
            args=(app, video.id, user_input, db_manager, progress_updates)
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'video': video.to_dict(),
            'message': 'Video generation started'
        }), 201
        
    except BadRequest as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/videos/<video_id>/progress', methods=['GET'])
def get_video_progress(video_id: str):
    """Get progress history for a video."""
    try:
        progress_entries = db_manager.get_video_progress(video_id)
        return jsonify({
            'success': True,
            'progress': [entry.to_dict() for entry in progress_entries]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/videos/<video_id>/events')
def video_events(video_id: str):
    """Server-Sent Events endpoint for real-time video generation updates."""
    def event_generator():
        """Generate SSE events for video progress."""
        try:
            # Store connection for this video
            if video_id not in sse_connections:
                sse_connections[video_id] = []
            
            # Add this connection to the list
            connection_id = len(sse_connections[video_id])
            sse_connections[video_id].append(True)
            
            # Send initial status with app context
            with app.app_context():
                video = db_manager.get_video(video_id)
                if video:
                    yield f"data: {json.dumps({'type': 'status', 'data': video.to_dict()})}\n\n"
            
            last_progress_timestamp = None
            
            # Keep connection alive and send updates
            while sse_connections[video_id][connection_id]:
                # Check for real-time progress updates
                if video_id in progress_updates:
                    progress_update = progress_updates[video_id]
                    if progress_update['timestamp'] != last_progress_timestamp:
                        # Send progress update with correct format
                        yield f"data: {json.dumps({'type': 'progress', 'progress': progress_update['progress'], 'message': progress_update['message']})}\n\n"
                        last_progress_timestamp = progress_update['timestamp']
                
                # Check for video updates with app context
                with app.app_context():
                    video = db_manager.get_video(video_id)
                    if video:
                        yield f"data: {json.dumps({'type': 'update', 'data': video.to_dict()})}\n\n"
                    
                    # If video is completed or failed, close connection
                    if video and video.status in ['completed', 'failed']:
                        # Send any remaining progress updates first
                        if video_id in progress_updates:
                            progress_update = progress_updates[video_id]
                            yield f"data: {json.dumps({'type': 'progress', 'progress': progress_update['progress'], 'message': progress_update['message']})}\n\n"
                        
                        # Send completion event
                        yield f"data: {json.dumps({'type': 'complete', 'data': video.to_dict()})}\n\n"
                        
                        # Close connection
                        sse_connections[video_id][connection_id] = False
                        
                        # Clean up progress updates after a small delay
                        if video_id in progress_updates:
                            del progress_updates[video_id]
                        break
                
                # Keep alive (check more frequently for real-time updates)
                yield f"data: {json.dumps({'type': 'heartbeat', 'timestamp': datetime.utcnow().isoformat()})}\n\n"
                
                # Sleep for a shorter time to get more real-time updates
                import time
                time.sleep(0.5)
                
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
        finally:
            # Clean up connection
            if video_id in sse_connections and connection_id < len(sse_connections[video_id]):
                sse_connections[video_id][connection_id] = False
    
    return Response(
        event_generator(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Cache-Control'
        }
    )

@app.route('/api/videos/<video_id>/download', methods=['GET'])
def download_video(video_id: str):
    """Download a video file."""
    try:
        video = db_manager.get_video(video_id)
        if not video:
            return jsonify({
                'success': False,
                'error': 'Video not found'
            }), 404
        
        if not video.file_path:
            return jsonify({
                'success': False,
                'error': 'Video file not available'
            }), 404
        
        # Ensure file path is under configured outputs dir for safety
        outputs_root = os.path.abspath(config.get('output_dir'))
        file_path = os.path.abspath(video.file_path)
        print(f"Download request path check: outputs_root={outputs_root} file_path={file_path}")
        if not file_path.startswith(outputs_root):
            return jsonify({'success': False, 'error': 'Invalid file path'}), 400
        if not os.path.exists(file_path):
            print(f"File not found at path: {file_path}")
            return jsonify({
                'success': False,
                'error': 'Video file not found on disk'
            }), 404
        
        from flask import send_file
        # Allow inline playback if requested
        as_attachment = request.args.get('inline') not in ('1', 'true', 'yes')
        return send_file(
            file_path,
            as_attachment=as_attachment,
            download_name=f"{video.title}.mp4",
            mimetype='video/mp4'
        )
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/videos/<video_id>', methods=['DELETE'])
def delete_video(video_id: str):
    """Delete a video and its files."""
    try:
        video = db_manager.get_video(video_id)
        if not video:
            return jsonify({
                'success': False,
                'error': 'Video not found'
            }), 404
        
        # Delete video file if it exists
        if video.file_path and os.path.exists(video.file_path):
            os.remove(video.file_path)
        
        # Delete from database
        db.session.delete(video)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Video deleted successfully'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint with DB and filesystem checks."""
    health = {
        'success': True,
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'mock_mode': config.get('mock_mode', False),
        'checks': {}
    }
    # DB check
    try:
        db.session.execute(text('SELECT 1'))
        health['checks']['database'] = 'ok'
    except Exception as e:
        health['checks']['database'] = f'error: {e}'
        health['success'] = False
        health['status'] = 'degraded'
    # Directory write checks
    for key in ['output_dir', 'temp_dir']:
        path = config.get(key)
        try:
            os.makedirs(path, exist_ok=True)
            test_file = os.path.join(path, '.healthcheck')
            with open(test_file, 'w') as f:
                f.write('ok')
            os.remove(test_file)
            health['checks'][key] = 'writable'
        except Exception as e:
            health['checks'][key] = f'not_writable: {e}'
            health['success'] = False
            health['status'] = 'degraded'
    return jsonify(health)

@app.route('/api/metrics', methods=['GET'])
def metrics():
    """Basic metrics: counts of videos by status."""
    try:
        counts = {s: 0 for s in ['pending', 'processing', 'completed', 'failed']}
        videos = db_manager.get_all_videos()
        for v in videos:
            if v.status in counts:
                counts[v.status] += 1
            else:
                counts[v.status] = counts.get(v.status, 0) + 1
        return jsonify({'success': True, 'counts': counts, 'total': len(videos)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/test-video', methods=['POST'])
def create_test_video():
    """Create a test video without AI generation (for testing)."""
    try:
        data = request.get_json()
        title = data.get('title', 'Test Video')
        description = data.get('description', 'Test video description')
        
        # Create video record
        video = db_manager.create_video(title, description, description)
        
        # Simulate completion without AI generation
        db_manager.update_video_status(video.id, 'completed', 'completed', 100)
        db_manager.add_progress_entry(video.id, 'test', 'completed', 'Test video created successfully')
        
        return jsonify({
            'success': True,
            'video': video.to_dict(),
            'message': 'Test video created successfully'
        }), 201
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def create_app():
    """Create and configure Flask app."""
    from config import validate_config
    
    # Validate configuration and create directories
    validate_config()
    
    init_database(app)
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True) 