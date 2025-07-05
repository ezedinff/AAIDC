import os
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

CONFIG: Dict[str, Any] = {
    # OpenAI Configuration
    "openai_api_key": os.getenv("OPENAI_API_KEY"),
    
    # Video Generation Settings
    "scene_count": int(os.getenv("SCENE_COUNT", "3")),
    "video_duration": int(os.getenv("VIDEO_DURATION", "30")),  # seconds
    "audio_voice": os.getenv("AUDIO_VOICE", "alloy"),
    "video_resolution": os.getenv("VIDEO_RESOLUTION", "1280x720"),
    "text_font_size": int(os.getenv("TEXT_FONT_SIZE", "48")),
    "text_color": os.getenv("TEXT_COLOR", "black"),
    "background_color": os.getenv("BACKGROUND_COLOR", "white"),
    
    # Directory Settings
    "output_dir": os.getenv("OUTPUT_DIR", "outputs"),
    "temp_dir": os.getenv("TEMP_DIR", "temp"),
    "data_dir": os.getenv("DATA_DIR", "data"),
    
    # Flask API Settings
    "flask_host": os.getenv("FLASK_HOST", "0.0.0.0"),
    "flask_port": int(os.getenv("FLASK_PORT", "5000")),
    "flask_debug": os.getenv("FLASK_ENV") == "development",
    "secret_key": os.getenv("SECRET_KEY", "dev-secret-key"),
    
    # Database Settings - use absolute path for Docker compatibility
    "database_url": os.getenv("DATABASE_URL", f"sqlite:///{os.path.abspath(os.getenv('DATA_DIR', 'data'))}/db.sqlite"),
    
    # CORS Settings
    "cors_origins": os.getenv("CORS_ORIGINS", "*").split(","),
}

def get_config() -> Dict[str, Any]:
    """Get the configuration dictionary."""
    return CONFIG.copy()

def validate_config() -> bool:
    """Validate that required configuration is present."""
    if not CONFIG["openai_api_key"]:
        raise ValueError("OPENAI_API_KEY environment variable is required")
    
    # Create directories if they don't exist
    for dir_key in ["output_dir", "temp_dir", "data_dir"]:
        dir_path = CONFIG[dir_key]
        os.makedirs(dir_path, exist_ok=True)
    
    return True 