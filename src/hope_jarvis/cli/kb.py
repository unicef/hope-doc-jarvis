"""CLI commands for Knowledge Base management."""

import click

from hope_jarvis.config import get_knowledge_path
from hope_jarvis.knowledge import list_knowledge_files, reset_knowledge_base


@click.group()
def kb():
    """Knowledge Base management (satisfied Q&A pairs)."""


@kb.command(name="list")
def list_knowledge():
    """List all entries in the knowledge base."""
    knowledge_dir = get_knowledge_path()

    if not knowledge_dir.exists():
        click.echo(f"Knowledge base directory does not exist: {knowledge_dir}")
        return

    files = list_knowledge_files()

    if not files:
        click.echo("Knowledge base is empty.")
        return

    click.echo(f"Knowledge base entries ({len(files)}):")
    click.echo("-" * 50)

    for f in files:
        title = f.stem
        try:
            with open(f, encoding="utf-8") as file:
                for line in file:
                    if line.startswith("# "):
                        title = line[2:].strip()
                        break
        except Exception as e:
            click.echo(f"  • {title} (error reading file: {e})")
            continue

        click.echo(f"  • {title}")
        click.echo(f"    File: {f.name}")
        click.echo()


@kb.command()
@click.option("--no-input", is_flag=True, help="Skip confirmation prompt (non-interactive mode).")
def reset(no_input):
    """Delete all entries in the knowledge base."""
    if not no_input and not click.confirm("Are you sure you want to delete all knowledge base entries?"):
        click.echo("Aborted.")
        return

    try:
        count = reset_knowledge_base()
        click.echo(f"✅ Deleted {count} entries from knowledge base.")
    except Exception as e:
        click.echo(f"❌ Error: {e}")
