.PHONY: down restart pull up git-pull

# Define the services
SERVICES = ai-service user-service api-gateway user-database ai-database

# Pull latest code from Git
git-pull:
	git pull

# Bring down the services
down:
	docker compose down

# Pull the latest Docker images
pull:
	docker compose pull --ignore-pull-failures $(SERVICES)

# Bring up the services
up:
	docker compose up -d $(SERVICES)

# Restart the services: git pull, down, pull docker images, up
restart: git-pull down pull up
