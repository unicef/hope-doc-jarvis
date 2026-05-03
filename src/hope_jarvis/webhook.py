"""Webhook server to trigger repo updates."""

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import sentry_sdk

from hope_jarvis.cli import jarvis

sentry_dsn = os.environ.get("SENTRY_DSN")
if sentry_dsn:
    sentry_sdk.init(
        dsn=sentry_dsn,
        environment=os.environ.get("ENVIRONMENT", "production"),
        send_default_pii=False,
    )

PORT = 9000
WEBHOOK_TOKEN = os.environ.get("WEBHOOK_TOKEN", "")


class WebhookHandler(BaseHTTPRequestHandler):
    def _check_auth(self):
        """Check if request has valid token."""
        if not WEBHOOK_TOKEN:
            return True  # No token configured, allow all
        auth_header = self.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
        else:
            token = self.headers.get("X-Webhook-Token", "")
        return token == WEBHOOK_TOKEN

    def do_POST(self):
        if not self._check_auth():
            self.send_response(401)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Unauthorized"}).encode())
            return

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length else b"{}"

        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            payload = {}

        repo_name = payload.get("repository", {}).get("name") or payload.get("repo")
        if not repo_name:
            self.send_response(400)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Missing repo name"}).encode())
            return

        print(f"Webhook received for repo: {repo_name}")

        try:
            from click.testing import CliRunner

            runner = CliRunner()
            result = runner.invoke(jarvis, ["update", repo_name])
            print(result.output)
            if result.exit_code != 0:
                raise Exception(result.output)

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(
                json.dumps({"status": "success", "repo": repo_name}).encode()
            )
        except Exception as e:
            print(f"Update error: {e}")
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(
                json.dumps({"status": "error", "message": str(e)}).encode()
            )

    def log_message(self, format, *args):
        print(f"[WEBHOOK] {format % args}")


def main():
    """Entry point for webhook server."""
    server = ThreadingHTTPServer(("0.0.0.0", PORT), WebhookHandler)
    print(
        f"Webhook server running on port {PORT} (auth: {'enabled' if WEBHOOK_TOKEN else 'disabled'})"
    )
    server.serve_forever()


if __name__ == "__main__":
    main()
