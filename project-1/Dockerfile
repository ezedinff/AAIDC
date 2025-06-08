FROM python:3.10-slim

WORKDIR /app

# Install system dependencies in a single layer
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set pip configuration to avoid timeouts
ENV PIP_DEFAULT_TIMEOUT=300
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
ENV PIP_NO_CACHE_DIR=1

# Install dependencies in stages to handle potential network issues
COPY requirements.txt .
RUN pip install --no-cache-dir pip setuptools wheel --upgrade && \
    pip install --no-cache-dir openai python-dotenv tiktoken && \
    pip install --no-cache-dir langchain langchain_openai && \
    pip install --no-cache-dir langchain_community && \
    pip install --no-cache-dir faiss-cpu && \
    pip install --no-cache-dir chromadb || echo "ChromaDB failed, continuing build" && \
    pip install --no-cache-dir -r requirements.txt || echo "Some packages may have failed to install"

# Copy application
COPY . .
RUN mkdir -p data vector_db logs

ENV PYTHONPATH=/app
CMD ["python", "src/main.py"] 