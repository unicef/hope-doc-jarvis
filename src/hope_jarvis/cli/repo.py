"""CLI entrypoint for HOPE Jarvis."""

import click

from hope_jarvis.ingestion import sync_all_repos, sync_repo_by_name


@click.group()
def repo():
    """Git Repositories management"""
    pass


@repo.command()
@click.option(
    "-r",
    "--repo",
    "repos",
    multiple=True,
    help="Repo(s) to sync. Repeatable. Default: all.",
)
@click.option("--force", "force", is_flag=True, help="Force re-ingestion.")
def pull(repos, force):
    """Sync repos and ingest changed files (pull + db update).

    Examples:
      jarvis repo pull                    # Sync all repos
      jarvis repo pull -r HOPE            # Sync single repo
      jarvis repo pull -r HOPE -r Aurora  # Sync multiple repos
      jarvis repo pull --force            # Force re-sync all repos
    """
    if repos:
        msg = f"Syncing repos: {', '.join(repos)}"
    else:
        msg = "Syncing all repos"
    if force:
        msg += " (force)"
    click.echo(msg)

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
