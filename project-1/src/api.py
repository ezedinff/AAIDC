import os
import sys
import logging
import json
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# Import project modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.rag_chain import RAGChain
from src.config_loader import get_app_config, get_prompt_config
from src.config import LOG_DIR

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Get the path to the static directory
static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")

# Create Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Get app config
app_config = get_app_config()

# Initialize global variables
rag_chain = None
session_id = None
log_file = None
reasoning_strategy = "Educational"  # Default to Educational for abortion awareness
prompt_template = app_config.get("default_prompt_template", "rag_prompt_abortion_awareness")

# Get available reasoning strategies
REASONING_STRATEGIES = app_config.get("reasoning_strategies", {})

# Get available prompt templates
try:
    prompt_configs = get_prompt_config("rag_prompt_default")  # Just to load the file
    PROMPT_TEMPLATES = {}
    
    for key in prompt_configs:
        if key.startswith("rag_prompt_"):
            PROMPT_TEMPLATES[key] = prompt_configs[key].get("description", key)
except Exception as e:
    logger.error(f"Error loading prompt templates: {e}")
    PROMPT_TEMPLATES = {"rag_prompt_default": "Default RAG prompt"}

def setup_logging(session_id):
    """Set up logging for the current session."""
    log_file = os.path.join(LOG_DIR, f"api_session_{session_id}.log")
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(file_handler)
    return log_file

def log_interaction(log_file, query, response):
    """Log the interaction to a JSON file for later evaluation."""
    interaction = {
        "timestamp": datetime.now().isoformat(),
        "query": query,
        "response": response
    }
    
    # Convert to JSON-serializable format
    if "source_documents" in interaction["response"]:
        interaction["response"]["source_documents"] = [
            {"content": doc["content"], "source": doc["source"]}
            for doc in interaction["response"]["source_documents"]
        ]
    
    # Create JSON log file if it doesn't exist
    json_log_file = log_file.replace(".log", ".json")
    
    # Append to the JSON log file
    try:
        if os.path.exists(json_log_file):
            with open(json_log_file, 'r') as f:
                interactions = json.load(f)
        else:
            interactions = []
        
        interactions.append(interaction)
        
        with open(json_log_file, 'w') as f:
            json.dump(interactions, f, indent=2)
    except Exception as e:
        logger.error(f"Error logging interaction: {e}")

def initialize_rag_chain():
    """Initialize the RAG chain."""
    global rag_chain, session_id, log_file
    
    # Generate a unique session ID
    session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Set up logging
    log_file = setup_logging(session_id)
    logger.info(f"Starting new API session: {session_id}")
    
    # Create the RAG chain
    try:
        rag_chain = RAGChain(
            use_memory=True,
            use_reasoning=True,
            reasoning_strategy=reasoning_strategy,
            prompt_template=prompt_template
        )
        logger.info(f"RAG chain initialized successfully with {reasoning_strategy} reasoning strategy and {prompt_template} prompt template")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize RAG chain: {e}")
        return False

@app.route('/')
def index():
    """Serve the index.html file."""
    return send_from_directory(static_dir, 'index.html')

@app.route('/<path:path>')
def static_files(path):
    """Serve static files."""
    return send_from_directory(static_dir, path)

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    if rag_chain is None:
        return jsonify({"status": "error", "message": "RAG chain not initialized"}), 503
    return jsonify({"status": "ok", "message": "RAG API is running"}), 200

@app.route('/strategies', methods=['GET'])
def get_strategies():
    """Get available reasoning strategies."""
    return jsonify({
        "status": "success",
        "strategies": list(REASONING_STRATEGIES.keys()),
        "current_strategy": reasoning_strategy
    }), 200

@app.route('/prompt_templates', methods=['GET'])
def get_prompt_templates():
    """Get available prompt templates."""
    return jsonify({
        "status": "success",
        "templates": PROMPT_TEMPLATES,
        "current_template": prompt_template
    }), 200

