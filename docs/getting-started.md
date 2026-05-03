# Getting Started

## Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)
- Git

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/unicef/hope-bot.git
cd hope-bot
```

### 2. Configure Environment

Create a `.env` file:

```bash
# Ollama Settings
OLLAMA_MODEL=tinyllama:1.1b
OLLAMA_TEMPERATURE=0.1

# Qdrant Settings
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION_NAME=hope_docs

# Embedding Model
EMBEDDING_MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2

# Paths
CONFIG_PATH=./config
DATA_PATH=./data

# Webhook Security (optional)
WEBHOOK_TOKEN=your-secret-token
```

### 3. Start Services

```bash
docker-compose up -d
```

This starts:
- **Ollama** - LLM server (port 11434)
- **Qdrant** - Vector database (port 6333)
- **HOPE Bot** - Web interface (port 8000) and webhook server (port 9000)

### 4. Ingest Documentation

```bash
# Update all repositories
docker-compose exec hope-bot jarvis update --all --force
```

### 5. Access the Interface

Open your browser to `http://localhost:8000` and start asking questions!

## Next Steps

- Configure [GitHub webhooks](webhook.md) for automatic updates
- Review [CLI commands](commands/index.md) for manual management
- Understand the [architecture](architecture.md)
