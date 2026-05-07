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
        with patch.dict("os.environ", {"OLLAMA_HOST": "localhost", "OLLAMA_PORT": "11434"}):
            assert config.get_ollama_base_url() == "http://localhost:11434"

    def test_get_ollama_base_url_default_port(self):
        """Test get_ollama_base_url with default port."""
        with patch.dict("os.environ", {"OLLAMA_HOST": "localhost"}):
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
        with patch.dict("os.environ", {"QDRANT_HOST": "localhost"}):
            assert config.get_qdrant_url() == "http://localhost:6333"

    def test_get_qdrant_url_grpc(self):
        """Test get_qdrant_url with gRPC protocol."""
        with patch.dict("os.environ", {"QDRANT_HOST": "localhost", "QDRANT_PROTOCOL": "grpc"}):
            assert config.get_qdrant_url() == "grpc://localhost:6334"

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

    def test_get_data_path_default(self):
        """Test get_data_path returns default when DATA_DIR not set."""
        with patch.dict("os.environ", {"CONFIG_PATH": "/tmp"}, clear=True):
            result = config.get_data_path()
            assert result == Path("/data")

    def test_get_repos_root_path(self):
        """Test get_repos_root_path."""
        with patch.dict("os.environ", {"DATA_DIR": "/tmp/data"}):
            assert config.get_repos_root_path() == Path("/tmp/data/repos")

    def test_get_knowledge_path(self):
        """Test get_knowledge_path."""
        with patch.dict("os.environ", {"DATA_DIR": "/tmp/data"}):
            assert config.get_knowledge_path() == Path("/tmp/data/knowledge")

    def test_get_qdrant_protocol_default(self):
        """Test get_qdrant_protocol returns http by default."""
        with patch.dict("os.environ", {}, clear=True):
            assert config.get_qdrant_protocol() == "http"

    def test_get_qdrant_protocol_grpc(self):
        """Test get_qdrant_protocol returns grpc when set."""
        with patch.dict("os.environ", {"QDRANT_PROTOCOL": "grpc"}):
            assert config.get_qdrant_protocol() == "grpc"

    def test_get_qdrant_port_http(self):
        """Test get_qdrant_port returns HTTP port by default."""
        with patch.dict("os.environ", {}, clear=True):
            assert config.get_qdrant_port() == 6333

    def test_get_qdrant_port_grpc(self):
        """Test get_qdrant_port returns gRPC port when protocol is grpc."""
        with patch.dict("os.environ", {"QDRANT_PROTOCOL": "grpc"}):
            assert config.get_qdrant_port() == 6334

    def test_get_qdrant_port_grpc_custom(self):
        """Test get_qdrant_port with custom gRPC port."""
        with patch.dict("os.environ", {"QDRANT_PROTOCOL": "grpc", "QDRANT_GRPC_PORT": "9999"}):
            assert config.get_qdrant_port() == 9999

    def test_get_qdrant_port_http_custom(self):
        """Test get_qdrant_port with custom HTTP port."""
        with patch.dict("os.environ", {"QDRANT_PROTOCOL": "http", "QDRANT_HTTP_PORT": "9999"}):
            assert config.get_qdrant_port() == 9999

    def test_get_qdrant_api_key_empty(self):
        """Test get_qdrant_api_key returns None for empty string."""
        with patch.dict("os.environ", {"QDRANT_API_KEY": ""}):
            assert config.get_qdrant_api_key() is None

    def test_get_qdrant_api_key_set(self):
        """Test get_qdrant_api_key returns value when set."""
        with patch.dict("os.environ", {"QDRANT_API_KEY": "secret-key"}):
            assert config.get_qdrant_api_key() == "secret-key"

    def test_get_hf_cache_path_hf_home(self):
        """Test get_hf_cache_path with HF_HOME set."""
        with patch.dict("os.environ", {"HF_HOME": "/custom/hf"}):
            assert config.get_hf_cache_path() == Path("/custom/hf")

    def test_get_hf_cache_path_hf_hub_cache(self):
        """Test get_hf_cache_path with HF_HUB_CACHE set."""
        with patch.dict("os.environ", {"HF_HUB_CACHE": "/custom/cache"}):
            assert config.get_hf_cache_path() == Path("/custom/cache")

    def test_get_hf_cache_path_default(self):
        """Test get_hf_cache_path returns default."""
        from pathlib import Path as StdPath

        with patch.dict("os.environ", {}, clear=True):
            result = config.get_hf_cache_path()
            expected = StdPath.home() / ".cache" / "huggingface"
            assert result == expected

    def test_get_repos_config_raw(self, tmp_path):
        """Test get_repos_config_raw."""
        repos_file = tmp_path / "repos.yaml"
        repos_file.write_text("repos:\n  - name: test\n")

        with patch.dict("os.environ", {"CONFIG_PATH": str(tmp_path)}):
            result = config.get_repos_config_raw()
            assert result == {"repos": [{"name": "test"}]}

    def test_get_all_repo_names(self, tmp_path):
        """Test get_all_repo_names."""
        repos_file = tmp_path / "repos.yaml"
        repos_file.write_text("repos:\n  - name: repo1\n  - name: repo2\n")

        with patch.dict("os.environ", {"CONFIG_PATH": str(tmp_path)}):
            result = config.get_all_repo_names()
            assert result == ["repo1", "repo2"]

    def test_get_all_repos(self, tmp_path):
        """Test get_all_repos yields repos."""
        repos_file = tmp_path / "repos.yaml"
        repos_file.write_text("repos:\n  - name: test\n    github_url: https://github.com/test\n")

        with patch.dict("os.environ", {"CONFIG_PATH": str(tmp_path)}):
            repos = list(config.get_all_repos())
            assert len(repos) == 1
            assert repos[0]["name"] == "test"
