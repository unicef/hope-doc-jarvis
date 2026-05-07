"""Knowledge base module for storing satisfied Q&A pairs."""

import re
from datetime import datetime
from pathlib import Path

from hope_jarvis.config import get_knowledge_path


def slugify(text: str, max_length: int = 100) -> str:
    """Convert text to a valid filename."""
    slug = re.sub(r"[^\w\s-]", "", text.lower())
    slug = re.sub(r"[-\s]+", "-", slug).strip("-")
    return slug[:max_length]


def save_qa_to_markdown(question: str, answer: str, sources: list[dict]) -> Path:
    """Save Q&A pair to markdown file with timestamp."""
    knowledge_dir = get_knowledge_path()
    knowledge_dir.mkdir(parents=True, exist_ok=True)

    slug = slugify(question)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    file_path = knowledge_dir / f"{slug}-{timestamp}.md"

    content = f"# {question}\n\n## Answer\n{answer}\n\n"
    if sources:
        content += "## Sources\n"
        for src in sources:
            content += f"- **{src['app']}**: [{src['url']}]({src['url']}) (score: {src['score']})\n"

    file_path.write_text(content, encoding="utf-8")
    return file_path


def list_knowledge_files() -> list[Path]:
    """List all markdown files in knowledge base."""
    knowledge_dir = get_knowledge_path()
    if not knowledge_dir.exists():
        return []
    return sorted(knowledge_dir.glob("*.md"))


def reset_knowledge_base() -> int:
    """Delete all files in knowledge base. Returns count of deleted files."""
    files = list_knowledge_files()
    count = len(files)
    for f in files:
        f.unlink()
    return count
