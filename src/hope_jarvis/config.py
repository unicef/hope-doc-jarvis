import os
from pathlib import Path
from typing import Generator


def _require_env(var_name: str) -> str:
    """Get required env var or raise."""
    val = os.environ.get(var_name)
    if val is None:
        raise OSError(f"Missing required env var: {var_name}")
    return val


def _get_env(var_name: str, default: str = None) -> str:
    """Get optional env var with default."""
    return os.environ.get(var_name, default)


# ---------------------------------------------------------------------------
# Ollama settings
# ---------------------------------------------------------------------------


def get_ollama_base_url() -> str:
    hostname = _require_env("OLLAMA_HOST")
    port = _get_env("OLLAMA_PORT", "11434")
    return f"http://{hostname}:{port}"


def get_ollama_model() -> str:
    return _require_env("OLLAMA_MODEL")


def get_ollama_temperature() -> float:
    return float(_get_env("OLLAMA_TEMPERATURE", "0.1"))


def get_ollama_streaming() -> bool:
    return _get_env("OLLAMA_STREAMING", "true").lower() == "true"


# ---------------------------------------------------------------------------
# Repo enumeration
# ---------------------------------------------------------------------------


def get_all_repos() -> Generator[dict]:
    """Return list of all configured repo names."""
    import yaml

    repos_config_path = get_repos_config()
    with open(repos_config_path) as f:
        config = yaml.safe_load(f)

    yield from config["repos"]


def get_repos_config_raw() -> dict:
    """Return raw repos config dict."""
    import yaml

    repos_config_path = get_repos_config()
    with open(repos_config_path) as f:
        return yaml.safe_load(f)


def get_all_repo_names() -> list[str]:
    """Return list of all configured repo names."""
    return [repo_config["name"] for repo_config in get_all_repos()]


# ---------------------------------------------------------------------------
# Qdrant settings
# ---------------------------------------------------------------------------


def get_qdrant_protocol() -> str:
    """Return Qdrant protocol: 'http' or 'grpc'."""
    return _get_env("QDRANT_PROTOCOL", "http").lower()


def get_qdrant_port() -> int:
    """Return Qdrant port based on protocol."""
    protocol = get_qdrant_protocol()
    if protocol == "grpc":
        return int(_get_env("QDRANT_GRPC_PORT", "6334"))
    return int(_get_env("QDRANT_HTTP_PORT", "6333"))


def get_qdrant_url() -> str:
    """Return Qdrant URL for HTTP or config dict for gRPC."""
    host = _require_env("QDRANT_HOST")
    protocol = get_qdrant_protocol()
    port = get_qdrant_port()
    if protocol == "grpc":
        return f"grpc://{host}:{port}"
    return f"http://{host}:{port}"


def get_qdrant_collection_name() -> str:
    return _require_env("QDRANT_COLLECTION_NAME")


def get_qdrant_api_key() -> str | None:
    return _get_env("QDRANT_API_KEY", "") or None


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
    if "DATA_DIR" in os.environ:
        return Path(_require_env("DATA_DIR"))
    return Path("/data")


def get_repos_root_path() -> Path:
    return get_data_path() / "repos"


def get_knowledge_path() -> Path:
    """Path to knowledge base directory for satisfied Q&A."""
    return get_data_path() / "knowledge"


def get_hf_cache_path() -> Path:
    """Get Hugging Face cache directory path."""
    import os

    if "HF_HOME" in os.environ:
        return Path(os.environ["HF_HOME"])
    if "HF_HUB_CACHE" in os.environ:
        return Path(os.environ["HF_HUB_CACHE"])
    return Path.home() / ".cache" / "huggingface"
