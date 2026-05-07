FROM python:3.13-slim


# Install git for repo cloning
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Copy all needed files for the build
WORKDIR /jarvis
COPY pyproject.toml uv.lock ./
COPY .python-version ./
COPY README.md ./
COPY src/ ./src/
COPY docker/app ./app

WORKDIR /jarvis/app

# Install uv and dependencies
RUN pip install uv && uv sync --frozen --no-dev

# Pre-download embedding model to cache in image
# RUN python -c "from fastembed import TextEmbedding; TextEmbedding(model_name='sentence-transformers/all-MiniLM-L6-v2')"

ENV DATA_DIR=/data
ENV HF_HOME=${DATA_DIR}/hf_cache
ENV HF_HUB_DISABLE_TELEMETRY=0
ENV QDRANT_PROTOCOL=http
ENV EMBEDDING_MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2
ENV CONFIG_PATH=/jarvis/app/config
ENV CHAINLIT_APP_ROOT=/jarvis/app/

# Set PATH to include venv binaries
ENV PATH="/jarvis/.venv/bin:$PATH"

# Expose Chainlit and Webhook ports
EXPOSE 8000 9000

# Run using startup script

CMD ["/jarvis/app/start.sh"]
