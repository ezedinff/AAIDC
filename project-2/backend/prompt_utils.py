"""
Prompt template construction functions for building modular prompts for video generation.
"""

import yaml
import os
from typing import Union, List, Optional, Dict, Any
from pathlib import Path


def load_yaml_config(file_path: str) -> Dict[str, Any]:
    """Load YAML configuration from file.
    
    Args:
        file_path: Path to the YAML configuration file.
        
    Returns:
        Dictionary containing the loaded configuration.
        
    Raises:
        FileNotFoundError: If the configuration file doesn't exist.
        yaml.YAMLError: If the YAML file is malformed.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        raise FileNotFoundError(f"Configuration file not found: {file_path}")
    except yaml.YAMLError as e:
        raise yaml.YAMLError(f"Error parsing YAML file {file_path}: {e}")


def get_config_path(config_name: str) -> str:
    """Get the full path to a configuration file.
    
    Args:
        config_name: Name of the configuration file (with or without .yaml extension).
        
    Returns:
        Full path to the configuration file.
    """
    if not config_name.endswith('.yaml'):
        config_name += '.yaml'
    
    # Get the directory of the current script
    current_dir = Path(__file__).parent
    config_dir = current_dir / 'config'
    
    return str(config_dir / config_name)


def lowercase_first_char(text: str) -> str:
    """Lowercases the first character of a string.

    Args:
        text: Input string.

    Returns:
        The input string with the first character lowercased.
    """
    return text[0].lower() + text[1:] if text else text


def format_prompt_section(lead_in: str, value: Union[str, List[str]]) -> str:
    """Formats a prompt section by joining a lead-in with content.

    Args:
        lead_in: Introduction sentence for the section.
        value: Section content, as a string or list of strings.

    Returns:
        A formatted string with the lead-in followed by the content.
    """
    if isinstance(value, list):
        formatted_value = "\n".join(f"- {item}" for item in value)
    else:
        formatted_value = value
    return f"{lead_in}\n{formatted_value}"


def build_prompt_from_config(
    config: Dict[str, Any],
    input_data: str = "",
    app_config: Optional[Dict[str, Any]] = None,
) -> str:
    """Builds a complete prompt string based on a config dictionary.

    Args:
        config: Dictionary specifying prompt components.
        input_data: Content to be processed.
        app_config: Optional app-wide configuration (e.g., reasoning strategies).

    Returns:
        A fully constructed prompt as a string.

    Raises:
        ValueError: If the required 'instruction' field is missing.
    """
    prompt_parts = []

    if role := config.get("role"):
        prompt_parts.append(f"You are {lowercase_first_char(role.strip())}.")

    instruction = config.get("instruction")
    if not instruction:
        raise ValueError("Missing required field: 'instruction'")
    prompt_parts.append(format_prompt_section("Your task is as follows:", instruction))

    if context := config.get("context"):
        prompt_parts.append(f"Here's some background that may help you:\n{context}")

    if constraints := config.get("output_constraints"):
        prompt_parts.append(
            format_prompt_section(
                "Ensure your response follows these rules:", constraints
            )
        )

    if tone := config.get("style_or_tone"):
        prompt_parts.append(
            format_prompt_section(
                "Follow these style and tone guidelines in your response:", tone
            )
        )

    if format_ := config.get("output_format"):
        prompt_parts.append(
            format_prompt_section("Structure your response as follows:", format_)
        )

    if examples := config.get("examples"):
        prompt_parts.append("Here are some examples to guide your response:")
        if isinstance(examples, list):
            for i, example in enumerate(examples, 1):
                prompt_parts.append(f"Example {i}:\n{example}")
        else:
            prompt_parts.append(str(examples))

    if goal := config.get("goal"):
        prompt_parts.append(f"Your goal is to achieve the following outcome:\n{goal}")

    if input_data:
        prompt_parts.append(
            "Here is the content you need to work with:\n"
            "<<<BEGIN CONTENT>>>\n"
            f"{input_data.strip()}\n"
            "<<<END CONTENT>>>"
        )

    reasoning_strategy = config.get("reasoning_strategy")
    if reasoning_strategy and reasoning_strategy != "None" and app_config:
        strategies = app_config.get("reasoning_strategies", {})
        if strategy_text := strategies.get(reasoning_strategy):
            prompt_parts.append(strategy_text.strip())

    prompt_parts.append("Now perform the task as instructed above.")
    return "\n\n".join(prompt_parts)


def print_prompt_preview(prompt: str, max_length: int = 500) -> None:
    """Prints a preview of the constructed prompt for debugging purposes.

    Args:
        prompt: The constructed prompt string.
        max_length: Maximum number of characters to show.
    """
    print("=" * 60)
    print("CONSTRUCTED PROMPT:")
    print("=" * 60)
    if len(prompt) > max_length:
        print(prompt[:max_length] + "...")
        print(f"\n[Truncated - Full prompt is {len(prompt)} characters]")
    else:
        print(prompt)
    print("=" * 60)


class PromptManager:
    """Manager class for loading and building prompts from configuration files."""
    
    def __init__(self):
        self.app_config = self._load_app_config()
        self.prompt_config = self._load_prompt_config()
    
    def _load_app_config(self) -> Dict[str, Any]:
        """Load application configuration."""
        try:
            config_path = get_config_path('config')
            return load_yaml_config(config_path)
        except Exception as e:
            print(f"Warning: Could not load app config: {e}")
            return {}
    
    def _load_prompt_config(self) -> Dict[str, Any]:
        """Load prompt configuration."""
        try:
            config_path = get_config_path('prompt_config')
            return load_yaml_config(config_path)
        except Exception as e:
            print(f"Warning: Could not load prompt config: {e}")
            return {}
    
    def get_prompt_for_agent(self, agent_name: str, input_data: str = "", 
                           reasoning_strategy: str = None) -> str:
        """Get a constructed prompt for a specific agent.
        
        Args:
            agent_name: Name of the agent (e.g., 'scene_generator', 'scene_critic').
            input_data: Content to be processed by the agent.
            reasoning_strategy: Optional reasoning strategy override.
            
        Returns:
            A fully constructed prompt string.
            
        Raises:
            ValueError: If the agent configuration is not found.
        """
        if agent_name not in self.prompt_config:
            raise ValueError(f"Agent '{agent_name}' not found in prompt configuration")
        
        config = self.prompt_config[agent_name].copy()
        
        # Add reasoning strategy from app config or override
        if reasoning_strategy:
            config["reasoning_strategy"] = reasoning_strategy
        elif "reasoning_strategy" not in config:
            # Use default from common config or app config
            common_config = self.prompt_config.get("common", {})
            config["reasoning_strategy"] = common_config.get("reasoning_strategy", "step_by_step")
        
        return build_prompt_from_config(config, input_data, self.app_config)
    
    def get_scene_generation_prompt(self, user_input: str, scene_count: int = 3, 
                                  video_duration: int = 30) -> str:
        """Get a prompt for scene generation.
        
        Args:
            user_input: User's video description.
            scene_count: Number of scenes to generate.
            video_duration: Total video duration in seconds.
            
        Returns:
            A constructed prompt for scene generation.
        """
        input_data = f"""
