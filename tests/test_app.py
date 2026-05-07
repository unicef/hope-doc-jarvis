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


class TestLoadPrompts:
    """Test load_prompts function."""

    def test_load_prompts_directory_exists(self, tmp_path):
        """Test loading prompts when directory exists."""
        from hope_jarvis.app import load_prompts

        # Create test prompt files
        prompt_dir = tmp_path / "prompts"
        prompt_dir.mkdir()
        (prompt_dir / "persona.md").write_text("I'm Jarvis")
        (prompt_dir / "other.md").write_text("Other prompt")

        # Patch PROMPTS_DIR
        with patch("hope_jarvis.app.PROMPTS_DIR", prompt_dir):
            prompts = load_prompts()
            assert "persona" in prompts
            assert "other" in prompts

    def test_load_prompts_directory_missing(self, tmp_path):
        """Test loading prompts when directory doesn't exist."""
        from hope_jarvis.app import load_prompts

        non_existent = tmp_path / "non_existent"
        with patch("hope_jarvis.app.PROMPTS_DIR", non_existent):
            prompts = load_prompts()
            assert prompts == {}


class TestIdentityCheck:
    """Test identity question detection."""

    def test_is_identity_question_italian(self):
        """Test Italian identity questions."""
        from hope_jarvis.app import is_identity_question

        assert is_identity_question("chi sei?")
        assert is_identity_question("Chi sei?")
        assert is_identity_question("cos'è jarvis?")
        assert is_identity_question("che cosa sei?")

    def test_is_identity_question_english(self):
        """Test English identity questions."""
        from hope_jarvis.app import is_identity_question

        assert is_identity_question("who are you?")
        assert is_identity_question("What are you?")
        assert is_identity_question("tell me about jarvis")
        assert is_identity_question("tell me about yourself")

    def test_is_identity_question_negative(self):
        """Test non-identity questions."""
        from hope_jarvis.app import is_identity_question

        assert not is_identity_question("How to install?")
        assert not is_identity_question("What is HOPE?")

    def test_get_identity_response_with_persona(self, tmp_path):
        """Test identity response with persona.md."""
        from hope_jarvis.app import get_identity_response

        # Create persona file
        prompt_dir = tmp_path / "prompts"
        prompt_dir.mkdir()
        persona_content = "> I'm Jarvis, your assistant"
        (prompt_dir / "persona.md").write_text(persona_content)

        with patch("hope_jarvis.app.PROMPTS_DIR", prompt_dir):
            response = get_identity_response()
            assert "I'm Jarvis" in response

    def test_get_identity_response_fallback(self):
        """Test identity response fallback."""
        from hope_jarvis.app import get_identity_response

        with patch("hope_jarvis.app.load_prompts", return_value={}):
            response = get_identity_response()
            assert "Jarvis" in response


class TestSentryInit:
    """Test Sentry initialization."""

    def test_sentry_init_with_dsn(self):
        """Test Sentry init when DSN is set."""
        with patch.dict("os.environ", {"SENTRY_DSN": "https://test@sentry.io/123", "ENVIRONMENT": "test"}):
            with patch("sentry_sdk.init") as mock_init:
                import importlib

                import hope_jarvis.app

                importlib.reload(hope_jarvis.app)

                mock_init.assert_called_once_with(
                    dsn="https://test@sentry.io/123",
                    environment="test",
                    send_default_pii=False,
                )

    def test_sentry_not_init_without_dsn(self):
        """Test Sentry not init when DSN not set."""
        with patch.dict("os.environ", {}, clear=True):
            with patch("sentry_sdk.init") as mock_init:
                import importlib

                import hope_jarvis.app

                importlib.reload(hope_jarvis.app)

                mock_init.assert_not_called()


