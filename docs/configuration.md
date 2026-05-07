# Configuration

HOPE Bot follows the [12-Factor App](https://12factor.net/config) methodology. All configuration is via environment variables.

## Required Environment Variables

These variables **must** be set for the application to run:

| Variable | Description | Example |
|----------|-------------|---------|
| `OLLAMA_HOST` | Ollama server hostname | `127.0.0.1` (local) or `ollama` (Docker) |
| `OLLAMA_MODEL` | LLM model name | `tinyllama:1.1b`, `llama3.1:8b` |
| `QDRANT_HOST` | Qdrant server hostname | `127.0.0.1` (local) or `qdrant` (Docker) |
| `QDRANT_COLLECTION_NAME` | Vector collection name | `hope_docs` |
| `EMBEDDING_MODEL_NAME` | Embedding model | `sentence-transformers/all-MiniLM-L6-v2` |
| `CONFIG_PATH` | Path to `repos.yaml` config dir | `./docker/app/config` |
| `DATA_DIR` | Path for cloned repos and data | `./~DATA/data/` |

## Optional Environment Variables

### Ollama Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_PORT` | `11434` | Ollama server port |
| `OLLAMA_TEMPERATURE` | `0.1` | Creativity level (0.0-1.0) |
| `OLLAMA_STREAMING` | `true` | Enable streaming responses |

**Recommended Models**:
- `tinyllama:1.1b` - Fastest, minimal resources (~637MB)
- `phi3:mini` - Best balance, good quality (~2.3GB)
- `llama3.1:8b` - High quality, more resources (~4.7GB)

### Qdrant Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `QDRANT_PROTOCOL` | `http` | Connection protocol: `http` or `grpc` |
| `QDRANT_HTTP_PORT` | `6333` | HTTP port (used when protocol is `http`) |
| `QDRANT_GRPC_PORT` | `6334` | gRPC port (used when protocol is `grpc`) |
| `QDRANT_API_KEY` | _(empty)_ | API key for authenticated Qdrant |

### Embedding Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `EMBEDDING_VECTOR_SIZE` | `384` | Vector dimensions |

**Recommended Models**:
- `sentence-transformers/all-MiniLM-L6-v2` - Default, good quality (80MB)
- `sentence-transformers/paraphrase-MiniLM-L3-v2` - Smaller, faster (50MB)

**Note**: Changing the embedding model requires re-ingestion:
```bash
jarvis db update --force
```

### Retrieval Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `RETRIEVAL_TOP_K` | `5` | Number of chunks to retrieve |
| `RETRIEVAL_SCORE_THRESHOLD` | `0.5` | Minimum similarity score (0.0-1.0) |

**Tuning Tips**:
- Lower `SCORE_THRESHOLD` if getting "no relevant info" responses
- Increase `TOP_K` for more context (slower but more comprehensive)

### Ingestion Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `INGESTION_CHUNK_SIZE` | `1000` | Characters per chunk |
| `INGESTION_CHUNK_OVERLAP` | `200` | Overlap between chunks |

**Guidelines**:
- Larger chunks: More context, fewer results
- Smaller chunks: More precise, may lose context
- Overlap: Helps maintain context across chunk boundaries

### Path Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `CONFIG_PATH` | _(required)_ | Directory containing `repos.yaml` and `sync_state.json` |
| `DATA_DIR` | _(required)_ | Directory for cloned repositories and knowledge base |
| `CHAINLIT_APP_ROOT` | _(optional)_ | Chainlit app root (theme, assets, chainlit.md) |

### Webhook Security

| Variable | Default | Description |
|----------|---------|-------------|
| `WEBHOOK_TOKEN` | _(empty)_ | Token to validate webhook requests |
| `WEBHOOK_PORT` | `9000` | Webhook server port |

If `WEBHOOK_TOKEN` is not set, authentication is disabled (development mode).

### Deployment Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `SENTRY_DSN` | _(empty)_ | Sentry DSN for error tracking |
| `ENVIRONMENT` | `production` | Deployment environment name |

### Hugging Face Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `HF_TOKEN` | _(empty)_ | Hugging Face token for higher rate limits |
| `HF_HUB_DISABLE_TELEMETRY` | `0` | Set to `1` to disable telemetry warnings |
| `HF_HOME` | `~/.cache/huggingface` | Hugging Face cache directory |
| `HF_HUB_CACHE` | `~/.cache/huggingface` | Alternative cache directory |

**To fix the warning:** "Warning: You are sending unauthenticated requests to the HF Hub"

**Option 1 - Set HF_TOKEN (recommended):**
1. Create a free account at https://huggingface.co
2. Generate a token at https://huggingface.co/settings/tokens
3. Add to `.env`:
```bash
HF_TOKEN=hf_xxxxxxxxxxxxx
```

**Option 2 - Suppress the warning:**
```bash
HF_HUB_DISABLE_TELEMETRY=1
```

**Note:** The embedding model (`sentence-transformers/all-MiniLM-L6-v2`) is downloaded from Hugging Face on first run.

---

## Environment Setup

### Using direnv (Recommended)

The project includes `.envrc` which loads `.env` via `dotenv` and exports all required variables.

```bash
# Install direnv: https://direnv.net
direnv allow
```

### Manual Setup

```bash
source .envrc
```

Or export variables individually:

```bash
# Services (local Docker)
export OLLAMA_HOST=127.0.0.1
export QDRANT_HOST=127.0.0.1

# Paths - share files with Docker compose
export CONFIG_PATH=./docker/app/config
export DATA_DIR=./~DATA/data/
export CHAINLIT_APP_ROOT=./docker/app

# Python
export PYTHONPATH="./src/"
```

---

## Local vs Docker Environment Comparison

The key difference between running locally and in Docker is the hostname for services:

| Variable | Local (with Docker services) | Full Docker |
|----------|------------------------------|-------------|
| `OLLAMA_HOST` | `127.0.0.1` | `ollama` |
| `QDRANT_HOST` | `127.0.0.1` | `qdrant` |
| `QDRANT_PROTOCOL` | `http` | `grpc` |
| `CONFIG_PATH` | `./docker/app/config` | `/jarvis/app/config` |
| `DATA_DIR` | `./~DATA/data/` | `/data/` |
| `CHAINLIT_APP_ROOT` | `./docker/app` | `/jarvis/app/` |

---

## Configuration Files

### repos.yaml

Located at `CONFIG_PATH/repos.yaml`:

```yaml
repos:
  - name: "HOPE"
    github_url: "https://github.com/unicef/hope"
    docs_dir: "docs"
    branch: "develop"
    rendered_base_url: "https://unicef.github.io/hope/"
    local_path: "repos/hope"

  - name: "Country Report"
    github_url: "https://github.com/unicef/hope-country-report"
    docs_dir: "docs"
    branch: "main"
    rendered_base_url: "https://unicef.github.io/hope-country-report/"
    local_path: "repos/country-report"
```

**Fields**:
- `name`: Unique identifier (used in CLI and Qdrant)
- `github_url`: Repository clone URL
- `docs_dir`: Directory containing markdown files
- `branch`: Git branch to use (default: `main`)
- `rendered_base_url`: Base URL for rendered documentation
- `local_path`: Local storage path (relative to `DATA_DIR`)

### sync_state.json

Located at `CONFIG_PATH/sync_state.json`. Tracks file hashes to detect changes during incremental sync. Automatically created on first `jarvis repo pull` or `jarvis db update`.

---

## Docker Compose Configuration

The `docker-compose.yml` uses environment variable substitution:

```yaml
x-variables: &variables
  OLLAMA_MODEL: ${OLLAMA_MODEL:-llama3.1:8b}
  QDRANT_API_KEY: ${QDRANT_API_KEY:-}
  QDRANT_COLLECTION_NAME: ${QDRANT_COLLECTION_NAME:-hope_docs}
  QDRANT_PROTOCOL: ${QDRANT_PROTOCOL:-grpc}
  ...

services:
  app:
    environment:
      <<: *variables
      OLLAMA_HOST: ollama
      QDRANT_HOST: qdrant
```

Create or edit `.env` in the project root to override defaults:

```bash
OLLAMA_MODEL=tinyllama:1.1b
QDRANT_VOLUME=./~DATA/qdrant_data
OLLAMA_VOLUME=./~DATA/ollama_data
JARVIS_VOLUME=./~DATA/data
QDRANT_COLLECTION_NAME=hope_docs
```

---

## Webhook API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/webhook` | POST | Receive GitHub push events |
| `/config` | GET | Return configuration info (repos, paths, models, cache) |
| `/health` | GET | Health check |

**Example usage:**
```bash
# Get configuration
curl http://localhost:9000/config

# Returns:
# {
#   "ollama_base_url": "http://localhost:11434",
#   "qdrant_url": "http://localhost:6333",
#   "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
#   "config_path": "/jarvis/app/config",
#   "data_path": "/data",
#   "knowledge_path": "/data/knowledge",
#   "repos_config": "/jarvis/app/config/repos.yaml",
#   "hf_cache": "/root/.cache/huggingface",
#   "repos": ["HOPE", "Aurora", ...]
# }
```
