# jarvis db

Database management commands for Qdrant.

## Commands

### jarvis db update

Update Qdrant database (ingestion only, no git operations). Works on all repos by default.

```bash
jarvis db update [OPTIONS]
```

**Options:**

| Option | Description |
|--------|-------------|
| `-r, --repo` | Repository name(s) to update. Can be used multiple times. Defaults to all repos. |
| `--force` | Force re-ingestion of all files |

**Examples:**

```bash
# Update all repos in Qdrant (default)
jarvis db update

# Update specific repos
jarvis db update -r HOPE
jarvis db update -r HOPE -r Aurora

# Force re-ingestion
jarvis db update --force
jarvis db update -r HOPE --force
```

**Process:**
1. Scans local repository files (no git pull)
2. Chunks markdown files
3. Generates embeddings
4. Stores in Qdrant

**Note:** Requires repos to be synced first with `jarvis repo pull`.

---

### jarvis db reset

Reset Qdrant data for specific repositories or the entire collection. Works on entire collection by default.

```bash
jarvis db reset [OPTIONS]
```

**Options:**

| Option | Description |
|--------|-------------|
| `-r, --repo` | Repository name(s) to reset. Can be used multiple times. Defaults to entire collection. |

**Confirmation:** This command requires confirmation before deleting data.

**Examples:**

```bash
# Reset entire collection (default)
jarvis db reset

# Reset specific repos
jarvis db reset -r HOPE
jarvis db reset -r HOPE -r Aurora
```

---

### jarvis db info

Display information about the Qdrant collection and stored data.

```bash
jarvis db info
```

**Output example:**
```
Collection: hope_docs
  Status: green
  Points: 1234
  Vector size: 384
  Distance: Cosine

Chunks per repo:
  HOPE: 500 chunks
  Country Report: 300 chunks
  Country Workspace: 250 chunks
  Aurora: 184 chunks
```

## Use Cases

- **db update**: Ingest local repo files into Qdrant
- **db reset**: After repository structure changes, or to start fresh
- **db info**: Check ingestion status and chunk distribution

## Warning

`jarvis db reset` (without `-r`) deletes ALL data in the collection. After running it, you'll need to re-ingest with:
```bash
jarvis repo pull --force
```
