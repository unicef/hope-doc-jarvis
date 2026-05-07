"""Tests for hope_jarvis.cli.repo module."""

from unittest.mock import patch

import pytest
from click.testing import CliRunner


@pytest.fixture
def runner():
    """CliRunner fixture."""
    return CliRunner()


class TestRepoGroup:
    """Test repo group command."""

    def test_repo_help(self, runner):
        """Test repo command help."""
        from hope_jarvis.cli.repo import repo

        result = runner.invoke(repo, ["--help"])
        assert result.exit_code == 0
        assert "Git Repositories management" in result.output


class TestPullCommand:
    """Test pull command."""

    def test_pull_all_repos(self, runner):
        """Test pull command with all repos."""
        from hope_jarvis.cli.repo import repo

        with patch("hope_jarvis.cli.repo.get_all_repo_names", return_value=["HOPE", "Aurora"]):
            with patch("hope_jarvis.cli.repo.sync_repo_by_name") as mock_sync:
                mock_sync.return_value = [{"repo_name": "HOPE", "file_path": "test.md"}]

                with patch.dict(
                    "os.environ",
                    {"CONFIG_PATH": "/tmp", "DATA_DIR": "/tmp"},
                ):
                    result = runner.invoke(repo, ["pull"])

                    assert result.exit_code == 0
                    assert "Syncing all repos" in result.output
                    assert mock_sync.call_count == 2

    def test_pull_specific_repos(self, runner):
        """Test pull command with specific repos."""
        from hope_jarvis.cli.repo import repo

        with patch("hope_jarvis.cli.repo.sync_repo_by_name") as mock_sync:
            mock_sync.return_value = []

            with patch.dict(
                "os.environ",
                {"CONFIG_PATH": "/tmp", "DATA_DIR": "/tmp"},
            ):
                result = runner.invoke(repo, ["pull", "-r", "HOPE", "-r", "Aurora"])

                assert result.exit_code == 0
                assert "HOPE" in result.output
                assert "Aurora" in result.output
                assert mock_sync.call_count == 2

    def test_pull_with_force_flag(self, runner):
        """Test pull command with force flag."""
        from hope_jarvis.cli.repo import repo

        with patch("hope_jarvis.cli.repo.get_all_repo_names", return_value=["HOPE"]):
            with patch("hope_jarvis.cli.repo.sync_repo_by_name") as mock_sync:
                mock_sync.return_value = []

                with patch.dict(
                    "os.environ",
                    {"CONFIG_PATH": "/tmp", "DATA_DIR": "/tmp"},
                ):
                    result = runner.invoke(repo, ["pull", "--force"])

                    assert result.exit_code == 0
                    assert "force" in result.output
                    mock_sync.assert_called_with("HOPE", force=True)

    def test_pull_no_files(self, runner):
        """Test pull command with no files changed."""
        from hope_jarvis.cli.repo import repo

        with patch("hope_jarvis.cli.repo.get_all_repo_names", return_value=["HOPE"]):
            with patch("hope_jarvis.cli.repo.sync_repo_by_name", return_value=[]):
                with patch.dict(
                    "os.environ",
                    {"CONFIG_PATH": "/tmp", "DATA_DIR": "/tmp"},
                ):
                    result = runner.invoke(repo, ["pull"])

                    assert result.exit_code == 0
                    assert "No files to process" in result.output

    def test_pull_help(self, runner):
        """Test pull command help."""
        from hope_jarvis.cli.repo import repo

        result = runner.invoke(repo, ["pull", "--help"])
        assert result.exit_code == 0
        assert "Sync repos" in result.output
        assert "Examples:" in result.output
