import logging
import os
from typing import Dict, Any, List
from PIL import Image, ImageDraw, ImageFont
from config import get_config

# Optional moviepy import - fallback if not available  
try:
    import moviepy
    from moviepy import ImageClip, AudioFileClip, concatenate_videoclips
    MOVIEPY_AVAILABLE = True
except ImportError as e:
    print(f"Warning: MoviePy not available - {e}")
    MOVIEPY_AVAILABLE = False
    ImageClip = None
    AudioFileClip = None
    concatenate_videoclips = None

logger = logging.getLogger(__name__)

class VideoAgent:
    """Agent responsible for assembling the final video from scenes and audio."""
    
    def __init__(self):
        self.config = get_config()
        self.mock_mode = self.config.get("mock_mode", False)
        self._ensure_output_dirs()
    
    def _ensure_output_dirs(self):
        """Ensure output directories exist."""
        os.makedirs(self.config["output_dir"], exist_ok=True)
        os.makedirs(self.config["temp_dir"], exist_ok=True)
    
    def assemble_video(self, scenes: List[Dict[str, Any]], audio_files: List[str]) -> str:
        """Assemble the final video from scenes and audio files."""
        # In mock mode, generate a placeholder file and return
        if self.mock_mode:
            return self._create_placeholder_video()
        if not MOVIEPY_AVAILABLE:
            logger.error("MoviePy not available - cannot create video")
            return ""
            
        try:
            video_clips = []
            
            for i, (scene, audio_file) in enumerate(zip(scenes, audio_files)):
                # Create video clip for this scene
                video_clip = self._create_scene_video(scene, audio_file, i)
                if video_clip:
                    video_clips.append(video_clip)
            
            if not video_clips:
                raise ValueError("No video clips were created")
            
            # Concatenate all video clips
            logger.info(f"Concatenating {len(video_clips)} video clips")
            final_video = concatenate_videoclips(video_clips, method="compose")
            
            # Save the final video
            output_filename = f"final_video_{self._get_timestamp()}.mp4"
            output_path = os.path.join(self.config["output_dir"], output_filename)
            
            logger.info(f"Writing video to: {output_path}")
            final_video.write_videofile(
                output_path,
                fps=24,
                codec='libx264',
                audio_codec='aac'
            )
            
            # Clean up temporary clips
            for clip in video_clips:
                clip.close()
            final_video.close()
            
            logger.info(f"Video assembled successfully: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error assembling video: {e}")
            return ""
    
    def _create_placeholder_video(self) -> str:
        """Create a placeholder artifact to simulate a final video in mock mode."""
        placeholder_path = os.path.join(self.config["output_dir"], f"final_video_{self._get_timestamp()}.mp4")
        try:
            with open(placeholder_path, 'wb') as f:
                f.write(b"MOCK_VIDEO")
        except Exception as e:
            logger.warning(f"Failed to create placeholder video: {e}")
        return placeholder_path
    
    def _create_scene_video(self, scene: Dict[str, Any], audio_file: str, scene_index: int):
        """Create a video clip for a single scene."""
        if not MOVIEPY_AVAILABLE:
            return None
            
        try:
            # Create text image
            text_image = self._create_text_image(scene["caption_text"])
            
            # Get duration from audio file if available, otherwise use default
            duration = scene.get("duration", 10)
            if audio_file and os.path.exists(audio_file):
                try:
                    audio_clip = AudioFileClip(audio_file)
                    duration = audio_clip.duration
                except:
                    logger.warning(f"Could not load audio file {audio_file}, using default duration")
                    duration = 10
            
            # Create video clip from image with MoviePy v2.x syntax
            video_clip = ImageClip(text_image).with_duration(duration)
            
            # Add audio if available
            if audio_file and os.path.exists(audio_file):
                try:
                    audio_clip = AudioFileClip(audio_file)
                    video_clip = video_clip.with_audio(audio_clip)
                except Exception as audio_error:
                    logger.warning(f"Could not add audio to video clip: {audio_error}")
            
            return video_clip
            
        except Exception as e:
            logger.error(f"Error creating scene video {scene_index}: {e}")
            return None
    
    def _create_text_image(self, text: str) -> str:
        """Create an image with text on a white background - simple and clean."""
        try:
            # Use HD resolution
            width, height = 1280, 720
            
            # Create white background image
            image = Image.new('RGB', (width, height), 'white')
            draw = ImageDraw.Draw(image)
            
            # Use a readable font size from configuration
            font_size = self.config.get("text_font_size", 120)
            try:
                # Try fonts available in Docker container
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
            except:
                try:
                    font = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", font_size)
                except:
                    try:
                        # Try system fonts (for local development)
                        font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", font_size)
                    except:
                        try:
                            font = ImageFont.truetype("arial.ttf", font_size)
                        except:
                            # Use default but try to make it bigger
                            font = ImageFont.load_default()
            
            # Wrap text to multiple lines if needed
            words = text.split()
            lines = []
            current_line = []
            max_width = width - 100  # 50px margin on each side
            
            for word in words:
                test_line = ' '.join(current_line + [word])
                try:
                    bbox = draw.textbbox((0, 0), test_line, font=font)
                    line_width = bbox[2] - bbox[0]
                except:
                    # Fallback if textbbox is not available
                    line_width = len(test_line) * 20  # Rough estimate
                
                if line_width <= max_width:
                    current_line.append(word)
                else:
                    if current_line:
                        lines.append(' '.join(current_line))
                        current_line = [word]
                    else:
                        lines.append(word)  # Single word too long, add it anyway
            
            if current_line:
                lines.append(' '.join(current_line))
            
            # Calculate positioning - scale line height with font size
            line_height = int(font_size * 1.5)  # 1.5x font size for good spacing
            total_height = len(lines) * line_height
            start_y = (height - total_height) // 2
            
            # Draw each line centered
            for i, line in enumerate(lines):
                try:
                    bbox = draw.textbbox((0, 0), line, font=font)
                    text_width = bbox[2] - bbox[0]
                except:
                    # Fallback positioning
                    text_width = len(line) * 20
                
                x = (width - text_width) // 2
                y = start_y + i * line_height
                
                # Draw black text on white background
                draw.text((x, y), line, fill='black', font=font)
            
            # Save image
            image_filename = f"text_scene_{self._get_timestamp()}.png"
            image_path = os.path.join(self.config["temp_dir"], image_filename)
            image.save(image_path)
            
            logger.info(f"Created text image: {image_path} with text: {text[:50]}...")
            return image_path
            
        except Exception as e:
            logger.error(f"Error creating text image: {e}")
            # Return a blank image as fallback
            return self._create_blank_image()
    
    def _create_blank_image(self) -> str:
        """Create a blank white image as fallback."""
        try:
            width, height = map(int, self.config["video_resolution"].split('x'))
            image = Image.new('RGB', (width, height), self.config["background_color"])
            
            image_filename = f"blank_image_{self._get_timestamp()}.png"
            image_path = os.path.join(self.config["temp_dir"], image_filename)
            image.save(image_path)
            
            return image_path
            
        except Exception as e:
            logger.error(f"Error creating blank image: {e}")
            return ""
    
    def _get_timestamp(self) -> str:
        """Get current timestamp for unique filenames."""
        import time
        return str(time.time_ns()) 