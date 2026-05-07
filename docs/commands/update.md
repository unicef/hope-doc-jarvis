# jarvis repo pull

Pull or clone repositories and ingest changed files into Qdrant (pull + db update).

## Command

### jarvis repo pull

Sync repositories and ingest changed files (pull + Qdrant ingestion).

```bash
jarvis repo pull [OPTIONS]
```

## Options

| Option | Description |
|--------|-------------|
| `-r, --repo` | Repository name(s) to process. Can be used multiple times. Defaults to all repos. |
| `--force` | Force re-pull/re-ingestion of all files, ignoring sync state |

## Default Behavior

**Works on all configured repositories by default.** Use `-r`/`--repo` to limit operations to specific repos.

## Examples

### Sync All Repositories (Pull + Ingest)
```bash
jarvis repo pull
```

Complete workflow for all repos:
1. Pull latest changes from GitHub
2. Detect changed markdown files
3. Chunk documents
4. Generate embeddings
5. Store in Qdrant

### Sync Specific Repositories
```bash
jarvis repo pull -r HOPE
jarvis repo pull -r HOPE -r Aurora
```

Syncs only the specified repositories.

### Force Operations
```bash
jarvis repo pull --force              # Force re-sync all repos
jarvis repo pull -r HOPE --force     # Force re-sync specific repo
```

Ignores sync state and re-processes all files. Useful after:
- Changing embedding models
- Modifying chunk settings
- Debugging ingestion issues

## How jarvis repo pull Works

1. **Pull**: Clones or pulls repositories to `DATA_PATH`
2. **Detect Changes**: Compares file hashes with sync state
3. **Chunk**: Splits markdown files using header-aware chunking
   - Extracts YAML frontmatter (title, tags, etc.) and adds to metadata
   - Converts `<glossary:TERM>` references to `TERM` in content
4. **Embed**: Generates vector embeddings using the configured model
5. **Store**: Upserts chunks into Qdrant with metadata (including frontmatter)

## Notes

- The Qdrant collection is automatically created if it doesn't exist
- Only markdown files in the configured `docs_dir` are processed
- Sync state is stored in `CONFIG_PATH/sync_state.json`
