#!/bin/bash

# setup venv if not exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "Installing dependencies..."
pip install -r requirements.txt

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Creating .env file. Please enter your OpenAI API key:"
    cp env.example .env
    read -p "OPENAI_API_KEY=" api_key
    sed -i "s/OPENAI_API_KEY=.*/OPENAI_API_KEY=$api_key/" .env
    echo ".env file created successfully!"
else
    echo ".env file already exists."
fi

# Create output directories
mkdir -p outputs temp data

# Make main.py executable
chmod +x main.py

echo "✅ Setup complete!"
