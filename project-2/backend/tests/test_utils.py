"""
Test utilities and helper functions for comprehensive testing.

This module provides reusable utilities for test setup, data generation,
and common testing patterns to improve maintainability and consistency.
"""

import os
import time
import json
import logging
from typing import Dict, Any, List, Optional, Callable
from unittest.mock import MagicMock, patch
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class VideoTestingMixin:
    """Mixin class providing common video testing functionality."""
    
    def create_test_video(self, client, video_data: Dict[str, Any]) -> str:
        """
        Create a test video and return its ID with error handling.
        
        Args:
            client: Flask test client
            video_data: Video creation payload
            
        Returns:
            Video ID string
            
        Raises:
            AssertionError: If video creation fails
        """
        try:
            response = client.post('/api/videos', json=video_data)
            assert response.status_code == 201, f"Video creation failed: {response.status_code}"
            
            response_data = response.get_json()
            assert response_data and 'video' in response_data, "Invalid response structure"
            
            video_id = response_data['video']['id']
            assert video_id, "Video ID should not be empty"
            
            logger.info(f"Created test video with ID: {video_id}")
            return video_id
            
        except Exception as e:
            raise AssertionError(f"Failed to create test video: {e}")
    
    def poll_video_completion(self, client, video_id: str, timeout: int = 30) -> str:
        """
        Poll video until completion with comprehensive error handling.
        
        Args:
            client: Flask test client
            video_id: ID of video to poll
            timeout: Maximum polling time in seconds
            
        Returns:
            Final video status
        """
        deadline = time.time() + timeout
        poll_count = 0
        last_status = None
        
        while time.time() < deadline:
            try:
                poll_count += 1
                response = client.get(f'/api/videos/{video_id}')
                
                if response.status_code != 200:
                    logger.warning(f"Poll {poll_count}: Status code {response.status_code}")
                    time.sleep(0.5)
                    continue
                
                response_data = response.get_json()
                if not response_data or 'video' not in response_data:
                    logger.warning(f"Poll {poll_count}: Invalid response structure")
                    time.sleep(0.5)
                    continue
                
                current_status = response_data['video'].get('status', 'unknown')
                
                if current_status != last_status:
                    logger.info(f"Poll {poll_count}: Status changed to '{current_status}'")
                    last_status = current_status
                
                # Check for terminal states
                if current_status in ['completed', 'failed', 'cancelled']:
                    logger.info(f"Video reached terminal state: {current_status}")
                    return current_status
                
                time.sleep(0.5)
                
            except Exception as e:
                logger.warning(f"Poll {poll_count}: Error - {e}")
                time.sleep(0.5)
        
        logger.warning(f"Polling timed out, last status: {last_status}")
        return last_status or 'timeout'
    
    def cleanup_video(self, client, video_id: str) -> bool:
        """
        Clean up a test video with error handling.
        
        Args:
            client: Flask test client
            video_id: ID of video to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            response = client.delete(f'/api/videos/{video_id}')
            success = response.status_code in [200, 404]  # 404 is OK if already deleted
            
            if success:
                logger.info(f"Successfully cleaned up video {video_id}")
            else:
                logger.warning(f"Failed to cleanup video {video_id}: {response.status_code}")
                
            return success
            
        except Exception as e:
            logger.warning(f"Error cleaning up video {video_id}: {e}")
            return False


class MockServiceManager:
    """Manager for consistently mocking external services across tests."""
    
    def __init__(self):
        self.active_patches = []
    
    @contextmanager
    def mock_openai_services(self, 
                           scene_response: Optional[str] = None,
                           audio_response: Optional[bytes] = None):
        """
        Context manager for mocking OpenAI services.
        
        Args:
            scene_response: Custom scene generation response
            audio_response: Custom audio generation response
        """
        # Default responses
        if scene_response is None:
            scene_response = json.dumps([{
                "description": "Test scene description",
                "caption_text": "Test scene caption",
                "duration": 5
            }])
        
        if audio_response is None:
            audio_response = b"MOCK_AUDIO_DATA"
        
        # Create mocks
        with patch('agents.scene_generator.openai') as mock_openai, \
             patch('agents.audio_agent.openai') as mock_audio_openai:
            
            # Configure scene generation mock
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = scene_response
            mock_openai.chat.completions.create.return_value = mock_response
            
            # Configure audio generation mock
            mock_audio_response = MagicMock()
            mock_audio_response.content = audio_response
            mock_audio_openai.audio.speech.create.return_value = mock_audio_response
            
            yield {
                'scene_generator': mock_openai,
                'audio_generator': mock_audio_openai
            }
    
    @contextmanager
    def mock_video_processing(self, output_path: Optional[str] = None):
        """
        Context manager for mocking video processing services.
        
        Args:
            output_path: Path to mock output video file
        """
        if output_path is None:
            output_path = "/tmp/mock_video.mp4"
        
        with patch('agents.video_agent.moviepy') as mock_moviepy:
            # Configure video processing mock
            mock_clip = MagicMock()
            mock_clip.duration = 15.0
            mock_moviepy.VideoFileClip.return_value = mock_clip
            
            # Mock file operations
            with patch('os.path.exists', return_value=True), \
                 patch('os.path.getsize', return_value=1024):
                
                yield {
                    'moviepy': mock_moviepy,
                    'output_path': output_path
                }


class TestDataValidator:
    """Validator for test data and responses."""
    
    @staticmethod
    def validate_video_structure(video_data: Dict[str, Any], 
                               required_fields: Optional[List[str]] = None) -> bool:
        """
        Validate video data structure.
        
        Args:
            video_data: Video data to validate
            required_fields: Optional list of required fields
            
        Returns:
            True if valid, False otherwise
        """
        if required_fields is None:
            required_fields = ['id', 'title', 'description', 'status']
        
        try:
            assert isinstance(video_data, dict), "Video data must be a dictionary"
            
            for field in required_fields:
                assert field in video_data, f"Missing required field: {field}"
                assert video_data[field] is not None, f"Field '{field}' cannot be None"
            
            # Validate specific field types
            if 'id' in video_data:
                assert isinstance(video_data['id'], str), "ID must be a string"
                assert len(video_data['id']) > 0, "ID cannot be empty"
            
            if 'status' in video_data:
                valid_statuses = ['pending', 'processing', 'completed', 'failed', 'cancelled']
                assert video_data['status'] in valid_statuses, f"Invalid status: {video_data['status']}"
            
            return True
            
        except AssertionError as e:
            logger.error(f"Video structure validation failed: {e}")
            return False
    
    @staticmethod
    def validate_progress_structure(progress_data: List[Dict[str, Any]]) -> bool:
        """
        Validate progress data structure.
        
        Args:
            progress_data: Progress entries to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            assert isinstance(progress_data, list), "Progress data must be a list"
            
            for i, entry in enumerate(progress_data):
                assert isinstance(entry, dict), f"Progress entry {i} must be a dictionary"
                
                # Check for at least one common progress field
                progress_fields = ['stage', 'step', 'status', 'message', 'timestamp', 'created_at']
                has_progress_field = any(field in entry for field in progress_fields)
                assert has_progress_field, f"Progress entry {i} missing progress fields"
            
            return True
            
        except AssertionError as e:
            logger.error(f"Progress structure validation failed: {e}")
            return False
    
    @staticmethod
    def validate_api_response(response, expected_status: int = 200, 
                            should_have_success_field: bool = True) -> bool:
        """
        Validate API response structure and status.
        
        Args:
            response: Flask test response
            expected_status: Expected HTTP status code
            should_have_success_field: Whether response should have success field
            
        Returns:
            True if valid, False otherwise
        """
        try:
            assert response.status_code == expected_status, \
                f"Expected status {expected_status}, got {response.status_code}"
            
            if response.status_code < 300:  # Success responses
                json_data = response.get_json()
                if json_data and should_have_success_field:
                    assert 'success' in json_data, "Response should have 'success' field"
                    if json_data.get('success') is False:
                        assert 'error' in json_data, "Failed response should have error details"
            
            return True
            
        except AssertionError as e:
            logger.error(f"API response validation failed: {e}")
            return False


