import os
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Any
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, DateTime, Text, Float
from sqlalchemy.ext.declarative import declarative_base
import uuid

db = SQLAlchemy()

class Video(db.Model):
    """Model for storing video metadata."""
    __tablename__ = 'videos'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=False)
    description = Column(Text)
    user_input = Column(Text, nullable=False)
    status = Column(String(50), default='pending')  # pending, processing, completed, failed
    file_path = Column(String(500))
    duration = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Progress tracking
    current_step = Column(String(100))
    progress_percent = Column(Integer, default=0)
    error_message = Column(Text)
    
    # Scene data (JSON as text)
    raw_scenes = Column(Text)
    improved_scenes = Column(Text)
    audio_files = Column(Text)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert video object to dictionary."""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'user_input': self.user_input,
            'status': self.status,
            'file_path': self.file_path,
            'duration': self.duration,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'current_step': self.current_step,
            'progress_percent': self.progress_percent,
            'error_message': self.error_message
        }

class VideoProgress(db.Model):
    """Model for tracking video generation progress."""
    __tablename__ = 'video_progress'
    
    id = Column(Integer, primary_key=True)
    video_id = Column(String(36), db.ForeignKey('videos.id'), nullable=False)
    step = Column(String(100), nullable=False)
    status = Column(String(50), nullable=False)  # started, completed, failed
    message = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert progress object to dictionary."""
        return {
            'id': self.id,
            'video_id': self.video_id,
            'step': self.step,
            'status': self.status,
            'message': self.message,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }

class DatabaseManager:
    """Manager class for database operations."""
    
    def __init__(self, db_instance):
        self.db = db_instance
    
    def create_video(self, title: str, description: str, user_input: str) -> Video:
        """Create a new video record."""
        video = Video(
            title=title,
            description=description,
            user_input=user_input,
            status='pending'
        )
        self.db.session.add(video)
        self.db.session.commit()
        return video
    
    def get_video(self, video_id: str) -> Optional[Video]:
        """Get video by ID."""
        return Video.query.filter_by(id=video_id).first()
    
    def get_all_videos(self) -> List[Video]:
        """Get all videos ordered by creation date."""
        return Video.query.order_by(Video.created_at.desc()).all()
    
    def update_video_status(self, video_id: str, status: str, current_step: str = None, 
                           progress_percent: int = None, error_message: str = None) -> bool:
        """Update video status and progress."""
        video = self.get_video(video_id)
        if not video:
            return False
        
        video.status = status
        video.updated_at = datetime.utcnow()
        
        if current_step:
            video.current_step = current_step
        if progress_percent is not None:
            video.progress_percent = progress_percent
        if error_message:
            video.error_message = error_message
        
        self.db.session.commit()
        return True
    
    def update_video_result(self, video_id: str, file_path: str, duration: float = None) -> bool:
        """Update video with final result."""
        video = self.get_video(video_id)
        if not video:
            return False
        
        video.file_path = file_path
        video.duration = duration
        video.status = 'completed'
        video.progress_percent = 100
        video.updated_at = datetime.utcnow()
        
        self.db.session.commit()
        return True
    
    def add_progress_entry(self, video_id: str, step: str, status: str, message: str = None):
        """Add a progress entry."""
        progress = VideoProgress(
            video_id=video_id,
            step=step,
            status=status,
            message=message
        )
        self.db.session.add(progress)
        self.db.session.commit()
        return progress
    
    def get_video_progress(self, video_id: str) -> List[VideoProgress]:
        """Get all progress entries for a video."""
        return VideoProgress.query.filter_by(video_id=video_id).order_by(VideoProgress.timestamp.asc()).all()

def init_database(app):
    """Initialize the database with the Flask app."""
    # Ensure data directory exists
    data_dir = os.getenv('DATA_DIR', 'data')
    os.makedirs(data_dir, exist_ok=True)
    
    with app.app_context():
        db.create_all()
        print("Database initialized successfully") 