# Webhook

HOPE Bot includes a webhook server to automatically trigger repository updates when changes are pushed to GitHub.

## Overview

The webhook server listens on port `9000` and accepts POST requests to trigger the `jarvis update` command for specific repositories.

## Security

The webhook endpoint is protected by an optional token. Configure it using the `WEBHOOK_TOKEN` environment variable.

### Authentication Methods

Send the token via one of these headers:

1. **Authorization Bearer** (recommended)
```
Authorization: Bearer your-secret-token
```

2. **Custom Header**
```
X-Webhook-Token: your-secret-token
```

If `WEBHOOK_TOKEN` is not set, authentication is disabled (useful for development).

## Endpoint

```
POST http://your-server:9000/
```

## Request Format

The webhook accepts GitHub webhook payloads or simplified JSON:

### GitHub Webhook Payload
```json
{
  "repository": {
    "name": "HOPE"
  }
}
```

### Simplified Payload
```json
{
  "repo": "HOPE"
}
```

## Setup with GitHub

### 1. Set Webhook Token

Add to your `.env` or `docker-compose.yml`:
```bash
WEBHOOK_TOKEN=your-secret-token
```

### 2. Add Webhook in GitHub

1. Go to your repository **Settings > Webhooks**
2. Click **Add webhook**
3. Configure:
   - **Payload URL**: `http://your-server:9000/`
   - **Content type**: `application/json`
   - **Secret**: `your-secret-token`
   - **Events**: Select "Push" or "Individual events > Pushes"
4. Click **Add webhook**

### 3. Test

Push a change to your repository. The webhook will:
1. Receive the GitHub event
2. Trigger `jarvis update <repo_name>`
3. Ingest changed markdown files
4. Return success/error response

## Response Format

### Success (200)
```json
{
  "status": "success",
  "repo": "HOPE"
}
```

### Missing Repo Name (400)
```json
{
  "error": "Missing repo name"
}
```

### Unauthorized (401)
```json
{
  "error": "Unauthorized"
}
```

### Server Error (500)
```json
{
  "status": "error",
  "message": "error details"
}
```

## Example Usage

### Manual Trigger
```bash
curl -X POST http://localhost:9000 \
  -H "Authorization: Bearer your-secret-token" \
  -H "Content-Type: application/json" \
  -d '{"repository": {"name": "HOPE"}}'
```

### GitHub CLI
```bash
gh api repos/unicef/hope/hooks \
  -X POST \
  -f name='web' \
  -f active=true \
  -f events='["push"]' \
  -f config[url]='http://your-server:9000' \
  -f config[content_type]='application/json' \
  -f config[secret]='your-secret-token'
```

## Notes

- The webhook server runs alongside the Chainlit web interface
- Repository names must match those in `config/repos.yaml`
- Failed updates are logged but don't block the webhook response
- Use `docker-compose logs hope-bot` to view webhook activity
