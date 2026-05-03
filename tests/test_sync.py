import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from hope_jarvis.ingestion.sync import (
    _load_sync_state,
    _process_repo,
    _save_sync_state,
    clone_or_pull_repo,
    find_markdown_files,
    get_file_hash,
    sync_all_repos,
    sync_repo_by_name,
)


class TestGetFileHash:
    """Test get_file_hash function."""

    def test_same_content_same_hash(self, tmp_path):
        """Test that same content produces same hash."""
        file1 = tmp_path / "test.md"
        file1.write_text("test content")

        hash1 = get_file_hash(file1)
        hash2 = get_file_hash(file1)

        assert hash1 == hash2

    def test_different_content_different_hash(self, tmp_path):
        """Test that different content produces different hash."""
        file1 = tmp_path / "test1.md"
        file2 = tmp_path / "test2.md"
        file1.write_text("content 1")
        file2.write_text("content 2")

        hash1 = get_file_hash(file1)
        hash2 = get_file_hash(file2)

        assert hash1 != hash2

    def test_hash_is_hex_string(self, tmp_path):
        """Test that hash is a hex string."""
        file1 = tmp_path / "test.md"
        file1.write_text("test")

        hash_val = get_file_hash(file1)

        assert isinstance(hash_val, str)
        assert len(hash_val) == 32
        assert all(c in "0123456789abcdef" for c in hash_val)

    def test_empty_file_hash(self, tmp_path):
        """Test hashing empty file."""
        file1 = tmp_path / "empty.md"
        file1.write_text("")

        hash_val = get_file_hash(file1)

        assert isinstance(hash_val, str)
        assert len(hash_val) == 32


class TestFindMarkdownFiles:
    """Test find_markdown_files function."""

    def test_finds_md_files(self, tmp_path):
        """Test finding markdown files."""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        (docs_dir / "readme.md").write_text("# Readme")
        (docs_dir / "guide.md").write_text("# Guide")

        files = find_markdown_files(str(tmp_path), "docs")

        assert len(files) == 2

    def test_finds_nested_md_files(self, tmp_path):
        """Test finding markdown files in nested directories."""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        subdir = docs_dir / "subdir"
        subdir.mkdir()
        (docs_dir / "readme.md").write_text("# Readme")
        (subdir / "nested.md").write_text("# Nested")

        files = find_markdown_files(str(tmp_path), "docs")

        assert len(files) == 2

    def test_ignores_non_md_files(self, tmp_path):
        """Test that non-markdown files are ignored."""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        (docs_dir / "readme.md").write_text("# Readme")
        (docs_dir / "readme.txt").write_text("Readme")
        (docs_dir / "image.png").write_text("binary")

        files = find_markdown_files(str(tmp_path), "docs")

        assert len(files) == 1
        assert files[0].name == "readme.md"

    def test_returns_empty_if_docs_dir_missing(self, tmp_path):
        """Test that empty list is returned if docs dir doesn't exist."""
        files = find_markdown_files(str(tmp_path), "nonexistent")

        assert files == []


class TestCloneOrPullRepo:
    """Test clone_or_pull_repo function."""

    @patch("hope_jarvis.ingestion.sync.get_data_path")
    @patch("hope_jarvis.ingestion.sync.Repo")
    def test_clones_new_repo(self, mock_repo_class, mock_get_data_path, tmp_path):
        """Test cloning a new repository."""
        data_path = tmp_path / "data"
        data_path.mkdir()
        mock_get_data_path.return_value = data_path

        with patch.object(Path, "exists", return_value=False):
            clone_or_pull_repo(
                {
                    "github_url": "https://github.com/test/repo",
                    "name": "test-repo",
                }
            )

            mock_repo_class.clone_from.assert_called_once()

    @patch("hope_jarvis.ingestion.sync.get_data_path")
    @patch("hope_jarvis.ingestion.sync.Repo")
    def test_pulls_existing_repo(self, mock_repo_class, mock_get_data_path, tmp_path):
        """Test pulling an existing repository."""
        data_path = tmp_path / "data"
        data_path.mkdir()
        mock_get_data_path.return_value = data_path

        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo

        with patch.object(Path, "exists", return_value=True):
            result = clone_or_pull_repo(
                {
                    "github_url": "https://github.com/test/repo",
                    "name": "test-repo",
                }
            )

            mock_repo.remotes.origin.pull.assert_called_once()
            assert result is not None


