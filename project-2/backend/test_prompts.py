#!/usr/bin/env python3
"""
Test script for the prompt generation system.
"""

import sys
import os
from typing import Dict, Any, List

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from prompt_utils import prompt_manager, print_prompt_preview

def test_scene_generation_prompt():
    """Test scene generation prompt."""
    print("\n" + "="*60)
    print("TESTING SCENE GENERATION PROMPT")
    print("="*60)
    
    user_input = "Create a video about making coffee at home"
    prompt = prompt_manager.get_scene_generation_prompt(
        user_input, 
        scene_count=3, 
        video_duration=30
    )
    
    print_prompt_preview(prompt, max_length=800)
    return prompt

def test_scene_critique_prompt():
    """Test scene critique prompt."""
    print("\n" + "="*60)
    print("TESTING SCENE CRITIQUE PROMPT")
    print("="*60)
    
    sample_scenes = [
        {
            "description": "A person waking up in the morning, looking tired",
            "caption_text": "Morning coffee ritual begins",
            "duration": 10
        },
        {
            "description": "Grinding coffee beans with a manual grinder",
            "caption_text": "Fresh beans make all the difference",
            "duration": 10
        },
        {
            "description": "Pouring hot water over coffee grounds",
            "caption_text": "The perfect brew",
            "duration": 10
        }
    ]
    
    prompt = prompt_manager.get_scene_critique_prompt(sample_scenes)
    print_prompt_preview(prompt, max_length=800)
    return prompt

def test_audio_generation_prompt():
    """Test audio generation prompt."""
    print("\n" + "="*60)
    print("TESTING AUDIO GENERATION PROMPT")
    print("="*60)
    
    sample_scene = {
        "description": "A person brewing coffee with a French press, steam rising from the cup",
        "caption_text": "The perfect morning brew",
        "duration": 10
    }
    
    prompt = prompt_manager.get_audio_generation_prompt(sample_scene)
    print_prompt_preview(prompt, max_length=800)
    return prompt

def test_video_assembly_prompt():
    """Test video assembly prompt."""
    print("\n" + "="*60)
    print("TESTING VIDEO ASSEMBLY PROMPT")
    print("="*60)
    
    sample_scenes = [
        {
            "description": "Coffee brewing scene",
            "caption_text": "Morning coffee",
            "duration": 10
        }
    ]
    
    sample_audio_files = [
        "temp/scene_1_audio.mp3"
    ]
    
    prompt = prompt_manager.get_video_assembly_prompt(sample_scenes, sample_audio_files)
    print_prompt_preview(prompt, max_length=800)
    return prompt

def test_configuration_loading():
    """Test configuration loading."""
    print("\n" + "="*60)
    print("TESTING CONFIGURATION LOADING")
    print("="*60)
    
    # Test app config
    app_config = prompt_manager.app_config
    print(f"App config loaded: {bool(app_config)}")
    if app_config:
        print(f"App name: {app_config.get('app', {}).get('name', 'Not found')}")
        print(f"Reasoning strategies: {list(app_config.get('reasoning_strategies', {}).keys())}")
    
    # Test prompt config
    prompt_config = prompt_manager.prompt_config
    print(f"Prompt config loaded: {bool(prompt_config)}")
    if prompt_config:
        print(f"Available agents: {list(prompt_config.keys())}")
    
    return app_config, prompt_config

def test_reasoning_strategies():
    """Test different reasoning strategies."""
    print("\n" + "="*60)
    print("TESTING REASONING STRATEGIES")
    print("="*60)
    
    strategies = ["step_by_step", "creative_flow", "analytical", "storytelling"]
    
    for strategy in strategies:
        print(f"\n--- Testing {strategy} strategy ---")
        try:
            prompt = prompt_manager.get_prompt_for_agent(
                "scene_generator", 
                "Create a video about cooking pasta",
                reasoning_strategy=strategy
            )
            print(f"✅ {strategy} strategy works")
            # Show a snippet of the reasoning section
            if "Think through this step by step" in prompt:
                print("   Contains step-by-step reasoning")
            elif "creative thinking" in prompt:
                print("   Contains creative thinking guidance")
            elif "analytical thinking" in prompt:
                print("   Contains analytical thinking guidance")
            elif "storytelling elements" in prompt:
                print("   Contains storytelling guidance")
        except Exception as e:
            print(f"❌ {strategy} strategy failed: {e}")

def main():
    """Run all prompt tests."""
    print("🧪 Testing Prompt Generation System")
    print("="*60)
    
    try:
        # Test configuration loading
        app_config, prompt_config = test_configuration_loading()
        
        if not app_config or not prompt_config:
            print("❌ Configuration loading failed. Check that config files exist.")
            return
        
        # Test individual prompts
        test_scene_generation_prompt()
        test_scene_critique_prompt()
        test_audio_generation_prompt()
        test_video_assembly_prompt()
        
        # Test reasoning strategies
        test_reasoning_strategies()
        
        print("\n" + "="*60)
        print("✅ All prompt tests completed successfully!")
        print("="*60)
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 