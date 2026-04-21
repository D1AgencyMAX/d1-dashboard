# VPS 2 deployment

The whole stack ships as one `docker compose` bundle:

| Container | Image | Purpose |
|---|---|---|
| `comedian-app` | built from `Dockerfile` | Next.js 16 standalone server on :3000 |
| `comedian-caddy` | `caddy:2-alpine` | Reverse proxy with auto-HTTPS on :80/:443 |

Every environment variable lives in a single `.env` file at the repo root
(the service-role key, Anthropic key, WhatsApp token, etc. — see
`.env.example`). No secrets in Dockerfiles, no secrets baked into images.

## One-shot install on a fresh VPS

As root on VPS 2:

```bash
curl -fsSL https://raw.githubusercontent.com/D1AgencyMAX/d1-dashboard/claude/ai-prank-call-comedian-RpBI6/deploy/install.sh \
  | sudo bash
```

First run clones into `/opt/comedian`, installs Docker, writes a blank
`.env`, and stops. Edit `/opt/comedian/.env` with real keys + `APP_HOSTNAME`,
then re-run the same command and it'll build + start everything.

## Manual install (if you'd rather see each step)

```bash
# 1. Install Docker
sudo apt update && sudo apt install -y ca-certificates curl git
curl -fsSL https://get.docker.com | sudo sh

# 2. Clone
sudo mkdir -p /opt && cd /opt
sudo git clone -b claude/ai-prank-call-comedian-RpBI6 \
  https://github.com/D1AgencyMAX/d1-dashboard.git comedian
cd comedian

# 3. Configure
sudo cp .env.example .env
sudo nano .env     # fill in every key + set APP_HOSTNAME

# 4. Run
sudo docker compose up -d --build

# 5. Check
sudo docker compose logs -f
```

## What `APP_HOSTNAME` should be

Caddy uses this to request a Let's Encrypt certificate on first run.
Anything resolvable publicly works:

| Example | Notes |
|---|---|
| `comedian.d1agency.com.au` | Real DNS A record pointing to VPS 2's IP |
| `50-6-251-57.nip.io` | nip.io wildcard — no DNS setup needed |
| `vps2.yourdomain.xyz` | Cloudflare / Route53 / whatever |

Caddy only fetches a cert after DNS points at the VPS and ports 80/443
are open. If that check fails you'll see it in `docker compose logs caddy`.

## Updating later

```bash
cd /opt/comedian
sudo git pull
sudo docker compose up -d --build
```

## Health checks (manual)

```bash
# Is the app healthy?
curl -sS http://localhost:3000/api/whatsapp/webhook?hub.mode=subscribe\&hub.verify_token=wrong\&hub.challenge=x
# -> 403, which means the handler is live (just with a bad token).

# Is Caddy terminating TLS?
curl -I https://$(grep APP_HOSTNAME .env | cut -d= -f2)
# -> HTTP/2 200 or 307 redirect from Next
```

## Where each secret comes from

- `NEXT_PUBLIC_SUPABASE_URL` / `NEXT_PUBLIC_SUPABASE_ANON_KEY` — Supabase → Project Settings → API
- `SUPABASE_SERVICE_ROLE_KEY` — same page, service_role row (treat like a root password)
- `ANTHROPIC_API_KEY` — console.anthropic.com → API Keys
- `OPENAI_API_KEY` — platform.openai.com → API Keys (only needed for voice-note transcription)
- `ELEVENLABS_API_KEY` — elevenlabs.io → Profile → API Key (only for voice-note replies)
- `WHATSAPP_ACCESS_TOKEN` — Meta → App Dashboard → WhatsApp → API Setup (long-lived System User token)
- `WHATSAPP_APP_SECRET` — Meta → App Dashboard → Settings → Basic
- `WHATSAPP_VERIFY_TOKEN` — you make this up; paste the same string into Meta's webhook config

## After the stack is up

1. **Run the Supabase migration** from `supabase/migrations/0001_comedian_schema.sql` in the Supabase SQL editor. Create a storage bucket called `call-recordings` (Public: off).
2. **In Meta**, point the webhook at `https://<APP_HOSTNAME>/api/whatsapp/webhook` with the same verify token. Subscribe to the `messages` field.
3. **In the dashboard**, go to `/numbers` and register the WhatsApp Business number (phone number ID + business account ID from Meta).
4. Text the number. Watch `/conversations` in real time.

## Troubleshooting

| Symptom | Check |
|---|---|
| `docker compose up` fails with "build arg required" | `NEXT_PUBLIC_SUPABASE_URL` not in `.env` |
| Caddy logs show ACME failures | DNS isn't pointing at the VPS yet, or port 80 is firewalled |
| `/playground` works but `/conversations` is empty | Supabase migration not run, or service-role key wrong |
| Meta "Could not validate URL" | `WHATSAPP_VERIFY_TOKEN` mismatch between `.env` and Meta's webhook config |
| Voice-note transcription fails | `OPENAI_API_KEY` missing or out of credit |
