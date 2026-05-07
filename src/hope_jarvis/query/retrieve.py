"""Query retrieval module."""

import logging
from typing import Any

from fastembed import TextEmbedding
from qdrant_client import QdrantClient

from hope_jarvis.config import (
    get_embedding_model_name,
    get_qdrant_api_key,
    get_qdrant_collection_name,
    get_qdrant_url,
    get_retrieval_score_threshold,
    get_retrieval_top_k,
)

# Suppress Hugging Face Hub warnings
logging.getLogger("huggingface_hub").setLevel(logging.ERROR)


def retrieve_relevant_chunks(
    query: str,
    qdrant_url: str = None,
    collection_name: str = None,
    top_k: int = None,
    score_threshold: float = None,
) -> list[dict[str, Any]]:
    """Retrieve relevant chunks from Qdrant based on query."""
    # Load config if not provided
    if qdrant_url is None or collection_name is None:
        qdrant_url = qdrant_url or get_qdrant_url()
        collection_name = collection_name or get_qdrant_collection_name()
        top_k = top_k or get_retrieval_top_k()
        score_threshold = score_threshold or get_retrieval_score_threshold()

    # Initialize clients
    qdrant_client = QdrantClient(url=qdrant_url, api_key=get_qdrant_api_key(), timeout=60)
    embedding_model = TextEmbedding(model_name=get_embedding_model_name())

    # Generate query embedding
    query_embedding = list(embedding_model.embed([query]))[0]

    # Search Qdrant
    search_results = qdrant_client.query_points(
        collection_name=collection_name,
        query=query_embedding,
        limit=top_k,
        score_threshold=score_threshold,
    )

    # Format results, filtering by score threshold if needed
    chunks = []
    for result in search_results.points:
        # Some Qdrant versions might not respect score_threshold in query_params
        if score_threshold is not None and result.score < score_threshold:
            continue
        chunks.append(
            {
                "content": result.payload.get("content", ""),
                "metadata": {
                    "repo_name": result.payload.get("repo_name"),
                    "file_path": result.payload.get("file_path"),
                    "raw_github_url": result.payload.get("raw_github_url"),
                    "rendered_html_url": result.payload.get("rendered_html_url"),
                    "headers": result.payload.get("headers", {}),
                    "score": result.score,
                },
            }
        )

    return chunks
