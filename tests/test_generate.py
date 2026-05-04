import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from hope_jarvis.query.generate import (
    _build_ollama_config,
    create_llm_chain,
    generate_response,
    generate_response_stream,
)


class TestBuildOllamaConfig:
    """Test _build_ollama_config function."""

    @patch(
        "hope_jarvis.query.generate.get_ollama_base_url",
        return_value="http://localhost:11434",
    )
    @patch("hope_jarvis.query.generate.get_ollama_model", return_value="llama3")
    @patch("hope_jarvis.query.generate.get_ollama_temperature", return_value=0.5)
    @patch("hope_jarvis.query.generate.get_ollama_streaming", return_value=True)
    def test_builds_config_correctly(self, mock_streaming, mock_temp, mock_model, mock_url):
        """Test that config is built correctly."""
        config = _build_ollama_config()

        assert config["base_url"] == "http://localhost:11434"
        assert config["model"] == "llama3"
        assert config["temperature"] == 0.5
        assert config["streaming"] is True


class TestCreateLlmChain:
    """Test create_llm_chain function."""

    def test_creates_chain(self):
        """Test that LLM chain is created."""
        config = {
            "ollama": {
                "base_url": "http://localhost:11434",
                "model": "llama3",
                "temperature": 0.5,
                "streaming": True,
            }
        }

        chain = create_llm_chain(config)

        assert chain is not None


class TestGenerateResponse:
    """Test generate_response function."""

    @patch("hope_jarvis.query.generate.create_llm_chain")
    def test_generates_response(self, mock_chain_creator):
        """Test generating a response."""
        mock_chain = MagicMock()
        mock_chain.invoke.return_value = "Test response"
        mock_chain_creator.return_value = mock_chain

        chunks = [
            {
                "content": "Test content",
                "metadata": {"rendered_html_url": "http://test.com"},
            }
        ]

        config = {
            "ollama": {
                "base_url": "http://localhost:11434",
                "model": "llama3",
                "temperature": 0.5,
                "streaming": True,
            }
        }

        result = generate_response("test query", chunks, config)

        assert result == "Test response"
        mock_chain.invoke.assert_called_once()

    @patch("hope_jarvis.query.generate.create_llm_chain")
    @patch("hope_jarvis.query.generate._build_ollama_config")
    def test_generates_response_without_config(self, mock_build_config, mock_chain_creator):
        """Test generating a response without config (uses defaults)."""
        mock_build_config.return_value = {
            "base_url": "http://localhost:11434",
            "model": "llama3",
            "temperature": 0.1,
            "streaming": True,
        }

        mock_chain = MagicMock()
        mock_chain.invoke.return_value = "Default response"
        mock_chain_creator.return_value = mock_chain

        chunks = [
            {
                "content": "Test content",
                "metadata": {"rendered_html_url": "http://test.com"},
            }
        ]

        result = generate_response("test query", chunks)

        assert result == "Default response"

    @patch("hope_jarvis.query.generate.create_llm_chain")
    def test_prepares_context_from_multiple_chunks(self, mock_chain_creator):
        """Test that context is prepared from multiple chunks."""
        mock_chain = MagicMock()
        mock_chain.invoke.return_value = "Response"
        mock_chain_creator.return_value = mock_chain

        chunks = [
            {
                "content": "Content 1",
                "metadata": {"rendered_html_url": "http://test1.com"},
            },
            {
                "content": "Content 2",
                "metadata": {"rendered_html_url": "http://test2.com"},
            },
        ]

        config = {
            "ollama": {
                "base_url": "http://localhost:11434",
                "model": "llama3",
                "temperature": 0.5,
                "streaming": True,
            }
        }

        generate_response("test query", chunks, config)

        call_args = mock_chain.invoke.call_args[0][0]
        assert "Content 1" in call_args["context"]
        assert "Content 2" in call_args["context"]
        assert "---" in call_args["context"]


class TestGenerateResponseStream:
    """Test generate_response_stream function."""

    @patch("hope_jarvis.query.generate.create_llm_chain")
    def test_streams_response(self, mock_chain_creator):
        """Test streaming a response."""
        mock_chain = MagicMock()
        mock_chain.stream.return_value = iter(["Hello ", "World"])
        mock_chain_creator.return_value = mock_chain

        chunks = [
            {
                "content": "Test content",
                "metadata": {"rendered_html_url": "http://test.com"},
            }
        ]

        config = {
            "ollama": {
                "base_url": "http://localhost:11434",
                "model": "llama3",
                "temperature": 0.5,
                "streaming": True,
            }
        }

        result = list(generate_response_stream("test query", chunks, config))

        assert result == ["Hello ", "World"]

    @patch("hope_jarvis.query.generate.create_llm_chain")
    @patch("hope_jarvis.query.generate._build_ollama_config")
    def test_streams_without_config(self, mock_build_config, mock_chain_creator):
        """Test streaming a response without config."""
        mock_build_config.return_value = {
            "base_url": "http://localhost:11434",
            "model": "llama3",
            "temperature": 0.1,
            "streaming": True,
        }

        mock_chain = MagicMock()
        mock_chain.stream.return_value = iter(["Streamed ", "response"])
        mock_chain_creator.return_value = mock_chain

        chunks = [
            {
                "content": "Test content",
                "metadata": {"rendered_html_url": "http://test.com"},
            }
        ]

        result = list(generate_response_stream("test query", chunks))

        assert result == ["Streamed ", "response"]

    @patch("hope_jarvis.query.generate.create_llm_chain")
    def test_streams_multiple_tokens(self, mock_chain_creator):
        """Test streaming multiple tokens."""
        mock_chain = MagicMock()
        mock_chain.stream.return_value = iter(["Token1", "Token2", "Token3"])
        mock_chain_creator.return_value = mock_chain

        chunks = [
            {
                "content": "Test content",
                "metadata": {"rendered_html_url": "http://test.com"},
            }
        ]

        config = {
            "ollama": {
                "base_url": "http://localhost:11434",
                "model": "llama3",
                "temperature": 0.5,
                "streaming": True,
            }
        }

        result = list(generate_response_stream("test query", chunks, config))

        assert len(result) == 3
        assert result[0] == "Token1"
        assert result[1] == "Token2"
        assert result[2] == "Token3"

    @patch("hope_jarvis.query.generate.create_llm_chain")
    def test_handles_empty_chunks(self, mock_chain_creator):
        """Test streaming with empty chunks."""
        mock_chain = MagicMock()
        mock_chain.stream.return_value = iter(["Response"])
        mock_chain_creator.return_value = mock_chain

        config = {
            "ollama": {
                "base_url": "http://localhost:11434",
                "model": "llama3",
                "temperature": 0.5,
                "streaming": True,
            }
        }

        result = list(generate_response_stream("test query", [], config))

        assert result == ["Response"]
