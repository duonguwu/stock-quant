#!/usr/bin/env python3
"""
Simple script to run the Trading Dashboard
"""

import uvicorn
import sys
from pathlib import Path

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

if __name__ == "__main__":
    print("🚀 Starting Simple Trading Dashboard...")
    print("📊 Access dashboard at: http://localhost:8000")
    print("📈 API docs at: http://localhost:8000/docs")
    print("🛑 Press Ctrl+C to stop")
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 