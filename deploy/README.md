# VPS deployment

The stack builds to a single Next.js standalone image plus (optionally) a
Caddy reverse proxy. Pick the path that matches your VPS:

| Scenario | Use |
|---|---|
| **VPS 1** — already runs VoxReach / nginx / Caddy on :80/:443 | **App-only** — installer default, no collision |
| **VPS 2** — fresh box, nothing else on :80/:443 | **App + Caddy** — pass `--with-caddy` |

Every secret lives in a single `.env` file at the repo root. See
`.env.example` for the full list; nothing gets baked into images.

## One-shot install (recommended)

SSH into the VPS, then run:

```bash
# VPS 1 (or any box with an existing reverse proxy)
curl -fsSL https://raw.githubusercontent.com/D1AgencyMAX/d1-dashboard/claude/ai-prank-call-comedian-RpBI6/deploy/install.sh \
  | sudo bash

# VPS 2 (fresh box — installs Caddy too, auto-HTTPS)
curl -fsSL https://raw.githubusercontent.com/D1AgencyMAX/d1-dashboard/claude/ai-prank-call-comedian-RpBI6/deploy/install.sh \
  | sudo bash -s -- --with-caddy
```

First run writes `/opt/comedian/.env` and stops. Edit the file with real
keys and re-run the same command to build + start.

The installer auto-detects :80/:443 collisions even if you pass
`--with-caddy` — if something's already listening it silently falls back
to app-only so it never breaks your existing services.

## What "app-only" looks like

- The app container binds to `127.0.0.1:3100` (configurable via
  `APP_PORT` / `APP_BIND` in `.env`).
- Not reachable from the public internet at all.
- You point your existing reverse proxy (nginx/Caddy/whatever runs
  VoxReach) at `127.0.0.1:3100`. Snippets live in `deploy/proxy-snippets/`.

## Wiring it into the existing reverse proxy on VPS 1

### If VPS 1 runs nginx

```bash
sudo cp /opt/comedian/deploy/proxy-snippets/nginx-vhost.conf.example \
        /etc/nginx/sites-available/comedian.conf
sudo $EDITOR /etc/nginx/sites-available/comedian.conf  # set server_name
sudo ln -s /etc/nginx/sites-available/comedian.conf /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx

# If you need a TLS cert on the new hostname:
sudo certbot --nginx -d comedian.your-host.example
```

### If VPS 1 runs Caddy

```bash
sudo $EDITOR /etc/caddy/Caddyfile
# Paste the block from /opt/comedian/deploy/proxy-snippets/Caddyfile.snippet
# and change "comedian.your-host.example" to your real hostname.
sudo caddy validate --config /etc/caddy/Caddyfile
sudo systemctl reload caddy
```

### If VPS 1 runs Dockerised Caddy/Traefik

Add the comedian container to the same docker network as your edge proxy,
or keep it on the host and proxy to `host.docker.internal:3100` (on Docker
Desktop / Linux with `--add-host=host.docker.internal:host-gateway`).

## Manual install (step by step)

```bash
# 1. Docker
sudo apt update && sudo apt install -y ca-certificates curl git
curl -fsSL https://get.docker.com | sudo sh

# 2. Clone
sudo mkdir -p /opt && cd /opt
sudo git clone -b claude/ai-prank-call-comedian-RpBI6 \
  https://github.com/D1AgencyMAX/d1-dashboard.git comedian
cd comedian

# 3. Configure
sudo cp .env.example .env
sudo $EDITOR .env

# 4a. App-only (VPS 1 path)
sudo docker compose up -d --build

# 4b. App + Caddy (VPS 2 path)
sudo docker compose -f docker-compose.yml -f docker-compose.edge.yml up -d --build

# 5. Verify
sudo docker compose ps
curl -sS -o /dev/null -w "%{http_code}\n" http://127.0.0.1:3100/playground   # expect 200
```

## Updating later

```bash
cd /opt/comedian
sudo git pull
sudo docker compose up -d --build        # or the edge variant, matching your first install
```

## Where each secret comes from

- `NEXT_PUBLIC_SUPABASE_URL` / `NEXT_PUBLIC_SUPABASE_ANON_KEY` — Supabase → Project Settings → API
- `SUPABASE_SERVICE_ROLE_KEY` — same page, service_role row (treat like root)
- `ANTHROPIC_API_KEY` — console.anthropic.com → API Keys
- `OPENAI_API_KEY` — platform.openai.com → API Keys (for Whisper transcription)
- `ELEVENLABS_API_KEY` — elevenlabs.io → Profile → API Key (for voice-note replies)
- `WHATSAPP_ACCESS_TOKEN` — Meta → App Dashboard → WhatsApp → API Setup (long-lived System User token)
- `WHATSAPP_APP_SECRET` — Meta → App Dashboard → Settings → Basic
- `WHATSAPP_VERIFY_TOKEN` — you make it up; paste same value into Meta's webhook config

## After the stack is up

1. **Run the Supabase migration** from `supabase/migrations/0001_comedian_schema.sql` in the Supabase SQL editor. Create a storage bucket called `call-recordings` (Public: off).
2. **In Meta**, point the webhook at `https://<your-hostname>/api/whatsapp/webhook` with the same verify token. Subscribe to the `messages` field.
3. **In the dashboard**, go to `/numbers` and register the WhatsApp Business number (phone number ID + business account ID from Meta).
4. Text the number. Watch `/conversations` in real time.

## Troubleshooting

| Symptom | Check |
|---|---|
| `docker compose up` fails with "build arg required" | `NEXT_PUBLIC_SUPABASE_URL` not in `.env` |
| `/playground` works but `/conversations` empty | Supabase migration not run, or service-role key wrong |
| Meta "Could not validate URL" | `WHATSAPP_VERIFY_TOKEN` mismatch between `.env` and Meta's webhook config |
| App reachable on :3100 but 502 from nginx | nginx vhost `proxy_pass` host wrong, or SELinux blocking (`setsebool -P httpd_can_network_connect 1`) |
| `--with-caddy` silently fell back to app-only | Something on VPS is already on :80/:443 — that's the safety net working |
