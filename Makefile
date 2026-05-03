.PHONY: help install sync ingest test docker-up docker-down docker-build

help:
	@echo "HOPE Bot - Available commands:"
	@echo "  make install      - Install dependencies with uv"
	@echo "  make docker-up    - Start all services with docker-compose"
	@echo "  make docker-down  - Stop all services"
	@echo "  make docker-build - Build docker images"

install:
	uv venv
	uv sync
	echo  'source .venv/bin/activate' >> .envrc

docker-up:
	docker-compose stop
	docker-compose rm --force
	docker-compose up --build

run:
	cd docker && chainlit run -w ../src/hope_jarvis/app.py

docker-down:
	docker-compose down

docker-build:
	docker-compose build
