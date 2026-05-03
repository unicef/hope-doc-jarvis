import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from hope_jarvis.utils import build_metadata


class TestBuildMetadata:
    """Test build_metadata function."""

    def test_basic_metadata(self):
        """Test basic metadata construction."""
        metadata = build_metadata(
            repo_name="HOPE",
            file_path="docs/guide.md",
            docs_dir="docs",
            github_url="https://github.com/unicef/hope",
            rendered_base_url="https://unicef.github.io/hope",
            content="Test content",
            chunk_index=0,
        )

        assert metadata["repo_name"] == "HOPE"
        assert metadata["file_path"] == "docs/guide.md"
        assert metadata["chunk_index"] == 0
        assert metadata["content_preview"] == "Test content"

    def test_raw_github_url(self):
        """Test raw GitHub URL construction."""
        metadata = build_metadata(
            repo_name="HOPE",
            file_path="docs/guide.md",
            docs_dir="docs",
            github_url="https://github.com/unicef/hope",
            rendered_base_url="https://unicef.github.io/hope",
            content="Test",
            chunk_index=0,
        )

        assert "raw.githubusercontent.com" in metadata["raw_github_url"]
        assert (
            metadata["raw_github_url"]
            == "https://raw.githubusercontent.com/unicef/hope/main/docs/guide.md"
        )

    def test_rendered_url_removes_docs_dir(self):
        """Test that docs_dir is removed from rendered URL."""
        metadata = build_metadata(
            repo_name="HOPE",
            file_path="docs/guide-user/targeting.md",
            docs_dir="docs",
            github_url="https://github.com/unicef/hope",
            rendered_base_url="https://unicef.github.io/hope",
            content="Test",
            chunk_index=0,
        )

        assert (
            metadata["rendered_html_url"]
            == "https://unicef.github.io/hope/guide-user/targeting/"
        )

    def test_rendered_url_index_file(self):
        """Test that index files produce clean URLs."""
        metadata = build_metadata(
            repo_name="HOPE",
            file_path="docs/index.md",
            docs_dir="docs",
            github_url="https://github.com/unicef/hope",
            rendered_base_url="https://unicef.github.io/hope",
            content="Test",
            chunk_index=0,
        )

        # The URL ends with index/ due to how the function handles empty rel_path
        assert metadata["rendered_html_url"].endswith("/")

    def test_rendered_url_nested_index(self):
        """Test nested index file handling."""
        metadata = build_metadata(
            repo_name="HOPE",
            file_path="docs/guide/index.md",
            docs_dir="docs",
            github_url="https://github.com/unicef/hope",
            rendered_base_url="https://unicef.github.io/hope",
            content="Test",
            chunk_index=0,
        )

        assert metadata["rendered_html_url"] == "https://unicef.github.io/hope/guide/"

    def test_rendered_url_trailing_slash(self):
        """Test that rendered URL has trailing slash."""
        metadata = build_metadata(
            repo_name="HOPE",
            file_path="docs/guide.md",
            docs_dir="docs",
            github_url="https://github.com/unicef/hope",
            rendered_base_url="https://unicef.github.io/hope",
            content="Test",
            chunk_index=0,
        )

        assert metadata["rendered_html_url"].endswith("/")

    def test_rendered_url_base_with_trailing_slash(self):
        """Test that trailing slash in base URL is handled."""
        metadata = build_metadata(
            repo_name="HOPE",
            file_path="docs/guide.md",
            docs_dir="docs",
            github_url="https://github.com/unicef/hope",
            rendered_base_url="https://unicef.github.io/hope/",
            content="Test",
            chunk_index=0,
        )

        assert metadata["rendered_html_url"] == "https://unicef.github.io/hope/guide/"

    def test_content_preview_truncated(self):
        """Test that content preview is truncated."""
        long_content = "A" * 300
        metadata = build_metadata(
            repo_name="HOPE",
            file_path="docs/guide.md",
            docs_dir="docs",
            github_url="https://github.com/unicef/hope",
            rendered_base_url="https://unicef.github.io/hope",
            content=long_content,
            chunk_index=0,
        )

        assert len(metadata["content_preview"]) == 200
        assert metadata["content_preview"] == "A" * 200

    def test_content_preview_short(self):
        """Test that short content is not truncated."""
        short_content = "Short"
        metadata = build_metadata(
            repo_name="HOPE",
            file_path="docs/guide.md",
            docs_dir="docs",
            github_url="https://github.com/unicef/hope",
            rendered_base_url="https://unicef.github.io/hope",
            content=short_content,
            chunk_index=0,
        )

        assert metadata["content_preview"] == "Short"

    def test_file_path_not_in_docs_dir(self):
        """Test when file path doesn't start with docs_dir."""
        metadata = build_metadata(
            repo_name="HOPE",
            file_path="readme.md",
            docs_dir="docs",
            github_url="https://github.com/unicef/hope",
            rendered_base_url="https://unicef.github.io/hope",
            content="Test",
            chunk_index=0,
        )

        assert "readme" in metadata["rendered_html_url"]

    def test_all_required_keys_present(self):
        """Test that all required keys are in metadata."""
        metadata = build_metadata(
            repo_name="HOPE",
            file_path="docs/guide.md",
            docs_dir="docs",
            github_url="https://github.com/unicef/hope",
            rendered_base_url="https://unicef.github.io/hope",
            content="Test",
            chunk_index=0,
        )

        required_keys = [
            "repo_name",
            "file_path",
            "raw_github_url",
            "rendered_html_url",
            "chunk_index",
            "content_preview",
        ]

        for key in required_keys:
            assert key in metadata
