# RAG System with LangChain

A retrieval-augmented generation (RAG) system that can answer questions based on custom knowledge documents. This implementation uses OpenAI's models for both embeddings and the language model.

## Setup

### Option 1: Local Installation

1. Clone this repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Create a `.env` file with your OpenAI API key:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```

### Option 2: Using Docker (Recommended)

1. Clone this repository
2. Create a `.env` file with your OpenAI API key:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```
3. Build and run using Docker Compose:
   ```
   docker compose up --build
   ```

### Option 3: Using Helper Script

1. Clone this repository
2. Run the setup script:
   ```
   ./run_rag.sh
   ```
   This script will:
   - Prompt for your OpenAI API key if not already configured
   - Check if documents are available
   - Build and start the Docker container

## Usage

### Local Usage

1. Add your documents to the `data/` directory
2. Run the ingestion script to process documents:
   ```
   python src/ingest.py
   ```
3. Run the API server:
   ```
   python src/api.py
   ```
4. Access the web interface at http://localhost:5000

### Docker Usage

1. Add your documents to the `data/` directory
2. Run the system:
   ```
   docker compose up
   ```
3. Access the web interface at http://localhost:5000

### Using Helper Script

1. Add your documents to the `data/` directory
2. Run the system:
   ```
   ./run_rag.sh
   ```
3. Access the web interface at http://localhost:5000

## API Endpoints

The system provides a REST API for interacting with the RAG system:

- `GET /health` - Health check endpoint
- `POST /query` - Send a query to the RAG system
  ```json
  {
    "query": "What is RAG?"
  }
  ```
- `POST /reset` - Reset the RAG session

## Web Interface

A simple web interface is available at http://localhost:5000 when running the API server. This provides a user-friendly way to interact with the RAG system.

## Models

The system uses the following OpenAI models:
- `text-embedding-3-small` for document embeddings
- `gpt-4o-mini` for generating responses

You can change these models in the `src/config.py` file.

## Evaluation

The system logs all queries and responses in the `logs/` directory. You can review these logs to evaluate system performance. 