"""Tests for hope_jarvis.cli.kb module."""

import sys
from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from hope_jarvis.cli.kb import kb


class TestKbGroup:
    """Test kb group command."""

    def test_kb_help(self):
        """Test kb command help."""
        runner = CliRunner()
        result = runner.invoke(kb, ["--help"])
        assert result.exit_code == 0
        assert "Knowledge Base" in result.output


class TestListCommand:
    """Test list command."""

    def test_list_help(self):
        """Test list command help."""
        runner = CliRunner()
        result = runner.invoke(kb, ["list", "--help"])
        assert result.exit_code == 0

    def test_list_directory_not_exists(self, tmp_path):
        """Test list when knowledge dir doesn't exist."""
        runner = CliRunner()

        with patch("hope_jarvis.cli.kb.get_knowledge_path", return_value=tmp_path / "nonexistent"):
            result = runner.invoke(kb, ["list"])
            assert result.exit_code == 0
            assert "does not exist" in result.output

    def test_list_empty(self, tmp_path):
        """Test list when knowledge dir is empty."""
        runner = CliRunner()

        with patch("hope_jarvis.cli.kb.list_knowledge_files", return_value=[]):
            with patch("hope_jarvis.cli.kb.get_knowledge_path", return_value=tmp_path):
                result = runner.invoke(kb, ["list"])
                assert result.exit_code == 0
                assert "empty" in result.output.lower()

    def test_list_with_entries(self, tmp_path):
        """Test list with entries."""
        runner = CliRunner()
        mock_files = [Path("test-qa.md")]

        with patch("hope_jarvis.cli.kb.list_knowledge_files", return_value=mock_files):
            with patch("hope_jarvis.cli.kb.get_knowledge_path", return_value=tmp_path):
                result = runner.invoke(kb, ["list"])
                assert result.exit_code == 0
                assert "Knowledge base entries" in result.output
                assert "test-qa" in result.output

    def test_list_with_error_reading_file(self, tmp_path):
        """Test list when file can't be read."""
        runner = CliRunner()
        mock_files = [Path("bad.md")]

        def fail_open(path, *args, **kwargs):
            raise PermissionError("Access denied")

        with patch("hope_jarvis.cli.kb.list_knowledge_files", return_value=mock_files):
            with patch("hope_jarvis.cli.kb.get_knowledge_path", return_value=tmp_path):
                with patch("builtins.open", side_effect=fail_open):
                    result = runner.invoke(kb, ["list"])
                    assert result.exit_code == 0
                    assert "error reading file" in result.output.lower()

    def test_list_multiple_entries(self, tmp_path):
        """Test list with multiple entries sorted."""
        runner = CliRunner()
        mock_files = [Path("a-qa.md"), Path("b-qa.md")]

        with patch("hope_jarvis.cli.kb.list_knowledge_files", return_value=mock_files):
            with patch("hope_jarvis.cli.kb.get_knowledge_path", return_value=tmp_path):
                result = runner.invoke(kb, ["list"])
                assert result.exit_code == 0
                assert "(2)" in result.output


class TestResetCommand:
    """Test reset command."""

    def test_reset_help(self):
        """Test reset command help."""
        runner = CliRunner()
        result = runner.invoke(kb, ["reset", "--help"])
        assert result.exit_code == 0

    def test_reset_aborted(self, tmp_path):
        """Test reset when user aborts."""
        runner = CliRunner()

        with patch("hope_jarvis.cli.kb.reset_knowledge_base", return_value=0):
            result = runner.invoke(kb, ["reset"], input="n\n")
            assert result.exit_code == 0
            assert "Aborted" in result.output

    def test_reset_no_input(self, tmp_path):
        """Test reset with --no-input flag."""
        runner = CliRunner()

        with patch("hope_jarvis.cli.kb.reset_knowledge_base", return_value=1):
            result = runner.invoke(kb, ["reset", "--no-input"])
            assert result.exit_code == 0
            assert "Deleted" in result.output

    def test_reset_confirmed(self, tmp_path):
        """Test reset when user confirms."""
        runner = CliRunner()

        with patch("hope_jarvis.cli.kb.reset_knowledge_base", return_value=1):
            result = runner.invoke(kb, ["reset"], input="y\n")
            assert result.exit_code == 0
            assert "Deleted" in result.output

    def test_reset_error(self, tmp_path):
        """Test reset when error occurs."""
        runner = CliRunner()

        with patch("hope_jarvis.cli.kb.reset_knowledge_base", side_effect=Exception("Disk error")):
            result = runner.invoke(kb, ["reset", "--no-input"])
            assert result.exit_code == 0
            assert "Error" in result.output
