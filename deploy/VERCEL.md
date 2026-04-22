# Deploy to Vercel (5 minutes, free tier, no credit card)

Vercel makes Next.js and natively supports everything in this app —
API routes, streaming, webhooks, all of it. Free tier covers
development-grade traffic easily (100 GB bandwidth, 100 GB-hours of
serverless compute, 1000 builds / month).

## One-time setup

### 1. Sign in with GitHub

Go to <https://vercel.com/signup> and pick **Continue with GitHub**.
Use the same GitHub account that owns `D1AgencyMAX/d1-dashboard`.

### 2. Import this repo

From the Vercel dashboard:

- Click **Add New → Project**
- Find `D1AgencyMAX/d1-dashboard` in the list, click **Import**
- If you don't see it, click **Adjust GitHub App Permissions** and add
  this repo to the Vercel GitHub app's access list.

### 3. Configure the project

**Root Directory**: leave blank (the repo IS the Next.js app).

**Framework Preset**: Vercel will auto-detect "Next.js" — leave as is.

**Build & Output settings**: leave defaults. `vercel.json` in the repo
already declares everything.

**Branch**: change from `main` to `claude/ai-prank-call-comedian-RpBI6`.

### 4. Paste environment variables

Click **Environment Variables** and add these (one at a time, or paste
the whole block into the import tool if available):

```
NEXT_PUBLIC_SUPABASE_URL=https://stub.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=stub
ANTHROPIC_API_KEY=<your-anthropic-key>
ELEVENLABS_API_KEY=<your-elevenlabs-key>
```

(Leave Supabase as stubs for now — the playground doesn't need them.
Full WhatsApp flow later wants the real Supabase keys + the
`SUPABASE_SERVICE_ROLE_KEY`, `WHATSAPP_*`, and `OPENAI_API_KEY` values.)

### 5. Click **Deploy**

First build takes ~90 seconds. When it finishes you get a URL like
`https://d1-dashboard-abc123.vercel.app`.

Open `https://<that-url>/playground` in Chrome, click **Start talking**,
speak. Bruno replies in his actual ElevenLabs voice this time.

## What happens on every push after that

Every commit pushed to `claude/ai-prank-call-comedian-RpBI6` triggers a
fresh build. PR branches get preview deployments at a different URL.
Merge to `main` → production URL gets the update.

## Custom domain (optional)

Vercel → your project → Settings → Domains → Add. Paste something like
`bruno.d1agency.com.au`. Vercel gives you a CNAME to add to your DNS;
once propagated (~15 min) the site is live on that domain with auto
HTTPS.

## Troubleshooting

| Symptom | Fix |
|---|---|
| Build fails with "NEXT_PUBLIC_SUPABASE_URL is undefined" | Environment variables weren't set. Project → Settings → Environment Variables → add them, then redeploy from the Deployments tab. |
| Playground returns 500 on send | Anthropic key wrong / out of credit. Check console.anthropic.com. |
| Voice mode says "ElevenLabs unreachable" | ElevenLabs key wrong or out of credit. Check elevenlabs.io/app/usage. |
| Deployment protected by Vercel authentication | Project → Settings → Deployment Protection → turn off "Vercel Authentication" (it blocks public access by default on some team plans). |
