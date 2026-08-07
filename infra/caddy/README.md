# Caddy

Caddy is the browser-facing reverse proxy for Employee Ops Assistant. It sends
all requests to OAuth2 Proxy, which authenticates the user before forwarding to
the private Gradio container.

## Local validation

The default site address is `http://localhost`, so start the stack and open that
URL:

```bash
docker compose -f infra/compose.yaml up -d --build
```

Configure both Google OAuth and `infra/oauth2-proxy/.env` with this callback:

```text
http://localhost/oauth2/callback
```

## EC2 with automatic HTTPS

Point a domain's DNS record to the EC2 public IP, configure Google OAuth and
OAuth2 Proxy with `https://<domain>/oauth2/callback`, and start Compose with the
domain as the Caddy site address:

```bash
APP_ADDRESS=assistant.example.com docker compose -f infra/compose.yaml up -d
```

Set `OAUTH2_PROXY_COOKIE_SECURE=true` for HTTPS. Ports 80 and 443 must reach the
instance so Caddy can complete certificate issuance and redirect HTTP to HTTPS.
Caddy stores certificates and state in the `caddy-data` and `caddy-config`
volumes.

Because the instance currently has no Elastic IP, update the DNS record whenever
its public IP changes.