class PerformanceTracker:
    """Utility for tracking test performance and timing."""
    
    def __init__(self):
        self.timings = {}
        self.start_times = {}
    
    def start_timing(self, operation: str):
        """Start timing an operation."""
        self.start_times[operation] = time.time()
        logger.debug(f"Started timing: {operation}")
    
    def stop_timing(self, operation: str) -> float:
        """
        Stop timing an operation and return duration.
        
        Args:
            operation: Name of operation to stop timing
            
        Returns:
            Duration in seconds
        """
        if operation not in self.start_times:
            logger.warning(f"No start time found for operation: {operation}")
            return 0.0
        
        duration = time.time() - self.start_times[operation]
        self.timings[operation] = duration
        del self.start_times[operation]
        
        logger.info(f"Operation '{operation}' took {duration:.2f} seconds")
        return duration
    
    def get_timing(self, operation: str) -> Optional[float]:
        """Get recorded timing for an operation."""
        return self.timings.get(operation)
    
    def get_all_timings(self) -> Dict[str, float]:
        """Get all recorded timings."""
        return self.timings.copy()
    
    def assert_timing_under_threshold(self, operation: str, threshold: float):
        """Assert that an operation completed under a time threshold."""
        duration = self.get_timing(operation)
        assert duration is not None, f"No timing recorded for operation: {operation}"
        assert duration < threshold, \
            f"Operation '{operation}' took {duration:.2f}s, expected under {threshold}s"


