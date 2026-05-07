"""Tests for hope_jarvis.cli.run module."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from hope_jarvis.cli.run import parse_host_port, run


class TestParseHostPort:
    """Test parse_host_port function."""

    def test_host_and_port(self):
        """Test parsing host:port."""
        assert parse_host_port("localhost:8000", 9000) == ("localhost", 8000)

    def test_host_only(self):
        """Test parsing host without port."""
        # "localhost" matches as host but no port, so port defaults
        assert parse_host_port("localhost", 9000) == ("localhost", 9000)

    def test_port_only(self):
        """Test parsing just :port."""
        assert parse_host_port(":8000", 9000) == (None, 8000)

    def test_empty_string(self):
        """Test empty string returns default."""
        assert parse_host_port("", 9000) == (None, 9000)

    def test_none_value(self):
        """Test None returns default."""
        assert parse_host_port(None, 9000) == (None, 9000)

    def test_invalid_format(self):
        """Test invalid format raises BadParameter."""
        with pytest.raises(Exception, match="Invalid"):
            parse_host_port("host:port:extra", 9000)

    def test_invalid_port_zero(self):
        """Test port 0 raises BadParameter."""
        with pytest.raises(Exception, match="Invalid"):
            parse_host_port(":0", 9000)

    def test_invalid_port_too_large(self):
        """Test port > 65535 raises BadParameter."""
        with pytest.raises(Exception, match="Invalid"):
            parse_host_port(":99999", 9000)

    def test_port_boundary_min(self):
        """Test port 1 is valid."""
        assert parse_host_port(":1", 9000) == (None, 1)

    def test_port_boundary_max(self):
        """Test port 65535 is valid."""
        assert parse_host_port(":65535", 9000) == (None, 65535)


class TestRunGroup:
    """Test run group command."""

    def test_run_help(self):
        """Test run command help."""
        runner = CliRunner()
        result = runner.invoke(run, ["--help"])
        assert result.exit_code == 0
        assert "Run Jarvis services" in result.output


class TestWebCommand:
    """Test web command."""

    def test_web_help(self):
        """Test web command help."""
        runner = CliRunner()
        result = runner.invoke(run, ["web", "--help"])
        assert result.exit_code == 0
        assert "Chainlit" in result.output

    def test_web_default(self):
        """Test web command with defaults."""
        runner = CliRunner()

        with patch("hope_jarvis.cli.run.subprocess.run") as mock_run:
            result = runner.invoke(run, ["web"])
            assert result.exit_code == 0
            assert "Starting Chainlit" in result.output
            mock_run.assert_called_once()
            cmd = mock_run.call_args[0][0]
            assert "chainlit" in cmd
            assert "--host" in cmd
            assert "--port" in cmd

    def test_web_custom_bind(self):
        """Test web command with custom bind."""
        runner = CliRunner()

        with patch("hope_jarvis.cli.run.subprocess.run") as mock_run:
            result = runner.invoke(run, ["web", "--bind", "0.0.0.0:9000"])
            assert result.exit_code == 0
            mock_run.assert_called_once()
            cmd = mock_run.call_args[0][0]
            assert "0.0.0.0" in cmd
            assert "9000" in cmd


class TestServiceCommand:
    """Test service command."""

    def test_service_help(self):
        """Test service command help."""
        runner = CliRunner()
        result = runner.invoke(run, ["service", "--help"])
        assert result.exit_code == 0
        assert "webhook" in result.output.lower()

    def test_service_no_auth(self):
        """Test service command without auth."""
        runner = CliRunner()

        with patch.dict("os.environ", {}, clear=True):
            with patch("uvicorn.run"):
                with patch("hope_jarvis.webhook.app", return_value=MagicMock()):
                    result = runner.invoke(run, ["service"])
                    assert result.exit_code == 0
                    assert "WITHOUT authentication" in result.output
                    assert "Listening on" in result.output

    def test_service_with_auth(self):
        """Test service command with auth token."""
        runner = CliRunner()

        with patch.dict("os.environ", {"WEBHOOK_TOKEN": "secret"}, clear=True):
            with patch("uvicorn.run"):
                with patch("hope_jarvis.webhook.app", return_value=MagicMock()):
                    result = runner.invoke(run, ["service"])
                    assert result.exit_code == 0
                    assert "authentication" in result.output

    def test_service_custom_bind(self):
        """Test service command with custom bind."""
        runner = CliRunner()

        with patch.dict("os.environ", {}, clear=True):
            with patch("uvicorn.run"):
                with patch("hope_jarvis.webhook.app", return_value=MagicMock()):
                    result = runner.invoke(run, ["service", "--bind", "127.0.0.1:8080"])
                    assert result.exit_code == 0
                    assert "127.0.0.1:8080" in result.output
