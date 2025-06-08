# RAG System for Abortion Awareness Education

A retrieval-augmented generation (RAG) system that provides factual, educational information about abortion awareness, reproductive health, and related women's health topics. This implementation uses OpenAI's models for both embeddings and the language model.

## Target Audience

This system is designed for:
- Educators providing reproductive health information
- Health professionals seeking a reference tool
- Students learning about women's reproductive health
- Anyone seeking factual, educational information about abortion and reproductive health

## Repository Structure

- `data/` - Contains knowledge documents used for the RAG system
- `src/` - Source code for the RAG implementation
  - `api.py` - Flask API server
  - `config.py` - Configuration settings
  - `ingest.py` - Document ingestion and processing
  - `main.py` - Main entry point
  - `rag_chain.py` - Core RAG implementation
  - `prompt_utils.py` - Prompt template utilities
  - `config_loader.py` - YAML configuration loader
- `static/` - Web interface HTML, CSS, and JavaScript
- `logs/` - Log files for system interactions

## Prerequisites

Before installation, ensure you have:
- Python 3.9 or higher
- An OpenAI API key with access to GPT-4o models
- At least 4GB of RAM available
- Basic understanding of terminal/command line interfaces
- Sufficient disk space (at least 1GB) for document storage and embeddings

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

### Data Requirements

The system works with text documents in the following formats:
- `.txt` - Plain text files
- `.pdf` - PDF documents
- `.docx` - Microsoft Word documents
- `.html` - Web pages

Documents should contain factual information about abortion, reproductive health, and related topics.

## API Endpoints

The system provides a REST API for interacting with the RAG system:

- `GET /health` - Health check endpoint
- `POST /query` - Send a query to the RAG system
  ```json
  {
    "query": "What is abortion?"
  }
  ```
- `POST /reset` - Reset the RAG session
- `GET /strategies` - Get available reasoning strategies
- `POST /strategy` - Set reasoning strategy
- `GET /prompt_templates` - Get available prompt templates
- `POST /prompt_template` - Set prompt template

## Web Interface

A simple web interface is available at http://localhost:5000 when running the API server. This provides a user-friendly way to interact with the RAG system.

## Models and Configuration

The system uses the following OpenAI models:
- `text-embedding-3-small` for document embeddings
- `gpt-4o-mini` for generating responses

Key configuration options:
- `CHUNK_SIZE` - Size of text chunks for embeddings (default: 1000)
- `CHUNK_OVERLAP` - Overlap between chunks (default: 200)
- `TOP_K_RESULTS` - Number of document chunks to retrieve (default: 4)
- `TEMPERATURE` - Model temperature setting (default: 0.2)
- `MAX_TOKENS` - Maximum tokens in response (default: 1000)

You can change these settings in the `src/config.py` file.

## Testing

To run the test suite:

```bash
# Install test dependencies
pip install -r requirements-test.txt

# Run all tests
python -m pytest tests/

# Run specific test file
python -m pytest tests/test_rag_chain.py
```

## Contributing

Contributions to this project are welcome. Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests to ensure they pass
5. Commit your changes (`git commit -m 'Add some amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

Please ensure your code follows the project's style guidelines and includes appropriate tests.

## Contact

For questions, issues, or contributions, please contact:
- Project Maintainer: [Ezedin Fedlu] - [ezedin.fedlu@gmail.com]
- GitHub Issues: [Submit an issue](https://github.com/ezedinff/aaidc)

## License

This project is licensed under the [MIT License](./LICENSE)