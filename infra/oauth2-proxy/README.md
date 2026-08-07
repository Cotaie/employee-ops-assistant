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

Set `OIDC_AUDIENCE` in `services/agent_api/.env` to the same Google client ID as
`OAUTH2_PROXY_CLIENT_ID`. Agent API uses it when validating forwarded ID tokens.

## Access

For local testing through Caddy, register
`http://localhost/oauth2/callback` with Google, use the same redirect URL in
`.env`, and open `http://localhost`.

For EC2, Caddy is the only browser-facing service. See
[`../caddy/README.md`](../caddy/README.md) for domain and automatic HTTPS setup.
OAuth2 Proxy port `4180` and Gradio port `7860` are available only inside the
Compose network.
