# CLI Commands

HOPE Bot provides a CLI interface with the `jarvis` command group.

## Command Overview

| Command | Description |
|---------|-------------|
| `jarvis run web` | Start the Chainlit web interface locally |
| `jarvis run service` | Start webhook server for GitHub events |
| `jarvis repo pull` | Pull or clone repositories (git operations only) |
| `jarvis check` | Verify environment variables and service connectivity |
| `jarvis db update` | Update Qdrant database (ingestion only) |
| `jarvis db reset` | Reset Qdrant data for repos or entire collection |
| `jarvis db info` | Show Qdrant database information |
| `jarvis kb list` | List all knowledge base entries |
| `jarvis kb reset` | Delete all knowledge base entries |

## Common Patterns

### Work on All Repos (Default)
All commands work on all configured repositories by default:
```bash
jarvis repo pull              # Pull all repos
jarvis db update             # Update all repos in Qdrant
```

### Limit to Specific Repos
Use `-r`/`--repo` option (repeatable) to target specific repositories:
```bash
jarvis repo pull -r HOPE                    # Pull only HOPE
jarvis db update -r HOPE -r Aurora    # Update specific repos in Qdrant
jarvis db reset -r HOPE               # Reset specific repo
```

### Force Operations
```bash
jarvis repo pull --force        # Force re-pull all repos
jarvis db update --force       # Force re-ingestion
```

### Database Management
```bash
jarvis db info          # Show stats
jarvis db reset         # Reset entire collection
jarvis db reset -r HOPE    # Reset single repo
```

## Command Structure

The CLI is organized into groups to separate concerns:

- **`jarvis run web`**: Start Chainlit web interface locally
- **`jarvis run service`**: Start webhook server for GitHub events
- **`jarvis repo pull`**: Git pull/clone only (no Qdrant ingestion)
- **`jarvis db update`**: Qdrant ingestion only (no git operations)

### jarvis run Commands

| Command | Description |
|---------|-------------|
| `jarvis run web [--bind host[:port]]` | Start Chainlit web interface (default: localhost:8000) |
| `jarvis run service [--bind host[:port]]` | Start webhook server for GitHub push events (default: 0.0.0.0:9000) |

**Bind Format:** `host[:port]` where port defaults to 8000 (web) or 9000 (service).

**Examples:**
```bash
jarvis run web                          # Start Chainlit on localhost:8000
jarvis run web --bind localhost:8080    # Custom host:port
jarvis run web --bind :9000             # Default host (localhost), custom port
jarvis run service                       # Start webhook on 0.0.0.0:9000
jarvis run service --bind 127.0.0.1    # Custom host, default port (9000)
jarvis run service --bind :8080         # All interfaces, custom port
```

Navigate to specific command documentation:
- [jarvis repo pull](update.md)
- [jarvis db](db.md)
- [jarvis kb](kb.md) *(to be created)*
- [jarvis check](check.md)
