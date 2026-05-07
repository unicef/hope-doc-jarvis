"""Tests for hope_jarvis.cli.db module."""

from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner


@pytest.fixture
def runner():
    """CliRunner fixture."""
    return CliRunner()


@pytest.fixture
def mock_dependencies():
    """Mock all dependencies for db commands."""
    with patch("hope_jarvis.cli.db.QdrantClient") as mock_client:
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        mock_instance.get_collections.return_value.collections = []
        yield mock_instance


class TestDbGroup:
    """Test db group command."""

    def test_db_help(self, runner):
        """Test db command help."""
        from hope_jarvis.cli.db import db

        result = runner.invoke(db, ["--help"])
        assert result.exit_code == 0
        assert "Database management commands" in result.output


class TestUpdateCommand:
    """Test update command."""

    def test_update_all_repos(self, runner):
        """Test update command with all repos."""
        from hope_jarvis.cli.db import db

        mock_repo = {
            "name": "HOPE",
            "docs_dir": "docs",
            "github_url": "https://github.com/test/hope",
            "rendered_base_url": "https://hope.example.com",
        }

        with patch("hope_jarvis.cli.db.init_qdrant_collection"):
            with patch("hope_jarvis.cli.db.get_all_repos", return_value=iter([mock_repo])):
                with patch("hope_jarvis.cli.db.find_markdown_files", return_value=[]):
                    with patch.dict(
                        "os.environ",
                        {
                            "QDRANT_HOST": "localhost",
                            "QDRANT_COLLECTION_NAME": "test",
                            "EMBEDDING_MODEL_NAME": "test-model",
                            "CONFIG_PATH": "/tmp",
                            "DATA_DIR": "/tmp",
                        },
                    ):
                        result = runner.invoke(db, ["update"])

                        assert result.exit_code == 0
                        assert "Updating Qdrant" in result.output

    def test_update_with_force_flag(self, runner):
        """Test update command with force flag."""
        from hope_jarvis.cli.db import db

        mock_repo = {
            "name": "HOPE",
            "docs_dir": "docs",
            "github_url": "https://github.com/test/hope",
            "rendered_base_url": "https://hope.example.com",
        }

        with patch("hope_jarvis.cli.db.init_qdrant_collection"):
            with patch("hope_jarvis.cli.db.get_all_repos", return_value=iter([mock_repo])):
                with patch("hope_jarvis.cli.db.find_markdown_files", return_value=[]):
                    with patch.dict(
                        "os.environ",
                        {
                            "QDRANT_HOST": "localhost",
                            "QDRANT_COLLECTION_NAME": "test",
                            "EMBEDDING_MODEL_NAME": "test-model",
                            "CONFIG_PATH": "/tmp",
                            "DATA_DIR": "/tmp",
                        },
                    ):
                        result = runner.invoke(db, ["update", "--force"])

                        assert result.exit_code == 0
                        assert "force" in result.output


class TestResetCommand:
    """Test reset command."""

    def test_reset_all(self, runner, mock_dependencies):
        """Test reset command for all repos."""
        from hope_jarvis.cli.db import db

        mock_dependencies.get_collection.return_value.status = "green"
        mock_dependencies.delete_collection.return_value = None

        with patch("hope_jarvis.cli.db.get_all_repo_names", return_value=[]):
            with patch("hope_jarvis.cli.db.init_qdrant_collection"):
                with patch.dict(
                    "os.environ",
                    {
                        "QDRANT_HOST": "localhost",
                        "QDRANT_COLLECTION_NAME": "test",
                        "QDRANT_API_KEY": "",
                    },
                ):
                    result = runner.invoke(db, ["reset", "--yes"])

                    assert result.exit_code == 0
                    assert "Reset" in result.output

    def test_reset_specific_repo(self, runner, mock_dependencies):
        """Test reset command for specific repo."""
        from hope_jarvis.cli.db import db

        mock_dependencies.get_collection.return_value.status = "green"

        with patch("hope_jarvis.cli.db.get_all_repo_names", return_value=["HOPE"]):
            with patch.dict(
                "os.environ",
                {
                    "QDRANT_HOST": "localhost",
                    "QDRANT_COLLECTION_NAME": "test",
                    "QDRANT_API_KEY": "",
                },
            ):
                result = runner.invoke(db, ["reset", "-r", "HOPE", "--yes"])

                assert result.exit_code == 0
                assert "HOPE" in result.output


class TestInfoCommand:
    """Test info command."""

    def test_info_collection_not_exist(self, runner, mock_dependencies):
        """Test info command when collection doesn't exist."""
        from hope_jarvis.cli.db import db

        mock_dependencies.get_collections.return_value.collections = []

        with patch.dict(
            "os.environ",
            {"QDRANT_HOST": "localhost", "QDRANT_COLLECTION_NAME": "test"},
        ):
            result = runner.invoke(db, ["info"])

            assert result.exit_code == 0
            assert "does not exist" in result.output

    def test_info_with_collection(self, runner, mock_dependencies):
        """Test info command with existing collection."""
        from hope_jarvis.cli.db import db

        mock_collection = MagicMock()
        mock_collection.name = "test"
        mock_dependencies.get_collections.return_value.collections = [mock_collection]

        mock_info = MagicMock()
        mock_info.status = "green"
        mock_info.points_count = 100
        mock_info.vectors_count = 100
        mock_info.indexed_vectors_count = 100
        mock_info.config.params.vectors.size = 384
        mock_info.config.params.vectors.distance = "Cosine"
        mock_dependencies.get_collection.return_value = mock_info

        # Mock scroll to return points
        mock_point = MagicMock()
        mock_point.payload = {"repo_name": "HOPE"}
        mock_dependencies.scroll.return_value = ([mock_point], None)

        with patch.dict(
            "os.environ",
            {
                "QDRANT_HOST": "localhost",
                "QDRANT_COLLECTION_NAME": "test",
                "QDRANT_API_KEY": "",
            },
        ):
            result = runner.invoke(db, ["info"])

            assert result.exit_code == 0
            assert "Collection:" in result.output
