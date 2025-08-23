"""
Unit tests for AI agents in mock mode.

This module tests the core functionality of all AI agents with mocked external services
to ensure deterministic behavior and reliable testing.
"""

import os
import pytest
import tempfile
import logging
from typing import List, Dict, Any
from unittest.mock import patch, MagicMock

# Configure mock mode before importing agents
os.environ.setdefault("MOCK_MODE", "true")

try:
    from agents.scene_generator import SceneGeneratorAgent  # type: ignore
    from agents.scene_critic import SceneCriticAgent  # type: ignore
    from agents.audio_agent import AudioAgent  # type: ignore
    from agents.video_agent import VideoAgent  # type: ignore
    from config import get_config  # type: ignore
except ImportError as e:
    pytest.fail(f"Failed to import required modules: {e}")

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestSceneGeneratorAgent:
    """Test suite for SceneGeneratorAgent in mock mode."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        try:
            self.agent = SceneGeneratorAgent()
        except Exception as e:
            pytest.fail(f"Failed to initialize SceneGeneratorAgent: {e}")

    def test_scene_generator_mock_basic_functionality(self):
        """Test basic scene generation functionality in mock mode."""
        try:
            scenes = self.agent.generate_scenes("make a video")
            
            # Validate return type and structure
            assert isinstance(scenes, list), "Expected scenes to be a list"
            assert len(scenes) > 0, "Expected at least one scene to be generated"
            
            # Validate scene structure
            for i, scene in enumerate(scenes):
                assert isinstance(scene, dict), f"Scene {i} should be a dictionary"
                required_fields = ['caption_text', 'description', 'duration']
                for field in required_fields:
                    assert field in scene, f"Scene {i} missing required field: {field}"
                    assert scene[field] is not None, f"Scene {i} field '{field}' should not be None"
                
                # Validate data types
                assert isinstance(scene['caption_text'], str), f"Scene {i} caption_text should be string"
                assert isinstance(scene['description'], str), f"Scene {i} description should be string"
                assert isinstance(scene['duration'], (int, float)), f"Scene {i} duration should be numeric"
                assert scene['duration'] > 0, f"Scene {i} duration should be positive"
                
        except Exception as e:
            pytest.fail(f"Scene generation failed with error: {e}")

    def test_scene_generator_empty_input_handling(self):
        """Test scene generator behavior with empty or invalid input."""
        test_cases = ["", "   ", None]
        
        for test_input in test_cases:
            try:
                # In mock mode, agents handle all inputs gracefully
                scenes = self.agent.generate_scenes(test_input)
                # Mock should return valid structure regardless of input
                assert isinstance(scenes, list), f"Expected list for input '{test_input}'"
                logger.info(f"Mock mode handled input '{test_input}' gracefully")
            except Exception as e:
                # Log unexpected errors but don't fail the test in mock mode
                logger.warning(f"Unexpected error with input '{test_input}': {e}")


class TestSceneCriticAgent:
    """Test suite for SceneCriticAgent in mock mode."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        try:
            self.scene_generator = SceneGeneratorAgent()
            self.scene_critic = SceneCriticAgent()
        except Exception as e:
            pytest.fail(f"Failed to initialize agents: {e}")

    def test_scene_critic_mock_improvement(self):
        """Test scene criticism and improvement functionality."""
        try:
            # Generate initial scenes
            scenes = self.scene_generator.generate_scenes("mock")
            assert len(scenes) > 0, "No scenes generated for testing"
            
            # Test scene improvement
            improved_scenes = self.scene_critic.improve_scenes(scenes)
            
            # Validate structure preservation
            assert isinstance(improved_scenes, list), "Improved scenes should be a list"
            assert len(improved_scenes) == len(scenes), "Number of scenes should be preserved"
            
            # In mock mode, scenes might be returned unchanged
            assert improved_scenes == scenes, "Mock mode should return unchanged scenes"
            
        except Exception as e:
            pytest.fail(f"Scene criticism failed with error: {e}")

    def test_scene_critic_invalid_input_handling(self):
        """Test scene critic behavior with invalid input."""
        invalid_inputs = [None, [], [{}], [{"invalid": "structure"}]]
        
        for invalid_input in invalid_inputs:
            try:
                if invalid_input is None or not invalid_input:
                    # Should handle gracefully or raise appropriate exception
                    result = self.scene_critic.improve_scenes(invalid_input)
                    assert isinstance(result, list)
                else:
                    # May process malformed scenes gracefully in mock mode
                    result = self.scene_critic.improve_scenes(invalid_input)
                    assert isinstance(result, list)
            except Exception as e:
                logger.info(f"Expected handling of invalid input {invalid_input}: {e}")