class TestCheckEnv:
    """Test _check_env function."""

    def test_check_env_all_set(self):
        """Test _check_env with all vars set."""
        env_vars = {
            "OLLAMA_HOST": "localhost",
            "OLLAMA_MODEL": "llama3",
            "QDRANT_HOST": "localhost",
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


class TestMainIdentityQuestion:
    """Test main message handler for identity questions."""

    @pytest.mark.asyncio
    async def test_main_identity_question(self, mock_chainlit):
        """Test main when question is about identity."""
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

            with patch("hope_jarvis.app.get_identity_response", return_value="I'm Jarvis"):
                message = MagicMock()
                message.content = "chi sei?"

                await app_module.main(message)

            mock_chainlit.Message.assert_called_with(content="I'm Jarvis")
        finally:
            app_module.cl = original_cl


class TestMainWithChunks:
    """Test main message handler with retrieved chunks."""

    @pytest.mark.asyncio
    async def test_main_with_chunks_and_streaming(self, mock_chainlit):
        """Test main when chunks are found and LLM streams response."""
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

            mock_chunks = [
                {
                    "content": "Test content from HOPE",
                    "metadata": {
                        "repo_name": "HOPE",
                        "rendered_html_url": "https://hope.example.com/docs",
                        "score": 0.85,
                    },
                }
            ]

            async def mock_astream(_):
                for token in ["Hello", " ", "from", " ", "Jarvis"]:
                    yield token

            mock_llm = MagicMock()
            mock_parser = MagicMock()

            mock_chain_instance = MagicMock()
            mock_chain_instance.astream = mock_astream

            mock_pipe1 = MagicMock()
            mock_pipe1.__or__ = MagicMock(return_value=mock_chain_instance)

            mock_prompt_template = MagicMock()
            mock_prompt_template.from_messages.return_value = mock_pipe1

            with (
                patch("hope_jarvis.app.is_identity_question", return_value=False),
                patch("hope_jarvis.app.retrieve_relevant_chunks", return_value=mock_chunks),
                patch("hope_jarvis.app.load_prompts", return_value={}),
                patch("hope_jarvis.app.get_all_repo_names", return_value=["HOPE"]),
                patch("langchain_core.prompts.ChatPromptTemplate", mock_prompt_template),
                patch("langchain_ollama.ChatOllama", return_value=mock_llm),
                patch("langchain_core.output_parsers.StrOutputParser", return_value=mock_parser),
                patch("hope_jarvis.app.logger"),
            ):
                message = MagicMock()
                message.content = "How does HOPE work?"

                await app_module.main(message)

            mock_chainlit.Message.assert_called()
            mock_chainlit.user_session.set.assert_called()
        finally:
            app_module.cl = original_cl

    @pytest.mark.asyncio
    async def test_main_with_multiple_sources_dedup(self, mock_chainlit):
        """Test main deduplicates sources from multiple chunks."""
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

            mock_chunks = [
                {
                    "content": "Content 1",
                    "metadata": {
                        "repo_name": "HOPE",
                        "rendered_html_url": "https://hope.example.com/docs",
                        "score": 0.85,
                    },
                },
                {
                    "content": "Content 2",
                    "metadata": {
                        "repo_name": "HOPE",
                        "rendered_html_url": "https://hope.example.com/docs",
                        "score": 0.82,
                    },
                },
            ]

            async def mock_astream(_):
                yield "Response"

            mock_llm = MagicMock()
            mock_parser = MagicMock()
            mock_chain_instance = MagicMock()
            mock_chain_instance.astream = mock_astream
            mock_pipe1 = MagicMock()
            mock_pipe1.__or__ = MagicMock(return_value=mock_chain_instance)
            mock_prompt_template = MagicMock()
            mock_prompt_template.from_messages.return_value = mock_pipe1

            with (
                patch("hope_jarvis.app.is_identity_question", return_value=False),
                patch("hope_jarvis.app.retrieve_relevant_chunks", return_value=mock_chunks),
                patch("hope_jarvis.app.load_prompts", return_value={}),
                patch("hope_jarvis.app.get_all_repo_names", return_value=["HOPE"]),
                patch("langchain_core.prompts.ChatPromptTemplate", mock_prompt_template),
                patch("langchain_ollama.ChatOllama", return_value=mock_llm),
                patch("langchain_core.output_parsers.StrOutputParser", return_value=mock_parser),
                patch("hope_jarvis.app.logger"),
            ):
                message = MagicMock()
                message.content = "Question about HOPE"

                await app_module.main(message)
        finally:
            app_module.cl = original_cl


class TestMainErrorHandling:
    """Test main message handler error handling."""

    @pytest.mark.asyncio
    async def test_main_connection_error(self, mock_chainlit):
        """Test main when connection error occurs."""
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

            with patch("hope_jarvis.app.retrieve_relevant_chunks") as mock_retrieve:
                mock_retrieve.side_effect = ConnectionError("Connection refused")

                with patch("hope_jarvis.app.sentry_sdk.capture_exception"):
                    message = MagicMock()
                    message.content = "test query"

                    await app_module.main(message)

            assert mock_chainlit.Message.call_count >= 1
            message_calls = [c.kwargs.get("content", "") for c in mock_chainlit.Message.call_args_list]
            assert any("Unable to connect" in c for c in message_calls)
        finally:
            app_module.cl = original_cl

    @pytest.mark.asyncio
    async def test_main_generic_error(self, mock_chainlit):
        """Test main when generic error occurs."""
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

            with patch("hope_jarvis.app.retrieve_relevant_chunks") as mock_retrieve:
                mock_retrieve.side_effect = ValueError("Some unexpected error")

                with patch("hope_jarvis.app.sentry_sdk.capture_exception"):
                    message = MagicMock()
                    message.content = "test query"

                    await app_module.main(message)

            assert mock_chainlit.Message.call_count >= 1
            message_calls = [c.kwargs.get("content", "") for c in mock_chainlit.Message.call_args_list]
            assert any("unexpected error" in c for c in message_calls)
        finally:
            app_module.cl = original_cl


class TestActionCallbacks:
    """Test action callback handlers."""

    @pytest.mark.asyncio
    async def test_on_satisfied_with_qa(self, mock_chainlit):
        """Test on_satisfied when Q&A is available."""
        import hope_jarvis.app as app_module

        original_cl = app_module.cl
        app_module.cl = mock_chainlit

        try:
            mock_chainlit.user_session.get.side_effect = lambda key, default=None: {
                "last_question": "What is HOPE?",
                "last_answer": "HOPE is a platform.",
                "last_sources": [{"app": "HOPE", "url": "https://example.com", "score": 0.85}],
            }.get(key, default)

            with patch("hope_jarvis.knowledge.save_qa_to_markdown") as mock_save:
                action = MagicMock()
                action.remove = AsyncMock()

                await app_module.on_satisfied(action)

            mock_save.assert_called_once()
            action.remove.assert_called_once()
        finally:
            app_module.cl = original_cl

    @pytest.mark.asyncio
    async def test_on_satisfied_save_error(self, mock_chainlit):
        """Test on_satisfied when save fails."""
        import hope_jarvis.app as app_module

        original_cl = app_module.cl
        app_module.cl = mock_chainlit

        try:
            mock_chainlit.user_session.get.side_effect = lambda key, default=None: {
                "last_question": "What is HOPE?",
                "last_answer": "HOPE is a platform.",
                "last_sources": [],
            }.get(key, default)

            with patch("hope_jarvis.knowledge.save_qa_to_markdown", side_effect=Exception("Save failed")):
                with patch("hope_jarvis.app.logger"):
                    action = MagicMock()
                    action.remove = AsyncMock()

                    await app_module.on_satisfied(action)

            action.remove.assert_called_once()
        finally:
            app_module.cl = original_cl

    @pytest.mark.asyncio
    async def test_on_satisfied_no_qa(self, mock_chainlit):
        """Test on_satisfied when no Q&A is available."""
        import hope_jarvis.app as app_module

        original_cl = app_module.cl
        app_module.cl = mock_chainlit

        try:
            mock_chainlit.user_session.get.side_effect = lambda key, default=None: {
                "last_question": "",
                "last_answer": "",
                "last_sources": [],
            }.get(key, default)

            action = MagicMock()
            action.remove = AsyncMock()

            await app_module.on_satisfied(action)

            action.remove.assert_called_once()
        finally:
            app_module.cl = original_cl

    @pytest.mark.asyncio
    async def test_on_not_satisfied(self, mock_chainlit):
        """Test on_not_satisfied callback."""
        import hope_jarvis.app as app_module

        original_cl = app_module.cl
        app_module.cl = mock_chainlit

        try:
            action = MagicMock()
            action.remove = AsyncMock()

            await app_module.on_not_satisfied(action)

            mock_chainlit.Message.assert_called_with(content="Mi dispiace. Come posso aiutarti meglio?")
            action.remove.assert_called_once()
        finally:
            app_module.cl = original_cl
