import os
import yaml
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# OpenAI API settings
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not found in environment variables")

# Directory paths
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
CONFIG_DIR = os.path.join(BASE_DIR, "config")
VECTOR_DB_PATH = os.path.join(BASE_DIR, "vector_db")
DATA_DIR = os.path.join(BASE_DIR, "data")
LOG_DIR = os.path.join(BASE_DIR, "logs")

# Create directories if they don't exist
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(CONFIG_DIR, exist_ok=True)

# Load config files
def load_yaml_config(filename):
    config_path = os.path.join(CONFIG_DIR, filename)
    if os.path.exists(config_path):
        with open(config_path, 'r') as file:
            return yaml.safe_load(file)
    return {}

# Load configurations
system_config = load_yaml_config("config.yaml")
prompt_config = load_yaml_config("prompt_config.yaml")

# Model settings
EMBEDDING_MODEL = "text-embedding-3-small"
LLM_MODEL = system_config.get("llm", "gpt-4o-mini")

# Reasoning strategies
REASONING_STRATEGIES = system_config.get("reasoning_strategies", {})

# RAG prompt templates
DEFAULT_RAG_TEMPLATE = """You are a helpful AI assistant. Use the following context to answer the user's question.
If you don't know the answer, just say that you don't know, don't try to make up an answer.

Context: {context}

Question: {question}

Helpful Answer:""" 