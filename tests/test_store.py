import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from hope_jarvis.ingestion.store import (
    _get_qdrant_config,
    init_qdrant_collection,
    store_chunks_in_qdrant,
)


class TestGetQdrantConfig:
    """Test _get_qdrant_config function."""

    @patch(
        "hope_jarvis.ingestion.store.get_qdrant_url",
        return_value="http://localhost:6333",
    )
    @patch(
        "hope_jarvis.ingestion.store.get_qdrant_collection_name",
        return_value="test-collection",
    )
    @patch(
        "hope_jarvis.ingestion.store.get_embedding_model_name",
        return_value="test-model",
    )
    @patch("hope_jarvis.ingestion.store.get_embedding_vector_size", return_value=384)
    def test_returns_correct_config(self, mock_size, mock_model, mock_collection, mock_url):
        """Test that config is returned correctly."""
        qdrant_config, embedding_config = _get_qdrant_config()

        assert qdrant_config["url"] == "http://localhost:6333"
        assert qdrant_config["collection_name"] == "test-collection"
        assert embedding_config["model_name"] == "test-model"
        assert embedding_config["vector_size"] == 384


class TestInitQdrantCollection:
    """Test init_qdrant_collection function."""

    @patch("hope_jarvis.ingestion.store.QdrantClient")
    @patch("hope_jarvis.ingestion.store._get_qdrant_config")
    def test_creates_collection_when_not_exists(self, mock_config, mock_client_class):
        """Test that collection is created when it doesn't exist."""
        mock_config.return_value = (
            {"url": "http://localhost:6333", "collection_name": "new-collection"},
            {"model_name": "test-model", "vector_size": 384},
        )

        mock_client = MagicMock()
        mock_client.get_collections.return_value.collections = []
        mock_client_class.return_value = mock_client

        result = init_qdrant_collection()

        mock_client.create_collection.assert_called_once()
        assert result == mock_client

    @patch("hope_jarvis.ingestion.store.QdrantClient")
    @patch("hope_jarvis.ingestion.store._get_qdrant_config")
    def test_skips_creation_when_exists(self, mock_config, mock_client_class):
        """Test that collection creation is skipped when it exists."""
        mock_config.return_value = (
            {"url": "http://localhost:6333", "collection_name": "existing-collection"},
            {"model_name": "test-model", "vector_size": 384},
        )

        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_collection.name = "existing-collection"
        mock_client.get_collections.return_value.collections = [mock_collection]
        mock_client_class.return_value = mock_client

        result = init_qdrant_collection()

        mock_client.create_collection.assert_not_called()
        assert result == mock_client


