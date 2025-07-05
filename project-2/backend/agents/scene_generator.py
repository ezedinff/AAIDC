import logging
from typing import Dict, Any, List
from openai import OpenAI
from config import get_config
from prompt_utils import prompt_manager

logger = logging.getLogger(__name__)

class SceneGeneratorAgent:
    """Agent responsible for generating video scenes from user input."""
    
    def __init__(self):
        self.config = get_config()
        self.client = OpenAI(api_key=self.config["openai_api_key"])
    
    def generate_scenes(self, user_input: str) -> List[Dict[str, Any]]:
        """Generate video scenes from user input."""
        try:
            # Use dynamic prompt generation
            prompt = prompt_manager.get_scene_generation_prompt(
                user_input, 
                self.config["scene_count"], 
                self.config["video_duration"]
            )
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )
            
            scenes = self._parse_response(response.choices[0].message.content)
            logger.info(f"Generated {len(scenes)} scenes")
            return scenes
            
        except Exception as e:
            logger.error(f"Error generating scenes: {e}")
            return []
    
    def _create_scene_prompt(self, user_input: str) -> str:
        """Create the prompt for scene generation."""
        return f"""
        Create {self.config['scene_count']} engaging video scenes based on this input: "{user_input}"
        
        Each scene should have:
        - description: A detailed description of what happens in the scene
        - caption_text: The text that will appear on screen (keep it concise and readable)
        - duration: How long the scene should last in seconds
        
        Total video duration should be approximately {self.config['video_duration']} seconds.
        
        Format your response as a JSON array of objects with these fields.
        Make sure the text is clear and suitable for voice narration.
        """
    
    def _parse_response(self, response: str) -> List[Dict[str, Any]]:
        """Parse the AI response into structured scene data."""
        try:
            import json
            # Try to extract JSON from the response
            start_idx = response.find('[')
            end_idx = response.rfind(']') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_str = response[start_idx:end_idx]
                scenes = json.loads(json_str)
                return scenes
            else:
                # Fallback: create basic scenes if JSON parsing fails
                return self._create_fallback_scenes()
                
        except Exception as e:
            logger.error(f"Error parsing response: {e}")
            return self._create_fallback_scenes()
    
    def _create_fallback_scenes(self) -> List[Dict[str, Any]]:
        """Create fallback scenes if parsing fails."""
        duration_per_scene = self.config["video_duration"] // self.config["scene_count"]
        return [
            {
                "description": f"Scene {i+1} content",
                "caption_text": f"Scene {i+1}",
                "duration": duration_per_scene
            }
            for i in range(self.config["scene_count"])
        ] 