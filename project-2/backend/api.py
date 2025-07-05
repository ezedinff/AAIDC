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

app = Flask(__name__)
CORS(app)

# Configure Flask app
config = get_config()
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

@app.route('/api/videos', methods=['GET'])
def get_videos():
    """Get all videos from the database."""
    try:
        videos = db_manager.get_all_videos()
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
        data = request.get_json()
        
        if not data or 'user_input' not in data:
            raise BadRequest('user_input is required')
        
        user_input = data['user_input']
        title = data.get('title', f'Video - {datetime.now().strftime("%Y-%m-%d %H:%M")}')
        description = data.get('description', '')
        
        # Create video record
        video = db_manager.create_video(title, description, user_input)
        
        # Start video generation in background
        thread = threading.Thread(
            target=generate_video_async,
            args=(video.id, user_input)
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
        
        if not os.path.exists(video.file_path):
            return jsonify({
                'success': False,
                'error': 'Video file not found on disk'
            }), 404
        
        from flask import send_file
        return send_file(
            video.file_path,
            as_attachment=True,
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
    """Health check endpoint."""
    return jsonify({
        'success': True,
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat()
    })

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

def generate_video_async(video_id: str, user_input: str):
    """Generate video asynchronously and update database."""
    with app.app_context():
        try:
            # Update status to processing
            db_manager.update_video_status(video_id, 'processing', 'initializing', 0)
            db_manager.add_progress_entry(video_id, 'initialization', 'started', 'Starting video generation')
            
            # Create a custom workflow that updates progress
            workflow_with_progress = VideoGeneratorWithProgress(video_id, db_manager)
            result = workflow_with_progress.generate_video(user_input)
            
            if result.get('final_video') and os.path.exists(result.get('final_video')):
                # Get video duration if possible
                duration = None
                try:
                    import moviepy.editor as mp
                    video_clip = mp.VideoFileClip(result['final_video'])
                    duration = video_clip.duration
                    video_clip.close()
                except:
                    pass
                
                # Update database with success
                db_manager.update_video_result(video_id, result['final_video'], duration)
                db_manager.add_progress_entry(video_id, 'completion', 'completed', 'Video generation completed successfully')
                
            else:
                # Update database with failure
                error_msg = result.get('error', 'Unknown error occurred')
                db_manager.update_video_status(video_id, 'failed', 'failed', 100, error_msg)
                db_manager.add_progress_entry(video_id, 'completion', 'failed', f'Video generation failed: {error_msg}')
                
        except Exception as e:
            # Update database with error
            error_msg = str(e)
            db_manager.update_video_status(video_id, 'failed', 'failed', 100, error_msg)
            db_manager.add_progress_entry(video_id, 'completion', 'failed', f'Video generation failed: {error_msg}')

class VideoGeneratorWithProgress:
    """Video generator wrapper that provides progress updates."""
    
    def __init__(self, video_id: str, db_manager: DatabaseManager):
        self.video_id = video_id
        self.db_manager = db_manager
        # Create generator with progress callback
        self.generator = VideoGeneratorGraph(progress_callback=self._send_sse_update)
    
    def _send_sse_update(self, step: str, progress: int, message: str):
        """Send SSE update to connected clients."""
        try:
            # Update database - use appropriate status based on step
            if step == 'completed':
                self.db_manager.update_video_status(self.video_id, 'completed', step, progress)
                self.db_manager.add_progress_entry(self.video_id, step, 'completed', message)
            elif step in ['failed', 'video_assembly_failed', 'scene_generation_failed', 'scene_critique_failed', 'audio_generation_failed']:
                self.db_manager.update_video_status(self.video_id, 'failed', step, progress)
                self.db_manager.add_progress_entry(self.video_id, step, 'failed', message)
            else:
                self.db_manager.update_video_status(self.video_id, 'processing', step, progress)
                self.db_manager.add_progress_entry(self.video_id, step, 'started', message)
            
            # Store progress update for SSE broadcasting
            progress_updates[self.video_id] = {
                'type': 'progress',
                'step': step,
                'progress': progress,
                'message': message,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            print(f"Progress update sent: {step} - {progress}% - {message}")
                            
        except Exception as e:
            print(f"Error sending SSE update: {e}")
    
    def generate_video(self, user_input: str) -> Dict[str, Any]:
        """Generate video with real-time progress tracking."""
        try:
            # Send initial progress update
            self._send_sse_update('initializing', 5, 'Starting video generation...')
            
            # Run the complete workflow - progress updates will be sent by individual nodes
            result = self.generator.generate_video(user_input)
            
            # Ensure final status is sent
            if result.get('final_video'):
                self._send_sse_update('completed', 100, 'Video generation completed successfully!')
            else:
                error_msg = result.get('error', 'Unknown error')
                self._send_sse_update('failed', 100, f"Video generation failed: {error_msg}")
            
            return result
            
        except Exception as e:
            self._send_sse_update('failed', 100, f'Video generation failed: {str(e)}')
            raise e

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