class TestStoreChunksInQdrant:
    """Test store_chunks_in_qdrant function."""

    @patch("hope_jarvis.ingestion.store.QdrantClient")
    @patch("hope_jarvis.ingestion.store.TextEmbedding")
    @patch("hope_jarvis.ingestion.store._get_qdrant_config")
    def test_stores_single_chunk(self, mock_config, mock_embedding_class, mock_client_class):
        """Test storing a single chunk."""
        mock_config.return_value = (
            {"url": "http://localhost:6333", "collection_name": "test-collection"},
            {"model_name": "test-model", "vector_size": 384},
        )

        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        mock_embedding = MagicMock()
        mock_embedding.embed.return_value = [MagicMock()]
        mock_embedding_class.return_value = mock_embedding

        chunks = [
            {
                "content": "test content",
                "metadata": {
                    "repo_name": "HOPE",
                    "file_path": "docs/test.md",
                    "chunk_index": 0,
                },
            }
        ]

        store_chunks_in_qdrant(chunks)

        mock_client.upsert.assert_called_once()

    @patch("hope_jarvis.ingestion.store.QdrantClient")
    @patch("hope_jarvis.ingestion.store.TextEmbedding")
    @patch("hope_jarvis.ingestion.store._get_qdrant_config")
    def test_stores_multiple_chunks(self, mock_config, mock_embedding_class, mock_client_class):
        """Test storing multiple chunks."""
        mock_config.return_value = (
            {"url": "http://localhost:6333", "collection_name": "test-collection"},
            {"model_name": "test-model", "vector_size": 384},
        )

        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        mock_embedding = MagicMock()
        mock_embedding.embed.return_value = [MagicMock()]
        mock_embedding_class.return_value = mock_embedding

        chunks = [
            {
                "content": f"content {i}",
                "metadata": {
                    "repo_name": "HOPE",
                    "file_path": f"docs/test{i}.md",
                    "chunk_index": i,
                },
            }
            for i in range(5)
        ]

        store_chunks_in_qdrant(chunks)

        mock_client.upsert.assert_called_once()

    @patch("hope_jarvis.ingestion.store.QdrantClient")
    @patch("hope_jarvis.ingestion.store.TextEmbedding")
    @patch("hope_jarvis.ingestion.store._get_qdrant_config")
    def test_uses_custom_url_and_collection(self, mock_config, mock_embedding_class, mock_client_class):
        """Test that custom URL and collection name are used."""
        mock_config.return_value = (
            {"url": "http://localhost:6333", "collection_name": "default-collection"},
            {"model_name": "test-model", "vector_size": 384},
        )
        mock_embedding_instance = MagicMock()
        mock_embedding_instance.embed.return_value = [[0.1, 0.2, 0.3]]
        mock_embedding_class.return_value = mock_embedding_instance

        chunks = [
            {"content": "Test content", "metadata": {"repo_name": "test", "file_path": "test.md", "chunk_index": 0}}
        ]

        store_chunks_in_qdrant(chunks, qdrant_url="http://custom:6333", collection_name="custom-collection")

        mock_client_class.assert_called_once_with(url="http://custom:6333", api_key=None)

    @patch("hope_jarvis.ingestion.store.QdrantClient")
    @patch("hope_jarvis.ingestion.store.TextEmbedding")
    @patch("hope_jarvis.ingestion.store._get_qdrant_config")
    def test_batches_large_number_of_chunks(self, mock_config, mock_embedding_class, mock_client_class):
        """Test that large number of chunks are batched."""
        mock_config.return_value = (
            {"url": "http://localhost:6333", "collection_name": "test-collection"},
            {"model_name": "test-model", "vector_size": 384},
        )

        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        mock_embedding = MagicMock()
        mock_embedding.embed.return_value = [MagicMock()]
        mock_embedding_class.return_value = mock_embedding

        # Create 150 chunks (should be split into 2 batches of 100)
        chunks = [
            {
                "content": f"content {i}",
                "metadata": {
                    "repo_name": "HOPE",
                    "file_path": f"docs/test{i}.md",
                    "chunk_index": i,
                },
            }
            for i in range(150)
        ]

        store_chunks_in_qdrant(chunks)

        assert mock_client.upsert.call_count == 2

    @patch("hope_jarvis.ingestion.store.QdrantClient")
    @patch("hope_jarvis.ingestion.store.TextEmbedding")
    @patch("hope_jarvis.ingestion.store._get_qdrant_config")
    def test_generates_consistent_point_ids(self, mock_config, mock_embedding_class, mock_client_class):
        """Test that point IDs are generated consistently."""
        mock_config.return_value = (
            {"url": "http://localhost:6333", "collection_name": "test-collection"},
            {"model_name": "test-model", "vector_size": 384},
        )

        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        mock_embedding = MagicMock()
        mock_embedding.embed.return_value = [MagicMock()]
        mock_embedding_class.return_value = mock_embedding

        chunks = [
            {
                "content": "test content",
                "metadata": {
                    "repo_name": "HOPE",
                    "file_path": "docs/test.md",
                    "chunk_index": 0,
                },
            }
        ]

        store_chunks_in_qdrant(chunks)

        call_args = mock_client.upsert.call_args
        points = call_args[1]["points"]
        assert len(points) == 1
        assert points[0].id == abs(hash("HOPE_docs/test.md_0"))

    @patch("hope_jarvis.ingestion.store.QdrantClient")
    @patch("hope_jarvis.ingestion.store.TextEmbedding")
    @patch("hope_jarvis.ingestion.store._get_qdrant_config")
    def test_stores_payload_with_content_and_metadata(self, mock_config, mock_embedding_class, mock_client_class):
        """Test that payload contains content and metadata."""
        mock_config.return_value = (
            {"url": "http://localhost:6333", "collection_name": "test-collection"},
            {"model_name": "test-model", "vector_size": 384},
        )

        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        mock_embedding = MagicMock()
        mock_embedding.embed.return_value = [MagicMock()]
        mock_embedding_class.return_value = mock_embedding

        chunks = [
            {
                "content": "test content",
                "metadata": {
                    "repo_name": "HOPE",
                    "file_path": "docs/test.md",
                    "chunk_index": 0,
                },
            }
        ]

        store_chunks_in_qdrant(chunks)

        call_args = mock_client.upsert.call_args
        points = call_args[1]["points"]
        assert points[0].payload["content"] == "test content"
        assert points[0].payload["repo_name"] == "HOPE"
