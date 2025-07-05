import logging
import os
from typing import Dict, Any, List
from openai import OpenAI
from config import get_config
from prompt_utils import prompt_manager

logger = logging.getLogger(__name__)

class AudioAgent:
    """Agent responsible for generating audio from scene descriptions."""
    
    def __init__(self):
        self.config = get_config()
        self.client = OpenAI(api_key=self.config["openai_api_key"])
        self._ensure_output_dirs()
    
    def _ensure_output_dirs(self):
        """Ensure output directories exist."""
        os.makedirs(self.config["output_dir"], exist_ok=True)
        os.makedirs(self.config["temp_dir"], exist_ok=True)
    
    def generate_audio(self, scenes: List[Dict[str, Any]]) -> List[str]:
        """Generate audio files for each scene."""
        audio_files = []
        
        for i, scene in enumerate(scenes):
            try:
                audio_file = self._generate_scene_audio(scene, i)
                audio_files.append(audio_file)
                logger.info(f"Generated audio for scene {i+1}: {audio_file}")
                
            except Exception as e:
                logger.error(f"Error generating audio for scene {i+1}: {e}")
                # Create empty audio file as fallback
                audio_files.append(self._create_silent_audio(scene["duration"]))
        
        return audio_files
    
    def _generate_scene_audio(self, scene: Dict[str, Any], scene_index: int) -> str:
        """Generate audio for a single scene."""
        # Create narration text from scene description
        narration_text = self._create_narration_text(scene)
        
        # Generate audio using OpenAI TTS
        response = self.client.audio.speech.create(
            model="tts-1",
            voice=self.config["audio_voice"],
            input=narration_text,
            response_format="mp3"
        )
        
        # Save audio file
        audio_filename = f"scene_{scene_index + 1}_audio.mp3"
        audio_path = os.path.join(self.config["temp_dir"], audio_filename)
        
        with open(audio_path, 'wb') as audio_file:
            audio_file.write(response.content)
        
        return audio_path
    
    def _create_narration_text(self, scene: Dict[str, Any]) -> str:
        """Create narration text from scene data."""
        try:
            # Use dynamic prompt generation for better narration
            prompt = prompt_manager.get_audio_generation_prompt(scene)
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.6,
                max_tokens=200
            )
            
            narration = response.choices[0].message.content.strip()
            logger.info(f"Generated narration: {narration[:50]}...")
            
        except Exception as e:
            logger.warning(f"Failed to generate dynamic narration: {e}")
            # Fallback to original method
            narration = scene.get("caption_text", "")
            if len(narration) < 10:
                narration = scene.get("description", "")
        
        # Clean up the text for better speech synthesis
        narration = self._clean_text_for_speech(narration)
        
        return narration
    
    def _clean_text_for_speech(self, text: str) -> str:
        """Clean text for better speech synthesis."""
        # Remove special characters that might cause issues
        text = text.replace("[", "").replace("]", "")
        text = text.replace("*", "").replace("#", "")
        
        # Ensure proper sentence ending
        if not text.endswith('.') and not text.endswith('!') and not text.endswith('?'):
            text += '.'
        
        return text
    
    def _create_silent_audio(self, duration: int) -> str:
        """Create a silent audio file as fallback."""
        try:
            # Try to import moviepy for silent audio
            from moviepy import AudioClip
            
            # Create silent audio clip
            silent_clip = AudioClip(lambda t: 0, duration=duration)
            
            # Save as mp3
            audio_filename = f"silent_{duration}s.mp3"
            audio_path = os.path.join(self.config["temp_dir"], audio_filename)
            silent_clip.write_audiofile(audio_path, verbose=False, logger=None)
            
            return audio_path
            
        except Exception as e:
            logger.warning(f"Cannot create silent audio (moviepy not available): {e}")
            return "" 