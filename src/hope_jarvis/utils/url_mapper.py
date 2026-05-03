import re
from typing import Dict


def build_metadata(
    repo_name: str,
    file_path: str,
    docs_dir: str,
    github_url: str,
    rendered_base_url: str,
    content: str,
    chunk_index: int,
    branch: str = "main",
) -> Dict:
    """Build metadata dict for a chunk."""
    # Construct raw GitHub URL with configurable branch
    raw_url = f"{github_url.replace('github.com', 'raw.githubusercontent.com')}/{branch}/{file_path}"

    # Build rendered URL by combining base URL with relative file path
    # Remove docs_dir prefix from file_path if present
    rel_path = file_path
    if rel_path.startswith(docs_dir + "/"):
        rel_path = rel_path[len(docs_dir) + 1 :]

    # Remove .md extension and index files for cleaner URLs
    rel_path = re.sub(r"\.md$", "", rel_path)
    if rel_path == "index" or rel_path.endswith("/index"):
        rel_path = rel_path.rsplit("/index", 1)[0]

    # Build final rendered URL
    rendered_url = rendered_base_url.rstrip("/")
    if rel_path:
        rendered_url += "/" + rel_path
    rendered_url = rendered_url.rstrip("/") + "/"

    return {
        "repo_name": repo_name,
        "file_path": file_path,
        "raw_github_url": raw_url,
        "rendered_html_url": rendered_url,
        "chunk_index": chunk_index,
        "content_preview": content[:200],
    }
