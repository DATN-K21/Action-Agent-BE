# Helm management Makefile for Action-Agent backend

.PHONY: help deploy upgrade uninstall status dry-run

ENV ?= dev
NAMESPACE ?= default
RELEASE_NAME ?= action-agent

help:
	@echo "Action-Agent Helm commands"
	@echo "  deploy      - install chart"
	@echo "  upgrade     - upgrade existing release"
	@echo "  uninstall   - remove release"
	@echo "  status      - show release status"
	@echo "  dry-run     - helm dry run"

deploy:
	./helm-deploy.sh --environment $(ENV) --namespace $(NAMESPACE) --release $(RELEASE_NAME)

upgrade:
	./helm-deploy.sh --environment $(ENV) --namespace $(NAMESPACE) --release $(RELEASE_NAME) --upgrade

uninstall:
	helm uninstall $(RELEASE_NAME)-$(ENV) --namespace $(NAMESPACE)

status:
	helm status $(RELEASE_NAME)-$(ENV) --namespace $(NAMESPACE)

dry-run:
	./helm-deploy.sh --environment $(ENV) --namespace $(NAMESPACE) --release $(RELEASE_NAME) --dry-run
