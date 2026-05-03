import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from hope_jarvis import config


class TestConfig:
    """Test configuration functions."""

    def test_require_env_missing(self):
        """Test that missing env var raises error."""
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(
                EnvironmentError, match="Missing required env var: TEST_VAR"
            ):
                config._require_env("TEST_VAR")

    def test_require_env_present(self):
        """Test that present env var is returned."""
        with patch.dict("os.environ", {"TEST_VAR": "test_value"}):
            result = config._require_env("TEST_VAR")
            assert result == "test_value"

    def test_get_env_with_default(self):
        """Test getting optional env var with default."""
        with patch.dict("os.environ", {}, clear=True):
            result = config._get_env("TEST_VAR", "default")
            assert result == "default"

    def test_get_env_without_default(self):
        """Test getting optional env var without default."""
        with patch.dict("os.environ", {}, clear=True):
            result = config._get_env("TEST_VAR")
            assert result is None

    def test_get_ollama_base_url(self):
        """Test get_ollama_base_url."""
        with patch.dict("os.environ", {"OLLAMA_BASE_URL": "http://localhost:11434"}):
            assert config.get_ollama_base_url() == "http://localhost:11434"

    def test_get_ollama_model(self):
        """Test get_ollama_model."""
        with patch.dict("os.environ", {"OLLAMA_MODEL": "llama3"}):
            assert config.get_ollama_model() == "llama3"

    def test_get_ollama_temperature(self):
        """Test get_ollama_temperature with default."""
        with patch.dict("os.environ", {}, clear=True):
            assert config.get_ollama_temperature() == 0.1

    def test_get_ollama_temperature_custom(self):
        """Test get_ollama_temperature with custom value."""
        with patch.dict("os.environ", {"OLLAMA_TEMPERATURE": "0.5"}):
            assert config.get_ollama_temperature() == 0.5

    def test_get_ollama_streaming(self):
        """Test get_ollama_streaming with default."""
        with patch.dict("os.environ", {}, clear=True):
            assert config.get_ollama_streaming() is True

    def test_get_ollama_streaming_false(self):
        """Test get_ollama_streaming with false value."""
        with patch.dict("os.environ", {"OLLAMA_STREAMING": "false"}):
            assert config.get_ollama_streaming() is False

    def test_get_qdrant_url(self):
        """Test get_qdrant_url."""
        with patch.dict("os.environ", {"QDRANT_URL": "http://localhost:6333"}):
            assert config.get_qdrant_url() == "http://localhost:6333"

    def test_get_qdrant_collection_name(self):
        """Test get_qdrant_collection_name."""
        with patch.dict("os.environ", {"QDRANT_COLLECTION_NAME": "test-collection"}):
            assert config.get_qdrant_collection_name() == "test-collection"

    def test_get_embedding_model_name(self):
        """Test get_embedding_model_name."""
        with patch.dict("os.environ", {"EMBEDDING_MODEL_NAME": "test-model"}):
            assert config.get_embedding_model_name() == "test-model"

    def test_get_embedding_vector_size_default(self):
        """Test get_embedding_vector_size with default."""
        with patch.dict("os.environ", {}, clear=True):
            assert config.get_embedding_vector_size() == 384

    def test_get_embedding_vector_size_custom(self):
        """Test get_embedding_vector_size with custom value."""
        with patch.dict("os.environ", {"EMBEDDING_VECTOR_SIZE": "768"}):
            assert config.get_embedding_vector_size() == 768

    def test_get_retrieval_top_k_default(self):
        """Test get_retrieval_top_k with default."""
        with patch.dict("os.environ", {}, clear=True):
            assert config.get_retrieval_top_k() == 5

    def test_get_retrieval_top_k_custom(self):
        """Test get_retrieval_top_k with custom value."""
        with patch.dict("os.environ", {"RETRIEVAL_TOP_K": "10"}):
            assert config.get_retrieval_top_k() == 10

    def test_get_retrieval_score_threshold_default(self):
        """Test get_retrieval_score_threshold with default."""
        with patch.dict("os.environ", {}, clear=True):
            assert config.get_retrieval_score_threshold() == 0.5

    def test_get_retrieval_score_threshold_custom(self):
        """Test get_retrieval_score_threshold with custom value."""
        with patch.dict("os.environ", {"RETRIEVAL_SCORE_THRESHOLD": "0.8"}):
            assert config.get_retrieval_score_threshold() == 0.8

    def test_get_ingestion_chunk_size_default(self):
        """Test get_ingestion_chunk_size with default."""
        with patch.dict("os.environ", {}, clear=True):
            assert config.get_ingestion_chunk_size() == 1000

    def test_get_ingestion_chunk_size_custom(self):
        """Test get_ingestion_chunk_size with custom value."""
        with patch.dict("os.environ", {"INGESTION_CHUNK_SIZE": "2000"}):
            assert config.get_ingestion_chunk_size() == 2000

    def test_get_ingestion_chunk_overlap_default(self):
        """Test get_ingestion_chunk_overlap with default."""
        with patch.dict("os.environ", {}, clear=True):
            assert config.get_ingestion_chunk_overlap() == 200

    def test_get_ingestion_chunk_overlap_custom(self):
        """Test get_ingestion_chunk_overlap with custom value."""
        with patch.dict("os.environ", {"INGESTION_CHUNK_OVERLAP": "300"}):
            assert config.get_ingestion_chunk_overlap() == 300

    def test_get_config_path(self):
        """Test get_config_path."""
        with patch.dict("os.environ", {"CONFIG_PATH": "/tmp/config"}):
            assert config.get_config_path() == Path("/tmp/config")

    def test_get_repos_config(self):
        """Test get_repos_config."""
        with patch.dict("os.environ", {"CONFIG_PATH": "/tmp/config"}):
            assert config.get_repos_config() == Path("/tmp/config/repos.yaml")

    def test_get_sync_state_path(self):
        """Test get_sync_state_path."""
        with patch.dict("os.environ", {"CONFIG_PATH": "/tmp/config"}):
            assert config.get_sync_state_path() == Path("/tmp/config/sync_state.json")

    def test_get_data_path(self):
        """Test get_data_path."""
        with patch.dict("os.environ", {"DATA_PATH": "/tmp/data"}):
            assert config.get_data_path() == Path("/tmp/data")
