import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@pytest.fixture
def mock_chainlit():
    """Mock chainlit module."""
    mock_cl = MagicMock()
    mock_cl.user_session = MagicMock()
    mock_msg = MagicMock()
    mock_msg.send = AsyncMock()
    mock_msg.stream_token = AsyncMock()
    mock_msg.update = AsyncMock()
    mock_cl.Message.return_value = mock_msg
    return mock_cl


class TestBuildConfig:
    """Test _build_config function."""

    @patch("hope_jarvis.app.get_ollama_base_url", return_value="http://localhost:11434")
    @patch("hope_jarvis.app.get_ollama_model", return_value="llama3")
    @patch("hope_jarvis.app.get_ollama_temperature", return_value=0.5)
    @patch("hope_jarvis.app.get_ollama_streaming", return_value=True)
    @patch("hope_jarvis.app.get_qdrant_url", return_value="http://localhost:6333")
    @patch("hope_jarvis.app.get_qdrant_collection_name", return_value="test-collection")
    @patch("hope_jarvis.app.get_retrieval_top_k", return_value=5)
    @patch("hope_jarvis.app.get_retrieval_score_threshold", return_value=0.5)
    @patch("hope_jarvis.app.get_ingestion_chunk_size", return_value=1000)
    @patch("hope_jarvis.app.get_ingestion_chunk_overlap", return_value=200)
    def test_builds_complete_config(self, *mocks):
        """Test that config contains all sections."""
        from hope_jarvis.app import _build_config

        config = _build_config()

        assert "ollama" in config
        assert config["ollama"]["base_url"] == "http://localhost:11434"
        assert config["ollama"]["model"] == "llama3"

        assert "qdrant" in config
        assert config["qdrant"]["url"] == "http://localhost:6333"

        assert "retrieval" in config
        assert config["retrieval"]["top_k"] == 5

        assert "ingestion" in config
        assert config["ingestion"]["chunk_size"] == 1000


class TestCheckEnv:
    """Test _check_env function."""

    def test_check_env_all_set(self):
        """Test _check_env with all vars set."""
        env_vars = {
            "OLLAMA_BASE_URL": "http://localhost:11434",
            "OLLAMA_MODEL": "llama3",
            "QDRANT_URL": "http://localhost:6333",
            "QDRANT_COLLECTION_NAME": "test",
            "EMBEDDING_MODEL_NAME": "test-model",
            "CONFIG_PATH": "/tmp",
            "DATA_PATH": "/tmp",
        }
        with patch.dict("os.environ", env_vars, clear=True):
            from hope_jarvis.app import _check_env

            _check_env()

    def test_check_env_missing_var(self):
        """Test _check_env with missing var raises error."""
        with patch.dict("os.environ", {}, clear=True):
            from hope_jarvis.app import _check_env

            try:
                _check_env()
                assert False, "Should have raised RuntimeError"
            except RuntimeError as e:
                assert "Missing env vars" in str(e)


class TestStart:
    """Test start function."""

    @pytest.mark.asyncio
    async def test_start_sets_config(self, mock_chainlit):
        """Test that start sets config and prompts in user session."""
        import hope_jarvis.app as app_module

        original_cl = app_module.cl
        app_module.cl = mock_chainlit

        try:
            with patch("hope_jarvis.app._check_env"):
                with patch(
                    "hope_jarvis.app._build_config", return_value={"test": "config"}
                ):
                    with patch(
                        "hope_jarvis.app.load_prompts", return_value={"persona": "test"}
                    ):
                        await app_module.start()

            mock_chainlit.user_session.set.assert_any_call("config", {"test": "config"})
            mock_chainlit.user_session.set.assert_any_call(
                "prompts", {"persona": "test"}
            )
        finally:
            app_module.cl = original_cl


