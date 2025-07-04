import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import after path setup
from app.celery_app import celery_app  # noqa: E402

if __name__ == "__main__":
    # Start the Celery worker
    celery_app.start()
