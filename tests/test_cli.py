import sys
from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from hope_jarvis.cli import jarvis
from hope_jarvis.webhook import _check_auth, app


class TestWebhookAuth:
    """Test webhook authentication."""

    def test_missing_auth(self):
        """Test request without auth token."""
        with patch("hope_jarvis.webhook.WEBHOOK_TOKEN", ""):
            # No token configured - should allow all
            result = _check_auth()
            assert result is True

    def test_valid_auth_header(self):
        """Test request with valid Authorization header."""
        with patch("hope_jarvis.webhook.WEBHOOK_TOKEN", "secret-token"):
            result = _check_auth(authorization="Bearer secret-token")
            assert result is True

    def test_valid_x_token_header(self):
        """Test request with valid X-Webhook-Token header."""
        with patch("hope_jarvis.webhook.WEBHOOK_TOKEN", "secret-token"):
            result = _check_auth(x_webhook_token="secret-token")
            assert result is True

    def test_no_token_configured(self):
        """Test that requests pass when no token is configured."""
        with patch("hope_jarvis.webhook.WEBHOOK_TOKEN", ""):
            result = _check_auth()
            assert result is True

    def test_wrong_token(self):
        """Test request with wrong token."""
        with patch("hope_jarvis.webhook.WEBHOOK_TOKEN", "secret-token"):
            result = _check_auth(authorization="Bearer wrong-token")
            assert result is False

    def test_wrong_x_token(self):
        """Test request with wrong X-Webhook-Token."""
        with patch("hope_jarvis.webhook.WEBHOOK_TOKEN", "secret-token"):
            result = _check_auth(x_webhook_token="wrong-token")
            assert result is False


class TestWebhookApp:
    """Test FastAPI webhook app."""

    def test_app_exists(self):
        """Test that FastAPI app is created."""
        assert app is not None
        assert hasattr(app, "routes")

    def test_has_webhook_route(self):
        """Test that /webhook endpoint exists."""
        paths = [route.path for route in app.routes]
        assert "/webhook" in paths

    def test_has_config_route(self):
        """Test that /config endpoint exists."""
        paths = [route.path for route in app.routes]
        assert "/config" in paths

    def test_has_health_route(self):
        """Test that /health endpoint exists."""
        paths = [route.path for route in app.routes]
        assert "/health" in paths


class TestCliCommands:
    """Test CLI commands."""

    def test_check_command(self):
        """Test the check command."""
        with patch.dict(
            "os.environ",
            {
                "OLLAMA_HOST": "localhost",
                "OLLAMA_MODEL": "test",
                "QDRANT_HOST": "localhost",
                "QDRANT_COLLECTION_NAME": "test",
                "EMBEDDING_MODEL_NAME": "test",
                "CONFIG_PATH": "test",
                "DATA_DIR": "test",
            },
        ):
            runner = CliRunner()
            result = runner.invoke(jarvis, ["check"])
            assert result.exit_code == 0

    def test_run_help(self):
        """Test jarvis run help."""
        runner = CliRunner()
        result = runner.invoke(jarvis, ["run", "--help"])
        assert result.exit_code == 0
        assert "web" in result.output
        assert "service" in result.output

    def test_kb_help(self):
        """Test jarvis kb help."""
        runner = CliRunner()
        result = runner.invoke(jarvis, ["kb", "--help"])
        assert result.exit_code == 0
