.PHONY: install run dev lint format test setup help build docker-run docker-compose-up docker-compose-down

# Extract DISCORD_BOT_TOKEN from config.yaml using poetry run python
DISCORD_BOT_TOKEN := $(shell poetry run python -c "import yaml; config = yaml.safe_load(open('config.yaml')); print(config['discord']['bot_token'])" 2>/dev/null || echo "")
export DISCORD_BOT_TOKEN

# Default target
help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

setup: ## Setup project (copy config.example.yaml to config.yaml if not exists)
	@if [ ! -f config.yaml ]; then \
		echo "Creating config.yaml file from config.example.yaml..."; \
		cp config.example.yaml config.yaml; \
		echo "Please edit config.yaml file and set your Discord bot token"; \
	else \
		echo "config.yaml file already exists"; \
	fi

install: ## Install dependencies
	poetry install

run: ## Run the Discord bot
	@if [ ! -f config.yaml ]; then \
		echo "Error: config.yaml file not found. Run 'make setup' first."; \
		exit 1; \
	fi
	poetry run python -m claude_code_discord_agent.main

dev: ## Run in development mode with auto-reload
	@if [ ! -f config.yaml ]; then \
		echo "Error: config.yaml file not found. Run 'make setup' first."; \
		exit 1; \
	fi
	poetry run python -m claude_code_discord_agent.main

lint: ## Run linting
	poetry run ruff check .

format: ## Format code
	poetry run ruff format .
	poetry run ruff check . --fix

test: ## Run tests
	poetry run pytest

build: ## Build Docker image
	docker build -t claude-code-discord-agent .

docker-run: ## Run Docker container with volume mount
	docker run --rm --name claude-code-discord-agent -v "$(PWD)/config.yaml:/app/config.yaml:ro" claude-code-discord-agent

docker-compose-up: ## Start services with docker-compose
	docker-compose up -d

docker-compose-down: ## Stop services with docker-compose
	docker-compose down