#!/usr/bin/env python3
"""
RAG Intent Gateway - Main Entry Point.

Usage:
    python main.py

The application will start on http://localhost:8000
"""
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.main import main

if __name__ == "__main__":
    main()