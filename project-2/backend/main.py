#!/usr/bin/env python3
"""
Simple Agentic AI Video Generator
Entry point for the video generation application.
"""

import logging
import sys
import os
from typing import Dict, Any

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import validate_config
from graph import VideoGeneratorGraph

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main entry point for the video generator."""
    try:
        # Validate configuration
        validate_config()
        logger.info("Configuration validated successfully")
        
        # Get user input
        if len(sys.argv) > 1:
            user_input = " ".join(sys.argv[1:])
        else:
            user_input = input("Enter your video idea: ")
        
        if not user_input.strip():
            logger.error("No input provided")
            return
        
        logger.info(f"Processing video request: {user_input}")
        
        # Create and run the video generator
        generator = VideoGeneratorGraph()
        result = generator.generate_video(user_input)
        
        # Report results
        print_results(result)
        
    except Exception as e:
        logger.error(f"Error in main: {e}")
        print(f"Error: {e}")
        sys.exit(1)

def print_results(result: Dict[str, Any]):
    """Print the results of video generation."""
    print("\n" + "="*50)
    print("VIDEO GENERATION RESULTS")
    print("="*50)
    
    current_step = result.get("current_step", "unknown")
    print(f"Final Step: {current_step}")
    
    if result.get("error"):
        print(f"Error: {result['error']}")
    
    # Print scene information
    scenes = result.get("improved_scenes", result.get("raw_scenes", []))
    if scenes:
        print(f"\nGenerated {len(scenes)} scenes:")
        for i, scene in enumerate(scenes, 1):
            print(f"  Scene {i}: {scene.get('caption_text', 'No caption')}")
            print(f"    Duration: {scene.get('duration', 0)}s")
    
    # Print audio files
    audio_files = result.get("audio_files", [])
    if audio_files:
        print(f"\nGenerated {len(audio_files)} audio files:")
        for i, audio_file in enumerate(audio_files, 1):
            print(f"  Audio {i}: {audio_file}")
    
    # Print final video
    final_video = result.get("final_video", "")
    if final_video:
        print(f"\nFinal Video: {final_video}")
        print("✅ Video generation completed successfully!")
    else:
        print("\n❌ Video generation failed!")
    
    # Print messages
    messages = result.get("messages", [])
    if messages:
        print(f"\nWorkflow Messages:")
        for msg in messages:
            print(f"  {msg.get('content', '')}")
    
    print("="*50)

def test_setup():
    """Test the setup with a simple example."""
    print("Testing video generator setup...")
    
    try:
        # Test configuration
        validate_config()
        print("✅ Configuration validated")
        
        # Test agent creation
        generator = VideoGeneratorGraph()
        print("✅ Video generator created")
        
        # Test with sample input
        test_input = "Create a simple test video"
        result = generator.generate_video(test_input)
        
        if result.get("final_video"):
            print("✅ Test video generated successfully")
        else:
            print("❌ Test video generation failed")
            
        print_results(result)
        
    except Exception as e:
        print(f"❌ Setup test failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        test_setup()
    else:
        main() 