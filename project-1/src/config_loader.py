"""
Utility functions for loading and managing configuration files.
"""

import os
import yaml
from typing import Dict, Any, Optional


def load_yaml_config(config_path: str) -> Dict[str, Any]:
    """Loads a YAML configuration file.
    
    Args:
        config_path: Path to the YAML configuration file
        
    Returns:
        Dictionary containing the configuration
        
    Raises:
        FileNotFoundError: If the configuration file doesn't exist
        yaml.YAMLError: If the configuration file is invalid
    """
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_path, 'r') as file:
        try:
            return yaml.safe_load(file)
        except yaml.YAMLError as e:
            raise yaml.YAMLError(f"Error parsing YAML file {config_path}: {e}")


def get_prompt_config(config_name: str, config_path: str = "config/prompt_config.yaml") -> Dict[str, Any]:
    """Gets a specific prompt configuration from the prompt config file.
    
    Args:
        config_name: Name of the prompt configuration to retrieve
        config_path: Path to the prompt configuration file
        
    Returns:
        Dictionary containing the prompt configuration
        
    Raises:
        KeyError: If the configuration name doesn't exist in the file
    """
    prompt_configs = load_yaml_config(config_path)
    
    if config_name not in prompt_configs:
        raise KeyError(f"Prompt configuration '{config_name}' not found in {config_path}")
    
    return prompt_configs[config_name]


def get_app_config(config_path: str = "config/config.yaml") -> Dict[str, Any]:
    """Gets the application configuration.
    
    Args:
        config_path: Path to the application configuration file
        
    Returns:
        Dictionary containing the application configuration
    """
    return load_yaml_config(config_path)


def get_reasoning_strategy(strategy_name: str, config_path: str = "config/config.yaml") -> Optional[str]:
    """Gets a specific reasoning strategy from the app config.
    
    Args:
        strategy_name: Name of the reasoning strategy to retrieve
        config_path: Path to the application configuration file
        
    Returns:
        String containing the reasoning strategy prompt, or None if not found
    """
    app_config = get_app_config(config_path)
    strategies = app_config.get("reasoning_strategies", {})
    
    return strategies.get(strategy_name) 