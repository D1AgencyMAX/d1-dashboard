# AI Comedian (WhatsApp) — setup

This feature turns the dashboard into a WhatsApp comedy-character bot. Targets
text or voice-note your WhatsApp Business number; a Claude-powered character
(default: **Bruno Papadopoulos**, a deadpan Mediterranean-Australian tyre-shop
uncle) replies in kind. Everything is recorded against a conversation thread
so you can pull the best bits for YouTube.

## Architecture (what calls what)

```
Target on WhatsApp
      │
      ▼
WhatsApp Cloud API  ── webhook ──▶  /api/whatsapp/webhook
      ▲                                     │
      │                                     ▼
      │                          orchestrate.ts
      │                          ├─ downloadMedia (voice notes)
      │                          ├─ transcribeAudio (Whisper)
      │                          ├─ generateReply (Claude)
      │                          ├─ synthesizeSpeech (ElevenLabs)
      │                          └─ uploadMedia
      │                                     │
      └──── sendText / sendAudio ◀──────────┘
```

Every turn is stored in Supabase: `conversations` + `messages` (with cost,
latency, and audio paths). Voice notes live in the `call-recordings` bucket
and stream back via `/api/media/[id]`.

## One-time setup

### 1. Supabase

1. Run the migration in `supabase/migrations/0001_comedian_schema.sql` against
   your project (via the SQL editor or `supabase db push`).
2. Create a **public = off** storage bucket called `call-recordings`. Files
   are served via signed URLs from `/api/media/[id]`, so no public access is
   needed.
3. Grab the **service role key** from *Project Settings → API* and paste it
   into `.env.local` as `SUPABASE_SERVICE_ROLE_KEY`.

### 2. Meta / WhatsApp Business Cloud API

1. Create a Meta app at <https://developers.facebook.com/apps>. Add the
   **WhatsApp** product. You get a test number for free; for production you
   attach the VoxReach number you already have.
2. From *WhatsApp → API Setup*, copy:
   - **Phone number ID** (`wa_phone_number_id`)
   - **WhatsApp Business Account ID** (`wa_business_account_id`)
3. Create a **System User** with `whatsapp_business_messaging` +
   `whatsapp_business_management` permissions and generate a long-lived token.
   Paste it as `WHATSAPP_ACCESS_TOKEN`.
4. From *App Dashboard → Settings → Basic*, copy the **App Secret** to
   `WHATSAPP_APP_SECRET`.
5. Pick any string for `WHATSAPP_VERIFY_TOKEN` (e.g. `bruno-is-on-the-case`)
   and paste the same value in Meta's webhook configuration.
6. Point the webhook at `https://<your-deploy>/api/whatsapp/webhook` and
   subscribe to the **messages** field on the WhatsApp Business Account.

### 3. Anthropic / OpenAI / ElevenLabs

Paste keys into `.env.local`:

- `ANTHROPIC_API_KEY` — required. Model defaults to `claude-sonnet-4-6`.
- `OPENAI_API_KEY` — required for voice notes (Whisper transcribes them).
- `ELEVENLABS_API_KEY` — required if you want the bot to reply with voice
  notes. Without it the bot always replies in text even if the target sends
  audio.

For ElevenLabs, find a voice that matches Bruno (try searching the voice
library for "Australian" or "Greek") and paste its voice ID into the character
editor at `/characters`.

## Day-to-day use

### Inbound (the easy path, no template approval needed)

1. Post the bot's WhatsApp number on your channel, IG story, livestream.
2. Anyone who messages it opens a 24-hour free-form window automatically.
3. Watch threads arrive in real-time at `/conversations`. Toggle **Highlight**
   on anything clip-worthy.

### Outbound (prank a specific target)

1. Get a release signed. `/releases` → fill in target phone, target name,
   signer name + typed signature. Store in DB.
2. Get a **template** approved in Meta (e.g. a simple "Hey, someone wanted me
   to reach out — reply if you want to chat" in neutral wording). Template
   approval takes 24–48h the first time; later templates are usually instant.
3. Back in `/releases`, pick the WhatsApp number + character, enter the
   target phone + approved template name, and click **Send template**.
4. If the target replies, the character takes over for the next 24 hours.

## Safety

- Every character prompt contains a hard safety block with a `[END_CALL]`
  sentinel. If the model detects distress, a self-identified minor, or the
  target asks "is this AI" twice, the bot drops character and flags the
  conversation. Flagged threads appear in orange on `/conversations`.
- The webhook verifies every POST with HMAC-SHA256 against
  `WHATSAPP_APP_SECRET`. Unsigned or malformed requests return 401.
- Outbound sends are hard-gated: no release on file = 403, no send, no
  conversation row created.

## Costs (rough guide, per turn)

| Piece | Price |
|---|---|
| Claude Sonnet 4.6 reply (~800 input / ~60 output tokens, with prompt caching after turn 1) | **~$0.002** |
| Whisper transcription (~10s voice note) | **~$0.001** |
| ElevenLabs voice note (~120 chars) | **~$0.035** |
| WhatsApp conversation (24h session, free for user-initiated) | **$0** |

Text-only replies are essentially free. Voice-note replies cost about 3.5¢
each thanks to ElevenLabs. A 10-turn voice-note conversation lands around 40¢.
