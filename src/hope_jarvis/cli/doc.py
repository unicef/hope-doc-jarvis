"""CLI entrypoint for HOPE Jarvis."""

import click

from hope_jarvis.config import (
    get_ingestion_chunk_overlap,
    get_ingestion_chunk_size,
    get_qdrant_collection_name,
    get_qdrant_url,
    get_repos_config,
)
from hope_jarvis.ingestion import sync_all_repos, sync_repo_by_name
from hope_jarvis.ingestion.chunker import chunk_markdown_file
from hope_jarvis.ingestion.store import init_qdrant_collection, store_chunks_in_qdrant


@click.group()
def doc():
    """Git Repositories management"""
    pass


@doc.command()
@click.option(
    "-r",
    "--repo",
    "repos",
    multiple=True,
    help="Repo(s) to sync. Repeatable. Default: all.",
)
@click.option("--force", "force", is_flag=True, help="Force re-ingestion.")
def sync(repos, force):
    """Sync repos and ingest changed files (pull + db update).

    Examples:
      jarvis sync                    # Sync all repos
      jarvis sync -r HOPE            # Sync single repo
      jarvis sync -r HOPE -r Aurora  # Sync multiple repos
      jarvis sync --force            # Force re-sync all repos
    """
    if repos:
        msg = f"Syncing repos: {', '.join(repos)}"
    else:
        msg = "Syncing all repos"
    if force:
        msg += " (force)"
    click.echo(msg)

    chunk_size = get_ingestion_chunk_size()
    chunk_overlap = get_ingestion_chunk_overlap()
    qdrant_url = get_qdrant_url()
    collection_name = get_qdrant_collection_name()

    # Ensure collection exists
    click.echo(f"Initialising Qdrant collection: {collection_name}")
    init_qdrant_collection()

    # Pull repos
    if repos:
        changed_files = []
        for repo_name in repos:
            click.echo(f"Syncing repo: {repo_name}")
            changed = sync_repo_by_name(repo_name, force=force)
            changed_files.extend(changed)
    else:
        changed_files = sync_all_repos(force=force)

    click.echo(f"Found {len(changed_files)} changed files.")

    if not changed_files:
        click.echo("No files to process.")
        return

    # Ingest into Qdrant
    all_chunks = []
    for file_info in changed_files:
        click.echo(f"Processing {file_info['repo_name']}/{file_info['file_path']}...")
        chunks = chunk_markdown_file(
            file_path=file_info["full_path"],
            relative_file_path=file_info["file_path"],
            repo_name=file_info["repo_name"],
            github_url=file_info["github_url"],
            rendered_base_url=file_info["rendered_base_url"],
            docs_dir=file_info["docs_dir"],
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            branch=file_info.get("branch", "main"),
        )
        click.echo(f"  Created {len(chunks)} chunks.")
        all_chunks.extend(chunks)

    if not all_chunks:
        click.echo(
            "No chunks created. Check if markdown files exist in docs directories."
        )
        return

    click.echo(f"Storing {len(all_chunks)} chunks in Qdrant...")
    store_chunks_in_qdrant(
        chunks=all_chunks,
        qdrant_url=qdrant_url,
        collection_name=collection_name,
    )

    click.echo("✅ Sync complete!")


@doc.command()
def info():
    """List all configured repositories."""
    import yaml

    repos_config_path = get_repos_config()
    with open(repos_config_path, "r") as f:
        config = yaml.safe_load(f)

    click.echo("Configured repositories:")
    click.echo("=" * 60)
    for repo in config.get("repos", []):
        click.echo(f"Name: {repo.get('name', 'N/A')}")
        click.echo(f"  URL: {repo.get('github_url', 'N/A')}")
        click.echo(f"  Docs dir: {repo.get('docs_dir', 'N/A')}")
        click.echo(f"  Rendered URL: {repo.get('rendered_base_url', 'N/A')}")
        click.echo("-" * 60)


@doc.command()
def check():
    """Check that all required environment variables are set."""
    required_vars = [
        "OLLAMA_BASE_URL",
        "OLLAMA_MODEL",
        "QDRANT_URL",
        "QDRANT_COLLECTION_NAME",
        "EMBEDDING_MODEL_NAME",
        "CONFIG_PATH",
        "DATA_PATH",
    ]
    missing = []
    import os

    for var in required_vars:
        if not os.environ.get(var):
            missing.append(var)

    if missing:
        click.echo("❌ Missing environment variables:")
        for var in missing:
            click.echo(f"  - {var}")
        raise SystemExit(1)
    else:
        click.echo("✅ All environment variables are set.")
