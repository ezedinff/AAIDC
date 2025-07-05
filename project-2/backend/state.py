from typing import TypedDict, List, Dict, Any
from langgraph.graph import add_messages
from typing_extensions import Annotated

class SimpleVideoState(TypedDict):
    """State schema for the video generator workflow."""
    user_input: str
    raw_scenes: List[Dict[str, Any]]  # {description, caption_text, duration}
    improved_scenes: List[Dict[str, Any]]
    audio_files: List[str]
    final_video: str
    current_step: str
    messages: Annotated[List[Dict[str, Any]], add_messages]
    error: str  # Track any errors that occur
    retry_count: int  # Track retry attempts for scene critique
    scene_critique_decision: str  # Decision from scene critique: "retry" or "continue" 