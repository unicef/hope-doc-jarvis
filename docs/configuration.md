# Configuration

HOPE Bot follows the [12-Factor App](https://12factor.net/config) methodology. All configuration is via environment variables.

## Environment Variables

### Ollama (LLM) Settings

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OLLAMA_BASE_URL` | Yes | - | Ollama API endpoint (e.g., `http://localhost:11434`) |
| `OLLAMA_MODEL` | Yes | - | Model name (e.g., `tinyllama:1.1b`, `phi3:mini`) |
| `OLLAMA_TEMPERATURE` | No | `0.1` | Creativity level (0.0-1.0) |
| `OLLAMA_STREAMING` | No | `true` | Enable streaming responses |

**Recommended Models**:
- `tinyllama:1.1b` - Fastest, minimal resources (~637MB)
- `phi3:mini` - Best balance, good quality (~2.3GB)
- `llama3.1:8b` - High quality, more resources (~4.7GB)

### Qdrant (Vector Database) Settings

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `QDRANT_URL` | Yes | - | Qdrant API endpoint (e.g., `http://localhost:6333`) |
| `QDRANT_COLLECTION_NAME` | Yes | - | Collection name for storing vectors |

### Embedding Settings

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `EMBEDDING_MODEL_NAME` | Yes | - | Model for text embeddings |
| `EMBEDDING_VECTOR_SIZE` | No | `384` | Vector dimensions |

**Recommended Models**:
- `sentence-transformers/all-MiniLM-L6-v2` - Default, good quality (80MB)
- `sentence-transformers/paraphrase-MiniLM-L3-v2` - Smaller, faster (50MB)

**Note**: Changing the embedding model requires re-ingestion:
```bash
jarvis update --all --force
```

### Retrieval Settings

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `RETRIEVAL_TOP_K` | No | `5` | Number of chunks to retrieve |
| `RETRIEVAL_SCORE_THRESHOLD` | No | `0.5` | Minimum similarity score (0.0-1.0) |

**Tuning Tips**:
- Lower `SCORE_THRESHOLD` if getting "no relevant info" responses
- Increase `TOP_K` for more context (slower but more comprehensive)

### Ingestion Settings

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `INGESTION_CHUNK_SIZE` | No | `1000` | Characters per chunk |
| `INGESTION_CHUNK_OVERLAP` | No | `200` | Overlap between chunks |

**Guidelines**:
- Larger chunks: More context, fewer results
- Smaller chunks: More precise, may lose context
- Overlap: Helps maintain context across chunk boundaries

### Path Settings

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `CONFIG_PATH` | Yes | - | Directory containing `repos.yaml` and `sync_state.json` |
| `DATA_PATH` | Yes | - | Directory for cloned repositories |

### Webhook Security

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `WEBHOOK_TOKEN` | No | (empty) | Token to validate webhook requests |

If not set, authentication is disabled (development mode).

## Configuration Files

### repos.yaml

Located at `CONFIG_PATH/repos.yaml`:

```yaml
repos:
  - name: "HOPE"
    github_url: "https://github.com/unicef/hope"
    docs_dir: "docs"
    rendered_base_url: "https://unicef.github.io/hope/"
    local_path: "repos/hope"

  - name: "Country Report"
    github_url: "https://github.com/unicef/hope-country-report"
    docs_dir: "docs"
    rendered_base_url: "https://unicef.github.io/hope-country-report/"
    local_path: "repos/country-report"
```

**Fields**:
- `name`: Unique identifier (used in CLI and Qdrant)
- `github_url`: Repository clone URL
- `docs_dir`: Directory containing markdown files
- `rendered_base_url`: Base URL for rendered documentation
- `local_path`: Local storage path (relative to `DATA_PATH`)

## .env Example

```bash
# Ollama
OLLAMA_MODEL=tinyllama:1.1b
OLLAMA_TEMPERATURE=0.1
OLLAMA_STREAMING=true

# Qdrant
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION_NAME=hope_docs

# Embeddings
EMBEDDING_MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2

# Retrieval
RETRIEVAL_TOP_K=5
RETRIEVAL_SCORE_THRESHOLD=0.5

# Ingestion
INGESTION_CHUNK_SIZE=1000
INGESTION_CHUNK_OVERLAP=200

# Paths
CONFIG_PATH=/app/config
DATA_PATH=/data

# Webhook
WEBHOOK_TOKEN=your-secret-token
```

## Docker Compose Override

For production, use environment substitution in `docker-compose.yml`:

```yaml
environment:
  - OLLAMA_MODEL=${OLLAMA_MODEL:-tinyllama:1.1b}
  - QDRANT_URL=${QDRANT_URL:-http://qdrant:6333}
  - WEBHOOK_TOKEN=${WEBHOOK_TOKEN:-}
```

Create a `.env` file in the project root to override defaults.
