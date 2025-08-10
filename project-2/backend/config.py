import os
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Resolve paths relative to the backend directory
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.abspath(os.path.join(_BASE_DIR, '..'))

CONFIG: Dict[str, Any] = {
    # OpenAI Configuration
    "openai_api_key": os.getenv("OPENAI_API_KEY"),
    # Mock mode to run without external services
    "mock_mode": os.getenv("MOCK_MODE", "false").lower() in ("1", "true", "yes"),
    
    # Video Generation Settings
    "scene_count": int(os.getenv("SCENE_COUNT", "3")),
    "video_duration": int(os.getenv("VIDEO_DURATION", "30")),  # seconds
    "audio_voice": os.getenv("AUDIO_VOICE", "alloy"),
    "video_resolution": os.getenv("VIDEO_RESOLUTION", "1280x720"),
    "text_font_size": int(os.getenv("TEXT_FONT_SIZE", "48")),
    "text_color": os.getenv("TEXT_COLOR", "black"),
    "background_color": os.getenv("BACKGROUND_COLOR", "white"),
    
    # Directory Settings (absolute paths; outputs defaults to project root /outputs)
    "output_dir": os.path.abspath(os.getenv("OUTPUT_DIR", os.path.join(_PROJECT_ROOT, 'outputs'))),
    "temp_dir": os.path.abspath(os.getenv("TEMP_DIR", os.path.join(_BASE_DIR, 'temp'))),
    "data_dir": os.path.abspath(os.getenv("DATA_DIR", os.path.join(_PROJECT_ROOT, 'data'))),
    
    # Flask API Settings
    "flask_host": os.getenv("FLASK_HOST", "0.0.0.0"),
    "flask_port": int(os.getenv("FLASK_PORT", "5000")),
    "flask_debug": os.getenv("FLASK_ENV") == "development",
    "secret_key": os.getenv("SECRET_KEY", "dev-secret-key"),
    
    # Database Settings - use absolute path for Docker compatibility
    "database_url": os.getenv("DATABASE_URL") or f"sqlite:///{os.path.abspath(os.path.join(_BASE_DIR, 'data', 'db.sqlite'))}",
    
    # CORS Settings
    "cors_origins": [o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",") if o.strip()],
}

def get_config() -> Dict[str, Any]:
    """Get the configuration dictionary."""
    return CONFIG.copy()


def validate_config() -> bool:
    """Validate that required configuration is present and directories exist."""
    # In non-mock mode, ensure API key is present
    if not CONFIG["mock_mode"] and not CONFIG["openai_api_key"]:
        raise ValueError("OPENAI_API_KEY environment variable is required (or set MOCK_MODE=true)")
    
    # Create directories if they don't exist
    for dir_key in ["output_dir", "temp_dir", "data_dir"]:
        dir_path = CONFIG[dir_key]
        os.makedirs(dir_path, exist_ok=True)
    
    return True 