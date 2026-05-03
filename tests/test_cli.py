import sys
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

from click.testing import CliRunner

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from hope_jarvis.cli import jarvis
from hope_jarvis.webhook import WebhookHandler


class TestWebhookHandler:
    """Test webhook functionality."""

    @patch("hope_jarvis.webhook.WEBHOOK_TOKEN", "secret-token")
    def test_missing_auth(self):
        """Test request without auth token."""
        handler = Mock(spec=WebhookHandler)
        handler.headers = {"Content-Type": "application/json"}
        handler._check_auth = WebhookHandler._check_auth.__get__(
            handler, WebhookHandler
        )

        result = handler._check_auth()
        assert not result

    @patch("hope_jarvis.webhook.WEBHOOK_TOKEN", "secret-token")
    def test_valid_auth_header(self):
        """Test request with valid Authorization header."""
        handler = Mock(spec=WebhookHandler)
        handler.headers = {"Authorization": "Bearer secret-token"}
        handler._check_auth = WebhookHandler._check_auth.__get__(
            handler, WebhookHandler
        )

        result = handler._check_auth()
        assert result

    @patch("hope_jarvis.webhook.WEBHOOK_TOKEN", "secret-token")
    def test_valid_x_token_header(self):
        """Test request with valid X-Webhook-Token header."""
        handler = Mock(spec=WebhookHandler)
        handler.headers = {"X-Webhook-Token": "secret-token"}
        handler._check_auth = WebhookHandler._check_auth.__get__(
            handler, WebhookHandler
        )

        result = handler._check_auth()
        assert result

    @patch("hope_jarvis.webhook.WEBHOOK_TOKEN", "")
    def test_no_token_configured(self):
        """Test that requests pass when no token is configured."""
        handler = Mock(spec=WebhookHandler)
        handler.headers = {}
        handler._check_auth = WebhookHandler._check_auth.__get__(
            handler, WebhookHandler
        )

        result = handler._check_auth()
        assert result

    @patch("hope_jarvis.webhook.WEBHOOK_TOKEN", "secret-token")
    def test_wrong_token(self):
        """Test request with wrong token."""
        handler = Mock(spec=WebhookHandler)
        handler.headers = {"Authorization": "Bearer wrong-token"}
        handler._check_auth = WebhookHandler._check_auth.__get__(
            handler, WebhookHandler
        )

        result = handler._check_auth()
        assert not result

    @patch("hope_jarvis.webhook.WEBHOOK_TOKEN", "secret-token")
    def test_wrong_x_token(self):
        """Test request with wrong X-Webhook-Token."""
        handler = Mock(spec=WebhookHandler)
        handler.headers = {"X-Webhook-Token": "wrong-token"}
        handler._check_auth = WebhookHandler._check_auth.__get__(
            handler, WebhookHandler
        )

        result = handler._check_auth()
        assert not result


