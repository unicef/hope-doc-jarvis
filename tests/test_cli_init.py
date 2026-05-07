"""Tests for hope_jarvis.cli.__init__ module."""

import json
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner


@pytest.fixture
def runner():
    """CliRunner fixture."""
    return CliRunner()


class TestCheckOllama:
    """Test _check_ollama function."""

    def test_ollama_reachable(self):
        """Test Ollama check when reachable."""
        from hope_jarvis.cli import _check_ollama

        with patch("hope_jarvis.cli._check_url", return_value=(True, "200")):
            ok, msg = _check_ollama("http://localhost:11434")
            assert ok
            assert "reachable" in msg

    def test_ollama_unreachable(self):
        """Test Ollama check when unreachable."""
        from hope_jarvis.cli import _check_ollama

        with patch("hope_jarvis.cli._check_url", return_value=(False, "Connection refused")):
            ok, msg = _check_ollama("http://localhost:11434")
            assert not ok
            assert "unreachable" in msg


class TestCheckQdrant:
    """Test _check_qdrant function."""

    def test_qdrant_healthy(self):
        """Test Qdrant check with healthy status."""
        from hope_jarvis.cli import _check_qdrant

        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({"status": "ok"}).encode()

        # Mock both /health and /collections to return healthy
        with patch("hope_jarvis.cli.urlopen", return_value=mock_resp):
            ok, msg = _check_qdrant("http://localhost:6333")
            assert ok
            assert "reachable" in msg

    def test_qdrant_with_api_key(self):
        """Test Qdrant check with API key."""
        from hope_jarvis.cli import _check_qdrant

        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({"status": "ok"}).encode()

        with patch("hope_jarvis.cli.urlopen") as mock_urlopen:
            mock_urlopen.return_value = mock_resp
            ok, msg = _check_qdrant("http://localhost:6333", api_key="test-key")
            assert ok

    def test_qdrant_unreachable(self):
        """Test Qdrant check when unreachable."""
        from hope_jarvis.cli import _check_qdrant

        with patch("hope_jarvis.cli.urlopen", side_effect=Exception("Connection refused")):
            ok, msg = _check_qdrant("http://localhost:6333")
            assert not ok
            assert "unreachable" in msg


class TestCheckCommand:
    """Test check command comprehensively."""

    def test_check_all_vars_set(self, runner):
        """Test check command with all vars set."""
        env_vars = {
            "OLLAMA_HOST": "localhost",
            "OLLAMA_MODEL": "llama3",
            "OLLAMA_TEMPERATURE": "0.5",
            "OLLAMA_STREAMING": "true",
            "QDRANT_HOST": "localhost",
            "QDRANT_COLLECTION_NAME": "test",
            "QDRANT_API_KEY": "test-key",
            "EMBEDDING_MODEL_NAME": "test-model",
            "EMBEDDING_VECTOR_SIZE": "384",
            "RETRIEVAL_TOP_K": "5",
            "RETRIEVAL_SCORE_THRESHOLD": "0.5",
            "INGESTION_CHUNK_SIZE": "1000",
            "INGESTION_CHUNK_OVERLAP": "200",
            "CONFIG_PATH": "/tmp",
            "DATA_DIR": "/tmp",
            "WEBHOOK_TOKEN": "test-token",
            "SENTRY_DSN": "https://test@sentry.io/123",
            "ENVIRONMENT": "test",
        }

        with patch.dict("os.environ", env_vars, clear=True):
            from hope_jarvis.cli import jarvis

            result = runner.invoke(jarvis, ["check"])
            assert result.exit_code == 0
            assert "JARVIS CHECK" in result.output

    def test_check_missing_vars(self, runner):
        """Test check command with missing vars."""
        with patch.dict(
            "os.environ",
            {"OLLAMA_HOST": "localhost", "QDRANT_HOST": "localhost", "OLLAMA_MODEL": "test"},
            clear=True,
        ):
            from hope_jarvis.cli import jarvis

            result = runner.invoke(jarvis, ["check"])
            assert result.exit_code == 0

    def test_check_services_not_configured(self, runner):
        """Test check command with services not configured."""
        with patch.dict(
            "os.environ",
            {"OLLAMA_HOST": "localhost", "QDRANT_HOST": "localhost", "OLLAMA_MODEL": "test"},
            clear=True,
        ):
            from hope_jarvis.cli import jarvis

            result = runner.invoke(jarvis, ["check"])
            assert result.exit_code == 0
            assert "not configured" in result.output

    def test_check_repos_configured(self, runner, tmp_path):
        """Test check command with repos configured."""
        repos_yaml = tmp_path / "repos.yaml"
        repos_yaml.write_text("""
repos:
  - name: HOPE
    github_url: https://github.com/test/hope
    docs_dir: docs
    rendered_base_url: https://hope.example.com
""")

        with patch.dict(
            "os.environ",
            {
                "OLLAMA_HOST": "localhost",
                "QDRANT_HOST": "localhost",
                "OLLAMA_MODEL": "test",
                "CONFIG_PATH": str(tmp_path),
            },
            clear=True,
        ):
            from hope_jarvis.cli import jarvis

            result = runner.invoke(jarvis, ["check"])
            assert result.exit_code == 0
            assert "repos configured" in result.output

    def test_check_directories_not_set(self, runner):
        """Test check command with directories not set."""
        with patch.dict(
            "os.environ",
            {"OLLAMA_HOST": "localhost", "QDRANT_HOST": "localhost", "OLLAMA_MODEL": "test"},
            clear=True,
        ):
            from hope_jarvis.cli import jarvis

            result = runner.invoke(jarvis, ["check"])
            assert result.exit_code == 0


class TestRunCommand:
    """Test run command."""

    def test_run_chainlit(self):
        """Test run command starts chainlit."""
        from hope_jarvis.cli import jarvis

        runner = CliRunner()

        with patch("subprocess.run") as mock_run:
            result = runner.invoke(jarvis, ["run", "web", "--bind", "localhost:9000"])
            assert result.exit_code == 0
            mock_run.assert_called_once()
            call_args = mock_run.call_args[0][0]
            assert "chainlit" in call_args
            assert "9000" in call_args
