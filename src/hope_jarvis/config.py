"""12-Factor App configuration.
All config from environment variables. No YAML files for config.
"""

import os
from pathlib import Path
from typing import Generator

import yaml


def _require_env(var_name: str) -> str:
    """Get required env var or raise."""
    val = os.environ.get(var_name)
    if val is None:
        raise EnvironmentError(f"Missing required env var: {var_name}")
    return val


def _get_env(var_name: str, default: str = None) -> str:
    """Get optional env var with default."""
    return os.environ.get(var_name, default)


# ---------------------------------------------------------------------------
# Ollama settings
# ---------------------------------------------------------------------------


def get_ollama_base_url() -> str:
    return _require_env("OLLAMA_BASE_URL")


def get_ollama_model() -> str:
    return _require_env("OLLAMA_MODEL")


def get_ollama_temperature() -> float:
    return float(_get_env("OLLAMA_TEMPERATURE", "0.1"))


def get_ollama_streaming() -> bool:
    return _get_env("OLLAMA_STREAMING", "true").lower() == "true"


# ---------------------------------------------------------------------------
# Qdrant settings
# ---------------------------------------------------------------------------


def get_qdrant_url() -> str:
    return _require_env("QDRANT_URL")


def get_qdrant_collection_name() -> str:
    return _require_env("QDRANT_COLLECTION_NAME")


def get_qdrant_api_key() -> str:
    return _get_env("QDRANT_API_KEY", "")


# ---------------------------------------------------------------------------
# Embedding settings
# ---------------------------------------------------------------------------


def get_embedding_model_name() -> str:
    return _require_env("EMBEDDING_MODEL_NAME")


def get_embedding_vector_size() -> int:
    return int(_get_env("EMBEDDING_VECTOR_SIZE", "384"))


# ---------------------------------------------------------------------------
# Retrieval settings
# ---------------------------------------------------------------------------


def get_retrieval_top_k() -> int:
    return int(_get_env("RETRIEVAL_TOP_K", "5"))


def get_retrieval_score_threshold() -> float:
    return float(_get_env("RETRIEVAL_SCORE_THRESHOLD", "0.5"))


# ---------------------------------------------------------------------------
# Ingestion settings
# ---------------------------------------------------------------------------


def get_ingestion_chunk_size() -> int:
    return int(_get_env("INGESTION_CHUNK_SIZE", "1000"))


def get_ingestion_chunk_overlap() -> int:
    return int(_get_env("INGESTION_CHUNK_OVERLAP", "200"))


# ---------------------------------------------------------------------------
# Paths (from CONFIG_PATH env var)
# ---------------------------------------------------------------------------


def get_config_path() -> Path:
    """Get base config directory from CONFIG_PATH env var."""
    return Path(_require_env("CONFIG_PATH"))


def get_repos_config() -> Path:
    """Path to repos.yaml (still used for repo list)."""
    return get_config_path() / "repos.yaml"


def get_sync_state_path() -> Path:
    """Path to sync_state.json."""
    return get_config_path() / "sync_state.json"


def get_data_path() -> Path:
    """Base data directory for repos (sibling of config dir)."""
    if "DATA_PATH" in os.environ:
        return Path(_require_env("DATA_PATH"))
    return Path("/jarvis/app")


def get_all_repos() -> Generator[str, None, None]:
    repos_config_path = get_repos_config()
    with open(repos_config_path, "r") as f:
        config = yaml.safe_load(f)

    for repo_config in config["repos"]:
        yield repo_config["name"]
