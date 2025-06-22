.PHONY: down restart pull up git-pull

# Default list of services (can be overridden via CLI)
SERVICES ?= api-gateway ai-service user-service extension-service user-db ai-db extension-db

# Pull latest code from Git
git-pull:
	git pull

# Bring down specific services (or all if none specified)
down:
	docker compose down $(SERVICES)

# Pull the latest Docker images
pull:
	docker compose pull --ignore-pull-failures $(SERVICES)

# Bring up the services
up:
	docker compose up -d $(SERVICES)

# Restart the services: git pull, stop/remove, pull images, up
restart:
	$(MAKE) git-pull
	$(MAKE) down SERVICES="$(SERVICES)"
	$(MAKE) pull SERVICES="$(SERVICES)"
	$(MAKE) up SERVICES="$(SERVICES)"
