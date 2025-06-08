import os
import sys
import logging
import json
from datetime import datetime
import argparse

# Import project modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.rag_chain import RAGChain
from src.config import LOG_DIR

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def setup_logging(session_id):
    """Set up logging for the current session."""
    log_file = os.path.join(LOG_DIR, f"session_{session_id}.log")
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

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="RAG System CLI")
    parser.add_argument("--no-memory", action="store_true", help="Disable conversation memory")
    parser.add_argument("--no-reasoning", action="store_true", help="Disable intermediate reasoning steps")
    return parser.parse_args()

def main():
    """Main entry point for the application."""
    # Parse arguments
    args = parse_arguments()
    
    # Generate a unique session ID
    session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Set up logging
    log_file = setup_logging(session_id)
    logger.info(f"Starting new session: {session_id}")
    
    # Create the RAG chain
    try:
        rag_chain = RAGChain(
            use_memory=not args.no_memory,
            use_reasoning=not args.no_reasoning
        )
        logger.info("RAG chain initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize RAG chain: {e}")
        print(f"Error: {e}")
        return
    
    # Print welcome message
    print("\n=== RAG System ===")
    print("Type 'exit' or 'quit' to end the session.")
    print("Type 'help' for assistance.\n")
    
    # Main interaction loop
    while True:
        try:
            # Get user input
            query = input("\nQuestion: ").strip()
            
            # Check for exit command
            if query.lower() in ("exit", "quit"):
                print("Goodbye!")
                break
            
            # Check for help command
            if query.lower() == "help":
                print("\nCommands:")
                print("  help - Show this help message")
                print("  exit/quit - End the session")
                print("\nAsk any question, and the system will try to answer based on the ingested documents.")
                continue
            
            # Skip empty queries
            if not query:
                continue
            
            # Process the query
            response = rag_chain.query(query)
            
            # Print the answer
            print("\nAnswer:", response["answer"])
            
            # Print sources
            if response.get("source_documents"):
                print("\nSources:")
                for i, doc in enumerate(response["source_documents"]):
                    print(f"  {i+1}. {doc.get('source', 'Unknown source')}")
            
            # Log the interaction
            log_interaction(log_file, query, response)
            
        except KeyboardInterrupt:
            print("\nSession terminated by user.")
            break
        except Exception as e:
            logger.error(f"Error during query processing: {e}")
            print(f"Error: {e}")
    
    logger.info(f"Session {session_id} ended")
    print(f"\nSession logs saved to {log_file}")

if __name__ == "__main__":
    main() 