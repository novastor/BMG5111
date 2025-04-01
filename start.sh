#!/bin/bash

# Install dependencies
#pip install -r requirements.txt

# Run Flask app using Gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker flask_app:app