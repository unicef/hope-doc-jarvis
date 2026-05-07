"""Tests for hope_jarvis.knowledge module."""

import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from hope_jarvis.knowledge import (
    list_knowledge_files,
    reset_knowledge_base,
    save_qa_to_markdown,
    slugify,
)


class TestSlugify:
    """Test slugify function."""

    def test_basic_text(self):
        """Test basic text slugification."""
        assert slugify("Hello World") == "hello-world"

    def test_special_characters(self):
        """Test removal of special characters."""
        assert slugify("Hello! @#$World") == "hello-world"

    def test_multiple_spaces(self):
        """Test multiple spaces become single dash."""
        assert slugify("Hello   World") == "hello-world"

    def test_max_length(self):
        """Test max length truncation."""
        long_text = "a" * 200
        result = slugify(long_text)
        assert len(result) == 100

    def test_strip_trailing_dash(self):
        """Test trailing dashes are stripped."""
        assert slugify("Hello World-") == "hello-world"


class TestSaveQaToMarkdown:
    """Test save_qa_to_markdown function."""

    def test_save_qa(self, tmp_path):
        """Test saving Q&A to markdown file."""
        with patch("hope_jarvis.knowledge.get_knowledge_path", return_value=tmp_path):
            file_path = save_qa_to_markdown(
                question="What is Python?",
                answer="Python is a programming language.",
                sources=[],
            )

            assert file_path.exists()
            content = file_path.read_text()
            assert "# What is Python?" in content
            assert "## Answer" in content
            assert "Python is a programming language." in content

    def test_save_qa_with_sources(self, tmp_path):
        """Test saving Q&A with sources."""
        sources = [{"app": "github", "url": "https://github.com/test", "score": 0.95}]

        with patch("hope_jarvis.knowledge.get_knowledge_path", return_value=tmp_path):
            file_path = save_qa_to_markdown(
                question="What is Python?",
                answer="Python is a programming language.",
                sources=sources,
            )

            content = file_path.read_text()
            assert "## Sources" in content
            assert "github" in content
            assert "https://github.com/test" in content

    def test_creates_directory(self, tmp_path):
        """Test that it creates the knowledge directory if needed."""
        nested = tmp_path / "nested" / "knowledge"
        with patch("hope_jarvis.knowledge.get_knowledge_path", return_value=nested):
            file_path = save_qa_to_markdown(
                question="Test question",
                answer="Test answer",
                sources=[],
            )
            assert file_path.exists()


class TestListKnowledgeFiles:
    """Test list_knowledge_files function."""

    def test_empty_directory(self, tmp_path):
        """Test listing when directory is empty."""
        with patch("hope_jarvis.knowledge.get_knowledge_path", return_value=tmp_path):
            files = list_knowledge_files()
            assert files == []

    def test_nonexistent_directory(self):
        """Test listing when directory doesn't exist."""
        nonexistent = Path("/nonexistent/path/that/does/not/exist")
        with patch("hope_jarvis.knowledge.get_knowledge_path", return_value=nonexistent):
            files = list_knowledge_files()
            assert files == []

    def test_returns_sorted_files(self, tmp_path):
        """Test that files are returned sorted."""
        (tmp_path / "b-file.md").write_text("# B")
        (tmp_path / "a-file.md").write_text("# A")

        with patch("hope_jarvis.knowledge.get_knowledge_path", return_value=tmp_path):
            files = list_knowledge_files()
            assert len(files) == 2
            assert files[0].name == "a-file.md"
            assert files[1].name == "b-file.md"

    def test_ignores_non_md_files(self, tmp_path):
        """Test that non-markdown files are ignored."""
        (tmp_path / "test.md").write_text("# Test")
        (tmp_path / "test.txt").write_text("Test")
        (tmp_path / "test.json").write_text("{}")

        with patch("hope_jarvis.knowledge.get_knowledge_path", return_value=tmp_path):
            files = list_knowledge_files()
            assert len(files) == 1
            assert files[0].name == "test.md"


class TestResetKnowledgeBase:
    """Test reset_knowledge_base function."""

    def test_delete_all_files(self, tmp_path):
        """Test deleting all knowledge files."""
        (tmp_path / "file1.md").write_text("# 1")
        (tmp_path / "file2.md").write_text("# 2")
        (tmp_path / "file3.md").write_text("# 3")

        with patch("hope_jarvis.knowledge.get_knowledge_path", return_value=tmp_path):
            count = reset_knowledge_base()

            assert count == 3
            assert list(tmp_path.glob("*.md")) == []

    def test_returns_zero_when_empty(self, tmp_path):
        """Test returns 0 when no files to delete."""
        with patch("hope_jarvis.knowledge.get_knowledge_path", return_value=tmp_path):
            count = reset_knowledge_base()
            assert count == 0

    def test_ignores_non_md_files(self, tmp_path):
        """Test that non-markdown files are not deleted."""
        (tmp_path / "test.md").write_text("# Test")
        (tmp_path / "test.txt").write_text("Keep this")

        with patch("hope_jarvis.knowledge.get_knowledge_path", return_value=tmp_path):
            count = reset_knowledge_base()

            assert count == 1
            assert (tmp_path / "test.txt").exists()
