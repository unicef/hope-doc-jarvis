# Getting Started

## Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)
- Git
- [direnv](https://direnv.net/) (recommended for environment management)

---

## Local Development (Recommended)

Run Ollama and Qdrant in Docker, but run the Jarvis app locally for faster development iteration.

### 1. Clone the Repository

```bash
git clone https://github.com/unicef/hope-bot.git
cd hope-bot
```

### 2. Start Infrastructure Services

```bash
docker compose up ollama qdrant -d
```

This starts:
- **ollama** (port 11434) - LLM server for text generation and embeddings
- **qdrant** (port 6333/6334) - Vector database for semantic search

The `-d` flag runs them in detached mode (background).

### 3. Configure Environment

The project uses `.envrc` (loaded by `direnv`) which automatically loads `.env` and exports all required variables.

**Option A - Using direnv (recommended):**

```bash
direnv allow
```

**Option B - Manual loading:**

```bash
source .envrc
```

**What gets configured:**

| Variable | Value | Purpose |
|----------|-------|---------|
| `OLLAMA_HOST` | `127.0.0.1` | Points to local Docker Ollama |
| `QDRANT_HOST` | `127.0.0.1` | Points to local Docker Qdrant |
| `CONFIG_PATH` | `./docker/app/config` | Shares `repos.yaml` with Docker |
| `DATA_DIR` | `./~DATA/data/` | Shares data volume with Docker |
| `CHAINLIT_APP_ROOT` | `./docker/app` | Chainlit assets and config |
| `PYTHONPATH` | `./src/` | Local package resolution |

From `.env` (via `dotenv`):

| Variable | Value | Purpose |
|----------|-------|---------|
| `OLLAMA_MODEL` | `tinyllama:1.1b` | LLM model to use |
| `EMBEDDING_MODEL_NAME` | `sentence-transformers/all-MiniLM-L6-v2` | Embedding model |
| `QDRANT_COLLECTION_NAME` | `hope_docs` | Vector collection name |

**Key points:**
- `OLLAMA_HOST` and `QDRANT_HOST` point to `127.0.0.1` (Docker services exposed on localhost)
- `CONFIG_PATH` points to `./docker/app/config` to share the same `repos.yaml` as the Docker container
- `DATA_DIR` points to `./~DATA/data/` which maps to the same volume (`${JARVIS_VOLUME}`) used by Docker, keeping data in sync

### 4. Install and Run Locally

```bash
pip install -e .
jarvis repo pull          # Clone docs from GitHub and ingest into Qdrant
jarvis run web            # Start Chainlit on http://localhost:8000
```

**What `jarvis run web` does:**
- Starts the Chainlit web interface (default: `localhost:8000`)
- Connects to Ollama and Qdrant running in Docker
- Enables hot-reload for development (code changes reflect immediately)
- Custom bind: `jarvis run web --bind host[:port]`

**Optional - Start webhook server:**
```bash
jarvis run service        # Start webhook server (default: 0.0.0.0:9000)
```

This receives GitHub push events and triggers automatic updates.
Custom bind: `jarvis run service --bind host[:port]`

**Benefits of local development:**
- Fast iteration (no Docker rebuilds)
- Easy debugging
- Hot-reload for code changes
- Direct access to logs
- Shared data with Docker services

### 5. Start Using Jarvis

Open your browser to `http://localhost:8000` and start asking questions!

---

## Docker Deployment (Alternative)

For production or full Docker setup:

### 1. Clone the Repository

```bash
git clone https://github.com/unicef/hope-bot.git
cd hope-bot
```

### 2. Configure Environment

The `.env` file provides defaults. Customize as needed:

```bash
# Model selection
OLLAMA_MODEL=llama3.1:8b

# Volumes
QDRANT_VOLUME=./~DATA/qdrant_data
OLLAMA_VOLUME=./~DATA/ollama_data
JARVIS_VOLUME=./~DATA/data
```

### 3. Start All Services

```bash
docker compose up -d
```

This starts:
- **ollama** - LLM server
- **qdrant** - Vector database
- **hope-bot** - Chainlit web interface (port 8000) and webhook server (port 9000)

### 4. Ingest Documentation

```bash
docker compose exec hope-bot jarvis repo pull --force
```

### 5. Access the Interface

Open `http://localhost:8000` in your browser.

---

## Volume Sharing: Local ↔ Docker

When running locally with Docker services, data is shared through the same volumes:

| Resource | Docker Path | Local Path | Env Var |
|----------|-------------|------------|---------|
| App config | `/jarvis/app/config` | `./docker/app/config` | `CONFIG_PATH` |
| Chainlit app | `/jarvis/app/` | `./docker/app` | `CHAINLIT_APP_ROOT` |
| Data (repos, knowledge) | `/data/` | `./~DATA/data/` | `DATA_DIR` |
| Repos storage | `/data/repos/` | `./~DATA/data/repos/` | (inside DATA_DIR) |
| Knowledge base | `/data/knowledge/` | `./~DATA/data/knowledge/` | (inside DATA_DIR) |
| Qdrant storage | `/qdrant/storage` | `./~DATA/qdrant_data` | (compose only) |
| Ollama models | `/root/.ollama` | `./~DATA/ollama_data` | (compose only) |
| Hugging Face cache | `${DATA_DIR}/hf_cache` | `./~DATA/data/hf_cache` | `HF_HOME` |

This means:
- Repos cloned locally via `jarvis repo pull` are visible to Docker
- Qdrant data persists across both local and Docker runs
- Switch between local dev and Docker without re-ingesting

---

## Next Steps

- Configure [GitHub webhooks](webhook.md) for automatic updates
- Review [CLI commands](commands/index.md) for manual management
- Understand the [architecture](architecture.md)
- Review [configuration](configuration.md) for all environment variables
