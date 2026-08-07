# OAuth2 Proxy

OAuth2 Proxy authenticates users with Google before forwarding browser requests
to the Gradio UI. Gradio remains private inside the Docker Compose network.

## Configuration

From the repository root, create the private environment file:

```bash
cp infra/oauth2-proxy/.env.example infra/oauth2-proxy/.env
```

Register the matching callback URL in the Google OAuth client and replace the
placeholder values in `.env`. Generate the cookie secret with:

```bash
openssl rand -base64 32 | tr -- '+/' '-_'
```

The `.env` file contains secrets and is ignored by Git. The `.env.example` file
documents the required settings and is safe to commit.

## Access

For local testing, open `http://localhost:4180` directly. For EC2 smoke testing,
tunnel local port `4180` to EC2 port `4180`, then open the same URL.

For production, Caddy should proxy HTTPS traffic to `127.0.0.1:4180`. Use the
HTTPS redirect URL and secure cookie settings documented in `.env.example`.
