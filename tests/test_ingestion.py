import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from hope_jarvis.ingestion import chunk_markdown_file
from hope_jarvis.ingestion.sync import (
    clone_or_pull_repo,
    find_markdown_files,
    get_file_hash,
)
from hope_jarvis.utils import build_metadata


def test_chunk_markdown_file():
    """Test markdown chunking with metadata."""
    test_content = """# Title

Some content here.

## Section 1

Content for section 1.

### Subsection

More content.

## Section 2

Content for section 2.
"""
    test_file = Path("/tmp/test_doc.md")
    test_file.write_text(test_content)

    try:
        chunks = chunk_markdown_file(
            file_path=str(test_file),
            relative_file_path="guide-user/targeting.md",
            repo_name="HOPE",
            github_url="https://github.com/unicef/hope",
            rendered_base_url="https://unicef.github.io/hope",
            docs_dir="docs",
        )

        assert len(chunks) > 0
        assert all("content" in c for c in chunks)
        assert all("metadata" in c for c in chunks)

        # Check metadata
        chunk = chunks[0]
        assert chunk["metadata"]["repo_name"] == "HOPE"
        assert "rendered_html_url" in chunk["metadata"]
        assert "chunk_index" in chunk["metadata"]
    finally:
        test_file.unlink(missing_ok=True)


def test_chunk_markdown_with_headers():
    """Test that headers are preserved in metadata."""
    test_content = """# User Guide

## Authentication

How to authenticate.

## Permissions

How to set permissions.
"""
    test_file = Path("/tmp/test_headers.md")
    test_file.write_text(test_content)

    try:
        chunks = chunk_markdown_file(
            file_path=str(test_file),
            relative_file_path="guide/user.md",
            repo_name="HOPE",
            github_url="https://github.com/unicef/hope",
            rendered_base_url="https://unicef.github.io/hope",
            docs_dir="docs",
        )

        assert len(chunks) >= 2
        # Check headers are preserved
        assert any("headers" in c["metadata"] for c in chunks)
    finally:
        test_file.unlink(missing_ok=True)


def test_build_metadata_rendered_url():
    """Test that rendered URL is built correctly."""
    metadata = build_metadata(
        repo_name="HOPE",
        file_path="guide-user/targeting.md",
        docs_dir="docs",
        github_url="https://github.com/unicef/hope",
        rendered_base_url="https://unicef.github.io/hope",
        content="Test content",
        chunk_index=0,
    )

    assert (
        metadata["rendered_html_url"]
        == "https://unicef.github.io/hope/guide-user/targeting/"
    )
    assert metadata["repo_name"] == "HOPE"
    assert metadata["file_path"] == "guide-user/targeting.md"


def test_build_metadata_rendered_url_index():
    """Test that index files are handled correctly."""
    metadata = build_metadata(
        repo_name="HOPE",
        file_path="index.md",
        docs_dir="docs",
        github_url="https://github.com/unicef/hope",
        rendered_base_url="https://unicef.github.io/hope",
        content="Test content",
        chunk_index=0,
    )

    assert "index" not in metadata["rendered_html_url"] or metadata[
        "rendered_html_url"
    ].endswith("/")


def test_get_file_hash():
    """Test file hash generation."""
    test_file = Path("/tmp/test_hash.md")
    test_file.write_text("Test content")

    try:
        hash1 = get_file_hash(test_file)
        hash2 = get_file_hash(test_file)

        assert hash1 == hash2
        assert isinstance(hash1, str)
        assert len(hash1) == 32  # MD5 length
    finally:
        test_file.unlink(missing_ok=True)


def test_find_markdown_files(tmp_path):
    """Test finding markdown files in docs directory."""
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()

    # Create test files
    (docs_dir / "readme.md").write_text("# Test")
    (docs_dir / "guide.md").write_text("# Guide")
    (docs_dir / "subdir").mkdir()
    (docs_dir / "subdir" / "nested.md").write_text("# Nested")

    files = find_markdown_files(str(tmp_path), "docs")

    assert len(files) == 3
    assert all(f.suffix == ".md" for f in files)


@patch("hope_jarvis.ingestion.sync.Repo")
def test_clone_or_pull_repo_existing(mock_repo):
    """Test pulling existing repo."""
    mock_repo.return_value.remotes.origin.pull.return_value = None

    with patch("hope_jarvis.config._require_env", return_value="/tmp/test_data"):
        with patch("pathlib.Path.exists", return_value=True):
            result = clone_or_pull_repo(
                {"github_url": "https://github.com/test/repo", "name": "test"}
            )

            assert result is not None


def test_chunk_markdown_large_content():
    """Test chunking of large content."""
    # Create content larger than chunk_size
    test_content = "# Title\n\n" + "Large content. " * 500
    test_file = Path("/tmp/test_large.md")
    test_file.write_text(test_content)

    try:
        chunks = chunk_markdown_file(
            file_path=str(test_file),
            relative_file_path="large.md",
            repo_name="HOPE",
            github_url="https://github.com/unicef/hope",
            rendered_base_url="https://unicef.github.io/hope",
            docs_dir="docs",
            chunk_size=200,
            chunk_overlap=50,
        )

        assert len(chunks) > 1  # Should be split
        # Check overlap
        assert all("chunk_index" in c["metadata"] for c in chunks)
    finally:
        test_file.unlink(missing_ok=True)