class TestMain:
    """Test main message handler."""

    @pytest.mark.asyncio
    async def test_main_no_chunks(self, mock_chainlit):
        """Test main when no chunks are found."""
        import hope_jarvis.app as app_module

        original_cl = app_module.cl
        app_module.cl = mock_chainlit

        try:
            mock_chainlit.user_session.get.return_value = {
                "ollama": {
                    "base_url": "http://localhost:11434",
                    "model": "llama3",
                    "temperature": 0.5,
                    "streaming": True,
                },
                "qdrant": {"url": "http://localhost:6333", "collection_name": "test"},
                "retrieval": {"top_k": 5, "score_threshold": 0.5},
                "ingestion": {"chunk_size": 1000, "chunk_overlap": 200},
            }

            with patch("hope_jarvis.app.retrieve_relevant_chunks", return_value=[]):
                message = MagicMock()
                message.content = "test query"

                await app_module.main(message)

            mock_chainlit.Message.assert_called_with(
                content="Sorry, I cannot help you on this topic."
            )
        finally:
            app_module.cl = original_cl

    @pytest.mark.asyncio
    async def test_main_with_config_none(self, mock_chainlit):
        """Test main when config is None (builds config)."""
        import hope_jarvis.app as app_module

        original_cl = app_module.cl
        app_module.cl = mock_chainlit

        try:
            mock_chainlit.user_session.get.return_value = None
            mock_chainlit.user_session.set = MagicMock()

            with patch("hope_jarvis.app.retrieve_relevant_chunks", return_value=[]):
                with patch("hope_jarvis.app._check_env"):
                    with patch("hope_jarvis.app._build_config") as mock_build:
                        mock_build.return_value = {
                            "ollama": {
                                "base_url": "http://localhost:11434",
                                "model": "llama3",
                                "temperature": 0.5,
                                "streaming": True,
                            },
                            "qdrant": {
                                "url": "http://localhost:6333",
                                "collection_name": "test",
                            },
                            "retrieval": {"top_k": 5, "score_threshold": 0.5},
                            "ingestion": {"chunk_size": 1000, "chunk_overlap": 200},
                        }

                        message = MagicMock()
                        message.content = "test query"

                        await app_module.main(message)

                        mock_chainlit.user_session.set.assert_called()
        finally:
            app_module.cl = original_cl


class TestEnd:
    """Test end function."""

    def test_end_does_nothing(self):
        """Test that end function is a no-op."""
        from hope_jarvis.app import end

        end()


class TestRunIngestion:
    """Test run_ingestion function."""

    @pytest.mark.asyncio
    async def test_run_ingestion_no_changes(self, mock_chainlit):
        """Test run_ingestion when no files changed."""
        import hope_jarvis.app as app_module

        original_cl = app_module.cl
        app_module.cl = mock_chainlit

        try:
            mock_chainlit.user_session.get.return_value = {
                "qdrant": {"url": "http://localhost:6333", "collection_name": "test"},
            }

            with patch("hope_jarvis.app.sync_all_repos", return_value=[]):
                with patch(
                    "hope_jarvis.app.get_ingestion_chunk_size", return_value=1000
                ):
                    with patch(
                        "hope_jarvis.app.get_ingestion_chunk_overlap", return_value=200
                    ):
                        result = await app_module.run_ingestion()

                        assert result == "Nessun file aggiornato."
        finally:
            app_module.cl = original_cl

    @pytest.mark.asyncio
    async def test_run_ingestion_success(self, mock_chainlit):
        """Test successful run_ingestion."""
        import hope_jarvis.app as app_module

        original_cl = app_module.cl
        app_module.cl = mock_chainlit

        try:
            mock_chainlit.user_session.get.return_value = {
                "qdrant": {"url": "http://localhost:6333", "collection_name": "test"},
            }

            with patch("hope_jarvis.app.sync_all_repos") as mock_sync:
                mock_sync.return_value = [
                    {
                        "repo_name": "HOPE",
                        "file_path": "test.md",
                        "full_path": "/tmp/test.md",
                        "github_url": "https://github.com/test",
                        "rendered_base_url": "https://test.github.io",
                        "docs_dir": "docs",
                    }
                ]
                with patch("hope_jarvis.app.chunk_markdown_file") as mock_chunk:
                    mock_chunk.return_value = [
                        {"content": "chunk1", "metadata": {}},
                        {"content": "chunk2", "metadata": {}},
                    ]
                    with patch("hope_jarvis.app.store_chunks_in_qdrant") as mock_store:
                        with patch(
                            "hope_jarvis.app.get_ingestion_chunk_size",
                            return_value=1000,
                        ):
                            with patch(
                                "hope_jarvis.app.get_ingestion_chunk_overlap",
                                return_value=200,
                            ):
                                result = await app_module.run_ingestion()

                                assert "2 chunks da 1 file" in result
                                mock_store.assert_called_once()
        finally:
            app_module.cl = original_cl
