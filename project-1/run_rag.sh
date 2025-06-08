#!/bin/bash

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Creating .env file. Please enter your OpenAI API key:"
    read -p "OPENAI_API_KEY=" api_key
    echo "OPENAI_API_KEY=$api_key" > .env
    echo ".env file created successfully!"
else
    echo ".env file already exists."
fi

# Check if data directory has documents
if [ -z "$(ls -A data 2>/dev/null)" ]; then
    echo "Warning: data directory is empty. Please add documents to the data directory before running the RAG system."
    echo "A sample document has been provided for testing."
fi

# Build and run the Docker container
echo "Building and starting the RAG API service..."
docker compose up --build

exit 0 