class TestCliCommands:
    """Test CLI commands."""

    def test_check_command(self):
        """Test the check command."""
        with patch.dict(
            "os.environ",
            {
                "OLLAMA_BASE_URL": "test",
                "OLLAMA_MODEL": "test",
                "QDRANT_URL": "test",
                "QDRANT_COLLECTION_NAME": "test",
                "EMBEDDING_MODEL_NAME": "test",
                "CONFIG_PATH": "test",
                "DATA_PATH": "test",
            },
        ):
            runner = CliRunner()
            result = runner.invoke(jarvis, ["doc", "check"])
            assert result.exit_code == 0

    @patch("hope_jarvis.ingestion.store.QdrantClient")
    @patch("hope_jarvis.ingestion.store.TextEmbedding")
    @patch("hope_jarvis.cli.doc.sync_all_repos")
    @patch("hope_jarvis.cli.doc.chunk_markdown_file")
    @patch("hope_jarvis.cli.doc.store_chunks_in_qdrant")
    def test_sync_all(
        self, mock_store, mock_chunk, mock_sync, mock_embedding, mock_qdrant_client
    ):
        """Test sync command with all repos."""
        mock_client = MagicMock()
        mock_qdrant_client.return_value = mock_client
        mock_client.get_collections.return_value.collections = []

        mock_embedding.return_value = MagicMock()

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
        mock_chunk.return_value = [{"content": "test", "metadata": {}}]

        with patch.dict(
            "os.environ",
            {
                "QDRANT_URL": "http://localhost:6333",
                "QDRANT_COLLECTION_NAME": "test",
                "EMBEDDING_MODEL_NAME": "test-model",
                "CONFIG_PATH": "/tmp",
                "DATA_PATH": "/tmp",
            },
        ):
            runner = CliRunner()
            result = runner.invoke(jarvis, ["doc", "sync", "--force"])
            assert result.exit_code == 0
            mock_sync.assert_called_once()

    def test_sync_help(self):
        """Test sync command help."""
        runner = CliRunner()
        result = runner.invoke(jarvis, ["doc", "sync", "--help"])
        assert result.exit_code == 0

    @patch("hope_jarvis.cli.db.QdrantClient")
    def test_db_info(self, mock_client):
        """Test db info command."""
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        mock_instance.get_collections.return_value = MagicMock(collections=[])

        with patch.dict(
            "os.environ",
            {
                "QDRANT_URL": "http://localhost:6333",
                "QDRANT_COLLECTION_NAME": "test",
            },
        ):
            runner = CliRunner()
            result = runner.invoke(jarvis, ["db", "info"])
            assert result.exit_code == 0

    @patch("hope_jarvis.cli.db.QdrantClient")
    @patch("hope_jarvis.ingestion.store.QdrantClient")
    @patch("hope_jarvis.ingestion.store.init_qdrant_collection")
    def test_db_reset_all(self, mock_init, mock_store_client, mock_client):
        """Test db reset --all command."""
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance

        with patch.dict(
            "os.environ",
            {
                "QDRANT_URL": "http://localhost:6333",
                "QDRANT_COLLECTION_NAME": "test",
                "EMBEDDING_MODEL_NAME": "test-model",
                "QDRANT_API_KEY": "",
            },
        ):
            runner = CliRunner()
            result = runner.invoke(jarvis, ["db", "reset", "--yes"])
            assert result.exit_code == 0
            mock_instance.delete_collection.assert_called_once()

    def test_check_command_missing_vars(self):
        """Test the check command with missing vars."""
        with patch.dict("os.environ", {}, clear=True):
            runner = CliRunner()
            result = runner.invoke(jarvis, ["doc", "check"])
            assert result.exit_code == 1

    def test_sync_with_repo_name(self):
        """Test sync with repo name."""
        with patch.dict(
            "os.environ",
            {
                "QDRANT_URL": "http://localhost:6333",
                "QDRANT_COLLECTION_NAME": "test",
                "CONFIG_PATH": "/tmp",
                "DATA_PATH": "/tmp",
            },
        ):
            with patch(
                "hope_jarvis.cli.doc.sync_repo_by_name", return_value=[]
            ) as mock_sync:
                with patch("hope_jarvis.cli.doc.init_qdrant_collection"):
                    runner = CliRunner()
                    result = runner.invoke(jarvis, ["doc", "sync", "-r", "HOPE"])
                    assert result.exit_code == 0
                    mock_sync.assert_called_once()

    def test_sync_no_changed_files(self):
        """Test sync when no files changed."""
        with patch.dict(
            "os.environ",
            {
                "QDRANT_URL": "http://localhost:6333",
                "QDRANT_COLLECTION_NAME": "test",
                "CONFIG_PATH": "/tmp",
                "DATA_PATH": "/tmp",
            },
        ):
            with patch("hope_jarvis.cli.doc.sync_all_repos", return_value=[]):
                with patch("hope_jarvis.cli.doc.init_qdrant_collection"):
                    runner = CliRunner()
                    result = runner.invoke(jarvis, ["doc", "sync"])
                    assert result.exit_code == 0
                    assert "No files to process" in result.output

    @patch("hope_jarvis.cli.db.QdrantClient")
    def test_db_info_collection_not_exist(self, mock_client):
        """Test db info when collection doesn't exist."""
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        mock_instance.get_collections.return_value.collections = []

        with patch.dict(
            "os.environ",
            {
                "QDRANT_URL": "http://localhost:6333",
                "QDRANT_COLLECTION_NAME": "test",
            },
        ):
            runner = CliRunner()
            result = runner.invoke(jarvis, ["db", "info"])
            assert result.exit_code == 0
            assert "does not exist" in result.output

    @patch("hope_jarvis.cli.doc.sync_all_repos")
    @patch("hope_jarvis.cli.doc.chunk_markdown_file")
    @patch("hope_jarvis.cli.doc.store_chunks_in_qdrant")
    @patch("hope_jarvis.ingestion.store.QdrantClient")
    def test_sync_force_flag(
        self, mock_qdrant_client, mock_store, mock_chunk, mock_sync
    ):
        """Test sync with --force flag."""
        mock_client = MagicMock()
        mock_qdrant_client.return_value = mock_client
        mock_client.get_collections.return_value.collections = []

        mock_sync.return_value = []

        with patch.dict(
            "os.environ",
            {
                "QDRANT_URL": "http://localhost:6333",
                "QDRANT_COLLECTION_NAME": "test",
                "EMBEDDING_MODEL_NAME": "test-model",
                "CONFIG_PATH": "/tmp",
                "DATA_PATH": "/tmp",
            },
        ):
            runner = CliRunner()
            result = runner.invoke(jarvis, ["doc", "sync", "--force"])
            assert result.exit_code == 0
            mock_sync.assert_called_once_with(force=True)

    @patch("hope_jarvis.cli.doc.sync_repo_by_name")
    @patch("hope_jarvis.cli.doc.init_qdrant_collection")
    def test_sync_repo_no_changes(self, mock_init, mock_sync):
        """Test sync for repo with no changes."""
        mock_sync.return_value = []

        with patch.dict(
            "os.environ",
            {
                "QDRANT_URL": "http://localhost:6333",
                "QDRANT_COLLECTION_NAME": "test",
                "CONFIG_PATH": "/tmp",
                "DATA_PATH": "/tmp",
            },
        ):
            runner = CliRunner()
            result = runner.invoke(jarvis, ["doc", "sync", "-r", "HOPE"])
            assert result.exit_code == 0
            assert "No files to process" in result.output

    @patch("hope_jarvis.cli.doc.sync_all_repos")
    @patch("hope_jarvis.cli.doc.chunk_markdown_file")
    @patch("hope_jarvis.cli.doc.store_chunks_in_qdrant")
    @patch("hope_jarvis.ingestion.store.QdrantClient")
    def test_sync_no_chunks_created(
        self, mock_qdrant_client, mock_store, mock_chunk, mock_sync
    ):
        """Test sync when no chunks are created from files."""
        mock_client = MagicMock()
        mock_qdrant_client.return_value = mock_client
        mock_client.get_collections.return_value.collections = []

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
        mock_chunk.return_value = []

        with patch.dict(
            "os.environ",
            {
                "QDRANT_URL": "http://localhost:6333",
                "QDRANT_COLLECTION_NAME": "test",
                "EMBEDDING_MODEL_NAME": "test-model",
                "CONFIG_PATH": "/tmp",
                "DATA_PATH": "/tmp",
            },
        ):
            runner = CliRunner()
            result = runner.invoke(jarvis, ["doc", "sync"])
            assert result.exit_code == 0
            assert "No chunks created" in result.output

    @patch("hope_jarvis.cli.doc.sync_all_repos")
    @patch("hope_jarvis.cli.doc.chunk_markdown_file")
    @patch("hope_jarvis.cli.doc.store_chunks_in_qdrant")
    @patch("hope_jarvis.ingestion.store.QdrantClient")
    def test_sync_with_chunks(
        self, mock_qdrant_client, mock_store, mock_chunk, mock_sync
    ):
        """Test sync with successful chunk processing."""
        mock_client = MagicMock()
        mock_qdrant_client.return_value = mock_client
        mock_client.get_collections.return_value.collections = []

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
        mock_chunk.return_value = [{"content": "test chunk", "metadata": {}}]

        with patch.dict(
            "os.environ",
            {
                "QDRANT_URL": "http://localhost:6333",
                "QDRANT_COLLECTION_NAME": "test",
                "EMBEDDING_MODEL_NAME": "test-model",
                "CONFIG_PATH": "/tmp",
                "DATA_PATH": "/tmp",
            },
        ):
            runner = CliRunner()
            result = runner.invoke(jarvis, ["doc", "sync"])
            assert result.exit_code == 0
            mock_store.assert_called_once()

    @patch("hope_jarvis.cli.db.QdrantClient")
    def test_db_info_with_collection(self, mock_client):
        """Test db info with existing collection."""
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance

        mock_collection = MagicMock()
        mock_collection.name = "test"
        mock_instance.get_collections.return_value.collections = [mock_collection]

        mock_info = MagicMock()
        mock_info.status = "green"
        mock_info.points_count = 100
        mock_info.vectors_count = 100
        mock_info.indexed_vectors_count = 100
        mock_info.config.params.vectors.size = 384
        mock_info.config.params.vectors.distance = "Cosine"
        mock_instance.get_collection.return_value = mock_info
        mock_instance.scroll.return_value = ([], None)

        with patch.dict(
            "os.environ",
            {
                "QDRANT_URL": "http://localhost:6333",
                "QDRANT_COLLECTION_NAME": "test",
            },
        ):
            runner = CliRunner()
            result = runner.invoke(jarvis, ["db", "info"])

            assert result.exit_code == 0
            assert "Collection: test" in result.output
