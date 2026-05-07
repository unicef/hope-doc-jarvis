"""Webhook server to trigger repo updates."""

import logging
import os
from pathlib import Path

import sentry_sdk
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from hope_jarvis.cli import jarvis

logger = logging.getLogger(__name__)

sentry_dsn = os.environ.get("SENTRY_DSN")
if sentry_dsn:
    sentry_sdk.init(
        dsn=sentry_dsn,
        environment=os.environ.get("ENVIRONMENT", "production"),
        send_default_pii=False,
    )

WEBHOOK_TOKEN = os.environ.get("WEBHOOK_TOKEN", "")
PORT = int(os.environ.get("WEBHOOK_PORT", "9000"))

app = FastAPI(
    title="HOPE Jarvis Webhook",
    description="Webhook server for GitHub events and config API",
)


def _check_auth(authorization: str = None, x_webhook_token: str = None) -> bool:
    """Check if request has valid token."""
    if not WEBHOOK_TOKEN:
        return True  # No token configured, allow all

    # Check Authorization header (Bearer token)
    if authorization and isinstance(authorization, str) and authorization.startswith("Bearer "):
        return authorization.split(" ")[1] == WEBHOOK_TOKEN

    # Check X-Webhook-Token header
    if x_webhook_token and isinstance(x_webhook_token, str):
        return x_webhook_token == WEBHOOK_TOKEN

    return False


@app.post("/webhook")
async def webhook_handler(request: Request):
    """Handle GitHub webhook events."""
    if not _check_auth():
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        body = await request.json()
    except Exception:
        body = {}

    repo_name = body.get("repository", {}).get("name") or body.get("repo")
    if not repo_name:
        raise HTTPException(status_code=400, detail="Missing repo name")

    try:
        from click.testing import CliRunner

        runner = CliRunner()
        result = runner.invoke(jarvis, ["db", "update", "-r", repo_name])
        if result.exit_code != 0:
            raise Exception(result.output)

        logger.info(f"[WEBHOOK] Successfully updated repo: {repo_name}")
        return JSONResponse({"status": "success", "repo": repo_name})

    except Exception as e:
        sentry_sdk.capture_exception(e)
        logger.error(f"[WEBHOOK] Error updating repo {repo_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/config")
async def get_config():
    """Return configuration information."""
    from hope_jarvis.config import (
        get_config_path,
        get_data_path,
        get_embedding_model_name,
        get_knowledge_path,
        get_ollama_base_url,
        get_qdrant_url,
        get_repos_config,
    )

    config = {
        "ollama_base_url": get_ollama_base_url(),
        "qdrant_url": get_qdrant_url(),
        "embedding_model": get_embedding_model_name(),
        "config_path": str(get_config_path()),
        "data_path": str(get_data_path()),
        "knowledge_path": str(get_knowledge_path()),
        "repos_config": str(get_repos_config()),
        "hf_cache": _get_hf_cache_path(),
    }

    # Add repos from config
    try:
        from hope_jarvis.config import get_all_repo_names

        config["repos"] = list(get_all_repo_names())
    except Exception as e:
        config["repos_error"] = str(e)

    return JSONResponse(config)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "webhook"}


def _get_hf_cache_path() -> str:
    """Get Hugging Face cache directory path."""
    if "HF_HOME" in os.environ:
        return os.environ["HF_HOME"]
    if "HF_HUB_CACHE" in os.environ:
        return os.environ["HF_HUB_CACHE"]
    return str(Path.home() / ".cache" / "huggingface")


if __name__ == "__main__":
    import uvicorn

    logger.info(f"Starting webhook server on port {PORT}...")
    uvicorn.run(app, host="0.0.0.0", port=PORT)  # noqa: S104
