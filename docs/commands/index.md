# CLI Commands

HOPE Bot provides a CLI interface with the `jarvis` command group.

## Command Overview

| Command | Description |
|---------|-------------|
| `jarvis pull` | Pull or clone repositories (git operations only) |
| `jarvis sync` | Sync repos and ingest changed files (pull + db update) |
| `jarvis info` | List all configured repositories |
| `jarvis check` | Verify environment variables are set |
| `jarvis db update` | Update Qdrant database (ingestion only) |
| `jarvis db reset` | Reset Qdrant data for repos or entire collection |
| `jarvis db info` | Show Qdrant database information |

## Common Patterns

### Work on All Repos (Default)
All commands work on all configured repositories by default:
```bash
jarvis pull              # Pull all repos
jarvis sync              # Sync all repos (pull + ingest)
jarvis db update        # Update all repos in Qdrant
```

### Limit to Specific Repos
Use `-r`/`--repo` option (repeatable) to target specific repositories:
```bash
jarvis pull -r HOPE                    # Pull only HOPE
jarvis sync -r HOPE -r Aurora         # Sync multiple repos
jarvis db update -r HOPE -r Aurora    # Update specific repos in Qdrant
jarvis db reset -r HOPE               # Reset specific repo
```

### Force Operations
```bash
jarvis pull --force        # Force re-pull all repos
jarvis sync --force        # Force re-sync all repos
jarvis db update --force  # Force re-ingestion
```

### Database Management
```bash
jarvis db info          # Show stats
jarvis db reset         # Reset entire collection
jarvis db reset -r HOPE    # Reset single repo
```

## New Command Structure

The CLI has been refactored to separate git operations from database operations:

- **`jarvis pull`**: Git pull/clone only (no Qdrant ingestion)
- **`jarvis db update`**: Qdrant ingestion only (no git operations)
- **`jarvis sync`**: Combines both (pull + db update)

Navigate to specific command documentation:
- [jarvis pull / sync](update.md)
- [jarvis db](db.md)
- [jarvis check](check.md)
- [jarvis info](info.md)
