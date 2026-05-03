"""CLI entrypoint for HOPE Jarvis."""

import click

from .db import db
from .doc import doc
from .repo import repo


@click.group()
def jarvis():
    """HOPE Jarvis CLI."""
    pass


jarvis.add_command(db)
jarvis.add_command(repo)
jarvis.add_command(doc)
