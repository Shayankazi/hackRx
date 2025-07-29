#!/usr/bin/env python3

import uvicorn
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import configuration
from config.settings import settings

if __name__ == "__main__":
    print(f"Starting {settings.API_TITLE} v{settings.API_VERSION}")
    print(f"Server will run on {settings.API_HOST}:{settings.API_PORT}")
    
    uvicorn.run(
        "api.main:app",
        host=settings.API_HOST,
        port=8002,  # Use explicit port to avoid env variable conflicts
        reload=True,  # Enable auto-reload for development
        workers=1,    # Use single worker for development; increase for production
    )