class TestEnvironmentManager:
    """Manager for test environment setup and cleanup."""
    
    def __init__(self):
        self.cleanup_functions = []
        self.temp_files = []
        self.test_videos = []
    
    def register_cleanup(self, cleanup_func: Callable, *args, **kwargs):
        """Register a cleanup function to be called after test."""
        self.cleanup_functions.append((cleanup_func, args, kwargs))
    
    def register_temp_file(self, file_path: str):
        """Register a temporary file for cleanup."""
        self.temp_files.append(file_path)
    
    def register_test_video(self, client, video_id: str):
        """Register a test video for cleanup."""
        self.test_videos.append((client, video_id))
    
    def cleanup_all(self):
        """Execute all registered cleanup operations."""
        cleanup_errors = []
        
        # Cleanup test videos
        for client, video_id in self.test_videos:
            try:
                response = client.delete(f'/api/videos/{video_id}')
                if response.status_code in [200, 404]:
                    logger.info(f"Cleaned up test video: {video_id}")
                else:
                    logger.warning(f"Failed to cleanup video {video_id}: {response.status_code}")
            except Exception as e:
                cleanup_errors.append(f"Video cleanup error for {video_id}: {e}")
        
        # Cleanup temporary files
        for file_path in self.temp_files:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.info(f"Cleaned up temp file: {file_path}")
            except Exception as e:
                cleanup_errors.append(f"File cleanup error for {file_path}: {e}")
        
        # Execute custom cleanup functions
        for cleanup_func, args, kwargs in self.cleanup_functions:
            try:
                cleanup_func(*args, **kwargs)
                logger.info(f"Executed cleanup function: {cleanup_func.__name__}")
            except Exception as e:
                cleanup_errors.append(f"Cleanup function error {cleanup_func.__name__}: {e}")
        
        # Log any cleanup errors
        if cleanup_errors:
            logger.warning(f"Cleanup errors occurred: {cleanup_errors}")
        
        # Reset state
        self.cleanup_functions.clear()
        self.temp_files.clear()
        self.test_videos.clear()


# Global instances for convenience
mock_service_manager = MockServiceManager()
test_data_validator = TestDataValidator()


def create_test_environment_manager() -> TestEnvironmentManager:
    """Factory function to create a new test environment manager."""
    return TestEnvironmentManager()


def create_performance_tracker() -> PerformanceTracker:
    """Factory function to create a new performance tracker."""
    return PerformanceTracker()


# Export commonly used utilities
__all__ = [
    'VideoTestingMixin',
    'MockServiceManager',
    'TestDataValidator',
    'PerformanceTracker',
    'TestEnvironmentManager',
    'mock_service_manager',
    'test_data_validator',
    'create_test_environment_manager',
    'create_performance_tracker'
]
