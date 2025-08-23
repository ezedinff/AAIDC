"""
End-to-end integration tests for the complete video generation workflow.

This module tests the entire video creation pipeline from initial request
through final download, including error handling and edge cases.
"""

import os
import time
import pytest
import logging
from typing import Dict, Any, Optional
from unittest.mock import patch, MagicMock

# Configure mock mode before importing modules
os.environ.setdefault("MOCK_MODE", "true")

from api import create_app  # type: ignore
from database import db  

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test configuration constants
POLLING_TIMEOUT_SECONDS = 30
POLLING_INTERVAL_SECONDS = 0.5
MAX_RETRIES = 3


@pytest.fixture(scope="module")
def client():
    """
    Create a test Flask application client for E2E testing.
    
    Yields:
        FlaskClient: Test client for making API requests
    """
    try:
        app = create_app()
        app.testing = True
        app.config['TESTING'] = True
        
        with app.test_client() as test_client:
            with app.app_context():
                # Ensure database is properly initialized
                db.create_all()
            yield test_client
            
    except Exception as e:
        pytest.fail(f"Failed to create test client: {e}")


@pytest.fixture
def sample_video_request() -> Dict[str, Any]:
    """Provide sample video generation request data."""
    return {
        "title": "E2E Test Video",
        "description": "End-to-end test video generation",
        "user_input": "Create a short mock video about testing workflows",
        "style": "educational",
        "duration": 15
    }


def test_create_to_complete_and_download(client, sample_video_request):
    """Test the complete successful video generation workflow with comprehensive error handling."""
    video_id = None
    
    try:
        # Step 1: Create video request with proper error handling
        logger.info("Step 1: Creating video generation request")
        response = client.post('/api/videos', json=sample_video_request)
        
        assert response.status_code == 201, f"Video creation failed with status {response.status_code}"
        
        response_data = response.get_json()
        assert response_data is not None, "Response should contain JSON data"
        assert 'video' in response_data, "Response should contain video data"
        
        video_data = response_data['video']
        video_id = video_data['id']
        assert video_id is not None, "Video should have a valid ID"
        
        logger.info(f"Video created successfully with ID: {video_id}")

        # Step 2: Poll for completion with timeout and error handling
        logger.info("Step 2: Polling for video completion")
        final_status = poll_for_completion(client, video_id)
        
        assert final_status == 'completed', f"Expected 'completed' status, got '{final_status}'"
        logger.info("Video generation completed successfully")

        # Step 3: Verify progress tracking with error handling
        logger.info("Step 3: Verifying progress tracking")
        verify_progress_tracking(client, video_id)

        # Step 4: Test download functionality with comprehensive validation
        logger.info("Step 4: Testing video download")
        verify_download_functionality(client, video_id)
        
        logger.info("Complete E2E workflow test passed successfully")

    except Exception as e:
        logger.error(f"E2E workflow test failed: {e}")
        if video_id:
            cleanup_test_video(client, video_id)
        pytest.fail(f"Complete workflow test failed: {e}")


def poll_for_completion(client, video_id: str, timeout: int = POLLING_TIMEOUT_SECONDS) -> Optional[str]:
    """
    Poll video status until completion or timeout with comprehensive error handling.
    
    Args:
        client: Flask test client
        video_id: ID of video to poll
        timeout: Maximum time to poll in seconds
        
    Returns:
        Final status of the video
    """
    deadline = time.time() + timeout
    last_status = None
    poll_count = 0
    
    logger.info(f"Starting to poll video {video_id} for up to {timeout} seconds")
    
    while time.time() < deadline:
        try:
            poll_count += 1
            response = client.get(f'/api/videos/{video_id}')
            
            if response.status_code != 200:
                logger.warning(f"Poll {poll_count}: Unexpected status code {response.status_code}")
                time.sleep(POLLING_INTERVAL_SECONDS)
                continue
            
            response_data = response.get_json()
            if not response_data or 'video' not in response_data:
                logger.warning(f"Poll {poll_count}: Invalid response structure")
                time.sleep(POLLING_INTERVAL_SECONDS)
                continue
            
            video_data = response_data['video']
            current_status = video_data.get('status', 'unknown')
            
            if current_status != last_status:
                logger.info(f"Poll {poll_count}: Status changed to '{current_status}'")
                last_status = current_status
            
            # Check for terminal states
            if current_status in ['completed', 'failed', 'cancelled']:
                logger.info(f"Video reached terminal state '{current_status}' after {poll_count} polls")
                return current_status
            
            # Continue polling for non-terminal states
            if current_status in ['pending', 'processing', 'in_progress']:
                time.sleep(POLLING_INTERVAL_SECONDS)
                continue
                
            # Unknown status - log and continue
            logger.warning(f"Poll {poll_count}: Unknown status '{current_status}', continuing to poll")
            time.sleep(POLLING_INTERVAL_SECONDS)
            
        except Exception as e:
            logger.warning(f"Poll {poll_count}: Error during polling: {e}")
            time.sleep(POLLING_INTERVAL_SECONDS)
    
    logger.warning(f"Polling timed out after {timeout} seconds, last status: {last_status}")
    return last_status