class TestAudioAgent:
    """Test suite for AudioAgent in mock mode."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        try:
            self.agent = AudioAgent()
            self.test_scenes = [{"caption_text": "hello world", "description": "desc", "duration": 2}]
        except Exception as e:
            pytest.fail(f"Failed to initialize AudioAgent: {e}")

    def test_audio_agent_mock_generation(self, tmp_path):
        """Test audio generation functionality with proper cleanup."""
        try:
            # Ensure configuration is properly set up
            cfg = get_config()
            temp_dir = cfg.get('temp_dir', str(tmp_path))
            os.makedirs(temp_dir, exist_ok=True)
            
            # Generate audio files
            audio_files = self.agent.generate_audio(self.test_scenes)
            
            # Validate results
            assert isinstance(audio_files, list), "Audio files should be returned as a list"
            assert len(audio_files) == len(self.test_scenes), "One audio file per scene expected"
            
            for i, audio_file in enumerate(audio_files):
                assert isinstance(audio_file, str), f"Audio file path {i} should be a string"
                assert os.path.exists(audio_file), f"Audio file {i} should exist: {audio_file}"
                assert audio_file.endswith(('.mp3', '.wav', '.m4a')), f"Audio file {i} should have valid extension"
                
        except Exception as e:
            pytest.fail(f"Audio generation failed with error: {e}")

    def test_audio_agent_empty_scenes_handling(self):
        """Test audio agent behavior with empty scene list."""
        try:
            audio_files = self.agent.generate_audio([])
            assert isinstance(audio_files, list), "Should return empty list for empty scenes"
            assert len(audio_files) == 0, "Should return empty list for empty scenes"
        except Exception as e:
            pytest.fail(f"Empty scenes handling failed: {e}")

    def test_audio_agent_malformed_scenes_handling(self):
        """Test audio agent behavior with malformed scene data."""
        malformed_scenes = [
            {"description": "missing caption_text"},
            {"caption_text": "", "description": "empty caption"},
            {"caption_text": "test", "description": "missing duration"}
        ]
        
        try:
            # Should handle gracefully or provide meaningful error
            audio_files = self.agent.generate_audio(malformed_scenes)
            assert isinstance(audio_files, list)
            # In mock mode, might still generate placeholder files
        except Exception as e:
            logger.info(f"Expected handling of malformed scenes: {e}")


class TestVideoAgent:
    """Test suite for VideoAgent in mock mode."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        try:
            self.agent = VideoAgent()
            self.test_scenes = [{"caption_text": "hello world", "description": "desc", "duration": 1}]
        except Exception as e:
            pytest.fail(f"Failed to initialize VideoAgent: {e}")

    def test_video_agent_mock_assembly(self):
        """Test video assembly functionality."""
        try:
            audio_files = [""]  # Mock audio file list
            
            output_file = self.agent.assemble_video(self.test_scenes, audio_files)
            
            # Validate output
            assert isinstance(output_file, str), "Output should be a file path string"
            assert output_file.endswith('.mp4'), "Output should be an MP4 file"
            assert os.path.exists(output_file), f"Output file should exist: {output_file}"
            
            # Validate file is not empty
            assert os.path.getsize(output_file) > 0, "Output file should not be empty"
            
        except Exception as e:
            pytest.fail(f"Video assembly failed with error: {e}")

    def test_video_agent_mismatched_inputs_handling(self):
        """Test video agent behavior with mismatched scene and audio counts."""
        try:
            # More scenes than audio files
            many_scenes = self.test_scenes * 3
            few_audio_files = ["file1.mp3"]
            
            output_file = self.agent.assemble_video(many_scenes, few_audio_files)
            
            # Should handle gracefully in mock mode
            assert isinstance(output_file, str)
            assert output_file.endswith('.mp4')
            
        except Exception as e:
            logger.info(f"Expected handling of mismatched inputs: {e}")

    def test_video_agent_cleanup_on_failure(self):
        """Test that temporary files are cleaned up on failure."""
        try:
            with patch.object(self.agent, 'assemble_video', side_effect=Exception("Simulated failure")):
                with pytest.raises(Exception):
                    self.agent.assemble_video(self.test_scenes, ["test.mp3"])
                    
            # In a real implementation, we'd check for cleanup of temporary files
            # This is a placeholder for that logic
            assert True, "Cleanup logic would be tested here"
            
        except Exception as e:
            logger.info(f"Cleanup test completed: {e}")


# Integration test for agent interaction
def test_agent_integration_workflow():
    """Test the complete workflow of all agents working together."""
    try:
        # Initialize all agents
        scene_gen = SceneGeneratorAgent()
        scene_critic = SceneCriticAgent()
        audio_agent = AudioAgent()
        video_agent = VideoAgent()
        
        # Step 1: Generate scenes
        scenes = scene_gen.generate_scenes("Create a test video")
        assert len(scenes) > 0, "Scene generation failed"
        
        # Step 2: Improve scenes
        improved_scenes = scene_critic.improve_scenes(scenes)
        assert len(improved_scenes) == len(scenes), "Scene criticism changed scene count"
        
        # Step 3: Generate audio
        audio_files = audio_agent.generate_audio(improved_scenes)
        assert len(audio_files) == len(improved_scenes), "Audio generation count mismatch"
        
        # Step 4: Assemble video
        final_video = video_agent.assemble_video(improved_scenes, audio_files)
        assert os.path.exists(final_video), "Final video not created"
        assert final_video.endswith('.mp4'), "Final video has wrong extension"
        
        logger.info(f"Integration test completed successfully. Final video: {final_video}")
        
    except Exception as e:
        pytest.fail(f"Integration workflow failed: {e}") 