.PHONY: run migrate dev start

# Run database migrations
migrate:
	alembic upgrade head

# Start the application (development)
dev:
	uvicorn app.main:app --host 0.0.0.0 --port 15001 --reload

# Start the application with migrations (production-like)
start: migrate
	uvicorn app.main:app --host 0.0.0.0 --port 15001

# Legacy run command (kept for compatibility)
run:
	uvicorn app.main:app --host 0.0.0 --port 15001 --reload