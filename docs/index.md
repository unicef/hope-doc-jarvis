# HOPE Bot Documentation

Welcome to the HOPE Bot documentation. This bot provides an intelligent interface to query HOPE ecosystem documentation using RAG (Retrieval-Augmented Generation).

## What is HOPE Bot?

HOPE Bot is a documentation assistant that:

- **Ingests** markdown documentation from multiple GitHub repositories
- **Indexes** content in Qdrant vector database using embeddings
- **Retrieves** relevant context based on semantic search
- **Generates** accurate answers using Ollama LLMs with source citations

## Quick Links

- [Getting Started](getting-started.md) - Set up and run the bot
- [CLI Commands](commands/index.md) - Manage repositories and data
- [Webhook](webhook.md) - Automate updates via GitHub webhooks
- [Architecture](architecture.md) - Understand the system design
- [Configuration](configuration.md) - Environment variables reference
