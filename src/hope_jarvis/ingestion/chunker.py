"""Markdown chunking module."""

import re
from typing import Any

import yaml
from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)

from hope_jarvis.config import get_ingestion_chunk_overlap, get_ingestion_chunk_size
from hope_jarvis.utils import build_metadata


def _extract_frontmatter(content: str) -> tuple[dict[str, Any], str]:
    """Extract YAML frontmatter from markdown content.

    Args:
        content: Raw markdown content.

    Returns:
        Tuple of (frontmatter dict, content without frontmatter).

    """
    frontmatter = {}
    remaining_content = content

    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            try:
                frontmatter = yaml.safe_load(parts[1]) or {}
            except yaml.YAMLError:
                frontmatter = {}
            remaining_content = parts[2]

    return frontmatter, remaining_content


def _clean_glossary_refs(content: str) -> str:
    """Replace <glossary:TERM> with TERM in content.

    Args:
        content: Markdown content with potential glossary references.

    Returns:
        Content with glossary references replaced by term text.

    """
    return re.sub(r"<glossary:(.*?)>", r"\1", content)


def chunk_markdown_file(
    file_path: str,
    relative_file_path: str,
    repo_name: str,
    github_url: str,
    rendered_base_url: str,
    docs_dir: str,
    chunk_size: int = None,
    chunk_overlap: int = None,
    branch: str = "main",
) -> list[dict[str, Any]]:
    """Chunk a markdown file with header awareness and metadata."""
    if chunk_size is None:
        chunk_size = get_ingestion_chunk_size()
    if chunk_overlap is None:
        chunk_overlap = get_ingestion_chunk_overlap()

    with open(file_path, encoding="utf-8") as f:
        content = f.read()

    frontmatter, content_without_fm = _extract_frontmatter(content)
    content_without_fm = _clean_glossary_refs(content_without_fm)

    headers_to_split_on = [
        ("#", "header_1"),
        ("##", "header_2"),
        ("###", "header_3"),
    ]
    md_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
    md_docs = md_splitter.split_text(content_without_fm)

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
    )

    chunks = []
    for i, doc in enumerate(md_docs):
        # Use relative_file_path if provided, otherwise extract from file_path
        meta_file_path = relative_file_path or file_path.rsplit("/", maxsplit=1)[-1]

        if len(doc.page_content) > chunk_size:
            sub_chunks = text_splitter.split_text(doc.page_content)
            for j, sub_content in enumerate(sub_chunks):
                metadata = build_metadata(
                    repo_name=repo_name,
                    file_path=meta_file_path,
                    docs_dir=docs_dir,
                    github_url=github_url,
                    rendered_base_url=rendered_base_url,
                    content=sub_content,
                    chunk_index=i * 100 + j,
                    branch=branch,
                )
                metadata["headers"] = doc.metadata
                metadata["frontmatter"] = frontmatter
                chunks.append({"content": sub_content, "metadata": metadata})
        else:
            metadata = build_metadata(
                repo_name=repo_name,
                file_path=meta_file_path,
                docs_dir=docs_dir,
                github_url=github_url,
                rendered_base_url=rendered_base_url,
                content=doc.page_content,
                chunk_index=i,
                branch=branch,
            )
            metadata["headers"] = doc.metadata
            metadata["frontmatter"] = frontmatter
            chunks.append({"content": doc.page_content, "metadata": metadata})

    return chunks
