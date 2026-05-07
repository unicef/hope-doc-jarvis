"""CLI entrypoint for HOPE Jarvis."""

import json
import os
from pathlib import Path
from urllib.request import Request, urlopen

import click

from hope_jarvis.config import get_all_repos, get_ollama_base_url, get_ollama_model, get_qdrant_url, get_repos_config

from .db import db
from .kb import kb
from .repo import repo
from .run import run


@click.group()
def jarvis():
    """HOPE Jarvis CLI."""


def _check_url(url, timeout=3):
    """Check if a URL is reachable. Returns (ok, message)."""
    try:
        req = Request(url, headers={"User-Agent": "jarvis-check"})  # noqa: S310
        with urlopen(req, timeout=timeout) as resp:  # noqa: S310
            return True, f"{resp.status if hasattr(resp, 'status') else resp.getcode()}"
    except Exception as e:
        return False, str(e)


def _check_ollama(base_url):
    """Check Ollama connectivity."""
    url = base_url.rstrip("/") + "/api/tags"
    ok, msg = _check_url(url)
    return ok, f"reachable ({msg}) [URL: {url}]" if ok else f"unreachable: {msg} [URL: {url}]"


def _check_qdrant(qdrant_url, api_key=None):
    """Check Qdrant connectivity."""
    # Try /health first, then /collections as fallback
    for path in ["/health", "/collections"]:
        url = qdrant_url.rstrip("/") + path
        try:
            req = Request(url, headers={"User-Agent": "jarvis-check"})  # noqa: S310
            if api_key:
                req.add_header("api-key", api_key)
            with urlopen(req, timeout=3) as resp:  # noqa: S310
                if path == "/health":
                    data = json.loads(resp.read())
                    if data.get("status") == "ok":
                        return True, f"reachable (healthy) [URL: {url}]"
                    return True, f"reachable (status: {data.get('status')}) [URL: {url}]"
                return True, f"reachable [URL: {url}]"
        except Exception as e:
            last_err = e
    return False, f"unreachable: {last_err} [URL: {url}]"


@jarvis.command()
def check():
    """Show environment variables, services, and directories used by Jarvis."""
    click.echo("=" * 70)
    click.echo("JARVIS CHECK - System Configuration")
    click.echo("=" * 70)

    services = []

    # Ollama
    ollama_url = get_ollama_base_url()
    if ollama_url:
        ok, msg = _check_ollama(ollama_url)
        status = click.style(f"✓ {msg}", fg="green") if ok else click.style(f"✗ {msg}", fg="red")
        services.append(("Ollama (LLM)", status, "LLM inference and embeddings"))
    else:
        services.append(("Ollama (LLM)", click.style("not configured", fg="yellow"), "LLM inference and embeddings"))
    services.append(("Ollama Model", get_ollama_model(), ""))

    # Qdrant
    qdrant_url = get_qdrant_url()
    if qdrant_url:
        api_key = os.environ.get("QDRANT_API_KEY")
        ok, msg = _check_qdrant(qdrant_url, api_key)
        status = click.style(f"✓ {msg}", fg="green") if ok else click.style(f"✗ {msg}", fg="red")
        services.append(("Qdrant (Vector DB)", status, "Vector storage and retrieval"))
    else:
        services.append(
            ("Qdrant (Vector DB)", click.style("not configured", fg="yellow"), "Vector storage and retrieval")
        )

    # Sentry
    sentry_dsn = os.environ.get("SENTRY_DSN")
    if sentry_dsn:
        services.append(("Sentry", click.style("configured", fg="green"), "Error tracking"))
    else:
        services.append(("Sentry", click.style("not configured", fg="yellow"), "Error tracking"))

    # Webhook
    webhook_token = os.environ.get("WEBHOOK_TOKEN")
    webhook_status = "with auth" if webhook_token else "no auth (port 9000)"
    services.append(("Webhook Server", webhook_status, "GitHub webhook receiver"))

    # GitHub Repos
    try:
        repo_count = len(list(get_all_repos()))
        services.append(("GitHub Repositories", f"{repo_count} repos configured", "Documentation sources"))
    except Exception as e:
        services.append(("GitHub Repositories", f"Error: {e}", "Documentation sources"))

    for name, status, description in services:
        click.echo(f"  {name:<25} {description}")
        click.echo(f"    Status: {status}")

    # Directories
    click.echo("\n📁 DIRECTORIES")
    click.echo("-" * 70)

    def rel_path(p):
        """Return path relative to cwd if possible."""
        try:
            return str(Path(p).resolve().relative_to(Path.cwd().resolve()))
        except ValueError:
            return str(p)

    directories = []

    # CONFIG_PATH
    config_path = os.environ.get("CONFIG_PATH")
    if config_path:
        config_dir = os.path.expanduser(config_path)
        exists = os.path.isdir(config_dir)
        directories.append(("CONFIG_PATH", rel_path(config_dir), exists))
    else:
        directories.append(("CONFIG_PATH", "not set", False))

    # DATA_DIR
    data_path = os.environ.get("DATA_DIR")
    if data_path:
        data_dir = os.path.expanduser(data_path)
        exists = os.path.isdir(data_dir)
        directories.append(("DATA_DIR", rel_path(data_dir), exists))
    else:
        directories.append(("DATA_DIR", "not set", False))

    # Repos config file
    try:
        repos_yaml = str(get_repos_config())
        exists = os.path.isfile(repos_yaml)
        directories.append(("repos.yaml", rel_path(repos_yaml), exists))
    except Exception:
        directories.append(("repos.yaml", "not found", False))

    # Sync state file
    try:
        from hope_jarvis.config import get_sync_state_path

        sync_state = str(get_sync_state_path())
        exists = os.path.isfile(sync_state)
        directories.append(("sync_state.json", rel_path(sync_state), exists))
    except Exception:
        directories.append(("sync_state.json", "not found", False))

    for name, path, exists in directories:
        status = click.style("✓ exists", fg="green") if exists else click.style("✗ not found", fg="red")
        click.echo(f"  {name:<25} {path}")
        click.echo(f"    {status}")

    click.echo("\n" + "=" * 70)


jarvis.add_command(db)
jarvis.add_command(repo)
jarvis.add_command(run)
jarvis.add_command(kb)
