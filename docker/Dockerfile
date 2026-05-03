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

# Set PATH to include venv binaries
ENV PATH="/jarvis/.venv/bin:$PATH"

# Expose Chainlit and Webhook ports
EXPOSE 8000 9000

# Run using startup script

CMD ["/jarvis/app/start.sh"]