class TestSyncState:
    """Test sync state functions."""

    def test_load_sync_state_empty(self, tmp_path):
        """Test loading sync state when no file exists."""
        state_path = tmp_path / "sync_state.json"

        with patch(
            "hope_jarvis.ingestion.sync.get_sync_state_path", return_value=state_path
        ):
            state = _load_sync_state()

            assert state == {}

    def test_load_sync_state_existing(self, tmp_path):
        """Test loading existing sync state."""
        state_path = tmp_path / "sync_state.json"
        state_data = {"repo/file.md": "hash123"}
        state_path.write_text(json.dumps(state_data))

        with patch(
            "hope_jarvis.ingestion.sync.get_sync_state_path", return_value=state_path
        ):
            state = _load_sync_state()

            assert state == state_data

    def test_save_sync_state(self, tmp_path):
        """Test saving sync state."""
        state_path = tmp_path / "sync_state.json"
        state_data = {"repo/file.md": "hash123"}

        with patch(
            "hope_jarvis.ingestion.sync.get_sync_state_path", return_value=state_path
        ):
            _save_sync_state(state_data)

            loaded = json.loads(state_path.read_text())
            assert loaded == state_data


class TestProcessRepo:
    """Test _process_repo function."""

    def test_detects_changed_files(self, tmp_path):
        """Test that changed files are detected."""
        repo_path = tmp_path / "repo"
        docs_dir = repo_path / "docs"
        docs_dir.mkdir(parents=True)
        md_file = docs_dir / "test.md"
        md_file.write_text("# Test")

        repo_config = {
            "name": "test-repo",
            "github_url": "https://github.com/test/repo",
            "rendered_base_url": "https://test.github.io",
            "docs_dir": "docs",
        }

        with patch(
            "hope_jarvis.ingestion.sync.clone_or_pull_repo", return_value=str(repo_path)
        ):
            changed = _process_repo(repo_config, sync_state={}, force=False)

            assert len(changed) == 1
            assert changed[0]["repo_name"] == "test-repo"
            assert changed[0]["file_path"] == "docs/test.md"

    def test_force_reprocesses_all(self, tmp_path):
        """Test that force flag reprocesses all files."""
        repo_path = tmp_path / "repo"
        docs_dir = repo_path / "docs"
        docs_dir.mkdir(parents=True)
        md_file = docs_dir / "test.md"
        md_file.write_text("# Test")

        repo_config = {
            "name": "test-repo",
            "github_url": "https://github.com/test/repo",
            "rendered_base_url": "https://test.github.io",
            "docs_dir": "docs",
        }

        sync_state = {"test-repo/docs/test.md": "existing_hash"}

        with patch(
            "hope_jarvis.ingestion.sync.clone_or_pull_repo", return_value=str(repo_path)
        ):
            changed = _process_repo(repo_config, sync_state=sync_state, force=True)

            assert len(changed) == 1

    def test_skips_unchanged_files(self, tmp_path):
        """Test that unchanged files are skipped."""
        repo_path = tmp_path / "repo"
        docs_dir = repo_path / "docs"
        docs_dir.mkdir(parents=True)
        md_file = docs_dir / "test.md"
        md_file.write_text("# Test")

        from hope_jarvis.ingestion.sync import get_file_hash

        file_hash = get_file_hash(md_file)

        repo_config = {
            "name": "test-repo",
            "github_url": "https://github.com/test/repo",
            "rendered_base_url": "https://test.github.io",
            "docs_dir": "docs",
        }

        sync_state = {"test-repo/docs/test.md": file_hash}

        with patch(
            "hope_jarvis.ingestion.sync.clone_or_pull_repo", return_value=str(repo_path)
        ):
            changed = _process_repo(repo_config, sync_state=sync_state, force=False)

            assert len(changed) == 0

    def test_raises_error_if_no_docs_dir(self, tmp_path):
        """Test that error is raised if docs_dir is missing."""
        repo_config = {
            "name": "test-repo",
            "github_url": "https://github.com/test/repo",
            "rendered_base_url": "https://test.github.io",
        }

        with patch(
            "hope_jarvis.ingestion.sync.clone_or_pull_repo", return_value=str(tmp_path)
        ):
            try:
                _process_repo(repo_config, sync_state={}, force=False)
                assert False, "Should have raised ValueError"
            except ValueError as e:
                assert "docs_dir" in str(e)


