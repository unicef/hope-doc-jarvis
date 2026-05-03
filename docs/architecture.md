# Architecture

HOPE Bot uses a RAG (Retrieval-Augmented Generation) architecture to provide accurate answers from documentation.

## System Overview

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   GitHub    │────▶│   Ingestion  │────▶│   Qdrant    │
│  Repositories│     │    Pipeline   │     │  (Vectors)  │
└─────────────┘     └──────────────┘     └──────┬──────┘
                                                │
┌─────────────┐     ┌──────────────┐           │
│   User      │────▶│  Chainlit    │───────────┘
│  (Browser)  │     │  Interface   │           │
└─────────────┘     └──────────────┘           │
                          │                    │
                          ▼                    ▼
                   ┌──────────────┐     ┌─────────────┐
                   │    Ollama    │◀────│  Retrieval  │
                   │  (LLM +     │     │  (Semantic  │
                   │   Embeddings)│     │   Search)   │
                   └──────────────┘     └─────────────┘
```

## Components

### 1. Ingestion Pipeline

**Purpose**: Process markdown documentation and store in vector database.

**Flow**:
1. **Sync**: Clone or pull GitHub repositories (`sync.py`)
2. **Detect Changes**: Compare file hashes via `sync_state.json`
3. **Chunk**: Split markdown using header-aware chunking (`chunker.py`)
4. **Embed**: Generate vectors using FastEmbed (`store.py`)
5. **Store**: Upsert into Qdrant with metadata

**Key Files**:
- `src/hope_jarvis/ingestion/sync.py` - Git operations
- `src/hope_jarvis/ingestion/chunker.py` - Markdown splitting
- `src/hope_jarvis/ingestion/store.py` - Qdrant operations

### 2. Vector Database (Qdrant)

**Purpose**: Store and retrieve document embeddings.

**Collection Schema**:
```python
{
  "id": <hash of repo+file+chunk>,
  "vector": <embedding vector>,
  "payload": {
    "content": "<chunk text>",
    "repo_name": "<repository name>",
    "file_path": "<relative path>",
    "rendered_html_url": "<documentation URL>",
    "headers": { "header_1": "...", "header_2": "..." }
  }
}
```

**Configuration**:
- Vector size: Depends on embedding model (default: 384 for all-MiniLM-L6-v2)
- Distance metric: Cosine similarity
- Collection name: Configured via `QDRANT_COLLECTION_NAME`

### 3. Retrieval System

**Purpose**: Find relevant documentation chunks for user queries.

**Flow**:
1. Convert user query to embedding
2. Search Qdrant for similar vectors
3. Filter by score threshold
4. Return top-k results with metadata

**Key File**: `src/hope_jarvis/query/retrieve.py`

### 4. LLM Interface (Ollama)

**Purpose**: Generate answers using retrieved context.

**Flow**:
1. Receive user question
2. Retrieve relevant chunks
3. Build prompt with context
4. Stream response from Ollama
5. Display answer with source citations

**Key File**: `src/hope_jarvis/app.py` (Chainlit interface)

### 5. Webhook Server

**Purpose**: Automatically trigger updates on GitHub pushes.

**Flow**:
1. Receive POST from GitHub
2. Validate token (if configured)
3. Extract repository name
4. Run `jarvis update <repo>`
5. Return status response

**Key File**: `src/hope_jarvis/webhook.py`

## Data Flow Example

**User asks**: "How do I configure authentication?"

1. **Query Embedding**: `"How do I configure authentication?"` → `[0.1, 0.3, ...]`
2. **Vector Search**: Qdrant returns top 5 similar chunks
3. **Context Assembly**: Concatenate chunk contents with source URLs
4. **LLM Prompt**:
   ```
   Context: [chunk1 content] Source: ...
             [chunk2 content] Source: ...

   Question: How do I configure authentication?
   ```
5. **Response**: LLM generates answer with citations like `[Source: ...]`

## Configuration

All configuration is 12-Factor compliant, using environment variables:

| Component | Variables |
|-----------|-----------|
| Ollama | `OLLAMA_BASE_URL`, `OLLAMA_MODEL`, `OLLAMA_TEMPERATURE` |
| Qdrant | `QDRANT_URL`, `QDRANT_COLLECTION_NAME` |
| Embeddings | `EMBEDDING_MODEL_NAME`, `EMBEDDING_VECTOR_SIZE` |
| Retrieval | `RETRIEVAL_TOP_K`, `RETRIEVAL_SCORE_THRESHOLD` |
| Ingestion | `INGESTION_CHUNK_SIZE`, `INGESTION_CHUNK_OVERLAP` |

See [Configuration](configuration.md) for details.

## Technology Stack

| Layer | Technology |
|-------|------------|
| LLM | Ollama (local LLMs) |
| Embeddings | FastEmbed (sentence-transformers) |
| Vector DB | Qdrant |
| Web Framework | Chainlit |
| CLI | Click |
| Container | Docker / Docker Compose |
