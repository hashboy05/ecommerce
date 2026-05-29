"""
WSGI entry point for production servers (e.g. gunicorn).

Usage (inside the Docker container):
    gunicorn --bind 0.0.0.0:5000 wsgi:app

This imports the application factory and builds a single app instance for the
WSGI server to serve. ``create_app`` also creates the database tables on first
import, so no separate migration step is needed for the SQLite prototype.
"""
from app import create_app

app = create_app()
