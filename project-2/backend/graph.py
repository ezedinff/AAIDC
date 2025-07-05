import logging
from typing import Dict, Any, List
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode

from state import SimpleVideoState
from agents.scene_generator import SceneGeneratorAgent
from agents.scene_critic import SceneCriticAgent
from agents.audio_agent import AudioAgent
from agents.video_agent import VideoAgent

logger = logging.getLogger(__name__)

class VideoGeneratorGraph:
    """LangGraph workflow for video generation."""
    
    def __init__(self, progress_callback=None):
        self.scene_generator = SceneGeneratorAgent()
        self.scene_critic = SceneCriticAgent()
        self.audio_agent = AudioAgent()
        self.video_agent = VideoAgent()
        self.progress_callback = progress_callback
        
        # Build the graph
        self.graph = self._build_graph()


        # draw the mermaid diagram
        self.graph.get_graph().draw_mermaid_png(output_file_path="graph.png")
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow."""
        # Create the state graph
        workflow = StateGraph(SimpleVideoState)
        
        # Add nodes
        workflow.add_node("scene_generation", self._scene_generation_node)
        workflow.add_node("scene_critique", self._scene_critique_node)
        workflow.add_node("audio_generation", self._audio_generation_node)
        workflow.add_node("video_assembly", self._video_assembly_node)
        
        # Add edges - workflow with retry logic
        workflow.add_edge(START, "scene_generation")
        workflow.add_edge("scene_generation", "scene_critique")
        
        # Add conditional edge from scene_critique that can retry or continue
        workflow.add_conditional_edges(
            "scene_critique",
            self._should_retry_scene_generation,
            {
                "retry": "scene_generation",  # Go back to scene generation
                "continue": "audio_generation"  # Continue to audio generation
            }
        )
        
        workflow.add_edge("audio_generation", "video_assembly")
        workflow.add_edge("video_assembly", END)
        
        # Compile the graph
        return workflow.compile()
    
    def _scene_generation_node(self, state: SimpleVideoState) -> Dict[str, Any]:
        """Scene generation node."""
        retry_count = state.get("retry_count", 0)
        logger.info(f"Starting scene generation (attempt {retry_count + 1})...")
        
        # Send progress update
        if self.progress_callback:
            self.progress_callback("scene_generation", 25, f"AI is generating video scenes (attempt {retry_count + 1})...")
        
        try:
            user_input = state.get("user_input", "")
            if not user_input:
                raise ValueError("No user input provided")
            
            # Generate scenes
            raw_scenes = self.scene_generator.generate_scenes(user_input)
            
            # Send completion update
            if self.progress_callback:
                self.progress_callback("scene_generation", 35, f"Generated {len(raw_scenes)} video scenes")
            
            return {
                "raw_scenes": raw_scenes,
                "current_step": "scene_generation",
                "messages": [{"role": "system", "content": f"Generated {len(raw_scenes)} scenes (attempt {retry_count + 1})"}]
            }
            
        except Exception as e:
            logger.error(f"Error in scene generation: {e}")
            if self.progress_callback:
                self.progress_callback("scene_generation_failed", 35, f"Scene generation failed: {e}")
            return {
                "error": str(e),
                "current_step": "scene_generation_failed",
                "messages": [{"role": "system", "content": f"Scene generation failed: {e}"}]
            }
    
    def _scene_critique_node(self, state: SimpleVideoState) -> Dict[str, Any]:
        """Scene critique node with retry logic."""
        retry_count = state.get("retry_count", 0)
        logger.info(f"Starting scene critique (retry {retry_count})...")
        
        # Send progress update
        if self.progress_callback:
            self.progress_callback("scene_critique", 45, f"AI is reviewing and improving scenes (attempt {retry_count + 1})...")
        
        try:
            raw_scenes = state.get("raw_scenes", [])
            if not raw_scenes:
                raise ValueError("No scenes to critique")
            
            # Improve scenes
            improved_scenes = self.scene_critic.improve_scenes(raw_scenes)
            
            # Use original scenes if improvement fails
            if not improved_scenes:
                improved_scenes = raw_scenes
                logger.warning("Using original scenes as critique failed")
            
            # Check if scenes are acceptable or need retry
            is_acceptable = self._evaluate_scenes_quality(improved_scenes, retry_count)
            
            if is_acceptable or retry_count >= 3:
                # Scenes are good or we've reached max retries
                if self.progress_callback:
                    self.progress_callback("scene_critique", 55, f"Scenes approved and ready for audio generation")
                return {
                    "improved_scenes": improved_scenes,
                    "current_step": "scene_critique",
                    "retry_count": retry_count,
                    "scene_critique_decision": "continue",
                    "messages": [{"role": "system", "content": f"Scenes approved after {retry_count} retries"}]
                }
            else:
                # Scenes need improvement, retry
                if self.progress_callback:
                    self.progress_callback("scene_critique_retry", 40, f"Scenes need improvement, retrying ({retry_count + 1}/3)...")
                return {
                    "improved_scenes": improved_scenes,
                    "current_step": "scene_critique_retry",
                    "retry_count": retry_count + 1,
                    "scene_critique_decision": "retry",
                    "messages": [{"role": "system", "content": f"Scenes need improvement, retry {retry_count + 1}/3"}]
                }
            
        except Exception as e:
            logger.error(f"Error in scene critique: {e}")
            if self.progress_callback:
                self.progress_callback("scene_critique_failed", 50, f"Scene critique failed: {e}")
            # Fall back to raw scenes and continue
            return {
                "improved_scenes": state.get("raw_scenes", []),
                "error": str(e),
                "current_step": "scene_critique_failed",
                "retry_count": state.get("retry_count", 0),
                "scene_critique_decision": "continue",
                "messages": [{"role": "system", "content": f"Scene critique failed: {e}"}]
            }
    
    def _audio_generation_node(self, state: SimpleVideoState) -> Dict[str, Any]:
        """Audio generation node."""
        logger.info("Starting audio generation...")
        
        # Send progress update
        if self.progress_callback:
            self.progress_callback("audio_generation", 65, "AI is generating high-quality audio narration...")
        
        try:
            scenes = state.get("improved_scenes", [])
            if not scenes:
                raise ValueError("No scenes for audio generation")
            
            # Generate audio
            audio_files = self.audio_agent.generate_audio(scenes)
            
            # Send completion update
            if self.progress_callback:
                self.progress_callback("audio_generation", 80, f"Generated {len(audio_files)} audio files successfully")
            
            return {
                "audio_files": audio_files,
                "current_step": "audio_generation",
                "messages": [{"role": "system", "content": f"Generated {len(audio_files)} audio files"}]
            }
            
        except Exception as e:
            logger.error(f"Error in audio generation: {e}")
            if self.progress_callback:
                self.progress_callback("audio_generation_failed", 75, f"Audio generation failed: {e}")
            return {
                "audio_files": [],
                "error": str(e),
                "current_step": "audio_generation_failed",
                "messages": [{"role": "system", "content": f"Audio generation failed: {e}"}]
            }
    
    def _video_assembly_node(self, state: SimpleVideoState) -> Dict[str, Any]:
        """Video assembly node."""
        logger.info("Starting video assembly...")
        
        # Send progress update
        if self.progress_callback:
            self.progress_callback("video_assembly", 90, "AI is assembling the final video...")
        
        try:
            scenes = state.get("improved_scenes", [])
            audio_files = state.get("audio_files", [])
            
            if not scenes:
                raise ValueError("No scenes for video assembly")
            
            # Assemble video
            final_video = self.video_agent.assemble_video(scenes, audio_files)
            
            if not final_video:
                raise ValueError("Video assembly failed")
            
            # Send completion update
            if self.progress_callback:
                self.progress_callback("completed", 100, "Video generation completed successfully!")
            
            return {
                "final_video": final_video,
                "current_step": "video_assembly",
                "messages": [{"role": "system", "content": f"Video assembled successfully: {final_video}"}]
            }
            
        except Exception as e:
            logger.error(f"Error in video assembly: {e}")
            if self.progress_callback:
                self.progress_callback("video_assembly_failed", 95, f"Video assembly failed: {e}")
            return {
                "final_video": "",
                "error": str(e),
                "current_step": "video_assembly_failed",
                "messages": [{"role": "system", "content": f"Video assembly failed: {e}"}]
            }
    
    def _should_retry_scene_generation(self, state: SimpleVideoState) -> str:
        """Determine if scene generation should be retried based on critique."""
        decision = state.get("scene_critique_decision", "continue")
        logger.info(f"Scene critique decision: {decision}")
        return decision
    
    def _evaluate_scenes_quality(self, scenes: List[Dict[str, Any]], retry_count: int) -> bool:
        """Evaluate if scenes are acceptable quality."""
        # Simple quality checks
        if not scenes:
            return False
        
        # Check if all scenes have required fields
        for scene in scenes:
            if not scene.get("caption_text") or not scene.get("description"):
                logger.warning(f"Scene missing required fields: {scene}")
                return False
            
            # Check caption length (should be reasonable for display)
            caption = scene.get("caption_text", "")
            if len(caption) > 150:  # Too long for display
                logger.warning(f"Caption too long: {len(caption)} characters")
                return False
            
            if len(caption) < 10:  # Too short to be meaningful
                logger.warning(f"Caption too short: {len(caption)} characters")
                return False
        
        # For now, accept scenes after first retry or if they pass basic checks
        # This can be enhanced with more sophisticated quality checks
        if retry_count >= 1:
            logger.info("Accepting scenes after retry attempt")
            return True
        
        # Check for scene variety (simple check for different content)
        captions = [scene.get("caption_text", "") for scene in scenes]
        if len(set(captions)) < len(captions) * 0.8:  # Too many similar captions
            logger.warning("Scenes lack variety, retrying")
            return False
        
        logger.info("Scenes passed quality evaluation")
        return True
    
    def generate_video(self, user_input: str) -> Dict[str, Any]:
        """Generate a video from user input."""
        logger.info(f"Starting video generation for input: {user_input}")
        
        # Initial state
        initial_state = {
            "user_input": user_input,
            "raw_scenes": [],
            "improved_scenes": [],
            "audio_files": [],
            "final_video": "",
            "current_step": "start",
            "messages": [],
            "error": "",
            "retry_count": 0,
            "scene_critique_decision": "continue"
        }
        
        try:
            # Run the workflow
            result = self.graph.invoke(initial_state)
            
            logger.info(f"Video generation completed. Current step: {result.get('current_step')}")
            return result
            
        except Exception as e:
            logger.error(f"Error in video generation workflow: {e}")
            return {
                **initial_state,
                "error": str(e),
                "current_step": "workflow_failed",
                "messages": [{"role": "system", "content": f"Workflow failed: {e}"}]
            } 