import os
from datetime import datetime
from typing import Dict, Any, Optional

from graph import VideoGeneratorGraph


class VideoGeneratorWithProgress:
    """Video generator wrapper that provides progress updates."""

    def __init__(self, video_id: str, db_manager, progress_updates: Dict[str, Dict[str, Any]]):
        self.video_id = video_id
        self.db_manager = db_manager
        self.progress_updates = progress_updates
        self.generator = VideoGeneratorGraph(progress_callback=self._send_sse_update, video_id=video_id)

    def _send_sse_update(self, step: str, progress: int, message: str):
        """Send SSE update to connected clients and persist progress."""
        try:
            if step == 'completed':
                self.db_manager.update_video_status(self.video_id, 'completed', step, progress)
                self.db_manager.add_progress_entry(self.video_id, step, 'completed', message)
            elif step in ['failed', 'video_assembly_failed', 'scene_generation_failed', 'scene_critique_failed', 'audio_generation_failed']:
                self.db_manager.update_video_status(self.video_id, 'failed', step, progress)
                self.db_manager.add_progress_entry(self.video_id, step, 'failed', message)
            else:
                self.db_manager.update_video_status(self.video_id, 'processing', step, progress)
                self.db_manager.add_progress_entry(self.video_id, step, 'started', message)

            self.progress_updates[self.video_id] = {
                'type': 'progress',
                'step': step,
                'progress': progress,
                'message': message,
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            print(f"Error sending SSE update: {e}")

    def generate_video(self, user_input: str) -> Dict[str, Any]:
        try:
            self._send_sse_update('initializing', 5, 'Starting video generation...')
            result = self.generator.generate_video(user_input)
            if result.get('final_video'):
                self._send_sse_update('completed', 100, 'Video generation completed successfully!')
            else:
                error_msg = result.get('error', 'Unknown error')
                self._send_sse_update('failed', 100, f"Video generation failed: {error_msg}")
            return result
        except Exception as e:
            self._send_sse_update('failed', 100, f'Video generation failed: {str(e)}')
            raise e


def generate_video_async(app, video_id: str, user_input: str, db_manager, progress_updates: Dict[str, Dict[str, Any]]) -> None:
    """Generate video asynchronously and update database within Flask app context."""
    with app.app_context():
        try:
            db_manager.update_video_status(video_id, 'processing', 'initializing', 0)
            db_manager.add_progress_entry(video_id, 'initialization', 'started', 'Starting video generation')

            workflow_with_progress = VideoGeneratorWithProgress(video_id, db_manager, progress_updates)
            result = workflow_with_progress.generate_video(user_input)

            final_video_path = result.get('final_video')
            if final_video_path and os.path.exists(final_video_path):
                duration = None
                try:
                    import moviepy.editor as mp
                    video_clip = mp.VideoFileClip(final_video_path)
                    duration = video_clip.duration
                    video_clip.close()
                except Exception:
                    pass

                if not duration:
                    scenes = result.get('improved_scenes') or result.get('raw_scenes') or []
                    try:
                        duration = float(sum(max(0.0, float(s.get('duration', 0))) for s in scenes))
                    except Exception:
                        duration = 0.0

                db_manager.update_video_result(video_id, final_video_path, duration or 0.0)
                db_manager.add_progress_entry(video_id, 'completion', 'completed', 'Video generation completed successfully')
            else:
                error_msg = result.get('error', 'Unknown error occurred')
                db_manager.update_video_status(video_id, 'failed', 'failed', 100, error_msg)
                db_manager.add_progress_entry(video_id, 'completion', 'failed', f'Video generation failed: {error_msg}')
        except Exception as e:
            error_msg = str(e)
            db_manager.update_video_status(video_id, 'failed', 'failed', 100, error_msg)
            db_manager.add_progress_entry(video_id, 'completion', 'failed', f'Video generation failed: {error_msg}') 