USER REQUEST: {user_input}
SCENE COUNT: {scene_count}
VIDEO DURATION: {video_duration} seconds
DURATION PER SCENE: Approximately {video_duration // scene_count} seconds each
"""
        
        return self.get_prompt_for_agent("scene_generator", input_data)
    
    def get_scene_critique_prompt(self, scenes: List[Dict[str, Any]]) -> str:
        """Get a prompt for scene critique.
        
        Args:
            scenes: List of scene dictionaries to critique.
            
        Returns:
            A constructed prompt for scene critique.
        """
        import json
        scenes_json = json.dumps(scenes, indent=2)
        input_data = f"SCENES TO REVIEW:\n{scenes_json}"
        
        return self.get_prompt_for_agent("scene_critic", input_data)
    
    def get_audio_generation_prompt(self, scene: Dict[str, Any]) -> str:
        """Get a prompt for audio generation.
        
        Args:
            scene: Scene dictionary containing description and caption.
            
        Returns:
            A constructed prompt for audio generation.
        """
        input_data = f"""
SCENE DESCRIPTION: {scene.get('description', '')}
CAPTION TEXT: {scene.get('caption_text', '')}
DURATION: {scene.get('duration', 10)} seconds
"""
        
        return self.get_prompt_for_agent("audio_generation", input_data)
    
    def get_video_assembly_prompt(self, scenes: List[Dict[str, Any]], 
                                 audio_files: List[str]) -> str:
        """Get a prompt for video assembly.
        
        Args:
            scenes: List of scene dictionaries.
            audio_files: List of audio file paths.
            
        Returns:
            A constructed prompt for video assembly.
        """
        import json
        input_data = f"""
SCENES: {json.dumps(scenes, indent=2)}
AUDIO FILES: {json.dumps(audio_files, indent=2)}
"""
        
        return self.get_prompt_for_agent("video_assembly", input_data)


# Global instance for easy access
prompt_manager = PromptManager()


def get_prompt_for_agent(agent_name: str, input_data: str = "", 
                        reasoning_strategy: str = None) -> str:
    """Convenience function to get a prompt for an agent.
    
    Args:
        agent_name: Name of the agent.
        input_data: Content to be processed.
        reasoning_strategy: Optional reasoning strategy.
        
    Returns:
        A constructed prompt string.
    """
    return prompt_manager.get_prompt_for_agent(agent_name, input_data, reasoning_strategy) 