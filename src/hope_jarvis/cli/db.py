"""CLI entrypoint for HOPE Jarvis."""

import click
from qdrant_client import QdrantClient
from qdrant_client.models import FieldCondition, Filter, FilterSelector, MatchValue

from hope_jarvis.config import (
    get_data_path,
    get_ingestion_chunk_overlap,
    get_ingestion_chunk_size,
    get_qdrant_api_key,
    get_qdrant_collection_name,
    get_qdrant_url,
    get_repos_config,
)
from hope_jarvis.ingestion.chunker import chunk_markdown_file
from hope_jarvis.ingestion.store import init_qdrant_collection, store_chunks_in_qdrant
from hope_jarvis.ingestion.sync import find_markdown_files


@click.group()
def db():
    """Database management commands."""
    pass


@db.command()
@click.option(
    "-r",
    "--repo",
    "repos",
    multiple=True,
    help="Repo(s) to update. Repeatable. Default: all.",
)
@click.option("--force", "force", is_flag=True, help="Force re-ingestion.")
def update(repos, force):
    """Update Qdrant database (ingestion only, no git operations).

    Examples:
      jarvis db update                    # Update all repos in Qdrant
      jarvis db update -r HOPE            # Update single repo
      jarvis db update -r HOPE -r Aurora  # Update multiple repos
      jarvis db update --force            # Force re-ingestion
    """
    if repos:
        msg = f"Updating Qdrant for: {', '.join(repos)}"
    else:
        msg = "Updating Qdrant for all repos"
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

    # Get repos to process
    import yaml

    repos_config_path = get_repos_config()
    with open(repos_config_path, "r") as f:
        config = yaml.safe_load(f)

    if repos:
        # Filter repos by name
        repos_to_process = [r for r in config.get("repos", []) if r["name"] in repos]
        if not repos_to_process:
            click.echo(f"❌ No matching repos found for: {', '.join(repos)}")
            return
    else:
        # All repos
        repos_to_process = config.get("repos", [])

    # Process each repo (scan local files, no git pull)
    all_chunks = []
    for repo_config in repos_to_process:
        repo_name = repo_config["name"]
        repo_path = get_data_path() / repo_name
        docs_dir = repo_config.get("docs_dir")

        if not repo_path.exists():
            click.echo(f"⚠️  Repo path not found: {repo_path}. Run 'jarvis pull' first.")
            continue

        click.echo(f"Scanning {repo_name}...")
        md_files = find_markdown_files(str(repo_path), docs_dir)

        for md_file in md_files:
            click.echo(f"  Processing {md_file.relative_to(repo_path)}...")
            chunks = chunk_markdown_file(
                file_path=str(md_file),
                relative_file_path=str(md_file.relative_to(repo_path)),
                repo_name=repo_name,
                github_url=repo_config["github_url"],
                rendered_base_url=repo_config["rendered_base_url"],
                docs_dir=docs_dir,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                branch=repo_config.get("branch", "main"),
            )
            all_chunks.extend(chunks)

    if not all_chunks:
        click.echo("No chunks created. Check if markdown files exist in docs.")
        return

    click.echo(f"Storing {len(all_chunks)} chunks in Qdrant...")
    store_chunks_in_qdrant(
        chunks=all_chunks,
        qdrant_url=qdrant_url,
        collection_name=collection_name,
    )

    click.echo("✅ Database update complete!")


@db.command()
@click.option(
    "-r",
    "--repo",
    "repos",
    multiple=True,
    help="Repo(s) to reset. Repeatable. Default: all.",
)
@click.confirmation_option(prompt="Are you sure you want to delete the data?")
def reset(repos):
    """Reset Qdrant data for repos or entire collection.

    Examples:
      jarvis db reset                    # Reset entire collection
      jarvis db reset -r HOPE            # Reset single repo
      jarvis db reset -r HOPE -r Aurora  # Reset multiple repos
    """
    import yaml

    from hope_jarvis.config import get_repos_config

    qdrant_url = get_qdrant_url()
    collection_name = get_qdrant_collection_name()
    client = QdrantClient(url=qdrant_url, api_key=get_qdrant_api_key())

    if not repos:
        # Reset entire collection
        click.echo(f"Resetting entire collection: {collection_name}")
        client.delete_collection(collection_name=collection_name)
        init_qdrant_collection()
        click.echo("✅ Collection reset complete.")
    else:
        # Reset specific repos
        repos_config_path = get_repos_config()
        with open(repos_config_path, "r") as f:
            config = yaml.safe_load(f)

        for repo_name in repos:
            # Verify repo exists in config
            repo_found = any(r["name"] == repo_name for r in config.get("repos", []))
            if not repo_found:
                click.echo(f"⚠️  Repo '{repo_name}' not found in config. Skipping.")
                continue

            click.echo(f"Resetting data for repo: {repo_name}")
            client.delete(
                collection_name=collection_name,
                points_selector=FilterSelector(
                    filter=Filter(
                        must=[
                            FieldCondition(
                                key="repo_name", match=MatchValue(value=repo_name)
                            )
                        ]
                    )
                ),
            )
            click.echo(f"✅ Reset complete for repo: {repo_name}")


@db.command()
def info():
    """Show Qdrant database information."""
    qdrant_url = get_qdrant_url()
    collection_name = get_qdrant_collection_name()
    client = QdrantClient(url=qdrant_url, api_key=get_qdrant_api_key())

    collections = client.get_collections().collections
    collection_names = [c.name for c in collections]

    if collection_name not in collection_names:
        click.echo(f"❌ Collection '{collection_name}' does not exist.")
        return

    info = client.get_collection(collection_name=collection_name)
    click.echo(f"Collection: {collection_name}")
    click.echo(f"  Status: {info.status}")

    # Handle different Qdrant client versions
    try:
        click.echo(f"  Points: {info.points_count}")
    except AttributeError:
        pass

    try:
        click.echo(f"  Vectors: {info.vectors_count}")
    except AttributeError:
        pass

    try:
        click.echo(f"  Indexed: {info.indexed_vectors_count}")
    except AttributeError:
        pass

    try:
        click.echo(f"  Vector size: {info.config.params.vectors.size}")
        click.echo(f"  Distance: {info.config.params.vectors.distance}")
    except AttributeError:
        pass

    # Count by repo using scroll
    try:
        points, _ = client.scroll(collection_name=collection_name, limit=10000)
        repo_counts = {}
        for p in points:
            repo = p.payload.get("repo_name", "unknown")
            repo_counts[repo] = repo_counts.get(repo, 0) + 1

        click.echo("\nChunks per repo:")
        for repo, count in sorted(repo_counts.items()):
            click.echo(f"  {repo}: {count} chunks")
    except Exception as e:
        click.echo(f"\nError counting chunks: {e}")
