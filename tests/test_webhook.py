import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from hope_jarvis.webhook import WebhookHandler


class TestWebhookHandlerPost:
    """Test webhook POST handler."""

    def _make_handler(self, token=""):
        """Create a mock handler for testing."""
        handler = Mock(spec=WebhookHandler)
        handler.headers = {}
        handler.rfile = Mock()
        handler.wfile = Mock()
        handler._check_auth = WebhookHandler._check_auth.__get__(
            handler, WebhookHandler
        )
        handler.send_response = Mock()
        handler.send_header = Mock()
        handler.end_headers = Mock()
        return handler

    @patch("hope_jarvis.webhook.WEBHOOK_TOKEN", "test-token")
    def test_unauthorized_request(self):
        """Test POST with invalid auth."""
        handler = self._make_handler()
        handler.headers = {"Content-Type": "application/json"}
        handler.do_POST = WebhookHandler.do_POST.__get__(handler, WebhookHandler)

        handler.do_POST()

        handler.send_response.assert_called_with(401)
        handler.wfile.write.assert_called_once()
        response = json.loads(handler.wfile.write.call_args[0][0])
        assert response["error"] == "Unauthorized"

    @patch("hope_jarvis.webhook.WEBHOOK_TOKEN", "")
    def test_missing_repo_name(self):
        """Test POST with missing repo name."""
        handler = self._make_handler()
        payload = b"{}"
        handler.headers = {"Content-Length": str(len(payload))}
        handler.rfile.read.return_value = payload
        handler.do_POST = WebhookHandler.do_POST.__get__(handler, WebhookHandler)

        handler.do_POST()

        handler.send_response.assert_called_with(400)
        handler.wfile.write.assert_called_once()
        response = json.loads(handler.wfile.write.call_args[0][0])
        assert response["error"] == "Missing repo name"

    @patch("hope_jarvis.webhook.WEBHOOK_TOKEN", "")
    @patch("click.testing.CliRunner")
    def test_successful_update(self, mock_runner_class):
        """Test successful webhook trigger."""
        mock_runner = MagicMock()
        mock_result = MagicMock()
        mock_result.exit_code = 0
        mock_result.output = "Success"
        mock_runner.invoke.return_value = mock_result
        mock_runner_class.return_value = mock_runner

        handler = self._make_handler()
        payload = json.dumps({"repository": {"name": "test-repo"}}).encode()
        handler.headers = {
            "Content-Length": str(len(payload)),
            "Content-Type": "application/json",
        }
        handler.rfile.read.return_value = payload
        handler.do_POST = WebhookHandler.do_POST.__get__(handler, WebhookHandler)

        handler.do_POST()

        handler.send_response.assert_called_with(200)
        handler.wfile.write.assert_called_once()
        response = json.loads(handler.wfile.write.call_args[0][0])
        assert response["status"] == "success"
        assert response["repo"] == "test-repo"

    @patch("hope_jarvis.webhook.WEBHOOK_TOKEN", "")
    @patch("click.testing.CliRunner")
    def test_update_error(self, mock_runner_class):
        """Test webhook update with error."""
        mock_runner = MagicMock()
        mock_result = MagicMock()
        mock_result.exit_code = 1
        mock_result.output = "Error occurred"
        mock_runner.invoke.return_value = mock_result
        mock_runner_class.return_value = mock_runner

        handler = self._make_handler()
        payload = json.dumps({"repo": "test-repo"}).encode()
        handler.headers = {
            "Content-Length": str(len(payload)),
            "Content-Type": "application/json",
        }
        handler.rfile.read.return_value = payload
        handler.do_POST = WebhookHandler.do_POST.__get__(handler, WebhookHandler)

        handler.do_POST()

        handler.send_response.assert_called_with(500)
        handler.wfile.write.assert_called_once()
        response = json.loads(handler.wfile.write.call_args[0][0])
        assert response["status"] == "error"

    @patch("hope_jarvis.webhook.WEBHOOK_TOKEN", "")
    @patch("click.testing.CliRunner")
    def test_update_with_repo_field(self, mock_runner_class):
        """Test webhook with direct repo field."""
        mock_runner = MagicMock()
        mock_result = MagicMock()
        mock_result.exit_code = 0
        mock_result.output = "Success"
        mock_runner.invoke.return_value = mock_result
        mock_runner_class.return_value = mock_runner

        handler = self._make_handler()
        payload = json.dumps({"repo": "my-repo"}).encode()
        handler.headers = {
            "Content-Length": str(len(payload)),
            "Content-Type": "application/json",
        }
        handler.rfile.read.return_value = payload
        handler.do_POST = WebhookHandler.do_POST.__get__(handler, WebhookHandler)

        handler.do_POST()

        handler.send_response.assert_called_with(200)

    @patch("hope_jarvis.webhook.WEBHOOK_TOKEN", "")
    def test_handles_invalid_json_body(self):
        """Test webhook with invalid JSON body."""
        handler = self._make_handler()
        payload = b"not json!!!"
        handler.headers = {
            "Content-Length": str(len(payload)),
            "Content-Type": "application/json",
        }
        handler.rfile.read.return_value = payload
        handler.do_POST = WebhookHandler.do_POST.__get__(handler, WebhookHandler)

        handler.do_POST()

        handler.send_response.assert_called_with(400)

    @patch("hope_jarvis.webhook.WEBHOOK_TOKEN", "")
    def test_handles_empty_body(self):
        """Test webhook with empty body."""
        handler = self._make_handler()
        handler.headers = {
            "Content-Length": "0",
            "Content-Type": "application/json",
        }
        handler.rfile.read.return_value = b""
        handler.do_POST = WebhookHandler.do_POST.__get__(handler, WebhookHandler)

        handler.do_POST()

        handler.send_response.assert_called_with(400)

    def test_log_message(self):
        """Test log_message method."""
        handler = self._make_handler()
        handler.log_message = WebhookHandler.log_message.__get__(
            handler, WebhookHandler
        )

        import io
        import sys

        captured = io.StringIO()
        sys.stdout = captured

        handler.log_message("Test message %s", "arg")

        sys.stdout = sys.__stdout__
        output = captured.getvalue()
        assert "[WEBHOOK]" in output


