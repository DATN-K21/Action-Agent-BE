"""
Main module for the ingest-service. This is just a wrapper to import the celery app.
The actual initialization and configuration happens in app.celery_app and app.core.init.
"""

# Just import the celery app to make it available
from app.celery_app import celery_app

# Export the celery app for the celery command
app = celery_app
