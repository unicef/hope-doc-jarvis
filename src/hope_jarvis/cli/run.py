"""CLI commands for running services."""

import re
import subprocess
from pathlib import Path

import click


def parse_host_port(bind_str, default_port):
    """Parse host[:port] string.

    Args:
        bind_str: String in format host[:port] (e.g., "localhost:8000", "localhost", ":8000")
        default_port: Default port to use if not specified in bind_str

    Returns:
        Tuple of (host, port)

    """
    if not bind_str:
        return None, default_port

    # Match patterns: host:port, host:, :port, host
    match = re.match(r"^(?:(?P<host>[^:]+))?(?::(?P<port>\d+))?$", bind_str)
    if not match:
        raise click.BadParameter(f"Invalid bind format: {bind_str}. Use host[:port]")

    host = match.group("host") or None
    port_str = match.group("port")

    port = int(port_str) if port_str else default_port

    if port < 1 or port > 65535:
        raise click.BadParameter(f"Invalid port: {port}. Must be between 1 and 65535")

    return host, port


@click.group()
def run():
    """Run Jarvis services."""


@run.command()
@click.option("--bind", "bind_str", default="localhost:8000", help="Host and port to bind to (host[:port]).")
def web(bind_str):
    """Start the Chainlit web interface."""
    host, port = parse_host_port(bind_str, 8000)
    app_path = str(Path(__file__).parent.parent / "app.py")
    cmd = ["chainlit", "run", app_path, "--host", host, "--port", str(port)]
    click.echo(f"Starting Chainlit on {host}:{port}...")
    subprocess.run(cmd, check=False)  # noqa: S603


@run.command()
@click.option("--bind", "bind_str", default="0.0.0.0:9000", help="Host and port to bind to (host[:port]).")
def service(bind_str):
    """Start the webhook server with Uvicorn."""
    import os

    from hope_jarvis.webhook import app

    host, port = parse_host_port(bind_str, 9000)

    webhook_token = os.environ.get("WEBHOOK_TOKEN", "")
    if webhook_token:
        click.echo("Webhook server starting with authentication...")
    else:
        click.echo("Webhook server starting WITHOUT authentication (development mode)...")

    click.echo(f"Listening on {host}:{port}...")
    click.echo(f"  Webhook endpoint: http://{host}:{port}/webhook")
    click.echo(f"  Config endpoint: http://{host}:{port}/config")
    click.echo(f"  Health check: http://{host}:{port}/health")

    import uvicorn

    uvicorn.run(app, host=host, port=port)