class TestWebhookMain:
    """Test webhook main function."""

    @patch("hope_jarvis.webhook.ThreadingHTTPServer")
    def test_main_starts_server(self, mock_server_class):
        """Test that main starts the server."""
        from hope_jarvis.webhook import main

        mock_server = MagicMock()
        mock_server_class.return_value = mock_server

        def stop_server(*args, **kwargs):
            import sys

            sys.exit(0)

        mock_server.serve_forever.side_effect = stop_server

        try:
            main()
        except SystemExit:
            pass

        mock_server_class.assert_called_once()


class TestSentryInit:
    """Test Sentry initialization."""

    def test_sentry_init_with_dsn(self):
        """Test Sentry is initialized when DSN is provided."""
        with patch.dict(
            "os.environ",
            {"SENTRY_DSN": "https://test@sentry.io/123", "ENVIRONMENT": "test"},
        ):
            with patch("sentry_sdk.init") as mock_init:
                import importlib
                import hope_jarvis.webhook

                importlib.reload(hope_jarvis.webhook)

                mock_init.assert_called_once_with(
                    dsn="https://test@sentry.io/123",
                    environment="test",
                    send_default_pii=False,
                )

    def test_sentry_not_init_without_dsn(self):
        """Test Sentry is not initialized when DSN is not provided."""
        with patch.dict("os.environ", {}, clear=True):
            with patch("sentry_sdk.init") as mock_init:
                import importlib
                import hope_jarvis.webhook

                importlib.reload(hope_jarvis.webhook)

                mock_init.assert_not_called()

    def test_sentry_init_default_environment(self):
        """Test Sentry uses 'production' as default environment."""
        with patch.dict(
            "os.environ", {"SENTRY_DSN": "https://test@sentry.io/123"}, clear=True
        ):
            with patch("sentry_sdk.init") as mock_init:
                import importlib
                import hope_jarvis.webhook

                importlib.reload(hope_jarvis.webhook)

                mock_init.assert_called_once_with(
                    dsn="https://test@sentry.io/123",
                    environment="production",
                    send_default_pii=False,
                )
