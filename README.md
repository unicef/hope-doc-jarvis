# HOPE Jarvis

RAG Bot for UNICEF HOPE documentation.

## Quick Start (Local Development - Recommended)

Run Ollama and Qdrant in Docker, then run the app locally for fast development iteration.

### 1. Start Infrastructure

```bash
docker compose up ollama qdrant -d
```

Starts **Ollama** (LLM server on port 11434) and **Qdrant** (vector database on ports 6333/6334) in background.

### 2. Configure Environment

```bash
pip install -e .
direnv allow    # or: source .envrc
```

The `.envrc` file configures everything you need:
- `OLLAMA_HOST=127.0.0.1` and `QDRANT_HOST=127.0.0.1` to connect to Docker services
- `CONFIG_PATH=./docker/app/config` to share `repos.yaml` with Docker
- `DATA_DIR=./~DATA/data/` to share the data volume with Docker
- `CHAINLIT_APP_ROOT=./docker/app` for Chainlit assets

From `.env` (loaded automatically):
- `OLLAMA_MODEL=tinyllama:1.1b`
- `EMBEDDING_MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2`
- `QDRANT_COLLECTION_NAME=hope_docs`

**Note:** On first run, the embedding model downloads from Hugging Face. To avoid the warning _"Warning: You are sending unauthenticated requests to the HF Hub"_, either:
- Set `HF_HUB_DISABLE_TELEMETRY=1`, or
- Get a free token from https://huggingface.co/settings/tokens and set `HF_TOKEN=hf_xxxxxxxxx`

### 3. Ingest Documentation

```bash
jarvis repo pull      # Clone docs from GitHub
jarvis db update      # Ingest into Qdrant
```

### 4. Run the App

```bash
jarvis run web        # Start Chainlit web interface (http://localhost:8000)
jarvis run service    # Start webhook server (port 9000)
```

**What these do:**
- `jarvis run web` - Starts the Chainlit web interface, connects to Ollama and Qdrant running in Docker
- `jarvis run service` - Starts the webhook server to receive GitHub push events and trigger auto-updates

---

## Full Docker Deployment (Alternative)

For production or containerized setup:

```bash
docker compose up -d
docker compose exec hope-bot jarvis repo pull
docker compose exec hope-bot jarvis db update --force
```

Access at `http://localhost:8000`.

---

## CLI Commands

```bash
jarvis run                # Start Chainlit web interface
jarvis repo pull          # Pull GitHub repos
jarvis db update          # Ingest docs into Qdrant
jarvis db reset           # Reset Qdrant data
jarvis db info            # Show database stats
jarvis kb list            # List knowledge base entries
jarvis kb reset           # Clear knowledge base
jarvis check              # Verify configuration
```

**Command details:**
- `jarvis run web` - Starts the Chainlit web UI locally (connects to Docker services)
- `jarvis run service` - Starts the webhook server (Uvicorn) with API endpoints
- `jarvis repo pull` - Clones/pulls documentation repos from GitHub
- `jarvis db update [-r repo] [--force]` - Processes markdown files and stores embeddings in Qdrant
- `jarvis db reset [-r repo]` - Deletes Qdrant data (with confirmation)
- `jarvis db info` - Displays collection status, point count, and chunks per repo
- `jarvis kb list` - Lists all saved Q&A pairs from satisfied users
- `jarvis kb reset` - Deletes all knowledge base entries (with confirmation)
- `jarvis check` - Verifies all environment variables and service connectivity

**Webhook API (after `jarvis run service`):**
- `POST /webhook` - Receive GitHub push events
- `GET /config` - Return configuration info (repos, paths, models, cache)
- `GET /health` - Health check endpoint

## Documentation

Full documentation available in the [`docs/`](docs/) directory:
- [Getting Started](docs/getting-started.md) - Detailed setup guide with Docker↔Local sharing
- [CLI Commands](docs/commands/index.md) - Complete command reference
- [Configuration](docs/configuration.md) - Environment variables reference
- [Architecture](docs/architecture.md) - System design overview
- [Webhook](docs/webhook.md) - GitHub webhook integration

## Useful Links

- **Chainlit Documentation:** https://docs.chainlit.io
- **Ollama:** https://ollama.ai
- **Qdrant:** https://qdrant.tech
