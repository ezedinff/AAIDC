#!/usr/bin/env python3
"""
Simple test script to verify SSE endpoint is working correctly
"""

import requests
import json
import time
import threading
from sseclient import SSEClient

def test_sse_connection(video_id):
    """Test SSE connection for a video ID."""
    print(f"Testing SSE connection for video {video_id}")
    
    try:
        # Create SSE client
        sse_url = f"http://localhost:5000/api/videos/{video_id}/events"
        print(f"Connecting to: {sse_url}")
        
        messages = SSEClient(sse_url)
        event_count = 0
        
        for msg in messages:
            if msg.data:
                try:
                    data = json.loads(msg.data)
                    event_count += 1
                    print(f"[{event_count}] SSE Event: {data}")
                    
                    # Stop after 10 events or completion
                    if event_count >= 10 or data.get('type') == 'complete':
                        print(f"Stopping after {event_count} events")
                        break
                        
                except json.JSONDecodeError:
                    print(f"[{event_count}] Raw message: {msg.data}")
                    
    except Exception as e:
        print(f"SSE connection error: {e}")

def create_test_video():
    """Create a test video and monitor its progress."""
    print("Creating test video...")
    
    data = {
        'title': 'SSE Real-time Test',
        'description': 'Testing real-time SSE progress updates',
        'user_input': 'Create a simple video about the benefits of drinking water with white background and black text'
    }
    
    try:
        response = requests.post('http://localhost:5000/api/videos', json=data)
        if response.status_code == 201:
            video_data = response.json()
            video_id = video_data['video']['id']
            print(f"Created video: {video_id}")
            
            # Start SSE monitoring in a separate thread
            sse_thread = threading.Thread(target=test_sse_connection, args=(video_id,))
            sse_thread.daemon = True
            sse_thread.start()
            
            # Monitor progress for 60 seconds
            for i in range(12):  # 12 * 5 seconds = 60 seconds
                time.sleep(5)
                
                # Check video status
                response = requests.get(f'http://localhost:5000/api/videos/{video_id}')
                if response.status_code == 200:
                    video = response.json()['video']
                    print(f"[{i*5}s] Status: {video['status']}, Progress: {video['progress_percent']}%, Step: {video['current_step']}")
                    
                    if video['status'] in ['completed', 'failed']:
                        print(f"Video {video['status']}!")
                        break
                else:
                    print(f"Failed to get video status: {response.text}")
            
            # Wait for SSE thread to finish
            sse_thread.join(timeout=5)
            
        else:
            print(f"Failed to create video: {response.text}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("Starting SSE Integration Test")
    print("=" * 50)
    
    # Check if sseclient is available
    try:
        import sseclient
        print("✓ sseclient module available")
    except ImportError:
        print("✗ sseclient module not available")
        print("Install with: pip install sseclient-py")
        exit(1)
    
    # Test health check
    try:
        response = requests.get('http://localhost:5000/api/health')
        if response.status_code == 200:
            print("✓ Backend health check passed")
        else:
            print("✗ Backend health check failed")
            exit(1)
    except Exception as e:
        print(f"✗ Backend not accessible: {e}")
        exit(1)
    
    # Run the test
    create_test_video()
    print("\nTest completed!") 