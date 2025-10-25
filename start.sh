#!/bin/bash
# Render startup script for Financial Analysis Application

# Install dependencies
pip install -r requirements.txt

# Start the application with gunicorn
gunicorn --bind 0.0.0.0:$PORT app:app