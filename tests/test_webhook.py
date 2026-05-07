"""Tests for webhook module (FastAPI implementation)."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from hope_jarvis.webhook import _check_auth, app


class TestCheckAuth:
    """Test authentication function."""

    def test_no_token_configured(self):
        """Test that requests pass when no token is configured."""
        with patch("hope_jarvis.webhook.WEBHOOK_TOKEN", ""):
            result = _check_auth()
            assert result is True

    def test_valid_auth_header(self):
        """Test request with valid Authorization header."""
        with patch("hope_jarvis.webhook.WEBHOOK_TOKEN", "secret-token"):
            result = _check_auth(authorization="Bearer secret-token")
            assert result is True

    def test_invalid_auth_header(self):
        """Test request with invalid Authorization header."""
        with patch("hope_jarvis.webhook.WEBHOOK_TOKEN", "secret-token"):
            result = _check_auth(authorization="Bearer wrong-token")
            assert result is False

    def test_valid_x_token_header(self):
        """Test request with valid X-Webhook-Token header."""
        with patch("hope_jarvis.webhook.WEBHOOK_TOKEN", "secret-token"):
            result = _check_auth(x_webhook_token="secret-token")
            assert result is True

    def test_invalid_x_token_header(self):
        """Test request with invalid X-Webhook-Token header."""
        with patch("hope_jarvis.webhook.WEBHOOK_TOKEN", "secret-token"):
            result = _check_auth(x_webhook_token="wrong-token")
            assert result is False

    def test_missing_auth(self):
        """Test request without auth token."""
        with patch("hope_jarvis.webhook.WEBHOOK_TOKEN", "secret-token"):
            result = _check_auth()
            assert result is False


class TestWebhookEndpoints:
    """Test FastAPI webhook endpoints."""

    def test_webhook_endpoint_exists(self):
        """Test that /webhook endpoint exists."""
        client = TestClient(app)
        # Just check the route exists (will fail auth without proper setup)
        response = client.post("/webhook", json={})
        assert response.status_code in [401, 400, 500]  # Not 404

    def test_config_endpoint(self):
        """Test that /config endpoint returns config."""
        with patch("hope_jarvis.config.get_ollama_base_url", return_value="test"):
            with patch("hope_jarvis.config.get_qdrant_url", return_value="test"):
                with patch("hope_jarvis.config.get_embedding_model_name", return_value="test"):
                    with patch("hope_jarvis.config.get_config_path", return_value=Path("/test")):
                        with patch("hope_jarvis.config.get_data_path", return_value=Path("/test")):
                            with patch("hope_jarvis.config.get_knowledge_path", return_value=Path("/test")):
                                with patch("hope_jarvis.config.get_all_repo_names", return_value=["HOPE"]):
                                    client = TestClient(app)
                                    response = client.get("/config")
                                    assert response.status_code == 200
                                    data = response.json()
                                    assert "ollama_base_url" in data
                                    assert "qdrant_url" in data
                                    assert "embedding_model" in data

    def test_health_endpoint(self):
        """Test that /health endpoint returns ok."""
        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "webhook"

    def test_webhook_without_auth(self):
        """Test webhook without authentication (no token configured)."""
        with patch("hope_jarvis.webhook.WEBHOOK_TOKEN", ""):
            with patch("click.testing.CliRunner") as mock_runner:
                mock_result = MagicMock()
                mock_result.exit_code = 0
                mock_runner.return_value.invoke.return_value = mock_result

                client = TestClient(app)
                response = client.post(
                    "/webhook",
                    json={"repository": {"name": "test-repo"}},
                )
                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "success"

    def test_webhook_wrong_token(self):
        """Test webhook with wrong token."""
        with patch("hope_jarvis.webhook.WEBHOOK_TOKEN", "secret-token"):
            client = TestClient(app)
            response = client.post(
                "/webhook",
                json={"repository": {"name": "test-repo"}},
                headers={"Authorization": "Bearer wrong-token"},
            )
            assert response.status_code == 401

    def test_webhook_missing_repo_name(self):
        """Test webhook with missing repo name."""
        with patch("hope_jarvis.webhook.WEBHOOK_TOKEN", ""):
            client = TestClient(app)
            response = client.post(
                "/webhook",
                json={"repository": {}},
            )
            assert response.status_code == 400

    def test_webhook_repo_from_body_repo_field(self):
        """Test webhook getting repo name from 'repo' field."""
        with patch("hope_jarvis.webhook.WEBHOOK_TOKEN", ""):
            with patch("click.testing.CliRunner") as mock_runner:
                mock_result = MagicMock()
                mock_result.exit_code = 0
                mock_runner.return_value.invoke.return_value = mock_result

                client = TestClient(app)
                response = client.post(
                    "/webhook",
                    json={"repo": "test-repo"},
                )
                assert response.status_code == 200

    def test_webhook_cli_error(self):
        """Test webhook when CLI command fails."""
        with patch("hope_jarvis.webhook.WEBHOOK_TOKEN", ""):
            with patch("click.testing.CliRunner") as mock_runner:
                mock_result = MagicMock()
                mock_result.exit_code = 1
                mock_result.output = "Error: something went wrong"
                mock_runner.return_value.invoke.return_value = mock_result

                client = TestClient(app)
                response = client.post(
                    "/webhook",
                    json={"repository": {"name": "test-repo"}},
                )
                assert response.status_code == 500

    def test_webhook_invalid_json(self):
        """Test webhook with invalid JSON body."""
        with patch("hope_jarvis.webhook.WEBHOOK_TOKEN", ""):
            with patch("click.testing.CliRunner") as mock_runner:
                mock_result = MagicMock()
                mock_result.exit_code = 0
                mock_runner.return_value.invoke.return_value = mock_result

                client = TestClient(app)
                response = client.post(
                    "/webhook",
                    content=b"not valid json",
                    headers={"content-type": "application/json"},
                )
                assert response.status_code == 400

    def test_config_endpoint_repos_error(self):
        """Test /config endpoint when getting repos fails."""
        with patch("hope_jarvis.config.get_ollama_base_url", return_value="test"):
            with patch("hope_jarvis.config.get_qdrant_url", return_value="test"):
                with patch("hope_jarvis.config.get_embedding_model_name", return_value="test"):
                    with patch("hope_jarvis.config.get_config_path", return_value=Path("/test")):
                        with patch("hope_jarvis.config.get_data_path", return_value=Path("/test")):
                            with patch("hope_jarvis.config.get_knowledge_path", return_value=Path("/test")):
                                with patch(
                                    "hope_jarvis.config.get_all_repo_names",
                                    side_effect=Exception("Config error"),
                                ):
                                    client = TestClient(app)
                                    response = client.get("/config")
                                    assert response.status_code == 200
                                    data = response.json()
                                    assert "repos_error" in data

    def test_config_endpoint_with_repos_config(self):
        """Test /config endpoint includes repos_config path."""
        with (
            patch("hope_jarvis.config.get_ollama_base_url", return_value="test"),
            patch("hope_jarvis.config.get_qdrant_url", return_value="test"),
            patch("hope_jarvis.config.get_embedding_model_name", return_value="test"),
            patch("hope_jarvis.config.get_config_path", return_value=Path("/test")),
            patch("hope_jarvis.config.get_data_path", return_value=Path("/test")),
            patch("hope_jarvis.config.get_knowledge_path", return_value=Path("/test")),
            patch("hope_jarvis.config.get_repos_config", return_value=Path("/test/repos.yaml")),
            patch("hope_jarvis.config.get_all_repo_names", return_value=["HOPE"]),
        ):
            client = TestClient(app)
            response = client.get("/config")
            assert response.status_code == 200
            data = response.json()
            assert "repos_config" in data
            assert "repos" in data

    def test_get_hf_cache_path_hf_home(self):
        """Test _get_hf_cache_path with HF_HOME set."""
        with patch.dict("os.environ", {"HF_HOME": "/custom/hf"}):
            from hope_jarvis.webhook import _get_hf_cache_path

            assert _get_hf_cache_path() == "/custom/hf"

    def test_get_hf_cache_path_hf_hub_cache(self):
        """Test _get_hf_cache_path with HF_HUB_CACHE set."""
        with patch.dict("os.environ", {"HF_HUB_CACHE": "/custom/cache"}):
            from hope_jarvis.webhook import _get_hf_cache_path

            assert _get_hf_cache_path() == "/custom/cache"

    def test_get_hf_cache_path_default(self):
        """Test _get_hf_cache_path default path."""
        with patch.dict("os.environ", {}, clear=True):
            from hope_jarvis.webhook import _get_hf_cache_path

            result = _get_hf_cache_path()
            assert result.endswith("huggingface")
