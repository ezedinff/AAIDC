#!/usr/bin/env python3
"""
Flask Application Entry Point
Main server for the Agentic AI Video Generator
"""

import os
import sys
from flask import Flask

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api import create_app

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    print(f"🚀 Starting Agentic AI Video Generator API on port {port}")
    print(f"🌐 API will be available at http://localhost:{port}")
    print(f"📊 Health check: http://localhost:{port}/api/health")
    print(f"📚 Video library: http://localhost:{port}/api/videos")
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug,
        threaded=True
    ) 