class TestSyncAllRepos:
    """Test sync_all_repos function."""

    def test_syncs_all_repos(self, tmp_path):
        """Test syncing all repositories."""
        repos_config_path = tmp_path / "repos.yaml"
        repos_config_path.write_text("""
repos:
  - name: repo1
    github_url: https://github.com/test/repo1
    docs_dir: docs
    rendered_base_url: https://test.github.io/repo1
""")

        with patch(
            "hope_jarvis.ingestion.sync.get_repos_config",
            return_value=repos_config_path,
        ):
            with patch(
                "hope_jarvis.ingestion.sync.get_data_path",
                return_value=tmp_path / "data",
            ):
                with patch(
                    "hope_jarvis.ingestion.sync.get_sync_state_path",
                    return_value=tmp_path / "sync_state.json",
                ):
                    with patch(
                        "hope_jarvis.ingestion.sync.clone_or_pull_repo",
                        return_value=str(tmp_path),
                    ):
                        with patch(
                            "hope_jarvis.ingestion.sync.find_markdown_files",
                            return_value=[],
                        ):
                            result = sync_all_repos()

                            assert result == []

    def test_syncs_multiple_repos(self, tmp_path):
        """Test syncing multiple repositories."""
        repos_config_path = tmp_path / "repos.yaml"
        repos_config_path.write_text("""
repos:
  - name: repo1
    github_url: https://github.com/test/repo1
    docs_dir: docs
    rendered_base_url: https://test.github.io/repo1
  - name: repo2
    github_url: https://github.com/test/repo2
    docs_dir: docs
    rendered_base_url: https://test.github.io/repo2
""")

        repo1_docs = tmp_path / "data" / "repo1" / "docs"
        repo1_docs.mkdir(parents=True)
        (repo1_docs / "test.md").write_text("# Test")

        repo2_docs = tmp_path / "data" / "repo2" / "docs"
        repo2_docs.mkdir(parents=True)
        (repo2_docs / "test.md").write_text("# Test")

        with patch(
            "hope_jarvis.ingestion.sync.get_repos_config",
            return_value=repos_config_path,
        ):
            with patch(
                "hope_jarvis.ingestion.sync.get_data_path",
                return_value=tmp_path / "data",
            ):
                with patch(
                    "hope_jarvis.ingestion.sync.get_sync_state_path",
                    return_value=tmp_path / "sync_state.json",
                ):
                    with patch("hope_jarvis.ingestion.sync.Repo"):
                        result = sync_all_repos()

                        # Should find 2 files from 2 repos
                        assert len(result) == 2


class TestSyncRepoByName:
    """Test sync_repo_by_name function."""

    def test_syncs_specific_repo(self, tmp_path):
        """Test syncing a specific repository by name."""
        repos_config_path = tmp_path / "repos.yaml"
        repos_config_path.write_text("""
repos:
  - name: HOPE
    github_url: https://github.com/test/hope
    docs_dir: docs
    rendered_base_url: https://test.github.io/hope
  - name: AURORA
    github_url: https://github.com/test/aurora
    docs_dir: docs
    rendered_base_url: https://test.github.io/aurora
""")

        with patch(
            "hope_jarvis.ingestion.sync.get_repos_config",
            return_value=repos_config_path,
        ):
            with patch(
                "hope_jarvis.ingestion.sync.get_data_path",
                return_value=tmp_path / "data",
            ):
                with patch(
                    "hope_jarvis.ingestion.sync.get_sync_state_path",
                    return_value=tmp_path / "sync_state.json",
                ):
                    with patch(
                        "hope_jarvis.ingestion.sync.clone_or_pull_repo",
                        return_value=str(tmp_path),
                    ):
                        with patch(
                            "hope_jarvis.ingestion.sync.find_markdown_files",
                            return_value=[],
                        ):
                            result = sync_repo_by_name("HOPE")

                            assert result == []

    def test_returns_empty_for_nonexistent_repo(self, tmp_path):
        """Test that empty list is returned for non-existent repo."""
        repos_config_path = tmp_path / "repos.yaml"
        repos_config_path.write_text("""
repos:
  - name: HOPE
    github_url: https://github.com/test/hope
    docs_dir: docs
    rendered_base_url: https://test.github.io/hope
""")

        with patch(
            "hope_jarvis.ingestion.sync.get_repos_config",
            return_value=repos_config_path,
        ):
            with patch(
                "hope_jarvis.ingestion.sync.get_data_path",
                return_value=tmp_path / "data",
            ):
                with patch(
                    "hope_jarvis.ingestion.sync.get_sync_state_path",
                    return_value=tmp_path / "sync_state.json",
                ):
                    result = sync_repo_by_name("NONEXISTENT")

                    assert result == []
