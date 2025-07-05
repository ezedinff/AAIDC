# tools/database_tools.py
from langchain_core.tools import tool
from typing import List, Dict, Any, Optional
from database import DatabaseManager, db
from flask import current_app

@tool
def save_scene_progress(video_id: str, scenes: List[Dict[str, Any]], step: str) -> str:
    """Save scene generation progress to database."""
    try:
        with current_app.app_context():
            db_manager = DatabaseManager(db)
            video = db_manager.get_video(video_id)
            if video:
                # Store scenes as JSON in database
                import json
                if step == "raw_scenes":
                    video.raw_scenes = json.dumps(scenes)
                elif step == "improved_scenes":
                    video.improved_scenes = json.dumps(scenes)
                db.session.commit()
                return f"Successfully saved {len(scenes)} scenes for step {step}"
            else:
                return f"Video {video_id} not found"
    except Exception as e:
        return f"Error saving scenes: {e}"

@tool
def search_similar_videos(topic: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Search for videos with similar topics for reference."""
    try:
        with current_app.app_context():
            db_manager = DatabaseManager(db)
            videos = db_manager.get_all_videos()
            # Simple keyword matching (could be enhanced with embeddings)
            similar = [v.to_dict() for v in videos 
                      if any(word.lower() in v.user_input.lower() 
                            for word in topic.split())][:limit]
            return similar
    except Exception as e:
        return []

@tool
def log_progress_event(video_id: str, step: str, status: str, message: str) -> str:
    """Log a progress event to database."""
    try:
        with current_app.app_context():
            db_manager = DatabaseManager(db)
            db_manager.add_progress_entry(video_id, step, status, message)
            return f"Logged: {step} - {status} - {message}"
    except Exception as e:
        return f"Error logging: {e}"

@tool
def get_video_context(video_id: str) -> Dict[str, Any]:
    """Get video context including title, description, and user input."""
    try:
        with current_app.app_context():
            db_manager = DatabaseManager(db)
            video = db_manager.get_video(video_id)
            if video:
                return {
                    "title": video.title,
                    "description": video.description,
                    "user_input": video.user_input,
                    "previous_scenes": video.raw_scenes,
                    "improved_scenes": video.improved_scenes
                }
            else:
                return {}
    except Exception as e:
        return {}