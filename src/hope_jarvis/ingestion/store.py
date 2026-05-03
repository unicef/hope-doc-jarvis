"""Qdrant storage module. 12-Factor: config from env vars."""

from typing import Any, Dict, List

from fastembed import TextEmbedding
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from hope_jarvis.config import (
    get_embedding_model_name,
    get_embedding_vector_size,
    get_qdrant_api_key,
    get_qdrant_collection_name,
    get_qdrant_url,
)


def _get_qdrant_config():
    """Load Qdrant and embedding config from environment."""
    return {
        "url": get_qdrant_url(),
        "collection_name": get_qdrant_collection_name(),
    }, {
        "model_name": get_embedding_model_name(),
        "vector_size": get_embedding_vector_size(),
    }


def init_qdrant_collection():
    """Initialize Qdrant collection if not exists."""
    qdrant_config, embedding_config = _get_qdrant_config()

    client = QdrantClient(url=qdrant_config["url"], api_key=get_qdrant_api_key())

    collections = client.get_collections().collections
    collection_names = [c.name for c in collections]

    if qdrant_config["collection_name"] not in collection_names:
        client.create_collection(
            collection_name=qdrant_config["collection_name"],
            vectors_config=VectorParams(
                size=embedding_config["vector_size"], distance=Distance.COSINE
            ),
        )
        print(f"Created collection: {qdrant_config['collection_name']}")
    else:
        print(f"Collection already exists: {qdrant_config['collection_name']}")

    return client


def store_chunks_in_qdrant(
    chunks: List[Dict[str, Any]],
    qdrant_url: str = None,
    collection_name: str = None,
) -> None:
    """Store chunks with embeddings in Qdrant."""
    qdrant_config, embedding_config = _get_qdrant_config()

    if qdrant_url is None:
        qdrant_url = qdrant_config["url"]
    if collection_name is None:
        collection_name = qdrant_config["collection_name"]

    client = QdrantClient(url=qdrant_url, api_key=get_qdrant_api_key())
    embedding_model = TextEmbedding(model_name=embedding_config["model_name"])

    points = []
    for chunk in chunks:
        embedding = list(embedding_model.embed([chunk["content"]]))[0]

        point = PointStruct(
            id=abs(
                hash(
                    f"{chunk['metadata']['repo_name']}_{chunk['metadata']['file_path']}_{chunk['metadata']['chunk_index']}"
                )
            ),
            vector=embedding,
            payload={"content": chunk["content"], **chunk["metadata"]},
        )
        points.append(point)

    batch_size = 100
    for i in range(0, len(points), batch_size):
        batch = points[i : i + batch_size]
        client.upsert(collection_name=collection_name, points=batch)

    print(f"Stored {len(points)} chunks in Qdrant")