@app.route('/strategy', methods=['POST'])
def set_strategy():
    """Set the reasoning strategy."""
    global reasoning_strategy, rag_chain
    
    # Get strategy from request
    data = request.json
    if not data or 'strategy' not in data:
        return jsonify({
            "status": "error",
            "message": "Missing 'strategy' field in request"
        }), 400
    
    new_strategy = data['strategy']
    
    # Check if strategy is valid
    if new_strategy not in REASONING_STRATEGIES:
        return jsonify({
            "status": "error",
            "message": f"Invalid strategy: {new_strategy}. Available strategies: {list(REASONING_STRATEGIES.keys())}"
        }), 400
    
    # Update strategy
    reasoning_strategy = new_strategy
    
    # Reset RAG chain to use new strategy
    rag_chain = None
    success = initialize_rag_chain()
    
    if success:
        return jsonify({
            "status": "success",
            "message": f"Reasoning strategy set to {reasoning_strategy}"
        }), 200
    else:
        return jsonify({
            "status": "error",
            "message": "Failed to initialize RAG chain with new strategy"
        }), 500

@app.route('/prompt_template', methods=['POST'])
def set_prompt_template():
    """Set the prompt template."""
    global prompt_template, rag_chain
    
    # Get template from request
    data = request.json
    if not data or 'template' not in data:
        return jsonify({
            "status": "error",
            "message": "Missing 'template' field in request"
        }), 400
    
    new_template = data['template']
    
    # Check if template is valid
    if new_template not in PROMPT_TEMPLATES:
        return jsonify({
            "status": "error",
            "message": f"Invalid template: {new_template}. Available templates: {list(PROMPT_TEMPLATES.keys())}"
        }), 400
    
    # Update template
    prompt_template = new_template
    
    # Reset RAG chain to use new template
    rag_chain = None
    success = initialize_rag_chain()
    
    if success:
        return jsonify({
            "status": "success",
            "message": f"Prompt template set to {prompt_template}"
        }), 200
    else:
        return jsonify({
            "status": "error",
            "message": "Failed to initialize RAG chain with new prompt template"
        }), 500

@app.route('/query', methods=['POST'])
def query():
    """Query endpoint to ask questions to the RAG system."""
    # Check if RAG chain is initialized
    if rag_chain is None:
        success = initialize_rag_chain()
        if not success:
            return jsonify({
                "status": "error",
                "message": "Failed to initialize RAG chain. Check logs for details."
            }), 500
    
    # Get query from request
    data = request.json
    if not data or 'query' not in data:
        return jsonify({
            "status": "error",
            "message": "Missing 'query' field in request"
        }), 400
    
    user_query = data['query']
    
    try:
        # Process the query
        response = rag_chain.query(user_query)
        
        # Log the interaction
        log_interaction(log_file, user_query, response)
        
        # Return the response
        return jsonify({
            "status": "success",
            "answer": response["answer"],
            "sources": [
                {"content": doc["content"], "source": doc["source"]}
                for doc in response.get("source_documents", [])
            ],
            "reasoning_strategy": reasoning_strategy,
            "prompt_template": prompt_template
        }), 200
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        return jsonify({
            "status": "error",
            "message": f"Error processing query: {str(e)}"
        }), 500

@app.route('/reset', methods=['POST'])
def reset():
    """Reset the RAG chain to start a new session."""
    global rag_chain, session_id, log_file
    
    # Reset RAG chain
    rag_chain = None
    
    # Initialize a new RAG chain
    success = initialize_rag_chain()
    
    if success:
        return jsonify({
            "status": "success",
            "message": f"RAG chain reset successfully. New session ID: {session_id}"
        }), 200
    else:
        return jsonify({
            "status": "error",
            "message": "Failed to reset RAG chain. Check logs for details."
        }), 500

def main():
    """Main function to run the Flask app."""
    # Initialize RAG chain
    initialize_rag_chain()
    
    # Create static directory if it doesn't exist
    os.makedirs(static_dir, exist_ok=True)
    
    # Run the Flask app
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)

if __name__ == "__main__":
    main() 