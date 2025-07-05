import logging
from typing import Dict, Any, List
from openai import OpenAI
from config import get_config
from prompt_utils import prompt_manager

logger = logging.getLogger(__name__)

class SceneCriticAgent:
    """Agent responsible for critiquing and improving video scenes."""
    
    def __init__(self):
        self.config = get_config()
        self.client = OpenAI(api_key=self.config["openai_api_key"])
    
    def improve_scenes(self, scenes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Improve the provided scenes through AI critique."""
        try:
            # Use dynamic prompt generation
            prompt = prompt_manager.get_scene_critique_prompt(scenes)
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5
            )
            
            improved_scenes = self._parse_response(response.choices[0].message.content)
            logger.info(f"Improved {len(improved_scenes)} scenes")
            return improved_scenes
            
        except Exception as e:
            logger.error(f"Error improving scenes: {e}")
            return scenes  # Return original scenes if improvement fails
    
    def _create_critique_prompt(self, scenes: List[Dict[str, Any]]) -> str:
        """Create the prompt for scene critique."""
        scenes_text = "\n".join([
            f"Scene {i+1}: {scene['description']}\n"
            f"Caption: {scene['caption_text']}\n"
            f"Duration: {scene['duration']}s\n"
            for i, scene in enumerate(scenes)
        ])
        
        return f"""
        Review and improve these video scenes:
        
        {scenes_text}
        
        Please improve them for:
        - Better clarity and readability of captions
        - Smoother narrative flow between scenes
        - More engaging descriptions
        - Appropriate timing and pacing
        
        Keep the same JSON structure with description, caption_text, and duration fields.
        Ensure captions are concise and suitable for on-screen display.
        Total duration should remain approximately {self.config['video_duration']} seconds.
        
        Return the improved scenes as a JSON array.
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
                
        except Exception as e:
            logger.error(f"Error parsing critic response: {e}")
            
        return []  # Return empty list if parsing fails 