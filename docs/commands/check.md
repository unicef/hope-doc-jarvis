# jarvis check

Verify that all required environment variables are properly configured.

## Syntax

```bash
jarvis check
```

## Required Environment Variables

| Variable | Description |
|----------|-------------|
| `OLLAMA_BASE_URL` | Ollama API endpoint |
| `OLLAMA_MODEL` | LLM model name (e.g., `tinyllama:1.1b`) |
| `QDRANT_URL` | Qdrant API endpoint |
| `QDRANT_COLLECTION_NAME` | Qdrant collection name |
| `EMBEDDING_MODEL_NAME` | Embedding model for vector search |
| `CONFIG_PATH` | Path to configuration directory |
| `DATA_PATH` | Path to data storage directory |

## Output

### Success
```
✅ All environment variables are set.
```

### Missing Variables
```
❌ Missing environment variables:
  - QDRANT_URL
  - EMBEDDING_MODEL_NAME
```

## Usage

Run this command after:
- Initial setup
- Changing `.env` file
- Deploying to a new environment
- Troubleshooting connection issues

## Note

This command only checks if variables are **set**, not if they point to valid services. Use `jarvis db info` to verify Qdrant connectivity.
