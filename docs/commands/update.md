# jarvis pull / jarvis sync

HOPE Bot provides two commands for updating repositories: `pull` for git operations only, and `sync` for the complete workflow (pull + Qdrant ingestion).

## Commands

### jarvis pull

Pull or clone repositories (git operations only, no Qdrant ingestion).

```bash
jarvis pull [OPTIONS]
```

### jarvis sync

Sync repositories and ingest changed files (pull + Qdrant ingestion).

```bash
jarvis sync [OPTIONS]
```

## Options

Both commands accept the same options:

| Option | Description |
|--------|-------------|
| `-r, --repo` | Repository name(s) to process. Can be used multiple times. Defaults to all repos. |
| `--force` | Force re-pull/re-ingestion of all files, ignoring sync state |

## Default Behavior

**All commands work on all configured repositories by default.** Use `-r`/`--repo` to limit operations to specific repos.

## Examples

### Pull All Repositories (Git Only)
```bash
jarvis pull
```

Clones or pulls all repositories from GitHub to `DATA_PATH`.

### Pull Specific Repositories
```bash
jarvis pull -r HOPE
jarvis pull -r HOPE -r Aurora
```

Pulls only the specified repositories.

### Sync All Repositories (Pull + Ingest)
```bash
jarvis sync
```

Complete workflow for all repos:
1. Pull latest changes from GitHub
2. Detect changed markdown files
3. Chunk documents
4. Generate embeddings
5. Store in Qdrant

### Sync Specific Repositories
```bash
jarvis sync -r HOPE
jarvis sync -r HOPE -r Aurora
```

Syncs only the specified repositories.

### Force Operations
```bash
jarvis pull --force              # Force re-pull all repos
jarvis sync --force              # Force re-sync all repos
jarvis sync -r HOPE --force     # Force re-sync specific repo
```

Ignores sync state and re-processes all files. Useful after:
- Changing embedding models
- Modifying chunk settings
- Debugging ingestion issues

## How jarvis sync Works

1. **Pull**: Clones or pulls repositories to `DATA_PATH`
2. **Detect Changes**: Compares file hashes with sync state
3. **Chunk**: Splits markdown files using header-aware chunking
4. **Embed**: Generates vector embeddings using the configured model
5. **Store**: Upserts chunks into Qdrant with metadata

## Notes

- The Qdrant collection is automatically created if it doesn't exist (only `jarvis sync`)
- Only markdown files in the configured `docs_dir` are processed
- Sync state is stored in `CONFIG_PATH/sync_state.json`
- `jarvis pull` only performs git operations, no Qdrant ingestion
