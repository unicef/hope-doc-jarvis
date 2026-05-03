import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from hope_jarvis.query import retrieve_relevant_chunks


@patch("hope_jarvis.query.retrieve.get_embedding_model_name", return_value="test-model")
@patch(
    "hope_jarvis.query.retrieve.get_qdrant_url", return_value="http://localhost:6333"
)
@patch("hope_jarvis.query.retrieve.get_qdrant_collection_name", return_value="test")
@patch("hope_jarvis.query.retrieve.get_retrieval_top_k", return_value=10)
@patch("hope_jarvis.query.retrieve.get_retrieval_score_threshold", return_value=None)
@patch("hope_jarvis.query.retrieve.QdrantClient")
@patch("hope_jarvis.query.retrieve.TextEmbedding")
def test_retrieve_chunks_success(
    mock_embedding,
    mock_qdrant,
    mock_threshold,
    mock_top_k,
    mock_collection,
    mock_url,
    mock_embedding_name,
):
    """Test successful chunk retrieval."""
    # Mock embedding
    mock_model = MagicMock()
    mock_model.embed.return_value = [[0.1] * 384]
    mock_embedding.return_value = mock_model

    # Mock Qdrant response
    mock_client = MagicMock()
    mock_qdrant.return_value = mock_client
    mock_client.query_points.return_value = MagicMock(
        points=[
            MagicMock(
                payload={
                    "content": "Test content",
                    "repo_name": "HOPE",
                    "rendered_html_url": "http://test.com",
                },
                score=0.8,
            )
        ]
    )

    result = retrieve_relevant_chunks(query="test query")

    assert len(result) == 1
    assert result[0]["content"] == "Test content"
    assert result[0]["metadata"]["repo_name"] == "HOPE"
    assert result[0]["metadata"]["score"] == 0.8


@patch("hope_jarvis.query.retrieve.get_embedding_model_name", return_value="test-model")
@patch(
    "hope_jarvis.query.retrieve.get_qdrant_url", return_value="http://localhost:6333"
)
@patch("hope_jarvis.query.retrieve.get_qdrant_collection_name", return_value="test")
@patch("hope_jarvis.query.retrieve.get_retrieval_top_k", return_value=10)
@patch("hope_jarvis.query.retrieve.get_retrieval_score_threshold", return_value=None)
@patch("hope_jarvis.query.retrieve.QdrantClient")
@patch("hope_jarvis.query.retrieve.TextEmbedding")
def test_retrieve_chunks_with_top_k(
    mock_embedding,
    mock_qdrant,
    mock_threshold,
    mock_top_k,
    mock_collection,
    mock_url,
    mock_embedding_name,
):
    """Test that top_k limits results."""
    mock_model = MagicMock()
    mock_model.embed.return_value = [[0.1] * 384]
    mock_embedding.return_value = mock_model

    mock_client = MagicMock()
    mock_qdrant.return_value = mock_client

    # Create mock points
    points = []
    for i in range(10):
        p = MagicMock()
        p.payload = {"content": f"Content {i}", "repo_name": "HOPE"}
        p.score = 0.9 - i * 0.01
        points.append(p)

    # Mock query_points to respect limit
    def mock_query(**kwargs):
        limit = kwargs.get("limit", 10)
        return MagicMock(points=points[:limit])

    mock_client.query_points.side_effect = mock_query

    result = retrieve_relevant_chunks(query="test", top_k=3)

    assert len(result) == 3
    # Check that query_points was called with limit=3
    call_kwargs = mock_client.query_points.call_args[1]
    assert call_kwargs["limit"] == 3