def verify_progress_tracking(client, video_id: str):
    """
    Verify that progress tracking is working correctly with error handling.
    
    Args:
        client: Flask test client
        video_id: ID of video to check progress for
    """
    try:
        response = client.get(f'/api/videos/{video_id}/progress')
        
        assert response.status_code == 200, f"Progress endpoint returned {response.status_code}"
        
        response_data = response.get_json()
        assert response_data is not None, "Progress response should contain JSON data"
        assert 'progress' in response_data, "Response should contain progress data"
        
        progress_entries = response_data['progress']
        assert isinstance(progress_entries, list), "Progress should be a list"
        assert len(progress_entries) >= 1, "Should have at least one progress entry"
        
        # Validate progress entry structure
        for i, entry in enumerate(progress_entries):
            assert isinstance(entry, dict), f"Progress entry {i} should be a dictionary"
            # Check for common progress fields (field names may vary by implementation)
            has_required_fields = any(field in entry for field in 
                ['stage', 'step', 'status', 'message', 'timestamp', 'created_at'])
            assert has_required_fields, f"Progress entry {i} missing required fields: {entry}"
        
        logger.info(f"Progress tracking verified: {len(progress_entries)} entries found")
        
    except Exception as e:
        raise AssertionError(f"Progress tracking verification failed: {e}")


def verify_download_functionality(client, video_id: str):
    """
    Verify that video download functionality works correctly with comprehensive validation.
    
    Args:
        client: Flask test client
        video_id: ID of video to download
    """
    try:
        response = client.get(f'/api/videos/{video_id}/download')
        
        assert response.status_code == 200, f"Download endpoint returned {response.status_code}"
        
        # Verify content type
        content_type = response.headers.get('Content-Type', '')
        assert 'video' in content_type.lower() or content_type == 'application/octet-stream', \
            f"Expected video content type, got: {content_type}"
        
        # Verify content exists
        content_length = response.headers.get('Content-Length')
        if content_length:
            assert int(content_length) > 0, "Downloaded content should not be empty"
        
        # Verify actual response data
        response_data = response.get_data()
        assert len(response_data) > 0, "Download response should contain data"
        
        logger.info(f"Download verification successful: {len(response_data)} bytes downloaded")
        
    except Exception as e:
        raise AssertionError(f"Download verification failed: {e}")


def cleanup_test_video(client, video_id: str):
    """
    Clean up test video after test completion or failure.
    
    Args:
        client: Flask test client
        video_id: ID of video to clean up
    """
    try:
        response = client.delete(f'/api/videos/{video_id}')
        if response.status_code == 200:
            logger.info(f"Successfully cleaned up test video {video_id}")
        else:
            logger.warning(f"Failed to clean up test video {video_id}: {response.status_code}")
            
    except Exception as e:
        logger.warning(f"Error during test video cleanup: {e}")


def test_workflow_error_handling(client, sample_video_request):
    """Test workflow behavior with various error conditions."""
    try:
        # Test with invalid request data
        invalid_request = sample_video_request.copy()
        invalid_request["title"] = ""  # Invalid empty title
        
        response = client.post('/api/videos', json=invalid_request)
        assert response.status_code == 400, "Should reject invalid request"
        
        # Test polling non-existent video
        fake_video_id = "non-existent-video-id"
        response = client.get(f'/api/videos/{fake_video_id}')
        assert response.status_code == 404, "Should return 404 for non-existent video"
        
        logger.info("Error handling tests completed successfully")
        
    except Exception as e:
        pytest.fail(f"Error handling test failed: {e}") 