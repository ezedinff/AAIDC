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
from config import get_config

app = create_app()

if __name__ == '__main__':
    cfg = get_config()
    port = int(os.environ.get('PORT', cfg.get('flask_port', 5000)))
    debug = os.environ.get('FLASK_ENV') == 'development'
    host = cfg.get('flask_host', '0.0.0.0')
    
    print(f"🚀 Starting Agentic AI Video Generator API on port {port}")
    print(f"🌐 API will be available at http://{host}:{port}")
    print(f"📊 Health check: http://{host}:{port}/api/health")
    print(f"📚 Video library: http://{host}:{port}/api/videos")
    
    app.run(
        host=host,
        port=port,
        debug=debug,
        threaded=True
    ) 