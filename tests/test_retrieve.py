import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from hope_jarvis.query import retrieve_relevant_chunks


class TestRetrieveRelevantChunks:
    """Additional tests for retrieve_relevant_chunks."""

    @patch("hope_jarvis.query.retrieve.get_embedding_model_name", return_value="test-model")
    @patch(
        "hope_jarvis.query.retrieve.get_qdrant_url",
        return_value="http://localhost:6333",
    )
    @patch("hope_jarvis.query.retrieve.get_qdrant_collection_name", return_value="test")
    @patch("hope_jarvis.query.retrieve.get_retrieval_top_k", return_value=10)
    @patch("hope_jarvis.query.retrieve.get_retrieval_score_threshold", return_value=0.5)
    @patch("hope_jarvis.query.retrieve.QdrantClient")
    @patch("hope_jarvis.query.retrieve.TextEmbedding")
    def test_filters_by_score_threshold(
        self,
        mock_embedding,
        mock_qdrant,
        mock_threshold,
        mock_top_k,
        mock_collection,
        mock_url,
        mock_embedding_name,
    ):
        """Test that chunks below threshold are filtered."""
        mock_model = MagicMock()
        mock_model.embed.return_value = [[0.1] * 384]
        mock_embedding.return_value = mock_model

        mock_client = MagicMock()
        mock_qdrant.return_value = mock_client

        high_score = MagicMock()
        high_score.payload = {
            "content": "High score",
            "repo_name": "HOPE",
            "rendered_html_url": "http://test.com",
        }
        high_score.score = 0.8

        low_score = MagicMock()
        low_score.payload = {
            "content": "Low score",
            "repo_name": "HOPE",
            "rendered_html_url": "http://test.com",
        }
        low_score.score = 0.3

        mock_client.query_points.return_value = MagicMock(points=[high_score, low_score])

        result = retrieve_relevant_chunks(query="test", score_threshold=0.5)

        assert len(result) == 1
        assert result[0]["content"] == "High score"

    @patch("hope_jarvis.query.retrieve.get_embedding_model_name", return_value="test-model")
    @patch(
        "hope_jarvis.query.retrieve.get_qdrant_url",
        return_value="http://localhost:6333",
    )
    @patch("hope_jarvis.query.retrieve.get_qdrant_collection_name", return_value="test")
    @patch("hope_jarvis.query.retrieve.get_retrieval_top_k", return_value=10)
    @patch("hope_jarvis.query.retrieve.get_retrieval_score_threshold", return_value=0.5)
    @patch("hope_jarvis.query.retrieve.QdrantClient")
    @patch("hope_jarvis.query.retrieve.TextEmbedding")
    def test_returns_empty_when_no_results(
        self,
        mock_embedding,
        mock_qdrant,
        mock_threshold,
        mock_top_k,
        mock_collection,
        mock_url,
        mock_embedding_name,
    ):
        """Test that empty list is returned when no results."""
        mock_model = MagicMock()
        mock_model.embed.return_value = [[0.1] * 384]
        mock_embedding.return_value = mock_model

        mock_client = MagicMock()
        mock_qdrant.return_value = mock_client
        mock_client.query_points.return_value = MagicMock(points=[])

        result = retrieve_relevant_chunks(query="test")

        assert result == []

    @patch("hope_jarvis.query.retrieve.get_embedding_model_name", return_value="test-model")
    @patch(
        "hope_jarvis.query.retrieve.get_qdrant_url",
        return_value="http://localhost:6333",
    )
    @patch("hope_jarvis.query.retrieve.get_qdrant_collection_name", return_value="test")
    @patch("hope_jarvis.query.retrieve.get_retrieval_top_k", return_value=10)
    @patch("hope_jarvis.query.retrieve.get_retrieval_score_threshold", return_value=0.5)
    @patch("hope_jarvis.query.retrieve.QdrantClient")
    @patch("hope_jarvis.query.retrieve.TextEmbedding")
    def test_metadata_contains_all_fields(
        self,
        mock_embedding,
        mock_qdrant,
        mock_threshold,
        mock_top_k,
        mock_collection,
        mock_url,
        mock_embedding_name,
    ):
        """Test that metadata contains all expected fields."""
        mock_model = MagicMock()
        mock_model.embed.return_value = [[0.1] * 384]
        mock_embedding.return_value = mock_model

        mock_client = MagicMock()
        mock_qdrant.return_value = mock_client

        mock_point = MagicMock()
        mock_point.payload = {
            "content": "Test content",
            "repo_name": "HOPE",
            "file_path": "docs/test.md",
            "raw_github_url": "http://github.com/test",
            "rendered_html_url": "http://test.com",
            "headers": {"header_1": "Title"},
        }
        mock_point.score = 0.8

        mock_client.query_points.return_value = MagicMock(points=[mock_point])

        result = retrieve_relevant_chunks(query="test")

        assert len(result) == 1
        metadata = result[0]["metadata"]
        assert metadata["repo_name"] == "HOPE"
        assert metadata["file_path"] == "docs/test.md"
        assert metadata["raw_github_url"] == "http://github.com/test"
        assert metadata["rendered_html_url"] == "http://test.com"
        assert metadata["headers"] == {"header_1": "Title"}
        assert metadata["score"] == 0.8

    @patch("hope_jarvis.query.retrieve.get_embedding_model_name", return_value="test-model")
    @patch(
        "hope_jarvis.query.retrieve.get_qdrant_url",
        return_value="http://localhost:6333",
    )
    @patch("hope_jarvis.query.retrieve.get_qdrant_collection_name", return_value="test")
    @patch("hope_jarvis.query.retrieve.get_retrieval_top_k", return_value=10)
    @patch("hope_jarvis.query.retrieve.get_retrieval_score_threshold", return_value=0.5)
    @patch("hope_jarvis.query.retrieve.QdrantClient")
    @patch("hope_jarvis.query.retrieve.TextEmbedding")
    def test_handles_missing_payload_fields(
        self,
        mock_embedding,
        mock_qdrant,
        mock_threshold,
        mock_top_k,
        mock_collection,
        mock_url,
        mock_embedding_name,
    ):
        """Test that missing payload fields are handled gracefully."""
        mock_model = MagicMock()
        mock_model.embed.return_value = [[0.1] * 384]
        mock_embedding.return_value = mock_model

        mock_client = MagicMock()
        mock_qdrant.return_value = mock_client

        mock_point = MagicMock()
        mock_point.payload = {"content": "Test content"}
        mock_point.score = 0.8

        mock_client.query_points.return_value = MagicMock(points=[mock_point])

        result = retrieve_relevant_chunks(query="test")

        assert len(result) == 1
        assert result[0]["content"] == "Test content"
        assert result[0]["metadata"]["repo_name"] is None

    @patch("hope_jarvis.query.retrieve.get_embedding_model_name", return_value="test-model")
    @patch(
        "hope_jarvis.query.retrieve.get_qdrant_url",
        return_value="http://localhost:6333",
    )
    @patch("hope_jarvis.query.retrieve.get_qdrant_collection_name", return_value="test")
    @patch("hope_jarvis.query.retrieve.get_retrieval_top_k", return_value=10)
    @patch("hope_jarvis.query.retrieve.get_retrieval_score_threshold", return_value=0.5)
    @patch("hope_jarvis.query.retrieve.QdrantClient")
    @patch("hope_jarvis.query.retrieve.TextEmbedding")
    def test_uses_provided_params(
        self,
        mock_embedding,
        mock_qdrant,
        mock_threshold,
        mock_top_k,
        mock_collection,
        mock_url,
        mock_embedding_name,
    ):
        """Test that provided params are used instead of defaults."""
        mock_model = MagicMock()
        mock_model.embed.return_value = [[0.1] * 384]
        mock_embedding.return_value = mock_model

        mock_client = MagicMock()
        mock_qdrant.return_value = mock_client
        mock_client.query_points.return_value = MagicMock(points=[])

        retrieve_relevant_chunks(
            query="test",
            qdrant_url="http://custom:6333",
            collection_name="custom-collection",
            top_k=3,
            score_threshold=0.7,
        )

        mock_client.query_points.assert_called_once()
        call_kwargs = mock_client.query_points.call_args[1]
        assert call_kwargs["collection_name"] == "custom-collection"
        assert call_kwargs["limit"] == 3
        assert call_kwargs["score_threshold"] == 0.7
